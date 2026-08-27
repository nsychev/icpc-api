# Using the library

`Icpc` is synchronous and `AsyncIcpc` has the same surface with `await`.

Every endpoint this client wraps is catalogued in
[reference.md](reference.md) — method, path, return type and which calls write.

## Getting a client

```python
from icpc import Icpc

with Icpc.from_store() as icpc:  # tokens cached by `icpc auth login`
    print(icpc.whoami().user_name)
```

```python
Icpc.from_password("me@example.com", "…")   # SRP login; renews itself
Icpc.from_store("me@example.com")           # a specific cached account
Icpc.from_token("eyJ…")                     # a borrowed id token; dies in an hour
Icpc.anonymous()                            # /contest/public/* only
```

An id token lasts an hour. Renewal is a fresh SRP login, not a refresh token:
this Cognito app client rejects `REFRESH_TOKEN_AUTH` outright, so
`from_token(refresh_token=…)` and `ICPC_REFRESH_TOKEN` are accepted by the code
but will not produce a working session. Long-running jobs want
`from_password(...)` or the credentials `icpc auth login` caches.

## Two layers

Every endpoint is a pure function returning an `Operation[T]`; the client only
knows how to send one. Nothing is issued until `send()`.

```python
from icpc.api import team

op = team.members(1234567)          # Operation[list[TeamMember]]
op.request.describe()               # 'GET /team/members/team/1234567'
roster = icpc.send(op)              # list[TeamMember]
```

On top of that sit search helpers (`count`, `page`, `all`, `iter`) and the
joined `load_contest`.

---

## Searching

> *Teams in contest 1234 from Chinese universities, accepted only.*

```python
from icpc import Icpc
from icpc.models import TeamStatus
from icpc.search import contest_teams

with Icpc.from_store() as icpc:
    teams = contest_teams(1234)
    f = teams.fields
    q = teams.query(
        proj=[f.id.name, f.name.name, f.inst_name.name, f.country.name],
        filters=[f.status.eq(TeamStatus.ACCEPTED), f.country.eq("China")],
        sort=[f.name.asc()],
    )
    print(icpc.count(teams, q))  # 271
    for row in icpc.all(teams, q):
        print(row.id, row.name, row.inst_name)
```

The columns are typed, so `f.instName` is an `AttributeError` at import time and
`teams.query(proj=["instNmae"])` raises `EmptyProjection` before any request.
Filter and sort columns are added to the projection automatically — the server
silently ignores a filter on an unprojected column and returns everything.

⚠ Some columns are projectable but not filterable. The server does not say so;
it returns the unfiltered result, or a 500. When a filter looks ignored, filter
on a column you have seen work — `country`, `status` — and narrow the rest
programmatically.

Streaming, when you do not want the whole contest in memory:

```python
for row in icpc.iter(contest_teams(1234), size=200):
    ...
```

`all()` fetches `/count` alongside the first page and pages until covered;
`iter()` stops on the first short page and never calls `/count`.

## Rows

Every field is optional, because `proj:` does not shape the response — the whole
DTO always comes back with unprojected fields null.

```python
row.status            # TeamStatus.ACCEPTED  (unknown values stay plain strings)
row.created_when      # datetime(2025, 9, 24, 11, 12, 35, 787000, tzinfo=UTC)
row.member_blobs      # [TeamMemberBlob(...)]  — the JSON-string roster, parsed
row.extras            # {"Course": "3"}       — custom registration answers
row.unknown_fields()  # anything the server added since this SDK was generated
```

---

## The joined contest

If you need data from multiple searches at once, you can use `load_contest` method.
It loads data from all tables at once and joins them into a single view.

