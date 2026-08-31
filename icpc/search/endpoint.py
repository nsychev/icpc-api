"""A bound search endpoint: path, row type, and its typed columns.

``SearchEndpoint`` only *builds* operations; sending them is the client's job. That
keeps every search reusable from both the async and the sync side and makes the
request assertable in tests without a network.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from icpc.config import DEFAULT_PAGE_SIZE
from icpc.errors import EmptyProjection, SearchError
from icpc.models.common import FileRef
from icpc.models.enums import ExportType
from icpc.search.dsl import Filter, FilterMode, Q, SortKey
from icpc.transport.operation import Operation, Request, list_op, model_op, scalar_op

__all__ = ["SearchEndpoint"]


@dataclass(frozen=True, slots=True)
class SearchEndpoint[RowT, FieldsT]:
    """One ``/search`` path with its ``/count`` and ``/export`` siblings."""

    path: str
    row: type[RowT]
    fields: FieldsT
    #: Columns the icpc.global grid shows by default.
    default_proj: tuple[str, ...]
    #: Every column the endpoint understands.
    all_fields: tuple[str, ...]
    name: str
    #: Whether the server honours ``filter:`` here at all. False for the handful
    #: of grids that accept the term and return everything anyway — see
    #: :meth:`validate`.
    filterable: bool = True

    # ------------------------------------------------------------ queries --

    def query(
        self,
        *,
        proj: Iterable[str] | None = None,
        filters: Iterable[Filter] = (),
        sort: Iterable[SortKey] = (),
        mode: FilterMode = "and",
    ) -> Q:
        """Build a query for this endpoint.

        The projection defaults to the columns the icpc.global grid itself requests.
        That is deliberately not *every* column: six of the grids answer 500 when
        asked for their full field set, while every grid accepts its own defaults.

        Columns named in ``filters`` or ``sort`` are added to the projection
        automatically. They have to be there — see :meth:`validate`.
        """
        columns = list(proj) if proj is not None else list(self.default_proj)
        filters = list(filters)
        sort = list(sort)
        for name in [f.column for f in filters] + [s.column for s in sort]:
            if name not in columns:
                columns.append(name)
        query = Q.build(columns, filters, sort, mode)
        self.validate(query)
        return query

    def validate(self, q: Q) -> None:
        """Refuse a query the server would reject or, worse, quietly misanswer."""
        self.validate_proj(q.proj)

        if q.filters and not self.filterable:
            raise SearchError(f"Server does not support filters for endpoint {self.name}.")

        # Filtering and sorting apply *only* to columns present in the projection.
        # A filter on an unprojected column is ignored without a word and the full
        # result set comes back looking perfectly correct, so this is checked
        # rather than trusted.
        projected = set(q.proj)
        ignored = sorted({f.column for f in q.filters} - projected)
        if ignored:
            raise SearchError(
                f"{self.name}: filter column(s) {ignored} are not in the projection, "
                f"so the server would ignore them and return everything. Add them to "
                f"proj, or use this endpoint's query() which does it for you."
            )
        unsorted = sorted({s.column for s in q.sort} - projected)
        if unsorted:
            raise SearchError(
                f"{self.name}: sort column(s) {unsorted} are not in the projection, "
                f"so the ordering would be ignored. Add them to proj."
            )

    def validate_proj(self, proj: Sequence[str]) -> None:
        """Refuse a projection the server would reject or silently ignore.

        A projection naming no valid column returns 500; individually unknown names
        are dropped without a word, which is worse, so we raise on those too.
        """
        if not proj:
            return
        unknown = [name for name in proj if name not in self.all_fields]
        if len(unknown) == len(proj):
            raise EmptyProjection(
                f"{self.name}: none of {list(proj)} is a column of this endpoint; "
                f"the server would answer 500"
            )
        if unknown:
            raise EmptyProjection(
                f"{self.name}: unknown column(s) {unknown}; the server would ignore "
                f"them and return null. Valid columns: {', '.join(self.all_fields)}"
            )

    def _checked(self, q: Q | None) -> Q:
        """Default the query, and validate one the caller built by hand."""
        if q is None:
            return self.query()
        self.validate(q)
        return q

    # --------------------------------------------------------- operations --

    def rows(
        self, q: Q | None = None, *, page: int = 1, size: int = DEFAULT_PAGE_SIZE
    ) -> Operation[list[RowT]]:
        """One page of results. ``page`` is 1-based; the body is a bare array."""
        query = self._checked(q)
        return list_op(
            Request(
                "GET",
                self.path,
                params={"q": query.render(), "page": page, "size": size},
                slow=size >= DEFAULT_PAGE_SIZE,
            ),
            self.row,
        )

    def count(self, q: Q | None = None) -> Operation[int]:
        """Total matching rows.

        The list response carries no total, so paging needs this second call — the
        frontend fires both at once for exactly this reason.

        Filters apply here on the same terms as they do to :meth:`rows`, so a count
        and its listing agree only when both carry the same projection.
        """
        query = self._checked(q)
        return scalar_op(
            Request(
                "GET",
                f"{self.path}/count",
                params={"q": query.render(), "page": 1, "size": 1},
            ),
            int,
        )

    def export(
        self, q: Q | None = None, export_type: ExportType | str = ExportType.CSV
    ) -> Operation[FileRef]:
        """Ask the server to render the current query as a file.

        The result arrives inline: ``data`` is base64 and ``mime`` is null, for both
        CSV and Excel. Use :meth:`~icpc.models.common.FileRef.content` to decode.
        """
        query = self._checked(q)
        return model_op(
            Request(
                "GET",
                f"{self.path}/export",
                params={"q": query.render(), "type": str(export_type)},
                slow=True,
            ),
            FileRef,
        )

    def field_names(self, *fields: Any) -> tuple[str, ...]:
        """Column names for a mix of :class:`~icpc.search.fields.Field` objects and strings."""
        return tuple(f.name if hasattr(f, "name") else str(f) for f in fields)
