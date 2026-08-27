# icpc-api

An unofficial Python client and CLI for [icpc.global](https://icpc.global) API.
Supports authentication and customizable search over contest data.

**Note:** This project is aimed for regional contest organizers. If you want to
compete, please [use Regional Finder](https://icpc.global/regionals/finder) to
find nearest regional competition to you and its schedule.

## Install

Use Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```bash
# add library to your project
uv add icpc-api

# run your script that uses `import icpc`
uv run --with icpc-api script.py

# install CLI into PATH
uv tool install 'icpc-api[cli]'
```

If you don't have `uv`, feel free to use `pip` or any other convenient Python package manager.

## Quick start

CLI:

```bash
icpc auth login
icpc whoami
icpc contest teams 1234 --status ACCEPTED
icpc search teams 1234 --proj id,name,status --sort name:asc -o csv > teams.csv
```

Python synchronous API:

```python
from icpc import Icpc
from icpc.search import contest_teams
from icpc.models import TeamStatus

with Icpc.from_store() as icpc:
    # Use DSL to build the request
    teams = contest_teams(1234)
    f = teams.fields
    q = teams.query(
        proj=[f.id.name, f.name.name, f.inst_short_name.name],
        filters=[f.status.eq(TeamStatus.ACCEPTED)],
        sort=[f.name.asc()],
    )
    # `icpc.all` executes search request
    for row in icpc.all(teams, q):
        print(row.id, row.name, row.inst_short_name)
```

Python asynchronous API:

```python
import asyncio
from icpc import AsyncIcpc, Include


async def main() -> None:
    async with AsyncIcpc.from_store() as icpc:
        view = await icpc.load_contest(1234, Include.DEFAULT)
        for team in view.teams:
            print(team.name, len(team.contestants), team.institution.inst_name)


asyncio.run(main())
```

`load_contest` is the unified search: it fetches the team, team-member, institution
and contest tables concurrently, then joins them — teams indexed by id, rosters
bucketed by team, institutions attached by `instId`, participants by `personId`, and
the JSON-in-a-string `teamMembers` and `extraField` columns parsed into real objects.

## Authentication

```python
Icpc.from_password("me@example.com", "…")  # SRP login
Icpc.from_store()  # use `icpc auth login` to authenticate
Icpc.from_token("eyJ…")  # a borrowed id token from localStorage
Icpc.anonymous()  # /contest/public/* only
```

When using store, token and credentials are written to `~/.config/icpc/credentials.json`.
You can also use `ICPC_USERNAME` and `ICPC_PASSWORD` or `ICPC_ID_TOKEN` environment
variables. ID Token is valid only for one hour.

## Documentation

Read detailed guides on how to use:

- [Python API](docs/api.md) — guide, with worked examples
- [CLI](docs/cli.md) — every command, with worked examples
- [API reference](docs/reference.md) — every endpoint this client wraps

## Development

```bash
uv sync --extra cli
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run ty check icpc tests
```
