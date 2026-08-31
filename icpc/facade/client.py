"""The clients users actually reach for.

``AsyncIcpc`` and ``Icpc`` are thin: they own a transport and an authenticator, add
auto-paging on top of :class:`~icpc.search.endpoint.SearchEndpoint`, and expose the
one join that needs several requests. Everything else is a low-level operation from
:mod:`icpc.api`, sent through ``send()``.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator, Iterable, Iterator
from enum import Flag, auto
from typing import Any, Self

from icpc import errors
from icpc.api import contest as contest_api
from icpc.api import person as person_api
from icpc.api import survey as survey_api
from icpc.api import team as team_api
from icpc.api.person import ReferenceRole
from icpc.auth.flows import AsyncCognitoAuth, CognitoAuth, StaticTokenAuth, SyncStaticTokenAuth
from icpc.auth.store import Account, CredentialStore
from icpc.auth.tokens import TokenSet
from icpc.config import DEFAULT_PAGE_SIZE, Settings
from icpc.facade.domain import ContestView, join
from icpc.models.entities import ContestReference, PersonBasic, Team
from icpc.models.surveys import SurveyResponseRow
from icpc.search import _generated as endpoints
from icpc.search.dsl import Q
from icpc.search.endpoint import SearchEndpoint
from icpc.search.surveys import survey_responses
from icpc.transport.async_client import AsyncTransport
from icpc.transport.operation import Operation
from icpc.transport.sync_client import Transport

__all__ = ["AsyncIcpc", "Icpc", "Include"]


def _full(endpoint: SearchEndpoint[Any, Any]) -> Q:
    """Every column of a grid.

    The join needs columns the grid's default projection leaves out — ``instId``
    to attach an institution, ``teamId`` to attach a roster — and asking for the
    full set costs nothing extra on the wire. The four grids used by
    :meth:`AsyncIcpc.load_contest` all accept their full field set; some others
    do not, which is why this is not the global default.
    """
    return endpoint.query(proj=endpoint.all_fields)


def _stored_account(store: CredentialStore, username: str | None) -> Account:
    """Load an account, failing with a message that says what is actually wrong."""
    account = store.load(username)
    if account is not None:
        return account
    known = store.usernames()
    if username is not None:
        raise errors.ConfigError(
            f"no cached credentials for {username}"
            + (f"; cached: {', '.join(known)}" if known else "; run `icpc auth login`")
        )
    if known:
        # Several accounts and no recorded default: say so instead of claiming
        # nothing is cached, which is what a fresh login looks like otherwise.
        raise errors.ConfigError(
            f"several accounts are cached ({', '.join(known)}) and none is the "
            f"default; pass --user/username=, or run `icpc auth use <username>`"
        )
    raise errors.ConfigError("no cached credentials; run `icpc auth login` first")


class Include(Flag):
    """Which tables :meth:`AsyncIcpc.load_contest` should fetch.

    Each one is a separate search over the whole contest, so ask only for what you
    need. ``TEAMS`` is implied by everything else.
    """

    TEAMS = auto()
    MEMBERS = auto()
    INSTITUTIONS = auto()
    PARTICIPANTS = auto()
    METADATA = auto()
    #: Every survey of the contest, and every response to each.
    SURVEYS = auto()

    #: Teams, rosters, institutions and contest metadata — not the participant table.
    DEFAULT = TEAMS | MEMBERS | INSTITUTIONS | METADATA
    ALL = TEAMS | MEMBERS | INSTITUTIONS | PARTICIPANTS | METADATA | SURVEYS

    @classmethod
    def named(cls, names: Iterable[str]) -> Include:
        """The union of the flags called ``names``, case-insensitively.

        The names are the flags' own, lowercased — the vocabulary a caller
        deciding tables from data works in, rather than one it has to keep in
        step by hand. ``default`` and ``all`` are accepted too.

        Raises :class:`ValueError` naming the tables, which a lookup by
        attribute cannot do: it would answer the same for a typo as for a
        method, and say nothing about what was allowed.
        """
        include = cls(0)
        for name in names:
            try:
                include |= cls[name.upper()]
            except KeyError:
                raise ValueError(
                    f"unknown table {name!r}; pick from "
                    f"{', '.join(flag.name.lower() for flag in cls if flag.name)}, default, all"
                ) from None
        return include


def _resolve_credentials(
    username: str | None, password: str | None
) -> tuple[str | None, str | None]:
    return (
        username or os.environ.get("ICPC_USERNAME"),
        password or os.environ.get("ICPC_PASSWORD"),
    )


class AsyncIcpc:
    """Asynchronous client."""

    def __init__(self, transport: AsyncTransport) -> None:
        self._t = transport

    # ------------------------------------------------------- construction --

    @classmethod
    def from_password(
        cls,
        username: str | None = None,
        password: str | None = None,
        *,
        store: CredentialStore | None = None,
        settings: Settings | None = None,
    ) -> Self:
        """Log in with an email and password over Cognito SRP.

        Nothing is sent until the first request; the login happens lazily. Falls
        back to ``ICPC_USERNAME`` / ``ICPC_PASSWORD``.
        """
        resolved = settings or Settings()
        user, secret = _resolve_credentials(username, password)
        if not user or not secret:
            raise errors.ConfigError("username and password are required")
        auth = AsyncCognitoAuth(username=user, password=secret, store=store, settings=resolved)
        return cls(AsyncTransport(auth, settings=resolved))

    @classmethod
    def from_token(
        cls,
        id_token: str | None = None,
        *,
        refresh_token: str | None = None,
        settings: Settings | None = None,
    ) -> Self:
        """Use an existing token.

        With only an id token there is no renewal and it stops working an hour
        after Cognito issued it; a refresh token is renewable indefinitely.
        """
        resolved = settings or Settings()
        id_token = id_token or os.environ.get("ICPC_ID_TOKEN")
        refresh_token = refresh_token or os.environ.get("ICPC_REFRESH_TOKEN")
        if refresh_token:
            tokens = TokenSet(id_token=id_token or "", refresh_token=refresh_token)
            return cls(
                AsyncTransport(
                    AsyncCognitoAuth(tokens=tokens, settings=resolved), settings=resolved
                )
            )
        if not id_token:
            raise errors.ConfigError("pass id_token or refresh_token, or set ICPC_ID_TOKEN")
        return cls(AsyncTransport(StaticTokenAuth(id_token), settings=resolved))

    @classmethod
    def from_store(
        cls,
        username: str | None = None,
        *,
        store: CredentialStore | None = None,
        settings: Settings | None = None,
    ) -> Self:
        """Use the tokens cached by ``icpc auth login``."""
        resolved = settings or Settings()
        token_store = store or CredentialStore()
        account = _stored_account(token_store, username)
        auth = AsyncCognitoAuth(
            username=account.username,
            password=account.password,
            tokens=account.tokens,
            store=token_store,
            settings=resolved,
        )
        return cls(AsyncTransport(auth, settings=resolved))

    @classmethod
    def anonymous(cls, *, settings: Settings | None = None) -> Self:
        """A client with no credentials, for ``/contest/public/*`` only."""
        return cls(AsyncTransport(None, settings=settings or Settings()))

    # ------------------------------------------------------------ requests --

    async def send[T](self, operation: Operation[T]) -> T:
        """Issue one operation and return its typed result."""
        return await self._t.send(operation)

    async def whoami(self) -> PersonBasic:
        """The account behind the current token."""
        return await self.send(person_api.whoami())

    async def id_token(self) -> str:
        """The current bearer token, refreshing it first if it is stale.

        Useful for handing the session to another tool. Treat it as a password.
        """
        if self._t.auth is None:
            raise errors.ConfigError("this client has no credentials")
        return await self._t.auth.id_token()

    async def my_contests(
        self, icpc_year: int, role: ReferenceRole | str = ReferenceRole.CONTEST_MANAGER
    ) -> list[ContestReference]:
        """Contests the signed-in account is attached to, for one ICPC season.

        With the default role this is the list of contests you can administer —
        what the icpc.global cabinet shows on its front page.

        ``icpc_year`` is the ICPC year, not the calendar year: a contest held in
        2026 belongs to season 2027.
        """
        me = await self.whoami()
        if me.id is None:
            raise errors.ConfigError("could not determine the signed-in person id")
        return await self.send(person_api.references(me.id, icpc_year, role))

    # -------------------------------------------------------------- search --

    async def count[R, F](self, endpoint: SearchEndpoint[R, F], q: Q | None = None) -> int:
        """How many rows the query matches."""
        return await self.send(endpoint.count(q))

    async def page[R, F](
        self,
        endpoint: SearchEndpoint[R, F],
        q: Q | None = None,
        *,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
    ) -> list[R]:
        """One page of results, 1-based."""
        return await self.send(endpoint.rows(q, page=page, size=size))

    async def all[R, F](
        self,
        endpoint: SearchEndpoint[R, F],
        q: Q | None = None,
        *,
        size: int = DEFAULT_PAGE_SIZE,
        max_rows: int | None = None,
    ) -> list[R]:
        """Every matching row, fetching pages until the total is covered.

        The total comes from the ``/count`` sibling, which is fetched alongside the
        first page. The data is live, so a row added between calls can shift the
        pages; :meth:`iter` has the same caveat.
        """
        query = q if q is not None else endpoint.query()
        total, first = await asyncio.gather(
            self.send(endpoint.count(query)),
            self.send(endpoint.rows(query, page=1, size=size)),
        )
        rows = list(first)
        limit = total if max_rows is None else min(total, max_rows)
        if len(rows) >= limit or not first:
            return rows[:limit]

        remaining = range(2, (limit + size - 1) // size + 1)
        gate = asyncio.Semaphore(self._t.settings.max_concurrency)

        async def fetch(number: int) -> list[R]:
            async with gate:
                return await self.send(endpoint.rows(query, page=number, size=size))

        for chunk in await asyncio.gather(*(fetch(n) for n in remaining)):
            rows.extend(chunk)
        return rows[:limit]

    async def iter[R, F](
        self,
        endpoint: SearchEndpoint[R, F],
        q: Q | None = None,
        *,
        size: int = DEFAULT_PAGE_SIZE,
    ) -> AsyncIterator[R]:
        """Stream results, one page at a time, stopping on the first short page."""
        query = q if q is not None else endpoint.query()
        number = 1
        while True:
            rows = await self.send(endpoint.rows(query, page=number, size=size))
            for row in rows:
                yield row
            if len(rows) < size:
                return
            number += 1

    async def _all_columns[R, F](self, endpoint: SearchEndpoint[R, F]) -> list[R]:
        return await self.all(endpoint, _full(endpoint))

    async def _survey_rows(self, contest_id: int) -> list[SurveyResponseRow]:
        """Every response to every survey of a contest, in one flat list.

        Two stages, because responses are keyed by survey rather than by
        contest: list the surveys, then fetch each one's rows.
        """
        surveys = await self.send(survey_api.for_contest(contest_id))
        ids = [s.id for s in surveys if s.id is not None]
        if not ids:
            return []
        fetched = await asyncio.gather(*(self.all(survey_responses(i)) for i in ids))
        return [row for rows in fetched for row in rows]

    # ------------------------------------------------------ joined contest --

    async def load_contest(
        self, contest_id: int, include: Include = Include.DEFAULT
    ) -> ContestView:
        """Fetch a contest's tables in parallel and join them.

        This is the unified search: one call replaces the four separate grid
        queries plus the manual stitching every consumer would otherwise write.
        """
        async with asyncio.TaskGroup() as group:
            teams = group.create_task(self._all_columns(endpoints.contest_teams(contest_id)))
            metadata = (
                group.create_task(self.send(contest_api.get(contest_id)))
                if Include.METADATA in include
                else None
            )
            sites = (
                group.create_task(self.send(contest_api.sites(contest_id)))
                if Include.METADATA in include
                else None
            )
            members = (
                group.create_task(self._all_columns(endpoints.contest_team_members(contest_id)))
                if Include.MEMBERS in include
                else None
            )
            institutions = (
                group.create_task(self._all_columns(endpoints.contest_institutions(contest_id)))
                if Include.INSTITUTIONS in include
                else None
            )
            participants = (
                group.create_task(self._all_columns(endpoints.contest_participants(contest_id)))
                if Include.PARTICIPANTS in include
                else None
            )
            surveys = (
                group.create_task(self._survey_rows(contest_id))
                if Include.SURVEYS in include
                else None
            )

        return join(
            teams.result(),
            contest=metadata.result() if metadata else None,
            sites=sites.result() if sites else (),
            members=members.result() if members else (),
            institutions=institutions.result() if institutions else (),
            participants=participants.result() if participants else (),
            survey_responses=surveys.result() if surveys else (),
        )

    # -------------------------------------------------------------- writes --

    async def update_team(self, team_id: int, **changes: Any) -> Team:
        """Read a team, apply ``changes``, and write the whole object back.

        ``POST /team/{id}`` is a full-object replace, not a patch, so this reads
        the team first and sends it back with ``changes`` applied. The server
        recomputes the team's eligibility as a result and drops any verified
        status — the web UI warns about the same thing before saving.

        Returns the team as the server reports it afterwards, so the caller can
        see whatever else moved.
        """
        current = await self.send(team_api.get(team_id))
        payload = current.model_dump(by_alias=True, exclude_none=False)
        payload.update(changes)
        await self.send(team_api.replace(team_id, payload))
        return await self.send(team_api.get(team_id))

    # ------------------------------------------------------------ lifetime --

    async def aclose(self) -> None:
        await self._t.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()


class Icpc:
    """Synchronous client. Same surface as :class:`AsyncIcpc`, minus the streaming."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    # ------------------------------------------------------- construction --

    @classmethod
    def from_password(
        cls,
        username: str | None = None,
        password: str | None = None,
        *,
        store: CredentialStore | None = None,
        settings: Settings | None = None,
    ) -> Self:
        """Log in with an email and password over Cognito SRP."""
        resolved = settings or Settings()
        user, secret = _resolve_credentials(username, password)
        if not user or not secret:
            raise errors.ConfigError("username and password are required")
        auth = CognitoAuth(username=user, password=secret, store=store, settings=resolved)
        return cls(Transport(auth, settings=resolved))

    @classmethod
    def from_token(
        cls,
        id_token: str | None = None,
        *,
        refresh_token: str | None = None,
        settings: Settings | None = None,
    ) -> Self:
        """Use an existing id token, or a renewable refresh token."""
        resolved = settings or Settings()
        id_token = id_token or os.environ.get("ICPC_ID_TOKEN")
        refresh_token = refresh_token or os.environ.get("ICPC_REFRESH_TOKEN")
        if refresh_token:
            tokens = TokenSet(id_token=id_token or "", refresh_token=refresh_token)
            return cls(Transport(CognitoAuth(tokens=tokens, settings=resolved), settings=resolved))
        if not id_token:
            raise errors.ConfigError("pass id_token or refresh_token, or set ICPC_ID_TOKEN")
        return cls(Transport(SyncStaticTokenAuth(id_token), settings=resolved))

    @classmethod
    def from_store(
        cls,
        username: str | None = None,
        *,
        store: CredentialStore | None = None,
        settings: Settings | None = None,
    ) -> Self:
        """Use the tokens cached by ``icpc auth login``."""
        resolved = settings or Settings()
        token_store = store or CredentialStore()
        account = _stored_account(token_store, username)
        auth = CognitoAuth(
            username=account.username,
            password=account.password,
            tokens=account.tokens,
            store=token_store,
            settings=resolved,
        )
        return cls(Transport(auth, settings=resolved))

    @classmethod
    def anonymous(cls, *, settings: Settings | None = None) -> Self:
        """A client with no credentials, for ``/contest/public/*`` only."""
        return cls(Transport(None, settings=settings or Settings()))

    # ------------------------------------------------------------ requests --

    def send[T](self, operation: Operation[T]) -> T:
        """Issue one operation and return its typed result."""
        return self._t.send(operation)

    def whoami(self) -> PersonBasic:
        """The account behind the current token."""
        return self.send(person_api.whoami())

    def id_token(self) -> str:
        """The current bearer token, refreshing it first if it is stale.

        Useful for handing the session to another tool. Treat it as a password.
        """
        if self._t.auth is None:
            raise errors.ConfigError("this client has no credentials")
        return self._t.auth.id_token()

    def my_contests(
        self, icpc_year: int, role: ReferenceRole | str = ReferenceRole.CONTEST_MANAGER
    ) -> list[ContestReference]:
        """Contests the signed-in account is attached to, for one ICPC season.

        See :meth:`AsyncIcpc.my_contests`.
        """
        me = self.whoami()
        if me.id is None:
            raise errors.ConfigError("could not determine the signed-in person id")
        return self.send(person_api.references(me.id, icpc_year, role))

    # -------------------------------------------------------------- search --

    def count[R, F](self, endpoint: SearchEndpoint[R, F], q: Q | None = None) -> int:
        """How many rows the query matches."""
        return self.send(endpoint.count(q))

    def page[R, F](
        self,
        endpoint: SearchEndpoint[R, F],
        q: Q | None = None,
        *,
        page: int = 1,
        size: int = DEFAULT_PAGE_SIZE,
    ) -> list[R]:
        """One page of results, 1-based."""
        return self.send(endpoint.rows(q, page=page, size=size))

    def all[R, F](
        self,
        endpoint: SearchEndpoint[R, F],
        q: Q | None = None,
        *,
        size: int = DEFAULT_PAGE_SIZE,
        max_rows: int | None = None,
    ) -> list[R]:
        """Every matching row, paging until the ``/count`` total is covered."""
        query = q if q is not None else endpoint.query()
        total = self.send(endpoint.count(query))
        limit = total if max_rows is None else min(total, max_rows)
        rows: list[R] = []
        number = 1
        while len(rows) < limit:
            chunk = self.send(endpoint.rows(query, page=number, size=size))
            if not chunk:
                break
            rows.extend(chunk)
            number += 1
        return rows[:limit]

    def iter[R, F](
        self,
        endpoint: SearchEndpoint[R, F],
        q: Q | None = None,
        *,
        size: int = DEFAULT_PAGE_SIZE,
    ) -> Iterator[R]:
        """Stream results, one page at a time, stopping on the first short page."""
        query = q if q is not None else endpoint.query()
        number = 1
        while True:
            rows = self.send(endpoint.rows(query, page=number, size=size))
            yield from rows
            if len(rows) < size:
                return
            number += 1

    def _all_columns[R, F](self, endpoint: SearchEndpoint[R, F]) -> list[R]:
        return self.all(endpoint, _full(endpoint))

    def _survey_rows(self, contest_id: int) -> list[SurveyResponseRow]:
        """Every response to every survey of a contest — see
        :meth:`AsyncIcpc._survey_rows`, of which this is the sequential twin.
        """
        surveys = self.send(survey_api.for_contest(contest_id))
        rows: list[SurveyResponseRow] = []
        for one in surveys:
            if one.id is not None:
                rows.extend(self.all(survey_responses(one.id)))
        return rows

    # ------------------------------------------------------ joined contest --

    def load_contest(self, contest_id: int, include: Include = Include.DEFAULT) -> ContestView:
        """Fetch a contest's tables and join them.

        The async client fetches them in parallel; here they are sequential, which
        is the honest cost of a synchronous API.
        """
        teams = self._all_columns(endpoints.contest_teams(contest_id))
        metadata = self.send(contest_api.get(contest_id)) if Include.METADATA in include else None
        sites = self.send(contest_api.sites(contest_id)) if Include.METADATA in include else []
        members = (
            self._all_columns(endpoints.contest_team_members(contest_id))
            if Include.MEMBERS in include
            else []
        )
        institutions = (
            self._all_columns(endpoints.contest_institutions(contest_id))
            if Include.INSTITUTIONS in include
            else []
        )
        participants = (
            self._all_columns(endpoints.contest_participants(contest_id))
            if Include.PARTICIPANTS in include
            else []
        )
        surveys = self._survey_rows(contest_id) if Include.SURVEYS in include else []
        return join(
            teams,
            contest=metadata,
            sites=sites,
            members=members,
            institutions=institutions,
            participants=participants,
            survey_responses=surveys,
        )

    # -------------------------------------------------------------- writes --

    def update_team(self, team_id: int, **changes: Any) -> Team:
        """Read a team, apply ``changes``, and write the whole object back.

        A full-object replace — see :meth:`AsyncIcpc.update_team`.
        """
        current = self.send(team_api.get(team_id))
        payload = current.model_dump(by_alias=True, exclude_none=False)
        payload.update(changes)
        self.send(team_api.replace(team_id, payload))
        return self.send(team_api.get(team_id))

    # ------------------------------------------------------------ lifetime --

    def close(self) -> None:
        self._t.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
