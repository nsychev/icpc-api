"""The two transports must stay mirrors of each other.

They are the only hand-duplicated code in the package. Rather than generate one
from the other — which would put generated code in stack traces — both are
normalised to a common shape and compared, so an edit to one that is not mirrored
in the other fails here.

Only the module body below the imports is compared: the import blocks genuinely
differ (``asyncio`` against ``threading`` and ``time``).
"""

from __future__ import annotations

import re
from pathlib import Path

TRANSPORT = Path(__file__).resolve().parents[2] / "icpc" / "transport"

#: Pairs that mean the same thing on either side.
EQUIVALENCES = [
    ("async ", ""),
    ("await ", ""),
    ("Async", ""),
    ("asyncio.sleep", "SLEEP"),
    ("time.sleep", "SLEEP"),
    ("asyncio.Semaphore", "SEMAPHORE"),
    ("threading.Semaphore", "SEMAPHORE"),
    ("aclose", "close"),
    ("__aenter__", "__enter__"),
    ("__aexit__", "__exit__"),
    ("sync_client", "CLIENT"),
    ("async_client", "CLIENT"),
    ("TokenProvider", "PROVIDER"),
]


def normalise(source: str) -> str:
    body = source.split("__all__", 1)[1]
    for pattern, replacement in EQUIVALENCES:
        body = body.replace(pattern, replacement)
    return re.sub(r"\s+", " ", body).strip()


def test_async_and_sync_transports_are_mirrors():
    a = normalise((TRANSPORT / "async_client.py").read_text(encoding="utf-8"))
    b = normalise((TRANSPORT / "sync_client.py").read_text(encoding="utf-8"))
    assert a == b, (
        "async_client.py and sync_client.py have diverged. Mirror the change, or "
        "extend EQUIVALENCES if the difference is genuinely unavoidable."
    )


def test_both_expose_the_same_public_surface():
    from icpc.transport.async_client import AsyncTransport
    from icpc.transport.sync_client import Transport

    def public(cls: type) -> set[str]:
        return {name for name in vars(cls) if not name.startswith("_")}

    assert public(AsyncTransport) - {"aclose"} == public(Transport) - {"close"}
