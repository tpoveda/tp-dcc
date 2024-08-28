from __future__ import annotations

from typing import Type

from Qt.QtCore import Qt, Signal, QEvent
from Qt.QtWidgets import QApplication, QWidget, QHBoxLayout, QLayout
from Qt.QtGui import QMouseEvent, QKeyEvent

from .. import utils
from ..widgets import dialogs


class OverlayWidget(dialogs.BaseDialog):
    widgetMousePress = Signal(object)
    widgetMouseMove = Signal(object)
    widgetMouseRelease = Signal(object)

    PRESSED = False
    OVERLAY_ACTIVE_KEY = Qt.AltModifier

    def __init__(self, parent: QWidget, layout_class: Type = QHBoxLayout):
        super().__init__(show_on_initialize=False, parent=parent)

        self._debug = False
        self.main_layout: QLayout | None = None

        self.set_debug_mode(False)
        self.setup_ui(layout_class)

    # noinspection PyMethodOverriding
    def update(self):
        self.setGeometry(
            0, 0, self.parent().geometry().width(), self.parent().geometry().height()
        )
        super().update()

    def enterEvent(self, event: QEvent) -> None:
        if not self.PRESSED:
            self.hide()

        event.ignore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not QApplication.keyboardModifiers() == self.OVERLAY_ACTIVE_KEY:
            event.ignore()
            return

        self.widgetMousePress.emit(event)
        self.PRESSED = True
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        pass

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        self.widgetMouseRelease.emit(event)
        self.PRESSED = False
        self.update()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        self.hide()

    # noinspection PyArgumentList
    def show(self, *args, **kwargs) -> None:
        self.PRESSED = True
        super().show(*args, **kwargs)
        self.update()

    def setup_ui(self, layout_class: Type = QLayout):
        """
        Setup overlay widget UI.

        :param Type layout_class: layout class for the overlay to use.
        """

        if utils.is_pyside2() or utils.is_pyqt5():
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.update()

        self.main_layout = layout_class()
        self.setLayout(self.main_layout)

    def set_debug_mode(self, debug: bool):
        """
        Debug mode to show where the dialog window is. Turns the window a transparent red

        :param bool debug: whether loading debug mode is enabled.
        """
        self._debug = debug
        if debug:
            self.setStyleSheet("background-color: #88ff0000;")
        else:
            self.setStyleSheet("background-color: transparent;")
