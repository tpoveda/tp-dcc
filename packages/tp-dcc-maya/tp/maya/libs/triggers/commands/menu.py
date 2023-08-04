from __future__ import annotations

from typing import Tuple, List, Dict
from operator import itemgetter

from overrides import override

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.maya.api import base, attributetypes
from tp.maya.cmds import decorators
from tp.maya.libs.triggers import consts, errors, markingmenu, managers, triggercallbacks, triggernode, triggercommand

TOP_LEVEL_MENU_NAME = 'tpTriggerMenu'


@decorators.undo
@triggercallbacks.block_selection_callback_decorator
def build_trigger_menu(parent_menu: str, node_name: str) -> bool:
	"""
	Handles the creation of the trigger menu for the given node.

	:param str parent_menu: Maya prent menu name.
	:param str node_name: initial node (under the mouse pointer).
	:return: True if menu was successfully created; False otherwise.
	:rtype: bool
	"""

	context_info = gather_menus_from_nodes(node_name)
	if not context_info:
		return False

	marking_menu_layout = context_info['layout']
	overrides = False

	if marking_menu_layout:
		if not marking_menu_layout.solve():
			return overrides
		markingmenu.MarkingMenu.build_from_marking_menu_layout_data(
			marking_menu_layout, TOP_LEVEL_MENU_NAME, parent_menu, options={}, arguments={'nodes': context_info['nodes']})
		overrides = True

	return overrides


def gather_menus_from_nodes(node_name: str | None = None) -> Dict:
	"""
	Returns the marking menus info for the node with given name.

	:param str node_name: name of the node.
	:return: found menus.
	:rtype: Dict
	"""

	node_name = node_name or ''
	selected_nodes = list(base.selected())

	if cmds.objExists(node_name):
		trigger_node = base.node_by_name(node_name)
		if trigger_node not in selected_nodes:
			selected_nodes.insert(0, trigger_node)
	if not selected_nodes:
		return {}

	trigger_nodes = list(triggernode.iterate_connected_trigger_nodes(selected_nodes, filter_class=TriggerMenuCommand))
	if not trigger_nodes:
		return {}

	layouts = []
	visited = set()
	for menu_node in trigger_nodes:
		trigger = triggernode.TriggerNode.from_node(menu_node)
		cmd = trigger.command
		menu_id = cmd.menu_id()
		if menu_id in visited or not menu_id:
			continue
		visited.add(menu_id)
		layout = cmd.execute({'nodes': selected_nodes})
		layouts.append(layout)
	if not layouts:
		return {}

	layouts.sort(key=itemgetter('sortOrder'), reverse=True)

	return {'nodes': selected_nodes, 'layout': layouts[-1]}


class TriggerMenuCommand(triggercommand.TriggerCommand):

	ID = 'triggerMenu'

	@override
	def attributes(self) -> List[Dict]:

		return [
			{'name': consts.TRIGGER_COMMAND_ATTR_NAME, 'type': attributetypes.kMFnDataString, 'locked': True}
		]

	def set_menu(self, menu_id: str, mod: OpenMaya.MDGModifier | None = None):
		"""
		Sets the current menu layout ID for this command on the node.

		:param str menu_id: ID of the marking menu layout to set.
		:param OpenMaya.MDGModifier or None mod: optional modifier to use to set marking menu layout ID attribute.
		"""

		if not managers.MarkingMenusManager().has_menu(menu_id):
			raise errors.MissingMarkingMenu(f'No marking menu registered: {menu_id}')

		attr = self._node.attribute(consts.TRIGGER_COMMAND_ATTR_NAME)
		try:
			attr.lock(False)
			attr.set(menu_id, mod=mod)
		finally:
			attr.lock(True)

	def menu_id(self) -> str:
		"""
		Returns the internal ID of the marking menu layout.

		:return: marking menu layout ID.
		:rtype: str
		"""

		attr = self._node.attribute(consts.TRIGGER_COMMAND_ATTR_NAME)
		return attr.value() if attr is not None else ''

	@override(check_signature=False)
	def execute(self, arguments: Dict) -> markingmenu.MarkingMenuLayout:

		menu_id = self.menu_id()
		if not menu_id:
			return markingmenu.MarkingMenuLayout()

		manager = managers.MarkingMenusManager()
		menu_type = manager.menu_type(menu_id)
		layout = markingmenu.MarkingMenuLayout(**{'items': {}})
		if menu_type == manager.STATIC_MARKING_MENU_LAYOUT_TYPE:
			new_layout = markingmenu.find_layout(menu_id)
		else:
			menu_plugin = manager.menu_factory.load_plugin(menu_id)
			new_layout = menu_plugin.execute(layout, arguments=arguments)
			layout.merge(new_layout)

		if new_layout:
			layout = new_layout

		return layout
