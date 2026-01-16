"""Wildcard type for generic ports.

A wildcard port adapts to whatever type it's connected to.
"""

from __future__ import annotations

from typing import Any

from .base import PortType
from .primitives import EXEC


class WildcardType(PortType):
    """Wildcard type that accepts any connection.

    Used for generic nodes that can work with any data type.
    When connected, the wildcard resolves to the connected type.
    """

    def __init__(self, resolved_type: PortType | None = None) -> None:
        """Create a wildcard type.

        Args:
            resolved_type: The type this wildcard has resolved to (if any).
        """

        self._resolved_type = resolved_type

    def __eq__(self, other: object) -> bool:
        """Returns whether this wildcard is equal to another.

        Args:
            other: The object to compare against.

        Returns:
            `True` if the wildcards are equal; `False` otherwise.
        """

        if not isinstance(other, WildcardType):
            return NotImplemented
        return self._resolved_type == other._resolved_type

    def __hash__(self) -> int:
        """Returns the hash value for this wildcard.

        Returns:
            The hash value for the wildcard.
        """

        return hash(("wildcard", self._resolved_type))

    @property
    def resolved_type(self) -> PortType | None:
        """The type this wildcard has resolved to."""

        return self._resolved_type

    @property
    def is_resolved(self) -> bool:
        """Whether this wildcard has been resolved to a concrete type."""

        return self._resolved_type is not None

    @property
    def name(self) -> str:
        """Human-readable type name."""

        if self._resolved_type:
            return f"wildcard<{self._resolved_type.name}>"
        return "wildcard"

    @property
    def display_name(self) -> str:
        """Display name for UI."""

        if self._resolved_type:
            return self._resolved_type.display_name
        return "*"

    @property
    def color(self) -> str:
        """Use the resolved type's color, or white if unresolved."""

        if self._resolved_type:
            return self._resolved_type.color
        return "#FFFFFF"

    def resolve(self, port_type: PortType) -> WildcardType:
        """Create a new wildcard resolved to a specific type.

        Args:
            port_type: The type to resolve to.

        Returns:
            A new `WildcardType` with the resolved type.
        """

        # Don't resolve to another wildcard.
        if isinstance(port_type, WildcardType):
            if port_type._resolved_type:
                return WildcardType(port_type._resolved_type)
            return self
        return WildcardType(port_type)

    def is_compatible_with(self, other: PortType) -> bool:
        """Wildcards are compatible with everything.

        If resolved, use the resolved type's compatibility.
        """

        # EXEC is never compatible with wildcards.
        if other == EXEC:
            return False

        if self._resolved_type:
            return self._resolved_type.is_compatible_with(other)

        return True

    def validate(self, value: Any) -> bool:
        """Validate using the resolved type or accept anything.

        Args:
            value: The value to validate.

        Returns:
            Whether the value is valid.
        """

        if self._resolved_type:
            return self._resolved_type.validate(value)
        return True

    def coerce(self, value: Any) -> Any:
        """Coerce using the resolved type or pass through.

        Args:
            value: The value to coerce.

        Returns:
            The coerced value.
        """

        if self._resolved_type:
            return self._resolved_type.coerce(value)
        return value

    def default_value(self) -> Any:
        """Return the resolved type's default, or None.

        Returns:
            The default value for the resolved type, or `None` if unresolved.
        """

        if self._resolved_type:
            return self._resolved_type.default_value()
        return None


# Singleton for unresolved wildcard
WILDCARD = WildcardType()
