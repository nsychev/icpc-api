"""Cognito flows and the token store, exercised over a mocked Cognito."""

from __future__ import annotations

import base64
import json
import time

import httpx
import pytest

from icpc import errors
from icpc.auth.flows import CognitoAuth
from icpc.auth.store import PASSWORD_KEY, CredentialStore
from icpc.auth.tokens import TokenSet, decode_jwt_claims
from icpc.config import Settings


def make_jwt(email: str, exp: float) -> str:
    def part(payload: dict) -> str:
        raw = json.dumps(payload).encode()
        return base64.urlsafe_b64encode(raw).decode().rstrip("=")

    return f"{part({'alg': 'RS256'})}.{part({'email': email, 'exp': exp})}.signature"


def cognito(responses: list[dict], seen: list[dict] | None = None) -> CognitoAuth:
    queue = list(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        if seen is not None:
            seen.append(
                {
                    "target": request.headers["x-amz-target"],
                    "body": json.loads(request.content),
                }
            )
        payload = queue.pop(0)
        return httpx.Response(payload.pop("_status", 200), json=payload)

    return CognitoAuth(
        settings=Settings(),
        http=httpx.Client(transport=httpx.MockTransport(handler)),
    )


CHALLENGE = {
    "ChallengeName": "PASSWORD_VERIFIER",
    "Session": "session-1",
    "ChallengeParameters": {
        "USER_ID_FOR_SRP": "abc-123",
        "SALT": "a3f1c9d2e4b6580a",
        "SRP_B": "1f" * 64,
        "SECRET_BLOCK": base64.b64encode(b"block").decode(),
    },
}


def tokens_response(email: str = "u@example.com", ttl: int = 3600) -> dict:
    return {
        "AuthenticationResult": {
            "IdToken": make_jwt(email, time.time() + ttl),
            "AccessToken": "access",
            "RefreshToken": "refresh-1",
            "ExpiresIn": ttl,
        }
    }


def test_login_runs_the_two_step_srp_exchange():
    seen: list[dict] = []
    auth = cognito([CHALLENGE, tokens_response()], seen)
    tokens = auth.login("u@example.com", "pw")

    assert tokens.username == "u@example.com"
    assert [call["target"] for call in seen] == [
        "AWSCognitoIdentityProviderService.InitiateAuth",
        "AWSCognitoIdentityProviderService.RespondToAuthChallenge",
    ]
    # icpc.global's pool wants CUSTOM_AUTH, not the usual USER_SRP_AUTH.
    assert seen[0]["body"]["AuthFlow"] == "CUSTOM_AUTH"
    assert seen[0]["body"]["AuthParameters"]["CHALLENGE_NAME"] == "SRP_A"
    # The session must be echoed back, and the username is the server's id.
    assert seen[1]["body"]["Session"] == "session-1"
    assert seen[1]["body"]["ChallengeResponses"]["USERNAME"] == "abc-123"


def test_bad_password_raises_invalid_credentials():
    auth = cognito(
        [{"_status": 400, "__type": "NotAuthorizedException", "message": "Incorrect username"}]
    )
    with pytest.raises(errors.InvalidCredentials):
        auth.login("u@example.com", "wrong")


def test_mfa_challenge_is_surfaced_with_its_session():
    mfa = {"ChallengeName": "SOFTWARE_TOKEN_MFA", "Session": "session-2", "ChallengeParameters": {}}
    auth = cognito([CHALLENGE, mfa])
    with pytest.raises(errors.MfaRequired) as caught:
        auth.login("u@example.com", "pw")
    assert caught.value.session == "session-2"


def test_mfa_code_completes_the_login():
    mfa = {"ChallengeName": "SOFTWARE_TOKEN_MFA", "Session": "session-2", "ChallengeParameters": {}}
    seen: list[dict] = []
    auth = cognito([CHALLENGE, mfa, tokens_response()], seen)
    tokens = auth.login("u@example.com", "pw", mfa_code="123456")
    assert tokens.username == "u@example.com"
    assert seen[2]["body"]["ChallengeResponses"]["SOFTWARE_TOKEN_MFA_CODE"] == "123456"


def test_expired_token_is_refreshed_rather_than_re_logged_in():
    seen: list[dict] = []
    auth = cognito([tokens_response(ttl=7200)], seen)
    auth._tokens = TokenSet(id_token="stale", refresh_token="refresh-0", expires_at=0)

    token = auth.id_token()

    assert seen[0]["body"]["AuthFlow"] == "REFRESH_TOKEN_AUTH"
    assert seen[0]["body"]["AuthParameters"]["REFRESH_TOKEN"] == "refresh-0"
    assert token != "stale"


def test_fresh_token_is_reused_without_a_round_trip():
    seen: list[dict] = []
    auth = cognito([], seen)
    fresh = TokenSet(id_token="good", refresh_token="r", expires_at=time.time() + 3600)
    auth._tokens = fresh
    assert auth.id_token() == "good"
    assert seen == []


def test_invalidate_forces_the_next_call_to_refresh():
    seen: list[dict] = []
    auth = cognito([tokens_response()], seen)
    auth._tokens = TokenSet(id_token="good", refresh_token="r", expires_at=time.time() + 3600)
    auth.invalidate()
    auth.id_token()
    assert len(seen) == 1


def test_a_rejected_refresh_token_without_a_password_reports_why():
    # icpc.global's app client rejects REFRESH_TOKEN_AUTH outright, so this is the
    # ordinary path rather than an edge case; the reason must not be swallowed.
    revoked = {
        "_status": 400,
        "__type": "NotAuthorizedException",
        "message": "Invalid Refresh Token.",
    }
    auth = cognito([revoked])
    auth._tokens = TokenSet(id_token="stale", refresh_token="dead", expires_at=0)
    with pytest.raises(errors.TokenExpired, match="Invalid Refresh Token"):
        auth.id_token()


def test_a_revoked_refresh_token_falls_back_to_a_password_login():
    revoked = {"_status": 400, "__type": "NotAuthorizedException", "message": "Refresh Token"}
    auth = cognito([revoked, CHALLENGE, tokens_response()])
    auth.username, auth._password = "u@example.com", "pw"
    auth._tokens = TokenSet(id_token="stale", refresh_token="dead", expires_at=0)
    assert auth.refresh().username == "u@example.com"


def test_no_credentials_at_all_is_a_config_error():
    auth = cognito([])
    with pytest.raises(errors.ConfigError, match="icpc auth login"):
        auth.id_token()


def test_refresh_response_keeps_the_original_refresh_token():
    # REFRESH_TOKEN_AUTH responses omit it; losing it would break the next renewal.
    result = tokens_response()["AuthenticationResult"]
    del result["RefreshToken"]
    tokens = TokenSet.from_cognito(result, refresh_token="carried-over")
    assert tokens.refresh_token == "carried-over"


def test_expiry_comes_from_the_jwt_not_the_clock():
    exp = time.time() + 1234
    tokens = TokenSet.from_cognito({"IdToken": make_jwt("u@example.com", exp), "ExpiresIn": 3600})
    assert abs(tokens.expires_at - exp) < 1


def test_decode_jwt_claims_tolerates_rubbish():
    assert decode_jwt_claims("not-a-jwt") == {}
    assert decode_jwt_claims("a.b.c") == {}


# ------------------------------------------------------------------ store --


def test_store_round_trips_tokens_and_is_private(tmp_path):
    store = CredentialStore(tmp_path / "credentials.json")
    tokens = TokenSet(id_token="i", refresh_token="r", expires_at=1.0, username="u@example.com")
    store.save_tokens(tokens)

    account = store.load("u@example.com")
    assert account is not None
    assert account.tokens == tokens
    assert account.password is None
    assert account.can_renew is False
    # Credentials; the file must not be readable by anyone else.
    assert (tmp_path / "credentials.json").stat().st_mode & 0o077 == 0


def test_password_round_trips_and_enables_renewal(tmp_path):
    store = CredentialStore(tmp_path / "credentials.json")
    store.save_tokens(TokenSet(id_token="i", username="u@example.com"))
    store.save_password("u@example.com", "password")

    account = store.load("u@example.com")
    assert account is not None
    assert account.password == "password"
    assert account.can_renew is True
    # Tokens survive the password write, and vice versa.
    assert account.tokens is not None
    assert account.tokens.id_token == "i"


def test_password_is_not_stored_as_a_greppable_literal(tmp_path):
    # Base64 is obfuscation, not encryption, and the docs say so.
    path = tmp_path / "credentials.json"
    store = CredentialStore(path)
    store.save_password("u@example.com", "password")

    raw = path.read_text()
    assert PASSWORD_KEY in raw
    stored = json.loads(raw)["accounts"]["u@example.com"][PASSWORD_KEY]
    assert stored != "password"
    # And it is trivially recoverable, which is the point of naming the key that way.
    import base64

    assert base64.b64decode(stored) == b"password"


def test_forget_password_keeps_the_tokens(tmp_path):
    store = CredentialStore(tmp_path / "credentials.json")
    store.save_tokens(TokenSet(id_token="i", username="u@example.com"))
    store.save_password("u@example.com", "password")

    assert store.forget_password("u@example.com") is True
    account = store.load("u@example.com")
    assert account is not None
    assert account.password is None
    assert account.tokens is not None
    assert store.forget_password("u@example.com") is False


def test_a_stored_password_lets_an_expired_session_renew_itself(tmp_path):
    # The whole reason the password is stored: this pool rejects
    # REFRESH_TOKEN_AUTH, so renewal is a fresh SRP login or nothing.
    store = CredentialStore(tmp_path / "credentials.json")
    store.save_tokens(TokenSet(id_token="stale", username="u@example.com", expires_at=0))
    store.save_password("u@example.com", "password")

    auth = cognito([CHALLENGE, tokens_response()])
    auth.store = store
    account = store.load("u@example.com")
    assert account is not None
    auth.username, auth._password = account.username, account.password
    auth._tokens = account.tokens

    assert auth.id_token() != "stale"


def test_login_only_saves_the_password_when_asked(tmp_path):
    store = CredentialStore(tmp_path / "credentials.json")
    auth = cognito([CHALLENGE, tokens_response()])
    auth.store = store
    auth.login("u@example.com", "password")

    saved = store.load("u@example.com")
    assert saved is not None
    assert saved.password is None

    auth2 = cognito([CHALLENGE, tokens_response()])
    auth2.store = store
    auth2.save_password = True
    auth2.login("u@example.com", "password")
    reloaded = store.load("u@example.com")
    assert reloaded is not None
    assert reloaded.password == "password"


def test_store_returns_the_only_account_when_none_is_named(tmp_path):
    store = CredentialStore(tmp_path / "credentials.json")
    store.save_tokens(TokenSet(id_token="i", username="only@example.com"))
    assert store.load() is not None

    # A second account does not silently steal the default from the first.
    store.save_tokens(TokenSet(id_token="j", username="second@example.com"))
    still = store.load()
    assert still is not None
    assert still.username == "only@example.com"


def test_store_delete_removes_the_password_too(tmp_path):
    path = tmp_path / "credentials.json"
    store = CredentialStore(path)
    store.save_tokens(TokenSet(id_token="i", username="u@example.com"))
    store.save_password("u@example.com", "password")

    assert store.delete("u@example.com") is True
    assert store.load("u@example.com") is None
    assert PASSWORD_KEY not in path.read_text()
    assert store.delete("u@example.com") is False


def test_missing_or_corrupt_store_is_not_an_error(tmp_path):
    assert CredentialStore(tmp_path / "absent.json").load() is None
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not json")
    assert CredentialStore(corrupt).load() is None


def test_an_undecodable_password_is_treated_as_absent(tmp_path):
    path = tmp_path / "credentials.json"
    path.write_text(
        json.dumps({"u@example.com": {"id_token": "i", PASSWORD_KEY: "!!not base64!!"}})
    )
    account = CredentialStore(path).load("u@example.com")
    assert account is not None
    assert account.password is None


def test_several_accounts_resolve_to_the_default_not_to_nothing(tmp_path):
    # Logging in while another account is cached leaves two entries. An
    # unqualified load must take the recorded default rather than give up and
    # report no cached credentials at all.
    store = CredentialStore(tmp_path / "credentials.json")
    store.save_tokens(TokenSet(id_token="a", username="first@example.com"), make_default=True)
    store.save_tokens(TokenSet(id_token="b", username="second@example.com"), make_default=True)

    account = store.load()
    assert account is not None
    assert account.username == "second@example.com"
    assert store.default_username() == "second@example.com"


def test_default_can_be_switched(tmp_path):
    store = CredentialStore(tmp_path / "credentials.json")
    store.save_tokens(TokenSet(id_token="a", username="first@example.com"), make_default=True)
    store.save_tokens(TokenSet(id_token="b", username="second@example.com"), make_default=True)

    assert store.set_default("first@example.com") is True
    loaded = store.load()
    assert loaded is not None
    assert loaded.username == "first@example.com"
    assert store.set_default("nobody@example.com") is False


def test_deleting_the_default_does_not_strand_the_others(tmp_path):
    store = CredentialStore(tmp_path / "credentials.json")
    store.save_tokens(TokenSet(id_token="a", username="first@example.com"), make_default=True)
    store.save_tokens(TokenSet(id_token="b", username="second@example.com"), make_default=True)

    store.delete("second@example.com")
    account = store.load()
    assert account is not None
    assert account.username == "first@example.com"


def test_a_pre_versioned_flat_file_still_loads(tmp_path):
    # Files written before the format carried a default must keep working.
    path = tmp_path / "credentials.json"
    path.write_text(
        json.dumps({"only@example.com": {"id_token": "a", "username": "only@example.com"}})
    )
    store = CredentialStore(path)

    account = store.load()
    assert account is not None
    assert account.username == "only@example.com"

    # And it is rewritten in the versioned shape on the next save.
    store.save_tokens(TokenSet(id_token="b", username="only@example.com"), make_default=True)
    data = json.loads(path.read_text())
    assert data["version"] == 1
    assert data["default"] == "only@example.com"


def test_ambiguous_flat_file_reports_the_ambiguity(tmp_path):
    from icpc.facade.client import _stored_account

    path = tmp_path / "credentials.json"
    path.write_text(
        json.dumps({"a@example.com": {"id_token": "x"}, "b@example.com": {"id_token": "y"}})
    )
    with pytest.raises(errors.ConfigError, match="several accounts are cached"):
        _stored_account(CredentialStore(path), None)
