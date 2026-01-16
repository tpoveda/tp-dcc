"""Base type system for port connections.

Defines the abstract PortType class that all types inherit from.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class PortType(ABC):
    """Abstract base class for all port types.

    Port types define what data can flow through connections.
    Types implement compatibility checking for safe connections.
    """

    def __eq__(self, other: object) -> bool:
        """Types are equal if they have the same name."""

        if not isinstance(other, PortType):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        """Hash based on type name."""

        return hash(self.name)

    def __repr__(self) -> str:
        """Return a string representation of the port type."""

        return f"{self.__class__.__name__}({self.name!r})"

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the port type."""
        ...

    @property
    def display_name(self) -> str:
        """Display name for UI (defaults to `name`)."""

        return self.name

    @property
    def color(self) -> str:
        """Hex color for UI representation."""

        return "#808080"  # Default gray

    @abstractmethod
    def default_value(self) -> Any:
        """Return the default value for this type.

        Returns:
            The default value for this type.
        """
        ...

    @abstractmethod
    def is_compatible_with(self, other: PortType) -> bool:
        """Check if this type can receive data from another type.

        This is directional: source.is_compatible_with(target) means
        data can flow from source to target.

        Args:
            other: The type to check compatibility with.

        Returns:
            `True` if connection is allowed; `False` otherwise.
        """
        ...

    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Check if a value is valid for this type.

        Args:
            value: The value to validate.

        Returns:
            `True` if the value is valid; `False` otherwise.
        """
        ...

    @abstractmethod
    def coerce(self, value: Any) -> Any:
        """Attempt to convert a value to this type.

        Args:
            value: The value to convert.

        Returns:
            The converted value.

        Raises:
            TypeError: If conversion is not possible.
            ValueError: If the value is not valid.
        """
        ...
