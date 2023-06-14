#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for Maya windows
"""

import os

import maya.cmds

from Qt.QtCore import Qt
from Qt.QtWidgets import QColorDialog, QPushButton
from Qt.QtGui import QColor

from tp.core import dcc
from tp.common.python import path as path_utils
from tp.common.qt.widgets import layouts, dialog, dividers
from tp.maya.cmds import directory


class MayaDialog(dialog.BaseDialog):
    def __init__(self, name='MayaDialog', parent=None, **kwargs):
        super(MayaDialog, self).__init__(name=name, parent=parent, **kwargs)


class MayaColorDialog(dialog.BaseColorDialog):
    def __init__(self, name='MayaColorDialog', parent=None, **kwargs):
        super(MayaColorDialog, self).__init__(name=name, parent=parent, **kwargs)

    def ui(self):
        if dcc.version() <= 2016:
            self.main_layout = self.get_main_layout()
            self.setLayout(self.main_layout)

            self.color_dialog = QColorDialog(parent=self)
            self.color_dialog.setWindowFlags(Qt.Widget)
            self.color_dialog.setOptions(QColorDialog.DontUseNativeDialog | QColorDialog.NoButtons)
            self.main_layout.addWidget(self.color_dialog)

            bottom_layout = layouts.HorizontalLayout()
            bottom_layout.setAlignment(Qt.AlignRight)
            self.main_layout.addLayout(bottom_layout)

            self.ok_btn = QPushButton('Ok')
            self.cancel_btn = QPushButton('Cancel')
            bottom_layout.addLayout(dividers.DividerLayout())
            bottom_layout.addWidget(self.ok_btn)
            bottom_layout.addWidget(self.cancel_btn)

        else:
            super(MayaColorDialog, self).ui()

    def setup_signals(self):
        if dcc.version() <= 2016:
            pass
        else:
            super(MayaColorDialog, self).setup_signals()

    def _on_set_color(self, color_index):
        if dcc.version() <= 2016:
            self.color_dialog.setCurrentColor(QColor.fromRgb(
                self.maya_colors[color_index][0] * 255,
                self.maya_colors[color_index][1] * 255,
                self.maya_colors[color_index][2] * 255
            ))
        else:
            super(MayaColorDialog, self)._on_set_color()

    def _on_ok_btn(self):
        if dcc.version() <= 2016:
            self.close()
        else:
            super(MayaColorDialog, self)._on_ok_btn()


class MayaOpenFileDialog(dialog.BaseOpenFileDialog):
    def __init__(self, name='MayaOpenFileDialog', parent=None, **kwargs):
        super(MayaOpenFileDialog, self).__init__(name=name, parent=parent, **kwargs)

    def open_app_browser(self):
        sel_file = maya.cmds.fileDialog2(
            caption=self.windowTitle(),
            fileMode=1,
            fileFilter=self.filters,
            dialogStyle=2
        )
        if sel_file:
            sel_file = sel_file[0]
            return [sel_file, os.path.dirname(sel_file), [os.path.basename(sel_file)]]

        return None


class MayaSaveFileDialog(dialog.BaseSaveFileDialog):
    def __init__(self, name='MaxSaveFileDialog', parent=None, **kwargs):
        super(MayaSaveFileDialog, self).__init__(name=name, parent=parent, **kwargs)

    def open_app_browser(self):
        sel_file = maya.cmds.fileDialog2(
            caption=self.windowTitle(),
            fileMode=0,
            fileFilter=self.filters,
            dialogStyle=2
        )
        if sel_file:
            sel_file = sel_file[0]
            return [sel_file, os.path.dirname(sel_file), [os.path.basename(sel_file)]]

        return None


class MayaSelectFolderDialog(dialog.BaseSelectFolderDialog):
    def __init__(self, name='MaxSelectFolderDialog', parent=None, **kwargs):
        super(MayaSelectFolderDialog, self).__init__(name=name, parent=parent, **kwargs)

    def open_app_browser(self):
        sel_folder = maya.cmds.fileDialog2(
            caption=self.windowTitle(),
            fileMode=3,
            fileFilter=self.filters,
            dialogStyle=2
        )
        if sel_folder:
            sel_folder = sel_folder[0]
            return [sel_folder, os.path.dirname(sel_folder), [os.path.basename(sel_folder)]]

        return None


class MayaNativeDialog(dialog.BaseNativeDialog):

    @staticmethod
    def open_file(title='Open File', start_directory=None, filters=None):
        """
        Function that shows open file Max native dialog
        :param title: str
        :param start_directory: str
        :param filters: str
        :return: str
        """

        start_directory = start_directory if start_directory else os.path.expanduser('~')
        clean_path = path_utils.clean_path(start_directory)
        file_path = directory.select_file_dialog(title=title, start_directory=clean_path, pattern=filters)

        return file_path

    @staticmethod
    def save_file(title='Save File', start_directory=None, filters=None):
        """
        Function that shows save file Max native dialog
        :param title: str
        :param start_directory: str
        :param filters: str
        :return: str
        """

        start_directory = start_directory if start_directory else os.path.expanduser('~')
        clean_path = path_utils.clean_path(start_directory)
        file_path = directory.save_file_dialog(title=title, start_directory=clean_path, pattern=filters)

        return file_path

    @staticmethod
    def select_folder(title='Select Folder', start_directory=None):
        """
        Function that shows select folder Maya dialog
        :param title: str
        :param start_directory: str
        :return: str
        """

        start_directory = start_directory if start_directory else os.path.expanduser('~')
        clean_path = path_utils.clean_path(start_directory)
        folder_path = directory.select_folder_dialog(title=title, start_directory=clean_path)

        return folder_path
