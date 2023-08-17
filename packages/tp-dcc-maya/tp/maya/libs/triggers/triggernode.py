from __future__ import annotations

import typing
from typing import Iterator, List, Dict, Type

import maya.api.OpenMaya as OpenMaya

from tp.maya.api import base, exceptions, attributetypes
from tp.maya.meta import base as meta_base
from tp.maya.libs.triggers import consts, errors, managers

if typing.TYPE_CHECKING:
	from tp.maya.libs.triggers.triggercommand import TriggerCommand


def create_trigger_for_node(
		node: base.DGNode, command_name: str, modifier: OpenMaya.MDGModifier | None = None) -> TriggerNode:
	"""
	Creates a trigger on the given node.

	:param base.DGNode node: node to create the trigger on.
	:param str command_name: name of the trigger command to add.
	:param OpenMaya.MDGModifier or None modifier: optional modifier to use to create trigger node.
	:return: newly created trigger node.
	:rtype: TriggerNode
	:raises errors.NodeHasExistingTriggerError: if given node already has a trigger on it.
	"""

	triggers_manager = managers.TriggersManager()
	found_command = triggers_manager.command(command_name)
	if TriggerNode.has_trigger(node):
		raise errors.NodeHasExistingTriggerError(f'Node already has a trigger: {node}')

	new_trigger_node = TriggerNode(node)
	new_trigger_node.set_command(found_command(new_trigger_node, triggers_manager.factory), modifier=modifier)

	return new_trigger_node


def iterate_connected_trigger_nodes(
		nodes: List[base.DGNode], filter_class: Type | None = None) -> Iterator[TriggerNode]:
	"""
	Generator function that iterates all trigger nodes within the given node.

	:param List[base.DGNode] nodes: nodes to iterate to search for trigger nodes.
	:param Type or None filter_class: optional class to filter by.
	:return: iterated trigger nodes.
	:rtype: Iterator[TriggerNode]
	"""

	visited = []
	for node in nodes:
		if node in visited:
			continue
		visited.append(node)
		if filter_class is None or (filter_class is not None and TriggerNode.has_command_type(node, filter_class)):
			yield node
		for i in meta_base.connected_meta_nodes(node):
			if i not in visited and filter_class is None or (
					filter_class is not None and TriggerNode.has_command_type(i, filter_class)):
				visited.append(i)
				yield i


def command_from_node(node: base.DGNode) -> TriggerCommand | None:
	"""
	Returns the command class object from the given node.

	:param base.DGNode node: node to get command from.
	:return: found trigger command.
	:rtype: TriggerCommand or None
	"""

	trigger_type_attr = node.attribute(consts.TRIGGER_COMMAND_TYPE_ATTR_NAME)
	if trigger_type_attr is None:
		return None

	trigger_type = trigger_type_attr.value()

	return managers.TriggersManager().command(trigger_type)


