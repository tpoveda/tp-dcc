#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for overlay widgets
"""

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QApplication

from tpDcc.libs.qt.widgets import dialog


class OverlayWidget(dialog.BaseDialog, object):
    """
    Invisible overlay widget used to capture mouse events among other things
    """

    widgetMousePress = Signal(object)
    widgetMouseMove = Signal(object)
    widgetMouseRelease = Signal(object)

    OVERLAY_ACTIVE_KEY = Qt.AltModifier
    _PRESSED = False

    def __init__(self, parent):
        super(OverlayWidget, self).__init__(parent=parent, show_on_initialize=False)

        self.set_debug_mode(False)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setMouseTracking(True)
        self.update()

    def mousePressEvent(self, event):
        """
        Overrides base QDialog mousePressEvent
        :param event:
        :return:
        """

        if not QApplication.keyboardModifiers() == self.OVERLAY_ACTIVE_KEY:
            event.ignore()
            return

        self.widgetMousePress.emit(event)
        self._PRESSED = True
        self.update()

    def enterEvent(self, event):
        """
        Overrides base QDialog enterEvent
        :param event:
        :return:
        """

        if not self._PRESSED:
            self.hide()

        event.ignore()

    def mouseMoveEvent(self, event):
        """
        Overrides base QDialog mouseMoveEvent
        :param event:
        :return:
        """

        pass

    def mouseReleaseEvent(self, event):
        """
        Overrides base QDialog mouseReleaseEvent
        :param event:
        :return:
        """

        self.widgetMouseRelease.emit(event)
        self._PRESSED = False
        self.update()

    def keyReleaseEvent(self, event):
        """
        Overrides base QDialog mousePressEvent
        :param event:
        :return:
        """

        self.hide()

    def update(self):
        """
        Overrides base QDialog update function
        Updates geometry to match parents geometry
        :return:
        """

        self.setGeometry(0, 0, self.parent().geometry().width(), self.parent().geometry().height())

    def show(self, *args, **kwargs):
        """
        Overrides base QDialog show
        :param event:
        :return:
        """

        self._PRESSED = True
        super(OverlayWidget, self).show(*args, **kwargs)
        self.update()

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def set_debug_mode(self, flag):
        """
        Enables or disable debug mode by making window semi red transparent. Useful to know where the widget is located
        :param flag: bool
        """

        if flag:
            self.setStyleSheet('background-color: #88ff0000;')
        else:
            self.setStyleSheet('background-color: transparent;')
