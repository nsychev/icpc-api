"""Small DTOs that appear across many endpoints."""

from __future__ import annotations

import base64
import binascii

from icpc.models.base import Row

__all__ = ["Country", "FileRef", "NamedRef"]


class Country(Row):
    """A country, as the person endpoints embed it.

    Only the person endpoints send this object; the search grids flatten the
    same thing to a bare name and are typed ``str`` there.
    """

    id: int
    version: int
    name: str
    #: ISO 3166-1 alpha-2, e.g. ``KZ``.
    a2: str | None = None
    #: ISO 3166-1 alpha-3, e.g. ``KAZ``.
    a3: str | None = None
    #: ISO 3166-1 numeric.
    number: int | None = None
    currency: str | None = None
    available: bool | None = None


class FileRef(Row):
    """The generic file envelope: exports, certificates, photos, resumes.

    Whether the payload arrives inline in :attr:`data` or has to be fetched from
    :attr:`url` varies by endpoint; :meth:`content` handles the inline case.
    """

    file_name: str | None = None
    mime: str | None = None
    #: Base64 payload, when the server inlines it.
    data: str | None = None
    url: str | None = None

    def content(self) -> bytes | None:
        """Decode :attr:`data`, or ``None`` if there is nothing inline to decode."""
        if not self.data:
            return None
        try:
            return base64.b64decode(self.data, validate=True)
        except (binascii.Error, ValueError):
            # Some endpoints inline plain text rather than base64.
            return self.data.encode()


class NamedRef(Row):
    """``{"id": …, "name": …}`` — how contests, sites and institutions are embedded."""

    id: int
    name: str
