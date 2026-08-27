"""``/team`` endpoints."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypedDict

from icpc.models.entities import (
    Eligibility,
    Team,
    TeamAction,
    TeamFile,
    TeamMember,
    TeamViewRestrictions,
)
from icpc.models.enums import TeamStatus
from icpc.transport.operation import (
    Operation,
    Request,
    list_op,
    model_op,
    none_op,
    scalar_op,
)

__all__ = [
    "action",
    "add_members",
    "bulk_update_status",
    "delete_file",
    "eligibility",
    "files",
    "get",
    "members",
    "other_sites",
    "promote",
    "register",
    "register_with_coach",
    "remove_member",
    "replace",
    "set_coach",
    "site_registrable",
    "update_member",
    "upload_file",
    "view_restrictions",
]


# -------------------------------------------------------------------- read --


def get(team_id: int) -> Operation[Team]:
    """A team, in the exact shape :func:`replace` expects back."""
    return model_op(Request("GET", f"/team/{team_id}"), Team)


def action(team_id: int) -> Operation[TeamAction]:
    """Name, extended status and payment state — what the team page header shows."""
    return model_op(Request("GET", f"/team/{team_id}/action"), TeamAction)


def members(team_id: int) -> Operation[list[TeamMember]]:
    """The team's roster, with per-member certificate and attendance flags."""
    return list_op(Request("GET", f"/team/members/team/{team_id}"), TeamMember)


def files(team_id: int) -> Operation[list[TeamFile]]:
    """Attachments on a team (enrollment letters, proofs of id, and so on)."""
    return list_op(Request("GET", f"/team/file/team/{team_id}"), TeamFile)


def eligibility(team_id: int) -> Operation[Eligibility]:
    """The team's eligibility verdict and its verification state."""
    return model_op(Request("GET", f"/team/eligibility/team/{team_id}"), Eligibility)


def view_restrictions(team_id: int) -> Operation[TeamViewRestrictions]:
    """What the current account is allowed to do to this team."""
    return model_op(Request("GET", f"/team/{team_id}/viewrestrictions"), TeamViewRestrictions)


def other_sites(team_id: int) -> Operation[list[dict[str, object]]]:
    """Sites this team could move to."""
    return list_op(Request("GET", f"/team/{team_id}/othersites"), dict[str, object])


# ------------------------------------------------------------------ writes --


def replace(team_id: int, team: dict[str, object]) -> Operation[None]:
    """Overwrite a team with ``team``.

    **Destructive.** This is a full-object replace, not a partial update: the server
    recomputes the team's eligibility and clears any verified statuses, exactly as
    the web UI warns before saving. Send back a complete object obtained from
    :func:`get` with only the intended fields changed — the facade's
    ``update_team`` does that read-modify-write for you.
    """
    return none_op(
        Request(
            "POST",
            f"/team/{team_id}",
            json=team,
            idempotent=False,
        )
    )


def bulk_update_status(
    contest_id: int, team_ids: Sequence[int], new_status: TeamStatus | str
) -> Operation[None]:
    """Accept, reject or reset many teams of one contest at once."""
    return none_op(
        Request(
            "PUT",
            f"/team/bulkupdate/contest/{contest_id}",
            json={"newStatus": str(new_status), "teamIds": list(team_ids)},
            idempotent=False,
        )
    )


def promote(team_id: int, site_id: int) -> Operation[None]:
    """Promote a team to a site of the parent contest.

    Refusals come back two ways. A team that is already promoted answers HTTP
    500 with a body saying so, which the transport turns into
    :class:`~icpc.errors.TeamNotPromotable` rather than a generic server error;
    a conflict with the target site answers a plain 400, "The team cannot be
    promoted, please check the target site for conflicts".
    """
    return none_op(
        Request(
            "POST",
            f"/team/{team_id}/promote/{site_id}",
            idempotent=False,
        )
    )


def upload_file(
    team_id: int, filename: str, content: bytes, mime: str = "application/pdf"
) -> Operation[None]:
    """Attach a file to a team.

    The server renames the upload, inserting a long random number before the
    extension — ``INVITATION-.pdf`` comes back as
    ``INVITATION-9776387880749677008.pdf`` — so match on prefix and suffix when
    looking it up again.
    """
    return none_op(
        Request(
            "POST",
            f"/team/file/{team_id}",
            files={"file": (filename, content, mime)},
            idempotent=False,
        )
    )


def delete_file(file_id: int) -> Operation[None]:
    """Remove one attachment, by *file* id — not team id."""
    return none_op(
        Request(
            "DELETE",
            f"/team/file/{file_id}",
            idempotent=False,
        )
    )


class NewTeamMember(TypedDict, total=False):
    """One member of a team being registered."""

    #: ``CONTESTANT``, ``COACH``, ``COCOACH`` or ``CONTESTANT_COACH``.
    role: str
    #: A *person id* — a bare number, not an object. Resolve one with
    #: :func:`icpc.api.person.suggest`.
    person: int
    badgeRole: str | None
    certificateRole: str | None


class NewTeam(TypedDict, total=False):
    """One team to register."""

    name: str
    siteId: int
    #: From :func:`icpc.api.common.institution_suggest` — *not* the ``instId`` or
    #: ``instUnitId`` of the institution search grid.
    institutionUnitId: int
    studentCoach: bool
    teamMembers: list[NewTeamMember]


