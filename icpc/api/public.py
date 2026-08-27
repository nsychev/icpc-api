"""``/contest/public`` — the endpoints that need no token.

Their requests set ``auth=False``, so a client built with no credentials at all can
still reach them.
"""

from __future__ import annotations

from icpc.models.entities import ContestUnder, PublicContest, RegionalRef, StandingRow
from icpc.search.dsl import Q
from icpc.transport.operation import Operation, Request, list_op, model_op

__all__ = ["contest", "contests_under", "regionals", "standings"]


def regionals(year: int) -> Operation[list[RegionalRef]]:
    """The regional contests of a season."""
    return list_op(Request("GET", f"/contest/public/regionals/{year}", auth=False), RegionalRef)


def contests_under(contest_id: int) -> Operation[list[ContestUnder]]:
    """Sub-contests of a contest, with registration counts."""
    return list_op(
        Request("GET", f"/contest/public/contests-under/{contest_id}", auth=False), ContestUnder
    )


def contest(abbreviation: str) -> Operation[PublicContest]:
    """A contest by *abbreviation*, not id.

    The abbreviation is sometimes year-suffixed (``NERC-2026``); a plain one that
    404s is usually worth retrying with the season appended.
    """
    return model_op(Request("GET", f"/contest/public/{abbreviation}", auth=False), PublicContest)


def standings(contest_id: int, *, page: int = 1, size: int = 1000) -> Operation[list[StandingRow]]:
    """Published standings for a contest.

    This is a search endpoint like the authenticated ones, but the empty projection
    is what the public pages send, and it returns the default columns.
    """
    return list_op(
        Request(
            "GET",
            f"/contest/public/search/contest/{contest_id}",
            params={"q": Q().render(), "page": page, "size": size},
            auth=False,
        ),
        StandingRow,
    )


def schedules(contest_id: int) -> Operation[list[dict[str, object]]]:
    """The contest's published schedule entries."""
    return list_op(
        Request("GET", f"/contest/public/{contest_id}/schedules", auth=False), dict[str, object]
    )


def regional_results(year: int) -> Operation[list[dict[str, object]]]:
    """The regional results tree for a season, contests nested under their parents."""
    return list_op(
        Request("GET", f"/contest/public/regionalresults/{year}", auth=False), dict[str, object]
    )
