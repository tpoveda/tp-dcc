#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for 3ds max dialogs
"""

import os

from tp.common.python import path as path_utils
from tp.common.qt.widgets import dialog
from tp.max.core import directory


class MaxDialog(dialog.BaseDialog, object):
    def __init__(self, name='MaxDialog', parent=None, **kwargs):
        super(MaxDialog, self).__init__(name=name, parent=parent, **kwargs)


class MaxOpenFileDialog(dialog.BaseOpenFileDialog, object):
    def __init__(self, name='MaxOpenFileDialog', parent=None, **kwargs):
        super(MaxOpenFileDialog, self).__init__(name=name, parent=parent, **kwargs)


class MaxSaveFileDialog(dialog.BaseSaveFileDialog, object):
    def __init__(self, name='MaxSaveFileDialog', parent=None, **kwargs):
        super(MaxSaveFileDialog, self).__init__(name=name, parent=parent, **kwargs)


class MaxSelectFolderDialog(dialog.BaseSelectFolderDialog, object):
    def __init__(self, name='MaxSelectFolderDialog', parent=None, **kwargs):
        super(MaxSelectFolderDialog, self).__init__(name=name, parent=parent, **kwargs)


class MaxNativeDialog(dialog.BaseNativeDialog, object):

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
