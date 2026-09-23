"""``/common``, ``/icpcprofile`` and the ``/aspectfaces`` schema registry."""

from __future__ import annotations

import mimetypes

from icpc.models.base import Row
from icpc.models.entities import (
    Globals,
    Institution,
    InstitutionSuggestion,
    InstitutionUnit,
    SuggestedInstitution,
)
from icpc.transport.operation import Operation, Request, list_op, model_op, none_op, scalar_op

__all__ = [
    "AspectFacesField",
    "AspectFacesSchema",
    "approve_suggested_institution",
    "create_suggested_institution",
    "globals_",
    "institution",
    "institution_suggest",
    "institution_unit",
    "institution_units",
    "schema",
    "set_institution_logo",
    "update_institution",
    "update_institution_unit",
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


def institution(institution_id: int) -> Operation[Institution]:
    """An institution, by the ``instId`` of the institution search grids."""
    return model_op(Request("GET", f"/common/institution/{institution_id}"), Institution)


def institution_units(institution_id: int) -> Operation[list[InstitutionUnit]]:
    """The units of an institution; usually exactly one."""
    return list_op(
        Request("GET", f"/common/institutionunit/inst/{institution_id}"), InstitutionUnit
    )


def institution_unit(unit_id: int) -> Operation[InstitutionUnit]:
    """An institution unit, by the ``instUnitId`` of the institution search grids."""
    return model_op(Request("GET", f"/common/institutionunit/{unit_id}"), InstitutionUnit)


def update_institution(institution: dict[str, object]) -> Operation[Institution]:
    """Overwrite an institution's names and homepage.

    A full-object replace keyed by ``id`` and ``version``: read with
    :func:`institution`, change what you want, send it all back.
    """
    return model_op(
        Request("POST", "/common/institution", json=institution, idempotent=False), Institution
    )


def update_institution_unit(unit: dict[str, object]) -> Operation[InstitutionUnit]:
    """Overwrite an institution unit, address and social links included.

    A full-object replace, like :func:`update_institution`. The unit repeats the
    institution's names; the two are not kept in sync by the server.
    """
    return model_op(
        Request("POST", "/common/institutionunit", json=unit, idempotent=False), InstitutionUnit
    )


def create_suggested_institution(
    institution: dict[str, object],
) -> Operation[SuggestedInstitution]:
    """Suggest a new institution, as the "can't find my institution" form does.

    Required: ``name`` (7+ characters), ``shortName``, ``homepageUrl`` and
    ``institutionUnitType``. ``mailingAddress.country`` is a whole country object;
    take it from :func:`icpc.models.countries.country`.
    """
    return model_op(
        Request("POST", "/common/suggestedinstitution/", json=institution, idempotent=False),
        SuggestedInstitution,
    )


def approve_suggested_institution(suggestion_id: int) -> Operation[None]:
    """Turn a suggestion from :func:`create_suggested_institution` into an institution."""
    return none_op(
        Request("PUT", f"/common/suggestedinstitution/approve/{suggestion_id}", idempotent=False)
    )


#: What the logo form accepts; the server enforces the same limits.
LOGO_TYPES = frozenset({"image/svg+xml", "image/jpeg", "image/bmp", "image/png", "image/gif"})
LOGO_MAX_BYTES = 3_000_000


def logo_mime(filename: str, size: int) -> str:
    """The content type for a logo upload, or ``ValueError`` if the form would refuse it."""
    mime, _ = mimetypes.guess_type(filename)
    if mime not in LOGO_TYPES:
        raise ValueError(f"{filename}: a logo must be SVG, JPEG, BMP, PNG or GIF")
    if size > LOGO_MAX_BYTES:
        raise ValueError(f"{filename}: {size} bytes; a logo must be under 3000 kB")
    return mime


def set_institution_logo(
    institution_id: int, filename: str, content: bytes, mime: str
) -> Operation[None]:
    """Upload an institution's logo, replacing any current one.

    Keyed by ``instId``. SVG, JPEG, BMP, PNG or GIF, at most 3000 kB;
    :func:`logo_mime` checks both and picks ``mime``.
    """
    return none_op(
        Request(
            "POST",
            f"/common/logo/institution/{institution_id}",
            files={"file": (filename, content, mime)},
            idempotent=False,
        )
    )
