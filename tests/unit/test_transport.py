"""Transport behaviour: error mapping, retries, the 401 replay, and the write gate."""

from __future__ import annotations

import httpx
import pytest

from icpc import errors
from icpc.api import contest as contest_api
from icpc.api import person as person_api
from icpc.api import public as public_api
from icpc.api import team as team_api
from icpc.config import Settings
from icpc.models.enums import TeamStatus
from icpc.transport.sync_client import Transport


class FakeAuth:
    """Hands out a token and counts how often it is asked for a fresh one."""

    def __init__(self) -> None:
        self.calls = 0
        self.invalidations = 0

    def id_token(self) -> str:
        self.calls += 1
        return f"token-{self.invalidations}"

    def invalidate(self) -> None:
        self.invalidations += 1


def transport(handler, *, settings: Settings | None = None, auth=None) -> Transport:
    resolved = settings or Settings(backoff_base=0.0, backoff_cap=0.0)
    return Transport(
        auth,
        settings=resolved,
        http=httpx.Client(
            base_url=resolved.base_url,
            transport=httpx.MockTransport(handler),
        ),
    )


def json_response(payload, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload)


def test_sends_the_bearer_token_and_parses_a_model():
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return json_response({"id": 7, "userName": "u", "firstName": "A", "lastName": "B"})

    person = transport(handler, auth=FakeAuth()).send(person_api.whoami())
    assert person.id == 7
    assert person.first_name == "A"
    assert seen[0].headers["authorization"] == "Bearer token-0"
    assert seen[0].url.path == "/api/person/info/basic"


def test_public_endpoints_send_no_authorization_header():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "authorization" not in request.headers
        return json_response([{"id": 1, "label": "NERC"}])

    rows = transport(handler, auth=FakeAuth()).send(public_api.regionals(2026))
    assert rows[0].label == "NERC"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (400, errors.BadRequest),
        (403, errors.Forbidden),
        (404, errors.NotFound),
        (405, errors.MethodNotAllowed),
        (500, errors.ServerError),
    ],
)
def test_statuses_map_to_the_exception_hierarchy(status, expected):
    client = transport(lambda _: json_response({"message": "nope"}, status))
    with pytest.raises(expected):
        client.send(contest_api.get(9180))


def test_server_error_keeps_the_opaque_support_code():
    body = {"message": "Please contact support with error code (acea61e1)."}
    client = transport(lambda _: json_response(body, 500))
    with pytest.raises(errors.ServerError) as caught:
        client.send(contest_api.get(9180))
    assert caught.value.error_code == "acea61e1"


def test_html_catch_all_is_reported_as_a_missing_path():
    # A path that does not exist is answered by the SPA with 200 text/html.
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text="<!doctype html><html>", headers={"content-type": "text/html"}
        )

    with pytest.raises(errors.NotFound, match="path does not exist"):
        transport(handler).send(contest_api.get(9180))


def test_401_triggers_exactly_one_reauth_and_replay():
    auth = FakeAuth()
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.headers["authorization"])
        if len(calls) == 1:
            return json_response({"message": "expired"}, 401)
        return json_response({"id": 1, "userName": "u", "firstName": "A", "lastName": "B"})

    result = transport(handler, auth=auth).send(person_api.whoami())
    assert result.id == 1
    assert auth.invalidations == 1
    assert calls == ["Bearer token-0", "Bearer token-1"]


def test_a_second_401_is_not_retried_forever():
    auth = FakeAuth()
    client = transport(lambda _: json_response({"message": "no"}, 401), auth=auth)
    with pytest.raises(errors.Unauthorized):
        client.send(person_api.whoami())
    assert auth.invalidations == 1


def test_transient_statuses_are_retried_for_reads():
    attempts = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] < 3:
            return json_response({"message": "busy"}, 503)
        return json_response({"id": 9180, "name": "NERC"})

    contest = transport(handler).send(contest_api.get(9180))
    assert contest.name == "NERC"
    assert attempts["n"] == 3


def test_writes_are_never_retried():
    # The one real protection a write gets: replaying it would apply it twice.
    attempts = {"n": 0}

    def handler(_: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return json_response({"message": "busy"}, 503)

    settings = Settings(backoff_base=0.0, backoff_cap=0.0)
    client = transport(handler, settings=settings)
    with pytest.raises(errors.ServerError):
        client.send(team_api.bulk_update_status(9180, [1], TeamStatus.ACCEPTED))
    assert attempts["n"] == 1


def test_every_write_is_marked_non_idempotent():
    writes = [
        team_api.replace(1, {}),
        team_api.bulk_update_status(9180, [1], TeamStatus.ACCEPTED),
        team_api.promote(1, 2),
        team_api.upload_file(1, "x.pdf", b"%PDF"),
        team_api.delete_file(1),
    ]
    assert [op.request.idempotent for op in writes] == [False] * len(writes)


def test_promote_conflict_gets_its_own_exception():
    body = {"message": "The team cannot be promoted, please check the target site for conflicts"}
    settings = Settings(backoff_base=0.0, backoff_cap=0.0)
    client = transport(lambda _: json_response(body, 500), settings=settings)
    with pytest.raises(errors.TeamNotPromotable):
        client.send(team_api.promote(1107579, 38055))


def test_bulk_update_sends_the_documented_body():
    seen: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.content)
        return json_response({})

    settings = Settings()
    transport(handler, settings=settings).send(
        team_api.bulk_update_status(9180, [1, 2], TeamStatus.CANCELED)
    )
    assert b'"newStatus":"CANCELED"' in seen[0].replace(b" ", b"")
    assert b'"teamIds":[1,2]' in seen[0].replace(b" ", b"")


def test_timeouts_become_transport_errors():
    def handler(_: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("too slow")

    with pytest.raises(errors.TransportError):
        transport(handler).send(contest_api.get(9180))


def test_an_empty_200_body_is_reported_as_not_found():
    # GET /contest/<unknown id> answers 200 with no body at all, not a 404.
    # Parsing that as JSON would raise something unhelpful.
    client = transport(lambda _: httpx.Response(200, content=b""))
    with pytest.raises(errors.NotFound, match="empty body"):
        client.send(contest_api.get(999999999))


def test_writes_may_answer_with_an_empty_body():
    settings = Settings()
    client = transport(lambda _: httpx.Response(200, content=b""), settings=settings)
    assert client.send(team_api.promote(1107579, 38055)) is None


def test_promote_builds_the_url():
    # The team comes first in the path, the target site second.
    request = team_api.promote(1102744, 39719).request
    assert request.path == "/team/1102744/promote/39719"
    assert request.method == "POST"
    assert request.json is None
    assert request.idempotent is False


def test_already_promoted_is_reported_as_a_conflict_not_a_server_fault():
    # A team already in the target contest gets a 500 carrying this body, which
    # is an ordinary refusal rather than a fault.
    body = "The team cannot be promoted, please check the target site for conflicts"
    settings = Settings(backoff_base=0.0, backoff_cap=0.0)
    client = transport(lambda _: httpx.Response(500, json={"message": body}), settings=settings)
    with pytest.raises(errors.TeamNotPromotable):
        client.send(team_api.promote(1102744, 39719))
