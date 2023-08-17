from __future__ import annotations

from overrides import override
from Qt.QtCore import QEvent, QSize
from Qt.QtWidgets import QWidget

import maya.cmds as cmds

from tp.core.abstract import window
from tp.common.python import decorators
from tp.common.qt.widgets import windows
from tp.maya.cmds import gui


class MayaWindow(window.AbstractWindow):

	def __init__(self, dockable: bool = False, parent: QWidget | None = None, **kwargs):
		parent = parent or gui.maya_window()
		super().__init__(parent, **kwargs)
		self._maya = True
		self._batch = cmds.about(batch=True)
		self.set_dockable(dockable, override=True)

		self._parent_temp = None

	@classmethod
	@override(check_signature=False)
	def clear_window_instance(cls, window_id: str, delete_window: bool =True) -> dict:
		previous_instance = super(MayaWindow, cls).clear_window_instance(window_id)
		if previous_instance is None:
			return
		cls.remove_callbacks(window_instance=previous_instance)

		if previous_instance['window'].dockable():
			previous_instance['window'].signalDisconnect('_maya_docking_destroy')

		if not previous_instance['window'].is_closed():
			try:
				previous_instance['window'].close()
			except (ReferenceError, ReferenceError):
				pass

		if delete_window and previous_instance['window'].dockable():
			gui.delete_workspace_control(previous_instance['window'].ID)

		return previous_instance

	@override
	def closeEvent(self, event: QEvent):
		dockable = self.dockable()
		if not dockable:
			self.save_window_position()
		self.clear_window_instance(self.ID, delete_window=True)

		return super().closeEvent(event)

	@override
	def resize(self, w: int, h: int | None = None) -> None:
		if isinstance(w, QSize):
			h = w.height()
			w = w.width()
		if self.dockable():
			return cmds.workspaceControl(self.ID, edit=True, resizeWidth=w, resizeHeight=h)

		return super(MayaWindow, self).resize(w, h)

	@decorators.HybridMethod
	def remove_callbacks(cls, self, group=None, window_instance=None, window_id=None):
		pass


class MayaBatchWindow(windows.StandaloneWindow):
	pass
