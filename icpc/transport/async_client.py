"""Async transport.

Make sure to keep this file consistent with a :mod:`icpc.transport.sync_client`.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Self

import httpx

from icpc import errors
from icpc.config import Settings
from icpc.transport._shared import (
    auth_headers,
    check_empty,
    check_html,
    raise_for_status,
    retry_delay,
    should_retry,
)

if TYPE_CHECKING:
    from icpc.auth.provider import AsyncTokenProvider
    from icpc.transport.operation import Operation

__all__ = ["AsyncTransport"]


class AsyncTransport:
    """Sends :class:`~icpc.transport.operation.Operation` objects over httpx."""

    def __init__(
        self,
        auth: AsyncTokenProvider | None = None,
        *,
        settings: Settings | None = None,
        http: httpx.AsyncClient | None = None,
    ) -> None:
        self.settings = settings or Settings()
        self.auth = auth
        self._owns_http = http is None
        self._http = http or httpx.AsyncClient(
            base_url=self.settings.base_url,
            timeout=self.settings.timeout,
            follow_redirects=True,
        )
        self._gate = asyncio.Semaphore(self.settings.max_concurrency)

    async def send[T](self, operation: Operation[T]) -> T:
        """Issue ``operation`` and return its parsed, typed result."""
        request = operation.request
        reauthenticated = False
        attempt = 0
        while True:
            token = await self._token(request.auth)
            try:
                async with self._gate:
                    response = await self._http.request(
                        request.method,
                        request.path,
                        params=dict(request.params),
                        json=request.json,
                        files=dict(request.files) if request.files else None,
                        headers=auth_headers(self.settings, token),
                        timeout=self._timeout(request.slow),
                    )
            except httpx.TimeoutException as exc:
                if request.idempotent and attempt + 1 < self.settings.max_attempts:
                    await asyncio.sleep(retry_delay(attempt, self.settings))
                    attempt += 1
                    continue
                raise errors.TransportError(f"{request.describe()}: {exc}") from exc
            except httpx.HTTPError as exc:
                raise errors.TransportError(f"{request.describe()}: {exc}") from exc

            if response.status_code == 401 and request.auth and not reauthenticated:
                reauthenticated = True
                await self._invalidate()
                continue
            if should_retry(response, request) and attempt + 1 < self.settings.max_attempts:
                await asyncio.sleep(retry_delay(attempt, self.settings, response))
                attempt += 1
                continue

            raise_for_status(response, request)
            check_html(response, request)
            if operation.expects_body:
                check_empty(response, request)
            return operation.parse(response)

    async def _token(self, needed: bool) -> str | None:
        if not needed or self.auth is None:
            return None
        return await self.auth.id_token()

    async def _invalidate(self) -> None:
        if self.auth is not None:
            await self.auth.invalidate()

    def _timeout(self, slow: bool) -> httpx.Timeout:
        if not slow:
            return self.settings.timeout
        return httpx.Timeout(
            connect=self.settings.timeout.connect,
            read=self.settings.slow_read_timeout,
            write=self.settings.slow_read_timeout,
            pool=self.settings.timeout.pool,
        )

    async def aclose(self) -> None:
        if self._owns_http:
            await self._http.aclose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()
