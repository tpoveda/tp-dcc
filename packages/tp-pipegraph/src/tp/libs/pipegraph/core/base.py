"""Base classes and common types for PipeGraph.

Provides foundational abstractions used throughout the system.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass
class Identifiable:
    """Base class for all entities with a unique identifier.

    Provides a UUID-based identity that persists across serialization.
    All domain objects (Graph, Node, Port, Connection, Variable) inherit from this.
    """

    id: UUID = field(default_factory=uuid4, kw_only=True)

    def __hash__(self) -> int:
        """Hash based on ID for use in sets and dicts.

        Returns:
            Hash value of the object's ID.
        """

        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        """Equality based on ID.

        Args:
            other: The object to compare against.

        Returns:
            `True` if the IDs are equal; `False` otherwise.
        """

        if not isinstance(other, Identifiable):
            return NotImplemented
        return self.id == other.id


@dataclass(frozen=True, slots=True)
class Position:
    """Immutable 2D position for node placement in the graph canvas.

    Attributes:
        x: Horizontal position.
        y: Vertical position.
    """

    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Position) -> Position:
        """Add two positions.

        Args:
            other: The position to add.

        Returns:
            The resulting position after addition.
        """

        if not isinstance(other, Position):
            return NotImplemented
        return Position(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Position) -> Position:
        """Subtract two positions.

        Args:
            other: The position to subtract.

        Returns:
            The resulting position after subtraction.
        """

        if not isinstance(other, Position):
            return NotImplemented

        return Position(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Position:
        """Multiply position by scalar.

        Args:
            scalar: The scalar to multiply by.

        Returns:
            The resulting position after multiplication.
        """

        return Position(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> Position:
        """Right multiply position by scalar.

        Args:
            scalar: The scalar to multiply by.

        Returns:
            The resulting position after multiplication.
        """

        return self.__mul__(scalar)

    def distance_to(self, other: Position) -> float:
        """Calculate Euclidean distance to another position.

        Args:
            other: The position to calculate distance to.

        Returns:
            The Euclidean distance between the positions.
        """

        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def lerp(self, other: Position, t: float) -> Position:
        """Linear interpolation between this position and another.

        Args:
            other: The other position to interpolate to.
            t: The interpolation parameter, between 0 and 1.

        Returns:
            The interpolated position.
        """

        return Position(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t,
        )
