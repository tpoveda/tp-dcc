from __future__ import annotations

import typing

from maya import cmds

if typing.TYPE_CHECKING:
    from .node import Node


class Attribute:
    """Class representing a Bifrost attribute."""

    def __init__(self, node: Node, attribute: str | None = None):
        """Initializes the Bifrost attribute.

        Args:
            node: The Bifrost node this attribute belongs to.
            attribute: The name of the attribute. If None, the default attribute is used.
        """

        self._node = node
        self._parent = str(node)
        self._board = node.board
        self._name = attribute
        self._plug = f"{node}.{attribute}"

    def __str__(self) -> str:
        """Returns a developer-oriented string representation of the Bifrost
        attribute.

        Returns:
            A string representation of the Bifrost attribute.
        """

        return self._plug

    def __repr__(self) -> str:
        """Returns a human-readable string representation of the Bifrost
        attribute.

        Returns:
            A string representation of the Bifrost attribute.
        """

        return f'{self.__class__.__name__}("{self._plug}")'

    def __rshift__(self, attribute: Attribute):
        """Overload the `>>` operator to connect this attribute to another
        attribute.

        Args:
            attribute: The attribute to connect to this attribute.
        """

        self.connect(attribute)

    def __floordiv__(self, attribute: Attribute):
        """Overload the `//` operator to disconnect this attribute from another
        attribute.

        Args:
            attribute: The attribute to disconnect from this attribute.
        """

        self.disconnect(attribute)

    @property
    def node(self) -> Node:
        """The Bifrost node this attribute belongs to."""

        return self._node

    @property
    def plug(self) -> str:
        """The plug string representation of the attribute."""

        return self._plug

    @property
    def type(self) -> str:
        """The attribute type."""

        return cmds.vnnNode(self._board, str(self._node), queryPortDataType=self._name)

    @property
    def value(self) -> int | float | bool | str:
        """The attribute value."""

        node = self._node if self._node.type else self._node.parent
        return cmds.vnnNode(self._board, str(node), queryPortDefaultValues=self._name)

    @value.setter
    def value(self, value: int | float | bool | str):
        """Set the attribute value."""

        if not value and not isinstance(value, (int, float, bool, str)):
            return

        kwargs = {"setPortDefaultValues": [self._name, value]}
        if self._node.parent == "/" and not self._node.type:
            cmds.vnnCompound(self._board, self._node.parent, **kwargs)
            return

        node = self._node if self._node.type else self._node.parent
        cmds.vnnNode(self._board, str(node), **kwargs)

    def exists(self) -> bool:
        """Check if the attribute exists.

        Returns:
            True if the attribute exists; False otherwise.
        """

        existing: list[str] = []
        nodes = cmds.vnnNode(self._board, str(self._node), listPorts=True) or []
        for each in nodes:
            existing.append(each.split(".", 1)[-1])

        return self._name in existing

    def add(
        self,
        direction: str,
        datatype: str = "auto",
        value: int | float | bool | str | None = None,
    ):
        """Add input plug on given node.

        Args:
            direction: The direction of the port, either "input" or "output".
            datatype: The data type of the port. Defaults to "auto".
            value: The default value for the port. Defaults to None.

        Raises:
            NameError: If the direction is not "input" or "output".
        """

        if direction not in ("input", "output"):
            raise NameError('`direction` must be either "input" or "output"')

        key = "create{}Port".format(direction.title())
        cmd = cmds.vnnCompound if self._node.is_compound else cmds.vnnNode
        cmd(self._board, str(self._parent), **{key: [self._name, datatype]})
        self.value = value

    def connect(self, target: Attribute):
        """Connect this attribute to another attribute.

        Args:
            target: The target attribute to connect to.
        """

        if not self.exists():
            self.add("output")

        if not target.node.type:
            target.add("input", self.type)

        if not target.exists():
            target.add("input")

        cmds.vnnConnect(self._board, self._plug, target.plug)

    def disconnect(self, target: Attribute):
        """Disconnect this attribute from another attribute.

        Args:
            target: The target attribute to disconnect from.
        """

        cmds.vnnConnect(self._board, self.plug, target.plug, disconnect=True)
