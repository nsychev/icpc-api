"""The site-wide institution grid: every institution, not only those with teams."""

from __future__ import annotations

from icpc.models import InstitutionRow
from icpc.search._generated import InstitutionFields
from icpc.search.endpoint import SearchEndpoint

__all__ = ["institutions"]


def institutions() -> SearchEndpoint[InstitutionRow, InstitutionFields]:
    """List of institutions.

    ``/common/institution/search``

    Same columns as :func:`~icpc.search.contest_institutions`. ``instId`` is the
    id :func:`icpc.api.common.institution` takes; ``instUnitId`` is the one
    :func:`icpc.api.common.institution_unit` takes.
    """
    return SearchEndpoint(
        path="/common/institution/search",
        row=InstitutionRow,
        fields=InstitutionFields(),
        # The grid's own defaults, plus instId: without it a row cannot be edited.
        default_proj=(
            "instId",
            "instName",
            "instUnitId",
            "instUnitNativeName",
            "instUnitShortName",
            "instUnitAbbreviation",
            "instUnitHomepageUrl",
            "city",
            "countryName",
        ),
        all_fields=InstitutionFields.all_fields,
        name="institutions",
        export_path="/common/institution/export",
    )
