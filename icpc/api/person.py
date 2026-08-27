"""``/person`` endpoints."""

from __future__ import annotations

from enum import StrEnum

from icpc.models.entities import (
    ContactInfo,
    ContestReference,
    Degree,
    Person,
    PersonBasic,
    PersonInfo,
    PersonName,
    PersonSuggestion,
    RegistrationStatus,
)
from icpc.transport.operation import Operation, Request, list_op, model_op, scalar_op

__all__ = [
    "ReferenceRole",
    "available",
    "contact_info",
    "degree",
    "get",
    "info",
    "name",
    "references",
    "registration_status",
    "suggest",
    "whoami",
]

#: The UI's person picker waits for this many characters before querying.
SUGGEST_MIN_LENGTH = 3


def whoami() -> Operation[PersonBasic]:
    """The account behind the current token. The cheapest way to check auth works."""
    return model_op(Request("GET", "/person/info/basic"), PersonBasic)


def get(person_id: int) -> Operation[Person]:
    """A full person record, including the nested personal information."""
    return model_op(Request("GET", f"/person/{person_id}"), Person)


def info(person_id: int) -> Operation[PersonInfo]:
    """The latest personal-information snapshot for a person."""
    return model_op(Request("GET", f"/person/info/person/{person_id}/latest"), PersonInfo)


def name(person_id: int) -> Operation[PersonName]:
    """Just the names — cheaper than :func:`get` when resolving an id."""
    return model_op(Request("GET", f"/person/name/{person_id}"), PersonName)


def contact_info(person_id: int) -> Operation[ContactInfo]:
    """Phone, emergency contact and shipping address."""
    return model_op(Request("GET", f"/person/contactinfo/person/{person_id}"), ContactInfo)


def degree(person_id: int) -> Operation[Degree]:
    """Area of study, degree pursued, and graduation dates."""
    return model_op(Request("GET", f"/person/degree/person/{person_id}"), Degree)


def registration_status(person_id: int) -> Operation[RegistrationStatus]:
    """Whether this person's registration is complete, and what the UI shows them."""
    return model_op(
        Request("GET", f"/person/registration/registrationStatus/{person_id}"),
        RegistrationStatus,
    )


def available(username: str) -> Operation[bool]:
    """Whether a username is free."""
    return scalar_op(Request("GET", f"/person/available/{username}"), bool)


def is_owner(person_id: int) -> Operation[bool]:
    """Whether the current account owns this person record."""
    return scalar_op(Request("GET", f"/person/isowner/{person_id}"), bool)


def suggest(name: str, *, page: int = 1, size: int = 10) -> Operation[list[PersonSuggestion]]:
    """Look a person up by name or email, as the UI's picker does.

    This is how you turn "Nikita Sychev" or an email address into the person id
    that team registration and staff creation need. The UI waits for three
    characters before querying; shorter terms are accepted but match very widely.

    ``page`` is 1-based, as everywhere else in this API.
    """
    return list_op(
        Request("GET", "/person/suggest", params={"name": name, "page": page, "size": size}),
        PersonSuggestion,
    )


class ReferenceRole(StrEnum):
    """Roles a person can hold in a contest, as ``/person/references`` spells them."""

    #: Administrative access — what the cabinet's front page lists.
    CONTEST_MANAGER = "contestmanager"
    SITE_MANAGER = "sitemanager"
    STAFF_MEMBER = "staffmember"
    #: Fills in the team and site fields as well.
    TEAM_MEMBER = "teammember"
    SPONSOR = "sponsor"
    MASTER = "master"
    SLAVE = "slave"


def references(
    person_id: int,
    icpc_year: int,
    role: ReferenceRole | str = ReferenceRole.CONTEST_MANAGER,
    *,
    page: int = 1,
    size: int = 200,
) -> Operation[list[ContestReference]]:
    """Contests a person is attached to in ``role``, for one ICPC season.

    ``icpc_year`` is the **ICPC year**, not the calendar year: NERC-2026 runs in
    calendar 2026 but has ``icpcYear`` 2027, so it is listed under 2027. It is
    the same number the cabinet's year picker shows.

    ``contestmanager`` is the administrative access the front page lists.
    ``teammember`` additionally fills in the team and site fields.
    """
    return list_op(
        Request(
            "GET",
            f"/person/references/{person_id}/{icpc_year}/{role}/search",
            params={"q": "proj:;", "page": page, "size": size},
        ),
        ContestReference,
    )
