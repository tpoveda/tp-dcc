from __future__ import annotations

import uuid

from overrides import override

from tp.common.qt import api as qt
from tp.common.resources import api as resources


class EditorView(qt.QDockWidget):

	# This is the unique ID for the editor. This ID MUST be unique.
	ID = None

	# version of the editor.
	VERSION = 0

	# nice name that will appear in the dock widget top bar area in the UI.
	NAME = 'Base Editor'

	#  tooltip that will appear if the user leaves the cursor on top of the editor in the UI.
	TOOLTIP = 'Default Tooltip'

	# default editor dock widget area
	DEFAULT_DOCK_AREA = qt.Qt.LeftDockWidgetArea

	# flag that defines whether the editor can be closed by the users.
	CLOSABLE = True

	# flag that defines whether an editor can have multiple instances opened at the same time.
	IS_SINGLETON = False

	closed = qt.Signal(str)

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent)

		self._uuid = uuid.uuid4()

		if self.CLOSABLE:
			self.setFeatures(qt.QDockWidget.AllDockWidgetFeatures)
		else:
			self.setFeatures(qt.QDockWidget.DockWidgetFloatable | qt.QDockWidget.DockWidgetMovable)
		self.setAllowedAreas(qt.Qt.AllDockWidgetAreas)
		self.setObjectName(self.unique_name())
		self.setFloating(False)
		self.setWindowIcon(self.icon())
		self.setWindowTitle(self.NAME)

	@staticmethod
	def icon() -> qt.QIcon:
		"""
		Returns editor icon.

		:return: editor icon.
		:rtype: QIcon
		"""

		return resources.icon('tpdcc')

	@override(check_signature=False)
	def show(self, **kwargs) -> None:
		self.setWindowTitle(self.NAME)
		super().show()

	@override
	def closeEvent(self, event: qt.QCloseEvent) -> None:

		self.teardown()
		self.closed.emit(self.ID)

		super().closeEvent(event)

	def run(self):
		"""
		Function that shows the editor view.
		"""

		self.setWindowTitle(self.NAME)
		self.show()

	def teardown(self):
		"""
		Function that is called just before editor is closed.
		"""

		pass

	def unique_name(self) -> str:
		"""
		Returns unique name for this editor.

		:return: editor unique name.
		:rtype: str
		"""

		return f'{self.ID}::{self._uuid}'
