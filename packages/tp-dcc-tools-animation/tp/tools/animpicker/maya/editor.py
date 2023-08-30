from __future__ import annotations

import typing
from typing import Tuple
from functools import partial

import maya.cmds as cmds

from tp.maya.cmds import gui
from tp.common.qt import api as qt
from tp.tools.animpicker.views import editor

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.widgets.tabs import EditableTabWidget
	from tp.tools.animpicker.maya.controller import MayaAnimPickerEditorController


class MayaAnimPickerEditorWidget(editor.AnimPickerEditorWidget):
	def __init__(
			self, controller: MayaAnimPickerEditorController, parent: qt.QWidget | None = None):
		super().__init__(controller=controller, parent=parent)

		self._setup_popup_menu()

	def _setup_popup_menu(self):
		"""
		Internal function that setup popup menu that appears when user presses Ctrl + Right click on top of the picker
		editor view.
		"""

		self._tab_maya_layout = ''
		self._tab_maya_layout = gui.to_maya_object(self._tab_widget)

		cmds.popupMenu(
			'animPicker:popupMenu', parent=self._tab_maya_layout, markingMenu=True, ctrlModifier=True, button=3,
			postMenuCommand=self._check_state_for_popup_menu)

		cmds.menuItem(
			'animPicker:selectAllMenu', label='Select All', boldFont=True, radialPosition='N', sourceType='python',
			command=self.select_current_all_items)
		cmds.menuItem(
			'animPicker:restAllMenu', label='Reset All', boldFont=True, radialPosition='W', sourceType='python',
			command=self.reset_all)
		cmds.menuItem(
			'animPicker:resetTransformMenu', label='Reset Transform', radialPosition='NW', sourceType='python',
			command=self.reset_transform)
		cmds.menuItem(
			'animPicker:resetDefinedMenu', label='Reset Defined', radialPosition='SW', sourceType='python',
			command=self.reset_defined)
		cmds.menuItem(
			'animPicker:keyAllMenu', label='Key All', boldFont=True, radialPosition='E', sourceType='python',
			command=self.key_all)
		cmds.menuItem(
			'animPicker:keyTransformMenu', label='Key Transform', radialPosition='NE', sourceType='python',
			command=self.key_transform)
		cmds.menuItem(
			'animPicker:keyDefinedMenu', label='Key Defined', radialPosition='SE', sourceType='python',
			command=self.key_defined)
		cmds.menuItem(
			'animPicker:showSelectListMenu', label='List Selected', boldFont=True, radialPosition='S',
			sourceType='python', command=self.show_selected_list)
		cmds.setParent('..', menu=True)

	def _check_state_for_popup_menu(self, *args: Tuple[str, str]):
		"""
		Internal function that is called after the Maya popup menu is opened. It updates the checkbox state of the
		popup menu items based on current scene state.

		:param Tuple[str, str] args: tuple containing the popup menu name and the name of the popup menu parent.
		"""

		pass

		# item_selected = self.is_item_selected()
		# current_scene_coop = self.is_current_scene_coop()
		# can_assign = False
		#
		# cmds.menuItem('animPicker:createButtonGroupMenu', edit=True, checkBox=item_selected)
		# cmds.menuItem('animPicker:coopMenu', edit=True, checkBox=current_scene_coop)
		# cmds.menuItem('animPicker:assignMenu', edit=True, checkBox=can_assign)