```python
import asyncio
from icpc import AsyncIcpc, Include


async def main() -> None:
    async with AsyncIcpc.from_store() as icpc:
        view = await icpc.load_contest(1234, Include.DEFAULT)

    print(len(view.teams), len(view.members()), len(view.institutions))
    # 361 1262 49

    team = max(view.teams, key=lambda t: len(t.members))
    print(team.name, len(team.contestants), len(team.coaches), team.institution.inst_name)
    # Team Nu 3 2 Tsinghua University

    print({str(k): len(v) for k, v in view.by_status().items()})
    # {'ACCEPTED': 271, 'CANCELED': 90}


asyncio.run(main())
```

`Include` controls which tables are fetched — each is a full search over the
contest, so ask only for what you need:

```python
Include.TEAMS                       # teams only
Include.DEFAULT                     # teams, rosters, institutions, metadata
Include.ALL                         # …and the contest-participant table

Include.named(["teams", "institutions"])   # by name, for tables decided at runtime
```

`load_contest` returns a `ContestView`:

```python
view.contest            # Contest — the metadata fetch
view.sites              # [NamedRef] — the contest's sites, id and name
view.teams              # [Team]
view.institutions       # {instId: InstitutionRow}
view.people             # {personId: ContestParticipantRow}

view.team(1234567)      # one team by id
view.members()          # every membership across every team, in team order
view.by_site()          # {site name: [Team]}
view.by_status()        # {TeamStatus: [Team]}
```

The view adds a few attributes that are useful for getting related entities.

`Team` has the following attributes:

```python
team.id, team.name, team.status, team.site   # , ...: team own attributes

team.members                                 # list[Member] — all team members
team.contestants, team.coaches, team.other   # members split by role
team.institution                             # InstitutionRow | None
team.extras                                  # {question: answer}
```

If there is a contestant coach, they will be present in both `coaches` and
`contestants`.

`Member` fields:

```python
member.first_name, member.shirt_size, member.attending_onsite   # , ...: "teammember" own attributes

member.registration_complete  # status of registration
member.participant            # ContestParticipantRow | None — the person's profile
member.extras
```

`participant` is not loaded by default: use `Include.ALL` if you need the profile data.

