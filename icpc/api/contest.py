"""``/contest`` endpoints (the authenticated ones)."""

from __future__ import annotations

from icpc.models.common import NamedRef
from icpc.models.entities import (
    Breadcrumb,
    Contest,
    ContestManager,
    ContestSettings,
    ContestStats,
    RegistrationInfo,
    SiteRow,
    SiteTreeNode,
)
from icpc.transport.operation import (
    Operation,
    Request,
    list_op,
    model_op,
    none_op,
    scalar_op,
)

__all__ = [
    "add_manager",
    "breadcrumbs",
    "create_site",
    "create_subcontest",
    "delete",
    "delete_site",
    "get",
    "managers",
    "next_contest",
    "previous_contest",
    "registration_info",
    "settings",
    "site",
    "site_settings",
    "site_table",
    "site_tree",
    "sites",
    "stats",
    "update",
    "update_registration_info",
    "update_settings",
    "update_site_settings",
]


def get(contest_id: int) -> Operation[Contest]:
    """A contest and its settings."""
    return model_op(Request("GET", f"/contest/{contest_id}"), Contest)


def settings(contest_id: int) -> Operation[ContestSettings]:
    """Just the settings block."""
    return model_op(Request("GET", f"/contest/settings/contest/{contest_id}"), ContestSettings)


def sites(contest_id: int) -> Operation[list[NamedRef]]:
    """The contest's sites, id and name only."""
    return list_op(Request("GET", f"/contest/{contest_id}/sites"), NamedRef)


def site_table(contest_id: int) -> Operation[list[SiteRow]]:
    """Sites with capacity and registration flags — the site administration grid."""
    return list_op(Request("GET", f"/contest/site/contest/{contest_id}/table"), SiteRow)


def site_tree(contest_id: int) -> Operation[list[SiteTreeNode]]:
    """The subtree of contests below this one."""
    return list_op(Request("GET", f"/contest/site/tree/{contest_id}"), SiteTreeNode)


def root_tree(*, eager: bool = False) -> Operation[list[SiteTreeNode]]:
    """The top of the contest tree. ``eager`` expands every descendant in one call."""
    path = "/contest/site/tree/root/eager" if eager else "/contest/site/tree/root"
    return list_op(Request("GET", path), SiteTreeNode)


def breadcrumbs(contest_id: int) -> Operation[list[Breadcrumb]]:
    """Where this contest sits in the hierarchy, upwards."""
    return list_op(Request("GET", f"/contest/{contest_id}/breadcrumbs"), Breadcrumb)


def stats(contest_id: int) -> Operation[ContestStats]:
    """Counts of sites, managers, and pending versus accepted teams."""
    return model_op(Request("GET", f"/contest/info/contest/{contest_id}/stats"), ContestStats)


def registration_info(contest_id: int) -> Operation[RegistrationInfo]:
    """Registration windows and which sections registrants must fill in."""
    return model_op(
        Request("GET", f"/contest/registrationinfo/contest/{contest_id}"), RegistrationInfo
    )


def managers(contest_id: int) -> Operation[list[ContestManager]]:
    """Who can administer this contest, and with which permissions."""
    return list_op(Request("GET", f"/contest/access/contest/{contest_id}/managers"), ContestManager)


def has_access(contest_id: int) -> Operation[bool]:
    """Whether the current account may administer this contest."""
    return scalar_op(Request("GET", f"/contest/access/contest/{contest_id}"), bool)


def next_contest(contest_id: int) -> Operation[int]:
    """Id of the next contest in the same series."""
    return scalar_op(Request("GET", f"/contest/info/contest/{contest_id}/next"), int)


def previous_contest(contest_id: int) -> Operation[int]:
    """Id of the previous contest in the same series."""
    return scalar_op(Request("GET", f"/contest/info/contest/{contest_id}/previous"), int)


# ------------------------------------------------------------------ writes --


