from __future__ import annotations

from typing import Type

from Qt.QtCore import Qt, Signal, QEvent, QSize
from Qt.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QLabel,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
)
from Qt.QtGui import QMouseEvent, QKeyEvent

from .dialogs import BaseDialog
from .. import uiconsts, utils, dpi, icons


class OverlayWidget(BaseDialog):
    """Base class for overlay widgets."""

    widgetMousePress = Signal(object)
    widgetMouseMove = Signal(object)
    widgetMouseRelease = Signal(object)

    PRESSED = False
    OVERLAY_ACTIVE_KEY = Qt.AltModifier

    def __init__(
        self,
        parent: QWidget,
        layout_class: Type[QVBoxLayout | QHBoxLayout | QGridLayout] = QHBoxLayout,
    ) -> None:
        super().__init__(show_on_initialize=False, parent=parent)

        self._debug = False
        self.main_layout: QVBoxLayout | QHBoxLayout | QGridLayout | None = None

        self.set_debug_mode(False)
        self._setup_ui(layout_class)

    # noinspection PyMethodOverriding
    def update(self) -> None:
        """Override update function to make sure the overlay covers the
        entire parent widget.
        """

        self.setGeometry(
            0, 0, self.parent().geometry().width(), self.parent().geometry().height()
        )
        super().update()

    def enterEvent(self, event: QEvent) -> None:
        """Event called when the mouse enters the overlay widget area.

        This event is ignored if the overlay is not pressed, so the event
        propagates to the parent widget.

        Args:
            event: Event instance.
        """

        if not self.PRESSED:
            self.hide()

        event.ignore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle the mouse press event on the widget, checking specific key
        modifiers and triggering appropriate responses.

        Args:
            event: The mouse press event being handled.
        """

        if not QApplication.keyboardModifiers() == self.OVERLAY_ACTIVE_KEY:
            event.ignore()
            return

        self.widgetMousePress.emit(event)
        self.PRESSED = True
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle the mouse move event.

        This method is triggered when the mouse is moved within the widget.
        It can be used to perform actions such as updating visuals or
        detecting interactions.

        Args:
            event: The event object containing details about the mouse
            movement, including position, buttons pressed, and other
            related data.
        """

        pass

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handles mouse release events.

        This method is triggered when a mouse release action occurs on the widget.
        It emits the `widgetMouseRelease` signal, updates the internal state to
        indicate that no mouse button is pressed, and requests a widget redraw.

        Args:
            event: The mouse event object containing information  about the
            mouse release action.
        """

        self.widgetMouseRelease.emit(event)
        self.PRESSED = False
        self.update()

    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        """Handle the event of a key being released.

        This method is used to respond to key release events and performs a
        specific  action when a key is released by the user.

        Args:
            event: The event object containing information about the key
                released.
        """

        self.hide()

    # noinspection PyArgumentList
    def show(self, *args, **kwargs) -> None:
        """Overrides show function to set the PRESSED flag to True
        when the overlay is shown.
        """

        self.PRESSED = True
        super().show(*args, **kwargs)
        self.update()

    def _setup_ui(
        self,
        layout_class: Type[QVBoxLayout | QHBoxLayout | QGridLayout] = QHBoxLayout,
    ):
        """Set up the overlay widget UI.

        Args:
            layout_class: Layout class for the overlay to use.
        """

        if utils.is_pyside2() or utils.is_pyqt5():
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        else:
            self.setWindowFlags(Qt.FramelessWindowHint)
        self.setMouseTracking(True)
        self.update()

        self.main_layout = layout_class()
        self.setLayout(self.main_layout)

        self.setup_ui()

    def setup_ui(self):
        """Method to be overridden by subclasses to set up the UI."""

    def set_debug_mode(self, debug: bool):
        """Debug mode to show where the dialog window is. Turns the window a transparent red

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

    def setup_ui(self):
        super().setup_ui()

        self.setStyleSheet("LoadingWidget {background-color: #77111111;}")

        label = QLabel("Loading...  ", parent=self)
        image_label = QLabel(parent=self)
        pixmap_size = dpi.dpi_scale(24)
        image_label.setPixmap(
            icons.icon("clock_start").pixmap(pixmap_size, pixmap_size)
        )

        self._loading_frame = OverlayLoadingFrame(self)
        self._loading_frame.setFixedSize(dpi.size_by_dpi(QSize(150, 40)))
        utils.set_stylesheet_object_name(self._loading_frame, "border")
        self._loading_frame_layout = QHBoxLayout()
        self._loading_frame.setLayout(self._loading_frame_layout)

        self._loading_frame_layout.addWidget(image_label)
        self._loading_frame_layout.addWidget(label)
        self._loading_frame_layout.setContentsMargins(
            *dpi.margins_dpi_scale(5, 0, 5, 0)
        )
        self._loading_frame_layout.setStretch(0, 2)
        self._loading_frame_layout.setStretch(1, 3)

        self.main_layout.addStretch(1)
        self.main_layout.addWidget(self._loading_frame)
        self.main_layout.addStretch(1)

    def update(self) -> None:
        """Overrides update function to make sure the overlay covers the
        entire parent widget.
        """

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

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Overrides `mousePressEvent` function to hide the overlay when
        clicked.

        Args:
            event: Mouse event.
        """

        super().mousePressEvent(event)
        self.hide()


class OverlayLoadingFrame(QFrame):
    """For style purposes."""

    pass
