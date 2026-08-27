"""Low-level endpoints.

Each function is pure: it builds an :class:`~icpc.transport.operation.Operation`
and performs no I/O. Send one with ``client.send(...)``::

    from icpc import Icpc
    from icpc.api import team

    with Icpc.from_store() as icpc:
        roster = icpc.send(team.members(1234567))

Not all endpoints are wrapped here. Please fill an issue for missing ones or use
`icpc raw`.
"""

from icpc.api import common, contest, person, public, staff, team

__all__ = ["common", "contest", "person", "public", "staff", "team"]
