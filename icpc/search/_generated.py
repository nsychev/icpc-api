"""Generated from icpc.global SPA bundle.

One entry per search endpoint. Each exposes:

* a ``Literal`` of its valid column names, so a projection typo is a type error
  rather than a silently empty column;
* a ``Fields`` namespace of typed descriptors for building filters and sort keys;
* a factory taking the contest or site id and returning a bound
  :class:`~icpc.search.endpoint.SearchEndpoint`.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from icpc.models._generated import (
    CertificateRow,
    ContestParticipantRow,
    InstitutionRow,
    PromoteRow,
    StaffFundingRow,
    StaffMemberRow,
    StaffRow,
    StaffTshirtRow,
    StandingsRow,
    TeamMemberRow,
    TeamRow,
    TeamSummaryRow,
    Top20Row,
    TransportationMissingRow,
    TshirtRow,
)
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
from icpc.search.endpoint import SearchEndpoint
from icpc.search.fields import Field

__all__ = [
    "CertificateFields",
    "ContestParticipantFields",
    "InstitutionFields",
    "PromoteFields",
    "StaffFields",
    "StaffFundingFields",
    "StaffMemberFields",
    "StaffTshirtFields",
    "StandingsFields",
    "TeamFields",
    "TeamMemberFields",
    "TeamSummaryFields",
    "Top20Fields",
    "TransportationMissingFields",
    "TshirtFields",
    "contest_institutions",
    "contest_missing_transportation",
    "contest_participants",
    "contest_promote_candidates",
    "contest_public_staff_members",
    "contest_staff",
    "contest_staff_certificates",
    "contest_staff_funding",
    "contest_staff_members",
    "contest_staff_tshirts",
    "contest_standings",
    "contest_team_certificates",
    "contest_team_members",
    "contest_team_summaries",
    "contest_teams",
    "contest_top20",
    "site_coach_tshirts",
    "site_cocoach_tshirts",
    "site_contestant_tshirts",
    "site_home_teams",
    "site_institutions",
    "site_participants",
    "site_team_certificates",
    "site_team_members",
    "site_teams",
]


#: Valid column names of :class:`~icpc.models.CertificateRow`.
type CertificateField = Literal[
    "id",
    "email",
    "userId",
    "name",
    "certificateName",
    "siteName",
    "siteId",
    "contestName",
    "contestId",
    "role",
    "institutionName",
    "instId",
    "institutionShortName",
    "teamName",
    "teamId",
    "teamMembers",
    "liteTeamMemberSet",
]


class CertificateFields:
    """Typed columns of :class:`~icpc.models.CertificateRow`."""

    id: Field[CertificateRow, int] = Field("id")
    email: Field[CertificateRow, str] = Field("email")
    user_id: Field[CertificateRow, int] = Field("userId")
    name: Field[CertificateRow, str] = Field("name")
    certificate_name: Field[CertificateRow, str] = Field("certificateName")
    site_name: Field[CertificateRow, str] = Field("siteName")
    site_id: Field[CertificateRow, int] = Field("siteId")
    contest_name: Field[CertificateRow, str] = Field("contestName")
    contest_id: Field[CertificateRow, int] = Field("contestId")
    role: Field[CertificateRow, str] = Field("role")
    institution_name: Field[CertificateRow, str] = Field("institutionName")
    inst_id: Field[CertificateRow, int] = Field("instId")
    institution_short_name: Field[CertificateRow, str] = Field("institutionShortName")
    team_name: Field[CertificateRow, str] = Field("teamName")
    team_id: Field[CertificateRow, int] = Field("teamId")
    team_members: Field[CertificateRow, str] = Field("teamMembers")
    lite_team_member_set: Field[CertificateRow, str] = Field("liteTeamMemberSet")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "id",
        "email",
        "name",
        "siteName",
        "contestName",
        "role",
        "institutionName",
        "institutionShortName",
        "teamName",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "id",
        "email",
        "userId",
        "name",
        "certificateName",
        "siteName",
        "siteId",
        "contestName",
        "contestId",
        "role",
        "institutionName",
        "instId",
        "institutionShortName",
        "teamName",
        "teamId",
        "teamMembers",
        "liteTeamMemberSet",
    )


#: Valid column names of :class:`~icpc.models.ContestParticipantRow`.
type ContestParticipantField = Literal[
    "personId",
    "username",
    "localName",
    "badgeName",
    "secondaryEmail",
    "firstName",
    "lastName",
    "title",
    "sex",
    "dob",
    "phone",
    "emergencyContact",
    "emergencyPhone",
    "jobTitle",
    "company",
    "specialNeeds",
    "shirtSize",
    "registrationComplete",
    "homeCountry",
    "expectedGrad",
    "beganDegree",
    "includeEmail",
    "employmentOpportunities",
    "informOtherContests",
    "addressLine1",
    "addressLine2",
    "addressLine3",
    "city",
    "state",
    "postalCode",
    "twitter",
    "facebook",
    "topCoder",
    "codeforces",
    "linkedin",
    "surname",
    "givenNames",
    "applyFromCity",
    "passportCountry",
    "visaPlan",
    "passportNumber",
    "passportExpiry",
    "passportIssue",
    "passportNationality",
    "residenceCountry",
    "residenceCity",
    "passportNotNeeded",
    "visaType",
    "consulateCountry",
    "consulateCity",
    "consulateInterview",
    "visaNeeded",
    "entryAirport",
    "instName",
    "instShortName",
    "instNativeName",
    "instId",
    "teamIds",
    "teamIdsOut",
    "teams",
    "teamsList",
    "teamRoles",
    "teamRolesOut",
    "teamSites",
    "teamSitesOut",
    "workstationIds",
    "workstationIdsOut",
    "staffRoles",
    "staffRolesOut",
    "staffSites",
    "staffSitesOut",
    "labels",
]


class ContestParticipantFields:
    """Typed columns of :class:`~icpc.models.ContestParticipantRow`."""

    person_id: Field[ContestParticipantRow, int] = Field("personId")
    username: Field[ContestParticipantRow, str] = Field("username")
    local_name: Field[ContestParticipantRow, str] = Field("localName")
    badge_name: Field[ContestParticipantRow, str] = Field("badgeName")
    secondary_email: Field[ContestParticipantRow, str] = Field("secondaryEmail")
    first_name: Field[ContestParticipantRow, str] = Field("firstName")
    last_name: Field[ContestParticipantRow, str] = Field("lastName")
    title: Field[ContestParticipantRow, Title | str] = Field("title")
    sex: Field[ContestParticipantRow, Sex | str] = Field("sex")
    dob: Field[ContestParticipantRow, date | str] = Field("dob")
    phone: Field[ContestParticipantRow, str] = Field("phone")
    emergency_contact: Field[ContestParticipantRow, str] = Field("emergencyContact")
    emergency_phone: Field[ContestParticipantRow, str] = Field("emergencyPhone")
    job_title: Field[ContestParticipantRow, str] = Field("jobTitle")
    company: Field[ContestParticipantRow, str] = Field("company")
    special_needs: Field[ContestParticipantRow, str] = Field("specialNeeds")
    shirt_size: Field[ContestParticipantRow, ShirtSize | str] = Field("shirtSize")
    registration_complete: Field[ContestParticipantRow, bool] = Field("registrationComplete")
    home_country: Field[ContestParticipantRow, str] = Field("homeCountry")
    expected_grad: Field[ContestParticipantRow, date | str] = Field("expectedGrad")
    began_degree: Field[ContestParticipantRow, date | str] = Field("beganDegree")
    include_email: Field[ContestParticipantRow, Consent | str] = Field("includeEmail")
    employment_opportunities: Field[ContestParticipantRow, Consent | str] = Field(
        "employmentOpportunities"
    )
    inform_other_contests: Field[ContestParticipantRow, Consent | str] = Field(
        "informOtherContests"
    )
    address_line1: Field[ContestParticipantRow, str] = Field("addressLine1")
    address_line2: Field[ContestParticipantRow, str] = Field("addressLine2")
    address_line3: Field[ContestParticipantRow, str] = Field("addressLine3")
    city: Field[ContestParticipantRow, str] = Field("city")
    state: Field[ContestParticipantRow, str] = Field("state")
    postal_code: Field[ContestParticipantRow, str] = Field("postalCode")
    twitter: Field[ContestParticipantRow, str] = Field("twitter")
    facebook: Field[ContestParticipantRow, str] = Field("facebook")
    top_coder: Field[ContestParticipantRow, str] = Field("topCoder")
    codeforces: Field[ContestParticipantRow, str] = Field("codeforces")
    linkedin: Field[ContestParticipantRow, str] = Field("linkedin")
    surname: Field[ContestParticipantRow, str] = Field("surname")
    given_names: Field[ContestParticipantRow, str] = Field("givenNames")
    apply_from_city: Field[ContestParticipantRow, str] = Field("applyFromCity")
    passport_country: Field[ContestParticipantRow, str] = Field("passportCountry")
    visa_plan: Field[ContestParticipantRow, str] = Field("visaPlan")
    passport_number: Field[ContestParticipantRow, str] = Field("passportNumber")
    passport_expiry: Field[ContestParticipantRow, date | str] = Field("passportExpiry")
    passport_issue: Field[ContestParticipantRow, date | str] = Field("passportIssue")
    passport_nationality: Field[ContestParticipantRow, str] = Field("passportNationality")
    residence_country: Field[ContestParticipantRow, str] = Field("residenceCountry")
    residence_city: Field[ContestParticipantRow, str] = Field("residenceCity")
    passport_not_needed: Field[ContestParticipantRow, bool] = Field("passportNotNeeded")
    visa_type: Field[ContestParticipantRow, str] = Field("visaType")
    consulate_country: Field[ContestParticipantRow, str] = Field("consulateCountry")
    consulate_city: Field[ContestParticipantRow, str] = Field("consulateCity")
    consulate_interview: Field[ContestParticipantRow, bool] = Field("consulateInterview")
    visa_needed: Field[ContestParticipantRow, bool] = Field("visaNeeded")
    entry_airport: Field[ContestParticipantRow, str] = Field("entryAirport")
    inst_name: Field[ContestParticipantRow, str] = Field("instName")
    inst_short_name: Field[ContestParticipantRow, str] = Field("instShortName")
    inst_native_name: Field[ContestParticipantRow, str] = Field("instNativeName")
    inst_id: Field[ContestParticipantRow, int] = Field("instId")
    team_ids: Field[ContestParticipantRow, str] = Field("teamIds")
    team_ids_out: Field[ContestParticipantRow, str] = Field("teamIdsOut")
    teams: Field[ContestParticipantRow, str] = Field("teams")
    teams_list: Field[ContestParticipantRow, str] = Field("teamsList")
    team_roles: Field[ContestParticipantRow, str] = Field("teamRoles")
    team_roles_out: Field[ContestParticipantRow, str] = Field("teamRolesOut")
    team_sites: Field[ContestParticipantRow, str] = Field("teamSites")
    team_sites_out: Field[ContestParticipantRow, str] = Field("teamSitesOut")
    workstation_ids: Field[ContestParticipantRow, str] = Field("workstationIds")
    workstation_ids_out: Field[ContestParticipantRow, str] = Field("workstationIdsOut")
    staff_roles: Field[ContestParticipantRow, str] = Field("staffRoles")
    staff_roles_out: Field[ContestParticipantRow, str] = Field("staffRolesOut")
    staff_sites: Field[ContestParticipantRow, str] = Field("staffSites")
    staff_sites_out: Field[ContestParticipantRow, str] = Field("staffSitesOut")
    labels: Field[ContestParticipantRow, str] = Field("labels")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "username",
        "title",
        "sex",
        "dob",
        "labels",
        "addressLine1",
        "addressLine2",
        "addressLine3",
        "city",
        "state",
        "postalCode",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "personId",
        "username",
        "localName",
        "badgeName",
        "secondaryEmail",
        "firstName",
        "lastName",
        "title",
        "sex",
        "dob",
        "phone",
        "emergencyContact",
        "emergencyPhone",
        "jobTitle",
        "company",
        "specialNeeds",
        "shirtSize",
        "registrationComplete",
        "homeCountry",
        "expectedGrad",
        "beganDegree",
        "includeEmail",
        "employmentOpportunities",
        "informOtherContests",
        "addressLine1",
        "addressLine2",
        "addressLine3",
        "city",
        "state",
        "postalCode",
        "twitter",
        "facebook",
        "topCoder",
        "codeforces",
        "linkedin",
        "surname",
        "givenNames",
        "applyFromCity",
        "passportCountry",
        "visaPlan",
        "passportNumber",
        "passportExpiry",
        "passportIssue",
        "passportNationality",
        "residenceCountry",
        "residenceCity",
        "passportNotNeeded",
        "visaType",
        "consulateCountry",
        "consulateCity",
        "consulateInterview",
        "visaNeeded",
        "entryAirport",
        "instName",
        "instShortName",
        "instNativeName",
        "instId",
        "teamIds",
        "teamIdsOut",
        "teams",
        "teamsList",
        "teamRoles",
        "teamRolesOut",
        "teamSites",
        "teamSitesOut",
        "workstationIds",
        "workstationIdsOut",
        "staffRoles",
        "staffRolesOut",
        "staffSites",
        "staffSitesOut",
        "labels",
    )


#: Valid column names of :class:`~icpc.models.InstitutionRow`.
type InstitutionField = Literal[
    "instId",
    "instName",
    "instNativeName",
    "instShortName",
    "instAbbreviation",
    "instHomepageUrl",
    "instUnitId",
    "instUnitName",
    "instUnitNativeName",
    "instUnitShortName",
    "instUnitAbbreviation",
    "instUnitHomepageUrl",
    "instUnitType",
    "addressLine1",
    "addressLine2",
    "addressLine3",
    "city",
    "state",
    "zip",
    "countryName",
    "longitude",
    "latitude",
    "twitterName",
    "twitterHash",
    "facebookPage",
]


class InstitutionFields:
    """Typed columns of :class:`~icpc.models.InstitutionRow`."""

    inst_id: Field[InstitutionRow, int] = Field("instId")
    inst_name: Field[InstitutionRow, str] = Field("instName")
    inst_native_name: Field[InstitutionRow, str] = Field("instNativeName")
    inst_short_name: Field[InstitutionRow, str] = Field("instShortName")
    inst_abbreviation: Field[InstitutionRow, str] = Field("instAbbreviation")
    inst_homepage_url: Field[InstitutionRow, str] = Field("instHomepageUrl")
    inst_unit_id: Field[InstitutionRow, int] = Field("instUnitId")
    inst_unit_name: Field[InstitutionRow, str] = Field("instUnitName")
    inst_unit_native_name: Field[InstitutionRow, str] = Field("instUnitNativeName")
    inst_unit_short_name: Field[InstitutionRow, str] = Field("instUnitShortName")
    inst_unit_abbreviation: Field[InstitutionRow, str] = Field("instUnitAbbreviation")
    inst_unit_homepage_url: Field[InstitutionRow, str] = Field("instUnitHomepageUrl")
    inst_unit_type: Field[InstitutionRow, InstitutionUnitType | str] = Field("instUnitType")
    address_line1: Field[InstitutionRow, str] = Field("addressLine1")
    address_line2: Field[InstitutionRow, str] = Field("addressLine2")
    address_line3: Field[InstitutionRow, str] = Field("addressLine3")
    city: Field[InstitutionRow, str] = Field("city")
    state: Field[InstitutionRow, str] = Field("state")
    zip: Field[InstitutionRow, str] = Field("zip")
    country_name: Field[InstitutionRow, str] = Field("countryName")
    longitude: Field[InstitutionRow, float] = Field("longitude")
    latitude: Field[InstitutionRow, float] = Field("latitude")
    twitter_name: Field[InstitutionRow, str] = Field("twitterName")
    twitter_hash: Field[InstitutionRow, str] = Field("twitterHash")
    facebook_page: Field[InstitutionRow, str] = Field("facebookPage")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "instId",
        "instName",
        "instUnitId",
        "instUnitNativeName",
        "instUnitShortName",
        "instUnitAbbreviation",
        "instUnitHomepageUrl",
        "instUnitType",
        "city",
        "countryName",
        "twitterName",
        "twitterHash",
        "facebookPage",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "instId",
        "instName",
        "instNativeName",
        "instShortName",
        "instAbbreviation",
        "instHomepageUrl",
        "instUnitId",
        "instUnitName",
        "instUnitNativeName",
        "instUnitShortName",
        "instUnitAbbreviation",
        "instUnitHomepageUrl",
        "instUnitType",
        "addressLine1",
        "addressLine2",
        "addressLine3",
        "city",
        "state",
        "zip",
        "countryName",
        "longitude",
        "latitude",
        "twitterName",
        "twitterHash",
        "facebookPage",
    )


#: Valid column names of :class:`~icpc.models.PromoteRow`.
type PromoteField = Literal[
    "rank",
    "teamId",
    "teamName",
    "siteId",
    "siteName",
    "institutionId",
    "institutionName",
    "promoteToContest",
    "promoteToSite",
]


class PromoteFields:
    """Typed columns of :class:`~icpc.models.PromoteRow`."""

    rank: Field[PromoteRow, int] = Field("rank")
    team_id: Field[PromoteRow, int] = Field("teamId")
    team_name: Field[PromoteRow, str] = Field("teamName")
    site_id: Field[PromoteRow, int] = Field("siteId")
    site_name: Field[PromoteRow, str] = Field("siteName")
    institution_id: Field[PromoteRow, int] = Field("institutionId")
    institution_name: Field[PromoteRow, str] = Field("institutionName")
    promote_to_contest: Field[PromoteRow, int] = Field("promoteToContest")
    promote_to_site: Field[PromoteRow, str] = Field("promoteToSite")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "rank",
        "siteName",
        "teamName",
        "institutionName",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "rank",
        "teamId",
        "teamName",
        "siteId",
        "siteName",
        "institutionId",
        "institutionName",
        "promoteToContest",
        "promoteToSite",
    )


#: Valid column names of :class:`~icpc.models.StaffFundingRow`.
type StaffFundingField = Literal[
    "contestParticipantId",
    "site",
    "siteId",
    "personId",
    "firstName",
    "lastName",
    "username",
    "homeTown",
    "homeCountry",
    "residenceCountry",
    "funding",
    "budget",
    "budgetAdjustment",
    "residenceTown",
    "initiated",
    "notes",
    "transport",
]


class StaffFundingFields:
    """Typed columns of :class:`~icpc.models.StaffFundingRow`."""

    contest_participant_id: Field[StaffFundingRow, int] = Field("contestParticipantId")
    site: Field[StaffFundingRow, str] = Field("site")
    site_id: Field[StaffFundingRow, int] = Field("siteId")
    person_id: Field[StaffFundingRow, int] = Field("personId")
    first_name: Field[StaffFundingRow, str] = Field("firstName")
    last_name: Field[StaffFundingRow, str] = Field("lastName")
    username: Field[StaffFundingRow, str] = Field("username")
    home_town: Field[StaffFundingRow, str] = Field("homeTown")
    home_country: Field[StaffFundingRow, str] = Field("homeCountry")
    residence_country: Field[StaffFundingRow, str] = Field("residenceCountry")
    funding: Field[StaffFundingRow, str] = Field("funding")
    budget: Field[StaffFundingRow, float] = Field("budget")
    budget_adjustment: Field[StaffFundingRow, float] = Field("budgetAdjustment")
    residence_town: Field[StaffFundingRow, str] = Field("residenceTown")
    initiated: Field[StaffFundingRow, bool] = Field("initiated")
    notes: Field[StaffFundingRow, str] = Field("notes")
    transport: Field[StaffFundingRow, str] = Field("transport")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "site",
        "firstName",
        "lastName",
        "username",
        "homeTown",
        "homeCountry",
        "budget",
        "budgetAdjustment",
        "notes",
        "initiated",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "contestParticipantId",
        "site",
        "siteId",
        "personId",
        "firstName",
        "lastName",
        "username",
        "homeTown",
        "homeCountry",
        "residenceCountry",
        "funding",
        "budget",
        "budgetAdjustment",
        "residenceTown",
        "initiated",
        "notes",
        "transport",
    )


#: Valid column names of :class:`~icpc.models.StaffMemberRow`.
type StaffMemberField = Literal[
    "staffMemberId",
    "siteId",
    "site",
    "title",
    "firstName",
    "lastName",
    "username",
    "userId",
    "badgeRole",
    "certificateRole",
    "institution",
    "instId",
    "registrationComplete",
    "showInPublicPages",
    "labels",
    "labelsLite",
]


class StaffMemberFields:
    """Typed columns of :class:`~icpc.models.StaffMemberRow`."""

    staff_member_id: Field[StaffMemberRow, int] = Field("staffMemberId")
    site_id: Field[StaffMemberRow, int] = Field("siteId")
    site: Field[StaffMemberRow, str] = Field("site")
    title: Field[StaffMemberRow, Title | str] = Field("title")
    first_name: Field[StaffMemberRow, str] = Field("firstName")
    last_name: Field[StaffMemberRow, str] = Field("lastName")
    username: Field[StaffMemberRow, str] = Field("username")
    user_id: Field[StaffMemberRow, int] = Field("userId")
    badge_role: Field[StaffMemberRow, str] = Field("badgeRole")
    certificate_role: Field[StaffMemberRow, str] = Field("certificateRole")
    institution: Field[StaffMemberRow, str] = Field("institution")
    inst_id: Field[StaffMemberRow, int] = Field("instId")
    registration_complete: Field[StaffMemberRow, bool] = Field("registrationComplete")
    show_in_public_pages: Field[StaffMemberRow, bool] = Field("showInPublicPages")
    labels: Field[StaffMemberRow, str] = Field("labels")
    labels_lite: Field[StaffMemberRow, str] = Field("labelsLite")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "site",
        "title",
        "firstName",
        "lastName",
        "username",
        "badgeRole",
        "certificateRole",
        "institution",
        "labels",
        "registrationComplete",
        "showInPublicPages",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "staffMemberId",
        "siteId",
        "site",
        "title",
        "firstName",
        "lastName",
        "username",
        "userId",
        "badgeRole",
        "certificateRole",
        "institution",
        "instId",
        "registrationComplete",
        "showInPublicPages",
        "labels",
        "labelsLite",
    )


#: Valid column names of :class:`~icpc.models.StaffRow`.
type StaffField = Literal[
    "staffMemberId",
    "username",
    "firstName",
    "lastName",
    "badgeName",
    "certificateName",
    "roles",
    "phone",
    "institution",
    "site",
    "shirtSize",
    "specialNeeds",
    "sex",
    "completeRegistration",
    "country",
    "twitter",
    "labels",
    "extraField",
    "personId",
]


class StaffFields:
    """Typed columns of :class:`~icpc.models.StaffRow`."""

    staff_member_id: Field[StaffRow, int] = Field("staffMemberId")
    username: Field[StaffRow, str] = Field("username")
    first_name: Field[StaffRow, str] = Field("firstName")
    last_name: Field[StaffRow, str] = Field("lastName")
    badge_name: Field[StaffRow, str] = Field("badgeName")
    certificate_name: Field[StaffRow, str] = Field("certificateName")
    roles: Field[StaffRow, str] = Field("roles")
    phone: Field[StaffRow, str] = Field("phone")
    institution: Field[StaffRow, str] = Field("institution")
    site: Field[StaffRow, str] = Field("site")
    shirt_size: Field[StaffRow, ShirtSize | str] = Field("shirtSize")
    special_needs: Field[StaffRow, str] = Field("specialNeeds")
    sex: Field[StaffRow, Sex | str] = Field("sex")
    complete_registration: Field[StaffRow, bool] = Field("completeRegistration")
    country: Field[StaffRow, str] = Field("country")
    twitter: Field[StaffRow, str] = Field("twitter")
    labels: Field[StaffRow, str] = Field("labels")
    extra_field: Field[StaffRow, str] = Field("extraField")
    person_id: Field[StaffRow, int] = Field("personId")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "username",
        "firstName",
        "lastName",
        "roles",
        "phone",
        "labels",
        "extraField",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "staffMemberId",
        "username",
        "firstName",
        "lastName",
        "badgeName",
        "certificateName",
        "roles",
        "phone",
        "institution",
        "site",
        "shirtSize",
        "specialNeeds",
        "sex",
        "completeRegistration",
        "country",
        "twitter",
        "labels",
        "extraField",
        "personId",
    )


#: Valid column names of :class:`~icpc.models.StaffTshirtRow`.
type StaffTshirtField = Literal[
    "contestParticipantId",
    "staffMemberId",
    "site",
    "personId",
    "firstName",
    "lastName",
    "username",
    "badgeRole",
    "institution",
    "registrationComplete",
    "shirtSize",
    "tshirts",
]


class StaffTshirtFields:
    """Typed columns of :class:`~icpc.models.StaffTshirtRow`."""

    contest_participant_id: Field[StaffTshirtRow, int] = Field("contestParticipantId")
    staff_member_id: Field[StaffTshirtRow, int] = Field("staffMemberId")
    site: Field[StaffTshirtRow, str] = Field("site")
    person_id: Field[StaffTshirtRow, int] = Field("personId")
    first_name: Field[StaffTshirtRow, str] = Field("firstName")
    last_name: Field[StaffTshirtRow, str] = Field("lastName")
    username: Field[StaffTshirtRow, str] = Field("username")
    badge_role: Field[StaffTshirtRow, str] = Field("badgeRole")
    institution: Field[StaffTshirtRow, str] = Field("institution")
    registration_complete: Field[StaffTshirtRow, bool] = Field("registrationComplete")
    shirt_size: Field[StaffTshirtRow, ShirtSize | str] = Field("shirtSize")
    tshirts: Field[StaffTshirtRow, str] = Field("tshirts")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "site",
        "firstName",
        "lastName",
        "username",
        "badgeRole",
        "institution",
        "registrationComplete",
        "shirtSize",
        "tshirts",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "contestParticipantId",
        "staffMemberId",
        "site",
        "personId",
        "firstName",
        "lastName",
        "username",
        "badgeRole",
        "institution",
        "registrationComplete",
        "shirtSize",
        "tshirts",
    )


#: Valid column names of :class:`~icpc.models.StandingsRow`.
type StandingsField = Literal[
    "id",
    "name",
    "enteredBy",
    "dateEntered",
    "certified",
    "certifiedBy",
    "dateCertified",
    "published",
]


class StandingsFields:
    """Typed columns of :class:`~icpc.models.StandingsRow`."""

    id: Field[StandingsRow, int] = Field("id")
    name: Field[StandingsRow, str] = Field("name")
    entered_by: Field[StandingsRow, str] = Field("enteredBy")
    date_entered: Field[StandingsRow, datetime | str] = Field("dateEntered")
    certified: Field[StandingsRow, bool] = Field("certified")
    certified_by: Field[StandingsRow, str] = Field("certifiedBy")
    date_certified: Field[StandingsRow, datetime | str] = Field("dateCertified")
    published: Field[StandingsRow, bool] = Field("published")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "name",
        "enteredBy",
        "dateEntered",
        "certified",
        "certifiedBy",
        "dateCertified",
        "published",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "id",
        "name",
        "enteredBy",
        "dateEntered",
        "certified",
        "certifiedBy",
        "dateCertified",
        "published",
    )


#: Valid column names of :class:`~icpc.models.TeamMemberRow`.
type TeamMemberField = Literal[
    "id",
    "role",
    "personId",
    "username",
    "firstName",
    "lastName",
    "localName",
    "phone",
    "specialNeeds",
    "sex",
    "completeRegistration",
    "attendingOnsite",
    "dob",
    "shirtSize",
    "country",
    "twitter",
    "teamMemberInstId",
    "teamMemberInstName",
    "areaOfStudy",
    "degreePursued",
    "beganDegree",
    "expectedGrad",
    "includeEmail",
    "employmentOpportunities",
    "informOtherContests",
    "badgeName",
    "certificateName",
    "teamId",
    "teamName",
    "workstationId",
    "teamStatus",
    "teamRank",
    "extraField",
    "labels",
    "teamInstId",
    "teamInstName",
    "teamInstShortName",
    "siteId",
    "siteName",
]


class TeamMemberFields:
    """Typed columns of :class:`~icpc.models.TeamMemberRow`."""

    id: Field[TeamMemberRow, int] = Field("id")
    role: Field[TeamMemberRow, MemberRole | str] = Field("role")
    person_id: Field[TeamMemberRow, int] = Field("personId")
    username: Field[TeamMemberRow, str] = Field("username")
    first_name: Field[TeamMemberRow, str] = Field("firstName")
    last_name: Field[TeamMemberRow, str] = Field("lastName")
    local_name: Field[TeamMemberRow, str] = Field("localName")
    phone: Field[TeamMemberRow, str] = Field("phone")
    special_needs: Field[TeamMemberRow, str] = Field("specialNeeds")
    sex: Field[TeamMemberRow, Sex | str] = Field("sex")
    complete_registration: Field[TeamMemberRow, bool] = Field("completeRegistration")
    attending_onsite: Field[TeamMemberRow, bool] = Field("attendingOnsite")
    dob: Field[TeamMemberRow, date | str] = Field("dob")
    shirt_size: Field[TeamMemberRow, ShirtSize | str] = Field("shirtSize")
    country: Field[TeamMemberRow, str] = Field("country")
    twitter: Field[TeamMemberRow, str] = Field("twitter")
    team_member_inst_id: Field[TeamMemberRow, int] = Field("teamMemberInstId")
    team_member_inst_name: Field[TeamMemberRow, str] = Field("teamMemberInstName")
    area_of_study: Field[TeamMemberRow, str] = Field("areaOfStudy")
    degree_pursued: Field[TeamMemberRow, str] = Field("degreePursued")
    began_degree: Field[TeamMemberRow, date | str] = Field("beganDegree")
    expected_grad: Field[TeamMemberRow, date | str] = Field("expectedGrad")
    include_email: Field[TeamMemberRow, Consent | str] = Field("includeEmail")
    employment_opportunities: Field[TeamMemberRow, Consent | str] = Field("employmentOpportunities")
    inform_other_contests: Field[TeamMemberRow, Consent | str] = Field("informOtherContests")
    badge_name: Field[TeamMemberRow, str] = Field("badgeName")
    certificate_name: Field[TeamMemberRow, str] = Field("certificateName")
    team_id: Field[TeamMemberRow, int] = Field("teamId")
    team_name: Field[TeamMemberRow, str] = Field("teamName")
    workstation_id: Field[TeamMemberRow, int] = Field("workstationId")
    team_status: Field[TeamMemberRow, TeamStatus | str] = Field("teamStatus")
    team_rank: Field[TeamMemberRow, int] = Field("teamRank")
    extra_field: Field[TeamMemberRow, str] = Field("extraField")
    labels: Field[TeamMemberRow, str] = Field("labels")
    team_inst_id: Field[TeamMemberRow, int] = Field("teamInstId")
    team_inst_name: Field[TeamMemberRow, str] = Field("teamInstName")
    team_inst_short_name: Field[TeamMemberRow, str] = Field("teamInstShortName")
    site_id: Field[TeamMemberRow, int] = Field("siteId")
    site_name: Field[TeamMemberRow, str] = Field("siteName")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "username",
        "firstName",
        "lastName",
        "localName",
        "teamInstName",
        "teamName",
        "labels",
        "teamMemberInstName",
        "areaOfStudy",
        "degreePursued",
        "extraField",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "id",
        "role",
        "personId",
        "username",
        "firstName",
        "lastName",
        "localName",
        "phone",
        "specialNeeds",
        "sex",
        "completeRegistration",
        "attendingOnsite",
        "dob",
        "shirtSize",
        "country",
        "twitter",
        "teamMemberInstId",
        "teamMemberInstName",
        "areaOfStudy",
        "degreePursued",
        "beganDegree",
        "expectedGrad",
        "includeEmail",
        "employmentOpportunities",
        "informOtherContests",
        "badgeName",
        "certificateName",
        "teamId",
        "teamName",
        "workstationId",
        "teamStatus",
        "teamRank",
        "extraField",
        "labels",
        "teamInstId",
        "teamInstName",
        "teamInstShortName",
        "siteId",
        "siteName",
    )


#: Valid column names of :class:`~icpc.models.TeamRow`.
type TeamField = Literal[
    "id",
    "name",
    "teamMembers",
    "status",
    "extendedState",
    "paid",
    "note",
    "checkIn",
    "workstationId",
    "rank",
    "certified",
    "eligibilityStatus",
    "eligibilityIssue",
    "eligibilityComment",
    "instId",
    "instName",
    "instShortName",
    "instAddress",
    "city",
    "country",
    "a2",
    "site",
    "createdWhen",
    "extraField",
]


class TeamFields:
    """Typed columns of :class:`~icpc.models.TeamRow`."""

    id: Field[TeamRow, int] = Field("id")
    name: Field[TeamRow, str] = Field("name")
    team_members: Field[TeamRow, str] = Field("teamMembers")
    status: Field[TeamRow, TeamStatus | str] = Field("status")
    extended_state: Field[TeamRow, str] = Field("extendedState")
    paid: Field[TeamRow, bool] = Field("paid")
    note: Field[TeamRow, str] = Field("note")
    check_in: Field[TeamRow, str] = Field("checkIn")
    workstation_id: Field[TeamRow, int] = Field("workstationId")
    rank: Field[TeamRow, int] = Field("rank")
    certified: Field[TeamRow, bool] = Field("certified")
    eligibility_status: Field[TeamRow, EligibilityStatus | str] = Field("eligibilityStatus")
    eligibility_issue: Field[TeamRow, str] = Field("eligibilityIssue")
    eligibility_comment: Field[TeamRow, str] = Field("eligibilityComment")
    inst_id: Field[TeamRow, int] = Field("instId")
    inst_name: Field[TeamRow, str] = Field("instName")
    inst_short_name: Field[TeamRow, str] = Field("instShortName")
    inst_address: Field[TeamRow, str] = Field("instAddress")
    city: Field[TeamRow, str] = Field("city")
    country: Field[TeamRow, str] = Field("country")
    a2: Field[TeamRow, str] = Field("a2")
    site: Field[TeamRow, str] = Field("site")
    created_when: Field[TeamRow, datetime | str] = Field("createdWhen")
    extra_field: Field[TeamRow, str] = Field("extraField")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "id",
        "name",
        "status",
        "certified",
        "instName",
        "instAddress",
        "city",
        "country",
        "site",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "id",
        "name",
        "teamMembers",
        "status",
        "extendedState",
        "paid",
        "note",
        "checkIn",
        "workstationId",
        "rank",
        "certified",
        "eligibilityStatus",
        "eligibilityIssue",
        "eligibilityComment",
        "instId",
        "instName",
        "instShortName",
        "instAddress",
        "city",
        "country",
        "a2",
        "site",
        "createdWhen",
        "extraField",
    )


#: Valid column names of :class:`~icpc.models.TeamSummaryRow`.
type TeamSummaryField = Literal[
    "teamId",
    "teamName",
    "rank",
    "siteId",
    "siteName",
    "country",
    "a2",
    "instId",
    "instName",
    "coachId",
    "coachName",
    "promotedFromTeamId",
    "promotedFromTeamName",
    "promotedFromContestId",
    "promotedFromContestName",
    "created",
    "status",
    "eligibilityId",
    "eligibilityStatus",
    "certified",
    "paid",
    "extendedState",
]


class TeamSummaryFields:
    """Typed columns of :class:`~icpc.models.TeamSummaryRow`."""

    team_id: Field[TeamSummaryRow, int] = Field("teamId")
    team_name: Field[TeamSummaryRow, str] = Field("teamName")
    rank: Field[TeamSummaryRow, int] = Field("rank")
    site_id: Field[TeamSummaryRow, int] = Field("siteId")
    site_name: Field[TeamSummaryRow, str] = Field("siteName")
    country: Field[TeamSummaryRow, str] = Field("country")
    a2: Field[TeamSummaryRow, str] = Field("a2")
    inst_id: Field[TeamSummaryRow, int] = Field("instId")
    inst_name: Field[TeamSummaryRow, str] = Field("instName")
    coach_id: Field[TeamSummaryRow, int] = Field("coachId")
    coach_name: Field[TeamSummaryRow, str] = Field("coachName")
    promoted_from_team_id: Field[TeamSummaryRow, int] = Field("promotedFromTeamId")
    promoted_from_team_name: Field[TeamSummaryRow, str] = Field("promotedFromTeamName")
    promoted_from_contest_id: Field[TeamSummaryRow, int] = Field("promotedFromContestId")
    promoted_from_contest_name: Field[TeamSummaryRow, str] = Field("promotedFromContestName")
    created: Field[TeamSummaryRow, datetime | str] = Field("created")
    status: Field[TeamSummaryRow, TeamStatus | str] = Field("status")
    eligibility_id: Field[TeamSummaryRow, int] = Field("eligibilityId")
    eligibility_status: Field[TeamSummaryRow, EligibilityStatus | str] = Field("eligibilityStatus")
    certified: Field[TeamSummaryRow, bool] = Field("certified")
    paid: Field[TeamSummaryRow, bool] = Field("paid")
    extended_state: Field[TeamSummaryRow, str] = Field("extendedState")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "teamId",
        "teamName",
        "rank",
        "siteName",
        "country",
        "instName",
        "coachName",
        "promotedFromTeamName",
        "promotedFromContestName",
        "created",
        "status",
        "eligibilityStatus",
        "certified",
        "paid",
        "extendedState",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "teamId",
        "teamName",
        "rank",
        "siteId",
        "siteName",
        "country",
        "a2",
        "instId",
        "instName",
        "coachId",
        "coachName",
        "promotedFromTeamId",
        "promotedFromTeamName",
        "promotedFromContestId",
        "promotedFromContestName",
        "created",
        "status",
        "eligibilityId",
        "eligibilityStatus",
        "certified",
        "paid",
        "extendedState",
    )


#: Valid column names of :class:`~icpc.models.Top20Row`.
type Top20Field = Literal[
    "area",
    "contest",
    "contestId",
    "rank",
    "team",
    "teamId",
    "role",
    "institution",
    "instId",
    "firstName",
    "lastName",
    "username",
    "userId",
    "inform",
]


class Top20Fields:
    """Typed columns of :class:`~icpc.models.Top20Row`."""

    area: Field[Top20Row, str] = Field("area")
    contest: Field[Top20Row, str] = Field("contest")
    contest_id: Field[Top20Row, int] = Field("contestId")
    rank: Field[Top20Row, int] = Field("rank")
    team: Field[Top20Row, str] = Field("team")
    team_id: Field[Top20Row, int] = Field("teamId")
    role: Field[Top20Row, str] = Field("role")
    institution: Field[Top20Row, str] = Field("institution")
    inst_id: Field[Top20Row, int] = Field("instId")
    first_name: Field[Top20Row, str] = Field("firstName")
    last_name: Field[Top20Row, str] = Field("lastName")
    username: Field[Top20Row, str] = Field("username")
    user_id: Field[Top20Row, int] = Field("userId")
    inform: Field[Top20Row, Consent | str] = Field("inform")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "area",
        "contest",
        "contestId",
        "rank",
        "team",
        "teamId",
        "role",
        "institution",
        "instId",
        "firstName",
        "lastName",
        "username",
        "userId",
        "inform",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "area",
        "contest",
        "contestId",
        "rank",
        "team",
        "teamId",
        "role",
        "institution",
        "instId",
        "firstName",
        "lastName",
        "username",
        "userId",
        "inform",
    )


#: Valid column names of :class:`~icpc.models.TransportationMissingRow`.
type TransportationMissingField = Literal[
    "personId",
    "firstName",
    "lastName",
    "attendingOnsite",
    "countryName",
    "countryA2",
    "email",
    "modifiedWhen",
    "participantId",
    "siteName",
    "coach",
]


class TransportationMissingFields:
    """Typed columns of :class:`~icpc.models.TransportationMissingRow`."""

    person_id: Field[TransportationMissingRow, int] = Field("personId")
    first_name: Field[TransportationMissingRow, str] = Field("firstName")
    last_name: Field[TransportationMissingRow, str] = Field("lastName")
    attending_onsite: Field[TransportationMissingRow, bool] = Field("attendingOnsite")
    country_name: Field[TransportationMissingRow, str] = Field("countryName")
    country_a2: Field[TransportationMissingRow, str] = Field("countryA2")
    email: Field[TransportationMissingRow, str] = Field("email")
    modified_when: Field[TransportationMissingRow, datetime | str] = Field("modifiedWhen")
    participant_id: Field[TransportationMissingRow, int] = Field("participantId")
    site_name: Field[TransportationMissingRow, str] = Field("siteName")
    coach: Field[TransportationMissingRow, bool] = Field("coach")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "countryName",
        "firstName",
        "lastName",
        "email",
        "attendingOnsite",
        "modifiedWhen",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "personId",
        "firstName",
        "lastName",
        "attendingOnsite",
        "countryName",
        "countryA2",
        "email",
        "modifiedWhen",
        "participantId",
        "siteName",
        "coach",
    )


#: Valid column names of :class:`~icpc.models.TshirtRow`.
type TshirtField = Literal[
    "institution",
    "personName",
    "teamName",
    "tshirtSize",
]


class TshirtFields:
    """Typed columns of :class:`~icpc.models.TshirtRow`."""

    institution: Field[TshirtRow, str] = Field("institution")
    person_name: Field[TshirtRow, str] = Field("personName")
    team_name: Field[TshirtRow, str] = Field("teamName")
    tshirt_size: Field[TshirtRow, ShirtSize | str] = Field("tshirtSize")

    #: Columns the icpc.global grid projects by default.
    default_proj: tuple[str, ...] = (
        "personName",
        "tshirtSize",
        "institution",
        "teamName",
    )

    #: Every column this endpoint accepts.
    all_fields: tuple[str, ...] = (
        "institution",
        "personName",
        "teamName",
        "tshirtSize",
    )


def contest_teams(contest_id: int) -> SearchEndpoint[TeamRow, TeamFields]:
    """Teams registered for a contest.

    ``/contest/search/contest/{contest_id}/team``
    """
    return SearchEndpoint(
        path=f"/contest/search/contest/{contest_id}/team",
        row=TeamRow,
        fields=TeamFields(),
        default_proj=TeamFields.default_proj,
        all_fields=TeamFields.all_fields,
        name="contest_teams",
    )


def site_teams(site_id: int) -> SearchEndpoint[TeamRow, TeamFields]:
    """Teams registered for one site of a contest.

    ``/contest/search/site/{site_id}/teams``
    """
    return SearchEndpoint(
        path=f"/contest/search/site/{site_id}/teams",
        row=TeamRow,
        fields=TeamFields(),
        default_proj=TeamFields.default_proj,
        all_fields=TeamFields.all_fields,
        name="site_teams",
    )


def contest_team_members(contest_id: int) -> SearchEndpoint[TeamMemberRow, TeamMemberFields]:
    """Every team member in a contest, one row per membership.

    ``/contest/search/contest/{contest_id}/teammember``
    """
    return SearchEndpoint(
        path=f"/contest/search/contest/{contest_id}/teammember",
        row=TeamMemberRow,
        fields=TeamMemberFields(),
        default_proj=TeamMemberFields.default_proj,
        all_fields=TeamMemberFields.all_fields,
        name="contest_team_members",
    )


def site_team_members(site_id: int) -> SearchEndpoint[TeamMemberRow, TeamMemberFields]:
    """Every team member at one site.

    ``/contest/search/site/{site_id}/teammember``
    """
    return SearchEndpoint(
        path=f"/contest/search/site/{site_id}/teammember",
        row=TeamMemberRow,
        fields=TeamMemberFields(),
        default_proj=TeamMemberFields.default_proj,
        all_fields=TeamMemberFields.all_fields,
        name="site_team_members",
    )


def contest_institutions(contest_id: int) -> SearchEndpoint[InstitutionRow, InstitutionFields]:
    """Institutions with at least one team in a contest.

    ``/contest/search/contest/{contest_id}/institution``
    """
    return SearchEndpoint(
        path=f"/contest/search/contest/{contest_id}/institution",
        row=InstitutionRow,
        fields=InstitutionFields(),
        default_proj=InstitutionFields.default_proj,
        all_fields=InstitutionFields.all_fields,
        name="contest_institutions",
    )


def site_institutions(site_id: int) -> SearchEndpoint[InstitutionRow, InstitutionFields]:
    """Institutions with at least one team at a site.

    ``/contest/search/site/{site_id}/institutions``
    """
    return SearchEndpoint(
        path=f"/contest/search/site/{site_id}/institutions",
        row=InstitutionRow,
        fields=InstitutionFields(),
        default_proj=InstitutionFields.default_proj,
        all_fields=InstitutionFields.all_fields,
        name="site_institutions",
    )


def contest_participants(
    contest_id: int,
) -> SearchEndpoint[ContestParticipantRow, ContestParticipantFields]:
    """Every person at a contest, with travel and visa detail. The widest DTO here.

    ``/contest/search/contest/{contest_id}/contestparticipant``
    """
    return SearchEndpoint(
        path=f"/contest/search/contest/{contest_id}/contestparticipant",
        row=ContestParticipantRow,
        fields=ContestParticipantFields(),
        default_proj=ContestParticipantFields.default_proj,
        all_fields=ContestParticipantFields.all_fields,
        name="contest_participants",
    )


def site_participants(
    site_id: int,
) -> SearchEndpoint[ContestParticipantRow, ContestParticipantFields]:
    """Every person at one site.

    ``/contest/search/site/{site_id}/contestparticipant``
    """
    return SearchEndpoint(
        path=f"/contest/search/site/{site_id}/contestparticipant",
        row=ContestParticipantRow,
        fields=ContestParticipantFields(),
        default_proj=ContestParticipantFields.default_proj,
        all_fields=ContestParticipantFields.all_fields,
        name="site_participants",
    )


def contest_staff(contest_id: int) -> SearchEndpoint[StaffRow, StaffFields]:
    """Contest staff, from the contest grid.

    ``/contest/search/contest/{contest_id}/staff``
    """
    return SearchEndpoint(
        path=f"/contest/search/contest/{contest_id}/staff",
        row=StaffRow,
        fields=StaffFields(),
        default_proj=StaffFields.default_proj,
        all_fields=StaffFields.all_fields,
        name="contest_staff",
    )


def contest_top20(contest_id: int) -> SearchEndpoint[Top20Row, Top20Fields]:
    """Top-20 participants of a contest.

    ``/contest/search/contest/{contest_id}/top20``
    """
    return SearchEndpoint(
        path=f"/contest/search/contest/{contest_id}/top20",
        row=Top20Row,
        fields=Top20Fields(),
        default_proj=Top20Fields.default_proj,
        all_fields=Top20Fields.all_fields,
        name="contest_top20",
    )


def contest_team_summaries(contest_id: int) -> SearchEndpoint[TeamSummaryRow, TeamSummaryFields]:
    """Teams of a contest in the alternate shape used by the team grid: ``teamId``/``teamName`` rather than ``id``/``name``, plus promotion history.

    ``/team/search/{contest_id}/all``
    """
    return SearchEndpoint(
        path=f"/team/search/{contest_id}/all",
        row=TeamSummaryRow,
        fields=TeamSummaryFields(),
        default_proj=TeamSummaryFields.default_proj,
        all_fields=TeamSummaryFields.all_fields,
        name="contest_team_summaries",
    )


def site_home_teams(site_id: int) -> SearchEndpoint[TeamSummaryRow, TeamSummaryFields]:
    """Teams of a site in the alternate team shape.

    ``/contest/search/site/{site_id}/home/teams``
    """
    return SearchEndpoint(
        path=f"/contest/search/site/{site_id}/home/teams",
        row=TeamSummaryRow,
        fields=TeamSummaryFields(),
        default_proj=TeamSummaryFields.default_proj,
        all_fields=TeamSummaryFields.all_fields,
        name="site_home_teams",
    )


def contest_promote_candidates(contest_id: int) -> SearchEndpoint[PromoteRow, PromoteFields]:
    """Teams eligible to be promoted out of a contest.

    ``/team/search/{contest_id}/promote``
    """
    return SearchEndpoint(
        path=f"/team/search/{contest_id}/promote",
        row=PromoteRow,
        fields=PromoteFields(),
        default_proj=PromoteFields.default_proj,
        all_fields=PromoteFields.all_fields,
        name="contest_promote_candidates",
    )


def contest_staff_members(contest_id: int) -> SearchEndpoint[StaffMemberRow, StaffMemberFields]:
    """Staff members of a contest, from the staff administration grid.

    ``/contest/staffmember/contest/{contest_id}/search``
    """
    return SearchEndpoint(
        path=f"/contest/staffmember/contest/{contest_id}/search",
        row=StaffMemberRow,
        fields=StaffMemberFields(),
        default_proj=StaffMemberFields.default_proj,
        all_fields=StaffMemberFields.all_fields,
        name="contest_staff_members",
    )


def contest_public_staff_members(
    contest_id: int,
) -> SearchEndpoint[StaffMemberRow, StaffMemberFields]:
    """Staff members flagged for the contest's public pages.

    ``/contest/staffmember/contest/{contest_id}/public/search``
    """
    return SearchEndpoint(
        path=f"/contest/staffmember/contest/{contest_id}/public/search",
        row=StaffMemberRow,
        fields=StaffMemberFields(),
        default_proj=StaffMemberFields.default_proj,
        all_fields=StaffMemberFields.all_fields,
        name="contest_public_staff_members",
    )


def contest_staff_funding(contest_id: int) -> SearchEndpoint[StaffFundingRow, StaffFundingFields]:
    """Staff funding and budget rows.

    ``/contest/staffMember/funding/contest/{contest_id}/search``
    """
    return SearchEndpoint(
        path=f"/contest/staffMember/funding/contest/{contest_id}/search",
        row=StaffFundingRow,
        fields=StaffFundingFields(),
        default_proj=StaffFundingFields.default_proj,
        all_fields=StaffFundingFields.all_fields,
        name="contest_staff_funding",
    )


def contest_staff_tshirts(contest_id: int) -> SearchEndpoint[StaffTshirtRow, StaffTshirtFields]:
    """Staff t-shirt sizes.

    ``/contest/staffmember/tshirt/contest/{contest_id}/search``
    """
    return SearchEndpoint(
        path=f"/contest/staffmember/tshirt/contest/{contest_id}/search",
        row=StaffTshirtRow,
        fields=StaffTshirtFields(),
        default_proj=StaffTshirtFields.default_proj,
        all_fields=StaffTshirtFields.all_fields,
        name="contest_staff_tshirts",
    )


def contest_standings(contest_id: int) -> SearchEndpoint[StandingsRow, StandingsFields]:
    """Uploaded standings documents for a contest (not the results themselves).

    ``/contest/standings/contest/{contest_id}/search``
    """
    return SearchEndpoint(
        path=f"/contest/standings/contest/{contest_id}/search",
        row=StandingsRow,
        fields=StandingsFields(),
        default_proj=StandingsFields.default_proj,
        all_fields=StandingsFields.all_fields,
        name="contest_standings",
    )


def contest_team_certificates(contest_id: int) -> SearchEndpoint[CertificateRow, CertificateFields]:
    """Team certificates issued for a contest.

    ``/contest/certificate/team/contest/{contest_id}/search``
    """
    return SearchEndpoint(
        path=f"/contest/certificate/team/contest/{contest_id}/search",
        row=CertificateRow,
        fields=CertificateFields(),
        default_proj=CertificateFields.default_proj,
        all_fields=CertificateFields.all_fields,
        name="contest_team_certificates",
    )


def contest_staff_certificates(
    contest_id: int,
) -> SearchEndpoint[CertificateRow, CertificateFields]:
    """Staff certificates issued for a contest.

    ``/contest/certificate/staff/contest/{contest_id}/search``
    """
    return SearchEndpoint(
        path=f"/contest/certificate/staff/contest/{contest_id}/search",
        row=CertificateRow,
        fields=CertificateFields(),
        default_proj=CertificateFields.default_proj,
        all_fields=CertificateFields.all_fields,
        name="contest_staff_certificates",
    )


def site_team_certificates(site_id: int) -> SearchEndpoint[CertificateRow, CertificateFields]:
    """Team certificates issued for one site.

    ``/contest/certificate/site/team/site/{site_id}/search``
    """
    return SearchEndpoint(
        path=f"/contest/certificate/site/team/site/{site_id}/search",
        row=CertificateRow,
        fields=CertificateFields(),
        default_proj=CertificateFields.default_proj,
        all_fields=CertificateFields.all_fields,
        name="site_team_certificates",
    )


def contest_missing_transportation(
    contest_id: int,
) -> SearchEndpoint[TransportationMissingRow, TransportationMissingFields]:
    """People who have not filled in their travel details.

    ``/contest/transportation/search/contest/{contest_id}/missing``
    """
    return SearchEndpoint(
        path=f"/contest/transportation/search/contest/{contest_id}/missing",
        row=TransportationMissingRow,
        fields=TransportationMissingFields(),
        default_proj=TransportationMissingFields.default_proj,
        all_fields=TransportationMissingFields.all_fields,
        name="contest_missing_transportation",
    )


def site_coach_tshirts(site_id: int) -> SearchEndpoint[TshirtRow, TshirtFields]:
    """Coach t-shirt sizes at a site.

    ``/contest/search/site/{site_id}/tshirt/coaches``
    """
    return SearchEndpoint(
        path=f"/contest/search/site/{site_id}/tshirt/coaches",
        row=TshirtRow,
        fields=TshirtFields(),
        default_proj=TshirtFields.default_proj,
        all_fields=TshirtFields.all_fields,
        name="site_coach_tshirts",
    )


def site_cocoach_tshirts(site_id: int) -> SearchEndpoint[TshirtRow, TshirtFields]:
    """Co-coach t-shirt sizes at a site.

    ``/contest/search/site/{site_id}/tshirt/cocoaches``
    """
    return SearchEndpoint(
        path=f"/contest/search/site/{site_id}/tshirt/cocoaches",
        row=TshirtRow,
        fields=TshirtFields(),
        default_proj=TshirtFields.default_proj,
        all_fields=TshirtFields.all_fields,
        name="site_cocoach_tshirts",
    )


def site_contestant_tshirts(site_id: int) -> SearchEndpoint[TshirtRow, TshirtFields]:
    """Contestant t-shirt sizes at a site.

    ``/contest/search/site/{site_id}/tshirt/contestants``
    """
    return SearchEndpoint(
        path=f"/contest/search/site/{site_id}/tshirt/contestants",
        row=TshirtRow,
        fields=TshirtFields(),
        default_proj=TshirtFields.default_proj,
        all_fields=TshirtFields.all_fields,
        name="site_contestant_tshirts",
    )
