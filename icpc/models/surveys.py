"""Survey definition.

A survey is a form linked to the contest. *Fields* define the questions.
Respondents are defined by :class:`~icpc.models.enums.SurveyVisibility`.
Each eligible person submit their own response.

A response row carries the person's identity in named columns and their answers
keyed by :attr:`SurveyField.id` as a string, so the answers arrive in
``model_extra`` rather than as declared fields. Read them off
:attr:`SurveyResponseRow.answers`.

Answers are always strings on the wire, whatever the field type: a
``CHECKBOXES`` multi-selection arrives as one joined string rather than a list.
Nothing here parses them further, because the separator is not consistent — see
:attr:`SurveyField.options`.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import date

from pydantic import Field

from icpc.models.base import Row
from icpc.models.enums import SurveyFieldType, SurveyVisibility

__all__ = ["Survey", "SurveyField", "SurveyResponseRow", "merge_answers"]


class Survey(Row):
    """One survey. ``GET /contest/survey/{contest_id}/table`` lists a contest's."""

    id: int | None = None
    #: Required server-side, 3 to 128 characters.
    name: str | None = None
    #: Up to 65536 characters.
    description: str | None = None
    #: Required server-side.
    visibility: SurveyVisibility | str | None = Field(default=None, union_mode="left_to_right")
    accepts_responses: bool | None = None
    survey_end_date: date | None = None
    #: How many people have answered — a count, not the responses themselves.
    responses: int | None = None
    #: Present on ``GET /contest/survey/{survey_id}``, absent from the list rows.
    contest_id: int | None = None


class SurveyField(Row):
    """One question. ``GET /contest/survey/field/{survey_id}/table``.

    ``next`` and ``prev`` chain the fields in display order, alongside
    :attr:`field_order`.
    """

    id: int | None = None
    #: Required server-side, 3 to 255 characters.
    name: str | None = None
    #: Up to 128 characters.
    hint: str | None = None
    #: Overloaded: prose for a ``DESCRIPTION``, the option list for a
    #: ``DROPDOWN`` or ``CHECKBOXES``. Up to 65536 characters. See :attr:`options`.
    default_value: str | None = None
    #: Required server-side.
    type: SurveyFieldType | str | None = Field(default=None, union_mode="left_to_right")
    field_order: int | None = None
    #: The ``name`` — not the id — of the field this one's display depends on.
    dependency_field_name: str | None = None
    #: Comma-separated values of ``dependency_field_name`` that reveal this field.
    #: When the dependency is a ``CHECKBOXES``, any overlap counts, not equality.
    dependency_field_value: str | None = None
    image: str | None = None
    next: int | None = None
    prev: int | None = None

    @property
    def is_question(self) -> bool:
        """Whether this field can hold an answer.

        ``DESCRIPTION`` fields are static text the form displays, so they are
        never answered and are not worth offering as a column.
        """
        return self.type != SurveyFieldType.DESCRIPTION

    @property
    def options(self) -> list[str]:
        """The choices of a ``DROPDOWN`` or ``CHECKBOXES``, decoded as the UI does.

        The frontend reads :attr:`default_value` as a JSON array of objects
        carrying a ``name``, and falls back to splitting on commas. That fallback
        is reproduced here rather than improved on: a survey storing its options
        semicolon-separated reads back as one option, and that is what the form
        itself shows.

        Empty for every other field type, where ``default_value`` is prose or a
        prefilled answer rather than a list of choices.
        """
        if self.type not in (SurveyFieldType.DROPDOWN, SurveyFieldType.CHECKBOXES):
            return []
        if not self.default_value:
            return []
        try:
            parsed = json.loads(self.default_value)
        except ValueError:
            parsed = None
        if isinstance(parsed, list) and all(
            isinstance(item, dict) and "name" in item for item in parsed
        ):
            return [str(item["name"]) for item in parsed]
        return [part for part in self.default_value.split(",") if part.strip()]


class SurveyResponseRow(Row):
    """One person's answers. ``GET /contest/survey/responses/{survey_id}/table``.

    Every column here is the wire's own, and every one but :attr:`user_id` is a
    string — including ``workstations`` and the two institution columns, which
    arrive bracket-wrapped (``"[SPb ITMO]"``) rather than as arrays.
    """

    #: The person id, matching ``personId`` on a team member. Arrives as a string.
    user_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    badge_name: str | None = None
    #: Not a :class:`~icpc.models.enums.Sex`: contests serve values such as
    #: ``"Default sex"`` here, so this stays free text.
    sex: str | None = None
    teams: str | None = None
    participation: str | None = None
    workstations: str | None = None
    institution_long_names: str | None = None
    institution_short_names: str | None = None

    @property
    def answers(self) -> dict[str, str]:
        """Answers by :attr:`SurveyField.id`, as a string key.

        The named columns above are the person, not the questionnaire; only the
        numerically-keyed extras are answers. Unanswered fields are dropped,
        which covers both the ``null`` and the empty-string forms the server
        uses inconsistently.
        """
        found: dict[str, str] = {}
        for key, value in (self.model_extra or {}).items():
            if key.isdigit() and value not in (None, ""):
                found[key] = str(value)
        return found


def merge_answers(rows: Iterable[SurveyResponseRow]) -> dict[int, dict[str, str]]:
    """Answers by person id, merged across however many surveys.

    Field ids are unique across a contest's surveys, so several surveys collapse
    into one mapping without colliding.
    """
    merged: dict[int, dict[str, str]] = {}
    for row in rows:
        if row.user_id is None:
            continue
        merged.setdefault(row.user_id, {}).update(row.answers)
    return merged
