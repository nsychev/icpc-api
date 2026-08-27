"""Output formatting for the CLI."""

from __future__ import annotations

import csv
import enum
import json
import sys
from collections.abc import Sequence
from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.table import Table

__all__ = ["OutputFormat", "cell", "fail", "note", "render", "warn"]

#: Data console. Markup is off: a cell holding `members[i].role` or `[dim]` is a
#: value, not a style, and rich would otherwise swallow the brackets.
_console = Console(markup=False)
_err = Console(stderr=True)


class OutputFormat(enum.StrEnum):
    """How to print results. ``auto`` means a table on a terminal, JSON in a pipe."""

    AUTO = "auto"
    TABLE = "table"
    JSON = "json"
    NDJSON = "ndjson"
    CSV = "csv"
    TSV = "tsv"


def _resolve(fmt: OutputFormat) -> OutputFormat:
    if fmt is not OutputFormat.AUTO:
        return fmt
    return OutputFormat.TABLE if sys.stdout.isatty() else OutputFormat.JSON


def _plain(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(by_alias=True, exclude_none=True)
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, list | tuple):
        return [_plain(item) for item in value]
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    return value


#: Table cells wider than this are elided. Some columns carry whole JSON blobs
#: (staff labels, team rosters) and one of them would otherwise squeeze every
#: other column into a vertical stripe.
MAX_CELL = 60


def cell(value: Any, *, limit: int | None = None) -> str:
    """One value as text: booleans as yes/no, structures as JSON, ``None`` blank."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, list | dict):
        text = json.dumps(_plain(value), ensure_ascii=False)
    else:
        text = str(value)
    if limit is not None and len(text) > limit:
        return text[: limit - 1] + "…"
    return text


def _tsv_cell(value: Any) -> str:
    """A cell without tabs or newlines, to put into a TSV file."""
    text = cell(value)
    for char in ("\t", "\r", "\n"):
        text = text.replace(char, " ")
    return text


def _rows(data: Any) -> list[dict[str, Any]]:
    items = data if isinstance(data, list) else [data]
    out: list[dict[str, Any]] = []
    for item in items:
        plain = _plain(item)
        out.append(plain if isinstance(plain, dict) else {"value": plain})
    return out


def render(data: Any, fmt: OutputFormat, *, columns: Sequence[str] | None = None) -> None:
    """Print ``data`` in the requested format.

    ``columns`` restricts and orders the table, CSV and TSV output; JSON always carries
    everything, because that is what a pipeline consumer wants.
    """
    resolved = _resolve(fmt)

    if resolved is OutputFormat.JSON:
        _console.print_json(json.dumps(_plain(data), ensure_ascii=False, default=str))
        return

    rows = _rows(data)

    if resolved is OutputFormat.NDJSON:
        for row in rows:
            sys.stdout.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
        return

    if not rows:
        _err.print("[dim]no rows[/dim]")
        return

    headers = list(columns) if columns else _headers(rows)

    if resolved is OutputFormat.CSV:
        writer = csv.DictWriter(sys.stdout, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: cell(row.get(key)) for key in headers})
        return

    if resolved is OutputFormat.TSV:
        sys.stdout.write("\t".join(headers) + "\n")
        for row in rows:
            sys.stdout.write("\t".join(_tsv_cell(row.get(key)) for key in headers) + "\n")
        return

    table = Table(show_lines=False, header_style="bold")
    for header in headers:
        table.add_column(header, overflow="fold")
    for row in rows:
        table.add_row(*(cell(row.get(header), limit=MAX_CELL) for header in headers))
    _console.print(table)


def _headers(rows: Sequence[dict[str, Any]]) -> list[str]:
    """Union of the rows' keys, in first-seen order.

    Rows come back with unprojected columns dropped by ``exclude_none``, so the
    first row alone is not a reliable header set.
    """
    seen: dict[str, None] = {}
    for row in rows:
        for key in row:
            seen.setdefault(key, None)
    return list(seen)


def note(message: str) -> None:
    """Progress and confirmation, on stderr so stdout stays pipeable."""
    _err.print(f"[dim]{message}[/dim]")


def warn(message: str) -> None:
    _err.print(f"[yellow]{message}[/yellow]")


def fail(message: str) -> None:
    _err.print(f"[red]{message}[/red]")
