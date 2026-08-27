"""Static configuration for the client.

The Cognito pool parameters belong to icpc.global's public SPA app client.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import httpx

__all__ = ["COGNITO_URL", "Settings"]

REGION = "us-east-1"
USER_POOL_ID = "us-east-1_WaDOo4Gqm"
CLIENT_ID = "6q2fe6opm0m24eoebqf9vj4emd"
COGNITO_URL = f"https://cognito-idp.{REGION}.amazonaws.com/"

BASE_URL = "https://icpc.global/api"

#: Page size the frontend's largest grid offers. The server accepts more, but this
#: is the biggest value known to be exercised in production.
DEFAULT_PAGE_SIZE = 1000


def _default_timeout() -> httpx.Timeout:
    return httpx.Timeout(connect=5.0, read=30.0, write=30.0, pool=5.0)


@dataclass(frozen=True, slots=True)
class Settings:
    """Tunables shared by the async and sync clients.

    The concurrency and retry defaults are deliberately conservative: this is
    someone else's production system, not ours.
    """

    base_url: str = BASE_URL
    cognito_url: str = COGNITO_URL
    user_pool_id: str = USER_POOL_ID
    client_id: str = CLIENT_ID

    timeout: httpx.Timeout = field(default_factory=_default_timeout)
    #: Read timeout used for exports and large search pages.
    slow_read_timeout: float = 120.0

    max_attempts: int = 3
    backoff_base: float = 0.5
    backoff_cap: float = 8.0

    #: Concurrent in-flight requests allowed by the client.
    max_concurrency: int = 4

    #: Renew the id token this many seconds before it actually expires.
    refresh_margin: float = 60.0

    user_agent: str = "icpc-api"
