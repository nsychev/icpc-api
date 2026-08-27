#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "icpc-api",
#   "tqdm>=4",
# ]
# ///
"""Attach one file per team, from a folder named after the attachment.

    ./upload_files.py CONTEST_ID FOLDER [--name PREFIX] [--no-replace]

The folder should contain one file per team, named by team id — `1234567.pdf`,
`1234568.pdf`. By default, the attachments will be named after the folder,
this behaviour is overridable with `--name`.

By default each team's existing attachments with the same prefix and extension
are deleted first, so re-running the script replaces rather than piles up.
`--no-replace` skips the deletion and leaves both copies.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from tqdm.asyncio import tqdm

from icpc import ApiError, AsyncIcpc
from icpc.api import team as team_api
from icpc.config import Settings
from icpc.facade.client import Include

#: How many stray team ids to name before "…" in the guard's error.
SHOWN = 5

#: What to tell the server a file is. Anything else goes up as a PDF, which is
#: what every attachment icpc.global asks for in practice is.
MIME = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


def collect(folder: Path) -> list[tuple[int, Path]]:
    """`(team id, path)` for every file in the folder named after a team id."""
    found = []
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if not path.stem.isdigit():
            print(f"skipping {path.name}: not named after a team id", file=sys.stderr)
            continue
        found.append((int(path.stem), path))
    return found


async def handle(
    icpc: AsyncIcpc, team_id: int, path: Path, prefix: str, args: argparse.Namespace
) -> tuple[int, int]:
    """One team's attachment: replace what is there, then upload.

    Returns `(deleted, uploaded)` so the caller can total them up. The steps
    are sequential on purpose — the delete has to happen before the upload, or
    it would match the file just uploaded and remove it again.
    """
    suffix = path.suffix.lower()
    filename = f"{prefix}{suffix}"
    deleted = 0
    if not args.no_replace:
        for old in await icpc.send(team_api.files(team_id)):
            name = old.name or ""
            if old.id is None or not (name.startswith(prefix) and name.endswith(suffix)):
                continue
            if args.dry_run:
                tqdm.write(f"team {team_id}: would delete {name}")
            else:
                await icpc.send(team_api.delete_file(old.id))
                tqdm.write(f"team {team_id}: deleted {name}")
            deleted += 1
    if args.dry_run:
        tqdm.write(f"team {team_id}: would upload {path} as {filename}")
        return deleted, 1
    # Off the event loop: with several uploads in flight, reading a PDF inline
    # would stall the others.
    content = await asyncio.to_thread(path.read_bytes)
    try:
        await icpc.send(
            team_api.upload_file(team_id, filename, content, MIME.get(suffix, "application/pdf"))
        )
    except ApiError as exc:
        tqdm.write(f"team {team_id}: upload failed: {exc}", file=sys.stderr)
        return deleted, 0
    tqdm.write(f"team {team_id}: uploaded {path.name} as {filename}")
    return deleted, 1


async def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("contest_id", type=int, help="Contest the teams must belong to.")
    parser.add_argument("folder", type=Path, help="Folder of {team id}.ext files.")
    parser.add_argument(
        "--name",
        help="Attachment name, extension excluded. Defaults to the folder's own name.",
    )
    parser.add_argument(
        "--no-replace",
        action="store_true",
        help="Keep existing attachments with this prefix instead of deleting them.",
    )
    parser.add_argument("--user", help="Which cached icpc.global account to use.")
    parser.add_argument(
        "--concurrency", type=int, default=4, help="Requests in flight (default: %(default)s)."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Say what would happen, change nothing."
    )
    args = parser.parse_args()

    if not args.folder.is_dir():
        parser.error(f"{args.folder} is not a folder")
    prefix = args.name or args.folder.resolve().name
    uploads = collect(args.folder)
    if not uploads:
        parser.error(f"no {{team id}}.ext files in {args.folder}")

    settings = Settings(max_concurrency=args.concurrency)
    async with AsyncIcpc.from_store(args.user, settings=settings) as icpc:
        # One cheap fetch of the team list, so a wrong folder fails before it
        # writes anything rather than halfway through.
        view = await icpc.load_contest(args.contest_id, Include.TEAMS)
        contest = {team.id for team in view.teams}
        strangers = [team_id for team_id, _ in uploads if team_id not in contest]
        if strangers:
            parser.error(
                f"{len(strangers)} of {len(uploads)} teams are not in contest "
                f"{args.contest_id}: {', '.join(map(str, strangers[:SHOWN]))}"
                f"{'…' if len(strangers) > SHOWN else ''}"
            )

        # Each team is independent, so they all start at once; the transport's
        # gate decides how many requests are actually in flight.
        results = await tqdm.gather(
            *(handle(icpc, team_id, path, prefix, args) for team_id, path in uploads),
            desc="uploading",
            unit="team",
            disable=not sys.stderr.isatty(),
        )

    replaced = sum(deleted for deleted, _ in results)
    uploaded = sum(count for _, count in results)
    verb = "would upload" if args.dry_run else "uploaded"
    print(f"{verb} {uploaded} files, replacing {replaced}", file=sys.stderr)
    return 0 if uploaded == len(uploads) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
