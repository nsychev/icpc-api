"""``icpc`` — command-line access to the icpc.global API.

The CLI drives the synchronous client; that is the main reason a synchronous
client exists.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated, Any

import typer

from icpc import errors
from icpc.api import common as common_api
from icpc.api import contest as contest_api
from icpc.api import person as person_api
from icpc.api import public as public_api
from icpc.api import staff as staff_api
from icpc.api import team as team_api
from icpc.api.person import ReferenceRole
from icpc.api.team import NewTeam, NewTeamMember
from icpc.auth.cognito import Challenge
from icpc.auth.flows import CognitoAuth
from icpc.auth.store import CredentialStore
from icpc.cli.columns import (
    JOIN,
    ROSTERS,
    RowKind,
    apply_columns,
    fields_of,
    resolve_columns,
    rows_of,
    tables_for,
    validate,
)
from icpc.cli.render import OutputFormat, fail, note, render, warn
from icpc.config import Settings
from icpc.facade.client import Icpc, Include
from icpc.models.enums import ExportType, MemberRole, TeamStatus
from icpc.search import _generated as endpoints
from icpc.search.dsl import Filter, SortKey
from icpc.search.endpoint import SearchEndpoint
from icpc.transport.operation import Request, json_op

app = typer.Typer(no_args_is_help=True, help=__doc__, add_completion=True)
auth_app = typer.Typer(no_args_is_help=True, help="Log in and manage cached tokens.")
contest_app = typer.Typer(no_args_is_help=True, help="Read contests and their grids.")
team_app = typer.Typer(no_args_is_help=True, help="Read and modify teams.")
public_app = typer.Typer(no_args_is_help=True, help="Public endpoints; no login needed.")
person_app = typer.Typer(no_args_is_help=True, help="Look people up.")
staff_app = typer.Typer(no_args_is_help=True, help="Contest staff.")
app.add_typer(auth_app, name="auth")
app.add_typer(contest_app, name="contest")
app.add_typer(team_app, name="team")
app.add_typer(public_app, name="public")
app.add_typer(person_app, name="person")
app.add_typer(staff_app, name="staff")


@dataclass
class Context:
    output: OutputFormat
    username: str | None


def _ctx(ctx: typer.Context) -> Context:
    return ctx.ensure_object(Context)


def _client(ctx: typer.Context) -> Icpc:
    """Build a client from whatever credentials are available.

    An explicit token in the environment wins, so CI and one-off shells do not
    need a login; otherwise the tokens cached by ``icpc auth login`` are used.
    """
    state = _ctx(ctx)
    if os.environ.get("ICPC_ID_TOKEN") or os.environ.get("ICPC_REFRESH_TOKEN"):
        return Icpc.from_token()
    return Icpc.from_store(state.username)


#: The search grids exposed as `icpc contest <name>` and `icpc search <name>`.
GRIDS: dict[str, Any] = {
    "teams": endpoints.contest_teams,
    "members": endpoints.contest_team_members,
    "institutions": endpoints.contest_institutions,
    "participants": endpoints.contest_participants,
    "staff": endpoints.contest_staff,
    "staff-members": endpoints.contest_staff_members,
    "standings": endpoints.contest_standings,
    "top20": endpoints.contest_top20,
    "summaries": endpoints.contest_team_summaries,
    "promote-candidates": endpoints.contest_promote_candidates,
    "certificates": endpoints.contest_team_certificates,
    "site-teams": endpoints.site_teams,
    "site-members": endpoints.site_team_members,
    "site-institutions": endpoints.site_institutions,
    "site-participants": endpoints.site_participants,
}


@app.callback()
def main(
    ctx: typer.Context,
    output: Annotated[
        OutputFormat, typer.Option("--output", "-o", help="Output format.")
    ] = OutputFormat.AUTO,
    username: Annotated[
        str | None,
        typer.Option("--user", "-u", envvar="ICPC_USERNAME", help="Which cached account to use."),
    ] = None,
) -> None:
    ctx.obj = Context(output=output, username=username)


# -------------------------------------------------------------------- auth --


@auth_app.command("login")
def auth_login(
    ctx: typer.Context,
    username: Annotated[str | None, typer.Option("--username", prompt=True)] = None,
    password: Annotated[
        str | None, typer.Option("--password", prompt=True, hide_input=True)
    ] = None,
    save_password: Annotated[
        bool,
        typer.Option(
            "--save-password/--no-save-password",
            help="Store the password so the session can renew itself after an hour.",
        ),
    ] = True,
) -> None:
    """Log in with your icpc.global email and password.

    Tokens are cached under ``~/.config/icpc``. By default the password is cached
    alongside them, because this Cognito app client has no working refresh-token
    flow: without a stored password every command more than an hour after a login
    would prompt again, and unattended jobs could not run at all.

    It is stored base64-encoded, which is obfuscation and not encryption — anyone
    who can read the file can recover it. Pass ``--no-save-password`` to keep it
    out of the file and accept the hourly re-prompt.
    """
    store = CredentialStore()
    auth = CognitoAuth(
        store=store,
        settings=Settings(),
        save_password=save_password,
        # A fresh login is the account you meant to use from now on.
        make_default=True,
    )
    assert username is not None and password is not None  # noqa: S101 - typer prompts fill these
    try:
        tokens = auth.login(username, password)
    except errors.MfaRequired as required:
        code = typer.prompt("MFA code")
        challenge = Challenge(required.challenge, required.session, {})
        tokens = auth.complete_mfa(challenge, username, code)
    note(f"logged in as {tokens.username}")
    if save_password:
        note(
            f"password saved base64-encoded (not encrypted) in {store.path}; "
            f"`icpc auth forget-password` removes it"
        )


@auth_app.command("use")
def auth_use(username: Annotated[str, typer.Argument(help="Account to make the default.")]) -> None:
    """Choose which cached account commands use when none is named."""
    if not CredentialStore().set_default(username):
        fail(f"{username} is not cached; `icpc auth status` lists what is")
        raise typer.Exit(1)
    note(f"now using {username}")


@auth_app.command("status")
def auth_status(ctx: typer.Context) -> None:
    """Show the cached accounts and whether their sessions can renew themselves."""
    store = CredentialStore()
    current = store.default_username()
    rows = []
    for username in store.usernames():
        account = store.load(username)
        if account is None:
            continue
        tokens = account.tokens
        expires = (
            datetime.fromtimestamp(tokens.expires_at, UTC).strftime("%Y-%m-%d %H:%M UTC")
            if tokens and tokens.expires_at
            else None
        )
        rows.append(
            {
                "username": username,
                "in_use": username == current,
                "token_expires": expires,
                "expired": tokens.expired(0) if tokens else True,
                # Never the password itself, only whether one is on disk.
                "password": account.password is not None,
            }
        )
    if not rows:
        warn("no cached credentials; run `icpc auth login`")
        raise typer.Exit(1)
    render(rows, _ctx(ctx).output)


@auth_app.command("logout")
def auth_logout(
    username: Annotated[str | None, typer.Argument(help="Account to forget; omit for all.")] = None,
) -> None:
    """Delete cached credentials — tokens and any stored password."""
    if not CredentialStore().delete(username):
        warn("nothing to delete")
        raise typer.Exit(1)


@auth_app.command("forget-password")
def auth_forget_password(
    username: Annotated[str | None, typer.Argument(help="Account; omit for all.")] = None,
) -> None:
    """Remove the stored password but stay logged in.

    The current token keeps working until it expires; after that, commands will
    prompt for the password again.
    """
    if not CredentialStore().forget_password(username):
        warn("no stored password to remove")
        raise typer.Exit(1)


@auth_app.command("token")
def auth_token(ctx: typer.Context) -> None:
    """Print the current id token. Treat it as a password."""
    with _client(ctx) as icpc:
        token = icpc.id_token()
    sys.stdout.write(token + "\n")


@app.command("my-contests")
def my_contests(
    ctx: typer.Context,
    icpc_year: Annotated[
        int, typer.Argument(help="ICPC season year, as the cabinet's year picker shows it.")
    ],
    role: Annotated[
        ReferenceRole, typer.Option("--role", help="Which kind of access to list.")
    ] = ReferenceRole.CONTEST_MANAGER,
) -> None:
    """Contests you have access to, for one ICPC season.

    With the default role this is what the icpc.global cabinet lists on its
    front page: the contests you can administer.

    The year is the ICPC season, not the calendar year — a contest held in 2026
    is listed under 2027.
    """
    with _client(ctx) as icpc:
        rows = icpc.my_contests(icpc_year, role)
    if not rows:
        warn(f"no contests for {role} in season {icpc_year}")
        raise typer.Exit(1)
    columns = ["contestId", "contest"]
    if any(r.team_id for r in rows):
        columns += ["team", "teamRole", "site"]
    render(rows, _ctx(ctx).output, columns=columns)


@app.command("whoami")
def whoami(ctx: typer.Context) -> None:
    """Show which account the cached token belongs to."""
    with _client(ctx) as icpc:
        render(icpc.whoami(), _ctx(ctx).output)


def _one_id(ctx: typer.Context, rows: list[Any], term: str) -> None:
    """Print exactly one id, for shell substitution.

    Refuses to guess: several matches means the caller must narrow the search,
    because silently taking the first would put the wrong id into a command.
    """
    ids = [r.id for r in rows if getattr(r, "id", None) is not None]
    if len(ids) > 1:
        fail(f"{len(ids)} matches for {term!r}; narrow it: " + ", ".join(str(i) for i in ids[:8]))
        raise typer.Exit(1)
    sys.stdout.write(f"{ids[0]}\n")


# ------------------------------------------------------------------ people --


@person_app.command("find")
def person_find(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Name or email; three characters or more.")],
    limit: Annotated[int, typer.Option("--limit", help="How many matches to return.")] = 10,
    id_only: Annotated[
        bool, typer.Option("--id", help="Print just the id, for $(...). Fails unless unique.")
    ] = False,
) -> None:
    """Find a person id by name or email.

    This is the lookup behind the web UI's person picker, and the way to get the
    person id that `team register` and `staff add` need.

        icpc staff add 12345 --person $(icpc person find root@nsychev.ru --id) \\
            --badge-role Judge
    """
    with _client(ctx) as icpc:
        rows = icpc.send(person_api.suggest(name, size=limit))
    if not rows:
        warn(f"nobody matches {name!r}")
        raise typer.Exit(1)
    if id_only:
        _one_id(ctx, list(rows), name)
        return
    render(rows, _ctx(ctx).output, columns=["id", "username", "firstName", "lastName"])


@person_app.command("show")
def person_show(ctx: typer.Context, person_id: int) -> None:
    """A person's record."""
    with _client(ctx) as icpc:
        render(icpc.send(person_api.get(person_id)), _ctx(ctx).output)


