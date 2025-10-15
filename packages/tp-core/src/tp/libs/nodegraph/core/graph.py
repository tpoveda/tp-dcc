from __future__ import annotations

import re
import typing
import weakref
from uuid import uuid4
from typing import Any

from Qt.QtCore import Signal, QObject

from .interfaces import ISerializable
from .errors import NodeExistsError

if typing.TYPE_CHECKING:
    from .node import Node
    from .ids import NodeId
    from .graph_manager import GraphManager


class GraphSignals(QObject):
    """Signals for the Graph class."""

    nameChanged = Signal(str)
    categoryChanged = Signal(str)


class Graph(ISerializable):
    def __init__(
        self,
        manager: GraphManager,
        *,
        uuid: str | None = None,
        name: str,
        category: str = "",
        parent_graph: Graph | None = None,
    ) -> None:
        super().__init__()

        self._manager = manager
        self._uuid = uuid or str(uuid4())
        self._name = name
        self._category = category
        self._parent_graph = parent_graph
        self._is_root = False
        self._nodes: dict[NodeId, Node] = {}
        self._child_graphs: set[Graph] = set()
        self._signals = GraphSignals()

        # Make sure to register this graph with the manager
        self._manager.register_graph(self)

    @property
    def id(self) -> str:
        """The unique identifier of the graph."""

        return self._uuid

    @property
    def name(self) -> str:
        """The name of the graph."""

        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of the graph.

        Args:
            value: The new name of the graph.
        """

        if self._name == value:
            return

        self._name = value
        self._signals.nameChanged.emit(value)

    @property
    def category(self) -> str:
        """The category of the graph."""

        return self._category

    @category.setter
    def category(self, value: str) -> None:
        """Set the category of the graph"""

        if self._category == value:
            return

        self._category = value
        self._signals.categoryChanged.emit(value)

    # === Nodes === #

    def nodes(self) -> list[Node]:
        """Return all nodes in the node graph.

        Returns:
            List of nodes in the graph.
        """

        return list(self._nodes.values())

    def unique_node_name(self, name: str) -> str:
        """Creates a unique node name ensuring the new node name is unique
        within this graph.

        Args:
            name: Node name.

        Returns:
            Unique node name.
        """

        name = " ".join(name.split())
        node_names = [n.name() for n in self.nodes()]
        if name not in node_names:
            return name

        regex = re.compile(r"\w+ (\d+)$")
        search = regex.search(name)
        if not search:
            for x in range(1, len(node_names) + 2):
                new_name = "{} {}".format(name, x)
                if new_name not in node_names:
                    return new_name

        version = search.group(1)
        name = name[: len(version) * -1].strip()
        for x in range(1, len(node_names) + 2):
            new_name = "{} {}".format(name, x)
            if new_name not in node_names:
                return new_name

        return name

    def add_node(self, node: Node) -> NodeId:
        """Add a node to the graph.

        Args:
            node: The node to add to the graph.

        Returns:
            The ID of the added node.

        Raises:
            NodeExistsError: If a node with the same ID already exists in
                the graph.
        """

        assert isinstance(node, Node), "node must be a `Node` instance."

        node_id = node.id
        if node_id in self._nodes:
            raise NodeExistsError(f"Node '{node.id}' already exists.")

        node.graph = weakref.ref(self)
        node.NODE_NAME = self.unique_node_name(node.NODE_NAME)
        node.model.name = node.NODE_NAME

    # === Graph Hierarchy === #

    @property
    def is_root(self) -> bool:
        """Whether this graph is a root graph (has no parent graph)."""

        return self._is_root

    @is_root.setter
    def is_root(self, flag: bool) -> None:
        """Set whether this graph is a root graph."""

        self._is_root = flag
        if flag:
            self._parent_graph = None

    @property
    def parent_graph(self) -> Graph | None:
        """The parent graph of this graph, if any."""

        return self._parent_graph

    @parent_graph.setter
    def parent_graph(self, graph: Graph | None) -> None:
        """Set the parent graph of this graph.

        Args:
            graph: The new parent graph.
        """

        if graph is None:
            self.is_root = True
            return

        # If the new parent is the same as the current parent, do nothing.
        if self._parent_graph == graph:
            return

        if self._parent_graph is not None:
            # Remove self from current parent's children set.
            if self in self._parent_graph.child_graphs:
                self._parent_graph.child_graphs.remove(self)

        # Add self to new parent's children set.
        graph.child_graphs.add(self)

        # Update parent.
        self._parent_graph = graph

    @property
    def child_graphs(self) -> set[Graph]:
        """Set of child graphs of this graph."""

        return self._child_graphs

    def depth(self) -> int:
        """Returns the depth of this graph in the hierarchy.

        Returns:
            Depth of the graph.
        """

        depth = 0
        parent = self.parent_graph
        while parent is not None:
            depth += 1
            parent = parent.parent_graph

        return depth

    # === Lifecycle === #

    def clear(self):
        """Clears the contents of the graph, as well as child graphs."""

        for child_graph in self._child_graphs:
            child_graph.clear()

        for node in list(self._nodes.values()):
            node.destroy()
        self._nodes.clear()

    # === Serialization === #

    def serialize(self) -> dict[str, Any]:
        """Returns a serialized representation of this graph.

        Returns:
            Serialized graph data.
        """

        return {
            "name": self.name,
            "category": self.category,
            "depth": self.depth(),
            "is_root": self.is_root,
            "parent_graph_name": self.parent_graph.name
            if self.parent_graph
            else str(None),
        }

    def deserialize(self, data: dict[str, Any], *args, **kwargs) -> None:
        raise NotImplementedError
