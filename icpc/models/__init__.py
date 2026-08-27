"""Typed wire models: generated search rows plus hand-written entity DTOs."""

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
from icpc.models.base import Row
from icpc.models.blobs import TeamMemberBlob, parse_extra_fields, parse_members
from icpc.models.common import FileRef, NamedRef
from icpc.models.enums import (
    ExportType,
    MemberRole,
    ParticipantRole,
    TeamStatus,
    coach_roles,
    contestant_roles,
)

__all__ = [
    "CertificateRow",
    "ContestParticipantRow",
    "ExportType",
    "FileRef",
    "InstitutionRow",
    "MemberRole",
    "NamedRef",
    "ParticipantRole",
    "PromoteRow",
    "Row",
    "StaffFundingRow",
    "StaffMemberRow",
    "StaffRow",
    "StaffTshirtRow",
    "StandingsRow",
    "TeamMemberBlob",
    "TeamMemberRow",
    "TeamRow",
    "TeamStatus",
    "TeamSummaryRow",
    "Top20Row",
    "TransportationMissingRow",
    "TshirtRow",
    "coach_roles",
    "contestant_roles",
    "parse_extra_fields",
    "parse_members",
]
