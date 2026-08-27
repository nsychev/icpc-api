# `icpc` command reference

## Global options

Use these options before the subcommand:

| Option | Meaning |
|---|---|
| `-o, --output table\|json\|ndjson\|csv\|tsv` | Output format. Defaults to `table` on a terminal, `json` in a pipe. |
| `-u, --user EMAIL` | Which cached account to use. Defaults to the one from `auth use` / the last login. |

## auth

Use these commands to manage your credentials.

```bash
icpc auth login                          # prompts for username and password
icpc auth status                         # which accounts are cached, which is in use
icpc auth use root@nsychev.ru            # switch the default account
icpc auth token                          # print the bearer token (treat as a password)
icpc auth forget-password                # drop the password, stay logged in
icpc auth logout [USERNAME]              # drop everything for one account, or all
```

```
$ icpc auth status
username                      in_use   token_expires          expired   password
root@nsychev.ru               yes      2026-08-28 03:00 UTC   no        yes
```

An id token lasts an hour, and this Cognito app client rejects refresh-token
renewal — so renewing means logging in again. That is why `auth login` caches
your password by default, and why `ICPC_REFRESH_TOKEN` will not get you a
session even though the code accepts it.

⚠ **The cached password is stored unencrypted** in `~/.config/icpc/credentials.json`.
To avoid that, use `icpc auth login --no-save-password` to store only token on
untrusted devices. Note that it will require re-authentication each hour.

## whoami

Helper to get your current account.

```bash
$ icpc -o json whoami
{"id": 234567, "userName": "root@nsychev.ru",
 "firstName": "Nikita", "lastName": "Sychev", "privacyPolicyAccepted": true}
```

---

## Example

> *Which teams in contest 1234 are from Chinese universities?*

```bash
icpc search teams 1234 --proj id,name,instName,country --filter country#China
```

```
     id   name         instName                      country
1234574   Team Gamma   Tsinghua University           China
1234575   Team Delta   Beijing Jiaotong University   China
…360 rows
```

Count without fetching:

```bash
$ icpc count teams 1234 --filter country#China
360
$ icpc count teams 1234
361
```

⚠ **Some columns cannot be filtered on.** icpc.global does not say which: a
filter on such a column comes back as the whole unfiltered response, or as an
internal error.

---

## Finding IDs

Almost every write needs a numeric ID. Use these requests to find one. Search is
fuzzy and requires at least three characters to work.

```bash
$ icpc person find root@nsychev.ru
     id   username          firstName   lastName
234567   root@nsychev.ru   Nikita      Sychev

$ icpc person find "Sychev" --limit 3      # by name, not just email

$ icpc institution University
    id   name                              country   url
  7523   Nazarbayev University             KZ        https://nu.edu.kz/
  7524   St. Petersburg State University   RU        https://spbu.ru/
  7525   Beijing Jiaotong University       CN        https://www.bjtu.edu.cn/…
```

⚠ Institution IDs from this request are only useful for passing in the subsequent
requests (e.g. you can use institution ID in `team register --institution`), but
both `instId` and `instUnitId` from export requests will be different.

```bash
$ icpc person show 234567        # the full person profile
```

`--id` prints just the id, so it composes:

```bash
icpc staff add 3456 --person $(icpc person find root@nsychev.ru --id) --badge-role Judge
icpc team register 3456 --name Alpha --institution $(icpc institution "Nazarbayev University" --id)
```

Make sure to specify full name as it won't work if several entries found.

`icpc team register --id` prints the new team id the same way.

---

## contest

```bash
icpc contest show 1234           # metadata and settings
icpc contest sites 1234          # sites with capacity and registration flags
icpc contest stats 1234          # counts of sites, managers, pending/accepted teams
icpc contest summary 1234        # teams per site, from one joined fetch
```