@app.command("institution")
def institution_find(
    ctx: typer.Context,
    name: Annotated[str, typer.Argument(help="Institution name; three characters or more.")],
    limit: Annotated[int, typer.Option("--limit")] = 10,
    id_only: Annotated[
        bool, typer.Option("--id", help="Print just the id, for $(...). Fails unless unique.")
    ] = False,
) -> None:
    """Find an institution id, for registering a team.

    The id printed here is the one `team register --institution` wants. It is a
    different number from the `instId` and `instUnitId` columns of the
    `institutions` grid, which point at other tables.
    """
    with _client(ctx) as icpc:
        rows = icpc.send(common_api.institution_suggest(name, size=limit))
    if not rows:
        warn(f"no institution matches {name!r}")
        raise typer.Exit(1)
    if id_only:
        _one_id(ctx, list(rows), name)
        return
    render(rows, _ctx(ctx).output, columns=["id", "name", "country", "url"])


# ------------------------------------------------------------------- staff --


@staff_app.command("add")
def staff_add(
    ctx: typer.Context,
    site_id: Annotated[int, typer.Argument(help="Site to attach the person to.")],
    person_id: Annotated[int, typer.Option("--person", help="Person id; see `icpc person find`.")],
    badge_role: Annotated[str, typer.Option("--badge-role", help="Printed on the badge.")],
    certificate_role: Annotated[
        str | None, typer.Option("--certificate-role", help="Defaults to --badge-role.")
    ] = None,
    public: Annotated[
        bool, typer.Option("--public", help="Show on the contest's public pages.")
    ] = False,
) -> None:
    """Attach a person to a site as staff."""
    with _client(ctx) as icpc:
        result = icpc.send(
            staff_api.add(
                site_id,
                person_id,
                badge_role=badge_role,
                certificate_role=certificate_role or badge_role,
                show_in_public_pages=public,
            )
        )
    note(f"staff member {result.get('id')} added to site {site_id}")
    render({"id": result.get("id")}, _ctx(ctx).output)


