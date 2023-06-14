from __future__ import annotations

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QLineEdit, QTextBrowser


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
