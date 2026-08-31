"""The survey-responses grid.

Note that it handles requests differently: ``q`` is required, but ``proj:`` is
not supported, so we always pass empty value here. ``filter:`` is accepted but
ignored.
"""

from __future__ import annotations

from icpc.models.surveys import SurveyResponseRow
from icpc.search.endpoint import SearchEndpoint
from icpc.search.fields import Field

__all__ = ["SurveyResponseFields", "survey_responses"]


class SurveyResponseFields:
    """Typed columns of :class:`~icpc.models.surveys.SurveyResponseRow`.

    The person's columns only. A survey's answers are keyed by field id and vary
    per survey, so they are reached through
    :attr:`~icpc.models.surveys.SurveyResponseRow.answers` rather than named here.
    """

    user_id: Field[SurveyResponseRow, int] = Field("userId")
    username: Field[SurveyResponseRow, str] = Field("username")
    first_name: Field[SurveyResponseRow, str] = Field("firstName")
    last_name: Field[SurveyResponseRow, str] = Field("lastName")
    badge_name: Field[SurveyResponseRow, str] = Field("badgeName")
    sex: Field[SurveyResponseRow, str] = Field("sex")
    teams: Field[SurveyResponseRow, str] = Field("teams")
    participation: Field[SurveyResponseRow, str] = Field("participation")
    workstations: Field[SurveyResponseRow, str] = Field("workstations")
    institution_long_names: Field[SurveyResponseRow, str] = Field("institutionLongNames")
    institution_short_names: Field[SurveyResponseRow, str] = Field("institutionShortNames")

    #: One column, because an empty projection is a 500 and a wider one buys
    #: nothing: the server returns every column regardless.
    default_proj: tuple[str, ...] = ("userId",)

    all_fields: tuple[str, ...] = (
        "userId",
        "username",
        "firstName",
        "lastName",
        "badgeName",
        "sex",
        "teams",
        "participation",
        "workstations",
        "institutionLongNames",
        "institutionShortNames",
    )


def survey_responses(
    survey_id: int,
) -> SearchEndpoint[SurveyResponseRow, SurveyResponseFields]:
    """One row per person who answered a survey.

    ``/contest/survey/responses/{survey_id}/table``

    Keyed by the survey rather than the contest, so
    :func:`icpc.api.survey.for_contest` comes first. Rows are per person for
    every :class:`~icpc.models.enums.SurveyVisibility`, a ``TEAMS`` survey
    included.
    """
    return SearchEndpoint(
        path=f"/contest/survey/responses/{survey_id}/table",
        row=SurveyResponseRow,
        fields=SurveyResponseFields(),
        default_proj=SurveyResponseFields.default_proj,
        all_fields=SurveyResponseFields.all_fields,
        name="survey_responses",
        filterable=False,
    )
