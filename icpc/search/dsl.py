"""The ``q=`` mini-language the icpc.global grids speak.

The frontend builds one string with up to three clauses, each terminated by ``;``::

    proj:id,name,status;filter:status#ACCEPTED&country#China;sort:name asc;

* **proj** — which columns to populate, comma-joined. It does *not* shape the
  response: the whole DTO always comes back and unprojected fields are ``null``.
  An empty projection is legal and yields the grid's default columns, but a
  projection in which *every* name is invalid returns 500.
* **filter** — ``column#value`` items joined by ``&`` (AND) or ``|`` (OR). Unknown
  column names are ignored silently, which is why the generated field literals
  matter more here than anywhere else.
* **sort** — multi-key, ``column asc``/``column desc``, comma-joined.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from typing import Literal

from icpc.errors import InvalidFilterValue

__all__ = ["Direction", "Filter", "FilterMode", "Q", "SortKey"]

Direction = Literal["asc", "desc"]
FilterMode = Literal["and", "or"]

#: Characters the grammar uses as separators and cannot escape.
FORBIDDEN_IN_VALUE = frozenset("#&|;,")


def _render_value(value: object) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


@dataclass(frozen=True, slots=True)
class Filter:
    """One ``column#value`` term."""

    column: str
    value: str

    def __post_init__(self) -> None:
        bad = sorted(FORBIDDEN_IN_VALUE & set(self.value))
        if bad:
            raise InvalidFilterValue(
                f"filter value for {self.column!r} contains {''.join(bad)!r}, which the "
                f"q grammar cannot escape; filter server-side on a safe substring and "
                f"narrow the result in Python"
            )

    @classmethod
    def of(cls, column: str, value: object) -> Filter:
        return cls(column, _render_value(value))

    def render(self) -> str:
        return f"{self.column}#{self.value}"


@dataclass(frozen=True, slots=True)
class SortKey:
    """One ``column asc``/``column desc`` term."""

    column: str
    direction: Direction = "asc"

    def render(self) -> str:
        return f"{self.column} {self.direction}"


@dataclass(frozen=True, slots=True)
class Q:
    """A rendered-on-demand search query."""

    proj: tuple[str, ...] = ()
    filters: tuple[Filter, ...] = ()
    #: How multiple filters combine. The UI exposes this as a toggle.
    mode: FilterMode = "and"
    sort: tuple[SortKey, ...] = field(default_factory=tuple)

    @classmethod
    def build(
        cls,
        proj: Iterable[str] = (),
        filters: Iterable[Filter] = (),
        sort: Iterable[SortKey] = (),
        mode: FilterMode = "and",
    ) -> Q:
        return cls(tuple(proj), tuple(filters), mode, tuple(sort))

    def with_proj(self, proj: Iterable[str]) -> Q:
        return Q(tuple(proj), self.filters, self.mode, self.sort)

    def where(self, *filters: Filter) -> Q:
        return Q(self.proj, self.filters + filters, self.mode, self.sort)

    def order_by(self, *keys: SortKey) -> Q:
        return Q(self.proj, self.filters, self.mode, self.sort + keys)

    def render(self) -> str:
        """Build the ``q`` parameter value, unencoded."""
        out = "proj:" + ",".join(self.proj) + ";"
        if self.filters:
            separator = "&" if self.mode == "and" else "|"
            out += "filter:" + separator.join(f.render() for f in self.filters) + ";"
        if self.sort:
            out += "sort:" + ",".join(s.render() for s in self.sort) + ";"
        return out

    def __str__(self) -> str:
        return self.render()


def params(q: Q, page: int = 1, size: int = 1000) -> dict[str, str | int]:
    """Query parameters for a search call. ``page`` is 1-based here."""
    return {"q": q.render(), "page": page, "size": size}


def merge_filters(existing: Sequence[Filter], extra: Iterable[Filter]) -> tuple[Filter, ...]:
    return tuple(existing) + tuple(extra)
