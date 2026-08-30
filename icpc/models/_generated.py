"""Generated from icpc.global SPA bundle.

Field *names* come from each search endpoint itself. The API publishes no schema
for their *types*, so a field this module does not type explicitly is ``str``,
which is right for most columns but is a default rather than a verified fact.

Every field is optional: ``proj:`` does not shape the response, so anything not
projected arrives as ``null``.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import Field as _Field

from icpc.models.base import Row
from icpc.models.enums import (
    Consent,
    EligibilityStatus,
    InstitutionUnitType,
    MemberRole,
    Sex,
    ShirtSize,
    TeamStatus,
    Title,
)
from icpc.models.mixins import HasExtraFields, HasTeamMembers

__all__ = [
    "CertificateRow",
    "ContestParticipantRow",
    "InstitutionRow",
    "PromoteRow",
    "StaffFundingRow",
    "StaffMemberRow",
    "StaffRow",
    "StaffTshirtRow",
    "StandingsRow",
    "TeamMemberRow",
    "TeamRow",
    "TeamSummaryRow",
    "Top20Row",
    "TransportationMissingRow",
    "TshirtRow",
]


class CertificateRow(HasTeamMembers, Row):
    """Team certificates issued for a contest.

    Returned by:
    * ``/contest/certificate/team/contest/{contest_id}/search``
    * ``/contest/certificate/staff/contest/{contest_id}/search``
    * ``/contest/certificate/site/team/site/{site_id}/search``
    """

    id: int | None = _Field(default=None, description="ID")
    email: str | None = _Field(default=None, description="Email")
    user_id: int | None = None
    name: str | None = _Field(default=None, description="Name")
    certificate_name: str | None = None
    site_name: str | None = _Field(default=None, description="Site Name")
    site_id: int | None = None
    contest_name: str | None = _Field(default=None, description="Contest Name")
    contest_id: int | None = None
    role: str | None = _Field(default=None, description="Role")
    institution_name: str | None = _Field(default=None, description="Institution Name")
    inst_id: int | None = None
    institution_short_name: str | None = _Field(default=None, description="Institution Short Name")
    team_name: str | None = _Field(default=None, description="Team Name")
    team_id: int | None = None
    team_members: str | None = None
    lite_team_member_set: list | None = None


class ContestParticipantRow(Row):
    """Every person at a contest, with travel and visa detail. The widest DTO here.

    Returned by:
    * ``/contest/search/contest/{contest_id}/contestparticipant``
    * ``/contest/search/site/{site_id}/contestparticipant``
    """

    person_id: int | None = None
    username: str | None = _Field(default=None, description="Username")
    local_name: str | None = _Field(default=None, description="Local Name")
    badge_name: str | None = _Field(default=None, description="Badge Name")
    secondary_email: str | None = _Field(default=None, description="Secondary Email")
    first_name: str | None = _Field(default=None, description="First Name")
    last_name: str | None = _Field(default=None, description="Last Name")
    title: Title | str | None = _Field(
        default=None, union_mode="left_to_right", description="Title"
    )
    sex: Sex | str | None = _Field(default=None, union_mode="left_to_right", description="Sex")
    dob: date | str | None = _Field(
        default=None, union_mode="left_to_right", description="Date of Birth"
    )
    phone: str | None = _Field(default=None, description="Phone")
    emergency_contact: str | None = _Field(default=None, description="Emergency Contact")
    emergency_phone: str | None = _Field(default=None, description="Emergency Phone")
    job_title: str | None = _Field(default=None, description="Job Title")
    company: str | None = _Field(default=None, description="Company")
    special_needs: str | None = _Field(default=None, description="Special Needs")
    shirt_size: ShirtSize | str | None = _Field(
        default=None, union_mode="left_to_right", description="Shirt Size"
    )
    registration_complete: bool | None = _Field(default=None, description="Registration Complete")
    home_country: str | None = _Field(default=None, description="Home Country")
    expected_grad: date | str | None = _Field(
        default=None, union_mode="left_to_right", description="Expected Graduation"
    )
    began_degree: date | str | None = _Field(
        default=None, union_mode="left_to_right", description="Began Degree"
    )
    include_email: Consent | str | None = _Field(
        default=None, union_mode="left_to_right", description="Interest - Include Email"
    )
    employment_opportunities: Consent | str | None = _Field(
        default=None, union_mode="left_to_right", description="Interest - Employment Opportunities"
    )
    inform_other_contests: Consent | str | None = _Field(
        default=None, union_mode="left_to_right", description="Interest - Inform Other Contests"
    )
    address_line1: str | None = _Field(default=None, description="Shipping Address Line 1")
    address_line2: str | None = _Field(default=None, description="Shipping Address Line 2")
    address_line3: str | None = _Field(default=None, description="Shipping Address Line 3")
    city: str | None = _Field(default=None, description="City")
    state: str | None = _Field(default=None, description="State")
    postal_code: str | None = _Field(default=None, description="Postal Code")
    twitter: str | None = _Field(default=None, description="Twitter")
    facebook: str | None = _Field(default=None, description="Facebook")
    top_coder: str | None = _Field(default=None, description="TopCoder")
    codeforces: str | None = _Field(default=None, description="CodeForces")
    linkedin: str | None = _Field(default=None, description="LinkedIn")
    surname: str | None = _Field(default=None, description="Surname")
    given_names: str | None = _Field(default=None, description="Given Names")
    apply_from_city: str | None = _Field(default=None, description="Apply From City")
    passport_country: str | None = _Field(default=None, description="Passport Country")
    visa_plan: str | None = _Field(default=None, description="Visa Plan")
    passport_number: str | None = _Field(default=None, description="Passport Number")
    passport_expiry: date | str | None = _Field(
        default=None, union_mode="left_to_right", description="Passport Expiry"
    )
    passport_issue: date | str | None = _Field(
        default=None, union_mode="left_to_right", description="Passport Issued"
    )
    passport_nationality: str | None = _Field(default=None, description="Residence Nationality")
    residence_country: str | None = _Field(default=None, description="Residence Country")
    residence_city: str | None = _Field(default=None, description="Residence City")
    passport_not_needed: bool | None = None
    visa_type: str | None = _Field(default=None, description="Visa Type")
    consulate_country: str | None = _Field(default=None, description="Consulate Country")
    consulate_city: str | None = _Field(default=None, description="Consulate City")
    consulate_interview: bool | None = _Field(default=None, description="Consulate Interview")
    visa_needed: bool | None = None
    entry_airport: str | None = _Field(default=None, description="Entry Airport")
    inst_name: str | None = _Field(default=None, description="Institution Name")
    inst_short_name: str | None = _Field(default=None, description="Institution Short Name")
    inst_native_name: str | None = _Field(default=None, description="Institution Local Name")
    inst_id: int | None = None
    team_ids: str | None = _Field(default=None, description="Team IDs")
    team_ids_out: str | None = None
    teams: str | None = _Field(default=None, description="Teams")
    teams_list: str | None = None
    team_roles: str | None = _Field(default=None, description="Team Roles")
    team_roles_out: str | None = None
    team_sites: str | None = _Field(default=None, description="Team Sites")
    team_sites_out: str | None = None
    workstation_ids: str | None = _Field(default=None, description="Workstation IDs")
    workstation_ids_out: str | None = None
    staff_roles: str | None = _Field(default=None, description="Staff Roles")
    staff_roles_out: str | None = None
    staff_sites: str | None = _Field(default=None, description="Staff Sites")
    staff_sites_out: str | None = None
    labels: str | None = _Field(default=None, description="Labels")


class InstitutionRow(Row):
    """Institutions with at least one team in a contest.

    Returned by:
    * ``/contest/search/contest/{contest_id}/institution``
    * ``/contest/search/site/{site_id}/institutions``
    """

    inst_id: int | None = _Field(default=None, description="Inst-ID")
    inst_name: str | None = _Field(default=None, description="Inst-Name")
    inst_native_name: str | None = _Field(default=None, description="Inst-NativeName")
    inst_short_name: str | None = _Field(default=None, description="Inst-ShortName")
    inst_abbreviation: str | None = _Field(default=None, description="Inst-Abbreviation")
    inst_homepage_url: str | None = _Field(default=None, description="Inst-URL")
    inst_unit_id: int | None = _Field(default=None, description="Inst-U-ID")
    inst_unit_name: str | None = _Field(default=None, description="Inst-U-Name")
    inst_unit_native_name: str | None = _Field(default=None, description="Inst-U-NativeName")
    inst_unit_short_name: str | None = _Field(default=None, description="Inst-U-ShortName")
    inst_unit_abbreviation: str | None = _Field(default=None, description="Inst-U-Abbreviation")
    inst_unit_homepage_url: str | None = _Field(default=None, description="Inst-U-URL")
    inst_unit_type: InstitutionUnitType | str | None = _Field(
        default=None, union_mode="left_to_right", description="Offered Degree"
    )
    address_line1: str | None = _Field(default=None, description="AddressLine1")
    address_line2: str | None = _Field(default=None, description="AddressLine2")
    address_line3: str | None = _Field(default=None, description="AddressLine3")
    city: str | None = _Field(default=None, description="City")
    state: str | None = _Field(default=None, description="State")
    zip: str | None = _Field(default=None, description="Postal Code")
    country_name: str | None = _Field(default=None, description="Country")
    longitude: float | None = _Field(default=None, description="Longitude")
    latitude: float | None = _Field(default=None, description="Latitude")
    twitter_name: str | None = _Field(default=None, description="Twitter Name")
    twitter_hash: str | None = _Field(default=None, description="Twitter Hash")
    facebook_page: str | None = _Field(default=None, description="Facebook Page")


class PromoteRow(Row):
    """Teams eligible to be promoted out of a contest.

    Returned by:
    * ``/team/search/{contest_id}/promote``
    """

    rank: int | None = _Field(default=None, description="Rank")
    team_id: int | None = _Field(default=None, description="Team Id")
    team_name: str | None = _Field(default=None, description="Team")
    site_id: int | None = None
    site_name: str | None = _Field(default=None, description="Site")
    institution_id: int | None = None
    institution_name: str | None = _Field(default=None, description="Institution")
    promote_to_contest: int | None = None
    promote_to_site: str | None = None


class StaffFundingRow(Row):
    """Staff funding and budget rows.

    Returned by:
    * ``/contest/staffMember/funding/contest/{contest_id}/search``
    """

    contest_participant_id: int | None = None
    site: str | None = _Field(default=None, description="Site")
    site_id: int | None = None
    person_id: int | None = None
    first_name: str | None = _Field(default=None, description="First Name")
    last_name: str | None = _Field(default=None, description="Last Name")
    username: str | None = _Field(default=None, description="Email")
    home_town: str | None = _Field(default=None, description="Home Town")
    home_country: str | None = _Field(default=None, description="Home Country")
    residence_country: str | None = None
    funding: str | None = None
    budget: float | None = _Field(default=None, description="Budget")
    budget_adjustment: float | None = _Field(default=None, description="Budget Adjustment")
    residence_town: str | None = None
    initiated: bool | None = _Field(default=None, description="Initiated")
    notes: str | None = _Field(default=None, description="Notes")
    transport: str | None = None


class StaffMemberRow(Row):
    """Staff members of a contest, from the staff administration grid.

    Returned by:
    * ``/contest/staffmember/contest/{contest_id}/search``
    * ``/contest/staffmember/contest/{contest_id}/public/search``
    """

    staff_member_id: int | None = None
    site_id: int | None = None
    site: str | None = _Field(default=None, description="Site")
    title: Title | str | None = _Field(
        default=None, union_mode="left_to_right", description="Title"
    )
    first_name: str | None = _Field(default=None, description="First Name")
    last_name: str | None = _Field(default=None, description="Last Name")
    username: str | None = _Field(default=None, description="Email")
    user_id: int | None = None
    badge_role: str | None = _Field(default=None, description="Badge Role")
    certificate_role: str | None = _Field(default=None, description="Certificate Role")
    institution: str | None = _Field(default=None, description="Institution Name")
    inst_id: int | None = None
    registration_complete: bool | None = _Field(default=None, description="Registration Complete")
    show_in_public_pages: bool | None = _Field(default=None, description="Show in Public Pages")
    labels: str | None = _Field(default=None, description="Labels")
    labels_lite: str | None = None


class StaffRow(HasExtraFields, Row):
    """Contest staff, from the contest grid.

    Returned by:
    * ``/contest/search/contest/{contest_id}/staff``
    """

    staff_member_id: int | None = None
    username: str | None = _Field(default=None, description="Username")
    first_name: str | None = _Field(default=None, description="First Name")
    last_name: str | None = _Field(default=None, description="Last Name")
    badge_name: str | None = _Field(default=None, description="Badge Name")
    certificate_name: str | None = _Field(default=None, description="Certificate Name")
    roles: str | None = _Field(default=None, description="Roles")
    phone: str | None = _Field(default=None, description="Phone")
    institution: str | None = _Field(default=None, description="Institution Name")
    site: str | None = _Field(default=None, description="Site")
    shirt_size: ShirtSize | str | None = _Field(
        default=None, union_mode="left_to_right", description="Shirt Size"
    )
    special_needs: str | None = _Field(default=None, description="Special Needs")
    sex: Sex | str | None = _Field(default=None, union_mode="left_to_right", description="Sex")
    complete_registration: bool | None = _Field(default=None, description="Registration Complete")
    country: str | None = _Field(default=None, description="Country")
    twitter: str | None = _Field(default=None, description="Twitter")
    labels: str | None = _Field(default=None, description="Labels")
    extra_field: str | None = _Field(default=None, description="Extra Fields")
    person_id: int | None = None


class StaffTshirtRow(Row):
    """Staff t-shirt sizes.

    Returned by:
    * ``/contest/staffmember/tshirt/contest/{contest_id}/search``
    """

    contest_participant_id: int | None = None
    staff_member_id: int | None = None
    site: str | None = _Field(default=None, description="Site")
    person_id: int | None = None
    first_name: str | None = _Field(default=None, description="First Name")
    last_name: str | None = _Field(default=None, description="Last Name")
    username: str | None = _Field(default=None, description="Email")
    badge_role: str | None = _Field(default=None, description="Badge Role")
    institution: str | None = _Field(default=None, description="Institution")
    registration_complete: bool | None = _Field(default=None, description="Registration Complete")
    shirt_size: ShirtSize | str | None = _Field(
        default=None, union_mode="left_to_right", description="Shirt size"
    )
    tshirts: str | None = _Field(default=None, description="T-shirts")


class StandingsRow(Row):
    """Uploaded standings documents for a contest (not the results themselves).

    Returned by:
    * ``/contest/standings/contest/{contest_id}/search``
    """

    id: int | None = None
    name: str | None = _Field(default=None, description="Standings Name")
    entered_by: str | None = _Field(default=None, description="Entered By")
    date_entered: datetime | str | None = _Field(
        default=None, union_mode="left_to_right", description="Date Entered"
    )
    certified: bool | None = _Field(default=None, description="Certified?")
    certified_by: str | None = _Field(default=None, description="Certified By")
    date_certified: datetime | str | None = _Field(
        default=None, union_mode="left_to_right", description="Date Certified"
    )
    published: bool | None = _Field(default=None, description="Published?")


class TeamMemberRow(HasExtraFields, Row):
    """Every team member in a contest, one row per membership.

    Returned by:
    * ``/contest/search/contest/{contest_id}/teammember``
    * ``/contest/search/site/{site_id}/teammember``
    """

    id: int | None = None
    role: MemberRole | str | None = _Field(
        default=None, union_mode="left_to_right", description="Role"
    )
    person_id: int | None = None
    username: str | None = _Field(default=None, description="Username")
    first_name: str | None = _Field(default=None, description="First Name")
    last_name: str | None = _Field(default=None, description="Last Name")
    local_name: str | None = _Field(default=None, description="Local Name")
    phone: str | None = _Field(default=None, description="Phone")
    special_needs: str | None = _Field(default=None, description="Special Needs")
    sex: Sex | str | None = _Field(default=None, union_mode="left_to_right", description="Sex")
    complete_registration: bool | None = _Field(default=None, description="Registration Complete")
    attending_onsite: bool | None = _Field(default=None, description="Attending Onsite")
    dob: date | str | None = _Field(
        default=None, union_mode="left_to_right", description="Date of Birth"
    )
    shirt_size: ShirtSize | str | None = _Field(
        default=None, union_mode="left_to_right", description="Shirt Size"
    )
    country: str | None = _Field(default=None, description="Country")
    twitter: str | None = _Field(default=None, description="Twitter")
    team_member_inst_id: int | None = None
    team_member_inst_name: str | None = _Field(default=None, description="Profile Institution Name")
    area_of_study: str | None = _Field(default=None, description="Area Of Study")
    degree_pursued: str | None = _Field(default=None, description="Degree Pursued")
    began_degree: date | str | None = _Field(
        default=None, union_mode="left_to_right", description="Began Degree"
    )
    expected_grad: date | str | None = _Field(
        default=None, union_mode="left_to_right", description="Expected Graduation"
    )
    include_email: Consent | str | None = _Field(default=None, union_mode="left_to_right")
    employment_opportunities: Consent | str | None = _Field(
        default=None, union_mode="left_to_right", description="Interest - Employment Opportunities"
    )
    inform_other_contests: Consent | str | None = _Field(default=None, union_mode="left_to_right")
    badge_name: str | None = _Field(default=None, description="Badge Name")
    certificate_name: str | None = _Field(default=None, description="Certificate Name")
    team_id: int | None = _Field(default=None, description="Team ID")
    team_name: str | None = _Field(default=None, description="Team Name")
    workstation_id: str | None = _Field(default=None, description="Workstation Id")
    team_status: TeamStatus | str | None = _Field(
        default=None, union_mode="left_to_right", description="Team Status"
    )
    team_rank: int | None = _Field(default=None, description="Team Rank")
    extra_field: str | None = _Field(default=None, description="Extra Fields")
    labels: str | None = _Field(default=None, description="Labels")
    team_inst_id: int | None = None
    team_inst_name: str | None = _Field(default=None, description="Team Institution Name")
    team_inst_short_name: str | None = _Field(
        default=None, description="Team Institution Short Name"
    )
    site_id: int | None = None
    site_name: str | None = _Field(default=None, description="Site")


class TeamRow(HasTeamMembers, HasExtraFields, Row):
    """Teams registered for a contest.

    Returned by:
    * ``/contest/search/contest/{contest_id}/team``
    * ``/contest/search/site/{site_id}/teams``
    """

    id: int | None = _Field(default=None, description="Team Id")
    name: str | None = _Field(default=None, description="Team Name")
    team_members: str | None = _Field(default=None, description="Team Members")
    status: TeamStatus | str | None = _Field(
        default=None, union_mode="left_to_right", description="Status"
    )
    extended_state: str | None = _Field(default=None, description="Extended State")
    paid: bool | None = _Field(default=None, description="Paid")
    note: str | None = _Field(default=None, description="Note")
    check_in: str | None = _Field(default=None, description="Check-In")
    workstation_id: str | None = _Field(default=None, description="Workstation Id")
    rank: int | None = _Field(default=None, description="Rank")
    certified: bool | None = _Field(default=None, description="Certified")
    eligibility_status: EligibilityStatus | str | None = _Field(
        default=None, union_mode="left_to_right", description="Eligibility Status"
    )
    eligibility_issue: str | None = _Field(default=None, description="Eligibility Issue")
    eligibility_comment: str | None = _Field(default=None, description="Eligibility Comment")
    inst_id: int | None = None
    inst_name: str | None = _Field(default=None, description="Institution Name")
    inst_short_name: str | None = _Field(default=None, description="Institution Short Name")
    inst_address: str | None = _Field(default=None, description="Institution Address")
    city: str | None = _Field(default=None, description="Institution City")
    country: str | None = _Field(default=None, description="Country")
    a2: str | None = None
    site: str | None = _Field(default=None, description="Site")
    created_when: datetime | str | None = _Field(
        default=None, union_mode="left_to_right", description="Created When"
    )
    extra_field: str | None = _Field(default=None, description="Extra Field")


class TeamSummaryRow(Row):
    """Teams of a contest in the alternate shape used by the team grid: ``teamId``/``teamName`` rather than ``id``/``name``, plus promotion history.

    Returned by:
    * ``/team/search/{contest_id}/all``
    * ``/contest/search/site/{site_id}/home/teams``
    """

    team_id: int | None = _Field(default=None, description="Team Id")
    team_name: str | None = _Field(default=None, description="Team Name")
    rank: int | None = _Field(default=None, description="Rank")
    site_id: int | None = None
    site_name: str | None = _Field(default=None, description="Site")
    country: str | None = _Field(default=None, description="Country")
    a2: str | None = None
    inst_id: int | None = None
    inst_name: str | None = _Field(default=None, description="Institution")
    coach_id: int | None = None
    coach_name: str | None = _Field(default=None, description="Coach")
    promoted_from_team_id: int | None = None
    promoted_from_team_name: str | None = _Field(default=None, description="Promoted from Team")
    promoted_from_contest_id: int | None = None
    promoted_from_contest_name: str | None = _Field(
        default=None, description="Promoted from Contest"
    )
    created: datetime | str | None = _Field(
        default=None, union_mode="left_to_right", description="Created"
    )
    status: TeamStatus | str | None = _Field(
        default=None, union_mode="left_to_right", description="Status"
    )
    eligibility_id: int | None = None
    eligibility_status: EligibilityStatus | str | None = _Field(
        default=None, union_mode="left_to_right", description="Eligibility"
    )
    certified: bool | None = _Field(default=None, description="Certified")
    paid: bool | None = _Field(default=None, description="Paid")
    extended_state: str | None = _Field(default=None, description="Extended Status")


class Top20Row(Row):
    """Top-20 participants of a contest.

    Returned by:
    * ``/contest/search/contest/{contest_id}/top20``
    """

    area: str | None = None
    contest: str | None = None
    contest_id: int | None = None
    rank: int | None = None
    team: str | None = None
    team_id: int | None = None
    role: str | None = None
    institution: str | None = None
    inst_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    user_id: int | None = None
    inform: Consent | str | None = _Field(default=None, union_mode="left_to_right")


class TransportationMissingRow(Row):
    """People who have not filled in their travel details.

    Returned by:
    * ``/contest/transportation/search/contest/{contest_id}/missing``
    """

    person_id: int | None = None
    first_name: str | None = _Field(default=None, description="First Name")
    last_name: str | None = _Field(default=None, description="Last Name")
    attending_onsite: bool | None = _Field(default=None, description="Attending Onsite")
    country_name: str | None = _Field(default=None, description="Country")
    country_a2: str | None = None
    email: str | None = _Field(default=None, description="Email")
    modified_when: datetime | str | None = _Field(
        default=None, union_mode="left_to_right", description="Modified"
    )
    participant_id: int | None = None
    site_name: str | None = None
    coach: bool | None = None


class TshirtRow(Row):
    """Coach t-shirt sizes at a site.

    Returned by:
    * ``/contest/search/site/{site_id}/tshirt/coaches``
    * ``/contest/search/site/{site_id}/tshirt/cocoaches``
    * ``/contest/search/site/{site_id}/tshirt/contestants``
    """

    institution: str | None = _Field(default=None, description="Institution")
    person_name: str | None = _Field(default=None, description="Name")
    team_name: str | None = _Field(default=None, description="Team")
    tshirt_size: ShirtSize | str | None = _Field(
        default=None, union_mode="left_to_right", description="Shirt Size"
    )
