"""Columns for `icpc contest load`."""

from __future__ import annotations

import re

import pytest

from icpc.cli.columns import (
    RowKind,
    apply_columns,
    fields_of,
    pluck,
    resolve_columns,
    rows_of,
    source_of,
    tables_for,
    validate,
)
from icpc.facade.client import Include
from icpc.facade.domain import join
from icpc.models import ContestParticipantRow, InstitutionRow, TeamMemberRow, TeamRow
from icpc.models.common import NamedRef
from icpc.models.entities import Contest

TEAMS = [
    TeamRow.model_validate(
        {"id": 1, "name": "Alpha", "status": "ACCEPTED", "site": "Almaty", "instId": 100}
    ),
    TeamRow.model_validate({"id": 2, "name": "Beta", "status": "PENDING", "site": "Almaty"}),
]

MEMBERS = [
    TeamMemberRow.model_validate(
        {"teamId": 1, "personId": 11, "firstName": "Ann", "lastName": "Lee", "role": "CONTESTANT"}
    ),
    TeamMemberRow.model_validate(
        {"teamId": 1, "personId": 12, "firstName": "Bo", "lastName": "Ng", "role": "COACH"}
    ),
    TeamMemberRow.model_validate(
        {"teamId": 1, "personId": 13, "firstName": "Cy", "lastName": "Vo", "role": "RESERVE"}
    ),
    TeamMemberRow.model_validate(
        {"teamId": 2, "personId": 21, "firstName": "Di", "lastName": "Ba", "role": "CONTESTANT"}
    ),
]

INSTITUTIONS = [InstitutionRow.model_validate({"instId": 100, "instName": "NU", "city": "Astana"})]

VIEW = join(TEAMS, members=MEMBERS, institutions=INSTITUTIONS)
ROWS = rows_of(VIEW, RowKind.TEAMS)


def test_rosters_are_split_by_role():
    """`other` is the complement of contestants and coaches, not a leftover list."""
    assert [m["username"] or m["personId"] for m in ROWS[0]["contestants"]] == [11]
    assert [m["personId"] for m in ROWS[0]["coaches"]] == [12]
    assert [m["personId"] for m in ROWS[0]["other"]] == [13]


def test_paths_reach_rosters_and_the_institution():
    assert pluck(ROWS[0], "name") == "Alpha"
    assert pluck(ROWS[0], "coaches[0].firstName") == "Bo"
    assert pluck(ROWS[0], "institution.instName") == "NU"
    assert pluck(ROWS[0], "contestants[-1].lastName") == "Lee"


@pytest.mark.parametrize(
    "path",
    ["nope", "coaches[3].firstName", "institution.instName.deeper", "coaches.firstName"],
)
def test_a_path_that_runs_out_is_blank_not_an_error(path):
    """A three-person team has no fourth contestant; that is data, not a bug."""
    assert pluck(ROWS[0], path) is None


def test_repeats_widen_to_the_longest_list():
    columns = resolve_columns(["C{n}=contestants[{i}].firstName"], ROWS)
    assert columns == [("C1", "contestants[0].firstName")]


def test_repeats_can_be_pinned_so_the_columns_stay_put():
    columns = resolve_columns(["C{n}=contestants[{i}].firstName"], ROWS, {"contestants": 3})
    assert [name for name, _ in columns] == ["C1", "C2", "C3"]
    # The teams have one contestant each, so the pinned extras are blank.
    assert apply_columns(ROWS, columns)[0] == {"C1": "Ann", "C2": None, "C3": None}


def test_consecutive_specs_over_one_list_are_interleaved():
    """`C1.First, C1.Last, C2.First, …` — the order a person reads a roster in."""
    columns = resolve_columns(
        ["C{n}.First=contestants[{i}].firstName", "C{n}.Last=contestants[{i}].lastName"],
        ROWS,
        {"contestants": 2},
    )
    assert [name for name, _ in columns] == ["C1.First", "C1.Last", "C2.First", "C2.Last"]


def test_separate_lists_keep_their_own_widths():
    columns = resolve_columns(
        ["C{n}=contestants[{i}].firstName", "O{n}=other[{i}].role"],
        ROWS,
        {"contestants": 2, "other": 1},
    )
    assert [name for name, _ in columns] == ["C1", "C2", "O1"]


def test_a_bare_spec_is_the_path_and_the_name():
    """`--col instName` is the common case: keep the grid's own name."""
    assert resolve_columns(["instName"], ROWS) == [("instName", "instName")]


@pytest.mark.parametrize("spec", ["=contestants", "name="])
def test_a_half_written_spec_is_rejected(spec):
    with pytest.raises(ValueError, match="NAME=PATH"):
        resolve_columns([spec], ROWS)