@staff_app.command("list")
def staff_list(ctx: typer.Context, contest_id: int) -> None:
    """Staff of a contest."""
    endpoint = endpoints.contest_staff_members(contest_id)
    with _client(ctx) as icpc:
        rows = icpc.all(endpoint)
    render(rows, _ctx(ctx).output, columns=list(endpoint.default_proj))


@staff_app.command("remove")
def staff_remove(ctx: typer.Context, staff_member_id: int) -> None:
    """Remove a staff member."""
    with _client(ctx) as icpc:
        icpc.send(staff_api.delete(staff_member_id))
    note(f"staff member {staff_member_id} removed")


# ----------------------------------------------------------------- contest --


@contest_app.command("show")
def contest_show(ctx: typer.Context, contest_id: int) -> None:
    """Contest metadata and settings."""
    with _client(ctx) as icpc:
        render(icpc.send(contest_api.get(contest_id)), _ctx(ctx).output)


@contest_app.command("sites")
def contest_sites(ctx: typer.Context, contest_id: int) -> None:
    """Sites of a contest, with capacity and registration flags."""
    with _client(ctx) as icpc:
        render(icpc.send(contest_api.site_table(contest_id)), _ctx(ctx).output)


@contest_app.command("stats")
def contest_stats(ctx: typer.Context, contest_id: int) -> None:
    """Counts of sites, managers, and pending versus accepted teams."""
    with _client(ctx) as icpc:
        render(icpc.send(contest_api.stats(contest_id)), _ctx(ctx).output)


@contest_app.command("set")
def contest_set(
    ctx: typer.Context,
    contest_id: int,
    changes: Annotated[list[str], typer.Argument(help="KEY=VALUE, e.g. name='New name'.")],
) -> None:
    """Change a contest's own fields.

    icpc contest set 1235 geographicArea="Northern Eurasia" email=me@example.com
    """
    _edit(
        ctx,
        "contest",
        contest_api.get(contest_id),
        lambda o: contest_api.update(contest_id, o),
        changes,
    )


