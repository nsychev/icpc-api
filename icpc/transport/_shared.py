"""Logic common to both the sync and async transports."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

import httpx

from icpc import errors
from icpc.config import Settings

if TYPE_CHECKING:
    from icpc.transport.operation import Request

__all__ = [
    "auth_headers",
    "check_empty",
    "check_html",
    "raise_for_status",
    "retry_delay",
    "should_retry",
]

_RETRY_STATUSES = frozenset({429, 502, 503, 504})


def auth_headers(settings: Settings, token: str | None) -> dict[str, str]:
    headers = {"Accept": "application/json", "User-Agent": settings.user_agent}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def should_retry(response: httpx.Response, request: Request) -> bool:
    """Retry only idempotent requests, and only on transient statuses.

    Every write sets ``idempotent=False``: replaying ``POST /team/{id}`` would
    rewrite the object a second time.
    """
    return request.idempotent and response.status_code in _RETRY_STATUSES


def retry_delay(attempt: int, settings: Settings, response: httpx.Response | None = None) -> float:
    """Exponential backoff with full jitter, honouring ``Retry-After``."""
    if response is not None:
        header = response.headers.get("Retry-After")
        if header is not None:
            try:
                return min(float(header), settings.backoff_cap)
            except ValueError:
                pass
    ceiling = min(settings.backoff_base * (2**attempt), settings.backoff_cap)
    return random.uniform(0, ceiling)  # noqa: S311 - jitter, not cryptography


def _retry_after(response: httpx.Response) -> float | None:
    header = response.headers.get("Retry-After")
    if header is None:
        return None
    try:
        return float(header)
    except ValueError:
        return None


def raise_for_status(response: httpx.Response, request: Request) -> None:
    """Map a non-2xx response onto the exception hierarchy."""
    status = response.status_code
    if status < 400:
        return

    body = response.text
    args = (status, request.method, request.path, body)

    match status:
        case 400:
            raise errors.BadRequest(*args)
        case 401:
            raise errors.Unauthorized(*args)
        case 403:
            raise errors.Forbidden(*args)
        case 404:
            raise errors.NotFound(*args)
        case 405:
            raise errors.MethodNotAllowed(*args)
        case 409:
            raise errors.Conflict(*args)
        case 429:
            raise errors.RateLimited(*args, _retry_after(response))
        case _ if status >= 500:
            # The promote endpoint reports an ordinary conflict as a 500.
            if "cannot be promoted" in body:
                raise errors.TeamNotPromotable(*args)
            raise errors.ServerError(*args)
        case _:
            raise errors.ApiError(*args)


def check_empty(response: httpx.Response, request: Request) -> None:
    """Reject a 200 with no body.

    ``GET /contest/{id}`` answers an unknown id with 200 and an empty body rather
    than a 404. Left alone, that surfaces as an unhelpful JSON parse error.
    """
    if not response.content:
        raise errors.NotFound(
            404, request.method, request.path, "the server returned an empty body"
        )


def check_html(response: httpx.Response, request: Request) -> None:
    """Reject the SPA's ``index.html`` catch-all that is often returned instead of 404."""
    content_type = response.headers.get("content-type", "")
    if content_type.startswith("text/html"):
        raise errors.NotFound(
            404,
            request.method,
            request.path,
            "path does not exist",
        )
