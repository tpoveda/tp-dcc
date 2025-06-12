from __future__ import annotations

from typing import Any

from maya import cmds

from .node import Node


class Graph:
    """A class that represents a Bifrost graph."""

    def __init__(self, board: str | None = None):
        """Initializes the Bifrost graph.

        Args:
            board: The name of the board to use for the graph.
        """

        self._board = self._get_or_create_board(board)

        self._create_name_attribute()

    def __repr__(self) -> str:
        """Returns a developer-oriented string representation of the Bifrost
        graph.

        Returns:
            A string representation of the Bifrost graph.
        """

        return f'{self.__class__.__name__}("{self._board}")'

    def __str__(self) -> str:
        """Returns a human-readable string representation of the Bifrost graph.

        Returns:
            A string representation of the Bifrost graph.
        """

        return self._board

    def __getitem__(self, key: str) -> Any:
        """Overrides the `__getitem__` method to allow access to nodes or
        properties using the syntax `graph[key]`.

        Args:
            key: The name of the node or property to retrieve.

        Returns:
            The node or property corresponding to the given key.
        """

        return self.get(key)

    @property
    def name(self) -> str:
        """The name of the Bifrost board node."""

        return self._board

    @name.setter
    def name(self, value: str):
        """Sets the name of the Bifrost board node.

        Raises:
            RuntimeError: If the Bifrost board does not exist in the scene.
        """

        if not cmds.objExists(self._board):
            raise RuntimeError(
                f"Bifrost board '{self._board}' no longer exists in the scene"
            )

        self._board = cmds.rename(self._board, value)

    @property
    def board(self) -> str:
        """The name of the Bifrost board node.

        Returns:
            The name of the Bifrost board node.
        """

        return self._board

    @property
    def nodes(self) -> list[Node]:
        """Get nodes at the board/root level.

        Returns:
            A list of `Node` instances representing the nodes at the board
            level.
        """

        children = cmds.vnnCompound(self.board, "/", listNodes=True) or []
        return [self.get(x) for x in children]

    def get(self, name: str) -> Any:
        """Returns the given string as a node or property.

        Args:
            name: The name of the node or property to retrieve.

        Returns:
            The node or property corresponding to the given name.
        """

        if name is None:
            return name

        name, _, attr = name.partition(".")
        node = Node(self, name)

        if attr:
            return node[attr]

        return node

    def create_node(self, node_type: str, parent: str = "/", name: str = None) -> Node:
        """Create a new bifrost node in the graph.

        Args:
            node_type: The type of the node to create.
            parent: The parent node or board where the new node will be created.
            name: The name of the new node. If None, a unique name will be generated.

        Returns:
            Node: An instance of the `Node` class representing the newly
            created node.
        """

        return Node(self, parent, node_type, name)

    @staticmethod
    def _get_or_create_board(name: str | None = None) -> str:
        """Get existing or create a new `BifrostBoard`.

        Args:
            name: The name of the board to create or get. If None,
                defaults to "bifrostGraph".

        Returns:
            The name of the Bifrost board node.
        """

        if name and cmds.objExists(name):
            if cmds.nodeType(name) == "bifrostBoard":
                return name

        name = name or "bifrostGraph"
        board = cmds.createNode("bifrostBoard")

        return cmds.rename(board, name)

    def _create_name_attribute(self):
        """Create a name attribute to identify the board."""

        node_attr = self._board + ".board_name"
        if not cmds.objExists(node_attr):
            cmds.addAttr(self._board, longName="board_name", dataType="string")
        cmds.setAttr(node_attr, self._board, type="string")
