from __future__ import annotations

import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NodeId:
    """Typed identity for a node."""

    value: str

    def __post_init__(self) -> None:
        if not bool(self.value):
            raise ValueError("NodeId cannot be empty.")

    @classmethod
    def new(cls) -> NodeId:
        """Create a new `NodeId` with a UUID4 backing."""

        return cls(f"n_{uuid.uuid4()}")

    @classmethod
    def from_str(cls, s: str) -> NodeId:
        """Create a `NodeId` from an existing string (e.g., when loading)."""

        return cls(s)

    def __str__(self) -> str:
        """Return the string representation of the `NodeId`."""

        return self.value
