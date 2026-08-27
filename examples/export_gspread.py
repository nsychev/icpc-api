#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "icpc-api[cli]",
#   "gspread>=6",
# ]
# ///
"""Export a contest into the three registration sheets, in one fetch.

    ./export_gspread.py SPREADSHEET_ID CONTEST_ID

Writes three worksheets, replacing all existing content:

    icpc     one row per team with all its members
    p-icpc   one row per person
    u-icpc   one row per institution

Google credentials come from a service account key: pass ``--credentials`` or
leave it at ``service-account.json``. Share the spreadsheet with that service
account's address, or it will not be able to open it.
"""

from __future__ import annotations

import argparse
import enum
import sys

import gspread

from icpc import Icpc
from icpc.cli.columns import RowKind, apply_columns, resolve_columns, rows_of, tables_for
from icpc.facade.client import Include

#: One row per team. `{i}` repeats a column over a roster, `{n}` numbers the
#: header from 1, and the widths are pinned so the columns of the sheet stay
#: where they are between runs.
TEAMS = [
    "id",
    "site",
    "instName",
    "name",
    "status",
    "eligibilityStatus",
    "eligibilityIssue",
    "C.First=coaches[0].firstName",
    "C.Last=coaches[0].lastName",
    "C.Id=coaches[0].username",
    "C{n}.First=contestants[{i}].firstName",
    "C{n}.Last=contestants[{i}].lastName",
    "C{n}.Id=contestants[{i}].username",
    "O{n}.Role=other[{i}].role",
    "O{n}.First=other[{i}].firstName",
    "O{n}.Last=other[{i}].lastName",
    "O{n}.Id=other[{i}].username",
    "instAddress",
]
WIDTHS = {"contestants": 3, "other": 5}

#: One row per person. `[*]` joins a list into one cell, which is what makes
#: TeamIds and Onsite possible: they are per-membership facts about a person.
PEOPLE = [
    "PersonId=personId",
    "Id=username",
    "First=firstName",
    "Last=lastName",
    "LocalName=localName",
    "BadgeName=badgeName",
    "CertificateName=memberships[*].certificateName",
    "Shirt=shirtSize",
    "TeamIds=memberships[*].team.id",
    "Onsite=memberships[*].attendingOnsite",
    "Phone=phone",
    "ExpectedGrad=expectedGrad",
    "DOB=dob",
]

INSTITUTIONS = [
    "Country=countryName",
    "Type=instUnitType",
    "UnitName=instUnitName",
    "UnitShortName=instUnitShortName",
    "Url=instHomepageUrl",
    "TwitterName=twitterName",
    "TwitterHash=twitterHash",
    "InstName=instName",
    "InstAbbr=instUnitShortName",
    "InstUnitId=instUnitId",
    "InstId=instId",
    "City=city",
    "InstNativeName=instNativeName",
    "instUnitNativeName=instUnitNativeName",
    "addressLine1=addressLine1",
    "addressLine2=addressLine2",
    "addressLine3=addressLine3",
    "state=state",
    "zip=zip",
    "longitude=longitude",
    "latitude=latitude",
    "facebookPage=facebookPage",
]

SHEETS: list[tuple[str, RowKind, list[str], dict[str, int]]] = [
    ("icpc", RowKind.TEAMS, TEAMS, WIDTHS),
    ("p-icpc", RowKind.PARTICIPANTS, PEOPLE, {}),
    ("u-icpc", RowKind.INSTITUTIONS, INSTITUTIONS, {}),
]


def _cell(value: object) -> object:
    """One cell as gspread wants it: a JSON scalar, never None.

    A cleared cell and an empty string are different to `=isblank()`, and the
    sheet is cleared before writing, so a blank must be written as "".
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, enum.Enum):
        # Statuses and shirt sizes arrive as enums; write what they say.
        return value.value
    if isinstance(value, int | float | str):
        return value
    return str(value)


def build(icpc: Icpc, contest_id: int) -> dict[str, list[list[object]]]:
    """Fetch the contest once and lay out all three sheets from it."""
    # Ask for every table any of the three layouts reads, then load once — the
    # three sheets share one fetch rather than three.
    tables = set()
    for _, kind, columns, _widths in SHEETS:
        tables |= tables_for(kind, [spec.rpartition("=")[2] for spec in columns])
    view = icpc.load_contest(contest_id, Include.named(tables))

    sheets = {}
    for title, kind, columns, widths in SHEETS:
        rows = rows_of(view, kind)
        layout = resolve_columns(columns, rows, widths)
        header = [name for name, _ in layout]
        sheets[title] = [header] + [
            [_cell(row[name]) for name in header] for row in apply_columns(rows, layout)
        ]
    return sheets


def write(spreadsheet: gspread.Spreadsheet, title: str, values: list[list[object]]) -> None:
    """Replace a worksheet's contents, creating it if this is the first run."""
    try:
        sheet = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        sheet = spreadsheet.add_worksheet(title, rows=len(values) + 10, cols=len(values[0]) + 5)
    # Clearing first matters: writing "" over an old cell leaves =isblank()
    # false, and writing None leaves the old value in place entirely.
    sheet.clear()
    sheet.update(values)
    print(
        f"{title}: {len(values) - 1} rows → "
        f"https://docs.google.com/spreadsheets/d/{spreadsheet.id}/edit?gid={sheet.id}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("spreadsheet_id", help="The key from the spreadsheet's URL.")
    parser.add_argument("contest_id", type=int)
    parser.add_argument(
        "--credentials",
        default="service-account.json",
        help="Google service-account key file (default: %(default)s).",
    )
    parser.add_argument("--user", help="Which cached icpc.global account to use.")
    args = parser.parse_args()

    client = gspread.service_account(filename=args.credentials)
    spreadsheet = client.open_by_key(args.spreadsheet_id)

    with Icpc.from_store(args.user) as icpc:
        sheets = build(icpc, args.contest_id)

    for title, _kind, _columns, _widths in SHEETS:
        write(spreadsheet, title, sheets[title])
    return 0


if __name__ == "__main__":
    sys.exit(main())
