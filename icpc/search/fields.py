"""Typed field references.

The server ignores unknown column names without complaining, so a typo produces a
silently empty column instead of an error. Static checking is therefore the only
guard we get, and these descriptors are how it is applied: a field belongs to one
row type, carries the type of its value, and is the only way to build a filter or a
sort key.

    >>> from icpc.search import contest_teams
    >>> f = contest_teams(1234).fields
    >>> q = Q.build([f.id.name, f.name.name], [f.status.eq("ACCEPTED")], [f.name.asc()])

Filters are built with :meth:`Field.eq` rather than ``==``. Making ``==`` return a
filter would break every ordinary use of equality on these objects — ``in``, dict
lookups, test assertions — for a few saved characters.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from icpc.search.dsl import Direction, Filter, SortKey

__all__ = ["Field"]


@dataclass(frozen=True, slots=True)
class Field[RowT, ValT]:
    """A column of ``RowT`` whose values are ``ValT``."""

    name: str

    def __str__(self) -> str:
        return self.name

    # The server has exactly one filter operator, `#`, a substring match on the
    # rendered value; `eq` and `contains` are therefore the same call.
    def eq(self, value: ValT) -> Filter:
        """Filter rows whose value in this column matches ``value``."""
        return Filter.of(self.name, value)

    def contains(self, value: ValT) -> Filter:
        """Alias for :meth:`eq`: the server's ``#`` is already a substring match."""
        return self.eq(value)

    def asc(self) -> SortKey:
        return SortKey(self.name, "asc")

    def desc(self) -> SortKey:
        return SortKey(self.name, "desc")

    def order(self, direction: Direction) -> SortKey:
        return SortKey(self.name, direction)


def names(*fields: Field[Any, Any]) -> tuple[str, ...]:
    """Column names of ``fields``, for use as a projection."""
    return tuple(f.name for f in fields)
