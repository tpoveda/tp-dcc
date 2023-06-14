from __future__ import annotations

import uuid
from typing import Tuple, List

from overrides import override
from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QWidget, QLabel, QToolButton, QSizePolicy
from Qt.QtGui import QKeyEvent

from tp.common.python import strings
from tp.common.resources import icon
from tp.common.resources import api as resources
from tp.common.qt import dpi, qtutils
from tp.common.qt.widgets import layouts, frameless, buttons


def show_warning(
		title: str = '', message: str = '', button_a: str | None = 'OK', button_b: str | None = 'Cancel',
		button_c: str | None = None, button_icon_a: str | None = None, button_icon_b: str | None = None,
		button_icon_c: str | None = None, icon: str | None = None, default: int = 0,
		parent: QWidget | None = None) -> str:
	"""
	Shows a warning popup message box.

	:param str title: message box title.
	:param str message: message box message.
	:param str or None button_a: optional first button text.
	:param str or None button_b: optional second button text.
	:param str or None button_c: optional third button text.
	:param str or None button_icon_a: optional first button icon.
	:param str or None button_icon_b: optional second button icon.
	:param str or None button_icon_c: optional third button icon.
	:param str or None icon: optional message box icon.
	:param int or None default: default button index.
	:param parent: optional message box parent widget.
	:return: message box selected button ('A', 'B' or 'C').
	:rtype: str
	"""

	new_message = MessageBoxBase(
		title=title, message=message, button_a=button_a, button_b=button_b, button_c=button_c,
		button_icon_a=button_icon_a or MessageBoxBase.OK_ICON, button_icon_b=button_icon_b or MessageBoxBase.CANCEL_ICON,
		button_icon_c=button_icon_c, icon=icon or MessageBoxBase.WARNING, default=default, parent=parent)
	new_message.show()
	while new_message.msg_closed is False:
		qtutils.process_ui_events()

	return new_message.result


class MessageBoxBase(frameless.FramelessWindowThin):

	INFO = 'Info'
	QUESTION = 'Question'
	WARNING = 'Warning'
	CRITICAL = 'Critical'

	INFO_ICON = 'information'
	QUESTION_ICON = 'help'
	WARNING_ICON = 'warning'
	CRITICAL_ICON = 'x_circle_mark2'
	OK_ICON = 'checkmark'
	CANCEL_ICON = 'multiply'

	def __init__(
			self, parent: QWidget, title: str = '', message: str = '', icon: str = QUESTION,
			button_a: str | None = 'OK', button_b: str | None = None, button_c: str | None = None,
			button_icon_a: str | None = OK_ICON, button_icon_b: str | None = CANCEL_ICON,
			button_icon_c: str | None = None, default: int = 0, on_top: bool = True,
			key_presses: Tuple[Qt.Key, ...] = (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Space)):

		self._args = locals()
		parent = parent.window() if parent else None
		name = self._generate_name(icon) if icon else self._generate_name('MessageBox')

		super().__init__(
			parent=parent, title=title, name=name, resizable=False, width=100, height=100, modal=False,
			minimize_enabled=False, on_top=on_top)

		self._default = default
		self._msg_closed = False
		self._result = None						# type: str | None
		self._buttons = []						# type: List[buttons.BaseButton]

		self._init()

	@property
	def msg_closed(self) -> bool:
		return self._msg_closed

	@property
	def result(self) -> str:
		return self._result

	@override
	def keyPressEvent(self, event: QKeyEvent) -> None:
		if self._default > 0:
			keys = self._args['key_presses']
			if any(map(lambda y: event.key() == y, keys)):
				self._buttons[self._default].leftClicked.emit()

	@override(check_signature=False)
	def close(self, result: str | None = None):
		self._msg_closed = True
		self._result = result
		super().close()

	def _generate_name(self, name: str):
		"""
		Internal function used to generate a unique name.

		:param str  name: original name.
		:return: unique name.
		:rtype: str
		"""

		return f'{name}_{str(uuid.uuid4())[:4]}'

	def _calculate_label_height(self, text: str, label: QLabel):
		"""
		Internal function that returns the height of a label based on its text.

		:param str text: label text.
		:param QLabel label: label instance.
		:return: label height.
		:rtype: int
		"""

		font_metrics = label.fontMetrics()
		width = label.size().width()
		height = font_metrics.height()
		lines = 1
		total_width = 0

		for char in text:
			char_width = font_metrics.horizontalAdvance(char)
			total_width += char_width + 1.1
			if total_width > width:
				total_width = width
				lines =+ 1

		new_lines = strings.new_lines(text)
		lines += new_lines

		return height * lines

	def _init(self):
		"""
		Internal function that intializes message box contents.
		"""

		self.set_maximize_button_visible(False)
		self.set_minimize_button_visible(False)
		self.title_bar.set_title_align(Qt.AlignCenter)

		icon_size = 32

		image = QToolButton(parent=self)
		button_icon = self._args['icon'] or None
		if button_icon == self.WARNING:
			button_icon = icon.colorize_icon(resources.icon(self.WARNING_ICON), size=icon_size, color=(220, 210, 0))
		elif button_icon == self.QUESTION:
			button_icon = icon.colorize_icon(resources.icon(self.QUESTION_ICON), size=icon_size, color=(0, 192, 32))
		elif button_icon == self.INFO:
			button_icon = icon.colorize_icon(resources.icon(self.INFO_ICON), size=icon_size, color=(220, 220, 220))
		elif button_icon == self.CRITICAL:
			button_icon = icon.colorize_icon(resources.icon(self.CRITICAL_ICON), size=icon_size, color=(220, 90, 90))
		if button_icon:
			image.setIcon(button_icon)
		else:
			image.hide()
		if button_icon:
			image.setIconSize(dpi.size_by_dpi(QSize(icon_size, icon_size)))
			image.setFixedSize(dpi.size_by_dpi(QSize(icon_size, icon_size)))

		self._label = QLabel(self._args['message'])
		self._label.setFixedWidth(min(self._label.fontMetrics().boundingRect(self._label.text()).width() + 20, 400))
		self._label.setFixedHeight(min(self._calculate_label_height(self._label.text(), self._label), 800))
		self._label.setAlignment(Qt.AlignTop)
		self._image_layout = layouts.horizontal_layout(spacing=15, margins=(15, 15, 15, 15))
		self._message_layout = layouts.vertical_layout()
		self._image_layout.addWidget(image)
		self._image_layout.addLayout(self._message_layout)
		self._message_layout.addWidget(self._label)
		self._buttons_layout = layouts.horizontal_layout(margins=(10, 0, 10, 10))
		self._buttons_layout.addStretch(1)

		msg_buttons = [self._args['button_a'], self._args['button_b'], self._args['button_c']]
		button_icons = [self._args['button_icon_a'], self._args['button_icon_b'], self._args['button_icon_c']]
		res = ['A', 'B', 'C']
		for i, msg_button in enumerate(msg_buttons):
			button = buttons.styled_button(text=f' {msg_button}', icon=button_icons[i], parent=self.parentWidget())
			button.setMinimumWidth(80)
			button.setMinimumHeight(24)
			qtutils.set_horizontal_size_policy(button, QSizePolicy.MinimumExpanding)
			self._buttons_layout.addWidget(button)
			button.leftClicked.connect(lambda x=res[i]: self.close(x))
			self._buttons.append(button)
		self._buttons_layout.addStretch(1)

		self.main_layout().addLayout(self._image_layout)
		self.main_layout().addLayout(self._buttons_layout)