def test_a_wildcard_collects_the_whole_list():
    people = rows_of(VIEW, RowKind.PARTICIPANTS)
    ann = next(p for p in people if p["personId"] == 11)
    assert pluck(ann, "memberships[*].team.id") == [1]
    assert pluck(ann, "memberships[*].role") == ["CONTESTANT"]


def test_a_wildcard_column_is_joined_into_one_cell():
    """A sheet wants `1,2` in a TeamIds column, not a JSON array."""
    rows = [{"memberships": [{"teamId": 1}, {"teamId": 2}]}]
    columns = resolve_columns(["TeamIds=memberships[*].teamId"], rows)
    assert apply_columns(rows, columns) == [{"TeamIds": "1,2"}]
    assert apply_columns(rows, columns, join=" ") == [{"TeamIds": "1 2"}]


def test_a_wildcard_over_booleans_uses_the_renderer_words():
    rows = [{"memberships": [{"attendingOnsite": True}, {"attendingOnsite": False}]}]
    columns = resolve_columns(["Onsite=memberships[*].attendingOnsite"], rows)
    assert apply_columns(rows, columns) == [{"Onsite": "yes,no"}]


def test_a_person_on_two_teams_is_one_row_with_two_memberships():
    """The whole point of `--rows participants`: aggregation the members table cannot do."""
    teams = [
        TeamRow.model_validate({"id": 1, "name": "Alpha"}),
        TeamRow.model_validate({"id": 2, "name": "Beta"}),
    ]
    members = [
        TeamMemberRow.model_validate({"teamId": 1, "personId": 11, "role": "COACH"}),
        TeamMemberRow.model_validate({"teamId": 2, "personId": 11, "role": "COACH"}),
    ]
    rows = rows_of(join(teams, members=members), RowKind.PARTICIPANTS)
    assert len(rows) == 1
    columns = resolve_columns(["TeamIds=memberships[*].team.id"], rows)
    assert apply_columns(rows, columns) == [{"TeamIds": "1,2"}]


def test_metadata_puts_the_site_id_and_the_contest_on_a_row():
    """A team row names its site but never carries the id; the join supplies it."""
    view = join(
        TEAMS,
        members=MEMBERS,
        contest=Contest.model_validate({"id": 9, "name": "Regional", "year": 2026}),
        sites=[NamedRef(id=77, name="Almaty")],
    )
    row = rows_of(view, RowKind.TEAMS)[0]
    assert pluck(row, "siteId") == 77
    assert pluck(row, "contest.name") == "Regional"
    assert pluck(rows_of(view, RowKind.MEMBERS)[0], "team.siteId") == 77


def test_without_the_metadata_fetch_those_are_blank_not_an_error():
    """`--include teams` skips the site list; the column is simply empty."""
    row = rows_of(join(TEAMS), RowKind.TEAMS)[0]
    assert pluck(row, "siteId") is None
    assert pluck(row, "contest.name") is None


@pytest.mark.parametrize("kind", list(RowKind))
def test_every_listed_field_is_a_path_that_resolves(kind):
    """`--fields` is read off the models; keep it honest about the rows built.

    Every listed path must be reachable — placeholders aside — or the listing
    would send people after columns that are always blank.
    """
    view = join(
        TEAMS,
        members=MEMBERS,
        institutions=INSTITUTIONS,
        participants=[ContestParticipantRow.model_validate({"personId": 11, "shirtSize": "L"})],
        contest=Contest.model_validate({"id": 9, "name": "Regional", "contestSettings": {"id": 8}}),
        sites=[NamedRef(id=77, name="Almaty")],
    )
    rows = rows_of(view, kind)
    for field in fields_of(kind):
        path = field["path"]
        if "<" in path:  # extras.<question> and the like: keyed by the contest
            continue
        parent, _, leaf = path.replace("[i]", "[0]").rpartition(".")
        containers = [pluck(row, parent) for row in rows] if parent else list(rows)
        assert any(isinstance(c, dict) and leaf in c for c in containers), (
            f"{path} is listed but no {kind} row has it"
        )


def test_the_field_listing_needs_no_contest():
    """It is model introspection, so `--fields` answers without a fetch."""
    assert {f["from"] for f in fields_of(RowKind.TEAMS)} == {
        "teams",
        "metadata",
        "institutions",
        "members",
        "participants",
        "surveys",
    }


