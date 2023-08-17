from __future__ import annotations

import typing
from typing import Tuple, List, Dict

import maya.api.OpenMaya as OpenMaya

from tp.common import plugin
from tp.common.python import decorators
from tp.maya.api import base
from tp.maya.libs.triggers import consts

if typing.TYPE_CHECKING:
	from tp.maya.libs.triggers.triggernode import TriggerNode
	from tp.maya.libs.triggers.markingmenu import MarkingMenuLayout


class TriggerCommand(plugin.Plugin):

	ID = ''
	BASE_TYPE = consts.TRIGGER_MENU_TYPE

	def __init__(self, trigger: TriggerNode | None = None, factory: plugin.PluginFactory | None = None):
		super().__init__(factory)

		self._trigger = trigger
		self._node = trigger.node

	def __repr__(self) -> str:
		return f'<{self.__class__.__name__} id: {self.ID}>'

	@property
	def node(self) -> base.DGNode:
		return self._node

	@decorators.abstractmethod
	def execute(self, *args: Tuple, **kwargs: Dict) -> MarkingMenuLayout:
		"""
		Function called when trigger command is executed.
		Must be overridden in child classes.
		"""

		raise NotImplementedError

	def attributes(self) -> List[Dict]:
		"""
		Retunrs list of unique attributes that should be created within trigger node.

		:return: list of attributes.
		:rtype: List[Dict]
		"""

		return []

	def on_create(self, modifier: OpenMaya.MDGModifier | None = None):
		"""
		Function that is called when the command gets created on the node.

		:param OpenMaya.MDGModifier or None modifier: optional modifier to handle changes with.
		"""

		pass
