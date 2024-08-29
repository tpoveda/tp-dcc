from __future__ import annotations

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QLineEdit, QPushButton, QStyle

from .abstract import AbstractPropertyWidget
from .. import dialogs


class FilePathPropertyWidget(AbstractPropertyWidget):
    """
    Property widget that represents a file path.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._extension: str = "*"
        self._file_directory: str | None = None

        self._line_edit = QLineEdit(parent=self)
        self._line_edit.setAlignment(Qt.AlignLeft)
        self._line_edit.clearFocus()
        self._button = QPushButton(parent=self)
        self._button.setIcon(self.style().standardIcon(QStyle.StandardPixmap(21)))

        self._line_edit.editingFinished.connect(self._on_value_changed)
        self._button.clicked.connect(self._on_button_clicked)

    def get_value(self) -> str:
        """
        Returns the value of the property widget.

        :return: value of the property widget.
        """

        return self._line_edit.text()

    def set_value(self, value: str):
        """
        Sets the value of the property widget.

        :param value: value to set.
        """

        value = str(value)
        if value == self.get_value():
            return

        self._line_edit.setText(value)
        self._on_value_changed(value)

    def set_file_extension(self, extension: str | None = None):
        """
        Sets the file extension of the property widget.

        :param extension: file extension to set.
        """

        self._extension = extension or "*"

    def set_file_directory(self, directory: str):
        """
        Sets the file directory of the property widget.

        :param directory: file directory to set.
        """

        self._file_directory = directory

    def _on_value_changed(self, value: str | None = None):
        """
        Internal callback function that is called when the value of the line edit is changed.

        :param value: value to set.
        """

        value = self._line_edit.text() if value is None else value
        self.set_file_directory(value)
        self.valueChanged.emit(self.name, value)

    def _on_button_clicked(self):
        """
        Internal callback function that is called when the button is clicked.
        """

        file_path = dialogs.get_open_file_name(
            start_directory=self._file_directory,
            extension_filter=self._extension,
            parent=self,
        )
        selected_file = file_path[0] or None
        if selected_file:
            self.set_value(selected_file)


class FileSavePathPropertyWidget(FilePathPropertyWidget):
    """
    Property widget that represents a file save path.
    """

    def _on_button_clicked(self):
        """
        Internal callback function that is called when the button is clicked.
        """

        file_path = dialogs.get_save_file_name(
            start_directory=self._file_directory,
            extension_filter=self._extension,
            parent=self,
        )
        selected_file = file_path[0] or None
        if selected_file:
            self.set_value(selected_file)
