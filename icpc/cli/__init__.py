"""The console script with guard for missing optional extra."""

from __future__ import annotations

import sys

__all__ = ["run"]


def run() -> None:
    try:
        from icpc.cli.main import run as _run  # noqa: PLC0415
    except ImportError as exc:
        sys.stderr.write(
            f"The CLI could not run: {exc}\n"
            f"Please install 'cli' extra dependencies, for example:\n"
            f"    uv tool install 'icpc-api[cli]'\n"
        )
        raise SystemExit(1) from exc
    _run()