@contest_app.command("set-settings")
def contest_set_settings(
    ctx: typer.Context,
    contest_id: int,
    changes: Annotated[list[str], typer.Argument(help="KEY=VALUE.")],
) -> None:
    """Change the contest settings block.

    icpc contest set-settings 1235 requireCertification=true
    icpc contest set-settings 1235 showPublicPages=WITH_PEOPLE
    """
    _edit(
        ctx,
        "contest settings",
        contest_api.settings(contest_id),
        lambda o: contest_api.update_settings(contest_id, o),
        changes,
    )


@contest_app.command("set-registration")
def contest_set_registration(
    ctx: typer.Context,
    contest_id: int,
    changes: Annotated[list[str], typer.Argument(help="KEY=VALUE.")],
) -> None:
    """Change the registration rules.

    icpc contest set-registration 1235 allowStudentCoach=true maxCoaches=2
    """
    _edit(
        ctx,
        "registration info",
        contest_api.registration_info(contest_id),
        lambda o: contest_api.update_registration_info(contest_id, o),
        changes,
    )


@contest_app.command("set-site")
def contest_set_site(
    ctx: typer.Context,
    contest_id: int,
    site_id: Annotated[int, typer.Option("--site", help="Site whose settings to change.")],
    changes: Annotated[list[str], typer.Argument(help="KEY=VALUE.")],
) -> None:
    """Change a site's settings.

        icpc contest set-site 1235 --site 12345 allowRegistration=true allowTeamChanges=true

    While `allowTeamChanges` is false the server answers 500 — not a clean
    refusal — to any attempt to add or remove a team member.
    """
    _edit(
        ctx,
        "site settings",
        contest_api.site_settings(site_id),
        lambda o: contest_api.update_site_settings(contest_id, o),
        changes,
    )


@contest_app.command("summary")
def contest_summary(ctx: typer.Context, contest_id: int) -> None:
    """Team counts by site and by status, from one joined fetch."""
    with _client(ctx) as icpc:
        view = icpc.load_contest(contest_id, Include.TEAMS)
    rows = [
        {"site": site or "—", "teams": len(teams)}
        for site, teams in sorted(view.by_site().items(), key=lambda item: str(item[0]))
    ]
    render(rows, _ctx(ctx).output, columns=["site", "teams"])


def _include(kind: RowKind, paths: Sequence[str]) -> Include:
    """Which tables the requested columns actually need.

    Every table is a full search over the contest, so a sheet that never
    mentions an institution has no reason to wait for the institution table.

    With no columns the whole row is the output — and `-o json` carries all of
    it — so there is nothing to read the answer off, and the usual four tables
    are fetched.
    """
    if not paths:
        return Include.DEFAULT
    tables = tables_for(kind, paths)
    note(f"fetching {', '.join(sorted(tables))}")
    return Include.named(tables)


@contest_app.command("load")
def contest_load(
    ctx: typer.Context,
    contest_id: Annotated[
        int | None,
        typer.Argument(help="Contest to load. Not needed with --fields."),
    ] = None,
    rows: Annotated[
        RowKind, typer.Option("--rows", help="What one output row is.")
    ] = RowKind.TEAMS,
    col: Annotated[
        list[str] | None,
        typer.Option("--col", help="NAME=PATH, or bare PATH; repeatable."),
    ] = None,
    join: Annotated[str, typer.Option("--join", help="Separator for a `[*]` column.")] = JOIN,
    repeat: Annotated[
        list[str] | None,
        typer.Option("--repeat", help="LIST=COUNT: pin a repeated column's width."),
    ] = None,
    fields: Annotated[
        bool, typer.Option("--fields", help="List the paths `--col` can take, and exit.")
    ] = False,
) -> None:
    """Fetch a whole contest in one go and flatten it into a table.

    This is `load_contest`: teams, rosters, institutions and metadata in a
    single joined fetch, rather than four grid queries stitched together by
    hand. Every column of the underlying grids is asked for, so `--col` can
    reach anything by its icpc.global name.

        icpc -o csv contest load 1234 --col id --col Team=name \\
            --col Coach='coaches[0].firstName' --col Uni='institution.instName'

    `--col NAME=PATH` names a column; a bare `--col PATH` keeps the grid's own
    name. A path may index a roster — `coaches`, `contestants`, `other`,
    `members` — or step into `institution`, `participant` and `extras`.

    `[{i}]` repeats a column across a list, `{n}` being the 1-based counter for
    the header:

        --col 'C{n}.Id=contestants[{i}].username'

    That widens the table to the largest roster in the contest; `--repeat
    contestants=3` pins it, which is what a spreadsheet with fixed columns
    wants.

    `[*]` instead collects the whole list into one cell, joined by `--join`:

        icpc contest load 1234 --rows participants \\
            --col Id=username --col TeamIds='memberships[*].teamId'

    Which tables are fetched follows from the columns: naming an `institution`
    field fetches institutions, a roster field fetches the rosters, and nothing
    else is waited for. With no `--col` the whole row is the output, so the
    usual four tables are fetched.
    """
    if fields:
        # Read off the models, so this answers without fetching the contest.
        if rows is RowKind.TEAMS:
            note(f"the roster fields work under any of: {', '.join(ROSTERS)}")
        render(fields_of(rows), _ctx(ctx).output, columns=["path", "from"])
        return
    if contest_id is None:
        raise typer.BadParameter("a contest id is required unless you pass --fields")
    try:
        pins = {k: int(v) for k, v in _assignments(repeat or []).items()}
    except (TypeError, ValueError) as exc:
        raise typer.BadParameter("--repeat wants LIST=COUNT, e.g. contestants=3") from exc
    # The path is the half after the name; both the check below and the choice
    # of tables read it, and neither wants the `NAME=` in front.
    paths = [spec.rpartition("=")[2] for spec in col or []]
    # Check them against the row's shape first: a typo should cost a message,
    # not a ten-second fetch that ends in an empty column.
    for path in paths:
        try:
            validate(rows, path)
        except ValueError as exc:
            raise typer.BadParameter(
                f"{exc}\nRun `icpc contest load --fields` to see them."
            ) from exc
    with _client(ctx) as icpc:
        view = icpc.load_contest(contest_id, _include(rows, paths))
    table = rows_of(view, rows)
    if not col:
        # No layout asked for: every scalar field, which is the grid's own shape.
        flat = [k for k, v in (table[0] if table else {}).items() if not isinstance(v, list | dict)]
        render(table, _ctx(ctx).output, columns=flat)
        return
    try:
        columns = resolve_columns(col, table, pins)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc
    render(
        apply_columns(table, columns, join), _ctx(ctx).output, columns=[name for name, _ in columns]
    )


