"""Surveys: field typing, the answer split, and the endpoint's refusals."""

from __future__ import annotations

from datetime import date

import pytest

from icpc.errors import SearchError
from icpc.models.enums import SurveyFieldType, SurveyVisibility
from icpc.models.surveys import Survey, SurveyField, SurveyResponseRow, merge_answers
from icpc.search.surveys import survey_responses


def test_a_survey_parses_its_enums_and_date():
    survey = Survey.model_validate(
        {
            "id": 969,
            "name": "Test Team Survey",
            "visibility": "TEAMS",
            "acceptsResponses": True,
            "surveyEndDate": "2026-09-06",
            "responses": 2,
        }
    )
    assert survey.visibility is SurveyVisibility.TEAMS
    assert survey.survey_end_date == date(2026, 9, 6)


def test_an_unknown_visibility_stays_a_string():
    """The union is left-to-right so a value added server-side still parses."""
    assert Survey.model_validate({"visibility": "SOMETHING_NEW"}).visibility == "SOMETHING_NEW"


@pytest.mark.parametrize("wire", [t.value for t in SurveyFieldType])
def test_every_field_type_parses(wire: str):
    assert SurveyField.model_validate({"type": wire}).type is SurveyFieldType(wire)


def test_a_description_is_not_a_question():
    """Static text on the form: it can never hold an answer, so never a column."""
    assert SurveyField.model_validate({"type": "DESCRIPTION"}).is_question is False
    assert SurveyField.model_validate({"type": "SHORT_ANSWER"}).is_question is True


def test_options_come_from_default_value_only_for_the_choice_types():
    assert SurveyField.model_validate({"type": "DROPDOWN", "defaultValue": "a,b,c"}).options == [
        "a",
        "b",
        "c",
    ]
    # `defaultValue` is prose here, not a list of choices.
    assert (
        SurveyField.model_validate({"type": "DESCRIPTION", "defaultValue": "Just text"}).options
        == []
    )


def test_options_may_arrive_as_json_objects():
    field = SurveyField.model_validate(
        {"type": "CHECKBOXES", "defaultValue": '[{"name": "Yes", "color": "#0f0"}]'}
    )
    assert field.options == ["Yes"]


def test_semicolon_separated_options_read_as_one_choice():
    """What the form itself shows. Reproduced rather than repaired: see `options`."""
    assert SurveyField.model_validate(
        {"type": "DROPDOWN", "defaultValue": "a;b;c;d;e"}
    ).options == ["a;b;c;d;e"]


def test_a_response_separates_the_person_from_the_answers():
    row = SurveyResponseRow.model_validate(
        {
            "userId": "1331699",
            "sex": "Default sex",
            "workstations": "[]",
            "1220": "other",
            "1221": "",
            "1223": None,
        }
    )
    # The wire sends the id as a string; the join needs it as a number.
    assert row.user_id == 1331699
    # Not a `Sex`: contests serve free text here.
    assert row.sex == "Default sex"
    # Unanswered in both the forms the server uses.
    assert row.answers == {"1220": "other"}


def test_merge_answers_groups_by_person_across_surveys():
    rows = [
        SurveyResponseRow.model_validate({"userId": "11", "1130": "a"}),
        SurveyResponseRow.model_validate({"userId": "11", "2200": "b"}),
        SurveyResponseRow.model_validate({"userId": "12", "1130": "c"}),
        SurveyResponseRow.model_validate({"1130": "no user id"}),
    ]
    assert merge_answers(rows) == {11: {"1130": "a", "2200": "b"}, 12: {"1130": "c"}}


def test_the_responses_endpoint_projects_one_column():
    """An empty projection renders `proj:;`, which the server answers with a 500."""
    assert survey_responses(894).query().render() == "proj:userId;"


def test_a_filtered_survey_query_is_refused():
    """The server takes the filter and returns every row regardless."""
    endpoint = survey_responses(894)
    with pytest.raises(SearchError, match="does not support filters"):
        endpoint.query(filters=[endpoint.fields.user_id.eq(1195024)])


def test_the_count_and_export_siblings_follow_the_table_path():
    endpoint = survey_responses(894)
    assert endpoint.count().request.path == "/contest/survey/responses/894/table/count"
    assert endpoint.export().request.path == "/contest/survey/responses/894/table/export"
