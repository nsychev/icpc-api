"""Static guarantees.

``ty`` checks these at lint time; running them here also proves the annotations
survive at runtime. The claim under test is the headline one: every request has a
type, and it is the type ``send()`` returns.
"""

from __future__ import annotations

from typing import assert_type

from icpc.api import contest as contest_api
from icpc.api import person as person_api
from icpc.api import public as public_api
from icpc.api import team as team_api
from icpc.models import ContestParticipantRow, TeamRow
from icpc.models.entities import Contest, PersonBasic, PublicContest, Team, TeamMember
from icpc.search import TeamFields, contest_participants, contest_teams
from icpc.search.dsl import Filter, SortKey
from icpc.search.endpoint import SearchEndpoint
from icpc.search.fields import Field
from icpc.transport.operation import Operation


def test_operations_carry_their_result_type():
    assert_type(team_api.get(1), Operation[Team])
    assert_type(team_api.members(1), Operation[list[TeamMember]])
    assert_type(contest_api.get(1), Operation[Contest])
    assert_type(person_api.whoami(), Operation[PersonBasic])
    assert_type(public_api.contest("NERC"), Operation[PublicContest])
    assert_type(team_api.promote(1, 2), Operation[None])


def test_search_endpoints_are_generic_in_their_row_type():
    teams = contest_teams(9180)
    assert_type(teams, SearchEndpoint[TeamRow, TeamFields])
    assert_type(teams.rows(), Operation[list[TeamRow]])
    assert_type(teams.count(), Operation[int])
    participants = contest_participants(9180)
    assert_type(participants.rows(), Operation[list[ContestParticipantRow]])


def test_fields_are_bound_to_their_row_and_value_types():
    f = contest_teams(9180).fields
    assert_type(f.paid, Field[TeamRow, bool])
    assert_type(f.inst_id, Field[TeamRow, int])
    assert_type(f.name.asc(), SortKey)
    assert_type(f.name.eq("Alpha"), Filter)


def test_row_types_are_actually_distinct():
    # The two team shapes are different DTOs and must not be conflated: the search
    # grid returns `id`/`name`, the team grid returns `teamId`/`teamName`.
    from icpc.models import TeamSummaryRow

    assert "id" in TeamRow.model_fields
    assert "team_id" in TeamSummaryRow.model_fields
    assert "id" not in TeamSummaryRow.model_fields
