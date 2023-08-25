from __future__ import annotations

import typing
from typing import List

from overrides import override
import maya.cmds as cmds

from tp.core import log
from tp.common.qt import api as qt
from tp.tools.animpicker import controller
from tp.tools.animpicker.maya import utils

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.widgets.graphics import DropScene

logger = log.modelLogger


class MayaAnimPickerController(controller.AnimPickerController):

	@override
	def filter_picker_nodes(self) -> List[str]:
		return utils.filter_picker_nodes()


class MayaAnimPickerViewerController(controller.AnimPickerViewerController):

	sceneChanged = qt.Signal(object)

	def __init__(self):
		super().__init__()

		self._scene = None					# type: DropScene

	@property
	def scene(self) -> DropScene:
		return self._scene

	@scene.setter
	def scene(self, value: DropScene):
		self._scene = value
		self.sceneChanged.emit(self._scene)

	@override
	def filter_picker_nodes(self) -> List[str]:
		return utils.filter_picker_nodes()


class MayaAnimPickerEditorController(MayaAnimPickerViewerController):

	canAssignDataChanged = qt.Signal(bool)

	def __init___(self):
		super().__init__()

		self._can_assign_data = False

	@property
	def can_assign_data(self) -> bool:
		return self._can_assign_data

	@can_assign_data.setter
	def can_assign_data(self, flag: bool):
		self._can_assign_data = flag
		self.canAssignDataChanged.emit(self._can_assign_data)







