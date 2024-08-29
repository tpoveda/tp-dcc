from __future__ import annotations

import os.path

from Qt.QtCore import Qt, QObject
from Qt.QtWidgets import QFileDialog, QMessageBox
from Qt.QtGui import QPixmap

_CURRENT_USER_DIRECTORY: str = os.path.expanduser("~")


def _set_directory(path: str):
    """
    Internal function that sets the current user directory.

    :param path: new path to set.
    """

    global _CURRENT_USER_DIRECTORY
    if os.path.isdir(path):
        _CURRENT_USER_DIRECTORY = path
    elif os.path.isfile(path):
        _CURRENT_USER_DIRECTORY = os.path.dirname(path)


def get_save_file_name(
    title: str = "Save File",
    start_directory: str | None = None,
    extension_filter: str = "*",
    parent: QObject | None = None,
) -> tuple[str, str]:
    """
    Prompts a file save dialog to get a file name.

    :param title: dialog title.
    :param start_directory: optional start directory.
    :param extension_filter: file extension filter.
    :param parent: optional dialog parent widget.
    :return: tuple containing the save file name file dialog and the selected filter.
    """

    start_directory = start_directory or os.path.expanduser("~")
    result = QFileDialog.getSaveFileName(
        parent, title, start_directory, extension_filter
    )
    file_path = result[0] or None
    if file_path:
        _set_directory(file_path)

    return result


def get_open_file_name(
    title: str = "Open File",
    start_directory: str | None = None,
    extension_filter: str = "*",
    parent: QObject | None = None,
) -> tuple[str, str]:
    """
    Prompts a file open dialog to get a file name.

    :param title: dialog title.
    :param start_directory: optional start directory.
    :param extension_filter: file extension filter.
    :param parent: optional dialog parent widget.
    :return: tuple containing the open file name file dialog and the selected filter.
    """

    start_directory = start_directory or os.path.expanduser("~")
    result = QFileDialog.getOpenFileName(
        parent, title, start_directory, extension_filter
    )
    file_path = result[0] or None
    if file_path:
        _set_directory(file_path)

    return result


def message_dialog(
    text: str = "",
    title: str = "Message",
    dialog_icon: str | None = None,
    custom_icon: str | None = None,
    parent: QObject | None = None,
):
    """
    Prompts a message dialog widget with "Ok" button.

    :param text: dialog text.
    :param title: dialog title.
    :param dialog_icon: optional display icon ("information", "warning", "critical").
    :param custom_icon: optional custom icon to display.
    :param parent: optional dialog parent widget.
    """

    dialog = QMessageBox(parent=parent)
    dialog.setWindowTitle(title)
    dialog.setInformativeText(text)
    dialog.setStandardButtons(QMessageBox.Ok)
    if custom_icon:
        pixmap = QPixmap(custom_icon).scaledToHeight(32, Qt.SmoothTransformation)
        dialog.setIconPixmap(pixmap)
    else:
        if dialog_icon == "information":
            dialog.setIcon(QMessageBox.Information)
        elif dialog_icon == "warning":
            dialog.setIcon(QMessageBox.Warning)
        elif dialog_icon == "critical":
            dialog.setIcon(QMessageBox.Critical)
    result = dialog.exec()


def question_dialog(
    text: str = "",
    title: str = "Are you sure?",
    dialog_icon: str | None = None,
    custom_icon: str | None = None,
    parent: QObject | None = None,
) -> bool:
    """
    Prompts a question dialog widget with "Yes" and "No" buttons.

    :param text: dialog text.
    :param title: dialog title.
    :param dialog_icon: optional display icon ("information", "warning", "critical").
    :param custom_icon: optional custom icon to display.
    :param parent: optional dialog parent widget.
    :return: True if "Yes" button is clicked, False otherwise.
    """

    dialog = QMessageBox(parent=parent)
    dialog.setWindowTitle(title)
    dialog.setInformativeText(text)
    dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
    if custom_icon:
        pixmap = QPixmap(custom_icon).scaledToHeight(32, Qt.SmoothTransformation)
        dialog.setIconPixmap(pixmap)
    else:
        if dialog_icon == "information":
            dialog.setIcon(QMessageBox.Information)
        elif dialog_icon == "warning":
            dialog.setIcon(QMessageBox.Warning)
        elif dialog_icon == "critical":
            dialog.setIcon(QMessageBox.Critical)
    result = dialog.exec()
    return bool(result == QMessageBox.Yes)
