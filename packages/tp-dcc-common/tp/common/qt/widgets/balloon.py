#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Collapsible accordion widget similar to Maya Attribute Editor
"""

from Qt.QtCore import Qt, Signal, QPoint, QTimer, QEvent
from Qt.QtWidgets import QWidget, QDialog
from Qt.QtGui import QPolygon, QRegion


class BalloonDialog(QDialog, object):

    FIXED_HEIGHT = 12
    FIXED_WIDTH = 25

    closed = Signal()

    class BallonDialogFocuser(QWidget, object):
        def __init__(self, w):
            super(BalloonDialog.BallonDialogFocuser, self).__init__()

            self._widget = w

        def show(self):
            """
            Overrides base QWidget show function
            """

            self._widget.show()
            self.focus()

        def focus(self):
            """
            Function that focus wrapped widget
            """

            self._widget.activateWindow()
            self._widget.raise_()

    def __init__(self, modal=False, parent=None):
        super(BalloonDialog, self).__init__(parent)

        self._lazy_show_window = QTimer(self)

        if modal:
            self.setModal(True)

        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self._lazy_show_window.timeout.connect(self._on_lazy_show_window)

    def resizeEvent(self, event):
        """
        Overrides base QDialog resizeEvent function
        :param event: QResizeEvent
        """

        r = self.rect()
        ss = self.styleSheet()
        # ss.replace(str(QRegExp("\\s*margin-top\\s*:\\s*.+?;")), "")
        self.setStyleSheet('{} margin-top: {}px;'.format(ss, self.FIXED_HEIGHT))

        poly = QPolygon()
        poly.append(QPoint(r.x(), r.y() + self.FIXED_HEIGHT))
        poly.append(QPoint(r.x() + r.width() / 2 - self.FIXED_WIDTH / 2, r.y() + self.FIXED_HEIGHT))
        poly.append(QPoint(r.x() + r.width() / 2, r.y()))
        poly.append(QPoint(r.x() + r.width() / 2 + self.FIXED_WIDTH / 2, r.y() + self.FIXED_HEIGHT))
        poly.append(QPoint(r.x() + r.width(), r.y() + self.FIXED_HEIGHT))
        poly.append(QPoint(r.x() + r.width(), r.y() + r.height()))
        poly.append(QPoint(r.x(), r.y() + r.height()))

        new_mask = QRegion(poly)
        self.setMask(new_mask)

    def event(self, e):
        """
        Overrides base QDialog event function
        :param e: QEvent
        :return: bool
        """

        if QEvent.WindowDeactivate == e.type():
            self.done(False)
            self.closed.emit()
            e.ignore()
            self.close()
            return True

        return super(BalloonDialog, self).event(e)

    def focusOutEvent(self, event):
        """
        Overrides base QDialog focusOutEvent function
        :param event: QFocusEven
        """

        pass

    def showEvent(self, event):
        """
        Overrides base QDialog showEvent function
        :param event: QShowEvent
        """

        focuser = BalloonDialog.BallonDialogFocuser(self)
        focuser.focus()

    def _on_lazy_show_window(self):
        """
        Internal callback function that is called when lazy show window timer finishes
        """

        self.activateWindow()
        self.setFocus()
