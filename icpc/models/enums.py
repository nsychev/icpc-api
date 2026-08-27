"""Wire enumerations.

Server returns these lists from the ``/aspectfaces`` form registry. Model fields
are typed ``Enum | str`` so that unrecognised values arrive as strings.
"""

from __future__ import annotations

from enum import StrEnum

__all__ = [
    "Consent",
    "ContestType",
    "EligibilityStatus",
    "ExportType",
    "InstitutionUnitType",
    "MemberRole",
    "ParticipantRole",
    "PublicPagesVisibility",
    "Sex",
    "ShirtSize",
    "TeamStatus",
    "Title",
    "coach_roles",
    "contestant_roles",
]


class TeamStatus(StrEnum):
    """Team registration status. Complete, from ``…team.businessobjects.Team``.

    The frontend labels the third one "Rejected"; the wire value is ``CANCELED``.
    """

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    CANCELED = "CANCELED"


class MemberRole(StrEnum):
    """A person's role on a team, from ``…team.businessobjects.TeamMember``."""

    COACH = "COACH"
    COCOACH = "COCOACH"
    #: A contestant who also coaches: counted as *both* a contestant and a coach.
    CONTESTANT_COACH = "CONTESTANT_COACH"
    CONTESTANT = "CONTESTANT"
    ATTENDEE = "ATTENDEE"
    RESERVE = "RESERVE"
    STAFF = "STAFF"
    #: Not in the server's current option list, but older contests may still
    #: carry it. Treated like ``CONTESTANT_COACH``: both a contestant and a coach.
    STUDENT_COACH = "STUDENT_COACH"


class ParticipantRole(StrEnum):
    """A person's role at a contest, independent of any team."""

    CONTESTANT = "CONTESTANT"
    COACH = "COACH"
    COCOACH = "COCOACH"
    RESERVE = "RESERVE"
    ATTENDEE = "ATTENDEE"
    STAFF = "STAFF"


class Consent(StrEnum):
    """A registration consent answer.

    Several columns read like booleans — ``includeEmail``,
    ``employmentOpportunities``, ``informOtherContests``, ``inform``, ``icpcRules``,
    ``mediaUse`` — but the wire carries words, so ``bool`` simply fails to parse.
    Complete, from ``…person.businessobjects.PersonInfoAbstract``.
    """

    AGREE = "AGREE"
    DISAGREE = "DISAGREE"


class Sex(StrEnum):
    """Complete, from ``…person.businessobjects.PersonInfoAbstract``."""

    FEMALE = "FEMALE"
    MALE = "MALE"


class EligibilityStatus(StrEnum):
    """Eligibility verdict on a team.

    Complete, from ``…team.businessobjects.Eligibility``. A full-object team write
    recomputes this and drops any ``VERIFIED_*`` value.
    """

    NOT_RESOLVED = "NOT_RESOLVED"
    NO_ISSUES_FOUND = "NO_ISSUES_FOUND"
    PREDICTED_INELIGIBLE = "PREDICTED_INELIGIBLE"
    VERIFIED_ELIGIBLE = "VERIFIED_ELIGIBLE"
    VERIFIED_INELIGIBLE = "VERIFIED_INELIGIBLE"
    ELIGIBILITY_CHECK_NOT_REQUIRED = "ELIGIBILITY_CHECK_NOT_REQUIRED"
    VALIDATED_BY_LOWER_CONTEST = "VALIDATED_BY_LOWER_CONTEST"


class ContestType(StrEnum):
    """Complete, from ``…contest.businessobjects.ContestSettings``."""

    WORLD_FINALS = "WORLD_FINALS"
    REGIONALS = "REGIONALS"
    QUALIFIER = "QUALIFIER"
    PRACTICE = "PRACTICE"
    CAMP = "CAMP"


class PublicPagesVisibility(StrEnum):
    """Whether a contest's public pages list people. Not a boolean, despite the name.

    Complete, from ``…contest.businessobjects.ContestSettings``.
    """

    WITH_PEOPLE = "WITH_PEOPLE"
    WITHOUT_PEOPLE = "WITHOUT_PEOPLE"


class Title(StrEnum):
    """Complete, from ``…person.businessobjects.PersonInfoAbstract``."""

    DR = "DR"
    DRS = "DRS"
    IR = "IR"
    MISS = "MISS"
    MR = "MR"
    MRS = "MRS"
    MS = "MS"
    PROFESSOR = "PROFESSOR"
    NONE = "NONE"


class InstitutionUnitType(StrEnum):
    """What kind of institution a unit is.

    Observed values only: the ``InstitutionUnit`` schema endpoint answers 500.
    """

    UNIVERSITY_GRADUATE = "UNIVERSITY_GRADUATE"
    UNIVERSITY_NO_GRADUATE = "UNIVERSITY_NO_GRADUATE"
    HIGH_SCHOOL = "HIGH_SCHOOL"


class ShirtSize(StrEnum):
    """Complete, from ``…person.businessobjects.PersonInfoAbstract``."""

    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"
    XXXL = "XXXL"
    XXXXL = "XXXXL"
    XXXXXL = "XXXXXL"


class ExportType(StrEnum):
    """Formats accepted by the ``/export`` sibling of a search endpoint."""

    CSV = "CSV"
    TSV = "TSV"
    TAB = "TAB"
    TXT = "TXT"
    EXCEL = "EXCEL"


def contestant_roles() -> frozenset[str]:
    """Roles that count as competing."""
    return frozenset(
        {
            MemberRole.CONTESTANT,
            MemberRole.STUDENT_COACH,
            MemberRole.CONTESTANT_COACH,
        }
    )


def coach_roles() -> frozenset[str]:
    """Roles that count as coaching."""
    return frozenset(
        {
            MemberRole.COACH,
            MemberRole.COCOACH,
            MemberRole.STUDENT_COACH,
            MemberRole.CONTESTANT_COACH,
        }
    )
