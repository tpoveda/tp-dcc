from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "CycleError",
    "DocstringContractError",
    "EdgeExistsError",
    "EdgeNotFoundError",
    "GraphError",
    "GraphIOError",
    "JSONParseError",
    "SchemaValidationError",
    "NodeError",
    "NodeError",
    "NodeExistsError",
    "NodeNotFoundError",
    "NodeNotRunnableError",
    "PortDirectionError",
    "PortNotFoundError",
    "PortTypeMismatchError",
    "PortValidationError",
    "TypeValidationError",
    "ValidationError",
]


@dataclass(frozen=True, slots=True)
class ValidationError(ValueError):
    """Base validation error with rich context for helpful messages."""

    message: str
    expected: str | None = None
    actual: str | None = None
    path: str | None = None  # e.g. "value['foo'][2]"

    def __str__(self) -> str:
        """Return a formatted string representation of the error."""

        bits: list[str] = [self.message]
        if self.path:
            bits.append(f"(at {self.path})")
        if self.expected:
            bits.append(f"expected={self.expected}")
        if self.actual:
            bits.append(f"actual={self.actual}")
        return " | ".join(bits)


class TypeValidationError(ValidationError):
    """Validation error for dtype mismatches."""


class PortValidationError(ValidationError):
    """Validation error scoped to a specific port."""

    def __init__(
        self,
        port_name: str,
        message: str,
        *,
        expected: str | None = None,
        actual: str | None = None,
        path: str | None = None,
    ) -> None:
        msg = f"Port '{port_name}': {message}"
        super().__init__(msg, expected=expected, actual=actual, path=path)


class NodeError(RuntimeError):
    """Base class for all node-related errors."""


class DocstringContractError(NodeError):
    """Raised when a node's docstring contract is violated."""


class NodeNotRunnableError(NodeError):
    """Raised when a node is not runnable due to missing inputs or other
    issues.
    """


class GraphError(Exception):
    """Base class for all graph-related errors."""


class GraphIOError(GraphError):
    """Base class for graph serialization/deserialization errors."""


@dataclass(frozen=True, slots=True)
class JSONParseError(GraphIOError):
    """Raised when JSON parsing fails with location information."""

    message: str
    line: int
    column: int

    def __str__(self) -> str:  # pragma: no cover - formatting wrapper
        return f"{self.message} (line {self.line}, column {self.column})"


@dataclass(frozen=True, slots=True)
class SchemaValidationError(GraphIOError):
    """Raised when a JSON payload does not conform to the graph schema."""

    message: str
    path: str | None = None

    def __str__(self) -> str:  # pragma: no cover - formatting wrapper
        return f"{self.message}{f' at {self.path}' if self.path else ''}"


class NodeExistsError(GraphError):
    """Raised when trying to add a node that already exists in the graph."""


class NodeNotFoundError(GraphError):
    """Raised when a node is not found in the graph."""


class PortNotFoundError(GraphError):
    """Raised when a port is not found in the graph."""


class PortDirectionError(GraphError):
    """Raised when a port's direction does not match the expected direction."""


class PortTypeMismatchError(GraphError):
    """Raised when a port's type does not match the expected type."""


class EdgeExistsError(GraphError):
    """Raised when trying to add an edge that already exists in the graph."""


class EdgeNotFoundError(GraphError):
    """Raised when an edge is not found in the graph."""


class CycleError(GraphError):
    """Raised when a cycle is detected in the graph, preventing a valid
    topological sort.
    """
