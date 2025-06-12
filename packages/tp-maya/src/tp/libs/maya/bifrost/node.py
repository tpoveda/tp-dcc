from __future__ import annotations

import uuid
import typing
from typing import Any
from pathlib import PurePath

from maya import cmds

from .attribute import Attribute

if typing.TYPE_CHECKING:
    from .graph import Graph


class Node:
    """Class that represents a Bifrost node in Maya."""

    def __init__(
        self,
        graph: Graph,
        parent: str,
        node_type: str | None = None,
        name: str | None = None,
    ):
        """Initialize the Bifrost node.

        Args:
            graph: The graph this node belongs to.
            parent: The parent node of this node.
            node_type: The type of the Bifrost node.
            name: The name of the Bifrost node.
        """

        self._graph = graph
        self._board = graph.board
        self._path = parent
        self._is_compound = False

        if node_type:
            self._create(node_type, name)

    def __repr__(self) -> str:
        """Returns a developer-oriented string representation of the Bifrost
        node.

        Returns:
            A string representation of the Bifrost node.
        """

        return f'{self.__class__.__name__}("{self._path}")'

    def __str__(self) -> str:
        """Returns a human-readable string representation of the Bifrost node.

        Returns:
            A string representation of the Bifrost node.
        """

        return self._path

    def __getitem__(self, key: str) -> Attribute | Node | str:
        """Override the getitem method to allow accessing nodes and attributes
        using a string key.

        Args:
            key: The key to access the node or attribute. It can be a full
                node path (e.g., "/node.attr"), an attribute (e.g., "attr"),
                or a node name (e.g., "node").

        Returns:
            Returns a `Node` object if the key is a node path, or an
                `Attribute` object if the key is an attribute.
        """

        # Handle ".first." attribute by removing it.
        if ".first." in key:
            key = key.replace(".first.", ".")

        # Handle a standard node path.
        if key.startswith("/"):
            return self.node(key)

        # Handle duplicate dots (node..attr).
        if key.startswith("."):
            key = key[1:]

        # Handle key "node.attr" not starting with "/".
        if "." in key and not key.startswith("."):
            return self.node("/" + key)

        return self.attr(key)

    @property
    def path(self) -> str:
        """The node's path."""

        return self._path

    @path.setter
    def path(self, value: str):
        """Set the node's path."""

        value = str(value)
        self._path = "/" + value if not value.startswith("/") else value

    @property
    def name(self) -> str:
        """The node's name."""

        return PurePath(self.path).name

    @property
    def parent(self) -> str:
        """The node's parent path."""

        return str(PurePath(self.path).parent) + "/"

    @property
    def type(self) -> str:
        """Get node's type."""

        type_ = cmds.vnnNode(self._board, self.path, queryTypeName=True)
        type_ = self._fix_type(type_)

        # Remove the board prefix if present.
        board_prefix = f"{self._board.lower()},"
        if type_.lower().startswith(board_prefix):
            type_ = type_[len(board_prefix) :]

        return type_

    @property
    def board(self) -> str:
        """The board this node belongs to."""

        return self._board

    @property
    def is_compound(self) -> bool:
        """Check if the node is a compound node."""

        return self._is_compound

    @property
    def uuid(self) -> str:
        """The node's UUID."""

        return cmds.vnnNode(self._board, self._path, queryMetaData="UUID")

    def attr(self, value: str) -> Attribute:
        """Return the attribute class."""

        return Attribute(self, value)

    def node(self, value: str) -> Node:
        """Get a child of this node.

        Args:
            value: The name of the child node or a full path to the node.
                If it contains a dot (.), it is treated as a node with an
                attribute (e.g., "node.attr"). If it does not contain a dot,
                it is treated as a node name (e.g., "node").

        Returns:
            A Node object representing the child node.
        """

        if "." in value:
            node, attr = value.split(".", 1)
            node = self.node(node)
            return node[attr]
        node = "/".join([self.path, value]).replace("//", "/")

        return Node(self._graph, node)

    def get_children(self) -> list[Node]:
        """Get children nodes.

        Returns:
            A list of child nodes.
        """

        try:
            nodes = cmds.vnnCompound(self.board, self, listNodes=True)
            return [self.node(x) for x in nodes]
        except RuntimeError:
            return []

    def set_metadata(self, metadata: Any):
        """Set node metadata.

        Args:
            metadata: The metadata to set for the node.
        """

        cmds.vnnNode(self._board, self._path, setMetaData=metadata)

    def rename(self, name: str):
        """Rename node.

        Args:
            name: The new name for the node.
        """

        if not name or self.name == name:
            return None

        all_nodes: list[str] = cmds.vnnCompound(
            self._board, self.parent, listNodes=True
        )
        cmds.vnnCompound(self._board, self.parent, renameNode=[self.name, name])
        new_nodes: list[str] = cmds.vnnCompound(
            self._board, self.parent, listNodes=True
        )
        node_diff = list(set(new_nodes) - set(all_nodes))
        if not node_diff:
            raise RuntimeError(f"Can't rename node '{self.name}' to '{name}'")

        node = node_diff[0]
        self.path = self.parent + node
        return self.path

    def create_node(self, node_type, name: str | None = None) -> Node:
        """Create a new node in the current compound."""

        return Node(self._graph, self.path, node_type, name)

    # noinspection PyTypeChecker
    @staticmethod
    def _fix_type(type_to_fix: str) -> str:
        """Fix nodeType when queried from the vnnNode command.

        Args:
            type_to_fix: The node type string to fix.

        Returns:
            A fixed node type string.
        """

        parts = type_to_fix.rsplit("::", 1)
        if len(parts) == 2 and "," not in parts[-1]:
            # Replace the last "::" with "," if no comma exists in the last
            # part.
            return f"{parts[0]},{parts[1]}"

        return type_to_fix

    def _create(self, node_type: str, name: str | None = None):
        """Create a Bifrost node in the graph."""

        path = self._path

        if node_type == "compound":
            node = cmds.vnnCompound(self._board, path, create="compound")
            self._is_compound = True
        else:
            node_type = self._fix_type(node_type)
            type_ = self._board + "," + node_type
            separator = "" if path.endswith("/") else "/"
            node = cmds.vnnCompound(self._board, path, addNode=type_)[0]
            node = "{}{}{}".format(path, separator, node)

        if not node:
            raise RuntimeError(f"Can't create node '{path}' (Type: '{node_type}')")

        self._path = node

        self.set_metadata(["UUID", str(uuid.uuid4()).upper()])
        self.rename(name)
