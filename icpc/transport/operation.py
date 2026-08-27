"""Types for request and response objects for both clients.

Every endpoint in :mod:`icpc.api` is a function returning an ``Operation[T]`` instead
of actually making the request. The operations holds a description of the request and
a parser that turns the response into ``T``.

This helps to make endpoints universal and typed for both the async and sync clients.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from functools import cache
from typing import Any, Literal

import httpx
from pydantic import TypeAdapter

__all__ = [
    "Method",
    "Operation",
    "Request",
    "bytes_op",
    "list_op",
    "model_op",
    "none_op",
    "scalar_op",
]

Method = Literal["GET", "POST", "PUT", "DELETE"]

#: A multipart part: (filename, content, content-type).
FilePart = tuple[str, bytes, str]


@dataclass(frozen=True, slots=True)
class Request:
    """Everything needed to issue one HTTP call, with no I/O attached."""

    method: Method
    #: Path relative to :attr:`icpc.config.Settings.base_url`, e.g. ``/team/1234567``.
    path: str
    params: Mapping[str, str | int] = field(default_factory=dict)
    json: object | None = None
    files: Mapping[str, FilePart] | None = None
    #: ``/contest/public/*`` works unauthenticated; those set this to ``False``.
    auth: bool = True
    #: Only idempotent requests are ever retried. Every write sets this to
    #: ``False``: replaying a write would apply it twice.
    idempotent: bool = True
    #: Exports and huge search pages need a longer read timeout.
    slow: bool = False

    def describe(self) -> str:
        """One-line summary used in errors and by ``--explain``/``icpc raw``."""
        query = "&".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.method} {self.path}" + (f"?{query}" if query else "")


@dataclass(frozen=True, slots=True)
class Operation[T]:
    """A request paired with the parser producing its typed result."""

    request: Request
    parse: Callable[[httpx.Response], T]
    #: Whether an empty response body is an error. False for writes, which often
    #: answer 200 with nothing at all.
    expects_body: bool = True

    def map[R](self, fn: Callable[[T], R]) -> Operation[R]:
        """Post-process the parsed result, keeping the request unchanged."""
        parse = self.parse
        return Operation(self.request, lambda response: fn(parse(response)), self.expects_body)


@cache
def _cached_adapter(spec: Any) -> TypeAdapter[Any]:
    # Building a TypeAdapter is expensive and endpoint factories run per call, so
    # every distinct type is compiled once and reused.
    return TypeAdapter(spec)


def _adapter[T](spec: Any) -> TypeAdapter[T]:
    """Cached adapter for ``spec``, asserted to produce ``T``.

    The cast is the one unchecked step in the whole parse path; every caller below
    passes a ``spec`` that matches its own annotation.
    """
    return _cached_adapter(spec)


def model_op[T](request: Request, type_: type[T]) -> Operation[T]:
    """Parse the body as a single ``type_``."""
    adapter: TypeAdapter[T] = _adapter(type_)
    return Operation(request, lambda r: adapter.validate_json(r.content))


def list_op[T](request: Request, type_: type[T]) -> Operation[list[T]]:
    """Parse the body as a bare JSON array of ``type_``.

    Search endpoints return a bare array with no envelope and no total; the total
    comes from the sibling ``/count`` path.
    """
    # Built at runtime from a variable, so it is a value here, not an annotation.
    list_of: Any = list
    adapter: TypeAdapter[list[T]] = _adapter(list_of[type_])
    return Operation(request, lambda r: adapter.validate_json(r.content))


def scalar_op[T: (int, float, str, bool)](request: Request, type_: type[T]) -> Operation[T]:
    """Parse a bare JSON scalar, as ``/count`` and a few boolean endpoints return."""
    adapter: TypeAdapter[T] = _adapter(type_)
    return Operation(request, lambda r: adapter.validate_json(r.content))


def none_op(request: Request) -> Operation[None]:
    """Discard the body. Several writes answer 200 with an empty or non-JSON body."""
    return Operation(request, lambda _: None, expects_body=False)


def bytes_op(request: Request) -> Operation[bytes]:
    """Return the raw body, for downloads."""
    return Operation(request, lambda r: r.content)


def json_op(request: Request) -> Operation[object]:
    """Parse arbitrary JSON. Used by the ``icpc raw`` escape hatch only."""
    return Operation(request, lambda r: r.json() if r.content else None, expects_body=False)


def paths(*parts: str | int) -> str:
    """Join path segments, stringifying ids."""
    return "/" + "/".join(str(p).strip("/") for p in parts)


def query_params(items: Sequence[tuple[str, str | int | None]]) -> dict[str, str | int]:
    """Drop ``None`` values from a parameter list."""
    return {k: v for k, v in items if v is not None}
