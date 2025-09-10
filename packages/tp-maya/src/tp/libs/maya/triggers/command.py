from __future__ import annotations

import typing

from maya.api import OpenMaya
from tp.libs.plugin import Plugin, PluginsManager

from . import constants


if typing.TYPE_CHECKING:
    from ..wrapper import DGNode
    from .node import TriggerNode


class TriggerCommand(Plugin):
    """Class that defines a trigger command."""

    ID = ""
    BASE_TYPE = constants.TRIGGER_BASE_TYPE_COMMAND

    def __init__(
        self,
        trigger_node: TriggerNode | None = None,
        manager: PluginsManager | None = None,
    ):
        super().__init__(manager=manager)

        self._trigger = trigger_node
        self._node = self._trigger.node

    @property
    def node(self) -> DGNode:
        """Getter method that returns the node of the trigger command.

        :return: DGNode
        """

        return self._node

    def attributes(self) -> list[dict]:
        """Returns a list of dictionaries that define the attributes of the trigger command.

        :return: list of dictionaries that define the attributes of the trigger command.
        """

        return []

    def on_create(self, modifier: OpenMaya.MDGModifier | None = None):
        """Function that is called when the command gets created on the node, allowing for
        custom control of the command.

        :param modifier: optional modifier to use to modify the node.
        """

        pass

    def execute(self, *args, **kwargs):
        """Function that loads the marking menu layout for the command."""

        raise NotImplementedError(
            "execute function must be implemented in derived classes!"
        )
