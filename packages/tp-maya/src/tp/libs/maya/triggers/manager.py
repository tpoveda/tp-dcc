from __future__ import annotations

import typing
from typing import Type

from maya.api import OpenMaya

from . import constants, errors
from .node import TriggerNode
from .command import TriggerCommand
from ... import plugin
from ...python.decorators import Singleton

if typing.TYPE_CHECKING:
    from ..wrapper import DGNode


class TriggersManager(metaclass=Singleton):
    """
    Singleton class that manages all trigger commands.
    """

    TRIGGER_ENV_VAR = constants.TRIGGER_ENV_VAR

    def __init__(self):
        super().__init__()

        self._plugin_factory = plugin.PluginFactory(
            interface=TriggerCommand, plugin_id="ID", name="triggersManager"
        )
        self._plugin_factory.register_paths_from_env_var(self.TRIGGER_ENV_VAR)

    @classmethod
    def command_from_node(cls, node: DGNode) -> Type[TriggerCommand] | None:
        """
        Returns a trigger command from a node.

        :param node: node to get the command from.
        :return: trigger command class instance.
        """

        trigger_type_attr = node.attribute(constants.COMMAND_TYPE_ATTR_NAME)
        if not trigger_type_attr:
            return None

        trigger_type = trigger_type_attr.value()
        return cls().command(trigger_type)

    @classmethod
    def create_trigger_from_node(
        cls,
        node: DGNode,
        command_name: str,
        modifier: OpenMaya.MDGModifier | None = None,
    ):
        """
        Creates a trigger from a node.

        :param node: DGNode, node to create the trigger from.
        :param command_name: str, name of the command to create.
        :param modifier: MDGModifier, modifier to use to create the trigger.
        :return: DGNode, created trigger node.
        """

        trigger_command_class = cls().command(command_name)
        if TriggerNode.has_trigger(node):
            raise errors.NodeHasExistingTriggerError(
                f"Node already has a trigger: {node}"
            )
        trigger_node = TriggerNode(node)
        trigger_node.set_command(
            trigger_command_class(trigger_node, cls().plugin_factory), modifier=modifier
        )

        return trigger_node

    @property
    def plugin_factory(self) -> plugin.PluginFactory:
        """
        Returns the plugin factory instance.

        :return: PluginFactory, plugin factory instance.
        """

        return self._plugin_factory

    def commands(self) -> dict[str, Type[TriggerCommand]]:
        """
        Returns all trigger commands.

        :return: dictionary with all trigger commands.
        """

        # noinspection PyUnresolvedReferences
        return {
            plugin_class.ID: plugin for plugin_class in self._plugin_factory.plugins()
        }

    def command_types(self) -> list[str]:
        """
        Returns all trigger command types.

        :return: list of trigger command types.
        """

        return list(self.commands().keys())

    def command(self, command_name: str) -> Type[TriggerCommand]:
        """
        Returns a trigger command by name.

        :param command_name: str, name of the command to return.
        :return: TriggerCommand, trigger command instance.
        """

        return self._plugin_factory.get_plugin_from_id(command_name)