See [CLI guide](cli.md#contest-load) for more examples.

---

## Finding ids

```python
from icpc.api import common, person

icpc.send(person.suggest("root@nsychev.ru"))
# [PersonSuggestion(id=234567, username='root@nsychev.ru', first_name='Nikita', …)]

icpc.send(common.institution_suggest("Nazarbayev"))
# [InstitutionSuggestion(id=7523, name='Nazarbayev University', country='KZ', …)]
```

The institution id from `institution_suggest` is the one team registration
wants; the `instId`/`instUnitId` columns of the institution grid are different
tables entirely.

## Contests you can administer

```python
icpc.my_contests(2027)
# [ContestReference(contest_id=1236, contest='NERC-2026', …)]

icpc.my_contests(2026, "teammember")     # also fills in team and site
```

The argument is the ICPC season, not the calendar year: a contest held in 2026
belongs to season 2027.

---

## Writing

Writes are ordinary calls. They are never retried, because replaying one would
apply it twice.

```python
from icpc.api import staff, team
from icpc.models import TeamStatus

# Registering teams. Your own account is added as a coach automatically.
created = icpc.send(team.register([{
    "name": "Example Team",
    "siteId": 3456,
    "institutionUnitId": 7523,
    "studentCoach": False,
    "teamMembers": [{"role": "CONTESTANT", "person": 234567,
                     "badgeRole": None, "certificateRole": None}],
}]))
# {'1234569': 'Example Team'}

# A team coached by somebody else: /team/register/bulk always makes *you* the
# coach, so this endpoint exists to not do that. It returns the new team id.
team_id = icpc.send(team.register_with_coach({
    "name": "Team Alpha", "siteId": 3456, "institutionUnitId": 7523,
    "studentCoach": False, "teamMembers": [],
}))
icpc.send(team.set_coach(team_id, 234567))     # refused if they are a contestant here

# set_coach fills the coach slot: an incumbent CONTESTANT_COACH is demoted to
# CONTESTANT in place, keeping their member id and flags, and maxCoaches is not
# checked. `role` also accepts CONTESTANT_COACH, the cheapest way to install one.
icpc.send(team.set_coach(team_id, 234568, role="CONTESTANT_COACH"))
icpc.send(team.add_members(team_id, [
    {"person": {"id": 234568}, "role": "CONTESTANT",
     "badgeRole": "Contestant", "certificateRole": "Contestant"},
]))

icpc.send(team.bulk_update_status(1234, [1234567], TeamStatus.ACCEPTED))
icpc.send(team.promote(1234567, 3457))
icpc.send(team.upload_file(1234567, "letter.pdf", pdf_bytes))
icpc.send(staff.add(3456, 234568, badge_role="Judge", certificate_role="Judge"))
```

`update_team` is a read-modify-write over `POST /team/{id}`, which is a
full-object replace: the server recomputes the team's eligibility and drops any
verified status.

```python
icpc.update_team(1234567, status="ACCEPTED")  # returns the team as it is afterwards
```

### Roles on a team

There is no role-change endpoint: remove the membership and add it back.

```python
from icpc.api import team

team_id = 1234568
roster = icpc.send(team.members(team_id))
member = next(m for m in roster if m.person_id == 234568)

icpc.send(team.remove_member(member.member_id))
icpc.send(team.add_members(team_id, [{
    "person": {"id": 234568}, "role": "CONTESTANT_COACH",
    "badgeRole": "Contestant Coach", "certificateRole": "Contestant Coach",
}]))
```

`CONTESTANT_COACH` counts against the contest's `maxCoaches`, and the site must
have `allowTeamChanges=true` — while it is false these calls answer 500 rather
than refusing cleanly.

`team.update_member()` exists but is only good for `attendingOnsite` and the two
certificate flags; changing `role` through it answers 500.

### Contest settings

Four groups, each a read-modify-write full-object replace:

```python
from icpc.api import contest

info = icpc.send(contest.registration_info(1235))
icpc.send(contest.update_registration_info(
    1235, {**info.model_dump(by_alias=True), "allowStudentCoach": True}))

settings = icpc.send(contest.settings(1235))
icpc.send(contest.update_settings(
    1235, {**settings.model_dump(by_alias=True), "requireCertification": True}))

meta = icpc.send(contest.get(1235))
icpc.send(contest.update(1235, {**meta.model_dump(by_alias=True), "email": "me@example.com"}))

site = icpc.send(contest.site_settings(3456))
icpc.send(contest.update_site_settings(1235, {**site, "allowTeamChanges": True}))
```

Send only the changed keys and everything else is wiped — the read is not
optional.

### Contests

```python
from icpc.api import contest

new = icpc.send(contest.create_subcontest(1234, {
    "name": "Example Qualifier",
    "shortName": "EX-QUAL",
    "abbreviation": "example-qualifier",   # ^[a-zA-Z-]*$, 3-42 chars
    "email": "you@example.com",
}))
site = icpc.send(contest.create_site(
    new.id, {"name": "Main Site", "email": "you@example.com"}))
icpc.send(contest.add_manager(new.id, 234567))
icpc.send(contest.delete(new.id))  # deletes the contest
```

## Errors

```python
from icpc import errors

try:
    icpc.send(team.get(1))
except errors.NotFound:
    ...  # also raised for the SPA's HTML catch-all and empty bodies
except errors.Forbidden:
    ...
except errors.ServerError as exc:
    print(exc.error_code)  # the opaque hex code, worth quoting to ICPC support
```

`SearchError` and its subclasses are raised *before* a request goes out —
`EmptyProjection` for an unknown column, `InvalidFilterValue` for a value
containing `# & | ; ,` (which the grammar cannot escape).

## Request Limits

The defaults cap concurrency at 4 in-flight requests, retry only idempotent
requests, and back off with jitter. You can customize this behavior:

```python
from icpc import Icpc, Settings

Icpc.from_store(settings=Settings(max_concurrency=2, max_attempts=5))
```
