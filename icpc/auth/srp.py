"""SRP-6a implementation used by Amazon Cognito.

Ported from warrant's ``aws_srp.py`` and reduced to the parts icpc.global's pool
actually exercises.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
from dataclasses import dataclass
from datetime import UTC, datetime

__all__ = ["SrpSession", "pad_hex"]

# https://github.com/aws-amplify/amplify-js/blob/36e3ce19983925ee6a68b75ebd9a01a95100989b/packages/auth/src/providers/cognito/utils/srp/AuthenticationHelper/AuthenticationHelper.ts
_N_HEX = (
    "FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
    "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3D"
    "C2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F"
    "83655D23DCA3AD961C62F356208552BB9ED529077096966D"
    "670C354E4ABC9804F1746C08CA18217C32905E462E36CE3B"
    "E39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9"
    "DE2BCBF6955817183995497CEA956AE515D2261898FA0510"
    "15728E5A8AAAC42DAD33170D04507A33A85521ABDF1CBA64"
    "ECFB850458DBEF0A8AEA71575D060C7DB3970F85A6E1E4C7"
    "ABF5AE8CDB0933D71E8C94E04A25619DCEE3D2261AD2EE6B"
    "F12FFA06D98A0864D87602733EC86A64521F2B18177B200C"
    "BBE117577A615D6C770988C0BAD946E208E24FA074E5AB31"
    "43DB5BFCE0FD108E4B82D120A93AD2CAFFFFFFFFFFFFFFFF"
)
_G_HEX = "2"
_INFO_BITS = b"Caldera Derived Key"

BIG_N = int(_N_HEX, 16)
G = int(_G_HEX, 16)

_TIMESTAMP_DAY = re.compile(r" 0(\d) ")
_WEEKDAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = (
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
)  # fmt: skip


def _hash_sha256(buf: bytes) -> str:
    digest = hashlib.sha256(buf).hexdigest()
    return digest.rjust(64, "0")


def _hex_hash(hex_string: str) -> str:
    return _hash_sha256(bytes.fromhex(hex_string))


def pad_hex(value: int | str) -> str:
    """Hex-encode for hashing, padded the way Cognito expects.

    An odd-length string gets one leading zero; a string whose first nibble is >= 8
    gets two, so it is never mistaken for a negative two's-complement number.
    """
    hex_str = value if isinstance(value, str) else f"{value:x}"
    if len(hex_str) % 2 == 1:
        return "0" + hex_str
    if hex_str[0] in "89ABCDEFabcdef":
        return "00" + hex_str
    return hex_str


def _compute_hkdf(ikm: bytes, salt: bytes) -> bytes:
    prk = hmac.new(salt, ikm, hashlib.sha256).digest()
    return hmac.new(prk, _INFO_BITS + b"\x01", hashlib.sha256).digest()[:16]


def _calculate_u(big_a: int, big_b: int) -> int:
    return int(_hex_hash(pad_hex(big_a) + pad_hex(big_b)), 16)


def cognito_timestamp(now: datetime) -> str:
    """``Tue Jan 7 09:04:11 UTC 2026`` — English names, UTC, no leading zero on the day.

    ``strftime("%a %b")`` would be locale-dependent, so the names are spelled out.
    """
    moment = now.astimezone(UTC)
    stamp = (
        f"{_WEEKDAYS[moment.weekday()]} {_MONTHS[moment.month - 1]} "
        f"{moment.day:02d} {moment:%H:%M:%S} UTC {moment.year}"
    )
    return _TIMESTAMP_DAY.sub(r" \1 ", stamp)


@dataclass(frozen=True, slots=True)
class SrpSession:
    """One client-side SRP exchange. Create it, send ``auth_parameters()``, then
    answer the server's challenge with ``process_challenge()``."""

    username: str
    password: str
    pool_id: str
    a: int
    big_a: int

    @classmethod
    def create(
        cls, username: str, password: str, pool_id: str, *, a: int | None = None
    ) -> SrpSession:
        """``a`` is injectable so tests can pin the exchange; otherwise it is random."""
        small_a = a if a is not None else int.from_bytes(os.urandom(128), "big") % BIG_N
        big_a = pow(G, small_a, BIG_N)
        if big_a % BIG_N == 0:
            raise ValueError("SRP safety check failed: A % N == 0")
        return cls(username=username, password=password, pool_id=pool_id, a=small_a, big_a=big_a)

    @property
    def pool_name(self) -> str:
        """``WaDOo4Gqm`` for ``us-east-1_WaDOo4Gqm`` — the part Cognito hashes."""
        return self.pool_id.split("_", 1)[1]

    def auth_parameters(self) -> dict[str, str]:
        """``AuthParameters`` for the initial ``InitiateAuth`` call.

        icpc.global's pool answers ``CUSTOM_AUTH`` + ``CHALLENGE_NAME: SRP_A`` with a
        ``PASSWORD_VERIFIER`` challenge; the app client has no secret, so there is no
        ``SECRET_HASH``.
        """
        return {
            "CHALLENGE_NAME": "SRP_A",
            "USERNAME": self.username,
            "SRP_A": f"{self.big_a:x}",
        }

    def _password_key(self, user_id_for_srp: str, server_b: int, salt_hex: str) -> bytes:
        u_value = _calculate_u(self.big_a, server_b)
        if u_value == 0:
            raise ValueError("SRP safety check failed: U == 0")
        credentials = f"{self.pool_name}{user_id_for_srp}:{self.password}"
        credentials_hash = _hash_sha256(credentials.encode())
        x_value = int(_hex_hash(pad_hex(salt_hex) + credentials_hash), 16)
        s_value = pow(
            server_b - _K * pow(G, x_value, BIG_N),
            self.a + u_value * x_value,
            BIG_N,
        )
        return _compute_hkdf(
            bytes.fromhex(pad_hex(s_value)),
            bytes.fromhex(pad_hex(f"{u_value:x}")),
        )

    def process_challenge(
        self, challenge_parameters: dict[str, str], *, now: datetime | None = None
    ) -> dict[str, str]:
        """Build ``ChallengeResponses`` for the ``PASSWORD_VERIFIER`` challenge."""
        user_id_for_srp = challenge_parameters["USER_ID_FOR_SRP"]
        secret_block = challenge_parameters["SECRET_BLOCK"]
        timestamp = cognito_timestamp(now or datetime.now(UTC))

        key = self._password_key(
            user_id_for_srp,
            int(challenge_parameters["SRP_B"], 16),
            challenge_parameters["SALT"],
        )
        message = (
            self.pool_name.encode()
            + user_id_for_srp.encode()
            + base64.standard_b64decode(secret_block)
            + timestamp.encode()
        )
        signature = base64.standard_b64encode(
            hmac.new(key, message, hashlib.sha256).digest()
        ).decode()
        return {
            "TIMESTAMP": timestamp,
            # Cognito wants the id it just handed us, not the email that was typed.
            "USERNAME": user_id_for_srp,
            "PASSWORD_CLAIM_SECRET_BLOCK": secret_block,
            "PASSWORD_CLAIM_SIGNATURE": signature,
        }


_K = int(_hex_hash("00" + _N_HEX + "0" + _G_HEX), 16)
