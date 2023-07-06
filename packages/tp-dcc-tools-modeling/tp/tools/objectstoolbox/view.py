from __future__ import annotations

from typing import Dict

from tp.common.qt import api as qt


def tooltips() -> Dict:

	return {
		'create_sphere': """
		Creates a Polygon Sphere. 
		Matches to the current selection, if there is a selection.
		
		Hotkey: None
		"""
	}


class ObjectsToolboxView(qt.QWidget):
	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._tooltips = tooltips()

		self._setup_widgets()
		self._setup_layouts()
		self._setup_signals()

	def _setup_widgets(self):
		"""
		Internal function that setup view widgets.
		"""

		self._objects_collapsable = qt.CollapsableFrameThin('Objects', collapsed=False, parent=self)

		self._sphere_button =

	def _setup_layouts(self):
		"""
		Internal function that setup view layouts.
		"""

		self._main_layout = qt.vertical_layout(
			margins=(qt.consts.WINDOW_SIDE_PADDING, qt.consts.WINDOW_TOP_PADDING, qt.consts.WINDOW_SIDE_PADDING),
			spacing=qt.consts.DEFAULT_SPACING)
		self.setLayout(self._main_layout)

		self._primitives_layout = qt.horizontal_layout(spacing=qt.consts.SPACING)
		self._objects_layout = qt.grid_layout(
			spacing=qt.consts.SPACING,
			margins=(qt.consts.DEFAULT_SPACING, qt.consts.SMALL_SPACING, qt.consts.DEFAULT_SPACING, 0))
		self._objects_collapsable.add_layout(self._primitives_layout)
		self._objects_collapsable.add_layout(self._objects_layout)
		self._objects_collapsable_layout = qt.vertical_layout(margins=(0, 0, 0, 0))
		self._objects_collapsable_layout.addWidget(self._objects_collapsable)

		self._main_layout.addLayout(self._objects_collapsable_layout)

	def _setup_signals(self):
		"""
		Internal function that setup signal connections.
		"""

		pass
