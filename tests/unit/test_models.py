"""Row parsing: the null-everywhere reality, deploy drift, and the string blobs."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime

from icpc.models import TeamMemberRow, TeamRow, TeamStatus
from icpc.models.enums import Consent, MemberRole
from icpc.search import contest_teams

ROSTER = [
    {"memberId": 1, "personId": 11, "fullName": "Ann Lee", "role": "CONTESTANT"},
    {"memberId": 2, "personId": 12, "fullName": "Bo Ng", "role": "COACH"},
]


def test_every_field_may_be_null():
    # `proj:` does not shape the response: unprojected columns come back null.
    row = TeamRow.model_validate({name: None for name in contest_teams(1).all_fields})
    assert row.id is None
    assert row.status is None
    assert row.member_blobs == []
    assert row.extras == {}


def test_unknown_columns_survive_a_deploy():
    row = TeamRow.model_validate({"id": 1, "brandNewColumn": "surprise"})
    assert row.id == 1
    assert row.unknown_fields() == {"brandNewColumn": "surprise"}
    assert row.extra("brandNewColumn") == "surprise"


def test_known_enum_values_parse_as_enums():
    row = TeamRow.model_validate({"status": "ACCEPTED"})
    assert row.status is TeamStatus.ACCEPTED


def test_unknown_enum_values_fall_back_to_the_raw_string():
    # A new status must not fail the whole page's validation.
    row = TeamRow.model_validate({"status": "SOMETHING_NEW"})
    assert row.status == "SOMETHING_NEW"


def test_team_members_blob_is_parsed():
    row = TeamRow.model_validate({"id": 1, "teamMembers": json.dumps(ROSTER)})
    assert [m.full_name for m in row.member_blobs] == ["Ann Lee", "Bo Ng"]
    assert row.member_blobs[0].role is MemberRole.CONTESTANT


def test_malformed_blob_yields_nothing_rather_than_raising():
    row = TeamRow.model_validate({"id": 1, "teamMembers": "{not json"})
    assert row.member_blobs == []


def test_extra_fields_blob_becomes_a_dict():
    blob = json.dumps(
        [
            {"field": "Course", "response": "3"},
            {"field": "Unanswered", "response": None},
        ]
    )
    row = TeamRow.model_validate({"extraField": blob})
    # Unanswered questions are dropped rather than mapped to None.
    assert row.extras == {"Course": "3"}


def test_camel_case_aliases_map_to_snake_case():
    row = TeamRow.model_validate({"instShortName": "MIPT", "site": "Almaty"})
    assert row.inst_short_name == "MIPT"
    assert row.site == "Almaty"


def test_timestamps_are_parsed():
    # icpc.global uses offset-aware ISO 8601 with milliseconds.
    row = TeamRow.model_validate({"createdWhen": "2025-09-24T11:12:35.787+00:00"})
    assert row.created_when == datetime(2025, 9, 24, 11, 12, 35, 787000, tzinfo=UTC)


def test_dates_are_parsed():
    member = TeamMemberRow.model_validate({"dob": "2005-01-09"})
    assert member.dob == date(2005, 1, 9)


def test_an_unparseable_date_stays_a_string_rather_than_failing_the_page():
    member = TeamMemberRow.model_validate({"dob": "sometime in 2005"})
    assert member.dob == "sometime in 2005"


def test_consent_columns_are_words_not_booleans():
    # includeEmail and friends look boolean but carry AGREE/DISAGREE.
    member = TeamMemberRow.model_validate({"includeEmail": "AGREE"})
    assert member.include_email is Consent.AGREE


def test_ids_are_coerced_to_int():
    # The wire sometimes stringifies numbers; pydantic normalises them.
    row = TeamMemberRow.model_validate({"teamId": "42", "personId": 7})
    assert row.team_id == 42
    assert row.person_id == 7
