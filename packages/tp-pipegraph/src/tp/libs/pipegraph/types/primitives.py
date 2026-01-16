"""Primitive types for port connections.

Defines the basic scalar types: bool, int, float, string, any, exec.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from .base import PortType


class PrimitiveTypeKind(Enum):
    """Enumeration of primitive type kinds."""

    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    ANY = "any"
    EXEC = "exec"


class PrimitiveType(PortType):
    """Primitive scalar type.

    Handles basic types like bool, int, float, string.
    Also includes special types: ANY (accepts anything) and EXEC (execution flow).
    """

    # Type promotion hierarchy: types can be promoted upward (numeric only).
    _PROMOTION_ORDER: dict[PrimitiveTypeKind, int] = {
        PrimitiveTypeKind.BOOL: 0,
        PrimitiveTypeKind.INT: 1,
        PrimitiveTypeKind.FLOAT: 2,
        # STRING is NOT in promotion order - it's incompatible with numeric types.
    }

    # UI colors for each type.
    _COLORS: dict[PrimitiveTypeKind, str] = {
        PrimitiveTypeKind.BOOL: "#CC0000",  # Red
        PrimitiveTypeKind.INT: "#00CC99",  # Cyan
        PrimitiveTypeKind.FLOAT: "#00CC00",  # Green
        PrimitiveTypeKind.STRING: "#CC00CC",  # Magenta
        PrimitiveTypeKind.ANY: "#CCCCCC",  # Gray
        PrimitiveTypeKind.EXEC: "#FFFFFF",  # White
    }

    # Python types for validation.
    _PYTHON_TYPES: dict[PrimitiveTypeKind, type | tuple[type, ...]] = {
        PrimitiveTypeKind.BOOL: bool,
        PrimitiveTypeKind.INT: (int, bool),  # bool is a subclass of int.
        PrimitiveTypeKind.FLOAT: (float, int, bool),
        PrimitiveTypeKind.STRING: str,
        PrimitiveTypeKind.ANY: object,
        PrimitiveTypeKind.EXEC: type(None),
    }

    def __init__(self, kind: PrimitiveTypeKind) -> None:
        """Create a primitive type.

        Args:
            kind: The kind of primitive type.
        """

        self._kind = kind

    def __eq__(self, other: object) -> bool:
        """Types are equal if they have the same kind.

        Args:
            other: The object to compare against.

        Returns:
            `True` if the types are equal; `False` otherwise.
        """

        if not isinstance(other, PrimitiveType):
            return NotImplemented
        return self._kind == other._kind

    def __hash__(self) -> int:
        """Hash based on kind.

        Returns:
            Hash value based on the primitive type kind.
        """

        return hash(self._kind)

    @property
    def kind(self) -> PrimitiveTypeKind:
        """The primitive type kind."""

        return self._kind

    @property
    def name(self) -> str:
        """Human-readable type name."""

        return self._kind.value

    @property
    def color(self) -> str:
        """Hex color for UI representation."""

        return self._COLORS.get(self._kind, "#808080")

    def is_compatible_with(self, other: PortType) -> bool:
        """Check if this type can connect to another.

        Rules:
        - ANY accepts anything except EXEC
        - EXEC only connects to EXEC
        - Numeric types can be promoted (bool -> int -> float)
        - STRING only accepts STRING
        """

        # Import here to avoid circular imports
        from tp.pipegraph.types.wildcard import WildcardType

        # Wildcards accept anything
        if isinstance(other, WildcardType):
            return True

        # ANY accepts anything except EXEC
        if self._kind == PrimitiveTypeKind.ANY:
            if isinstance(other, PrimitiveType):
                return other._kind != PrimitiveTypeKind.EXEC
            return True  # ANY accepts non-primitive types too

        # Target is ANY - allow anything except EXEC
        if (
            isinstance(other, PrimitiveType)
            and other._kind == PrimitiveTypeKind.ANY
        ):
            return self._kind != PrimitiveTypeKind.EXEC

        # EXEC only connects to EXEC
        if self._kind == PrimitiveTypeKind.EXEC:
            return (
                isinstance(other, PrimitiveType)
                and other._kind == PrimitiveTypeKind.EXEC
            )

        # Non-primitive target - not compatible with primitives (except ANY)
        if not isinstance(other, PrimitiveType):
            return False

        # Same type is always compatible
        if self._kind == other._kind:
            return True

        # Check promotion hierarchy
        source_order = self._PROMOTION_ORDER.get(self._kind)
        target_order = self._PROMOTION_ORDER.get(other._kind)

        if source_order is not None and target_order is not None:
            # Can promote to higher types (e.g., int -> float)
            return source_order <= target_order

        return False

    def validate(self, value: Any) -> bool:
        """Check if a value is valid for this type."""
        if self._kind == PrimitiveTypeKind.ANY:
            return True
        if self._kind == PrimitiveTypeKind.EXEC:
            return value is None
        expected = self._PYTHON_TYPES.get(self._kind, object)
        return isinstance(value, expected)

    def coerce(self, value: Any) -> Any:
        """Convert a value to this type.

        Raises:
            TypeError: If conversion is not possible.
        """
        if self._kind == PrimitiveTypeKind.ANY:
            return value

        if self._kind == PrimitiveTypeKind.EXEC:
            return None

        if self._kind == PrimitiveTypeKind.BOOL:
            return bool(value)

        if self._kind == PrimitiveTypeKind.INT:
            if isinstance(value, bool):
                return int(value)
            if isinstance(value, (int, float, str)):
                return int(value)
            raise TypeError(f"Cannot coerce {type(value).__name__} to int")

        if self._kind == PrimitiveTypeKind.FLOAT:
            if isinstance(value, (bool, int, float, str)):
                return float(value)
            raise TypeError(f"Cannot coerce {type(value).__name__} to float")

        if self._kind == PrimitiveTypeKind.STRING:
            return str(value)

        return value

    def default_value(self) -> Any:
        """Return the default value for this type."""
        defaults: dict[PrimitiveTypeKind, Any] = {
            PrimitiveTypeKind.BOOL: False,
            PrimitiveTypeKind.INT: 0,
            PrimitiveTypeKind.FLOAT: 0.0,
            PrimitiveTypeKind.STRING: "",
            PrimitiveTypeKind.ANY: None,
            PrimitiveTypeKind.EXEC: None,
        }
        return defaults.get(self._kind)


# Singleton instances for common types
BOOL = PrimitiveType(PrimitiveTypeKind.BOOL)
INT = PrimitiveType(PrimitiveTypeKind.INT)
FLOAT = PrimitiveType(PrimitiveTypeKind.FLOAT)
STRING = PrimitiveType(PrimitiveTypeKind.STRING)
ANY = PrimitiveType(PrimitiveTypeKind.ANY)
EXEC = PrimitiveType(PrimitiveTypeKind.EXEC)
