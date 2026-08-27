"""Columns for ``icpc contest load``: what a row can be read with.

:meth:`Icpc.load_contest` hands back a joined object graph; a CSV wants a flat
table. This module is the bridge: it turns the graph into plain dicts keyed by
the same column names the icpc.global grids use, and evaluates dotted paths —
``instName``, ``coaches[0].firstName``, ``institution.countryName`` — against
them, so a spreadsheet layout is expressible on the command line.
"""

from __future__ import annotations

import difflib
import enum
import re
import typing
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from icpc.cli.render import cell
from icpc.facade.domain import ContestView, Member, Team
from icpc.models._generated import (
    ContestParticipantRow,
    InstitutionRow,
    TeamMemberRow,
    TeamRow,
)
from icpc.models.entities import Contest

__all__ = [
    "RowKind",
    "apply_columns",
    "fields_of",
    "pluck",
    "resolve_columns",
    "rows_of",
    "source_of",
    "tables_for",
    "validate",
]

#: ``name``, ``name[3]``, ``name[*]`` or ``name[{i}]`` — one step of a path.
_STEP = re.compile(r"(?P<key>[^.\[\]]+)(?:\[(?P<index>-?\d+|\*)\])?$")
#: The same, but for a path whose repeats are not resolved yet, so ``[{i}]`` and
#: ``[{n}]`` count as indexes too. Only :func:`validate` sees those.
_STEP_ANY = re.compile(r"(?P<key>[^.\[\]]+)(?:\[(?P<index>-?\d+|\*|\{[in]\})\])?$")
#: The list a repeated column iterates over: the key in front of ``[{i}]``.
_LOOP = re.compile(r"(?P<list>[^.\[\]]+)\[\{[in]\}\]")
#: The default separator for a ``[*]`` column.
JOIN = ","


class RowKind(enum.StrEnum):
    """What one row of the output is."""

    TEAMS = "teams"
    MEMBERS = "members"
    INSTITUTIONS = "institutions"
    PARTICIPANTS = "participants"


def _dump(model: BaseModel | None) -> dict[str, Any]:
    """Wire-named fields, so paths match the column names the grids use."""
    return model.model_dump(by_alias=True) if model is not None else {}


def _grid(model: BaseModel, columns: type[BaseModel]) -> dict[str, Any]:
    """Just the grid's own columns of a joined row, plus anything new on the wire.

    ``Team`` and ``Member`` are their grid rows with the join's fields added, so
    the dump is restricted to the row type's columns; the join's own go on below
    under the names the paths use.
    """
    row = model.model_dump(by_alias=True, include=set(columns.model_fields))
    row.update(model.model_extra or {})
    return row


def _member(member: Member) -> dict[str, Any]:
    row = _grid(member, TeamMemberRow)
    # Without the teammember table the roster comes from each team's embedded
    # blob, whose completeness flag is the only one of these the grid columns do
    # not already carry.
    if row.get("completeRegistration") is None:
        row["completeRegistration"] = member.registration_complete
    row["participant"] = _dump(member.participant)
    row["extras"] = member.extras
    return row


def _team(team: Team, context: dict[str, Any] | None = None) -> dict[str, Any]:
    row = _grid(team, TeamRow)
    # The raw blob is replaced by the three roster lists below; keeping it would
    # put a wall of JSON in the default column set.
    row.pop("teamMembers", None)
    row["members"] = [_member(m) for m in team.members]
    row["coaches"] = [_member(m) for m in team.coaches]
    row["contestants"] = [_member(m) for m in team.contestants]
    row["other"] = [_member(m) for m in team.other]
    row["institution"] = _dump(team.institution)
    row["extras"] = team.extras
    context = context or {}
    row["contest"] = context.get("contest", {})
    # The site's id, joined on by name: the teams grid names a team's site but
    # never numbers it, and the id is what every site-scoped call wants.
    row["siteId"] = context.get("_sites", {}).get(team.site, {}).get("id")
    return row


def _context(view: ContestView) -> dict[str, Any]:
    """What the metadata fetch adds: the contest, and the sites by name.

    Team rows name their site but never carry its id, so the id every other
    site-scoped command wants — ``search site-teams``, ``contest set-site`` —
    is only reachable by joining the site list back on.
    """
    return {
        "contest": _dump(view.contest),
        "_sites": {site.name: _dump(site) for site in view.sites},
    }


def rows_of(view: ContestView, kind: RowKind) -> list[dict[str, Any]]:
    """Flatten one table out of the joined view.

    ``members`` is one row per *membership*, not per person: somebody on two
    teams appears twice, each row carrying its own ``teamId``.
    """
    context = _context(view)
    if kind is RowKind.TEAMS:
        return [_team(team, context) for team in view.teams]
    if kind is RowKind.MEMBERS:
        return [
            {
                **_member(member),
                "team": _team_ref(team, context),
                "contest": context["contest"],
            }
            for team in view.teams
            for member in team.members
        ]
    if kind is RowKind.INSTITUTIONS:
        return [_dump(row) for row in view.institutions.values()]
    return _participants(view)


