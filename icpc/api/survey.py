"""``/contest/survey`` endpoints."""

from __future__ import annotations

from icpc.models.surveys import Survey, SurveyField
from icpc.transport.operation import Operation, Request, list_op, model_op

__all__ = ["fields", "for_contest", "get"]


def for_contest(contest_id: int) -> Operation[list[Survey]]:
    """Every survey of a contest."""
    return list_op(Request("GET", f"/contest/survey/{contest_id}/table"), Survey)


def get(survey_id: int) -> Operation[Survey]:
    """One survey, by its own id rather than its contest's.

    Note that this endpoint and :func:`for_contest` return different subset
    of fields about the model.
    """
    return model_op(Request("GET", f"/contest/survey/{survey_id}"), Survey)


def fields(survey_id: int) -> Operation[list[SurveyField]]:
    """A survey's fields, in ``fieldOrder``.

    ``DESCRIPTION`` entries are not questions but just text labels; see
    :attr:`~icpc.models.surveys.SurveyField.is_question`.
    """
    return list_op(Request("GET", f"/contest/survey/field/{survey_id}/table"), SurveyField)
