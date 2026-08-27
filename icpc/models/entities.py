"""DTOs for the non-search endpoints.

Some fields may be missing, they can be accessed through
:meth:`~icpc.models.base.Row.extra` instead.
"""

from __future__ import annotations

from pydantic import Field

from icpc.models.base import Row
from icpc.models.common import Country, NamedRef
from icpc.models.enums import (
    ContestType,
    EligibilityStatus,
    MemberRole,
    PublicPagesVisibility,
    Sex,
    ShirtSize,
    TeamStatus,
    Title,
)

__all__ = [
    "Breadcrumb",
    "ContactInfo",
    "Contest",
    "ContestManager",
    "ContestReference",
    "ContestSettings",
    "ContestStats",
    "ContestUnder",
    "Degree",
    "Eligibility",
    "Globals",
    "InstitutionSuggestion",
    "InstitutionUnitAssignment",
    "Person",
    "PersonBasic",
    "PersonInfo",
    "PersonName",
    "PersonSuggestion",
    "PublicContest",
    "RegionalRef",
    "RegistrationInfo",
    "RegistrationStatus",
    "SiteRow",
    "SiteTreeNode",
    "StandingRow",
    "Team",
    "TeamAction",
    "TeamFile",
    "TeamMember",
    "TeamViewRestrictions",
]


# ------------------------------------------------------------------ people --


class PersonBasic(Row):
    """``GET /person/info/basic`` — who the current token belongs to."""

    id: int
    user_name: str
    first_name: str
    last_name: str
    privacy_policy_accepted: bool | None = None


class PersonName(Row):
    """``GET /person/name/{id}``."""

    id: int
    username: str
    first_name: str
    last_name: str


class PersonInfo(Row):
    """The mutable half of a person record."""

    id: int
    version: int
    title: Title | str | None = Field(default=None, union_mode="left_to_right")
    first_name: str
    last_name: str
    local_name: str | None = None
    badge_name: str | None = None
    certificate_name: str | None = None
    sex: Sex | str | None = Field(default=None, union_mode="left_to_right")
    shirt_size: ShirtSize | str | None = Field(default=None, union_mode="left_to_right")
    date_of_birth: str | None = None
    home_town: str | None = None
    home_state: str | None = None
    home_country: Country | None = None
    residence_country: Country | None = None
    job_title: str | None = None
    company: str | None = None
    special_needs: str | None = None
    acm_id: str | None = None
    registration_issue: str | None = None


class Person(Row):
    """``GET /person/{id}``."""

    id: int
    version: int
    username: str
    person_info: PersonInfo | None = None
    privacy_policy_accepted: bool | None = None
    hide_mfa_message: bool | None = None


class ShippingAddress(Row):
    address_line1: str | None = None
    address_line2: str | None = None
    address_line3: str | None = None
    city: str | None = None
    state: str | None = None
    zip: str | None = None
    country: Country | None = None


class ContactInfo(Row):
    """``GET /person/contactinfo/person/{id}``."""

    id: int | None = None
    version: int | None = None
    voice: str | None = None
    mobile: str | None = None
    im_screen_name: str | None = None
    im_service: str | None = None
    airport_code: str | None = None
    emergency_contact: str | None = None
    emergency_phone: str | None = None
    passport_country: Country | None = None
    shipping_address: ShippingAddress | None = None


class Degree(Row):
    """``GET /person/degree/person/{id}``."""

    id: int | None = None
    version: int | None = None
    area_of_study: str | None = None
    degree_pursued: str | None = None
    expected_graduation: str | None = None
    began_degree: str | None = None
    num_stem_semesters_completed: int | None = None


class RegistrationStatus(Row):
    """``GET /person/registration/registrationStatus/{id}`` — what the UI may show."""

    show_contestant_info: bool | None = None
    show_passport_info: bool | None = None
    show_contact_info: bool | None = None
    show_address: bool | None = None
    has_appointment_letters: bool | None = None
    registration_complete: bool | None = None
    registration_issue: str | None = None
    enabled: bool | None = None


# ------------------------------------------------------------------- teams --


class InstitutionUnitAssignment(Row):
    """The institution a team competes for, as embedded in a team."""

    id: int
    name: str
    abbr: str | None = None
    url: str | None = None
    country: str | None = None


