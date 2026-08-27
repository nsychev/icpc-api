# API reference

Every endpoint this SDK wraps, read off the `Request` each call builds:
an endpoint is a function returning `Operation[T]`, and calling one
performs no I/O.

Paths are relative to `https://icpc.global/api`. `Returns` is the type
`client.send()` gives back. ✎ marks a write: those are never retried.

## People

Looking people up and reading their records.

| Call | Endpoint | Returns | What it does |
|---|---|---|---|
| `person.available` | `GET /person/available/{username}` | `bool` | Whether a username is free. |
| `person.contact_info` | `GET /person/contactinfo/person/{person_id}` | `ContactInfo` | Phone, emergency contact and shipping address. |
| `person.degree` | `GET /person/degree/person/{person_id}` | `Degree` | Area of study, degree pursued, and graduation dates. |
| `person.whoami` | `GET /person/info/basic` | `PersonBasic` | The account behind the current token. The cheapest way to check auth works. |
| `person.info` | `GET /person/info/person/{person_id}/latest` | `PersonInfo` | The latest personal-information snapshot for a person. |
| `person.name` | `GET /person/name/{person_id}` | `PersonName` | Just the names — cheaper than `get` when resolving an id. |
| `person.references` | `GET /person/references/{person_id}/{icpc_year}/{role}/search` | `list[ContestReference]` | Contests a person is attached to in `role`, for one ICPC season. Query: `q`, `page`, `size`. |
| `person.registration_status` | `GET /person/registration/registrationStatus/{person_id}` | `RegistrationStatus` | Whether this person's registration is complete, and what the UI shows them. |
| `person.suggest` | `GET /person/suggest` | `list[PersonSuggestion]` | Look a person up by name or email, as the UI's picker does. Query: `name`, `page`, `size`. |
| `person.get` | `GET /person/{person_id}` | `Person` | A full person record, including the nested personal information. |


## Teams

Reading teams and their rosters, and every team write.

| Call | Endpoint | Returns | What it does |
|---|---|---|---|
| `team.bulk_update_status` ✎ | `PUT /team/bulkupdate/contest/{contest_id}` | `None` | Accept, reject or reset many teams of one contest at once. Body: `newStatus`, `teamIds`. |
| `team.eligibility` | `GET /team/eligibility/team/{team_id}` | `Eligibility` | The team's eligibility verdict and its verification state. |
| `team.files` | `GET /team/file/team/{team_id}` | `list[TeamFile]` | Attachments on a team (enrollment letters, proofs of id, and so on). |
| `team.delete_file` ✎ | `DELETE /team/file/{file_id}` | `None` | Remove one attachment, by *file* id — not team id. |
| `team.upload_file` ✎ | `POST /team/file/{team_id}` | `None` | Attach a file to a team. Body: multipart file. |
| `team.members` | `GET /team/members/team/{team_id}` | `list[TeamMember]` | The team's roster, with per-member certificate and attendance flags. |
| `team.add_members` ✎ | `POST /team/members/team/{team_id}/add` | `list[TeamMember]` | Add people to an existing team. The body is an array, even for one member. Body: the whole object. |
| `team.set_coach` ✎ | `POST /team/members/team/{team_id}/coach` | `TeamMember` | Make someone the team's coach, or its `CONTESTANT_COACH`. Body: `person`, `role`, `badgeRole`, `certificateRole`. |
| `team.remove_member` ✎ | `DELETE /team/members/{member_id}` | `None` | Remove a member, by *member* id — not person id. |
| `team.update_member` ✎ | `POST /team/members/{member_id}` | `TeamMember` | Overwrite a member with `member`, a full object from `members`. Body: the whole object. |
| `team.register` ✎ | `POST /team/register/bulk` | `dict[str, str]` | Register one or more teams, returning `{new team id: name}`. Body: the whole object. |
| `team.register_with_coach` ✎ | `POST /team/register/customcoach` | `int` | Register a single team **without** making yourself its coach. Body: `name`, `siteId`, `institutionUnitId`, `studentCoach`, `teamMembers`, `coachId`. |
| `team.site_registrable` | `GET /team/site/{site_id}/registrable` | `bool` | Whether a site is currently open for team registration. |
| `team.get` | `GET /team/{team_id}` | `Team` | A team, in the exact shape `replace` expects back. |
| `team.replace` ✎ | `POST /team/{team_id}` | `None` | Overwrite a team with `team`. Body: the whole object. |
| `team.action` | `GET /team/{team_id}/action` | `TeamAction` | Name, extended status and payment state — what the team page header shows. |
| `team.other_sites` | `GET /team/{team_id}/othersites` | `list[dict[str, object]]` | Sites this team could move to. |
| `team.promote` ✎ | `POST /team/{team_id}/promote/{site_id}` | `None` | Promote a team to a site of the parent contest. |
| `team.view_restrictions` | `GET /team/{team_id}/viewrestrictions` | `TeamViewRestrictions` | What the current account is allowed to do to this team. |


