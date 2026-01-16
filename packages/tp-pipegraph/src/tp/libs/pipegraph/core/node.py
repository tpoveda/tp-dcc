"""Node classes for graph processing units.

Nodes are the fundamental processing units in a graph.
They have input ports, output ports, and a compute method.
"""

from __future__ import annotations

import typing
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar

from .base import Identifiable, Position
from .port import InputPort, OutputPort

if typing.TYPE_CHECKING:
    from .graph import Graph


@dataclass(eq=False)
class Node(Identifiable, ABC):
    """Abstract base class for all nodes.

    Nodes are processing units that:
        - Have named input and output ports.
        - Implement a `compute()` method.
        - Maintain their position in the canvas.
        - Can be enabled/disabled.
    """

    # Class-level metadata for node registration
    node_name: ClassVar[str] = "Node"
    node_category: ClassVar[str] = "General"
    node_description: ClassVar[str] = ""
    node_icon: ClassVar[str] = ""  # Path to node icon image
    node_color: ClassVar[str] = (
        ""  # Header color as hex string (e.g., "#5050FF")
    )
    node_tags: ClassVar[tuple[str, ...]] = ()

    # Instance fields
    name: str = ""
    position: Position = field(default_factory=Position)
    _inputs: dict[str, InputPort] = field(default_factory=dict, repr=False)
    _outputs: dict[str, OutputPort] = field(default_factory=dict, repr=False)
    _graph: Graph | None = field(default=None, repr=False)
    _is_disabled: bool = field(default=False)
    _is_bypassed: bool = field(default=False)
    _is_dirty: bool = field(default=True)
    _has_breakpoint: bool = field(default=False)
    _metadata: dict[str, str] = field(default_factory=dict, repr=False)
    _error: str | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize node after dataclass creation."""

        if not self.name:
            self.name = self.__class__.node_name

        # Define ports (subclasses override this).
        self.define_ports()

        # Set port ownership.
        for in_port in self._inputs.values():
            in_port.node = self
        for out_port in self._outputs.values():
            out_port.node = self

    @abstractmethod
    def define_ports(self) -> None:
        """Define the node's input and output ports.

        Subclasses must implement this to declare their ports.
        """
        ...

    @abstractmethod
    def compute(self) -> None:
        """Execute the node's computation.

        This method reads from input ports and writes to output ports.
        """
        ...
