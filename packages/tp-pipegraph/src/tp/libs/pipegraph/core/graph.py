"""Graph class - the container for nodes, connections, and variables.

The Graph is the top-level container that manages:
    - A collection of nodes
    - Connections between node ports
    - Graph-scoped variables
    - Topology queries (cycles, evaluation order, etc.)
"""

from __future__ import annotations

import typing
from dataclasses import dataclass, field
from uuid import UUID

from .connection import Connection
from .variable import Variable

if typing.TYPE_CHECKING:
    from .node import Node


from .base import Identifiable


@dataclass
class Graph(Identifiable):
    """Container for nodes, connections, and variables.

    The Graph manages:
        - Node collection with add/remove/query operations.
        - Connection management with validation.
        - Variable storage.
        - Topology analysis (cycles, order, dependencies).
        - Subgraph hierarchy (parent/child relationships).

    Subgraph Support:
        - A Graph can have a parent_graph (making it a subgraph).
        - A Graph can contain SubgraphNodes which have their own internal graphs.
        - Navigation between parent and child graphs is supported via breadcrumb.
    """

    name: str = "Untitled Graph"
    description: str = ""
    _nodes: dict[UUID, Node] = field(default_factory=dict, repr=False)
    _connections: set[Connection] = field(default_factory=set, repr=False)
    _variables: dict[str, Variable] = field(default_factory=dict, repr=False)
    _metadata: dict[str, str] = field(default_factory=dict, repr=False)

    # Subgraph hierarchy.
    _parent_graph: Graph | None = field(default=None, repr=False)
    _owner_node: Node | None = field(
        default=None, repr=False
    )  # SubgraphNode that owns this graph
