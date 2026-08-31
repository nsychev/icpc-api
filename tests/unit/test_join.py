"""Unit tests for the unified join."""

from __future__ import annotations

import json

from icpc.facade.domain import join
from icpc.models import ContestParticipantRow, InstitutionRow, TeamMemberRow, TeamRow
from icpc.models.enums import MemberRole, TeamStatus
from icpc.models.surveys import SurveyResponseRow

TEAMS = [
    TeamRow.model_validate(
        {
            "id": 1,
            "name": "Alpha",
            "status": "ACCEPTED",
            "site": "Moscow",
            "instId": 100,
            "teamMembers": json.dumps(
                [{"personId": 11, "fullName": "Ann Lee", "role": "CONTESTANT"}]
            ),
        }
    ),
    TeamRow.model_validate({"id": 2, "name": "Beta", "status": "PENDING", "site": "Almaty"}),
]

MEMBERS = [
    TeamMemberRow.model_validate(
        {"teamId": 1, "personId": 11, "firstName": "Ann", "lastName": "Lee", "role": "CONTESTANT"}
    ),
    TeamMemberRow.model_validate(
        {"teamId": 1, "personId": 12, "firstName": "Bo", "lastName": "Ng", "role": "COACH"}
    ),
    TeamMemberRow.model_validate(
        {"teamId": 1, "personId": 13, "firstName": "Cy", "lastName": "Vo", "role": "STUDENT_COACH"}
    ),
]

INSTITUTIONS = [InstitutionRow.model_validate({"instId": 100, "instShortName": "MIPT"})]
PARTICIPANTS = [ContestParticipantRow.model_validate({"personId": 12, "shirtSize": "L"})]


def test_members_attach_to_their_team():
    view = join(TEAMS, members=MEMBERS)
    assert [m.first_name for m in view.teams[0].members] == ["Ann", "Bo", "Cy"]
    assert view.teams[1].members == []


def test_student_coach_counts_as_both_contestant_and_coach():
    # Deliberate double counting: the role really is both, and this matches the
    # ICPC UI.
    team = join(TEAMS, members=MEMBERS).teams[0]
    assert [m.role for m in team.contestants] == [MemberRole.CONTESTANT, MemberRole.STUDENT_COACH]
    assert [m.role for m in team.coaches] == [MemberRole.COACH, MemberRole.STUDENT_COACH]


def test_roster_falls_back_to_the_embedded_blob_when_members_were_not_fetched():
    view = join(TEAMS)
    assert [m.person_id for m in view.teams[0].members] == [11]
    # The blob carries no first/last name, so the grid's name columns stay empty.
    assert view.teams[0].members[0].first_name is None
    assert view.teams[1].members == []


def test_institution_attaches_by_inst_id():
    view = join(TEAMS, institutions=INSTITUTIONS)
    assert view.teams[0].institution is not None
    assert view.teams[0].institution.inst_short_name == "MIPT"
    assert view.teams[1].institution is None


def test_participants_attach_by_person_id():
    view = join(TEAMS, members=MEMBERS, participants=PARTICIPANTS)
    coach = next(m for m in view.teams[0].members if m.person_id == 12)
    assert coach.participant is not None
    assert coach.participant.shirt_size == "L"


def test_grouping_helpers():
    view = join(TEAMS, members=MEMBERS)
    assert sorted(str(site) for site in view.by_site()) == ["Almaty", "Moscow"]
    assert view.by_status()[TeamStatus.ACCEPTED] == [view.teams[0]]
    assert len(view.members()) == 3
    assert view.team(2) is not None
    assert view.team(999) is None


SURVEY_ROWS = [
    SurveyResponseRow.model_validate(
        # The wire sends the id as a string, and mixes null and "" for a
        # question nobody answered.
        {"userId": "11", "1130": "Ann's answer", "1131": "", "1132": None}
    ),
    SurveyResponseRow.model_validate({"userId": "12", "1130": "Bo's answer"}),
    # A second survey of the same contest: its field ids cannot collide, so the
    # two merge into one mapping per person.
    SurveyResponseRow.model_validate({"userId": "11", "2200": "from survey two"}),
    # Nobody on any team; must not raise.
    SurveyResponseRow.model_validate({"userId": "999", "1130": "stranger"}),
]


def test_survey_answers_attach_by_person_id_and_merge_across_surveys():
    view = join(TEAMS, members=MEMBERS, survey_responses=SURVEY_ROWS)
    ann = next(m for m in view.teams[0].members if m.person_id == 11)
    assert ann.survey == {"1130": "Ann's answer", "2200": "from survey two"}
    bo = next(m for m in view.teams[0].members if m.person_id == 12)
    assert bo.survey == {"1130": "Bo's answer"}


def test_survey_answers_are_empty_for_people_who_did_not_answer():
    view = join(TEAMS, members=MEMBERS, survey_responses=SURVEY_ROWS)
    cy = next(m for m in view.teams[0].members if m.person_id == 13)
    assert cy.survey == {}


def test_survey_answers_reach_a_roster_built_from_the_blob():
    """The blob carries `personId`, which is all the join needs."""
    view = join(TEAMS, survey_responses=SURVEY_ROWS)
    assert view.teams[0].members[0].survey == {"1130": "Ann's answer", "2200": "from survey two"}


def test_survey_is_empty_when_no_responses_were_fetched():
    view = join(TEAMS, members=MEMBERS)
    assert all(m.survey == {} for m in view.members())
