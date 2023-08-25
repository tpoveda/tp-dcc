from __future__ import annotations

import typing

import maya.cmds as cmds

from tp.maya.cmds import gui
from tp.common.qt import api as qt
from tp.tools.animpicker.views import viewer

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.controller import AnimPickerViewerController


class MayaAnimPickerViewer(viewer.AnimPickerViewerWidget):
	def __init__(
			self, controller: AnimPickerViewerController, parent: qt.QWidget | None = None):
		super().__init__(controller=controller, parent=parent)

		self._tab_maya_layout = None				# type: str

		self._tab_maya_layout = gui.to_maya_object(self._tab_widget)
		class_name = self.__class__.__name__

		menu = cmds.popupMenu(
			'animPicker:popupMenu', parent=self._tab_maya_layout, markingMenu=True, ctrlModifier=True, button=3)
