#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom widgets to handle file/folder browser related tasks
"""

import os
import sys
import subprocess

from Qt.QtCore import Signal, Property, QSize
from Qt.QtWidgets import QSizePolicy, QFileDialog

from tp.common.qt.widgets import buttons


def browse_file(self):
    filter_list = 'File({})'.format(' '.join(['*' + e for e in self.filters])) if self.filters else 'Any File(*)'
    if self.multiple:
        r_files, _ = QFileDialog.getOpenFileNames(self, 'Browse Files', self.path, filter_list)
        if r_files:
            self.filesChanged.emit(r_files)
            self.path = r_files[0]
    else:
        r_file, _ = QFileDialog.getOpenFileName(self, 'Browse File', self.path, filter_list)
        if r_file:
            self.fileChanged.emit(r_file)
            self.path = r_file


def browse_folder(self):
    r_folder = QFileDialog.getExistingDirectory(self, 'Browse Folder', self.path)
    if not r_folder:
        return

    if self.multiple:
        self.foldersChanged.emit([r_folder])
    else:
        self.folderChanged.emit(r_folder)
    self.path = r_folder


def save_file(self):
    filter_list = 'File({})'.format(' '.join(['*' + e for e in self.filters])) if self.filters else 'Any File(*)'
    r_file, _ = QFileDialog.getSaveFileName(self, 'Save File', self.path, filter_list)
    if not r_file:
        return

    self.fileChanged.emit(r_file)
    self.path = r_file


class ClickBrowserFileButton(buttons.BaseButton, object):
    fileChanged = Signal(str)
    filesChanged = Signal(list)

    _on_browse_file = browse_file

    def __init__(self, text='Browse', multiple=False, parent=None):
        super(ClickBrowserFileButton, self).__init__(text=text, parent=parent)

        self._path = None
        self._multiple = multiple
        self._filters = list()

        self.setToolTip('Click to browse file')
        self.clicked.connect(self._on_browse_file)

    def _get_filters(self):
        """
        Returns browse filters
        :return: list(str)
        """

        return self._filters

    def _set_filters(self, value):
        """
        Sets browse filters
        :param value: list(str)
        """

        self._filters = value

    def _get_path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    def _set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    def _get_multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    def _set_multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag

    filters = Property(list, _get_filters, _set_filters)
    path = Property(str, _get_path, _set_path)
    multiple = Property(bool, _get_multiple, _set_multiple)


class ClickBrowserFolderButton(buttons.BaseButton, object):
    folderChanged = Signal(str)
    foldersChanged = Signal(list)

    _on_browse_folder = browse_folder

    def __init__(self, text='', multiple=False, parent=None):
        super(ClickBrowserFolderButton, self).__init__(text=text, parent=parent)

        self._path = None
        self._multiple = multiple

        self.setToolTip('Click to browse folder')
        self.clicked.connect(self._on_browse_folder)

    def _get_path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    def _set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    def _get_multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    def _set_multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag

    path = Property(str, _get_path, _set_path)
    multiple = Property(bool, _get_multiple, _set_multiple)


class ClickBrowserFileToolButton(buttons.BaseToolButton, object):
    fileChanged = Signal(str)
    filesChanged = Signal(list)

    _on_browse_file = browse_file

    def __init__(self, multiple=False, parent=None):
        super(ClickBrowserFileToolButton, self).__init__(parent=parent)

        self._path = None
        self._multiple = multiple
        self._filters = list()

        self.image('folder')
        self.icon_only()
        self.setToolTip('Click to browse file')
        self.clicked.connect(self._on_browse_file)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_filters(self):
        """
        Returns browse filters
        :return: list(str)
        """

        return self._filters

    def _set_filters(self, value):
        """
        Sets browse filters
        :param value: list(str)
        """

        self._filters = value

    def _get_path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    def _set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    def _get_multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    def _set_multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag

    filters = Property(list, _get_filters, _set_filters)
    path = Property(str, _get_path, _set_path)
    multiple = Property(bool, _get_multiple, _set_multiple)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self.path = value


class ClickSaveFileToolButton(buttons.BaseToolButton, object):
    fileChanged = Signal(str)

    _on_browse_file = browse_file

    def __init__(self, multiple=False, parent=None):
        super(ClickSaveFileToolButton, self).__init__(parent=parent)

        self._path = None
        self._multiple = multiple
        self._filters = list()

        self.image('save')
        self.icon_only()
        self.setToolTip('Click to save file')
        self.clicked.connect(self._on_browse_file)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_filters(self):
        """
        Returns browse filters
        :return: list(str)
        """

        return self._filters

    def _set_filters(self, value):
        """
        Sets browse filters
        :param value: list(str)
        """

        self._filters = value

    def _get_path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    def _set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    filters = Property(list, _get_filters, _set_filters)
    path = Property(str, _get_path, _set_path)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self.path = value


# @mixin.property_mixin
class ClickBrowserFolderToolButton(buttons.BaseToolButton, object):
    folderChanged = Signal(str)
    foldersChanged = Signal(list)

    _on_browse_folder = browse_folder

    def __init__(self, multiple=False, parent=None):
        super(ClickBrowserFolderToolButton, self).__init__(parent=parent)

        self._path = None
        self._multiple = multiple

        self.image('folder')
        self.icon_only()
        self.setToolTip('Click to browse folder')
        self.clicked.connect(self._on_browse_folder)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    def _set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    def _get_multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    def _set_multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag

    path = Property(str, _get_path, _set_path)
    multiple = Property(bool, _get_multiple, _set_multiple)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self.path = value


class DragFileButton(buttons.BaseToolButton, object):
    fileChanged = Signal(str)
    filesChanged = Signal(list)
    _on_browse_file = browse_file

    def __init__(self, text='', multiple=False, parent=None):
        super(DragFileButton, self).__init__(parent=parent)

        self._path = None
        self._multiple = multiple
        self._filters = list()

        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.text_under_icon()
        self.setText(text)

        self.theme_size = 60
        self.image('attach')
        self.setIconSize(QSize(60, 60))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setToolTip('Click to browse file or drag file here')
        self.clicked.connect(self._on_browse_file)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_filters(self):
        """
        Returns browse filters
        :return: list(str)
        """

        return self._filters

    def _set_filters(self, value):
        """
        Sets browse filters
        :param value: list(str)
        """

        self._filters = value

    def _get_path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    def _set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    def _get_multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    def _set_multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag

    filters = Property(list, _get_filters, _set_filters)
    path = Property(str, _get_path, _set_path)
    multiple = Property(bool, _get_multiple, _set_multiple)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def dragEnterEvent(self, event):
        """
        Overrides base QToolButton dragEnterEvent to validate dragged files
        :param event: QDragEvent
        """

        if event.mimeData().hasFormat("text/uri-list"):
            file_list = self._get_valid_file_list(event.mimeData().urls())
            count = len(file_list)
            if count == 1 or (count > 1 and self._multiple):
                event.acceptProposedAction()
                return

    def dropEvent(self, event):
        """
        Overrides base QToolButton dropEvent Event to accept dropped files
        :param event: QDropEvent
        """

        file_list = self._get_valid_file_list(event.mimeData().urls())
        if self._multiple:
            self.filesChanged.emit(file_list)
            self.set_path(file_list)
        else:
            self.fileChanged.emit(file_list[0])
            self.set_path(file_list[0])

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def get_path(self):
        """
        Returns file path
        :return: str
        """

        return self._path

    def set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self.path = value

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _get_valid_file_list(self, url_list):
        """
        Returns lits of valid dropped files
        :param url_list:
        :return: list(str)
        """

        file_list = list()
        for url in url_list:
            file_name = url.toLocalFile()
            if sys.platform == 'darwin':
                sub_process = subprocess.Popen(
                    'osascript -e \'get posix path of posix file \"file://{}\" -- kthxbai\''.format(file_name),
                    stdout=subprocess.PIPE, shell=True)
                file_name = sub_process.communicate()[0].strip()
                sub_process.wait()
            if os.path.isfile(file_name):
                if self.property('format'):
                    if os.path.splitext(file_name)[-1] in self.property('format'):
                        file_list.append(file_name)
                else:
                    file_list.append(file_name)

        return file_list


# @mixin.cursor_mixin
# @mixin.property_mixin
class DragFolderButton(buttons.BaseToolButton, object):
    folderChanged = Signal(str)
    foldersChanged = Signal(list)
    _on_browse_folder = browse_folder

    def __init__(self, multiple=False, parent=None):
        super(DragFolderButton, self).__init__(parent=parent)

        self._path = None
        self._multiple = multiple

        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.text_under_icon()

        self.theme_size = 60
        self.image('folder')
        self.setText('Click or drag folder here')
        self.setIconSize(QSize(60, 60))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setToolTip('Click to browse folder or drag folder here')
        self.clicked.connect(self._on_browse_folder)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_path(self):
        """
        Returns last browse file path
        :return: str
        """

        return self._path

    def _set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self._path = value

    def _get_multiple(self):
        """
        Returns whether or not browse can select multiple files
        :return: bool
        """

        return self._multiple

    def _set_multiple(self, flag):
        """
        Sets whether or not browse can select multiple files
        :param flag: bool
        """

        self._multiple = flag

    path = Property(str, _get_path, _set_path)
    multiple = Property(bool, _get_multiple, _set_multiple)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def dragEnterEvent(self, event):
        """
        Overrides base QToolButton dragEnterEvent to validate dragged files
        :param event: QDragEvent
        """

        if event.mimeData().hasFormat("text/uri-list"):
            folder_list = [url.toLocalFile() for url in event.mimeData().urls() if os.path.isdir(url.toLocalFile())]
            count = len(folder_list)
            if count == 1 or (count > 1 and self._multiple):
                event.acceptProposedAction()
                return

    def dropEvent(self, event):
        """
        Overrides base QToolButton dropEvent Event to accept dropped files
        :param event: QDropEvent
        """

        folder_list = [url.toLocalFile() for url in event.mimeData().urls() if os.path.isdir(url.toLocalFile())]
        if self._multiple:
            self.foldersChanged.emit(folder_list)
            self.set_path(folder_list)
        else:
            self.folderChanged.emit(folder_list[0])
            self.set_path(folder_list[0])

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def get_path(self):
        """
        Returns file path
        :return: str
        """

        return self._path

    def set_path(self, value):
        """
        Sets browse start path
        :param value: str
        """

        self.path = value
