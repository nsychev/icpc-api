# Examples

Use `uv` to run these examples:

```bash
uv run examples/export_gspread.py SPREADSHEET_ID CONTEST_ID
```

The scripts carry their dependencies in [PEP723][pep723] metadata, so they will
be handled automatically.

If you don't want to use `uv`, you can create a virtualenv and manually install
the dependencies listed in the beginning of a respective script.

Authenticate before using via `icpc auth login`.

[pep723]: https://peps.python.org/pep-0723/

## `export_gspread.py` — the registration spreadsheet

```bash
uv run examples/export_gspread.py 1AbC…xyz 1234 --credentials service-account.json
```

Fetches the contest and writes three worksheets: `icpc` for team list, `p-icpc`
for contestant list, and `u-icpc` for university list.

The list of columns is defined in the script and could be changed.
Use `icpc contest load --fields [--rows participants|institutions]` to list all
known fields.

Needs a Google service-account key, and the spreadsheet shared with that
account's address.

## `promote.py` — advancing teams to the next stage

```bash
./examples/promote.py 3456 1234567 1234568
./examples/promote.py 3456 --from-file advancing.txt      # `-` reads stdin
```

One team ID per line, `#` comments ignored. `--dry-run` prints the plan and
exits.

## `upload_files.py` — upload attachments to icpc.global

```bash
./examples/upload_files.py 1234 INVITATION-/
./examples/upload_files.py 1234 attachments/ --name INVITATION- --no-replace
```

The folder holds `{team id}.pdf` files and is named after the attachment, so
`INVITATION-/1234567.pdf` is uploaded to team 1234567 as `INVITATION-.pdf`.

⚠ **icpc.global renames uploads.** `INVITATION-.pdf` appears in the cabinet as
`INVITATION-9776387880749677008.pdf` — a long random number is inserted before
the extension. Hence the trailing dash in the prefix, and hence replacement
matches on prefix and extension rather than on the whole name.

By default an existing attachment with the same prefix and extension is deleted
before the new one goes up, so re-running replaces rather than accumulates;
`--no-replace` keeps both. `--dry-run` shows what would be deleted and uploaded.