def test_the_listing_reports_the_table_a_path_reads():
    """The `from` column is the same rule that decides what gets fetched."""
    listed = {f["path"]: f["from"] for f in fields_of(RowKind.TEAMS)}
    assert listed["id"] == "teams"
    assert listed["siteId"] == "metadata"
    assert listed["institution.city"] == "institutions"
    # Both live under `members[i].`, and they cost different fetches.
    assert listed["members[i].username"] == "teams"
    assert listed["members[i].firstName"] == "members"
    assert listed["members[i].participant.<participant field>"] == "participants"


@pytest.mark.parametrize(
    "path",
    [
        "instName",
        "coaches[0].shirtSize",
        "members[*].participant.dob",
        "institution.countryName",
        "contest.contestSettings.requireCertification",
        "extras.whatever-the-contest-asked",
        "contestants",  # a bare list is a legal column; it renders as JSON
    ],
)
def test_a_good_path_validates(path):
    validate(RowKind.TEAMS, path)


@pytest.mark.parametrize(
    ("path", "message"),
    [
        ("personInfo.shirtSize", "unknown field 'personInfo'"),
        ("contestants[0].personInfo.shirtSize", "under 'contestants[0]'"),
        ("instname", "did you mean instName"),
        ("coaches.firstName", "is a list"),
        ("institution.city.deeper", "nothing is under it"),
        ("instName[0]", "is not a list"),
        ("contest.year.month", "nothing is under it"),
    ],
)
def test_a_bad_path_is_rejected_with_a_reason(path, message):
    """Typing a column wrong should cost a message, not an empty column."""
    with pytest.raises(ValueError, match=re.escape(message)):
        validate(RowKind.TEAMS, path)


def test_validation_follows_the_row_kind():
    """`memberships` exists for people and nowhere else."""
    validate(RowKind.PARTICIPANTS, "memberships[0].team.siteId")
    with pytest.raises(ValueError, match="unknown field 'memberships'"):
        validate(RowKind.TEAMS, "memberships[0].team.siteId")


@pytest.mark.parametrize(
    ("path", "tables"),
    [
        ("name", {"teams"}),
        ("institution.instName", {"teams", "institutions"}),
        ("contest.year", {"teams", "metadata"}),
        ("siteId", {"teams", "metadata"}),
        # The team row's own blob names the roster, so ids, usernames and roles
        # cost nothing extra.
        ("coaches[0].username", {"teams"}),
        ("contestants[*].personId", {"teams"}),
        # Anything else about a member means the teammember table.
        ("coaches[0].firstName", {"teams", "members"}),
        ("contestants[{i}].shirtSize", {"teams", "members"}),
        # The blob roster carries person ids, so the participant record
        # attaches without the teammember table.
        ("members[*].participant.dob", {"teams", "participants"}),
    ],
)
def test_the_columns_decide_what_is_fetched(path, tables):
    assert tables_for(RowKind.TEAMS, [path]) == tables


def test_the_row_kind_adds_what_it_cannot_work_without():
    assert tables_for(RowKind.PARTICIPANTS, ["username"]) == {"teams", "members", "participants"}
    assert tables_for(RowKind.INSTITUTIONS, ["instName"]) == {"teams", "institutions"}


def test_member_rows_are_one_per_membership():
    rows = rows_of(VIEW, RowKind.MEMBERS)
    assert len(rows) == len(MEMBERS)
    assert pluck(rows[0], "team.name") == "Alpha"
    assert pluck(rows[0], "firstName") == "Ann"


def test_include_named_takes_the_tables_that_were_asked_for():
    """`tables_for` answers in names; `Include.named` is what turns them into flags."""
    tables = tables_for(RowKind.TEAMS, ["institution.instName"])
    assert Include.named(tables) == Include.TEAMS | Include.INSTITUTIONS
    assert Include.named(["default"]) is Include.DEFAULT
    assert Include.named([]) == Include(0)


@pytest.mark.parametrize("name", ["nope", "named", "TEAM"])
def test_include_named_says_what_the_tables_are(name):
    """A lookup by attribute would answer the same for a typo and for a method."""
    with pytest.raises(ValueError, match="pick from teams, members"):
        Include.named([name])


def test_a_survey_column_is_open_and_reads_the_surveys_table():
    """Answers are keyed by survey field id, so anything under `survey.` goes."""
    validate(RowKind.MEMBERS, "survey.1134")
    validate(RowKind.TEAMS, "contestants[0].survey.1134")
    assert source_of(RowKind.MEMBERS, "survey.1134") == "surveys"


def test_surveys_are_fetched_only_for_a_survey_column():
    """Every survey costs its own paged fetch, so it must not be on by default."""
    assert "surveys" not in tables_for(RowKind.MEMBERS, ["firstName"])
    assert "surveys" in tables_for(RowKind.MEMBERS, ["survey.1134"])
