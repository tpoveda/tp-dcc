from __future__ import annotations

from typing import Type

from Qt.QtCore import Qt, Signal, QEvent, QSize
from Qt.QtWidgets import QApplication, QWidget, QFrame, QHBoxLayout, QLayout
from Qt.QtGui import QIcon, QMouseEvent, QKeyEvent

from .labels import BaseLabel
from .dialogs import BaseDialog
from .. import uiconsts, utils, dpi
from ...python.paths import canonical_path


class OverlayWidget(BaseDialog):
    """
    Base class for overlay widgets.
    """

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

    def enterEvent(self, event: QEvent):
        if not self.PRESSED:
            self.hide()

        event.ignore()

    def mousePressEvent(self, event: QMouseEvent):
        if not QApplication.keyboardModifiers() == self.OVERLAY_ACTIVE_KEY:
            event.ignore()
            return

        self.widgetMousePress.emit(event)
        self.PRESSED = True
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pass

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.widgetMouseRelease.emit(event)
        self.PRESSED = False
        self.update()

    def keyReleaseEvent(self, event: QKeyEvent):
        self.hide()

    # noinspection PyArgumentList
    def show(self, *args, **kwargs):
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


# noinspection PyAttributeOutsideInit
class OverlayLoadingWidget(OverlayWidget):
    def __init__(self, parent=None):
        super().__init__(layout_class=QHBoxLayout, parent=parent)

    def setup_ui(self, layout_class: Type = QLayout):
        super().setup_ui(layout_class)

        self.setStyleSheet("LoadingWidget {background-color: #77111111;}")

        label = BaseLabel("Loading...  ", parent=self)
        image_label = BaseLabel(parent=self)
        pix_size = dpi.dpi_scale(24)
        image_label.setPixmap(
            QIcon(canonical_path("../../resources/icons/clock_start.png")).pixmap(
                pix_size, pix_size
            )
        )

        self._loading_frame = OverlayLoadingFrame(self)
        self._loading_frame.setFixedSize(dpi.size_by_dpi(QSize(150, 40)))
        utils.set_stylesheet_object_name(self._loading_frame, "border")
        self._loading_frame_layout = QHBoxLayout()
        self._loading_frame.setLayout(self._loading_frame_layout)

        # the loading widget with the label and text
        self._loading_frame_layout.addWidget(image_label)
        self._loading_frame_layout.addWidget(label)
        self._loading_frame_layout.setContentsMargins(
            *dpi.margins_dpi_scale(5, 0, 5, 0)
        )
        self._loading_frame_layout.setStretch(0, 2)
        self._loading_frame_layout.setStretch(1, 3)

        # noinspection PyUnresolvedReferences
        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self._loading_frame)
        # noinspection PyUnresolvedReferences
        self.main_layout.addStretch(1)

    def update(self):
        x1 = uiconsts.FRAMELESS_HORIZONTAL_PADDING
        y1 = uiconsts.FRAMELESS_VERTICAL_PADDING

        x_padding = uiconsts.FRAMELESS_HORIZONTAL_PADDING
        y_padding = uiconsts.FRAMELESS_VERTICAL_PADDING

        self.setGeometry(
            x1,
            y1,
            self.parent().geometry().width() - x_padding * 2,
            self.parent().geometry().height() - y_padding * 2,
        )
        super().update()

    def mousePressEvent(self, event: QMouseEvent):
        """
        Overrides mousePressEvent function.

        :param event: Qt mouse event.
        """

        super().mousePressEvent(event)
        self.hide()


class OverlayLoadingFrame(QFrame):
    """
    For style purposes.
    """

    pass
