from __future__ import annotations

import typing
from typing import Iterable, Any
from dataclasses import dataclass, field

if typing.TYPE_CHECKING:
    from .nodes import DGNodeDescriptor


@dataclass
class NamedGraph:
    """Class that defines a network of Dependency Graph (DG) nodes, and their
    internal connections
    """

    id: str = ""
    name: str = ""
    nodes: list[DGNodeDescriptor] = field(default_factory=list)
    connections: list[dict[str, Any]] = field(default_factory=list)
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_data(cls, data: dict[str, Any]) -> NamedGraph:
        """Creates a `NamedGraph` object from a dictionary.

        Args:
            data: Dictionary containing the data for the `NamedGraph`.

        Returns:
            A `NamedGraph` object.
        """

        data = data.copy()
        data["name"] = data.get("name", data.get("id", ""))
        data["nodes"] = [DGNodeDescriptor(i) for i in data.get("nodes", [])]
        return cls(**data)

    def node(self, node_id: str) -> DGNodeDescriptor | None:
        """Get a node by its ID.

        Args:
            node_id: The ID of the node.

        Returns:
            The node with the given ID, or None if not found.
        """

        found_node: DGNodeDescriptor | None = None
        for node in self.nodes:
            if node.id == node_id:
                found_node = node
                break

        return found_node


class NamedGraphs(list):
    """List of `NamedGraph` objects."""

    @classmethod
    def from_data(cls, layer_data: Iterable[dict[str, Any]]) -> NamedGraphs:
        """Creates a `NamedGraphs` object from a list of dictionaries.

        Args:
            layer_data: List of dictionaries containing the data for each `NamedGraph`.

        Returns:
            A `NamedGraphs` object.
        """

        return cls([NamedGraph.from_data(**data) for data in layer_data])

    def graph(self, graph_id: str) -> NamedGraph | None:
        """Get a graph by its ID.

        Args:
            graph_id: The ID of the graph.

        Returns:
            The graph with the given ID, or None if not found.
        """

        found_graph: NamedGraph | None = None
        for graph in self:
            if graph.id == graph_id:
                found_graph = graph
                break

        return found_graph