## Contests

Contest metadata, sites, access, and the settings writes.

| Call | Endpoint | Returns | What it does |
|---|---|---|---|
| `contest.add_manager` ✎ | `POST /contest/access/contest/{contest_id}/manager` | `str` | Grant a person administrative access to a contest. Body: `recursive`, `person`. |
| `contest.managers` | `GET /contest/access/contest/{contest_id}/managers` | `list[ContestManager]` | Who can administer this contest, and with which permissions. |
| `contest.next_contest` | `GET /contest/info/contest/{contest_id}/next` | `int` | Id of the next contest in the same series. |
| `contest.previous_contest` | `GET /contest/info/contest/{contest_id}/previous` | `int` | Id of the previous contest in the same series. |
| `contest.stats` | `GET /contest/info/contest/{contest_id}/stats` | `ContestStats` | Counts of sites, managers, and pending versus accepted teams. |
| `contest.registration_info` | `GET /contest/registrationinfo/contest/{contest_id}` | `RegistrationInfo` | Registration windows and which sections registrants must fill in. |
| `contest.update_registration_info` ✎ | `POST /contest/registrationinfo/contest/{contest_id}` | `RegistrationInfo` | Overwrite the registration rules — team sizes, windows, what registrants must give. Body: the whole object. |
| `contest.settings` | `GET /contest/settings/contest/{contest_id}` | `ContestSettings` | Just the settings block. |
| `contest.update_settings` ✎ | `POST /contest/settings/contest/{contest_id}` | `ContestSettings` | Overwrite the contest settings block — certification, public pages, type. Body: the whole object. |
| `contest.site_table` | `GET /contest/site/contest/{contest_id}/table` | `list[SiteRow]` | Sites with capacity and registration flags — the site administration grid. |
| `contest.create_site` ✎ | `POST /contest/site/create/{contest_id}` | `dict[str, object]` | Add a site to a contest. `name` (3 to 128 characters) and `email` are required. Body: the whole object. |
| `contest.update_site_settings` ✎ | `POST /contest/site/sitesettings/contest/{contest_id}` | `dict[str, object]` | Overwrite a site's settings — capacity, and whether it is open. Body: the whole object. |
| `contest.site_tree` | `GET /contest/site/tree/{contest_id}` | `list[SiteTreeNode]` | The subtree of contests below this one. |
| `contest.delete_site` ✎ | `DELETE /contest/site/{site_id}` | `None` | Remove a site. |
| `contest.site` | `GET /contest/site/{site_id}` | `dict[str, object]` | One site, with its settings nested under `siteSettings`. |
| `contest.site_settings` | `GET /contest/site/{site_id}` | `dict[str, object]` | The settings of one site, as embedded in `site`. |
| `contest.delete` ✎ | `DELETE /contest/{contest_id}` | `None` | Delete a contest. Used by the UI for subcontests and camps. |
| `contest.get` | `GET /contest/{contest_id}` | `Contest` | A contest and its settings. |
| `contest.update` ✎ | `POST /contest/{contest_id}` | `Contest` | Overwrite a contest's own fields — name, dates, hosts, email. Body: the whole object. |
| `contest.breadcrumbs` | `GET /contest/{contest_id}/breadcrumbs` | `list[Breadcrumb]` | Where this contest sits in the hierarchy, upwards. |
| `contest.sites` | `GET /contest/{contest_id}/sites` | `list[NamedRef]` | The contest's sites, id and name only. |
| `contest.create_subcontest` ✎ | `POST /contest/{parent_id}/subcontest/create` | `Contest` | Create a contest beneath `parent_id`. Body: the whole object. |