class Team(Row):
    """``GET /team/{id}``.

    This exact shape is what ``POST /team/{id}`` expects back — it is a full-object
    replace, not a patch.
    """

    id: int
    #: The server rejects a null name on a write: "Name - must not be null".
    name: str
    status: TeamStatus | str | None = Field(default=None, union_mode="left_to_right")
    role: str | None = None
    institution_unit_assignment: InstitutionUnitAssignment | None = None
    contest: NamedRef | None = None
    site: NamedRef | None = None
    extended_state: str | None = None
    billing_comment: str | None = None
    billing_info: str | None = None
    paid: bool | None = None
    swear_word: str | None = None
    require_cert: bool | None = None
    certified: bool | None = None
    registration_time: str | None = None
    current_year: bool | None = None
    wf: bool | None = None


class TeamAction(Row):
    """``GET /team/{id}/action``."""

    name: str
    extended_status: str | None = None
    paid: bool | None = None


class TeamViewRestrictions(Row):
    """``GET /team/{id}/viewrestrictions`` — what this account may do to the team.

    Worth checking before a write: it is the server's own answer, and cheaper than
    discovering the answer from a 403.
    """

    can_edit_team: bool | None = None
    can_delete_team: bool | None = None
    can_move_team: bool | None = None
    can_add_team_member: bool | None = None
    can_modify_team_members: bool | None = None
    can_change_attending_members: bool | None = None
    can_edit_team_certification: bool | None = None
    can_edit_certificate: bool | None = None
    can_edit_institution: bool | None = None
    can_see_report: bool | None = None
    can_see_similar_people: bool | None = None


class Eligibility(Row):
    """``GET /team/eligibility/team/{id}``.

    A full-object team write recomputes this and clears :attr:`verified`.
    """

    id: int | None = None
    status: EligibilityStatus | str | None = Field(default=None, union_mode="left_to_right")
    issue: str | None = None
    comment: str | None = None
    public_comment: str | None = None
    logs: str | None = None
    eligible: bool | None = None
    verified: bool | None = None
    modified_when: str | None = None
    can_edit: bool | None = None


class TeamMember(Row):
    """``GET /team/members/team/{id}``."""

    member_id: int
    person_id: int
    name: str
    email: str | None = None
    sex: Sex | str | None = Field(default=None, union_mode="left_to_right")
    role: MemberRole | str | None = Field(default=None, union_mode="left_to_right")
    registration_complete: bool | None = None
    on_team_certificate: bool | None = None
    on_individual_certificate: bool | None = None
    attending_onsite: bool | None = None
    badge_role: str | None = None
    certificate_role: str | None = None


class TeamFile(Row):
    """``GET /team/file/team/{id}`` — an attachment on a team."""

    id: int
    name: str
    created_when: str | None = None
    mime: str | None = None
    entered_by: str | None = None
    size: int | None = None
    size_human: str | None = None
    file_type: str | None = None


# ---------------------------------------------------------------- contests --


class ContestSettings(Row):
    """``GET /contest/settings/contest/{id}``, also embedded in :class:`Contest`."""

    id: int | None = None
    version: int | None = None
    read_only: bool | None = None
    show_teams_in_public_pages: bool | None = None
    #: Not a boolean, despite the name: "with" or "without" people.
    show_public_pages: PublicPagesVisibility | str | None = Field(
        default=None, union_mode="left_to_right"
    )
    require_certification: bool | None = None
    require_eligibility_validation: bool | None = None
    force_enrollment_letters_upload: bool | None = None
    publish_materials: bool | None = None
    publish_announcement: bool | None = None
    contest_type: ContestType | str | None = Field(default=None, union_mode="left_to_right")
    welcome_message: str | None = None
    require_proof_of_id: bool | None = None
    require_resume: bool | None = None
    allow_attending_members_changes: bool | None = None


class Contest(Row):
    """``GET /contest/{id}``.

    The live object nests a dozen further collections (sponsors, sites, surveys,
    notifications); the ones this SDK models are declared, the rest survive in
    ``model_extra``.
    """

    id: int
    version: int | None = None
    #: The server rejects a null name on a write: "Name - must not be null".
    name: str
    abbreviation: str | None = None
    short_name: str | None = None
    year: int | None = None
    icpc_year: int | None = None
    email: str | None = None
    hosts: str | None = None
    geographic_area: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    archival_date: str | None = None
    announcement: str | None = None
    root_contest: bool | None = None
    contest_settings: ContestSettings | None = None


class ContestStats(Row):
    """``GET /contest/info/contest/{id}/stats``."""

    num_subcontests: int | None = None
    num_sites: int | None = None
    num_contest_managers: int | None = None
    num_pending_teams: int | None = None
    num_accepted_teams: int | None = None


