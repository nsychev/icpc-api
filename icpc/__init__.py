"""Unofficial client for the icpc.global API.

Read a whole contest in one call::

    from icpc import Icpc

    with Icpc.from_store() as icpc:
        teams = icpc.load_contest(1234)
        print(len(teams.teams), "teams")
"""

from icpc.config import Settings
from icpc.errors import ApiError, AuthError, IcpcError, SearchError
from icpc.facade.client import AsyncIcpc, Icpc, Include
from icpc.facade.domain import ContestView, Member, Team

__version__ = "0.2.0"

__all__ = [
    "ApiError",
    "AsyncIcpc",
    "AuthError",
    "ContestView",
    "Icpc",
    "IcpcError",
    "Include",
    "Member",
    "SearchError",
    "Settings",
    "Team",
    "__version__",
]