def _assignments(pairs: list[str]) -> dict[str, Any]:
    """Parse ``key=value`` arguments, coercing the obvious literals.

    ``true``/``false``/``null`` and bare numbers become JSON values; everything
    else stays a string. Wrap a value in quotes to force a string.
    """
    out: dict[str, Any] = {}
    for pair in pairs:
        key, sep, raw = pair.partition("=")
        if not sep:
            raise typer.BadParameter(f"expected KEY=VALUE, got {pair!r}")
        low = raw.lower()
        if low in ("true", "false"):
            out[key] = low == "true"
        elif low in ("null", "none"):
            out[key] = None
        elif raw.lstrip("-").isdigit():
            out[key] = int(raw)
        else:
            out[key] = raw.strip('"')
    return out


def _edit(ctx: typer.Context, label: str, read: Any, write: Any, pairs: list[str]) -> None:
    """Read a settings object, apply ``key=value`` changes, write it back.

    These endpoints are full-object replaces, so the read is not optional: send
    only the changed keys and everything else is wiped.
    """
    changes = _assignments(pairs)
    with _client(ctx) as icpc:
        current = icpc.send(read)
        obj = current if isinstance(current, dict) else current.model_dump(by_alias=True)
        unknown = [k for k in changes if k not in obj]
        if unknown:
            fail(f"{label} has no field(s) {unknown}; known: {', '.join(sorted(obj))}")
            raise typer.Exit(1)
        for key, value in changes.items():
            note(f"{key}: {obj.get(key)!r} -> {value!r}")
        icpc.send(write({**obj, **changes}))
        after = icpc.send(read)
    render(after, _ctx(ctx).output)


def _grid(name: str, entity_id: int) -> SearchEndpoint[Any, Any]:
    factory = GRIDS.get(name)
    if factory is None:
        raise typer.BadParameter(f"unknown grid {name!r}; try one of: {', '.join(GRIDS)}")
    return factory(entity_id)


def _parse_filters(raw: list[str]) -> list[Filter]:
    filters = []
    for item in raw:
        column, _, value = item.partition("#")
        if not value:
            raise typer.BadParameter(f"filter must be COLUMN#VALUE, got {item!r}")
        filters.append(Filter.of(column, value))
    return filters


def _parse_sort(raw: list[str]) -> list[SortKey]:
    keys = []
    for item in raw:
        column, _, direction = item.partition(":")
        if direction not in {"", "asc", "desc"}:
            raise typer.BadParameter(f"sort direction must be asc or desc, got {direction!r}")
        keys.append(SortKey(column, direction or "asc"))  # type: ignore[arg-type]
    return keys


@app.command("search")
def search(
    ctx: typer.Context,
    grid: Annotated[str, typer.Argument(help=f"One of: {', '.join(GRIDS)}")],
    entity_id: Annotated[int, typer.Argument(help="Contest id, or site id for site-* grids.")],
    proj: Annotated[
        str | None, typer.Option("--proj", help="Comma-separated columns; default is the grid's.")
    ] = None,
    filter_: Annotated[
        list[str] | None, typer.Option("--filter", help="COLUMN#VALUE, repeatable.")
    ] = None,
    sort: Annotated[
        list[str] | None, typer.Option("--sort", help="COLUMN[:asc|desc], repeatable.")
    ] = None,
    any_filter: Annotated[
        bool, typer.Option("--any", help="Combine filters with OR instead of AND.")
    ] = False,
    limit: Annotated[int | None, typer.Option("--limit", help="Stop after this many rows.")] = None,
    fields: Annotated[
        bool, typer.Option("--fields", help="List the grid's columns and exit.")
    ] = False,
) -> None:
    """Run one of the search grids.

    Column names are the server's own; ``--fields`` lists them. An unknown column
    is rejected here rather than silently ignored by the server.
    """
    endpoint = _grid(grid, entity_id)
    if fields:
        render(
            [{"column": name} for name in endpoint.all_fields],
            _ctx(ctx).output,
            columns=["column"],
        )
        return
    columns = proj.split(",") if proj else list(endpoint.default_proj)
    q = endpoint.query(
        proj=columns,
        filters=_parse_filters(filter_ or []),
        sort=_parse_sort(sort or []),
        mode="or" if any_filter else "and",
    )
    with _client(ctx) as icpc:
        rows = icpc.all(endpoint, q, max_rows=limit)
    render(rows, _ctx(ctx).output, columns=columns)