## Staff

Contest staff — people attached to a site with a badge role.

| Call | Endpoint | Returns | What it does |
|---|---|---|---|
| `staff.add` ✎ | `POST /contest/staffmember/site/{site_id}` | `dict[str, object]` | Attach a person to a site as staff. Body: `smId`, `personId`, `badgeRole`, `certificateRole`, `showInPublicPages`. |
| `staff.update` ✎ | `PUT /contest/staffmember/site/{site_id}` | `dict[str, object]` | Change an existing staff member. Same body as `add`, plus `smId`. Body: `smId`, `personId`, `badgeRole`, `certificateRole`, `showInPublicPages`. |
| `staff.delete` ✎ | `DELETE /contest/staffmember/{staff_member_id}` | `None` | Remove a staff member. |
| `staff.get` | `GET /contest/staffmember/{staff_member_id}` | `StaffMemberRow` | One staff member. |


## Common

Site-wide values, institution lookup, and the schema registry.

| Call | Endpoint | Returns | What it does |
|---|---|---|---|
| `common.schema` | `GET /aspectfaces/{java_class}` | `AspectFacesSchema` | Fetch a server-side form definition. |
| `common.wf_year` | `GET /common/globals/WFYear` | `int` | The current World Finals year. |
| `common.globals_` | `GET /common/globals/all` | `Globals` | Site-wide settings: the current World Finals and regionals years. |
| `common.institution_suggest` | `GET /common/institutionunit/suggest` | `list[InstitutionSuggestion]` | Look an institution up by name, as the UI's picker does. Query: `name`, `page`, `size`. |


## Public

No authentication required.

| Call | Endpoint | Returns | What it does |
|---|---|---|---|
| `public.contests_under` | `GET /contest/public/contests-under/{contest_id}` | `list[ContestUnder]` | Sub-contests of a contest, with registration counts. |
| `public.regionals` | `GET /contest/public/regionals/{year}` | `list[RegionalRef]` | The regional contests of a season. |
| `public.standings` | `GET /contest/public/search/contest/{contest_id}` | `list[StandingRow]` | Published standings for a contest. Query: `q`, `page`, `size`. |
| `public.contest` | `GET /contest/public/{abbreviation}` | `PublicContest` | A contest by *abbreviation*, not id. |


## Search grids

Each takes a `q=` query and has `/count` and `/export` siblings. The
projection defaults to the columns the icpc.global grid itself requests,
because six of these answer 500 when asked for their full field set.

