from __future__ import annotations

import maya.cmds as cmds

from tp.maya import api
from tp.common.python import decorators
from tp.libs.rig.freeform.library.functions import character


@decorators.add_metaclass(decorators.Singleton)
class FreeformContextMenu:

	def __init__(self):

		# scene node that menu will be build for.
		self._node: api.DGNode | api.DagNode | api.Joint | None = None

		# base menu that we populate based on the found node.
		self._menu: str = ''

		# active model panel.
		self._model_panel: str = ''

		# dictionary of menu items that get created, keyed by the menu's category.
		self._menu_dict: dict = {}

		self.create()
		self.reset()

	@staticmethod
	def refresh():
		"""
		Refreshes context menu.
		"""

		if not FreeformContextMenu().menu:
			FreeformContextMenu().create()
			FreeformContextMenu().reset()

	@property
	def menu(self) -> str:
		return self._menu

	def create(self):
		"""
		Creates the base menu associated to the current model panel (which should always be the active view).
		"""

		model_panels = cmds.getPanel(type='modelPanel')
		visible_panels = cmds.getPanel(vis=True)
		visible_model_panels = [x for x in model_panels if x in visible_panels]
		if visible_model_panels:
			self._model_panel = visible_model_panels[0]
			self._menu = cmds.popupMenu(
				parent=self._model_panel, button=1, altModifier=True, ctrlModifier=True, markingMenu=True,
				postMenuCommand=self._build_menu)

	def reset(self):
		"""
		Clears out the node and deletes all items from context menu.
		"""

		self._node = None
		self._menu_dict.clear()
		if self._menu:
			cmds.popupMenu(self._menu, edit=True, deleteAllItems=True)

	def delete(self):
		"""
		Deletes menu.
		"""

		self.reset()
		cmds.deleteUI(self._menu)
		self._menu = ''
		self._model_panel = ''

	def _build_menu(self, *_, **__):
		"""
		Internal function that resets the menu and then builds all menu items based on the selected node.
		"""

		self.reset()

		cmds.dagObjectHit(menu=self._menu)
		dag_menu = cmds.popupMenu(self._menu, query=True, itemArray=True)

		context_node = None
		if dag_menu:
			context_obj = cmds.menuItem(dag_menu[0], query=True, label=True).strip('.')
			context_node = api.node_by_name(context_obj) if context_obj else None
		selected_nodes = api.selected()
		selected_node = selected_nodes[-1] if selected_nodes else None

		self._node = context_node if context_node else selected_node
		if self._node:
			# node_name = self._node.fullPathName(partial_name=True, include_namespace=False)
			self._menu_dict['properties'] = self._build_property_menu()

	def _build_property_menu(self) -> str | None:
		"""
		Internal function that builds property menu.

		:return: created property menu.
		:rtype: str or None
		"""

		cmds.menuItem(
			'Characterize Skeleton', parent=self._menu, subMenu=True, radialPosition='S',
			command=lambda _: character.characterize_skeleton(self._node))

		return None
