from __future__ import annotations

import typing
from typing import Type, Iterator

from maya.api import OpenMaya

from . import constants, errors
from ..meta import base
from ..om import attributetypes

if typing.TYPE_CHECKING:
    from ..wrapper import DGNode
    from .command import TriggerCommand


class TriggerNode:
    """
    Class that encapsulates a single node trigger, including menus to execute commands
    and menus.
    """

    TRIGGER_ATTR_NAME = constants.TRIGGER_ATTR_NAME
    COMMAND_TYPE_ATTR_NAME = constants.COMMAND_TYPE_ATTR_NAME
    TRIGGER_MENU_TYPE = constants.TRIGGER_MENU_TYPE
    TRIGGER_SELECTION_TYPE = constants.TRIGGER_SELECTION_TYPE

    def __init__(self, node: DGNode):
        super().__init__()

        self._node = node
        self._command: TriggerCommand | None = None

    def __repr__(self) -> str:
        """
        Returns a string representation of the trigger node.

        :return: string representation of the trigger node.
        """

        return (
            f"<{self.__class__.__name__}> command: {self._command}, node: {self._node}"
        )

    def __eq__(self, other: TriggerNode) -> bool:
        """
        Returns whether this trigger node is equal to the given trigger node.

        :param other: trigger node to compare to.
        :return: True if both trigger nodes are equal, False otherwise.
        """

        return self._node == other._node

    def __ne__(self, other: TriggerNode) -> bool:
        """
        Returns whether this trigger node is not equal to the given trigger node.

        :param other: trigger node to compare to.
        :return: True if both trigger nodes are not equal, False otherwise.
        """

        return not self.__eq__(other)

    @property
    def node(self) -> DGNode:
        """
        Getter that returns the node of this trigger node.

        :return: node of this trigger node.
        """

        return self._node

    @property
    def command(self) -> TriggerCommand:
        """
        Getter that returns the command of this trigger node.

        :return: command of this trigger node.
        """

        return self._command

    @classmethod
    def has_trigger(cls, node: DGNode, strict: bool = False) -> bool:
        """
        Returns whether given node contains a trigger or connected meta nodes has a
        trigger.

        :param node: node to check if it has a trigger.
        :param strict: whether to only check the given node or connected meta nodes.
        :return: True if the given node has a trigger, False otherwise.
        """

        if node.hasAttribute(cls.TRIGGER_ATTR_NAME):
            return True

        if strict:
            return False

        for meta_node in base.connected_meta_nodes(node):
            if meta_node.attribute(cls.TRIGGER_ATTR_NAME):
                return True

        return False

    @classmethod
    def from_node(cls, node: DGNode) -> TriggerNode | None:
        """
        Creates a TriggerNode instance from the given node.

        :param node: node to create the TriggerNode instance from.
        :return: trigger node instance.
        :raises errors.MissingTriggerAttributeError: If the node does not have a trigger.
        """

        from .manager import TriggersManager

        if not cls.has_trigger(node, strict=True):
            return

        trigger_node = TriggerNode(node)
        command_class = TriggersManager.command_from_node(node)
        if command_class is None:
            raise errors.MissingRegisteredCommandOnNodeError(node.fullPathName())
        trigger_node.set_command(
            command_class(trigger_node, TriggersManager().plugin_factory)
        )

        return trigger_node

    @classmethod
    def iterate_connected_trigger_nodes(
        cls, nodes: list[DGNode], filter_class: Type[TriggerCommand] | None = None
    ) -> Iterator[DGNode]:
        """
        Iterates over the connected trigger nodes from the given nodes.

        :param nodes: nodes to iterate the connected trigger nodes from.
        :param filter_class: optional command class to filter the trigger nodes.
        :return: iterator of connected trigger nodes.
        """

        visited: list[DGNode] = []
        for node in nodes:
            if node in visited:
                continue
            visited.append(node)

            if filter_class is None or (
                filter_class is not None and cls.has_command_type(node, filter_class)
            ):
                yield node

            for meta_node in base.connected_meta_nodes(node):
                if (
                    meta_node not in visited
                    and filter_class is None
                    or (
                        filter_class is not None
                        and cls.has_command_type(meta_node, filter_class)
                    )
                ):
                    visited.append(meta_node)
                    yield meta_node

    @staticmethod
    def has_command_type(node: DGNode, command_type: Type[TriggerCommand]) -> bool:
        """
        Returns whether the given node has the given command type.

        :param node: node to check if it has the given command type.
        :param command_type: command type to check.
        :return: True if the node has the given command type, False otherwise.
        """

        from .manager import TriggersManager

        command_class = TriggersManager.command_from_node(node)
        if not command_class:
            return False

        return (
            True
            if issubclass(command_class, command_type) or command_class == command_type
            else False
        )

    def set_command(
        self,
        command: TriggerCommand,
        modifier: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ):
        """
        Sets the trigger command instance, which will result in trigger attributes
        being created.

        :param command: command to set for this trigger node instance. If a command
            already exists, it will be replaced with the given command.
        :param modifier: optional modifier to use when setting the command.
        :param apply: whether to apply the modifier or not.
        :raises errors.NodeHasExistingCommandError: If the node already has a command.
        """

        if self._command:
            raise errors.NodeHasExistingCommandError(
                f"{command.ID}: {self._node.fullPathName()}"
            )

        self._command = command

        if not self._node.hasAttribute(self.TRIGGER_ATTR_NAME):
            self._create_attributes(modifier, apply=apply)
            self._command.on_create(modifier)
            if apply and modifier is not None:
                modifier.doIt()

    def is_command_type(self, command_type: TriggerCommand) -> bool:
        """
        Returns whether the trigger node has the given command type.

        :param command_type: command type to check.
        :return: True if the trigger node has the given command type, False otherwise.
        """

        command = self._command
        return True if command and isinstance(command, command_type) else False

    def is_command_base_type(self, base_type: int) -> bool:
        """
        Returns whether the trigger node has the given base type.

        :param base_type: base type to check.
        :return: True if the trigger node has the given base type, False otherwise.
        """

        command = self._command
        return True if command and command.BASE_TYPE == base_type else False

    def attributes(self) -> list[dict]:
        """
        Returns the list of attributes which will be added to the trigger node.

        :return: list of attributes.
        """

        command_id = self._command.ID if self._command else ""
        attrs = [
            {
                "name": constants.COMMAND_TYPE_ATTR_NAME,
                "type": attributetypes.kMFnDataString,
                "value": command_id,
                "locked": True,
            }
        ]
        if self._command:
            attrs.extend(self._command.attributes())

        return attrs

    def delete_triggers(
        self, modifier: OpenMaya.MDGModifier | None = None, apply: bool = True
    ):
        """
        Deletes the trigger attributes on the node.

        :param modifier: optional modifier to use when deleting the attributes.
        :param apply: whether to apply the modifier or not.
        """

        if not self._node.hasAttribute(self.TRIGGER_ATTR_NAME):
            return

        self._node.deleteAttribute(self.TRIGGER_ATTR_NAME, modifier)
        if modifier is not None and apply:
            modifier.doIt()

    def _create_attributes(
        self, modifier: OpenMaya.MDGModifier | None = None, apply: bool = True
    ):
        """
        Internal function that creates the trigger command attributes on the node.

        :param modifier: optional modifier to use when creating the attributes.
        :param apply: whether to apply the modifier or not.
        :raises ValueError: If the node already has the trigger attribute.
        """

        if self._node.hasAttribute(self.TRIGGER_ATTR_NAME):
            raise ValueError(
                f"Node already has trigger attribute: {self._node.fullPathName()}"
            )

        attributes = self.attributes()
        new_attributes: list[dict] = []
        for child in attributes:
            if self._node.hasAttribute(child["name"]):
                continue
            new_attributes.append(child)
        if not new_attributes:
            return

        self._node.addCompoundAttribute(
            self.TRIGGER_ATTR_NAME, attributes, mod=modifier, apply=apply
        )
        if modifier is not None and apply:
            modifier.doIt()
