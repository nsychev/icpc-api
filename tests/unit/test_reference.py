"""The invariants the API reference depends on.

``docs/reference.md`` catalogues every function in ``icpc.api.*`` whose return
type is ``Operation[T]``, together with the request it builds. Two things have
to hold for that catalogue to stay complete and trustworthy, and neither is
enforced by the type checker.
"""

from __future__ import annotations

import inspect
import typing

import pytest

from icpc.api import common, contest, person, public, staff, survey, team
from icpc.transport.operation import Operation

MODULES = [common, contest, person, public, staff, survey, team]


def _is_mapping(annotation: object) -> bool:
    """A dict payload: either `dict` itself or a TypedDict.

    `isinstance(SomeTypedDict, type)` is True, so `is_typeddict` is the check
    that actually distinguishes them.
    """
    if annotation is dict or typing.get_origin(annotation) is dict:
        return True
    return typing.is_typeddict(annotation)


def exported_functions(module):
    for name in getattr(module, "__all__", []):
        candidate = getattr(module, name, None)
        if inspect.isfunction(candidate):
            yield name, candidate


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__)
def test_every_exported_function_is_an_api_call(module):
    """Nothing in an api module is a helper.

    If a plain helper is ever exported from one of these modules it will be
    absent from the reference with no warning, so the modules stay pure: every
    exported function builds an Operation.
    """
    wrong = []
    for name, func in exported_functions(module):
        hints = typing.get_type_hints(func)
        if typing.get_origin(hints.get("return")) is not Operation:
            wrong.append(f"{name} -> {hints.get('return')}")
    assert not wrong, (
        f"{module.__name__} exports functions that are not API calls: {wrong}. "
        f"Move helpers out of __all__, or they will be missing from docs/reference.md."
    )


@pytest.mark.parametrize("module", MODULES, ids=lambda m: m.__name__)
def test_api_calls_build_a_request_without_io(module):
    """Calling an endpoint function must be pure and must not need the network.

    This is what lets the reference be generated, and what lets a test assert a
    request without a server.
    """
    for name, func in exported_functions(module):
        signature = inspect.signature(func)
        hints = typing.get_type_hints(func)
        args, kwargs = [], {}
        for param in signature.parameters.values():
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue
            annotation = hints.get(param.name)
            value: object = 1 if annotation is int else "x"
            if annotation is bool:
                value = False
            elif annotation is bytes:
                value = b""
            elif typing.get_origin(annotation) in (list, tuple):
                value = []
            elif _is_mapping(annotation):
                value = {}
            if param.kind is param.KEYWORD_ONLY:
                kwargs[param.name] = value
            else:
                args.append(value)
        operation = func(*args, **kwargs)
        assert operation.request.path.startswith("/"), f"{name} built {operation.request.path!r}"
        assert operation.request.method in ("GET", "POST", "PUT", "DELETE")


def test_writes_are_the_ones_that_are_not_idempotent():
    """The reference marks writes from `idempotent`; keep that meaningful."""
    reads = [team.get(1), team.members(1), contest.get(1), person.whoami()]
    writes = [team.replace(1, {}), team.promote(1, 2), team.remove_member(1)]
    assert all(op.request.idempotent for op in reads)
    assert not any(op.request.idempotent for op in writes)
