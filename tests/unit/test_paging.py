"""Auto-paging, projection validation, and the async client's parallel fetch."""

from __future__ import annotations

import httpx
import pytest

from icpc.errors import EmptyProjection, SearchError
from icpc.facade.client import AsyncIcpc, Icpc
from icpc.search import Q, contest_teams
from icpc.transport.async_client import AsyncTransport
from icpc.transport.sync_client import Transport

TOTAL = 2500
PAGE = 1000


def paged_handler(calls: list[httpx.Request]):
    """Serve ``TOTAL`` fake teams, plus the sibling ``/count``."""

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/count"):
            # The list response carries no total; this is where it comes from.
            return httpx.Response(200, json=TOTAL)
        page = int(request.url.params["page"])
        size = int(request.url.params["size"])
        start = (page - 1) * size
        rows = [{"id": i, "name": f"Team {i}"} for i in range(start, min(start + size, TOTAL))]
        return httpx.Response(200, json=rows)

    return handler


def test_sync_all_pages_until_the_count_is_covered():
    calls: list[httpx.Request] = []
    client = Icpc(
        Transport(
            http=httpx.Client(
                base_url="https://icpc.global/api",
                transport=httpx.MockTransport(paged_handler(calls)),
            )
        )
    )
    rows = client.all(contest_teams(9180), size=PAGE)
    assert len(rows) == TOTAL
    assert [r.id for r in rows[:2]] == [0, 1]
    # One /count plus three pages.
    assert len(calls) == 4


def test_max_rows_stops_early():
    calls: list[httpx.Request] = []
    client = Icpc(
        Transport(
            http=httpx.Client(
                base_url="https://icpc.global/api",
                transport=httpx.MockTransport(paged_handler(calls)),
            )
        )
    )
    rows = client.all(contest_teams(9180), size=PAGE, max_rows=1500)
    assert len(rows) == 1500


def test_iter_stops_on_the_first_short_page():
    calls: list[httpx.Request] = []
    client = Icpc(
        Transport(
            http=httpx.Client(
                base_url="https://icpc.global/api",
                transport=httpx.MockTransport(paged_handler(calls)),
            )
        )
    )
    ids = [row.id for row in client.iter(contest_teams(9180), size=PAGE)]
    assert len(ids) == TOTAL
    # No /count call at all: streaming needs only the short-page signal.
    assert all(not c.url.path.endswith("/count") for c in calls)


@pytest.mark.asyncio
async def test_async_all_matches_the_sync_result():
    calls: list[httpx.Request] = []
    transport = AsyncTransport(
        http=httpx.AsyncClient(
            base_url="https://icpc.global/api",
            transport=httpx.MockTransport(paged_handler(calls)),
        )
    )
    async with AsyncIcpc(transport) as client:
        rows = await client.all(contest_teams(9180), size=PAGE)
    assert [r.id for r in rows] == list(range(TOTAL))


def test_page_numbers_are_one_based():
    calls: list[httpx.Request] = []
    client = Icpc(
        Transport(
            http=httpx.Client(
                base_url="https://icpc.global/api",
                transport=httpx.MockTransport(paged_handler(calls)),
            )
        )
    )
    client.page(contest_teams(9180), size=10)
    assert calls[0].url.params["page"] == "1"


def test_an_unknown_projection_column_is_refused_before_the_request():
    # The server would silently return null for it, which is worse than an error.
    with pytest.raises(EmptyProjection, match="teamNmae"):
        contest_teams(9180).query(proj=["id", "teamNmae"])


def test_an_entirely_invalid_projection_is_refused():
    # This one would be a 500 server-side.
    with pytest.raises(EmptyProjection, match="500"):
        contest_teams(9180).query(proj=["nope"])


def test_default_query_uses_the_grids_own_projection():
    # Not every column: six grids answer 500 when asked for their full field set,
    # while every grid accepts the columns its own UI requests.
    endpoint = contest_teams(9180)
    assert endpoint.query().proj == endpoint.default_proj


def test_filter_and_sort_columns_are_added_to_the_projection():
    # A filter on an unprojected column is silently ignored by the server, so the
    # column has to be projected for the filter to mean anything.
    endpoint = contest_teams(9180)
    f = endpoint.fields
    q = endpoint.query(proj=["id"], filters=[f.status.eq("ACCEPTED")], sort=[f.rank.desc()])
    assert q.proj == ("id", "status", "rank")


def test_a_filter_on_an_unprojected_column_is_refused():
    endpoint = contest_teams(9180)
    f = endpoint.fields
    bad = Q.build(["id"], [f.status.eq("ACCEPTED")])
    with pytest.raises(SearchError, match="not in the projection"):
        endpoint.rows(bad)


def test_a_sort_on_an_unprojected_column_is_refused():
    endpoint = contest_teams(9180)
    bad = Q.build(["id"], sort=[endpoint.fields.name.asc()])
    with pytest.raises(SearchError, match="ordering would be ignored"):
        endpoint.count(bad)


def test_count_uses_the_sibling_path():
    assert contest_teams(9180).count().request.path == "/contest/search/contest/9180/team/count"


def test_export_asks_for_a_file():
    request = contest_teams(9180).export().request
    assert request.path.endswith("/export")
    assert request.params["type"] == "CSV"
    assert request.slow is True
