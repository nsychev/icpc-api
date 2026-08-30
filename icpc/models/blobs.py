"""Parsers for the JSON-in-a-string fields.

Two search columns carry JSON encoded *as a string* rather than as nested JSON:

* ``teamMembers`` on a team row — the roster, so a team listing needs no second call.
* ``extraField`` — the answers to a contest's extra registration fields

Both are parsed here into real objects, and always tolerantly: a malformed blob
yields an empty result rather than failing the whole page.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import Field

from icpc.models.base import Row
from icpc.models.enums import MemberRole

__all__ = ["TeamMemberBlob", "parse_extra_fields", "parse_members"]


class TeamMemberBlob(Row):
    """One entry of the ``teamMembers`` string on a team search row."""

    member_id: int | None = None
    person_id: int | None = None
    full_name: str | None = None
    username: str | None = None
    reg_complete: bool | None = None
    # Try the enum first so a known role arrives as an enum member, but keep
    # `str` in the union so an unrecognised one still parses.
    role: MemberRole | str | None = Field(default=None, union_mode="left_to_right")


def _loads(blob: str | None) -> Any:
    if not blob:
        return None
    try:
        return json.loads(blob)
    except ValueError:
        return None


def parse_members(blob: str | None) -> list[TeamMemberBlob]:
    """Decode a ``teamMembers`` string into typed entries."""
    data = _loads(blob)
    if not isinstance(data, list):
        return []
    return [TeamMemberBlob.model_validate(item) for item in data if isinstance(item, dict)]


def parse_extra_fields(blob: str | None) -> dict[str, str]:
    """Decode ``extraField`` into ``{question: answer}``.

    Entries with no answer are dropped; the question text is the contest's own
    label, so keys vary between contests.
    """
    data = _loads(blob)
    if not isinstance(data, list):
        return {}
    result: dict[str, str] = {}
    for item in data:
        if not isinstance(item, dict):
            continue
        field = item.get("field")
        response = item.get("response")
        if field is not None and response is not None:
            result[str(field)] = str(response)
    return result


class ExtraField(Row):
    """An answered custom registration question, in its list form."""

    field: str | None = None
    response: str | None = None
    field_id: int | None = Field(default=None, alias="fieldId")