class RegistrationInfo(Row):
    """``GET /contest/registrationinfo/contest/{id}``."""

    id: int | None = None
    version: int | None = None
    allow_reserve: bool | None = None
    allow_student_coach: bool | None = None
    require_contact_info: bool | None = None
    require_address: bool | None = None
    lite_registration: bool | None = None
    require_passport_info: bool | None = None
    registration_to_other_contests_limit: int | None = None
    reg_start_date: str | None = None
    reg_end_date: str | None = None
    actual_reg_end_date: str | None = None
    advanced_reg_end_date: str | None = None
    time_zone: str | None = None


class ContestManager(Row):
    """``GET /contest/access/contest/{id}/managers``."""

    person: PersonName | None = None
    contest_read: bool | None = None
    contest_update: bool | None = None
    contest_grant_permissions: bool | None = None
    contest_contact: bool | None = None
    export: bool | None = None
    standings_upload: bool | None = None
    team_attachment_upload: bool | None = None
    subcontest_create: bool | None = None


class Breadcrumb(Row):
    """``GET /contest/{id}/breadcrumbs`` — the contest's place in the hierarchy."""

    id: int
    name: str
    type: str | None = None
    sub_breadcrumbs: list[Breadcrumb] | None = None


class SiteRow(Row):
    """``GET /contest/site/contest/{id}/table`` — a site with its capacity."""

    id: int | None = None
    name: str | None = None
    site_type: str | None = None
    spots_taken: int | None = None
    capacity: int | None = None
    allow_registration: bool | None = None
    invitation_only: bool | None = None
    allow_team_changes: bool | None = None
    enforce_capacity: bool | None = None


class SiteTreeNode(Row):
    """``GET /contest/site/tree/...`` — the contest tree, recursively."""

    id: int | None = None
    label: str | None = None
    active: bool | None = None
    super_contest_id: int | None = None
    type: str | None = None
    additional_info: str | None = None
    leaf: bool | None = None
    descendants: list[SiteTreeNode] | None = None


class Globals(Row):
    """``GET /common/globals/all`` — the site-wide year settings."""

    world_finals_year: int | None = None
    regionals_year: int | None = None
    world_finals_contest_id: int | None = None
    video_status: str | None = None
    video_name: str | None = None
    max_monthly_snapshots: int | None = None


# ------------------------------------------------------------------ public --


class RegionalRef(Row):
    """An entry of ``GET /contest/public/regionals/{year}``."""

    id: int | None = None
    label: str | None = None


class ContestUnder(Row):
    """An entry of ``GET /contest/public/contests-under/{id}``."""

    id: int | None = None
    abbreviation: str | None = None
    contest: str | None = None
    date: str | None = None
    capacity: int | None = None
    registered: int | None = None
    reg_active: bool | None = None


class PublicContest(Row):
    """``GET /contest/public/{abbreviation}``.

    Keyed by the contest's *abbreviation*, not its id — and the abbreviation is
    sometimes year-suffixed, e.g. ``NERC-2026``.
    """

    id: int | None = None
    name: str | None = None
    shortname: str | None = None
    contest_type: ContestType | str | None = Field(default=None, union_mode="left_to_right")
    start_date: str | None = None
    end_date: str | None = None
    reg_end_date: str | None = None
    homepage: str | None = None
    email: str | None = None
    hosts: str | None = None
    sponsors: str | None = None
    sites: list[NamedRef] | None = None
    active_sites: list[NamedRef] | None = None


class StandingRow(Row):
    """A row of ``GET /contest/public/search/contest/{id}`` — actual results."""

    rank: int | None = None
    institution: str | None = None
    team_name: str | None = None
    problems_solved: int | None = None
    total_time: int | None = None
    last_problem_time: int | None = None
    medal_citation: str | None = None


class PersonSuggestion(Row):
    """A row of ``GET /person/suggest`` — what the UI's person picker shows."""

    id: int | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    @property
    def full_name(self) -> str:
        return " ".join(p for p in (self.first_name, self.last_name) if p)


class InstitutionSuggestion(Row):
    """A row of ``GET /common/institutionunit/suggest``.

    :attr:`id` is the ``institutionUnitId`` that team registration wants — which
    is *not* the ``instId`` or ``instUnitId`` the institution search grid returns.
    """

    id: int | None = None
    name: str | None = None
    abbr: str | None = None
    url: str | None = None
    country: str | None = None


class ContestReference(Row):
    """A row of ``GET /person/references/{personId}/{icpcYear}/{role}/search``.

    One contest a person is attached to in some role. The ``teammember`` role
    fills in the team and site fields as well; the others leave them null.
    """

    contest_id: int | None = None
    contest: str | None = None
    site_id: int | None = None
    site: str | None = None
    team_id: int | None = None
    team: str | None = None
    team_role: MemberRole | str | None = Field(default=None, union_mode="left_to_right")
