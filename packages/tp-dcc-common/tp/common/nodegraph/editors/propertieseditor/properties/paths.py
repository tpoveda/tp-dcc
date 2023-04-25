from Qt.QtCore import Qt
from Qt.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QStyle

from tp.common.nodegraph.widgets import dialogs
from tp.common.nodegraph.editors.propertieseditor.properties import base


class PropFilePath(base.BaseProperty):
	"""
	Displays a node property as a "QFileDialog" open widget in the properties editor.
	"""

	def __init__(self, parent=None):
		super(PropFilePath, self).__init__(parent)
		self._ledit = QLineEdit()
		self._ledit.setAlignment(Qt.AlignLeft)
		self._ledit.editingFinished.connect(self._on_value_change)
		self._ledit.clearFocus()

		icon = self.style().standardIcon(QStyle.StandardPixmap(21))
		_button = QPushButton()
		_button.setIcon(icon)
		_button.clicked.connect(self._on_select_file)

		hbox = QHBoxLayout(self)
		hbox.setContentsMargins(0, 0, 0, 0)
		hbox.addWidget(self._ledit)
		hbox.addWidget(_button)

		self._ext = '*'
		self._file_directory = None

	def _on_select_file(self):
		file_path = dialogs.get_open_filename(self, file_dir=self._file_directory, ext_filter=self._ext)
		file = file_path[0] or None
		if file:
			self.set_value(file)

	def _on_value_change(self, value=None):
		if value is None:
			value = self._ledit.text()
		self.valueChanged.emit(self.toolTip(), value)

	def set_file_ext(self, ext=None):
		self._ext = ext or '*'

	def set_file_directory(self, directory):
		self._file_directory = directory

	def value(self):
		return self._ledit.text()

	def set_value(self, value):
		_value = str(value)
		if _value != self.value():
			self._ledit.setText(_value)
			self._on_value_change(_value)


class PropFileSavePath(PropFilePath):
	"""
	Displays a node property as a "QFileDialog" save widget in the properties editor.
	"""

	def _on_select_file(self):
		file_path = dialogs.get_save_filename(self, file_dir=self._file_directory, ext_filter=self._ext)
		file = file_path[0] or None
		if file:
			self.set_value(file)