```
$ icpc -o json contest stats 1234
{"numSubcontests": 0, "numSites": 2, "numContestManagers": 10,
 "numPendingTeams": 0, "numAcceptedTeams": 271}

$ icpc contest summary 1234
site        teams
Main Site   361
```

---

## contest load

This command helps to export data from multiple sources at once into a table.

```bash
icpc contest load 1234                                  # one row per team (default)
icpc contest load 1234 --rows members                   # one row per membership
icpc contest load 1234 --rows institutions              # one row per institution
icpc contest load 1234 --rows participants              # one row per person
```

Unlike `search` endpoint that fetches a certain Search page from icpc.global admin
interface, this endpoint can combine data from all of them: for example, you can extract
T-Shirt sizes for all teams.

Note that `members` mode will return several rows for a person if they are in multiple
roles (the most common example is coaching many teams). `participants` mode returns only
one row for such people.

To choose columns, use `--col name=path`. It adds a column named `name` and populates it
with a data obtained by `path`. `path` may contain:
- `.` to select nested fields
- `[number]` to select certain item of array (0-indexed), e.g. `[1]`
- `[{i}]` (literal) to add _repeated_ group of columns
- `[*]` to join all elements of array into a single value

When you use `[{i}]`, you ask a system to generate a column set for each item of an array.
You can use `{n}` literal in the name to insert 1-based index.

Example:

```
$ icpc -o tsv contest load 1234 --col id --col 'C{n}.First=contestants[{i}].firstName' --col 'C{n}.Last=contestants[{i}].lastName'
fetching members, teams
id	C1.First	C1.Last	C2.First	C2.Last	C3.First	C3.Last
1234567	John	Smith	Jane	Doe	Richard	Roe
...
```

This will insert columns: `C1.First`, `C1.Last`, `C2.First`, `C2.Last`, etc, containing
respectively `contestants[0].firstName`, `contestants[0].lastName`,
`contestants[1].firstName`, `contestants[1].lastName`, ….

CLI calculates number of the groups dynamically. You can force a certain value by using `--repeat field=N`, e.g.
`--repeat others=5` will always render 5 groups for `others[{i}]` even if there is no row with 5 “other” persons.
It is useful if you process the resulting table in Excel or Google Sheets and don't want to change your formulas
during the registration process.

Join syntax will keep only one column:

```
$ icpc -o tsv contest load 1234 --col id --col shirts=members[*].shirtSize
fetching members, teams
id	shirts
1234567	XL,L,M,XL
...
```

Default separator is comma (`,`), but you can change it with `--join`.

You can use `--fields` to list all fields available:
```
$ icpc -o tsv contest load --fields | grep -i shirt
members[i].shirtSize   members

$ icpc contest load --rows participants --fields
path                       from
personId                   participants
username                   participants
…
memberships[i].role        members
memberships[i].team.name   members
contest.name               metadata
```

Advanced example:

```bash
icpc -o csv contest load 1234 \
  --col id --col site --col instName --col name --col status \
  --col eligibilityStatus --col eligibilityIssue \
  --col C.First='coaches[0].firstName' --col C.Last='coaches[0].lastName' \
  --col C.Id='coaches[0].username' \
  --col 'C{n}.First=contestants[{i}].firstName' \
  --col 'C{n}.Last=contestants[{i}].lastName' \
  --col 'C{n}.Id=contestants[{i}].username' \
  --col 'O{n}.Role=other[{i}].role' --col 'O{n}.First=other[{i}].firstName' \
  --col 'O{n}.Last=other[{i}].lastName' --col 'O{n}.Id=other[{i}].username' \
  --col instAddress \
  --repeat contestants=3 --repeat other=5 > teams.csv
$ head -1 teams.csv
id,site,instName,name,status,eligibilityStatus,eligibilityIssue,C.First,C.Last,
C.Id,C1.First,C1.Last,C1.Id,C2.First,C2.Last,C2.Id,C3.First,C3.Last,C3.Id,
O1.Role,O1.First,…,O5.Id,instAddress

$ icpc -o tsv contest load 1234 --rows participants --col username \
    --col TeamIds='memberships[*].team.id' --col Onsite='memberships[*].attendingOnsite'
username        TeamIds                            Onsite
g@example.com   1234580                            yes
h@example.com   1234582,1234583,1234580,1234581…   yes,yes,yes,yes…
```

