from __future__ import annotations

import typing

from overrides import override

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.controller import AnimPickerController


class AnimPickerView(qt.FramelessWindow):

	WINDOW_SETTINGS_PATH = 'tp/animpicker'
	VERSION = '0.0.1'

	def __init__(self, controller: AnimPickerController, parent: qt.QWidget | None = None):

		self._controller = controller

		super().__init__(title=f'Animation Picker {self.VERSION}', width=800, height=600, parent=parent)

	@override
	def setup_ui(self):
		super().setup_ui()

		self.set_main_layout(qt.vertical_layout(margins=(6, 6, 6, 6)))

	@override
	def setup_signals(self):
		super().setup_signals()
