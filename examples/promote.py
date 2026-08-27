#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "icpc-api",
#   "tqdm>=4",
# ]
# ///
"""Promote teams to a site of the parent contest.

    ./promote.py SITE_ID TEAM_ID...
    ./promote.py SITE_ID --from-file advancing.txt
    cat advancing.txt | ./promote.py SITE_ID -

One team ID per line in a file, blank lines and `#` comments ignored.
The script skips and reports all teams that can not be promoted.
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


def read_ids(source: str) -> list[int]:
    """Team ids from a file, or from stdin when the name is `-`."""
    text = sys.stdin.read() if source == "-" else Path(source).read_text()
    lines = (line.split("#", 1)[0].strip() for line in text.splitlines())
    return [int(line) for line in lines if line]


async def promote(icpc: AsyncIcpc, team_id: int, site_id: int) -> str | None:
    """Promote one team, returning what to report on failure and None on success.

    Both refusals — already promoted (an HTTP 500 the SDK raises as
    `TeamNotPromotable`) and a site conflict (a plain 400) — are `ApiError`,
    and neither is worth abandoning the rest of the batch for.
    """
    try:
        await icpc.send(team_api.promote(team_id, site_id))
    except ApiError as exc:
        return f"team {team_id}: {exc.body.strip()[:120] or exc}"
    # `tqdm.write` instead of `print`, or the line lands on top of the bar.
    tqdm.write(f"team {team_id} → site {site_id}")
    return None


async def main() -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("site_id", type=int, help="Site of the parent contest to promote into.")
    parser.add_argument("team_ids", type=int, nargs="*", help="Team ids; or use --from-file.")
    parser.add_argument("--from-file", metavar="PATH", help="Read team ids from a file, or `-`.")
    parser.add_argument("--user", help="Which cached icpc.global account to use.")
    parser.add_argument(
        "--concurrency", type=int, default=4, help="Requests in flight (default: %(default)s)."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Say what would be promoted, promote nothing."
    )
    args = parser.parse_args()

    teams = list(args.team_ids)
    if args.from_file:
        teams += read_ids(args.from_file)
    if not teams:
        parser.error("no team ids: pass them as arguments or with --from-file")

    if args.dry_run:
        for team_id in teams:
            print(f"would promote {team_id} → site {args.site_id}")
        return 0

    settings = Settings(max_concurrency=args.concurrency)
    async with AsyncIcpc.from_store(args.user, settings=settings) as icpc:
        failures = await tqdm.gather(
            *(promote(icpc, team_id, args.site_id) for team_id in teams),
            desc="promoting",
            unit="team",
            disable=not sys.stderr.isatty(),
        )

    for failure in filter(None, failures):
        print(failure, file=sys.stderr)
    failed = sum(1 for failure in failures if failure)
    print(f"promoted {len(teams) - failed} of {len(teams)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
