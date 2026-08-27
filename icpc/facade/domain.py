"""The joined object model and the pure function that builds it.

Search endpoints hand back four disconnected tables — teams, team members,
institutions, participants — keyed by ids. :func:`join` stitches them into one
navigable structure. It touches no network, so it is testable from recorded rows
alone, and the client is free to fetch the four tables concurrently.

:class:`Team` and :class:`Member` *are* their grid rows: they subclass
:class:`~icpc.models._generated.TeamRow` and
:class:`~icpc.models._generated.TeamMemberRow`, so every column of a grid is a
typed attribute on them directly, with the join's own fields alongside.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Any

from pydantic import Field

from icpc.models._generated import (
    ContestParticipantRow,
    InstitutionRow,
    TeamMemberRow,
    TeamRow,
)
from icpc.models.base import Row
from icpc.models.blobs import TeamMemberBlob
from icpc.models.common import NamedRef
from icpc.models.entities import Contest
from icpc.models.enums import TeamStatus, coach_roles, contestant_roles

__all__ = ["ContestView", "Member", "Team", "join"]


class Member(TeamMemberRow):
    """One person's membership of one team.

    Every column of the ``teammember`` grid is an attribute here. When that
    table was not fetched the roster comes from each team row's embedded blob
    instead, and only :attr:`person_id`, :attr:`username`, :attr:`role` and
    :attr:`registration_complete` are populated — the rest are ``None``, as they
    are for any unprojected column.
    """

    #: Whether registration is complete, from whichever source built this
    #: membership. The inherited :attr:`complete_registration` is the grid's own
    #: column, and is ``None`` when the roster came from the blob.
    registration_complete: bool | None = None
    #: The person's contest-wide record, when the participant table was fetched.
    participant: ContestParticipantRow | None = None


class Team(TeamRow):
    """A team with its roster and institution attached.

    Every column of the ``team`` grid is an attribute here; :attr:`members` and
    :attr:`institution` are what the join adds.
    """

    #: The joined roster. The row's embedded blob is still on
    #: :attr:`~icpc.models.mixins.HasTeamMembers.member_blobs`.
    members: list[Member] = Field(default_factory=list)
    #: The institution row, when that table was fetched.
    institution: InstitutionRow | None = None

    @property
    def contestants(self) -> list[Member]:
        """Members who compete.

        ``STUDENT_COACH`` and ``CONTESTANT_COACH`` appear here *and* in
        :attr:`coaches` — they hold both roles, and the ICPC UI counts them twice.
        """
        roles = contestant_roles()
        return [m for m in self.members if m.role in roles]

    @property
    def coaches(self) -> list[Member]:
        """Members who coach. Overlaps :attr:`contestants`; see there."""
        roles = coach_roles()
        return [m for m in self.members if m.role in roles]

    @property
    def other(self) -> list[Member]:
        """Members who neither compete nor coach: reserves, attendees, staff.

        The complement of :attr:`contestants` and :attr:`coaches` together, so a
        contestant coach is not in here despite holding two roles.
        """
        roles = contestant_roles() | coach_roles()
        return [m for m in self.members if m.role not in roles]


@dataclass(slots=True)
class ContestView:
    """Everything fetched about one contest, joined up."""

    contest: Contest | None = None
    sites: list[NamedRef] = field(default_factory=list)
    teams: list[Team] = field(default_factory=list)
    institutions: dict[int, InstitutionRow] = field(default_factory=dict)
    people: dict[int, ContestParticipantRow] = field(default_factory=dict)

    def team(self, team_id: int) -> Team | None:
        return next((t for t in self.teams if t.id == team_id), None)

    def by_site(self) -> dict[str | None, list[Team]]:
        """Teams grouped by site name."""
        grouped: dict[str | None, list[Team]] = {}
        for team in self.teams:
            grouped.setdefault(team.site, []).append(team)
        return grouped

    def by_status(self) -> dict[TeamStatus | str | None, list[Team]]:
        grouped: dict[TeamStatus | str | None, list[Team]] = {}
        for team in self.teams:
            grouped.setdefault(team.status, []).append(team)
        return grouped

    def members(self) -> list[Member]:
        """Every membership across every team, in team order."""
        return [member for team in self.teams for member in team.members]


def _columns(row: Row) -> dict[str, Any]:
    """A fetched row's fields and its unknown extras, ready to re-seed a subclass.

    Taken straight off the instance rather than through ``model_dump``: the rows
    are already validated, and a contest is thousands of them.
    """
    return {**row.__dict__, **(row.__pydantic_extra__ or {})}


def _member_from_row(row: TeamMemberRow) -> Member:
    return Member.model_construct(
        **_columns(row),
        registration_complete=row.complete_registration,
        participant=None,
    )


def _member_from_blob(blob: TeamMemberBlob) -> Member:
    return Member.model_construct(
        person_id=blob.person_id,
        username=blob.username,
        role=blob.role,
        registration_complete=blob.reg_complete,
        participant=None,
    )


def join(
    teams: Sequence[TeamRow],
    *,
    contest: Contest | None = None,
    sites: Sequence[NamedRef] = (),
    members: Iterable[TeamMemberRow] = (),
    institutions: Iterable[InstitutionRow] = (),
    participants: Iterable[ContestParticipantRow] = (),
) -> ContestView:
    """Build a :class:`ContestView` from raw search rows.

    When ``members`` is empty the roster falls back to each team row's embedded
    ``teamMembers`` blob, which is thinner but costs no extra request.
    """
    by_inst = {row.inst_id: row for row in institutions if row.inst_id is not None}
    by_person = {row.person_id: row for row in participants if row.person_id is not None}

    rosters: dict[int, list[Member]] = {}
    for row in members:
        if row.team_id is None:
            continue
        rosters.setdefault(row.team_id, []).append(_member_from_row(row))

    built: list[Team] = []
    for row in teams:
        roster = rosters.get(row.id) if row.id is not None else None
        if roster is None:
            roster = [_member_from_blob(blob) for blob in row.member_blobs]
        for member in roster:
            if member.person_id is not None:
                member.participant = by_person.get(member.person_id)
        built.append(
            Team.model_construct(
                **_columns(row),
                members=roster,
                institution=by_inst.get(row.inst_id) if row.inst_id is not None else None,
            )
        )

    return ContestView(
        contest=contest,
        sites=list(sites),
        teams=built,
        institutions=by_inst,
        people=by_person,
    )
