"""Node and port definitions for the registry system.

Provides dataclasses that describe node and port structure
for registration, discovery, and UI purposes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..types import PortType


class PortDirection(Enum):
    """Direction of a port on a node."""

    INPUT = auto()
    OUTPUT = auto()


@dataclass(frozen=True)
class PortDefinition:
    """Definition of a port for node registration.

    Describes a port's structure, type, and metadata for registry and UI
    purposes.
    """

    name: str
    data_type: PortType
    direction: PortDirection
    default_value: Any = None
    required: bool = True
    multi_connection: bool = False
    display_name: str = ""
    description: str = ""

    def __post_init__(self) -> None:
        """Validate port definition."""

        if not self.name:
            raise ValueError("Port name cannot be empty")

    @property
    def effective_display_name(self) -> str:
        """Display name, falling back to name if not set."""

        return self.display_name or self.name


@dataclass(frozen=True)
class NodeDefinition:
    """Definition of a node type for registration.

    Contains all metadata needed to:
        - Register the node in the registry
        - Create instances of the node
        - Display the node in the UI
        - Search for nodes by name/category/keywords
    """

    # Required identification
    type_id: str
    node_class: type[Node]