@app.command("count")
def count(
    ctx: typer.Context,
    grid: Annotated[str, typer.Argument(help=f"One of: {', '.join(GRIDS)}")],
    entity_id: int,
    filter_: Annotated[list[str] | None, typer.Option("--filter")] = None,
) -> None:
    """Count matching rows without fetching them."""
    endpoint = _grid(grid, entity_id)
    q = endpoint.query(filters=_parse_filters(filter_ or []))
    with _client(ctx) as icpc:
        sys.stdout.write(f"{icpc.count(endpoint, q)}\n")


@app.command("export")
def export(
    ctx: typer.Context,
    grid: Annotated[str, typer.Argument(help=f"One of: {', '.join(GRIDS)}")],
    entity_id: int,
    export_type: Annotated[ExportType, typer.Option("--type")] = ExportType.CSV,
    out: Annotated[
        str | None, typer.Option("--out", "-O", help="Write here instead of stdout.")
    ] = None,
) -> None:
    """Ask the server to render a grid as a file."""
    endpoint = _grid(grid, entity_id)
    with _client(ctx) as icpc:
        result = icpc.send(endpoint.export(endpoint.query(), export_type))
    content = result.content()
    if content is None:
        render(result, _ctx(ctx).output)
        return
    if out:
        with open(out, "wb") as handle:  # noqa: PTH123 - a user-supplied path
            handle.write(content)
        warn(f"wrote {len(content)} bytes to {out}")
    else:
        sys.stdout.buffer.write(content)


# -------------------------------------------------------------------- team --


@team_app.command("show")
def team_show(ctx: typer.Context, team_id: int) -> None:
    """One team."""
    with _client(ctx) as icpc:
        render(icpc.send(team_api.get(team_id)), _ctx(ctx).output)


@team_app.command("members")
def team_members(ctx: typer.Context, team_id: int) -> None:
    """A team's roster."""
    with _client(ctx) as icpc:
        render(icpc.send(team_api.members(team_id)), _ctx(ctx).output)


@team_app.command("files")
def team_files(ctx: typer.Context, team_id: int) -> None:
    """Attachments on a team."""
    with _client(ctx) as icpc:
        render(icpc.send(team_api.files(team_id)), _ctx(ctx).output)


@team_app.command("can")
def team_can(ctx: typer.Context, team_id: int) -> None:
    """What this account is allowed to do to a team."""
    with _client(ctx) as icpc:
        render(icpc.send(team_api.view_restrictions(team_id)), _ctx(ctx).output)


@team_app.command("register")
def team_register(
    ctx: typer.Context,
    site_id: Annotated[int, typer.Argument(help="Site to register into.")],
    name: Annotated[str, typer.Option("--name", help="Team name.")],
    institution: Annotated[
        int, typer.Option("--institution", help="Institution id; see `icpc institution`.")
    ],
    contestant: Annotated[
        list[int] | None, typer.Option("--contestant", help="Person id; repeatable.")
    ] = None,
    coach: Annotated[
        int | None,
        typer.Option("--coach", help="Person id of the coach. Defaults to you."),
    ] = None,
    student_coach: Annotated[
        bool,
        typer.Option(
            "--student-coach",
            help="Make the coach a CONTESTANT_COACH: you, or `--coach`'s person.",
        ),
    ] = False,
    id_only: Annotated[bool, typer.Option("--id", help="Print just the new team id.")] = False,
) -> None:
    """Register a team.

    Without `--coach` your own account becomes the coach, because the bulk
    registration endpoint always adds the registering account and the usual
    limit is one coach per team.

    With `--coach` a different endpoint is used that does not add you, and the
    named person is attached afterwards. Note the server refuses to make someone
    a coach if they are already a contestant in the same contest.

    `--student-coach` makes that coach a `CONTESTANT_COACH` either way — the
    registering account on the first path, `--coach`'s person on the second.
    """
    contestants = [
        NewTeamMember(role="CONTESTANT", person=pid, badgeRole=None, certificateRole=None)
        for pid in (contestant or [])
    ]
    team = NewTeam(
        name=name,
        siteId=site_id,
        institutionUnitId=institution,
        studentCoach=student_coach,
        teamMembers=contestants,
    )
    with _client(ctx) as icpc:
        if not icpc.send(team_api.site_registrable(site_id)):
            warn(f"site {site_id} is not open for registration; the server may refuse this")
        if coach is None:
            created = icpc.send(team_api.register([team]))
            rows = [{"id": int(k), "name": v} for k, v in created.items()]
        else:
            # Two calls, and the second can fail on its own: say so precisely
            # rather than leaving a coachless team and an opaque error.
            team_id = icpc.send(team_api.register_with_coach(team))
            role = MemberRole.CONTESTANT_COACH if student_coach else MemberRole.COACH
            try:
                icpc.send(team_api.set_coach(team_id, coach, role=str(role)))
            except errors.ApiError as exc:
                fail(
                    f"team {team_id} was created, but person {coach} could not be made "
                    f"its coach: {exc.body.strip()[:160]}\n"
                    f"The team now exists with no coach. Attach one with:\n"
                    f"    icpc team set-coach {team_id} --person <PERSON_ID>"
                    f"{' --student-coach' if student_coach else ''}\n"
                    f"A person who is already a contestant in this contest cannot "
                    f"also be its coach"
                    + (
                        ", and a CONTESTANT_COACH may not be a contestant on another team in it."
                        if student_coach
                        else "."
                    )
                )
                raise typer.Exit(1) from exc
            rows = [{"id": team_id, "name": name}]
    for row in rows:
        note(f"registered team {row['id']}: {row['name']}")
    if id_only:
        sys.stdout.write(f"{rows[0]['id']}\n")
        return
    render(rows, _ctx(ctx).output, columns=["id", "name"])


