"""The token set and its expiry bookkeeping."""

from __future__ import annotations

import base64
import binascii
import json
import time
from dataclasses import dataclass
from typing import Any, Self

__all__ = ["TokenSet", "decode_jwt_claims"]

#: header.payload.signature
_JWT_PARTS = 3


def decode_jwt_claims(token: str) -> dict[str, Any]:
    """Read a JWT's payload without verifying it.

    We never validate the signature: Cognito issued it, we only hand it back. The
    claims are read for the username and the real expiry.
    """
    parts = token.split(".")
    if len(parts) != _JWT_PARTS:
        return {}
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    try:
        return json.loads(base64.urlsafe_b64decode(payload))
    except (binascii.Error, ValueError, UnicodeDecodeError):
        return {}


@dataclass(slots=True)
class TokenSet:
    """Cognito's ``AuthenticationResult``.

    Only :attr:`id_token` is accepted by icpc.global; the access token is not, which
    is a documented and surprising property of this API.
    """

    id_token: str
    #: Absent when the set came from a bare ``ICPC_ID_TOKEN``.
    refresh_token: str | None = None
    access_token: str | None = None
    #: Unix time at which ``id_token`` stops being valid.
    expires_at: float = 0.0
    username: str | None = None

    @classmethod
    def from_cognito(cls, result: dict[str, Any], *, refresh_token: str | None = None) -> Self:
        id_token = result["IdToken"]
        claims = decode_jwt_claims(id_token)
        expires_at = float(claims.get("exp") or (time.time() + result.get("ExpiresIn", 3600)))
        return cls(
            id_token=id_token,
            # REFRESH_TOKEN_AUTH responses omit the refresh token; carry the old one.
            refresh_token=result.get("RefreshToken") or refresh_token,
            access_token=result.get("AccessToken"),
            expires_at=expires_at,
            username=claims.get("email") or claims.get("cognito:username"),
        )

    def expired(self, margin: float = 60.0) -> bool:
        """True once the token is within ``margin`` seconds of expiring."""
        return time.time() >= self.expires_at - margin

    def to_dict(self) -> dict[str, Any]:
        return {
            "id_token": self.id_token,
            "refresh_token": self.refresh_token,
            "access_token": self.access_token,
            "expires_at": self.expires_at,
            "username": self.username,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id_token=data["id_token"],
            refresh_token=data.get("refresh_token"),
            access_token=data.get("access_token"),
            expires_at=float(data.get("expires_at", 0.0)),
            username=data.get("username"),
        )
