#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom tray balloon
"""

from Qt.QtWidgets import QWidget, QSystemTrayIcon, QMenu


class TrayMessage(QWidget, object):

    def __init__(self, parent=None):
        super(TrayMessage, self).__init__(parent=parent)

        self._tools_icon = None

        self.tray_icon_menu = QMenu(self)
        self.tray_icon = QSystemTrayIcon(self)
        # self.tray_icon.setIcon(self._tools_icon)
        self.tray_icon.setToolTip('Tray')
        self.tray_icon.setContextMenu(self.tray_icon_menu)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise OSError('Tray Icon is not available!')

        self.tray_icon.show()

    def show_message(self, title, msg):
        try:
            self.tray_icon.showMessage(title, msg, self._tools_icon)
        except Exception:
            self.tray_icon.showMessage(title, msg)