---

## search / count / export

`GRID` is one of: `teams`, `members`, `institutions`, `participants`, `staff`,
`staff-members`, `standings`, `top20`, `summaries`, `promote-candidates`,
`certificates`, and the `site-*` variants (which take a **site** id).

```bash
icpc search teams 1234 --fields                       # list this grid's columns
icpc search teams 1234 --proj id,name,status          # pick columns
icpc search teams 1234 --filter status#ACCEPTED       # filter (substring match)
icpc search teams 1234 --filter status#ACCEPTED --filter country#China
icpc search teams 1234 --filter status#ACCEPTED --filter status#PENDING --any   # OR
icpc search teams 1234 --sort name:asc --sort rank:desc
icpc search teams 1234 --limit 20
icpc search members 1234 -o csv > members.csv
icpc search site-teams 3457                           # site id, not contest id
```

```
$ icpc search teams 1234 --proj id,name,status --filter status#ACCEPTED --sort name:asc --limit 3
     id   name           status
1234576   Team Epsilon   ACCEPTED
1234577   Team Eta       ACCEPTED
1234578   Team Zeta      ACCEPTED

$ icpc count teams 1234 --filter status#CANCELED
90

$ icpc export teams 1234 --type CSV --out teams.csv
wrote 46828 bytes to teams.csv
```

Filter and sort columns are added to the projection automatically, because the
server ignores a filter on a column that is not projected. A typo in `--proj` is
rejected before the request goes out.

`--proj` defaults to the columns the icpc.global grid itself requests, not every
column. That is deliberate: six of the grids — `staff`, `staff-members`,
`certificates` and the `site-participants` variant among them — answer **500**
when asked for their complete field set. `--fields` lists what a grid accepts,
and asking for a subset always works.

---

## team

```bash
icpc team show 1234567            # one team
icpc team members 1234567         # its roster
icpc team files 1234567           # attachments
icpc team can 1234567             # what your account may do to it
```

```
$ icpc -o json team members 1234567
[{"memberId": 3456789, "personId": 234567, "name": "Nikita Sychev",
  "email": "root@nsychev.ru", "role": "CONTESTANT", "registrationComplete": true, …}]
```

### Registering a team

```bash
icpc team register SITE_ID --name NAME --institution INST_ID \
    [--contestant PERSON_ID]... [--coach PERSON_ID]... [--student-coach]
```

```
$ icpc team register 3456 --name "Team Iota" --institution 7523 --contestant 234567
registered team 1234569: Team Iota
```

* By default, your own account becomes the coach. You can pass custom one through `--coach`.
* You can also make yourself or specified person a contestant coach by passing `--student-coach`
  if contest settings allow that.

If you're using `--coach`, during some conditions it may fail:

```
$ icpc team register 3456 --name X --institution 7523 --coach 234567
team 1234570 was created, but person 234567 could not be made its coach:
{"message":"Person root@nsychev.ru can't be coach."}
The team now exists with no coach. Attach one with:
    icpc team set-coach 1234570 --person <PERSON_ID>
```

In this case the team is empty. It is necessary to attach the coach manually.

### Changing a coach

```bash
icpc team set-coach 1234568 --person 234567 [--student-coach]
```

This command **replaces** a coach with the provided person.

- If there was already a **contestant coach**, they are demoted to a contestant.
- If there was already a coach, they will be removed from the team.
- If `--student-coach` is passed, the person will be added as a contestant coach.

The person must not be a contestant in any team (including the current one).
To promote contestant of this team to a contestant coach, use instead:

