from __future__ import annotations

import enum

from Qt.QtCore import Signal
from Qt.QtWidgets import QWidget
from Qt.QtGui import QColor, QIcon, QPalette

from tp.common.python import path
from tp.common.qt import qtutils, contexts as qt_contexts
from tp.common.qt.widgets import layouts, labels, lineedits, buttons
from tp.common.resources import api as resources


class DirectoryWidget(QWidget):
	"""
	Widget that contains variables to store current working directory.
	"""

	directoryChanged = Signal(str)

	def __init__(self, parent=None):

		self._directory = ''
		self._last_directory = ''

		super().__init__(parent=parent)

	@property
	def directory(self) -> str:
		return self._directory

	@directory.setter
	def directory(self, value: str):
		self._last_directory = self._directory
		self._directory = value
		self.directoryChanged.emit(self._directory)


class PathWidget(DirectoryWidget):
	"""
	Custom widget that is composed by:
		- Line Edit with drag & drop behaviour for files and directories.
		- Button that allow to open a file or folder selector dialog.
	"""

	class Mode(enum.IntEnum):
		EXISTING_DIR = 0
		EXISTING_FILE = 1
		SAVE_FILE = 2

	def __init__(
			self, mode: int = Mode.EXISTING_DIR, default_path: str = '', label_text: str = '', dialog_label: str = '',
			button_icon: QIcon | None = None, filters: str | None = None, start_directory: str = '', clear: bool = False,
			parent: QWidget | None = None):
		super().__init__(parent=parent)

		self._mode = int(mode)
		self._label_text = label_text
		self._dialog_label = dialog_label
		self._folder_icon = button_icon or resources.icon('open')
		self._filters = filters
		self._start_directory = start_directory
		self._clear = clear

		self._main_layout = layouts.vertical_layout(spacing=2, margins=(2, 2, 2, 2))
		self.setLayout(self._main_layout)
		path_layout = layouts.horizontal_layout(spacing=2, margins=(2, 2, 2, 2))
		self._path_widget = QWidget(parent=self)
		self._path_widget.setLayout(path_layout)
		self._path_label = labels.BaseLabel('' if not self._label_text else '{}'.format(self._label_text))
		self._path_label.setVisible(bool(self._label_text))
		self._path_line = lineedits.FolderLineEdit(parent=self)
		if path.exists(self._directory):
			self._path_line.setText(self._directory)
		self._path_button = buttons.BaseButton(parent=self)
		if self._folder_icon:
			self._path_button.set_icon(self._folder_icon)
		else:
			self._path_button.setText('Browse...')
		self._clear_button = buttons.BaseButton(parent=self)
		self._clear_button.set_icon(resources.icon('close'))
		self._clear_button.setVisible(self._clear)
		path_layout.addWidget(self._path_label)
		path_layout.addWidget(self._path_line)
		path_layout.addWidget(self._path_button)
		path_layout.addWidget(self._clear_button)
		self._main_layout.addWidget(self._path_widget)

		self.directory = default_path

		self._path_line.textChanged.connect(self._on_path_directory_text_changed)
		self._path_button.clicked.connect(self._on_path_button_clicked)
		self._clear_button.clicked.connect(self._on_clear_button_clicked)

	@property
	def line_edit(self) -> lineedits.FolderLineEdit:
		return self._path_line

	@property
	def folder_button(self) -> buttons.BaseButton:
		return self._path_button

	@property
	def start_directory(self) -> str:
		return self._start_directory

	@start_directory.setter
	def start_directory(self, value: str):
		self._start_directory = str(value)

	def add_widget(self, qwidget: QWidget):
		"""
		Adds a new widget to the path widget.

		:param QWidget qwidget: QWidget to add.
		"""

		self._main_layout.addWidget(qwidget)

	@DirectoryWidget.directory.setter
	def directory(self, value: str):
		DirectoryWidget.directory.fset(self, value)
		with qt_contexts.block_signals(self._path_line):
			self._path_line.setText(self._directory)
		self.directoryChanged.emit(self._directory)

	def set_placeholder_text(self, text: str):
		"""
		Sets line edit placeholder text.

		:param str text: placeholder text.
		"""

		self._path_line.setPlaceholderText(text)

	def _get_existing_directory(self) -> str | None:
		"""
		Internal function that opens a select folder dialog.

		:return: selected existing directory.
		:rtype: str or None
		"""

		selected_path = qtutils.get_folder(directory=self._directory or self._start_directory, parent=self)
		if not path.is_dir(selected_path):
			return None

		return selected_path

	def _get_existing_file(self) -> str | None:
		"""
		Internal function that opens a select folder dialog.

		:return: selected existing directory.
		:rtype: str or None
		"""

		selected_path = qtutils.get_open_filename(
			file_dir=self._directory or self._start_directory, ext_filter=self._filters, title=self._dialog_label,
			parent=self)
		selected_path = selected_path[0] if selected_path else None
		if not path.is_file(selected_path):
			return None

		return selected_path

	def _get_save_file(self) -> str | None:
		"""
		Internal function that opens a save file dialog.

		:return: selected save directory.
		:rtype: str or None
		"""

		selected_path = qtutils.get_save_filename(
			file_dir=self._directory or self._start_directory, ext_filter=self._filters, title=self._dialog_label,
			parent=self)
		selected_path = selected_path[0] if selected_path else None

		return selected_path

	def _set_error(self, flag: bool):
		"""
		Internal function that updates directory line color based on whether selected file/folder exists.

		:param bool flag: True when file/folder does not exist; False otherwise.
		"""

		yes_color = QColor(200, 255, 200, 100)
		no_color = QColor(25, 200, 200, 100)

		palette = QPalette()
		if flag:
			palette.setColor(QPalette().Base, no_color)
		else:
			palette.setColor(QPalette().Base, yes_color)

		self._path_line.setPalette(palette)

	def _on_path_directory_text_changed(self, text: str):
		"""
		Internal callback function that is called when directory value changes.

		:param str text: new directory.
		"""

		with qt_contexts.block_signals(self):
			self.directory = text

		self._set_error(not path.exists(text))
		if not text:
			self._path_line.setPalette(lineedits.BaseLineEdit().palette())

		self.directoryChanged.emit(text)

	def _on_path_button_clicked(self):
		"""
		Internal callback function that is called when folder browse button is clicked by the user.
		"""

		directory = None
		if self._mode == 0:
			directory = self._get_existing_directory()
		elif self._mode == 1:
			directory = self._get_existing_file()
		elif self._mode == 2:
			directory = self._get_save_file()
		if not directory:
			return None

		directory = path.clean_path(directory)
		self.directory = directory

		return directory

	def _on_clear_button_clicked(self):
		"""
		Internal callback function that is called when clear button is clicked by the user.
		"""

		self.directory = ''
