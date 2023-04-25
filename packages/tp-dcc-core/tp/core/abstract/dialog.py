#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC dialog abstract implementation
"""

from tp.common.python import decorators


class AbstractDialog(object):

    def __init__(self, *args, **kwargs):
        super(AbstractDialog, self).__init__(*args, **kwargs)

    @decorators.abstractmethod
    def default_settings(self):
        pass

    @decorators.abstractmethod
    def load_theme(self):
        pass

    @decorators.abstractmethod
    def set_widget_height(self):
        pass

    @decorators.abstractmethod
    def is_frameless(self):
        pass

    @decorators.abstractmethod
    def set_frameless(self, flag):
        pass


class AbstractColorDialog(object):
    pass


class AbstractFileFolderDialog(object):

    @decorators.abstractmethod
    def open_app_browser(self):
        pass


class AbstractNativeDialog(object):

    @staticmethod
    @decorators.abstractmethod
    def open_file(title='Open File', start_directory=None, filters=None):
        """
        Function that shows open file DCC native dialog
        :param title: str
        :param start_directory: str
        :param filters: str
        :return: str
        """

        raise NotImplementedError('open_file() function is not implemented')

    @staticmethod
    @decorators.abstractmethod
    def save_file(title='Save File', start_directory=None, filters=None):
        """
        Function that shows save file DCC native dialog
        :param title: str
        :param start_directory: str
        :param filters: str
        :return: str
        """

        raise NotImplementedError('save_file() function is not implemented')

    @staticmethod
    @decorators.abstractmethod
    def select_folder(title='Select Folder', start_directory=None):
        """
        Function that shows select folder DCC native dialog
        :param title: str
        :param start_directory: str
        :return: str
        """

        raise NotImplementedError('select_folder() function is not implemented')