def _participants(view: ContestView) -> list[dict[str, Any]]:
    """One row per *person*, with every membership they hold under ``memberships``.

    The participant table is one row per person already, but what it says about
    teams is flat text; the per-membership facts — the role, the team, whether
    they attend on site — live on the teammember rows. Collecting them here is
    what lets ``memberships[*].teamId`` answer a question about a person rather
    than about one of their memberships.
    """
    context = _context(view)
    rows: dict[int, dict[str, Any]] = {
        person_id: {**_dump(row), "memberships": [], "contest": context["contest"]}
        for person_id, row in view.people.items()
        if person_id is not None
    }
    for team in view.teams:
        for member in team.members:
            if member.person_id is None:
                continue
            row = rows.setdefault(
                member.person_id,
                {**_dump(member.participant), "memberships": [], "contest": context["contest"]},
            )
            row.setdefault("personId", member.person_id)
            row.setdefault("username", member.username)
            rows[member.person_id]["memberships"].append(
                {**_member(member), "team": _team_ref(team, context)}
            )
    return list(rows.values())


def _team_ref(team: Team, context: dict[str, Any] | None = None) -> dict[str, Any]:
    sites = (context or {}).get("_sites", {})
    return {
        "id": team.id,
        "name": team.name,
        "site": team.site,
        "siteId": sites.get(team.site, {}).get("id"),
        "status": team.status,
    }


#: The four roster lists on a team row. They hold the same fields; which
#: members land in each is the only difference.
ROSTERS = ("members", "coaches", "contestants", "other")


class Open:
    """A dict whose keys are data, not schema — ``extras``, keyed by the contest."""


@dataclass(frozen=True)
class ListOf:
    """A list; ``of`` is the shape of one element."""

    of: Shape


#: One level of an object: field name to whatever is under it. Split out from
#: :data:`Shape` because everything that *builds* a shape returns this branch,
#: and only a traversal has to cope with the others.
type Fields = dict[str, "Shape | ListOf"]

#: What a level of a row looks like: ``None`` is a scalar, a dict is an object,
#: and the two markers above cover lists and free-form dicts.
type Shape = Fields | type[Open] | None


def _nested(annotation: Any) -> type[BaseModel] | None:
    """The model inside ``X | None``, ``list[X]`` and friends, if there is one."""
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    for argument in typing.get_args(annotation):
        found = _nested(argument)
        if found is not None:
            return found
    return None


def _from_model(model: type[BaseModel], depth: int = 2) -> Fields:
    """A model's fields, expanding nested models while ``depth`` allows."""
    shape: Fields = {}
    for name, field in model.model_fields.items():
        inner = _nested(field.annotation) if depth > 0 else None
        shape[field.alias or name] = _from_model(inner, depth - 1) if inner else None
    return shape


def _member_shape() -> Fields:
    return {
        **_from_model(TeamMemberRow),
        "participant": _from_model(ContestParticipantRow),
        "extras": Open,
    }


def _team_ref_shape() -> Fields:
    return {"id": None, "name": None, "site": None, "siteId": None, "status": None}


def shape_of(kind: RowKind) -> Fields:
    """The full shape of one row kind: what every path is checked against."""
    if kind is RowKind.TEAMS:
        team = dict(_from_model(TeamRow))
        team.pop("teamMembers")  # replaced by the roster lists
        return {
            **team,
            "extras": Open,
            "siteId": None,
            "contest": _from_model(Contest),
            "institution": _from_model(InstitutionRow),
            **{roster: ListOf(_member_shape()) for roster in ROSTERS},
        }
    if kind is RowKind.MEMBERS:
        return {**_member_shape(), "team": _team_ref_shape(), "contest": _from_model(Contest)}
    if kind is RowKind.INSTITUTIONS:
        return _from_model(InstitutionRow)
    return {
        **_from_model(ContestParticipantRow),
        "memberships": ListOf({**_member_shape(), "team": _team_ref_shape()}),
        "contest": _from_model(Contest),
    }


