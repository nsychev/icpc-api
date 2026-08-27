"""Behaviour attached to generated rows that carry JSON-in-a-string columns.

The annotations are under ``TYPE_CHECKING`` on purpose: pydantic collects fields
from every base class's annotations, and re-declaring them here would fight with the
generated ones. At runtime these are plain attribute reads on the model.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from icpc.models.blobs import TeamMemberBlob, parse_extra_fields, parse_members

__all__ = ["HasExtraFields", "HasTeamMembers"]


class HasTeamMembers:
    """A row whose ``teamMembers`` column holds the roster as a JSON string."""

    if TYPE_CHECKING:
        team_members: str | None

    @property
    def member_blobs(self) -> list[TeamMemberBlob]:
        """The roster embedded in this row. Useful if ``teammember`` was not
        fetched.
        """
        return parse_members(self.team_members)


class HasExtraFields:
    """A row whose ``extraField`` column holds custom-question answers."""

    if TYPE_CHECKING:
        extra_field: str | None

    @property
    def extras(self) -> dict[str, str]:
        """Answers to the contest's custom registration questions.

        Keys are the contest's own question labels, so they differ between
        contests and are frequently not in English.
        """
        return parse_extra_fields(self.extra_field)
