from __future__ import annotations

from typing import Dict

from overrides import override
from Qt.QtCore import Qt, Signal, Property
from Qt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from tp.preferences.interfaces import core
from tp.common.qt.widgets import buttongroups, stack, dividers, buttons


class LineTabWidget(QWidget):
	"""
	Custom tab widget that represents tabs in one line with underline decoration. Also supports the alignment of the
	tabs
	"""

	def __init__(self, alignment: Qt.AlignmentFlag = Qt.AlignCenter, parent: QWidget | None = None):
		super().__init__(parent)

		self._theme_pref = core.theme_preference_interface()

		self._main_layout = QVBoxLayout()
		self._main_layout.setSpacing(0)
		self._main_layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self._main_layout)

		self._tool_button_group = UnderlineButtonGroup(tab=self, parent=self)
		self._bar_layout = QHBoxLayout()
		self._bar_layout.setContentsMargins(0, 0, 0, 0)
		if alignment == Qt.AlignCenter:
			self._bar_layout.addStretch()
			self._bar_layout.addWidget(self._tool_button_group)
			self._bar_layout.addStretch()
		elif alignment == Qt.AlignLeft:
			self._bar_layout.addWidget(self._tool_button_group)
			self._bar_layout.addStretch()
		elif alignment == Qt.AlignRight:
			self._bar_layout.addStretch()
			self._bar_layout.addWidget(self._tool_button_group)
		self._stack = stack.SlidingOpacityStackedWidget()
		self._tool_button_group.checkedChanged.connect(self._stack.setCurrentIndex)

		self._main_layout.addLayout(self._bar_layout)
		self._main_layout.addWidget(dividers.Divider())
		self._main_layout.addSpacing(5)
		self._main_layout.addWidget(self._stack)

		self._theme_size = self._theme_pref.theme_data().default_size

	@property
	def tool_button_group(self) -> UnderlineButtonGroup:
		return self._tool_button_group

	def add_tab(self, widget: QWidget, button_data: Dict) -> QPushButton:
		"""
		Adds a new tab and creates a button to select that new tab with the given button data..

		:param QWidget widget: widget to add into the tab.
		:param Dict button_data: dictionary with the data to create the button. e.g:
			{
				'text': 'Hello World',
				'checkable': True,
				'checked': False,
				'shortcut': 'Ctrl+T',
				'tooltip': 'This is the button tooltip',
				'icon': QIcon,
				'clicked': Callable,
				'toggled': Callable,
				'combine': 'horizontal',
				'position': 'left'
			}
		:return: added button.
		:rtype: QPushButton
		"""

		self._stack.addWidget(widget)
		new_button = self._tool_button_group.add_button(button_data, self._stack.count() - 1)
		return new_button

	def append_widget(self, widget: QWidget):
		"""
		Adds the given widget into the line tabs right position.

		:param QWidget widget: widget to add.
		"""

		self._bar_layout.addWidget(widget)

	def insert_widget(self, widget: QWidget):
		"""
		Inserts the given widget into the line tabs left position.

		:param QWidget widget: widget to insert.
		"""

		self._bar_layout.insertWidget(0, widget)

	def _get_theme_size(self) -> int:
		"""
		Returns line tab size.

		:return: line tab size.
		:rtype: int
		"""

		return self._theme_size

	def _set_theme_size(self, value: int):
		"""
		Sets line tab size.

		:param int value: line tab size.
		"""

		self._theme_size = value
		self._tool_button_group.update_size(self._theme_size)
		self.style().polish(self)

	theme_size = Property(int, _get_theme_size, _set_theme_size)


class UnderLineButton(buttons.BaseToolButton):
	"""
	Styled button with a line under it.
	"""

	def __init__(self, parent: QWidget | None = None):
		super(UnderLineButton, self).__init__(parent=parent)

		self.setCheckable(True)


class UnderlineButtonGroup(buttongroups.BaseButtonGroup):
	"""
	Custom button group implementation that contains underlined buttons.
	"""

	checkedChanged = Signal(int)

	def __init__(self, tab: LineTabWidget, parent: QWidget | None = None):
		super().__init__(parent=parent)

		self._line_tab = tab

		self.set_spacing(1)
		self._button_group.setExclusive(True)
		self._button_group.buttonClicked[int].connect(self.checkedChanged.emit)

	@override(check_signature=False)
	def create_button(self, data: Dict) -> UnderLineButton:
		new_button = UnderLineButton(parent=self)
		if data.get('image'):
			new_button.image(data.get('image'))
		if data.get('text'):
			if data.get('image') or data.get('icon'):
				new_button.text_beside_icon()
			else:
				new_button.text_only()
		else:
			new_button.icon_only()

		new_button.theme_size = self._line_tab.theme_size

		return new_button

	def update_size(self, size: int):
		"""
		Updates button size.

		:param int size: button size to set.
		"""

		for button in self._button_group.buttons():
			button.theme_size = size

	def _get_checked(self) -> int:
		"""
		Intenral function that returns current checked button's ID.
		:return: checked button ID.
		:rtype: int
		"""

		return self._button_group.checkedId()

	def _set_checked(self, value: int):
		"""
		Sets current checked button's ID.

		:param int value: checke button ID.
		"""

		btn = self._button_group.button(value)
		btn.setChecked(True)
		self.checkedChanged.emit(value)

	theme_checked = Property(int, _get_checked, _set_checked, notify=checkedChanged)
