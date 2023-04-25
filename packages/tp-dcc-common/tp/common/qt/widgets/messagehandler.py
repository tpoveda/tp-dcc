#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to show different kind of message boxes
"""

from Qt.QtWidgets import QMessageBox

from tpDcc import dcc


class MessageHandler(object):

    def __init__(self):
        super(MessageHandler, self).__init__()

        self.parent_window = dcc.main_window()

    def set_message(self, msg, level=0):
        """
        Sets a message in the status bar
        :param msg: str, message to show
        :param level: message level (0=info, 1=warning, 2=error)
        """

        if level < 0:
            level = 0
        if level > 3:
            level = 3

        # import maya.OpenMaya as OpenMaya
        # output = {0: OpenMaya.MGlobal.displayInfo, 1:
        # OpenMaya.MGlobal.displayWarning, 2: OpenMaya.MGlobal.displayError}
        # output[level](msg)

    def show_confirm_dialog(self, msg, title='Title'):
        """
        Shows a yes/no confirmation dialog
        :param msg: str, message to show with the dialog
        :param title: str, title of the dialog
        :return: bool, Whether the user has pressed yes(True) or No(False)
        """

        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Question)
        result = dialog.question(self.parent_window, title, msg, QMessageBox.Yes, QMessageBox.No)
        if result == QMessageBox.Yes:
            return True
        return False

    def show_warning_dialog(self, msg, detail=None):
        """
        Shows a warning dialog
        :param msg: str, message to show with the dialog
        :param detail: str, detail information to show (optional)
        """

        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle('Warning')
        dialog.setText(msg)
        if detail:
            dialog.setDetailedText(detail)
        dialog.exec_()

    def show_info_dialog(self, msg, title='Info'):
        """
        Shows a info dialog
        :param msg: str, message to show with the dialog
        :param title: str, title of the dialog
        """

        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Information)
        dialog.setWindowTitle(title)
        dialog.setText(msg)
        dialog.exec_()