def fields_of(kind: RowKind) -> list[dict[str, str]]:
    """Every path a ``--col`` can take for one row kind.

    Read off the models rather than off a fetch, so it answers instantly and
    without a contest. ``extras`` is keyed by the contest's own registration
    questions, so it can only be shown as a placeholder.

    Each path is reported with the table it reads, which is also what asking
    for it will make ``contest load`` fetch.
    """
    paths: list[str] = []

    def walk(shape: Shape, prefix: str) -> None:
        if shape is Open:
            paths.append(f"{prefix}<question>")
            return
        if not isinstance(shape, dict):
            paths.append(prefix.rstrip("."))
            return
        for key, value in shape.items():
            # The other three rosters hold identical fields, and `participant`
            # repeats a table listed in full elsewhere: spelling either out
            # would quadruple the listing without saying anything new.
            if prefix == "" and key in ROSTERS[1:]:
                continue
            if key == "participant":
                paths.append(f"{prefix}participant.<participant field>")
                continue
            if isinstance(value, ListOf):
                walk(value.of, f"{prefix}{key}[i].")
            elif value is None:
                paths.append(f"{prefix}{key}")
            else:
                walk(value, f"{prefix}{key}.")

    walk(shape_of(kind), "")
    # `[i]` is this listing's way of writing an index; the source rules want a
    # real one.
    return [{"path": path, "from": source_of(kind, path.replace("[i]", "[0]"))} for path in paths]


#: What a roster carries when the teammember table was *not* fetched: the fields
#: of each team row's embedded blob.
BLOB_FIELDS = frozenset({"personId", "username", "role", "completeRegistration"})

#: Which fetched table each top-level key comes from.
_NEEDS = {
    "institution": "institutions",
    "participant": "participants",
    "contest": "metadata",
    "siteId": "metadata",
}


#: What each row kind needs before any column is considered.
_BASE = {
    RowKind.TEAMS: {"teams"},
    RowKind.MEMBERS: {"teams", "members"},
    RowKind.INSTITUTIONS: {"teams", "institutions"},
    RowKind.PARTICIPANTS: {"teams", "members", "participants"},
}


def source_of(kind: RowKind, path: str) -> str:
    """Which fetched table a path reads.

    One table per path: the join hangs each sub-object off exactly one of them,
    and knowing which is what lets a column pay only for what it reads.
    """
    steps = [(_STEP_ANY.match(step) or {"key": step})["key"] for step in path.split(".")]
    for step in steps:
        if step in _NEEDS:
            return _NEEDS[step]
    if steps[0] in ROSTERS:
        # The embedded blob covers a roster of ids, usernames and roles; a real
        # name or a shirt size means the teammember table.
        return "teams" if set(steps[1:]) <= BLOB_FIELDS else "members"
    if steps[0] == "memberships":
        return "members"
    if steps[0] == "team":
        return "teams"
    return {
        RowKind.TEAMS: "teams",
        RowKind.MEMBERS: "members",
        RowKind.INSTITUTIONS: "institutions",
        RowKind.PARTICIPANTS: "participants",
    }[kind]


def tables_for(kind: RowKind, paths: Iterable[str]) -> set[str]:
    """The tables these columns actually need — the rest is not worth fetching.

    Each table is a full search over the contest, and most sheets touch two or
    three of them. Asking each path where it reads from is enough to skip the
    others.
    """
    return set(_BASE[kind]) | {source_of(kind, path) for path in paths}


def validate(kind: RowKind, path: str) -> None:
    """Check a ``--col`` path against the row's shape, or say what is wrong.

    The shapes come from the same models the rows are built from, so this
    catches a typo at any depth — not just the first hop — before a fetch that
    would otherwise take ten seconds to produce an empty column.
    """
    # Rebound to whatever is under each step, so it widens past the dict Fields is.
    shape: Shape | ListOf = shape_of(kind)
    walked: list[str] = []
    for step in path.split("."):
        match = _STEP_ANY.match(step)
        if match is None:
            raise ValueError(f"{step!r} is not a field name in {path!r}")
        key, index = match["key"], match["index"]
        if shape is Open:  # below `extras` anything is a question id
            return
        if isinstance(shape, ListOf):
            here = ".".join(walked)
            raise ValueError(f"{here!r} is a list in {path!r}; index it as {here}[i] or {here}[*]")
        if not isinstance(shape, dict):
            raise ValueError(f"{'.'.join(walked)!r} is a value in {path!r}; nothing is under it")
        if key not in shape:
            raise ValueError(_unknown(key, path, walked, shape))
        walked.append(step)
        found = shape[key]
        if index is not None:
            if not isinstance(found, ListOf):
                raise ValueError(f"{key!r} is not a list in {path!r}, so it cannot be indexed")
            found = found.of
        # A bare list is a legal final column; only stepping *into* one needs an
        # index, which the ListOf branch above catches on the next lap.
        shape = found


def _unknown(key: str, path: str, walked: list[str], shape: dict[str, Any]) -> str:
    where = f" under {'.'.join(walked)!r}" if walked else ""
    close = difflib.get_close_matches(key, list(shape), n=3, cutoff=0.5)
    hint = f"; did you mean {', '.join(close)}?" if close else f"; try --fields{where and ''}"
    return f"unknown field {key!r}{where} in {path!r}{hint}"


