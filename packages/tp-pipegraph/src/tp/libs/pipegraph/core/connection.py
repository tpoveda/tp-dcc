"""Connection class for linking ports.

Connections represent data flow between output and input ports.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Connection:
    """Immutable connection between an output port and an input port.

    Connections are directional: data flows from source (output) to target (input).
    Connections are identified by their source and target port IDs.
    """

    source_port_id: UUID
    target_port_id: UUID

    def __hash__(self) -> int:
        """Hash based on source and target port IDs.

        Returns:
            The hash value.
        """

        return hash((self.source_port_id, self.target_port_id))

    def __eq__(self, other: object) -> bool:
        """Two connections are equal if they connect the same ports.

        Args:
            other: The object to compare against.

        Returns:
            `True` if the connections are equal; `False` otherwise.
        """

        if not isinstance(other, Connection):
            return NotImplemented
        return (
            self.source_port_id == other.source_port_id
            and self.target_port_id == other.target_port_id
        )

    def __repr__(self) -> str:
        """Return a string representation of the connection."""

        return f"Connection({self.source_port_id!s:.8} -> {self.target_port_id!s:.8})"

    @property
    def id(self) -> UUID:
        """Deterministic ID based on source and target."""

        combined = f"{self.source_port_id}:{self.target_port_id}"
        return UUID(bytes=combined.encode()[:16].ljust(16, b"\x00"), version=4)

    def involves_port(self, port_id: UUID) -> bool:
        """Check if this connection involves a specific port.

        Args:
            port_id: The port ID to check.

        Returns:
            `True` if the connection involves the port; `False` otherwise.
        """

        return self.source_port_id == port_id or self.target_port_id == port_id

    def involves_ports(self, port_ids: set[UUID]) -> bool:
        """Check if this connection involves any of the given ports.

        Args:
            port_ids: The port IDs to check.

        Returns:
            `True` if the connection involves any of the given ports; `False` otherwise.
        """

        return (
            self.source_port_id in port_ids or self.target_port_id in port_ids
        )

    def reversed(self) -> Connection:
        """Create a reversed connection (for undoing).

        Notes:
            This is typically invalid as it swaps input/output, but useful
                for some internal operations.
        """

        return Connection(
            source_port_id=self.target_port_id,
            target_port_id=self.source_port_id,
        )
