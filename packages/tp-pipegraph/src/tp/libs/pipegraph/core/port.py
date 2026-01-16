"""Port classes for node inputs and outputs.

Ports are connection points on nodes through which data flows.
"""

from __future__ import annotations

import typing
from dataclasses import dataclass, field
from typing import Any, Callable
from uuid import UUID

from ..types import FLOAT, PortType
from .base import Identifiable

if typing.TYPE_CHECKING:
    from .node import Node


@dataclass
class Port(Identifiable):
    """Base class for node ports.

    Ports are connection points that carry typed data.
    Each port belongs to a node and has a specific data type.
    """

    name: str
    port_type: PortType = field(default=FLOAT)
    node: Node | None = field(default=None, repr=False)
    description: str = ""
    hidden: bool = False

    def __post_init__(self) -> None:
        """Validate port after initialization."""
        if not self.name:
            raise ValueError("Port name cannot be empty")

    @property
    def qualified_name(self) -> str:
        """Full name including node: 'NodeName.PortName'."""
        if self.node:
            return f"{self.node.name}.{self.name}"
        return self.name

    @property
    def is_input(self) -> bool:
        """Whether this is an input port."""
        return isinstance(self, InputPort)

    @property
    def is_output(self) -> bool:
        """Whether this is an output port."""
        return isinstance(self, OutputPort)

    def can_connect_to(self, other: Port) -> bool:
        """Check if this port can connect to another port.

        Connection rules:
            - `Input` can only connect to `Output` (and vice versa).
            - Types must be compatible.
            - Cannot connect to `self` or to the same node.
        """

        # Can't connect to the same port type (input-input or output-output)
        if type(self) is type(other):
            return False

        # Can't connect to self.
        if self.id == other.id:
            return False

        # Can't connect ports on same node.
        if self.node is not None and other.node is not None:
            if self.node.id == other.node.id:
                return False

        # Check type compatibility.
        if self.is_output:
            return self.port_type.is_compatible_with(other.port_type)
        else:
            return other.port_type.is_compatible_with(self.port_type)


@dataclass
class InputPort(Port):
    """Input port that receives data from connections or default values.

    Input ports can have:
        - A default value used when not connected.
        - A connection to an output port.
        - Multi-connection support (for some types).
    """

    default_value: Any = field(default=None)
    multi_connection: bool = False
    _value: Any = field(default=None, repr=False)
    _is_connected: bool = field(default=False, repr=False)
    _connected_port_ids: set[UUID] = field(default_factory=set, repr=False)
    _is_watched: bool = field(default=False, repr=False)
    _last_value: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize with a default value if not set."""

        super().__post_init__()

        if self._value is None and self.default_value is None:
            self._value = self.port_type.default_value()
        elif self._value is None:
            self._value = self.default_value

    @property
    def value(self) -> Any:
        """Current value of the port."""

        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the port value with coercion to ensure the correct type."""

        self._value = self.port_type.coerce(new_value)

    @property
    def is_connected(self) -> bool:
        """Whether this port has an incoming connection."""

        return self._is_connected

    @property
    def connected_port_ids(self) -> frozenset[UUID]:
        """IDs of connected output ports."""

        return frozenset(self._connected_port_ids)

    def reset_to_default(self) -> None:
        """Reset the port to its default value."""

        if self.default_value is not None:
            self._value = self.default_value
        else:
            self._value = self.port_type.default_value()

    def mark_connected(self, source_port_id: UUID) -> None:
        """Mark this port as connected to a source."""

        self._is_connected = True
        self._connected_port_ids.add(source_port_id)

    def mark_disconnected(self, source_port_id: UUID) -> None:
        """Mark this port as disconnected from a source."""

        self._connected_port_ids.discard(source_port_id)
        self._is_connected = len(self._connected_port_ids) > 0

    @property
    def is_watched(self) -> bool:
        """Whether this port is being watched for value changes."""

        return self._is_watched

    @is_watched.setter
    def is_watched(self, value: bool) -> None:
        """Set the watch state for this port."""

        self._is_watched = value

    @property
    def last_value(self) -> Any:
        """Last computed value (stored after evaluation)."""

        return self._last_value

    def store_last_value(self) -> None:
        """Store current value as last value (call after evaluation)."""

        self._last_value = self._value


@dataclass
class OutputPort(Port):
    """Output port that provides computed data.

    Output ports:
        - Hold the result of node computation.
        - Can connect to multiple input ports.
        - May have an optional compute function.
    """

    _value: Any = field(default=None, repr=False)
    _connected_port_ids: set[UUID] = field(default_factory=set, repr=False)
    compute_func: Callable[[], Any] | None = field(default=None, repr=False)
    _is_watched: bool = field(default=False, repr=False)
    _last_value: Any = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize the port."""

        super().__post_init__()

        if self._value is None:
            self._value = self.port_type.default_value()

    @property
    def value(self) -> Any:
        """Current value of the port."""

        # If there's a `compute` function, call it.
        if self.compute_func is not None:
            return self.compute_func()
        return self._value

    @value.setter
    def value(self, new_value: Any) -> None:
        """Set the port value with coercion to ensure the correct type."""

        self._value = self.port_type.coerce(new_value)

    @property
    def is_connected(self) -> bool:
        """Whether this port has outgoing connections."""

        return len(self._connected_port_ids) > 0

    @property
    def connected_port_ids(self) -> frozenset[UUID]:
        """IDs of connected input ports."""

        return frozenset(self._connected_port_ids)

    @property
    def connection_count(self) -> int:
        """Number of connections from this port."""

        return len(self._connected_port_ids)

    def mark_connected(self, target_port_id: UUID) -> None:
        """Mark this port as connected to a target."""

        self._connected_port_ids.add(target_port_id)

    def mark_disconnected(self, target_port_id: UUID) -> None:
        """Mark this port as disconnected from a target."""

        self._connected_port_ids.discard(target_port_id)

    @property
    def is_watched(self) -> bool:
        """Whether this port is being watched for value changes."""

        return self._is_watched

    @is_watched.setter
    def is_watched(self, value: bool) -> None:
        """Set the watch state for this port."""

        self._is_watched = value

    @property
    def last_value(self) -> Any:
        """Last computed value (stored after evaluation)."""

        return self._last_value

    def store_last_value(self) -> None:
        """Store current value as last value (call after evaluation)."""

        self._last_value = self._value