def register(teams: Sequence[NewTeam]) -> Operation[dict[str, str]]:
    """Register one or more teams, returning ``{new team id: name}``.

    This is ``/team/register/bulk``, which is what the registration wizard
    actually calls; the singular ``/team/register`` is defined in the frontend
    bundle but never used by it, and rejects everything this sends.

    Two things the server does that are not obvious:

    * **The registering account is added as a coach automatically.** Listing
      yourself again gives "Person … is twice in team", and listing another coach
      as well can exceed the contest's coach limit.
    * The whole batch is validated before anything is written, so a rejected
      batch leaves no partial team behind.

    The UI registers at most ten teams at a time and checks
    ``GET /team/site/{siteId}/registrable`` first.
    """
    return Operation(
        Request("POST", "/team/register/bulk", json=list(teams), idempotent=False),
        lambda r: dict(r.json()) if r.content else {},
    )


def site_registrable(site_id: int) -> Operation[bool]:
    """Whether a site is currently open for team registration."""
    return scalar_op(Request("GET", f"/team/site/{site_id}/registrable"), bool)


class NewMember(TypedDict, total=False):
    """A member being added to an existing team.

    Note this is not shaped like :class:`NewTeamMember`: here ``person`` is an
    object and the role field is ``role`` (the ``TeamMemberRegistrationDto``),
    whereas bulk registration wants a bare person id.
    """

    person: dict[str, int]
    #: ``CONTESTANT``, ``COACH``, ``COCOACH``, ``CONTESTANT_COACH``,
    #: ``ATTENDEE``, ``RESERVE`` or ``STAFF``.
    role: str
    badgeRole: str
    certificateRole: str


def register_with_coach(team: NewTeam, coach_id: int | None = None) -> Operation[int]:
    """Register a single team **without** making yourself its coach.

    ``/team/register/bulk`` always adds the registering account as a coach, so
    with the usual limit of one coach per team there is no room for anybody
    else. This endpoint does not, which is what it is for.

    It takes a single object, not an array, and returns the new team id as a
    bare number. ``coach_id`` is accepted for symmetry but the server ignores
    it: the team is created with no coach at all, and :func:`set_coach` is how
    you attach one.
    """
    body = dict(team)
    if coach_id is not None:
        body["coachId"] = coach_id  # type: ignore[typeddict-unknown-key]
    return scalar_op(
        Request("POST", "/team/register/customcoach", json=body, idempotent=False), int
    )


def set_coach(
    team_id: int,
    person_id: int,
    *,
    role: str = "COACH",
    badge_role: str | None = None,
    certificate_role: str | None = None,
) -> Operation[TeamMember]:
    """Make someone the team's coach, or its ``CONTESTANT_COACH``.

    This endpoint is not the same as :func:`add_members` with a coaching role,
    and the difference matters:

    * **It fills the coach slot rather than adding to it.** An incumbent
      ``CONTESTANT_COACH`` is demoted to ``CONTESTANT`` in place — same member
      id, and ``registrationComplete``, attendance and the certificate flags
      all survive, unlike the remove-and-re-add that a role change otherwise
      costs.
    * **It ignores ``maxCoaches``.** The same swap through ``/add`` answers
      "2 coaches exceeds the coach limit of 1"; this path just goes through.

    The person must not already be on the team ("Person … is twice in team"),
    and a person who is already a *contestant* in the same contest cannot be a
    coach there ("Person … can't be coach").

    ``role`` may be ``CONTESTANT_COACH``, which the server accepts here and
    which is the cheapest way to install one. It then validates the contestant
    half too, so the person must not be a contestant on another team in the
    contest ("Contestant … can participate only in one team").

    ``badge_role`` and ``certificate_role`` default to ``role`` in title case —
    "Coach", "Contestant Coach".
    """
    label = badge_role or role.replace("_", " ").title()
    return model_op(
        Request(
            "POST",
            f"/team/members/team/{team_id}/coach",
            json={
                "person": {"id": person_id},
                "role": role,
                "badgeRole": label,
                "certificateRole": certificate_role or label,
            },
            idempotent=False,
        ),
        TeamMember,
    )


def add_members(team_id: int, members: Sequence[NewMember]) -> Operation[list[TeamMember]]:
    """Add people to an existing team. The body is an array, even for one member."""
    return list_op(
        Request("POST", f"/team/members/team/{team_id}/add", json=list(members), idempotent=False),
        TeamMember,
    )


def remove_member(member_id: int) -> Operation[None]:
    """Remove a member, by *member* id — not person id."""
    return none_op(Request("DELETE", f"/team/members/{member_id}", idempotent=False))


def update_member(member_id: int, member: dict[str, object]) -> Operation[TeamMember]:
    """Overwrite a member with ``member``, a full object from :func:`members`.

    A full-object replace, like the team write. The web UI uses this only for
    ``attendingOnsite`` and the two certificate flags; changing ``role`` through
    it answers 500, so change a role by removing the member and adding them back
    with :func:`remove_member` and :func:`add_members`.
    """
    return model_op(
        Request("POST", f"/team/members/{member_id}", json=member, idempotent=False),
        TeamMember,
    )
