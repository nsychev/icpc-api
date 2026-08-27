"""``/common``, ``/icpcprofile`` and the ``/aspectfaces`` schema registry."""

from __future__ import annotations

from icpc.models.base import Row
from icpc.models.entities import Globals, InstitutionSuggestion
from icpc.transport.operation import Operation, Request, list_op, model_op, scalar_op

__all__ = [
    "AspectFacesField",
    "AspectFacesSchema",
    "globals_",
    "institution_suggest",
    "schema",
    "wf_year",
]


def globals_() -> Operation[Globals]:
    """Site-wide settings: the current World Finals and regionals years."""
    return model_op(Request("GET", "/common/globals/all"), Globals)


def wf_year() -> Operation[int]:
    """The current World Finals year."""
    return scalar_op(Request("GET", "/common/globals/WFYear"), int)


def suggested_institution(institution_id: int) -> Operation[dict[str, object]]:
    """A suggested-institution record."""
    return model_op(
        Request("GET", f"/common/suggestedinstitution/{institution_id}"), dict[str, object]
    )


class AspectFacesField(Row):
    """One field of a server-side form definition."""

    name: str | None = None
    tag: str | None = None
    label: str | None = None
    label_key: str | None = None
    placeholder: str | None = None
    order: int | None = None
    #: Allowed values, when the field is a choice — the closest thing to an enum
    #: definition this API publishes.
    options: list[object] | None = None
    constraints: object | None = None
    tooltip: str | None = None


class AspectFacesSchema(Row):
    """``GET /aspectfaces/<java.class.Name>`` — a form definition."""

    name: str | None = None
    fields: list[AspectFacesField] | None = None
    obj: object | None = None


def schema(java_class: str, *associations: str) -> Operation[AspectFacesSchema]:
    """Fetch a server-side form definition.

    This is the only schema the API exposes. It is the authoritative source for
    enum option lists and required-field constraints, and therefore the right place
    to look before constructing a write payload::

        schema("global.icpc.base.model.team.businessobjects.Team", "teamInfo")
    """
    path = f"/aspectfaces/{java_class}"
    if associations:
        path += "->" + ",".join(associations)
    return model_op(Request("GET", path), AspectFacesSchema)


def countries() -> Operation[list[dict[str, object]]]:
    """The country list used by the registration forms."""
    return list_op(Request("GET", "/common/country/all"), dict[str, object])


def institution_suggest(
    name: str, *, page: int = 1, size: int = 10
) -> Operation[list[InstitutionSuggestion]]:
    """Look an institution up by name, as the UI's picker does.

    The ``id`` it returns is the ``institutionUnitId`` that
    :func:`icpc.api.team.register` expects. Take care: it is a different number
    from both the ``instId`` and the ``instUnitId`` columns of the institution
    search grid, which are ids in other tables entirely.
    """
    return list_op(
        Request(
            "GET",
            "/common/institutionunit/suggest",
            params={"name": name, "page": page, "size": size},
        ),
        InstitutionSuggestion,
    )
