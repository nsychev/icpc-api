"""Cognito RPCs over plain HTTP — no boto3, no AWS credentials.

``InitiateAuth`` and ``RespondToAuthChallenge`` are unsigned operations on a public
app client, so they are ordinary JSON-1.1 POSTs. This module holds the pure request
builders and response parsing; :mod:`icpc.auth.flows` drives them over httpx.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from icpc import errors
from icpc.auth.srp import SrpSession
from icpc.auth.tokens import TokenSet
from icpc.config import Settings

__all__ = ["Challenge", "CognitoCall", "Outcome", "parse_outcome"]

_TARGET = "AWSCognitoIdentityProviderService"

PASSWORD_VERIFIER = "PASSWORD_VERIFIER"
SOFTWARE_TOKEN_MFA = "SOFTWARE_TOKEN_MFA"
SMS_MFA = "SMS_MFA"
NEW_PASSWORD_REQUIRED = "NEW_PASSWORD_REQUIRED"

#: First HTTP status Cognito uses to signal a failure.
_HTTP_ERROR = 400


@dataclass(frozen=True, slots=True)
class CognitoCall:
    """A single JSON-1.1 RPC: where to send it and what to send."""

    target: str
    payload: dict[str, Any]

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": f"{_TARGET}.{self.target}",
        }


@dataclass(frozen=True, slots=True)
class Challenge:
    """Cognito wants another round trip before it will issue tokens."""

    name: str
    session: str
    parameters: dict[str, str]


#: Either we got tokens, or we owe Cognito another answer.
type Outcome = TokenSet | Challenge


def initiate_srp(settings: Settings, srp: SrpSession) -> CognitoCall:
    """Step 1 of the password login.

    icpc.global's pool uses ``CUSTOM_AUTH`` with ``CHALLENGE_NAME: SRP_A`` rather
    than the more usual ``USER_SRP_AUTH``; it answers with ``PASSWORD_VERIFIER``.
    """
    return CognitoCall(
        "InitiateAuth",
        {
            "AuthFlow": "CUSTOM_AUTH",
            "ClientId": settings.client_id,
            "AuthParameters": srp.auth_parameters(),
        },
    )


def respond_password_verifier(
    settings: Settings, responses: dict[str, str], session: str
) -> CognitoCall:
    """Step 2: the SRP proof. ``Session`` must be echoed back for ``CUSTOM_AUTH``."""
    return CognitoCall(
        "RespondToAuthChallenge",
        {
            "ClientId": settings.client_id,
            "ChallengeName": PASSWORD_VERIFIER,
            "ChallengeResponses": responses,
            "Session": session,
        },
    )


def respond_mfa(settings: Settings, challenge: Challenge, username: str, code: str) -> CognitoCall:
    """Answer a software-token or SMS MFA challenge."""
    key = "SOFTWARE_TOKEN_MFA_CODE" if challenge.name == SOFTWARE_TOKEN_MFA else "SMS_MFA_CODE"
    return CognitoCall(
        "RespondToAuthChallenge",
        {
            "ClientId": settings.client_id,
            "ChallengeName": challenge.name,
            "ChallengeResponses": {"USERNAME": username, key: code},
            "Session": challenge.session,
        },
    )


def refresh(settings: Settings, refresh_token: str) -> CognitoCall:
    """Renew the id token. Needs no password and no AWS credentials."""
    return CognitoCall(
        "InitiateAuth",
        {
            "AuthFlow": "REFRESH_TOKEN_AUTH",
            "ClientId": settings.client_id,
            "AuthParameters": {"REFRESH_TOKEN": refresh_token},
        },
    )


def parse_outcome(payload: dict[str, Any], *, refresh_token: str | None = None) -> Outcome:
    """Turn a Cognito response into tokens or the next challenge."""
    result = payload.get("AuthenticationResult")
    if result:
        return TokenSet.from_cognito(result, refresh_token=refresh_token)

    name = payload.get("ChallengeName")
    if name is None:
        raise errors.CognitoError("UnexpectedResponse", f"no tokens and no challenge: {payload}")
    if name == NEW_PASSWORD_REQUIRED:
        raise errors.AuthError("Cognito requires a password change before this account can log in")
    return Challenge(
        name=name,
        session=payload.get("Session", ""),
        parameters=payload.get("ChallengeParameters", {}),
    )


def raise_for_error(status: int, payload: dict[str, Any]) -> None:
    """Map a Cognito error body onto :mod:`icpc.errors`."""
    if status < _HTTP_ERROR:
        return
    code = str(payload.get("__type", "CognitoError")).rsplit("#", 1)[-1]
    message = str(payload.get("message", payload))
    if code in {"NotAuthorizedException", "UserNotFoundException"}:
        raise errors.InvalidCredentials(f"{code}: {message}")
    raise errors.CognitoError(code, message)
