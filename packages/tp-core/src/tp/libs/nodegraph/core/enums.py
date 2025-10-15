from __future__ import annotations

from enum import Enum


class PortDirection(str, Enum):
    """Direction of a port on a node."""

    In = "in"
    Out = "out"

    def opposite(self) -> PortDirection:
        """Return in the opposite direction."""

        return PortDirection.Out if self is PortDirection.In else PortDirection.In


class PortKind(str, Enum):
    """Semantic kind of a port.

    Data: carries typed data payloads.
    Exec: carries execution/control flow (no data payload).
    """

    Data = "data"
    Exec = "exec"
