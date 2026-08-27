"""``/contest/staffmember`` — contest staff.

A *staff member* is a person attached to a site with a badge and certificate
role. That is distinct from a *contest manager*, who has administrative
permissions on the contest; managers live in :mod:`icpc.api.contest`.
"""

from __future__ import annotations

from icpc.models._generated import StaffMemberRow
from icpc.transport.operation import Operation, Request, model_op, none_op

__all__ = ["add", "delete", "get", "update"]


def get(staff_member_id: int) -> Operation[StaffMemberRow]:
    """One staff member."""
    return model_op(Request("GET", f"/contest/staffmember/{staff_member_id}"), StaffMemberRow)


def add(
    site_id: int,
    person_id: int,
    *,
    badge_role: str,
    certificate_role: str,
    show_in_public_pages: bool = False,
) -> Operation[dict[str, object]]:
    """Attach a person to a site as staff.

    Both roles are free text — they are printed on the badge and the certificate,
    so they are whatever the contest wants to call the job. The web form refuses
    to submit without both, and this mirrors that by requiring them.

    Resolve ``person_id`` with :func:`icpc.api.person.suggest`.
    """
    return Operation(
        Request(
            "POST",
            f"/contest/staffmember/site/{site_id}",
            json={
                "smId": None,
                "personId": person_id,
                "badgeRole": badge_role,
                "certificateRole": certificate_role,
                "showInPublicPages": show_in_public_pages,
            },
            idempotent=False,
        ),
        lambda r: dict(r.json()) if r.content else {},
    )


def update(
    site_id: int,
    staff_member_id: int,
    person_id: int,
    *,
    badge_role: str,
    certificate_role: str,
    show_in_public_pages: bool = False,
) -> Operation[dict[str, object]]:
    """Change an existing staff member. Same body as :func:`add`, plus ``smId``."""
    return Operation(
        Request(
            "PUT",
            f"/contest/staffmember/site/{site_id}",
            json={
                "smId": staff_member_id,
                "personId": person_id,
                "badgeRole": badge_role,
                "certificateRole": certificate_role,
                "showInPublicPages": show_in_public_pages,
            },
            idempotent=False,
        ),
        lambda r: dict(r.json()) if r.content else {},
    )


def delete(staff_member_id: int) -> Operation[None]:
    """Remove a staff member."""
    return none_op(Request("DELETE", f"/contest/staffmember/{staff_member_id}", idempotent=False))