def _is_list(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def pluck(row: dict[str, Any], path: str) -> Any:
    """Follow a dotted path, returning ``None`` wherever it runs out.

    A missing key and a short list are both ordinary here — the fourth
    contestant of a three-person team is simply blank, not an error.

    ``[*]`` maps the rest of the path over a list and returns every answer, so
    ``memberships[*].teamId`` is all of a person's team ids. Blanks are dropped,
    and nested wildcards flatten into one list.
    """
    return _walk(row, path.split("."))


def _walk(current: Any, steps: Sequence[str]) -> Any:
    for position, step in enumerate(steps):
        match = _STEP.match(step)
        if match is None or not isinstance(current, dict):
            return None
        current = current.get(match["key"])
        index = match["index"]
        if index is not None:
            if not _is_list(current):
                return None
            if index == "*":
                return _map(current, steps[position + 1 :])
            offset = int(index)
            current = current[offset] if -len(current) <= offset < len(current) else None
        if current is None:
            return None
    return current


def _map(items: Sequence[Any], steps: Sequence[str]) -> list[Any]:
    out: list[Any] = []
    for item in items:
        value = _walk(item, steps) if steps else item
        if _is_list(value):
            out.extend(v for v in value if v is not None)
        elif value is not None:
            out.append(value)
    return out


def _loop_length(rows: Iterable[dict[str, Any]], list_path: str) -> int:
    longest = 0
    for row in rows:
        value = pluck(row, list_path)
        if isinstance(value, Sequence) and not isinstance(value, str | bytes):
            longest = max(longest, len(value))
    return longest


def resolve_columns(
    specs: Sequence[str],
    rows: Sequence[dict[str, Any]],
    repeats: dict[str, int] | None = None,
) -> list[tuple[str, str]]:
    """Resolve ``NAME=PATH`` specs into the concrete ``(name, path)`` columns.

    A spec is what a person writes; a column is what a row is read with. The
    difference is the repeats, which only the data can settle.

    A spec whose path indexes a list with ``[{i}]`` is repeated over that list:
    ``'C{n}.First=contestants[{i}].firstName'`` becomes ``C1.First``,
    ``C2.First``, … ``{i}`` is the 0-based index used in the path and ``{n}``
    is the 1-based counter that usually reads better in a header.

    How many times it repeats is the longest such list in the data, so the
    table is as wide as it needs to be; ``repeats`` pins a list to a fixed
    length instead, which is what you want when the columns of a sheet have to
    stay put between runs.

    Consecutive specs over the *same* list are resolved together, one group per
    index — ``C1.First, C1.Last, C2.First, C2.Last``, not all the firsts
    followed by all the lasts. That is the order a person reads a roster in.
    """
    repeats = repeats or {}
    out: list[tuple[str, str]] = []
    for list_path, group in _grouped(specs):
        if list_path is None:
            out.extend(group)
            continue
        list_name = list_path.rsplit(".", 1)[-1]
        count = repeats.get(list_name, repeats.get(list_path, _loop_length(rows, list_path)))
        for index in range(count):
            subs = {"{i}": str(index), "{n}": str(index + 1)}
            out.extend((_substitute(name, subs), _substitute(path, subs)) for name, path in group)
    return out


def _grouped(specs: Sequence[str]) -> list[tuple[str | None, list[tuple[str, str]]]]:
    """Split specs into runs, each run being consecutive columns over one list.

    ``None`` marks a run of plain, unrepeated columns.
    """
    groups: list[tuple[str | None, list[tuple[str, str]]]] = []
    for spec in specs:
        name, sep, path = spec.partition("=")
        if not sep:
            # `--col instName` is `--col instName=instName`: most columns are
            # wanted under the name the grid already gives them.
            name, path = spec, spec
        if not name or not path:
            raise ValueError(f"column {spec!r} is not NAME=PATH")
        loop = _LOOP.search(path)
        key = path[: loop.end("list")] if loop else None
        if groups and groups[-1][0] == key:
            groups[-1][1].append((name, path))
        else:
            groups.append((key, [(name, path)]))
    return groups


def _substitute(text: str, subs: dict[str, str]) -> str:
    for placeholder, value in subs.items():
        text = text.replace(placeholder, value)
    return text


def apply_columns(
    rows: Sequence[dict[str, Any]],
    columns: Sequence[tuple[str, str]],
    join: str = JOIN,
) -> list[dict]:
    """Apply resolved columns to every row.

    A ``[*]`` column collapses its list into one cell, joined by ``join`` — a
    spreadsheet wants ``1234571,1234569`` in a ``TeamIds`` column, not a JSON
    array. Every other list is left alone for the renderer to format.
    """
    out = []
    for row in rows:
        cells: dict[str, Any] = {}
        for name, path in columns:
            value = pluck(row, path)
            cells[name] = join.join(cell(v) for v in value) if "[*]" in path else value
        out.append(cells)
    return out
