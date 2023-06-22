from __future__ import annotations

from overrides import override
from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QLineEdit, QTextBrowser
from Qt.QtGui import QFocusEvent, QMouseEvent

from tp.common.qt import validators


def line_edit(text='', read_only=False, placeholder_text='', parent=None):
	"""
	Creates a basic line edit widget.

	:param str text: default line edit text.
	:param bool read_only: whether line edit is read only.
	:param str placeholder_text: line edit placeholder text.
	:param QWidget parent: parent widget.
	:return: newly created combo box.
	:rtype: BaseLineEdit
	"""

	new_line_edit = BaseLineEdit(text=text, parent=parent)
	new_line_edit.setReadOnly(read_only)
	new_line_edit.setPlaceholderText(str(placeholder_text))

	return new_line_edit


def text_browser(parent=None):
	"""
	Creates a text browser widget.

	:param QWidget parent: parent widget.
	:return: newly created text browser.
	:rtype: QTextBrowser
	"""

	new_text_browser = QTextBrowser(parent=parent)

	return new_text_browser


class BaseLineEdit(QLineEdit):
	def __init__(
			self, text: str = '', enable_menu: bool = False, placeholder: str = '', tooltip: str = '',
			edit_width: int | None = None, fixed_width: int | None = None, menu_vertical_offset: int = 20,
			parent: QWidget | None = None):
		super().__init__(parent)



class EditableLineEditOnClick(QLineEdit):
	"""
	Custom QLineEdit that becomes editable on click or double click.
	"""

	def __init__(
			self, text: str, single: bool = False, double: bool = True, pass_through_clicks: bool = True,
			upper: bool = False, parent: QWidget | None = None):
		super().__init__(text, parent=parent)

		self._upper = upper
		self._validator = validators.UpperCaseValidator()

		if upper:
			self.setValidator(self._validator)
			self.setText(text)

		self.setReadOnly(True)
		self._editing_style = self.styleSheet()
		self._default_style = 'QLineEdit {border: 0;}'
		self.setStyleSheet(self._default_style)
		self.setContextMenuPolicy(Qt.NoContextMenu)
		self.setProperty('clearFocus', True)

		if single:
			self.mousePressEveNT = self._edit_event
		else:
			if pass_through_clicks:
				self.mousePressEvent = self.mouse_click_pass_through
		if double:
			self.mouseDoubleClickEvent = self._edit_event
		else:
			if pass_through_clicks:
				self.mouseDoubleClickEvent = self.mouse_click_pass_through

		self.editingFinished.connect(self._on_editing_finished)

	@override
	def setText(self, arg__1: str) -> None:
		if self._upper:
			arg__1 = arg__1.upper()

		super().setText(arg__1)

	@override
	def focusOutEvent(self, arg__1: QFocusEvent) -> None:
		super().focusOutEvent(arg__1)
		self._edit_finished()

	@override
	def mousePressEvent(self, arg__1: QMouseEvent) -> None:
		arg__1.ignore()

	def mouseReleaseEvent(self, arg__1: QMouseEvent) -> None:
		arg__1.ignore()

	def _edit_event(self, event: QMouseEvent):
		"""
		Internal function that overrides mouse press/release event behaviour.

		:param QMouseEvent event: Qt mouse event.
		"""

		self.setStyleSheet(self._editing_style)
		self.selectAll()
		self.setReadOnly(False)
		self.setFocus()
		event.accept()

	def mouse_click_pass_through(self, event: QMouseEvent):
		"""
		Internal function that overrides mouse press/release event behaviour to pass through the click.

		:param QMouseEvent event: Qt mouse event.
		"""

		event.ignore()

	def _edit_finished(self):
		"""
		Internal function that exits from the edit mode.
		"""

		self.setReadOnly(True)
		self.setStyleSheet(self._default_style)
		self.deselect()

	def _on_editing_finished(self):
		"""
		Internal callback function that is called when line edit text is changed.
		"""

		self._edit_finished()