| Factory | Path | Row type | Columns | Default projection |
|---|---|---|---|---|
| `search.site_team_certificates` | `GET /contest/certificate/site/team/site/{site_id}/search` | `CertificateRow` | 17 | `id`, `email`, `name`, `siteName`, `contestName`, … (9) |
| `search.contest_staff_certificates` | `GET /contest/certificate/staff/contest/{contest_id}/search` | `CertificateRow` | 17 | `id`, `email`, `name`, `siteName`, `contestName`, … (9) |
| `search.contest_team_certificates` | `GET /contest/certificate/team/contest/{contest_id}/search` | `CertificateRow` | 17 | `id`, `email`, `name`, `siteName`, `contestName`, … (9) |
| `search.contest_participants` | `GET /contest/search/contest/{contest_id}/contestparticipant` | `ContestParticipantRow` | 72 | `username`, `title`, `sex`, `dob`, `labels`, … (11) |
| `search.contest_institutions` | `GET /contest/search/contest/{contest_id}/institution` | `InstitutionRow` | 25 | `instId`, `instName`, `instUnitId`, `instUnitNativeName`, `instUnitShortName`, … (13) |
| `search.contest_staff` | `GET /contest/search/contest/{contest_id}/staff` | `StaffRow` | 19 | `username`, `firstName`, `lastName`, `roles`, `phone`, … (7) |
| `search.contest_teams` | `GET /contest/search/contest/{contest_id}/team` | `TeamRow` | 24 | `id`, `name`, `status`, `certified`, `instName`, … (9) |
| `search.contest_team_members` | `GET /contest/search/contest/{contest_id}/teammember` | `TeamMemberRow` | 39 | `username`, `firstName`, `lastName`, `localName`, `teamInstName`, … (11) |
| `search.contest_top20` | `GET /contest/search/contest/{contest_id}/top20` | `Top20Row` | 14 | `area`, `contest`, `contestId`, `rank`, `team`, … (14) |
| `search.site_participants` | `GET /contest/search/site/{site_id}/contestparticipant` | `ContestParticipantRow` | 72 | `username`, `title`, `sex`, `dob`, `labels`, … (11) |
| `search.site_home_teams` | `GET /contest/search/site/{site_id}/home/teams` | `TeamSummaryRow` | 22 | `teamId`, `teamName`, `rank`, `siteName`, `country`, … (15) |
| `search.site_institutions` | `GET /contest/search/site/{site_id}/institutions` | `InstitutionRow` | 25 | `instId`, `instName`, `instUnitId`, `instUnitNativeName`, `instUnitShortName`, … (13) |
| `search.site_team_members` | `GET /contest/search/site/{site_id}/teammember` | `TeamMemberRow` | 39 | `username`, `firstName`, `lastName`, `localName`, `teamInstName`, … (11) |
| `search.site_teams` | `GET /contest/search/site/{site_id}/teams` | `TeamRow` | 24 | `id`, `name`, `status`, `certified`, `instName`, … (9) |
| `search.site_coach_tshirts` | `GET /contest/search/site/{site_id}/tshirt/coaches` | `TshirtRow` | 4 | `personName`, `tshirtSize`, `institution`, `teamName` |
| `search.site_cocoach_tshirts` | `GET /contest/search/site/{site_id}/tshirt/cocoaches` | `TshirtRow` | 4 | `personName`, `tshirtSize`, `institution`, `teamName` |
| `search.site_contestant_tshirts` | `GET /contest/search/site/{site_id}/tshirt/contestants` | `TshirtRow` | 4 | `personName`, `tshirtSize`, `institution`, `teamName` |
| `search.contest_staff_funding` | `GET /contest/staffMember/funding/contest/{contest_id}/search` | `StaffFundingRow` | 17 | `site`, `firstName`, `lastName`, `username`, `homeTown`, … (10) |
| `search.contest_public_staff_members` | `GET /contest/staffmember/contest/{contest_id}/public/search` | `StaffMemberRow` | 16 | `site`, `title`, `firstName`, `lastName`, `username`, … (11) |
| `search.contest_staff_members` | `GET /contest/staffmember/contest/{contest_id}/search` | `StaffMemberRow` | 16 | `site`, `title`, `firstName`, `lastName`, `username`, … (11) |
| `search.contest_staff_tshirts` | `GET /contest/staffmember/tshirt/contest/{contest_id}/search` | `StaffTshirtRow` | 12 | `site`, `firstName`, `lastName`, `username`, `badgeRole`, … (9) |
| `search.contest_standings` | `GET /contest/standings/contest/{contest_id}/search` | `StandingsRow` | 8 | `name`, `enteredBy`, `dateEntered`, `certified`, `certifiedBy`, … (7) |
| `search.contest_missing_transportation` | `GET /contest/transportation/search/contest/{contest_id}/missing` | `TransportationMissingRow` | 11 | `countryName`, `firstName`, `lastName`, `email`, `attendingOnsite`, … (6) |
| `search.contest_team_summaries` | `GET /team/search/{contest_id}/all` | `TeamSummaryRow` | 22 | `teamId`, `teamName`, `rank`, `siteName`, `country`, … (15) |
| `search.contest_promote_candidates` | `GET /team/search/{contest_id}/promote` | `PromoteRow` | 9 | `rank`, `siteName`, `teamName`, `institutionName` |

Column names are typed: `search.<factory>(id).fields` exposes each one, and
a projection naming an unknown column is refused before the request is sent.
