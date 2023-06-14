from __future__ import annotations

from typing import List, Dict

from Qt.QtCore import Qt
from Qt.QtWidgets import QSizePolicy, QWidget, QBoxLayout, QButtonGroup, QPushButton
from Qt.QtGui import QIcon

from tp.common.python import decorators


class BaseButtonGroup(QWidget):
	"""
	Widget class that stores a collection of buttons.
	This class should not be instantiated directly.
	"""

	def __init__(self, orientation: Qt.AlignmentFlag = Qt.Horizontal, parent: QWidget | None = None):
		super().__init__(parent)

		self._orientation = 'horizontal' if orientation == Qt.Horizontal else 'vertical'

		self._main_layout = QBoxLayout(QBoxLayout.LeftToRight if orientation == Qt.Horizontal else QBoxLayout.TopToBottom)
		self._main_layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(self._main_layout)
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

		self._button_group = QButtonGroup()

	@property
	def button_group(self) -> QButtonGroup:
		return self._button_group

	@decorators.abstractmethod
	def create_button(self, data: Dict) -> QPushButton:
		"""
		Creates a new button for this group.

		:param Dict data: dictionary with the data to create the button. e.g:
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
		:return: newly created button intsance.
		:rtype: QPushButton
		"""

		raise NotImplementedError()

	def set_spacing(self, value: int):
		"""
		Sets the layout spacing for this widget.

		:param int value: main layout spacing.
		"""

		self._main_layout.setSpacing(value)

	def add_button(self, data: Dict | str | QIcon, index: int | None = None) -> QPushButton:
		"""
		Adds a new button into this group.

		:param Dict data: dictionary with the data to create the button. e.g:
			{
				'text': 'Hello World',
				'checkable': True,
				'checked': False,
				'shortcut': 'Ctrl+T',
				'tooltip': 'This is the button tooltip',
				'icon': QIcon,
				'clicked': Callable,
				'toggled': Callable,
				'combine': 'horizontal'
				'position': 'left'
			}
		:param int or None index: optional logical position of the button within the group.
		:return: added button.
		:rtype: QPushButton
		"""

		if isinstance(data, str):
			data = {'text': data}
		elif isinstance(data, QIcon):
			data = {'icon': data}

		new_button = self.create_button(data)
		new_button.setProperty('combine', self._orientation)

		for property_name in ['text', 'icon', 'data', 'checked', 'shortcut', 'tooltip', 'checkable']:
			if data.get(property_name):
				new_button.setProperty(property_name, data[property_name])
		if data.get('clicked'):
			new_button.clicked.connect(data['clicked'])
		if data.get('toggled'):
			new_button.toggled.connect(data['toggled'])

		if index is None:
			self._button_group.addButton(new_button)
		else:
			self._button_group.addButton(new_button, index)

		self._main_layout.insertWidget(self._main_layout.count(), new_button)

		return new_button

	def set_buttons(self, buttons: List[Dict]):
		"""
		Clears already added buttons and add given ones into the group.

		:param List[Dict] buttons: list of dictioanries with the data of the buttons to add.
		"""

		for button in self._button_group.buttons():
			self._button_group.removeButton(button)
			self._main_layout.removeWidget(button)
			button.setVisible(False)
		for i, data in enumerate(buttons):
			new_button = self.add_button(data, i)
			if i == 0:
				new_button.setProperty('position', 'left')
			elif i == len(buttons) - 1:
				new_button.setProperty('position', 'right')
			else:
				new_button.setProperty('position', 'center')