```bash
icpc team add-member 1234568 --person 234568 --role CONTESTANT_COACH
```

It is forbidden to be a coach and a contestant of a different team at the same time.

In many cases, you can change role of a member in the arbitrary way:

```bash
icpc team set-role 1234568 --person 234568 --role CONTESTANT_COACH
```

### Changing teams

```bash
icpc team bulk-status 1234 --status ACCEPTED --ids 1234567,1234579   # prompts; --yes skips
icpc team promote 1234567 --site 3457                               # promote to a parent site
```

---

## Changing contest settings

All four settings groups are writable, and all are **full-object replaces**: the
CLI reads the current object, applies your `KEY=VALUE` changes and writes it
back, so nothing else is wiped. An unknown key is rejected with the list of real
ones rather than silently ignored.

```bash
icpc contest set 1235 geographicArea="Northern Eurasia" email=me@example.com
icpc contest set-settings 1235 requireCertification=true showPublicPages=WITH_PEOPLE
icpc contest set-registration 1235 allowStudentCoach=true maxCoaches=2 maxContestants=3
icpc contest set-site 1235 --site 3456 allowRegistration=true capacity=50
```

```
$ icpc contest set-registration 1235 maxCoaches=2
maxCoaches: 1 -> 2
```

`true`/`false`/`null` and bare numbers are parsed as such; anything else is a
string. The four groups map to:

| Command | What it holds |
|---|---|
| `contest set` | name, short name, email, dates, hosts, sponsors, geographic area |
| `contest set-settings` | certification and eligibility requirements, public pages, contest type |
| `contest set-registration` | team sizes, coach limits, registration windows, `allowStudentCoach` |
| `contest set-site` | capacity, `allowRegistration`, `allowTeamChanges`, invitation-only |

`icpc schema <java.class.Name>` prints the server's own field list and allowed
values for each, which is the reliable way to see what a field will accept.

---

## staff

A *staff member* is a person attached to a site with a badge and certificate
role. A *contest manager* is different — that is an administrative permission.

```bash
icpc staff list 1235                                        # staff of a contest
icpc staff add 3456 --person 234568 --badge-role Judge      # attach to a site
icpc staff add 3456 --person 234568 --badge-role Judge --certificate-role "Chief Judge" --public
icpc staff remove 456789
```

```
$ icpc staff add 3456 --person 234568 --badge-role Judge
staff member 456789 added to site 3456
```

`--certificate-role` defaults to `--badge-role`. Both are free text: they are
printed on the badge and the certificate.

---

## my-contests

The contests you have access to — what the icpc.global cabinet lists on its front
page.

```bash
$ icpc my-contests 2027
contestId   contest
1236        NERC-2026

$ icpc my-contests 2026 --role teammember     # also fills in team and site
```

⚠ The year is the **ICPC season**, not the calendar year — the contest held in
calendar 2026 has `icpcYear` 2027 and is listed under 2027. It is the same number
the cabinet's year picker shows.

`--role` is one of `contestmanager` (the default, meaning administrative access),
`sitemanager`, `staffmember`, `teammember`, `sponsor`, `master`, `slave`.

---

## public

No login required.

```bash
icpc public regionals 2026          # regional contests of a season
icpc public under 1237              # sub-contests, with registration counts
icpc public contest NERC-2026       # by abbreviation, not id
icpc public standings 1234          # published results
```

---

## schema / raw

```bash
$ icpc schema global.icpc.base.model.team.businessobjects.Team
```

`/aspectfaces` is the server's own form registry and the only schema this API
publishes. It is where the enum option lists in this SDK came from, and the
right place to look before building a payload for an endpoint the SDK does not
wrap.

```bash
$ icpc raw /team/1234567
$ icpc raw /contest/search/contest/1234/team -p 'q=proj:id,name;' -p page=1 -p size=5
```

Use `raw` to make custom request that is not available in this library.
Please do not hesitate to open an issue for adding new endpoints.
