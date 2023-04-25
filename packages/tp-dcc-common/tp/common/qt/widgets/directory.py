#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets related with directories and files
"""

import os
import enum

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QSizePolicy, QWidget, QListWidget, QAbstractItemView
from Qt.QtGui import QColor, QPalette

from tp.core import log, dcc
from tp.core.managers import resources
from tp.common.python import path
from tp.common.qt import base, qtutils, contexts as qt_contexts
from tp.common.qt.widgets import layouts, buttons, lineedits, labels

logger = log.tpLogger


def open_folder_widget(default_path='', label_text='', dialog_label='', start_directory='', clear=False, parent=None):
    """
    Creates a widget that allows user to open a folder.

    :param str default_path: default directory path.
    :param str label_text: label text.
    :param str dialog_label: open folder dialog label.
    :param str start_directory: default start directory path when browser is opened.
    :param bool clear: whether a clear button should appear.
    :param QWidget parent: optional parent widget.
    :return: select folder widget instance.
    :rtype: PathWidget
    """

    new_open_folder_widget = PathWidget(
        mode=PathWidget.Mode.EXISTING_DIR, default_path=default_path, label_text=label_text,
        dialog_label=dialog_label, start_directory=start_directory, clear=clear, parent=parent)

    return new_open_folder_widget


def open_file_widget(
        default_path='', label_text='', dialog_label='', filters=None, start_directory='', clear=False, parent=None):
    """
    Creates a widget that allows user to open a file.

    :param str default_path: default file path.
    :param str label_text: label text.
    :param str dialog_label: open folder dialog label.
    :param str filters: file filters.
    :param str start_directory: default start directory path when browser is opened.
    :param bool clear: whether a clear button should appear.
    :param QWidget parent: optional parent widget.
    :return: select folder widget instance.
    :rtype: PathWidget
    """

    new_open_file_widget = PathWidget(
        mode=PathWidget.Mode.EXISTING_FILE, default_path=default_path, label_text=label_text,
        dialog_label=dialog_label, filters=filters, start_directory=start_directory, clear=clear, parent=parent)

    return new_open_file_widget


def save_file_widget(
        default_path='', label_text='', dialog_label='', filters=None, start_directory='', clear=False, parent=None):
    """
    Creates a widget that allows user to select a file to save.

    :param str default_path: default file path.
    :param str label_text: label text.
    :param str dialog_label: open folder dialog label.
    :param str filters: file filters.
    :param str start_directory: default start directory path when browser is opened.
    :param bool clear: whether a clear button should appear.
    :param QWidget parent: optional parent widget.
    :return: select folder widget instance.
    :rtype: PathWidget
    """

    new_open_file_widget = PathWidget(
        mode=PathWidget.Mode.SAVE_FILE, default_path=default_path, label_text=label_text,
        dialog_label=dialog_label, filters=filters, start_directory=start_directory, clear=clear, parent=parent)

    return new_open_file_widget


class FileListWidget(QListWidget, object):
    """
    Widgets that shows files and directories such Windows Explorer
    """

    directory_activated = Signal(str)
    file_activated = Signal(str)
    file_selected = Signal(str)
    folder_selected = Signal(str)
    directory_selected = Signal(str)
    files_selected = Signal(list)
    up_requested = Signal()
    update_requested = Signal()

    def __init__(self, parent):
        self.parent = parent
        super(FileListWidget, self).__init__(parent)

        self.itemSelectionChanged.connect(self.selectItem)
        self.itemDoubleClicked.connect(self.activateItem)

    def resizeEvent(self, event):
        """
        Overrides QWidget resizeEvent so when the widget is resize a update request signal is emitted
        :param event: QResizeEvent
        """

        self.update_requested.emit()
        super(FileListWidget, self).resizeEvent(event)

    def wheelEvent(self, event):
        """
        Overrides QWidget wheelEvent to smooth scroll bar movement
        :param event: QWheelEvent
        """

        sb = self.horizontalScrollBar()
        minValue = sb.minimum()
        maxValue = sb.maximum()
        if sb.isVisible() and maxValue > minValue:
            sb.setValue(sb.value() + (-1 if event.delta() > 0 else 1))
        super(FileListWidget, self).wheelEvent(event)

    def keyPressEvent(self, event):
        """
        Overrides QWidget keyPressEvent with some shortcuts when using the widget
        :param event:
        :return:
        """
        modifiers = event.modifiers()
        if event.key() == int(Qt.Key_Return) and modifiers == Qt.NoModifier:
            if len(self.selectedItems()) > 0:
                item = self.selectedItems()[0]
                if item.type() == 0:  # directory
                    self.directory_activated.emit(item.text())
                else:  # file
                    self.file_activated.emit(item.text())
        elif event.key() == int(Qt.Key_Backspace) and modifiers == Qt.NoModifier:
            self.up_requested.emit()
        elif event.key() == int(Qt.Key_F5) and modifiers == Qt.NoModifier:
            self.update_requested.emit()
        else:
            super(FileListWidget, self).keyPressEvent(event)

    def selectItem(self):
        if len(self.selectedItems()) > 0:
            item = self.selectedItems()[0]
            if item.type() == 0:    # directory
                self.folder_selected.emit(item.text())
            if item.type() == 1:  # file
                self.file_selected.emit(item.text())

    def activateItem(self):
        if len(self.selectedItems()) > 0:
            item = self.selectedItems()[0]
            if item.type() == 0:  # directory
                self.directory_activated.emit(item.text())
            else:  # file
                self.file_activated.emit(item.text())

    def setExtendedSelection(self):
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.itemSelectionChanged.disconnect(self.selectItem)
        self.itemSelectionChanged.connect(self.processSelectionChanged)

    def processSelectionChanged(self):
        """
        Gets all selected items and emits a proper signal with the proper selected item names
        """

        items = filter(lambda x: x.type() != 0, self.selectedItems())
        names = map(lambda x: x.text(), items)
        self.files_selected.emit(names)


class FolderEditLine(lineedits.BaseLineEdit, object):
    """
    Custom QLineEdit with drag and drop behaviour for files and folders
    """

    def __init__(self, parent=None):
        super(FolderEditLine, self).__init__(parent)

        self.setDragEnabled(True)
        self.setReadOnly(True)

    def dragEnterEvent(self, event):
        """
        Overrides QWidget dragEnterEvent to enable drop behaviour with file
        :param event: QDragEnterEvent
        :return:
        """
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            event.acceptProposedAction()

    def dropEvent(self, event):
        data = event.mimeData()
        urls = data.urls()
        if (urls and urls[0].scheme() == 'file'):
            self.setText(urls[0].toLocalFile())


class SelectFolderButton(QWidget, object):
    """
    Button widget that allows to select folder paths
    """

    beforeNewDirectory = Signal()
    directoryChanged = Signal(object)   # Signal that is called when a new folder is selected

    def __init__(self, text='Browse', directory='', use_app_browser=False, parent=None):
        super(SelectFolderButton, self).__init__(parent)

        self._use_app_browser = use_app_browser
        self._directory = directory
        self.settings = None

        main_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
        self.setLayout(main_layout)

        folder_icon = resources.icon('folder')
        self._folder_btn = buttons.BaseButton(text, parent=self)
        self._folder_btn.setIcon(folder_icon)
        main_layout.addWidget(self._folder_btn)

        self._folder_btn.clicked.connect(self._open_folder_browser_dialog)

    @property
    def folder_btn(self):
        return self._folder_btn

    def get_init_directory(self):
        return self._directory

    def set_init_directory(self, directory):
        self._directory = directory

    init_directory = property(get_init_directory, set_init_directory)

    def set_settings(self, settings):
        self.settings = settings

    def _open_folder_browser_dialog(self):
        """
        Opens a set folder browser and returns the selected path
        :return: str, Path of the selected folder
        """

        self.beforeNewDirectory.emit()

        result = dcc.select_folder_dialog('Select Folder', start_directory=self.init_directory) or ''

        self.directoryChanged.emit(result)
        # if not result or not os.path.isdir(result[0]):
        if not result or not os.path.isdir(result):
            return
        return path.clean_path(result[0])


class SelectFolder(QWidget, object):
    """
    Widget with button and line edit that opens a folder dialog to select folder paths
    """

    directoryChanged = Signal(object)  # Signal that is called when a new folder is selected

    def __init__(self, label_text='Select Folder', directory='', use_app_browser=False, use_icon=True, parent=None):
        super(SelectFolder, self).__init__(parent)

        self._use_app_browser = use_app_browser
        self._use_icon = use_icon
        self.settings = None
        self.directory = None
        self._label_text = label_text
        self._directory = directory

        main_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
        self.setLayout(main_layout)

        self._folder_label = labels.BaseLabel(
            '{0}'.format(self._label_text)) if self._label_text == '' else labels.BaseLabel(
            '{0}:'.format(self._label_text))
        if not self._label_text:
            self._folder_label.setVisible(False)
        self._folder_line = FolderEditLine()
        self._folder_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if os.path.exists(self._directory):
            self._folder_line.setText(self._directory)

        self._folder_btn = buttons.BaseButton(parent=self)
        if self._use_icon:
            folder_icon = resources.icon('folder')
            self._folder_btn.setIcon(folder_icon)
        else:
            self._folder_btn.setText('Browse ...')

        for widget in [self._folder_label, self._folder_line, self._folder_btn]:
            main_layout.addWidget(widget)

        self._folder_btn.clicked.connect(self._open_folder_browser_dialog)

    @property
    def folder_label(self):
        return self._folder_label

    @property
    def folder_line(self):
        return self._folder_line

    @property
    def folder_btn(self):
        return self._folder_btn

    def set_directory_text(self, new_text):
        """
        Sets the text of the directory line
        :param new_text: str
        """

        self._folder_line.setText(new_text)

    def get_directory(self):
        """
        Returns directory set on the directory line
        :return: str
        """

        return str(self._folder_line.text())

    def set_directory(self, directory):
        """
        Sets the directory of the directory line
        """

        if not directory:
            return

        self.directory = directory

        self.set_directory_text(directory)

    def _open_folder_browser_dialog(self):
        """
        Opens a set folder browser and returns the selected path
        :return: str, Path of the selected folder
        """

        result = dcc.select_folder_dialog('Select Folder', start_directory=self.folder_line.text()) or ''
        if not result or not os.path.isdir(result):
            return
        else:
            filename = path.clean_path(result)
            self.set_directory(filename)
            self._text_changed()

        return filename

    def _text_changed(self):
        """
        This function is called each time the user manually changes the line text
        Emits the signal to notify that the directory has changed
        :param directory: str, new edit line text after user edit
        """

        directory = self.get_directory()
        if path.is_dir(directory):
            self.directoryChanged.emit(directory)

    def _send_directories(self, directory):
        """
        Emit the directory changed signal with the given directory
        :param directory: str
        :return: str
        """

        self.directoryChanged.emit(directory)


class PathWidget(base.DirectoryWidget):

    class Mode(enum.IntEnum):
        EXISTING_DIR = 0
        EXISTING_FILE = 1
        SAVE_FILE = 2

    def __init__(self, mode=Mode.EXISTING_DIR, default_path='', label_text='', dialog_label='', button_icon=None,
                 filters=None, start_directory='', clear=False, parent=None):

        self._mode = int(mode)
        self._label_text = label_text
        self._dialog_label = dialog_label
        self._folder_icon = button_icon or resources.icon('open')
        self._filters = filters
        self._start_directory = start_directory
        self._clear = clear

        super(PathWidget, self).__init__(parent=parent)

        with qt_contexts.block_signals(self):
            self.directory = default_path

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def line_edit(self):
        return self._path_line

    @property
    def folder_button(self):
        return self._path_button

    @property
    def start_directory(self):
        return self._start_directory

    @start_directory.setter
    def start_directory(self, value):
        self._start_directory = str(value)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def add_widget(self, qwidget):
        """
        Adds a new widget to the path widget.

        :param QWidget qwidget: QWidget to add
        """

        self.main_layout.addWidget(qwidget)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    @base.DirectoryWidget.directory.setter
    def directory(self, value):
        base.DirectoryWidget.directory.fset(self, value)
        with qt_contexts.block_signals(self._path_line):
            self._path_line.setText(self._directory)
        self.directoryChanged.emit(self._directory)

    def get_main_layout(self):
        return layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))

    def ui(self):
        super(PathWidget, self).ui()

        self._path_widget = base.BaseWidget(
            layout=layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2)), parent=self)
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
        self._clear_button.setIcon(resources.icon('close'))
        self._clear_button.setVisible(self._clear)
        self._path_widget.main_layout.addWidget(self._path_label)
        self._path_widget.main_layout.addWidget(self._path_line)
        self._path_widget.main_layout.addWidget(self._path_button)
        self._path_widget.main_layout.addWidget(self._clear_button)

        self.main_layout.addWidget(self._path_widget)

    def setup_signals(self):
        super(PathWidget, self).setup_signals()

        self._path_line.textChanged.connect(self._on_path_directory_text_changed)
        self._path_button.clicked.connect(self._on_path_button_clicked)
        self._clear_button.clicked.connect(self._on_clear_button_clicked)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_placeholder_text(self, text):
        """
        Sets line edit placeholder text.

        :param str text: placeholder text.
        """

        self._path_line.setPlaceholderText(text)

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _get_existing_directory(self):
        """
        Internal function that opens a select folder dialog.

        :return: selected existing directory.
        :rtype: str or None
        """

        selected_path = qtutils.get_folder(directory=self._directory or self._start_directory, parent=self)
        if not path.is_dir(selected_path):
            return None

        return selected_path

    def _get_existing_file(self):
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
            return

        return selected_path

    def _get_save_file(self):
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

    def _set_error(self, flag):
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

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_path_directory_text_changed(self, text):
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


class SelectFile(base.DirectoryWidget, object):
    """
    Widget with button and line edit that opens a file dialog to select file paths
    """

    directoryChanged = Signal(object)  # Signal that is called when a new folder is selected

    def __init__(self, label_text='Select File', directory='', use_app_browser=False,
                 filters=None, use_icon=True, parent=None):

        self._use_app_browser = use_app_browser
        self.settings = None
        self._use_icon = use_icon
        self._directory = directory
        self._label_text = label_text
        self._filters = filters

        super(SelectFile, self).__init__(parent)

    @property
    def file_label(self):
        return self._file_label

    @property
    def file_line(self):
        return self._file_line

    @property
    def file_btn(self):
        return self._folder_btn

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
        return main_layout

    def ui(self):
        super(SelectFile, self).ui()

        self._file_label = labels.BaseLabel(
            '{0}'.format(self._label_text)) if self._label_text == '' else labels.BaseLabel(
            '{0}:'.format(self._label_text), parent=self)
        if not self._label_text:
            self._file_label.setVisible(False)
        self._file_line = FolderEditLine()
        self._file_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if self._directory and os.path.exists(self._directory):
            self._file_line.setText(self._directory)

        self._file_btn = buttons.BaseButton(parent=self)
        self._clear_btn = buttons.BaseButton(parent=self)
        if self._use_icon:
            self._file_btn.setIcon(resources.icon('folder'))
            self._clear_btn.setIcon(resources.icon('delete'))
        else:
            self._file_btn.setText('Browse ...')
            self._clear_btn.setText('Clear')

        for widget in [self._file_label, self._file_line, self._file_btn, self._clear_btn]:
            self.main_layout.addWidget(widget)

    def setup_signals(self):
        self._file_btn.clicked.connect(self._open_file_browser_dialog)
        self._clear_btn.clicked.connect(self._on_reset_path)
        self._file_line.textChanged.connect(self._text_changed)

    def set_settings(self, settings):
        """
        Set new settings. Override in new classes to add custom behaviour
        :param settings:
        :return:
        """
        self.settings = settings

    def update_settings(self, filename):
        """
        Updates current settings. Override in new classes to add custom behaviour
        :param settings: new selected path for the user
        """

        pass

    def set_label(self, text):
        """
        Sets the directory label text
        :param text: str, new directory label text
        :return:
        """

        self._file_label.setText(text)
        self._file_label.setVisible(bool(text))

    def set_directory(self, directory):
        """
        Sets the text of the directory line
        :param directory: str
        """

        super(SelectFile, self).set_directory(directory=directory)

        self._file_line.setText(directory)

    def get_directory(self):
        """
        Returns directory setted on the directory line
        :return: str
        """

        return self._file_line.text()

    def _open_file_browser_dialog(self):
        """
        Opens a set folder browser and returns the selected path
        :return: str, Path of the selected folder
        """

        file_line = self._file_line.text()
        if os.path.isfile(file_line):
            file_line = os.path.dirname(file_line)
        result = dcc.select_file_dialog('Select File', start_directory=file_line, pattern=self._filters or '') or ''
        if not result or not os.path.isfile(result):
            logger.warning('Selected file "{}" is not a valid file!'.format(result))
            return
        else:
            filename = path.clean_path(result)
            self.set_directory(filename)
            self.directoryChanged.emit(filename)
            self.update_settings(filename=filename)

        return filename

    def _on_reset_path(self):
        self.set_directory('')
        self.directoryChanged.emit('')
        self.update_settings(filename='')

    def _text_changed(self):
        """
        This function is called each time the user manually changes the line text
        :param directory: str, new edit line text after user edit
        """

        f = self.get_directory()
        if path.is_file(f):
            self.directoryChanged.emit(f)


class GetDirectoryWidget(base.DirectoryWidget, object):
    directoryChanged = Signal(object)
    textChanged = Signal(object)

    def __init__(self, parent=None):

        self._label = 'directory'
        self._show_files = False

        super(GetDirectoryWidget, self).__init__(parent=parent)

    @property
    def show_files(self):
        return self._show_files

    def ui(self):
        super(GetDirectoryWidget, self).ui()

        self._directory_widget = QWidget()
        directory_layout = layouts.HorizontalLayout()
        self._directory_widget.setLayout(directory_layout)
        self.main_layout.addWidget(self._directory_widget)

        self._directory_lbl = labels.BaseLabel('directory', parent=self)
        self._directory_lbl.setMinimumWidth(60)
        self._directory_lbl.setMaximumWidth(100)
        self._directory_edit = lineedits.BaseLineEdit(parent=self)
        self._directory_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._directory_browse_btn = buttons.BaseButton('browse', parent=self)

        directory_layout.addWidget(self._directory_lbl)
        directory_layout.addWidget(self._directory_edit)
        directory_layout.addWidget(self._directory_browse_btn)

    def setup_signals(self):
        self._directory_edit.textChanged.connect(self._on_text_changed)
        self._directory_browse_btn.clicked.connect(self._on_browse)

    def set_directory(self, directory):
        super(GetDirectoryWidget, self).set_directory(directory)
        self.set_directory_text(directory)

    def get_directory(self):
        return self._directory_edit.text()

    def set_label(self, label):
        length = len(label) * 8
        self._directory_lbl.setMinimumWidth(length)
        self._directory_lbl.setText(label)

    def set_directory_text(self, text):
        self._directory_edit.setText(text)

    def set_placeholder_text(self, text):
        self._directory_edit.setPlaceholderText(text)

    def set_example(self, text):
        self.set_placeholder_text('example: {}'.format(text))

    def set_error(self, flag):

        if dcc.is_maya():
            yes_color = QColor(0, 255, 0, 50)
            no_color = QColor(255, 0, 0, 50)
        else:
            yes_color = QColor(200, 255, 200, 100)
            no_color = QColor(25, 200, 200, 100)

        palette = QPalette()
        if flag:
            palette.setColor(QPalette().Base, no_color)
        else:
            palette.setColor(QPalette().Base, yes_color)

        self._directory_edit.setPalette(palette)

    def _on_text_changed(self, text):
        directory = self.get_directory()
        if os.path.exists(directory):
            self.set_error(False)
        else:
            self.set_error(True)

        if not text:
            self._directory_edit.setPalette(lineedits.BaseLineEdit().palette())

        self.directoryChanged.emit(directory)

    def _on_browse(self):
        directory = self.get_directory()
        if not directory:
            placeholder = self._directory_edit.placeholderText()
            if placeholder and placeholder.startswith('example: '):
                example_path = placeholder[0]
                if os.path.exists(example_path):
                    directory = example_path

        filename = qtutils.get_folder(directory, show_files=self._show_files, parent=self)
        filename = path.clean_path(filename)
        if filename and path.is_dir(filename):
            self._directory_edit.setText(filename)
            self.directoryChanged.emit(filename)
