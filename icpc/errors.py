"""Exception hierarchy.

Client-side problems (`SearchError` and friends) are raised *before* a request goes
out; everything under `ApiError` carries the real HTTP response.
"""

from __future__ import annotations

import re

__all__ = [
    "ApiError",
    "AuthError",
    "BadRequest",
    "CognitoError",
    "ConfigError",
    "Conflict",
    "EmptyProjection",
    "Forbidden",
    "IcpcError",
    "InvalidCredentials",
    "InvalidFilterValue",
    "MethodNotAllowed",
    "MfaRequired",
    "NotFound",
    "RateLimited",
    "SearchError",
    "ServerError",
    "TokenExpired",
    "TransportError",
    "Unauthorized",
]

_ERROR_CODE = re.compile(r"error code \(([0-9a-f]+)\)")


class IcpcError(Exception):
    """Base class for every error raised by this package."""


class ConfigError(IcpcError):
    """Missing or contradictory configuration (no credentials, unknown profile)."""


# --------------------------------------------------------------------- auth --


class AuthError(IcpcError):
    """Authentication or token management failed."""


class InvalidCredentials(AuthError):
    """Cognito rejected the username/password pair."""


class MfaRequired(AuthError):
    """Cognito wants a software-token MFA code to finish the login."""

    def __init__(self, challenge: str, session: str, username: str) -> None:
        super().__init__(f"MFA challenge {challenge} required for {username}")
        self.challenge = challenge
        self.session = session
        self.username = username


class TokenExpired(AuthError):
    """The id token expired and could not be renewed."""


class CognitoError(AuthError):
    """A Cognito RPC returned an error body."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


# ---------------------------------------------------------------- transport --


class TransportError(IcpcError):
    """The request never produced a response (connection, TLS or timeout)."""


# ---------------------------------------------------------------------- api --


class ApiError(IcpcError):
    """A non-2xx response from icpc.global."""

    def __init__(self, status: int, method: str, path: str, body: str) -> None:
        super().__init__(f"HTTP {status} {method} {path}: {body[:400]}")
        self.status = status
        self.method = method
        self.path = path
        self.body = body


class BadRequest(ApiError):
    """400 — usually a missing or malformed ``q``."""


class Unauthorized(ApiError):
    """401 — the id token was rejected even after a refresh."""


class Forbidden(ApiError):
    """403 — authenticated, but not entitled to this contest or team."""


class NotFound(ApiError):
    """404."""


class MethodNotAllowed(ApiError):
    """405 — the path exists but not under this verb."""


class Conflict(ApiError):
    """409."""


class RateLimited(ApiError):
    """429."""

    def __init__(
        self, status: int, method: str, path: str, body: str, retry_after: float | None
    ) -> None:
        super().__init__(status, method, path, body)
        self.retry_after = retry_after


class ServerError(ApiError):
    """5xx. ICPC's 500 bodies carry an opaque hex code worth quoting to support."""

    def __init__(self, status: int, method: str, path: str, body: str) -> None:
        super().__init__(status, method, path, body)
        match = _ERROR_CODE.search(body)
        self.error_code: str | None = match.group(1) if match else None


class TeamNotPromotable(ServerError):
    """``POST /team/{id}/promote/{siteId}`` refused: already promoted, or site conflict."""


# ------------------------------------------------------------------- search --


class SearchError(IcpcError):
    """The search query is invalid; raised before the request is sent."""


class InvalidFilterValue(SearchError):
    """A filter value contains a character the ``q`` grammar cannot escape."""


class EmptyProjection(SearchError):
    """A projection naming no valid field would 500 server-side."""