class TriggerNode:

	def __init__(self, node: base.DGNode):
		self._node = node
		self._command = None				# type: TriggerCommand

	def __repr__(self) -> str:
		return f'<{self.__class__.__name__}> command: {self._command}, node: {self._node}'

	def __eq__(self, other: TriggerNode) -> bool:
		return self._node == other.node

	def __ne__(self, other: TriggerNode) -> bool:
		return self._node != other.node

	@property
	def node(self) -> base.DGNode:
		return self._node

	@property
	def command(self) -> TriggerCommand:
		return self._command

	@staticmethod
	def from_node(node: base.DGNode) -> TriggerNode | None:
		"""
		Returns a trigger node instance from the given node.

		:param base.DGNode node: node to cast.
		:return: trigger node instance.
		:rtype: TriggerNode or None
		:raises errors.MissingRegisteredCommandOnNodeError: if node has no trigger command defined.
		"""

		if not TriggerNode.has_trigger(node, strict=True):
			return

		trigger_node = TriggerNode(node)
		command = command_from_node(node)
		if command is None:
			raise errors.MissingRegisteredCommandOnNodeError(node.fullPathName())
		trigger_node.set_command(command(trigger_node, managers.TriggersManager().factory))

		return trigger_node

	@staticmethod
	def has_trigger(node: base.DGNode, strict: bool = False) -> bool:
		"""
		Returns whether given node contains a trigger or connected meta nodes has a trigger.

		:param base.DGNode node: node to check triggers of.
		:param bool strict: whether to skip check connected meta nodes.
		:return: True if node has a trigger; False otherwise.
		:rtype: bool
		"""

		if node.hasAttribute(consts.TRIGGER_ATTR_NAME):
			return True

		if strict:
			return False

		attached_meta = meta_base.connected_meta_nodes(node)
		for i in attached_meta:
			if i.hasAttribute(consts.TRIGGER_ATTR_NAME):
				return True

		return False

	@staticmethod
	def has_command_type(node: base.DGNode, command_type: Type) -> bool:
		"""
		Returns whether the given node has a command of the given type.

		:param base.DGNode node: node to search.
		:param Type command_type: command type.
		:return: True if given node has a command of given type; False otherwise.
		:rtype: bool
		"""

		callable_command = command_from_node(node)
		if callable_command is None:
			return False

		if issubclass(callable_command, command_type) or callable_command == command_type:
			return True

		return False

	def is_command_type(self, command_type: Type) -> bool:
		"""
		Returns whether current command is an instance of given class.

		:param Type command_type: command type to check against.
		:return: True if command is an instance of given class; False otherwise.
		:rtype: bool
		"""

		command = self._command
		if not command:
			return False
		if isinstance(command, command_type):
			return True

		return False

	def is_command_base_type(self, base_type: Type) -> bool:
		"""
		Returns whether current command is an instance of given class.

		:param Type base_type: base type to check against.
		:return: True if command is an instance of given class; False otherwise.
		:rtype: bool
		"""

		command = self._command
		if not command:
			return False

		return command.BASE_TYPE == base_type

	def set_command(self, command: TriggerCommand, modifier: OpenMaya.MDGModifier | None = None, apply: bool = True):
		"""
		Sets the trigger command instance, which will result in trigger attributes being created witin the wrapped
		triggered node.

		:param TriggerCommand command: trigger command instance to set.
		:param OpenMaya.MDGModifier or None modifier: optional modifier to use.
		:param bool apply: whether to immediately execute command functionality.
		:raises errors.NodeHasExistingCommandError: if a trigger command is already set.
		"""

		if self._command:
			raise errors.NodeHasExistingCommandError(f'{command.ID}: {self._node.fullPathName()}')

		self._command = command

		if not self._node.hasAttribute(consts.TRIGGER_ATTR_NAME):
			self._create_attributes(modifier, apply=apply)
			self._command.on_create(modifier=modifier)
			if apply and modifier is not None:
				modifier.doIt()

	def attributes(self) -> List[Dict]:
		"""
		Returns a list of attributes which will be added to the wrapped node.

		:return: list of attributes.
		:rtype: List[Dict]
		"""

		command_id = self._command.ID if self._command else ''

		attrs = [
			{'name': consts.TRIGGER_COMMAND_TYPE_ATTR_NAME, 'type': attributetypes.kMFnDataString, 'value': command_id}
		]
		if self._command:
			attrs.extend(self._command.attributes())

		return attrs

	def delete_triggers(self, modifier: OpenMaya.MDGModifier | None = None, apply: bool = True):
		"""
		Deletes the trigger from the wrapped node.

		:param OpenMaya.MDGModifier or None modifier: optional modifier to use.
		:param bool apply: whether to immediately execute command functionality.
		"""

		self._node.deleteAttribute(consts.TRIGGER_ATTR_NAME, mod=modifier)
		if modifier is not None and apply:
			modifier.doIt()

	def _create_attributes(self, modifier: OpenMaya.MDGModifier | None = None, apply: bool = True):
		"""
		Internal function that creates the trigger attributes within wrapped node.

		:param OpenMaya.MDGModifier or None modifier: optional modifier to use.
		:param bool apply: whether to immediately execute command functionality.
		:raises exceptions.AttributeAlreadyExistsError: if triggers attribute already exists within wrapped node.
		"""

		if self._node.hasAttribute(consts.TRIGGER_ATTR_NAME):
			raise exceptions.AttributeAlreadyExistsError()

		attrs = self.attributes()
		new_attributes = []
		for child in attrs:
			if self._node.hasAttribute(child['name']):
				continue
			new_attributes.append(child)
		if not new_attributes:
			return
		self._node.addCompoundAttribute(consts.TRIGGER_ATTR_NAME, attrs, mod=modifier, apply=apply)
		if modifier is not None and apply:
			modifier.doIt()