@team_app.command("add-member")
def team_add_member(
    ctx: typer.Context,
    team_id: int,
    person_id: Annotated[int, typer.Option("--person", help="Person id; see `icpc person find`.")],
    role: Annotated[MemberRole, typer.Option("--role")] = MemberRole.CONTESTANT,
    badge_role: Annotated[str | None, typer.Option("--badge-role")] = None,
) -> None:
    """Add someone to a team.

        icpc team add-member 1234568 --person 234568 --role CONTESTANT_COACH

    `CONTESTANT_COACH` counts against the contest's coach limit, so a team that
    already has a coach will refuse one until the coach is removed or
    `maxCoaches` is raised.
    """
    label = badge_role or str(role).replace("_", " ").title()
    with _client(ctx) as icpc:
        added = icpc.send(
            team_api.add_members(
                team_id,
                [
                    {
                        "person": {"id": person_id},
                        "role": str(role),
                        "badgeRole": label,
                        "certificateRole": label,
                    }
                ],
            )
        )
    for m in added:
        note(f"added {m.name} <{m.email}> as {m.role} (memberId {m.member_id})")
    render(added, _ctx(ctx).output, columns=["memberId", "personId", "name", "email", "role"])


@team_app.command("remove-member")
def team_remove_member(
    ctx: typer.Context,
    member_id: Annotated[int, typer.Argument(help="Member id — not person id.")],
) -> None:
    """Remove someone from a team. `icpc team members` lists the member ids."""
    with _client(ctx) as icpc:
        icpc.send(team_api.remove_member(member_id))
    note(f"removed member {member_id}")


@team_app.command("set-role")
def team_set_role(
    ctx: typer.Context,
    team_id: int,
    person_id: Annotated[int, typer.Option("--person", help="Person id.")],
    role: Annotated[MemberRole, typer.Option("--role")],
) -> None:
    """Change someone's role on a team.

        icpc team set-role 1234568 --person 234568 --role CONTESTANT_COACH

    The API has no role-change operation, so this removes the membership and
    creates a new one. The member id changes and per-member settings — badge and
    certificate roles, attendance, certificate flags — are reset to defaults.
    """
    with _client(ctx) as icpc:
        roster = icpc.send(team_api.members(team_id))
        existing = next((m for m in roster if m.person_id == person_id), None)
        if existing is None or existing.member_id is None:
            fail(f"person {person_id} is not on team {team_id}")
            raise typer.Exit(1)
        if existing.role == role:
            note(f"already {role}; nothing to do")
            return
        label = str(role).replace("_", " ").title()
        icpc.send(team_api.remove_member(existing.member_id))
        try:
            added = icpc.send(
                team_api.add_members(
                    team_id,
                    [
                        {
                            "person": {"id": person_id},
                            "role": str(role),
                            "badgeRole": label,
                            "certificateRole": label,
                        }
                    ],
                )
            )
        except errors.ApiError as exc:
            fail(
                f"removed the old membership but could not add the new one: "
                f"{exc.body.strip()[:160]}\n"
                f"Person {person_id} is no longer on team {team_id}. Re-add them with:\n"
                f"    icpc team add-member {team_id} --person {person_id} "
                f"--role {existing.role}"
            )
            raise typer.Exit(1) from exc
    note(f"{person_id} is now {role} on team {team_id}")
    render(added, _ctx(ctx).output, columns=["memberId", "personId", "name", "email", "role"])


