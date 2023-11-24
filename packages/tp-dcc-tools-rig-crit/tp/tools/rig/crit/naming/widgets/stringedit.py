from __future__ import annotations

from overrides import override

from tp.common.qt import api as qt
from tp.common.qt.widgets import layouts, labels, lineedits


class StringEdit(qt.QWidget):
	"""
	Custom widget that creates a label, textbox (QLineEdit) and an optional button
	"""

	buttonClicked = qt.Signal()

	def __init__(
			self, label: str = '', edit_text: str = '', edit_placeholder: str = '', button_text: str | None = None,
			edit_width: int | None = None, label_ratio: int = 1, button_ratio: int = 1, edit_ratio: int = 5,
			tooltip: str = '', orientation: qt.Qt.Orientation = qt.Qt.Horizontal, enable_menu: bool = False,
			rounding: int = 3, parent: qt.QWidget | None = None):
		super().__init__(parent)

		self._label = label
		self._button_text = button_text
		self._enable_menu = enable_menu
		self._button = None								# type: QPushButton

		self._layout = (
			layouts.horizontal_layout if orientation == qt.Qt.Horizontal else layouts.vertical_layout)(parent=self)

		self._edit = self._setup_edit_line(
			edit_text=edit_text, placeholder=edit_placeholder, tooltip=tooltip, edit_width=edit_width,
			enable_menu=enable_menu)
		if label:
			self._label = labels.label(text=label, tooltip=tooltip, parent=self)
			self._layout.addWidget(self._label, label_ratio)
		self._layout.addWidget(self._edit, edit_ratio)

		if self._button_text:
			self._button = qt.QPushButton(button_text, parent)
			self._layout.addWidget(self._button, button_ratio)

		self._setup_signals()

	@property
	def label(self) -> labels.BaseLabel:
		return self._label

	@property
	def edit(self) -> lineedits.BaseLineEdit:
		return self._edit

	@property
	def editingFinished(self) -> qt.Signal:
		return self._edit.editingFinished

	@property
	def textChanged(self) -> qt.Signal:
		return self._edit.textChanged

	@property
	def returnPressed(self) -> qt.Signal:
		return self._edit.returnPressed

	def text(self) -> str:
		"""
		Returns text from line edit.

		:return: line edit text.
		:rtype: str
		"""

		return self._edit.text()

	def set_text(self, text: str):
		"""
		Sets line edit text.

		:param str text: new text.
		"""

		self._edit.setText(text)

	def select_all(self):
		"""
		Selects all text in the line edit.
		"""

		self._edit.selectAll()

	def set_placeholder_text(self, text: str):
		"""
		Sets line edit placeholder text.

		:param str text: placeholder text.
		"""

		self._edit.setPlaceholderText(text)

	def _setup_edit_line(
			self, edit_text: str, placeholder: str, tooltip: str, edit_width: int,
			enable_menu: bool) -> lineedits.BaseLineEdit:
		"""
		Internal function that creates the line edit widget instance to use within thsi widget.

		:param str edit_text:
		:param str palceholder:
		:param str tooltip:
		:param int edit_with:
		:param bool enable_menu:
		:return: line edit instance.
		:rtype: lineedits.BaseLineEdit.
		"""

		return lineedits.BaseLineEdit(
			text=edit_text, placeholder=placeholder, tooltip=tooltip, edit_width=edit_width,
			enable_menu=enable_menu, parent=self)

	def _setup_signals(self):
		"""
		Internal function that setup widget signals.
		"""

		if self._button:
			self._button.clicked.connect(self.buttonClicked.emit)


class CompleterStringEdit(StringEdit):
	def __init__(
			self, label: str = '', edit_text: str = '', edit_placeholder: str = '', button_text: str | None = None,
			edit_width: int | None = None, label_ratio: int = 1, button_ratio: int = 1, edit_ratio: int = 5,
			tooltip: str = '', orientation: qt.Qt.Orientation = qt.Qt.Horizontal, enable_menu: bool = False,
			rounding: int = 3, parent: qt.QWidget | None = None):
		super().__init__(
			label=label, edit_text=edit_text, edit_placeholder=edit_placeholder, button_text=button_text,
			edit_width=edit_width, label_ratio=label_ratio, button_ratio=button_ratio, edit_ratio=edit_ratio,
			tooltip=tooltip, orientation=orientation, enable_menu=enable_menu, rounding=rounding, parent=parent)

	@override(check_signature=False)
	def _setup_edit_line(
			self, edit_text: str, placeholder: str, tooltip: str, edit_width: int,
			enable_menu: bool) -> CompleterLineEdit:
		return CompleterLineEdit(text=edit_text, tooltip=tooltip, edit_width=edit_width, parent=self)


class CompleterLineEdit(qt.BaseLineEdit):
	pass
