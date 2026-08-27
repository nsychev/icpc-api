"""Base model shared by every DTO and search row.

Two facts about this API drive the configuration:

* ``proj:`` does not shape the response — the full DTO always comes back with the
  unprojected fields set to ``null``. So every field of a *search row* is
  optional, always. The non-search endpoints in :mod:`icpc.models.entities` take
  no projection, and the handful of fields observed never to be null there are
  declared required; see that module.
* The frontend redeploys often and adds columns. ``extra="allow"`` means a new
  server-side field lands in ``model_extra`` instead of breaking the parse.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

__all__ = ["Row"]


class Row(BaseModel):
    """A wire object: camelCase on the wire, snake_case in Python."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="allow",
        # Search rows are decoded a thousand at a time; skip re-validating models.
        revalidate_instances="never",
    )

    def extra(self, name: str) -> Any:
        """Read a field the server sent but this version of the SDK doesn't know."""
        return (self.model_extra or {}).get(name)

    def unknown_fields(self) -> dict[str, Any]:
        """Fields present on the wire but absent from the model."""
        return dict(self.model_extra or {})
