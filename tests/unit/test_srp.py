"""SRP-6a against a reference implementation.

The port dropped boto3 and rewrote the helpers, so the risk is a silent arithmetic
or encoding difference — which would show up only as "wrong password" against the
live pool. The original warrant-derived algorithm is reproduced here verbatim and
the two are compared on pinned inputs.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
from datetime import UTC, datetime

import pytest

from icpc.auth.srp import BIG_N, SrpSession, cognito_timestamp, pad_hex

POOL_ID = "us-east-1_WaDOo4Gqm"
N_HEX = f"{BIG_N:X}"
G_HEX = "2"
INFO_BITS = bytearray("Caldera Derived Key", "utf-8")


# --------------------------------------------------------------- reference --
# Vendored from warrant's aws_srp.py, unchanged apart from removing boto3.


def _ref_hash_sha256(buf):
    a = hashlib.sha256(buf).hexdigest()
    return (64 - len(a)) * "0" + a


def _ref_hex_hash(hex_string):
    return _ref_hash_sha256(bytearray.fromhex(hex_string))


def _ref_pad_hex(long_int):
    hash_str = long_int if isinstance(long_int, str) else "%x" % long_int
    if len(hash_str) % 2 == 1:
        hash_str = "0%s" % hash_str
    elif hash_str[0] in "89ABCDEFabcdef":
        hash_str = "00%s" % hash_str
    return hash_str


def _ref_compute_hkdf(ikm, salt):
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    info_bits_update = INFO_BITS + bytearray(chr(1), "utf-8")
    return hmac.new(prk, info_bits_update, hashlib.sha256).digest()[:16]


def _ref_calculate_u(big_a, big_b):
    return int(_ref_hex_hash(_ref_pad_hex(big_a) + _ref_pad_hex(big_b)), 16)


def _ref_process_challenge(username, password, small_a, big_a, params, now):
    big_n = int(N_HEX, 16)
    g = int(G_HEX, 16)
    k = int(_ref_hex_hash("00" + N_HEX + "0" + G_HEX), 16)
    pool_name = POOL_ID.split("_")[1]

    user_id = params["USER_ID_FOR_SRP"]
    salt_hex = params["SALT"]
    server_b = int(params["SRP_B"], 16)
    secret_block_b64 = params["SECRET_BLOCK"]

    timestamp = re.sub(r" 0(\d) ", r" \1 ", now.strftime("%a %b %d %H:%M:%S UTC %Y"))

    u_value = _ref_calculate_u(big_a, server_b)
    username_password = "%s%s:%s" % (pool_name, user_id, password)
    username_password_hash = _ref_hash_sha256(username_password.encode("utf-8"))
    x_value = int(_ref_hex_hash(_ref_pad_hex(salt_hex) + username_password_hash), 16)
    g_mod_pow_xn = pow(g, x_value, big_n)
    int_value2 = server_b - k * g_mod_pow_xn
    s_value = pow(int_value2, small_a + u_value * x_value, big_n)
    hkdf = _ref_compute_hkdf(
        bytearray.fromhex(_ref_pad_hex(s_value)),
        bytearray.fromhex(_ref_pad_hex("%x" % u_value)),
    )

    secret_block_bytes = base64.standard_b64decode(secret_block_b64)
    msg = (
        bytearray(pool_name, "utf-8")
        + bytearray(user_id, "utf-8")
        + bytearray(secret_block_bytes)
        + bytearray(timestamp, "utf-8")
    )
    signature = base64.standard_b64encode(hmac.new(hkdf, msg, hashlib.sha256).digest())
    return {
        "TIMESTAMP": timestamp,
        "USERNAME": user_id,
        "PASSWORD_CLAIM_SECRET_BLOCK": secret_block_b64,
        "PASSWORD_CLAIM_SIGNATURE": signature.decode("utf-8"),
    }


# -------------------------------------------------------------- the tests --

SMALL_A = 0x1F3B7C9D2E4A6058B1C3D5E7F90A2B4C6D8E0F123456789ABCDEF0123456789A
CHALLENGE = {
    "USER_ID_FOR_SRP": "8f14e45f-ceea-467a-9a1b-1c0f3d5a7b90",
    "SALT": "a3f1c9d2e4b6580a",
    # A plausible server B: any value that is not a multiple of N works.
    "SRP_B": f"{pow(2, 0x2A3B4C5D6E7F, BIG_N):x}",
    "SECRET_BLOCK": base64.b64encode(b"opaque-cognito-secret-block").decode(),
}
NOW = datetime(2026, 3, 7, 9, 4, 11, tzinfo=UTC)


def test_matches_the_reference_implementation():
    session = SrpSession.create("user@example.com", "password", POOL_ID, a=SMALL_A)
    ours = session.process_challenge(CHALLENGE, now=NOW)
    theirs = _ref_process_challenge(
        "user@example.com",
        "password",
        SMALL_A,
        session.big_a,
        CHALLENGE,
        NOW.replace(tzinfo=None),
    )
    assert ours == theirs


def test_srp_a_matches_the_reference():
    session = SrpSession.create("user@example.com", "password", POOL_ID, a=SMALL_A)
    assert session.auth_parameters() == {
        "CHALLENGE_NAME": "SRP_A",
        "USERNAME": "user@example.com",
        "SRP_A": "%x" % pow(2, SMALL_A, BIG_N),
    }


def test_timestamp_strips_the_days_leading_zero():
    # Cognito rejects "Sat Mar 07"; it wants "Sat Mar 7".
    assert cognito_timestamp(NOW) == "Sat Mar 7 09:04:11 UTC 2026"


def test_timestamp_keeps_a_two_digit_day():
    stamp = cognito_timestamp(datetime(2026, 3, 17, 9, 4, 11, tzinfo=UTC))
    assert stamp == "Tue Mar 17 09:04:11 UTC 2026"


def test_timestamp_is_converted_to_utc():
    from datetime import timedelta, timezone

    moscow = timezone(timedelta(hours=3))
    stamp = cognito_timestamp(datetime(2026, 3, 7, 12, 4, 11, tzinfo=moscow))
    assert stamp == "Sat Mar 7 09:04:11 UTC 2026"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0x0A, "0a"),
        (0xFF, "00ff"),  # leading nibble >= 8 gains two zeros, not one
        (0x123, "0123"),  # odd length gains one
        ("8abc", "008abc"),
        ("7abc", "7abc"),
    ],
)
def test_pad_hex(value, expected):
    assert pad_hex(value) == expected


def test_pad_hex_agrees_with_the_reference_over_many_values():
    for candidate in range(0, 0x2000, 7):
        assert pad_hex(candidate) == _ref_pad_hex(candidate)


def test_pool_name_is_the_suffix():
    session = SrpSession.create("u", "p", POOL_ID, a=SMALL_A)
    assert session.pool_name == "WaDOo4Gqm"


def test_secret_block_is_echoed_back_untouched():
    session = SrpSession.create("u", "p", POOL_ID, a=SMALL_A)
    response = session.process_challenge(CHALLENGE, now=NOW)
    assert response["PASSWORD_CLAIM_SECRET_BLOCK"] == CHALLENGE["SECRET_BLOCK"]
    # And the username is the server's id, not the email that was typed.
    assert response["USERNAME"] == CHALLENGE["USER_ID_FOR_SRP"]
