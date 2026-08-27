"""What the transports need from an authenticator."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["AsyncTokenProvider", "TokenProvider"]


@runtime_checkable
class AsyncTokenProvider(Protocol):
    async def id_token(self) -> str:
        """Return a currently valid Cognito id token, obtaining one if needed."""
        ...

    async def invalidate(self) -> None:
        """Drop the cached token; the next call must fetch a fresh one.

        Called by the transport after a 401, which is the only reliable signal that
        a token the clock says is fine has actually been rejected.
        """
        ...


@runtime_checkable
class TokenProvider(Protocol):
    def id_token(self) -> str: ...

    def invalidate(self) -> None: ...
