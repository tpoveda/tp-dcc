#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for Houdini dialogs
"""

from __future__ import print_function, division, absolute_import

import os

from tpDcc.libs.python import path as path_utils
from tpDcc.libs.qt.widgets import dialog
from tpDcc.dccs.houdini.core import directory


class HoudiniDialog(dialog.BaseDialog):
    def __init__(self, name='HoudiniDialog', parent=None, **kwargs):
        super(HoudiniDialog, self).__init__(name=name, parent=parent, **kwargs)


class HoudiniOpenFileDialog(dialog.BaseOpenFileDialog):
    def __init__(self, name='HoudiniOpenFileDialog', parent=None, **kwargs):
        super(HoudiniOpenFileDialog, self).__init__(name=name, parent=parent, **kwargs)


class HoudiniSaveFileDialog(dialog.BaseSaveFileDialog):
    def __init__(self, name='HoudiniSaveFileDialog', parent=None, **kwargs):
        super(HoudiniSaveFileDialog, self).__init__(name=name, parent=parent, **kwargs)


class HoudiniSelectFolderDialog(dialog.BaseSelectFolderDialog):
    def __init__(self, name='HoudiniSelectFolderDialog', parent=None, **kwargs):
        super(HoudiniSelectFolderDialog, self).__init__(name=name, parent=parent, **kwargs)


class HoudiniNativeDialog(dialog.BaseNativeDialog):

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