@team_app.command("set-coach")
def team_set_coach(
    ctx: typer.Context,
    team_id: int,
    person_id: Annotated[int, typer.Option("--person", help="Person id; see `icpc person find`.")],
    student_coach: Annotated[
        bool, typer.Option("--student-coach", help="Install them as a CONTESTANT_COACH.")
    ] = False,
    badge_role: Annotated[str | None, typer.Option("--badge-role")] = None,
) -> None:
    """Make someone the team's coach.

    This fills the coach slot rather than adding to it: an incumbent
    `CONTESTANT_COACH` is demoted to `CONTESTANT` in place, keeping their member
    id and per-member settings, and the contest's `maxCoaches` is not checked.
    So swapping in a real coach over a contestant coach is this one command --
    do not free the slot first.

    Refused if that person is already on the team, or already a contestant in
    the same contest.
    """
    role = MemberRole.CONTESTANT_COACH if student_coach else MemberRole.COACH
    with _client(ctx) as icpc:
        member = icpc.send(
            team_api.set_coach(
                team_id,
                person_id,
                role=str(role),
                badge_role=badge_role,
                certificate_role=badge_role,
            )
        )
    note(f"{member.name} <{member.email}> is now the {member.role} of team {team_id}")
    render(member, _ctx(ctx).output)


@team_app.command("promote")
def team_promote(
    ctx: typer.Context,
    team_id: int,
    site_id: Annotated[int, typer.Option("--site", help="Target site id.")],
) -> None:
    """Promote a team to a site of the parent contest."""
    with _client(ctx) as icpc:
        try:
            icpc.send(team_api.promote(team_id, site_id))
        except errors.TeamNotPromotable as exc:
            fail(str(exc))
            raise typer.Exit(1) from exc
    warn(f"team {team_id} promoted to site {site_id}")


@team_app.command("bulk-status")
def team_bulk_status(
    ctx: typer.Context,
    contest_id: int,
    status: Annotated[TeamStatus, typer.Option("--status")],
    ids: Annotated[str, typer.Option("--ids", help="Comma-separated team ids.")],
    yes: Annotated[bool, typer.Option("--yes", help="Skip the confirmation prompt.")] = False,
) -> None:
    """Set the status of many teams of one contest."""
    team_ids = [int(part) for part in ids.split(",") if part.strip()]
    if not team_ids:
        raise typer.BadParameter("--ids is empty")
    if not yes:
        typer.confirm(
            f"set {len(team_ids)} team(s) to {status} in contest {contest_id}?", abort=True
        )
    with _client(ctx) as icpc:
        icpc.send(team_api.bulk_update_status(contest_id, team_ids, status))
    warn(f"updated {len(team_ids)} team(s)")


# ------------------------------------------------------------------ public --


@public_app.command("regionals")
def public_regionals(ctx: typer.Context, year: int) -> None:
    """Regional contests of a season."""
    with Icpc.anonymous() as icpc:
        render(icpc.send(public_api.regionals(year)), _ctx(ctx).output)


@public_app.command("under")
def public_under(ctx: typer.Context, contest_id: int) -> None:
    """Sub-contests of a contest, with registration counts."""
    with Icpc.anonymous() as icpc:
        render(icpc.send(public_api.contests_under(contest_id)), _ctx(ctx).output)


@public_app.command("contest")
def public_contest(ctx: typer.Context, abbreviation: str) -> None:
    """A public contest page, by abbreviation (e.g. ``NERC-2026``)."""
    with Icpc.anonymous() as icpc:
        render(icpc.send(public_api.contest(abbreviation)), _ctx(ctx).output)


@public_app.command("standings")
def public_standings(ctx: typer.Context, contest_id: int) -> None:
    """Published standings for a contest."""
    with Icpc.anonymous() as icpc:
        render(icpc.send(public_api.standings(contest_id)), _ctx(ctx).output)


# ------------------------------------------------------------------- misc --


@app.command("schema")
def schema(ctx: typer.Context, java_class: str) -> None:
    """Fetch a server-side form definition from ``/aspectfaces``.

    The best available source for enum option lists and required-field constraints
    when building a write payload.
    """
    with _client(ctx) as icpc:
        render(icpc.send(common_api.schema(java_class)), _ctx(ctx).output)


@app.command("raw")
def raw(
    ctx: typer.Context,
    path: Annotated[str, typer.Argument(help="Path under /api, e.g. /team/1234567")],
    param: Annotated[list[str] | None, typer.Option("--param", "-p", help="key=value")] = None,
) -> None:
    """GET any path. The escape hatch for endpoints this SDK does not model."""
    params: dict[str, str | int] = {}
    for item in param or []:
        key, _, value = item.partition("=")
        params[key] = value
    with _client(ctx) as icpc:
        render(icpc.send(json_op(Request("GET", path, params=params))), _ctx(ctx).output)


def run() -> None:
    """Entry point that turns SDK errors into terse messages."""
    try:
        app()
    except errors.IcpcError as exc:
        fail(f"{type(exc).__name__}: {exc}")
        raise SystemExit(1) from exc


if __name__ == "__main__":
    run()
