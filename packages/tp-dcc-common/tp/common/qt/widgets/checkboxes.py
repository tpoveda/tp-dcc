from __future__ import annotations

from typing import Any
from functools import partial

from overrides import override
from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QLabel, QCheckBox, QHBoxLayout
from Qt.QtGui import QMouseEvent

from tp.common.qt import contexts
from tp.common.qt.widgets import layouts, menus


def checkbox(text: str = '', flag: bool = False, tooltip: str = '', parent: QWidget | None = None) -> QCheckBox:
	"""
	Creates a basic QCheckBox widget.

	:param str text: checkbox text.
	:param bool flag: true to check by default; False otherwise.
	:param str tooltip: checkbox tooltip.
	:param QWidget parent: parent widget.
	:return: newly created combo box.
	:rtype: QCheckBox
	"""

	new_checkbox = QCheckBox(text=text, parent=parent)
	new_checkbox.setChecked(flag)
	if tooltip:
		new_checkbox.setToolTip(tooltip)

	return new_checkbox


def checkbox_widget(
		text: str = '', checked: bool = False, tooltip: str = '', enable_menu: bool = True, right: bool = False,
		label_ratio: int = 0, box_ratio: int = 0, parent: QWidget | None = None) -> BaseCheckBoxWidget:
	"""
	Creates a BaseCheckbox widget instance.

	:param str text: checkbox text.
	:param bool checked: true to check by default; False otherwise.
	:param str tooltip: checkbox tooltip.
	:param bool enable_menu: whether to enable checkbox menu.
	:param bool right: whether checkbox label should be placed to the right.
	:param int label_ratio: label layout ratio.
	:param int box_ratio: combobox layout ratio.
	:param QWidget parent: parent widget.
	:return: newly created combo box.
	:rtype: BaseCheckBoxWidget
	"""

	return BaseCheckBoxWidget(
		text=text, checked=checked, tooltip=tooltip, enable_menu=enable_menu, label_ratio=label_ratio,
		box_ratio=box_ratio, right=right, parent=parent)


@menus.mixin
class BaseCheckBoxWidget(QWidget):
	"""
	Custom widget class that adds the ability for a middle/right/click menu to be added to the QCheckbox.
	"""

	leftClicked = Signal()
	middleClicked = Signal()
	rightClicked = Signal()
	stateChanged = Signal(object)

	def __init__(
			self, text: str = '', checked: bool = False, tooltip: str = '', enable_menu: bool = True,
			menu_vertical_offset: int = 20, right: bool = False, label_ratio: int = 0, box_ratio: int = 0,
			parent: QWidget | None = None):

		super().__init__(parent=parent)

		self._right = right
		self._label_ratio = label_ratio
		self._box_ratio = box_ratio
		self._checkbox = QCheckBox(text or '', parent=self)
		self._label = None											# type: QLabel
		self._main_layout = None  									# type: QHBoxLayout

		if tooltip:
			self.setToolTip(tooltip)

		self._setup_ui()
		self._setup_signals()
		self.setChecked(checked)
		self.set_text(text)

		if enable_menu:
			self._setup_menu_class(menu_vertical_offset=menu_vertical_offset)
			self.leftClicked.connect(partial(self.show_context_menu, Qt.LeftButton))
			self.middleClicked.connect(partial(self.show_context_menu, Qt.MiddleButton))
			self.rightClicked.connect(partial(self.show_context_menu, Qt.RightButton))

	def __getattr__(self, item: str) -> Any:
		if self._checkbox and hasattr(self._checkbox, item):
			return getattr(self._checkbox, item)

	@override
	def mousePressEvent(self, event: QMouseEvent) -> None:

		for mouse_button, menu_instance in self._click_menu.items():
			if menu_instance and event.button() == mouse_button:
				if mouse_button == Qt.LeftButton:
					return self.leftClicked.emit()
				elif mouse_button == Qt.MiddleButton:
					return self.middleClicked.emit()
				elif mouse_button == Qt.RightButton:
					return self.rightClicked.emit()

		super().mousePressEvent(event)

	def text(self) -> str:
		"""
		Returns checkbox text.

		:return: checkbox text.
		:rtype: str
		"""

		return self._label.text() if self._label else self._checkbox.text()

	def set_text(self, value: str):
		"""
		Sets checkbox text.

		:param str value: checkbox text to set.
		"""

		if self._label:
			self._label.setText(value)

		self._checkbox.setText('' if self._right else value)

	def set_checked_quiet(self, flag: bool):
		"""
		Sets the checkbox check status without emiting any signal.

		:param bool flag: whether checkbox is checked.
		"""

		with contexts.block_signals(self._checkbox):
			self._checkbox.setChecked(flag)

	def _setup_ui(self):
		"""
		Internal function that setup widgets.
		"""

		self._main_layout = layouts.horizontal_layout(parent=self)
		self.setLayout(self._main_layout)

		if self._right:
			self._label = QLabel(parent=self)
			self._main_layout.addWidget(self._label, self._label_ratio)
		self._main_layout.addWidget(self._checkbox, self._box_ratio)

	def _setup_signals(self):
		"""
		Internal function that setup signal connections.
		"""

		self._checkbox.stateChanged.connect(self.stateChanged.emit)