def create_subcontest(parent_id: int, contest: dict[str, object]) -> Operation[Contest]:
    """Create a contest beneath ``parent_id``.

    There is no endpoint for creating a *top-level* contest; every contest is
    either a child of another or the product of a rollover.

    ``contest`` is a Contest object. ``name``, ``shortName`` and ``email`` are
    required; ``abbreviation`` must match ``^[a-zA-Z-]*$`` and be 3 to 42 characters.
    ``GET /aspectfaces/global.icpc.base.model.contest.businessobjects.Contest``
    is the authoritative field list — ``icpc schema`` prints it.

    The child inherits ``year`` and ``icpcYear`` from its parent, and is created
    with an "Administrative Site" already attached.
    """
    return model_op(
        Request("POST", f"/contest/{parent_id}/subcontest/create", json=contest, idempotent=False),
        Contest,
    )


def delete(contest_id: int) -> Operation[None]:
    """Delete a contest. Used by the UI for subcontests and camps."""
    return none_op(Request("DELETE", f"/contest/{contest_id}", idempotent=False))


def create_site(contest_id: int, site: dict[str, object]) -> Operation[dict[str, object]]:
    """Add a site to a contest. ``name`` (3 to 128 characters) and ``email`` are required.

    New sites start closed: ``allowRegistration`` is false, so
    :func:`icpc.api.team.site_registrable` reports false until it is opened.
    """
    return Operation(
        Request("POST", f"/contest/site/create/{contest_id}", json=site, idempotent=False),
        lambda r: dict(r.json()) if r.content else {},
    )


def delete_site(site_id: int) -> Operation[None]:
    """Remove a site."""
    return none_op(Request("DELETE", f"/contest/site/{site_id}", idempotent=False))


def add_manager(contest_id: int, person_id: int, *, recursive: bool = False) -> Operation[str]:
    """Grant a person administrative access to a contest.

    ``recursive`` extends the grant to every contest beneath this one. Requires
    the ``contestGrantPermissions`` right on the contest.
    """
    return Operation(
        Request(
            "POST",
            f"/contest/access/contest/{contest_id}/manager",
            json={"recursive": recursive, "person": {"id": person_id}},
            idempotent=False,
        ),
        lambda r: r.text,
    )


def update(contest_id: int, contest: dict[str, object]) -> Operation[Contest]:
    """Overwrite a contest's own fields — name, dates, hosts, email.

    A full-object replace: read with :func:`get`, change what you want, send it
    all back. The web UI keeps ``abbreviation``, ``archivalDate`` and
    ``lastRevalidationAt`` read-only even though the endpoint accepts them.
    """
    return model_op(
        Request("POST", f"/contest/{contest_id}", json=contest, idempotent=False), Contest
    )


def update_settings(contest_id: int, settings: dict[str, object]) -> Operation[ContestSettings]:
    """Overwrite the contest settings block — certification, public pages, type."""
    return model_op(
        Request("POST", f"/contest/settings/contest/{contest_id}", json=settings, idempotent=False),
        ContestSettings,
    )


def update_registration_info(
    contest_id: int, info: dict[str, object]
) -> Operation[RegistrationInfo]:
    """Overwrite the registration rules — team sizes, windows, what registrants must give.

    ``allowStudentCoach`` lives here, and must be true before a team can be
    registered with a contestant coach.
    """
    return model_op(
        Request(
            "POST",
            f"/contest/registrationinfo/contest/{contest_id}",
            json=info,
            idempotent=False,
        ),
        RegistrationInfo,
    )


def site_settings(site_id: int) -> Operation[dict[str, object]]:
    """The settings of one site, as embedded in :func:`site`."""
    return Operation(
        Request("GET", f"/contest/site/{site_id}"),
        lambda r: dict(r.json().get("siteSettings") or {}),
    )


def site(site_id: int) -> Operation[dict[str, object]]:
    """One site, with its settings nested under ``siteSettings``."""
    return Operation(Request("GET", f"/contest/site/{site_id}"), lambda r: dict(r.json()))


def update_site_settings(
    contest_id: int, settings: dict[str, object]
) -> Operation[dict[str, object]]:
    """Overwrite a site's settings — capacity, and whether it is open.

    Note the path is keyed by *contest*, while the settings object identifies the
    site; read one with :func:`site_settings`.

    ``allowRegistration`` and ``allowTeamChanges`` are worth knowing about: while
    ``allowTeamChanges`` is false, adding or removing a team member answers
    **500**, not a clean refusal.
    """
    return Operation(
        Request(
            "POST",
            f"/contest/site/sitesettings/contest/{contest_id}",
            json=settings,
            idempotent=False,
        ),
        lambda r: dict(r.json()) if r.content else {},
    )
