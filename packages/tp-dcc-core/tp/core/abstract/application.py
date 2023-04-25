#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC application abstract implementation
"""

from Qt.QtWidgets import QApplication

from tp.common.python import decorators


class AbstractApp(object):
    def __init__(self):
        super(AbstractApp, self).__init__()

    @staticmethod
    def main_qt_window():
        """
        Returns the application's top most window
        """

        parent = QApplication.activeWindow()
        if parent:
            grand_parent = parent
            while grand_parent is None:
                parent = grand_parent
                grand_parent = parent.parent()

        return parent

    @decorators.abstractmethod
    def name(self):
        """
        Returns the unique name of the DCC.
        """

        return ''

    @decorators.abstractmethod
    def get_extension(self):
        """
        Returns file extension of the DCC app
        :return: str
        """

        return ''

    @decorators.abstractmethod
    def allowed_characters(self):
        """
        Returns regex expression that validates with all the characters valid for DCC app
        :return: str
        """

        return ''

    @decorators.abstractmethod
    def year(self):
        """
        Returns the version year of the software.
        :return: int, version number
        """
        return 0

    @decorators.abstractmethod
    def version(self):
        """
        Returns the version of the software.
        :return: int || str, version number
        """

        return 0

    @decorators.abstractmethod
    def request_focus(self):
        """
        Requests focus from DCC application
        :return: bool
        """

        return False

    @decorators.abstractmethod
    def use_event_filters(self):
        """
        Returns whether the DCC application can use Qt EventFiltering functionality or not
        :return: bool
        """

        return False

    @decorators.abstractmethod
    def main_dcc_window(self):
        """
        Returns the main window of the current executed DCC
        :param handle: bool, Whether to return pointer handle to the window or window PySide instance
        :return: QMainWindow
        """

        return None

    @decorators.abstractmethod
    def parent_to_dcc_window(self, widget):
        """
        Parent the window/widget to the 3ds Max main window
        """

        return None

    @decorators.abstractmethod
    def get_installation_path(self):
        """
        Returns path where DCC application is installed
        :return: str
        """

        return None

    @decorators.abstractmethod
    def show_warning_window(self, message, title):
        """
        Shows a warning window with the given message and title
        :param message: str, message of the warning window
        :param title: str, title of the warning window
        """

        pass

    @decorators.abstractmethod
    def show_error_window(self, title, message):
        """
        Shows an error window with the given message and title
        :param title: str, title of the error window
        :param message: str, message of the error window
        """

        pass
