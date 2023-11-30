#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains frameless related widgets implementations.
"""

from __future__ import annotations

import uuid
import weakref
import webbrowser
from typing import Tuple, List, Type

from overrides import override
from Qt.QtCore import Qt, Signal, QObject, QPoint, QSize, QTimer, QEvent, QSettings
from Qt.QtWidgets import (
    QApplication, QSizePolicy, QWidget, QFrame, QToolButton, QGridLayout, QVBoxLayout, QHBoxLayout, QMainWindow,
    QTabWidget, QSpacerItem, QAction, QSplitter, QLayout
)
from Qt.QtGui import (
    QCursor, QColor, QPainter, QResizeEvent, QShowEvent, QCloseEvent, QMoveEvent, QMouseEvent, QKeyEvent
)

from tp.core import log, dcc
from tp.preferences.interfaces import core as core_interfaces
from tp.common.python import osplatform
from tp.common.qt import consts, dpi, qtutils
from tp.common.qt.widgets import layouts, overlay, buttons, labels
from tp.common.resources import icon
from tp.common.resources import api as resources

if dcc.is_maya():
    import maya.cmds as cmds
    from maya.app.general import mayaMixin
    from tp.maya.cmds.ui import docking
    from tp.maya.cmds.ui import tooltips

logger = log.tpLogger


def frameless_windows() -> List[FramelessWindow]:
    """
    Returns all frameless windows in the scene.

    :return: list of frameless windows.
    :rtype: List[FramelessWindow]
    """

    found_windows = list()
    for child in dcc.main_window().children():
        if isinstance(child, FramelessWindow):
            found_windows.append(child)

    return found_windows


class ContainerType:
    """
    Class that defines the different frameless container types
    """

    Docking = 1
    FramelessWindow = 2


class ContainerWidget:
    """
    Abstract class used by custom container widgets.

    This class should never be instantiated directly.
    """

    def is_docking_container(self) -> bool:
        """
        Returns whether current instance is a docking container widget.

        :return: True if current instance is a DockingContainer instance; False otherwise.
        :rtype: bool
        """

        return isinstance(self, DockingContainer)

    def is_frameless_window(self) -> bool:
        """
        Returns whether current instance is a frameless window widget.

        :return: True if current instance is a FramelessWindow instance; False otherwise.
        :rtype: bool
        """

        return isinstance(self, FramelessWindowContainer)

    def container_type(self) -> int:
        """
        Returns the type of container.

        :return: type container.
        :rtype: int
        """

        return ContainerType.FramelessWindow if self.is_frameless_window() else ContainerType.Docking

    def set_widget(self, widget: QWidget):
        """
        Sets container widget.

        :param QWidget widget: container widget.
        """

        self.setObjectName(widget.objectName())

    def set_on_top(self, flag: bool):
        """
        Sets whether container should stay on top.

        :param bool flag: True to set container on top; False otherwise.
        """

        pass


if dcc.is_maya():
    DockableMixin = mayaMixin.MayaQWidgetDockableMixin
else:
    class DockableMixin:
        pass


class DockingContainer(DockableMixin, QWidget, ContainerWidget):
    """
    Custom widget container that can be docked withing DCCs
    """

    def __init__(self, parent: QMainWindow | None = None, workspace_control_name: str | None = None, *args, **kwargs):
        super(DockingContainer, self).__init__(parent=parent, *args, **kwargs)

        self._main_widget = None                    # type: FramelessWindow
        self._orig_widget_size = None                # type: QSize
        self._win = None                            # type: QWidget
        self._prev_floating = True
        self._detaching = False
        self._workspace_control = parent
        self._workspace_control_name = workspace_control_name
        self._detach_counter = 0
        self._logo_icon = QToolButton(parent=self)
        self._container_size = self.size()

        self._setup_ui()

    @override
    def enterEvent(self, event: QEvent) -> None:
        """
        Overrides base QWidget enterEvent function.

        :param QEvent event: Qt enter event event.
        """

        if self._detaching:
            self.undock()

    @override
    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Overrides base QWidget resizeEvent function.

        :param QEvent event: Qt resize event.
        """

        if not self._detaching and not self.isFloating():
            self._container_size = self.size()

        return super().resizeEvent(event)

    @override
    def showEvent(self, event: QShowEvent) -> None:
        """
        Overrides base QWidget showEvent function.

        :param QShowEvent event: Qt show event.
        """

        if not self.isFloating():
            self._logo_icon.hide()
        if not self._prev_floating and self.isFloating():
            self._detaching = True
        self._prev_floating = self.isFloating()

    @override
    def moveEvent(self, event: QMoveEvent) -> None:
        """
        Overrides base QWidget moveEvent function.

        :param QMoveEvent event: Qt move event.
        """

        if not self._detaching:
            return

        # Use detach counter to workaround issue where detaching would prematurely run the undock command.
        self._detach_counter += 1
        new_size = QSize(self._container_size.width(), self._orig_widget_size.height())
        self.setFixedSize(new_size)

        # Check detach event twice before undocking because sometimes when you drag off the window does not stay on
        # the mouse.
        if self._detach_counter == 2:
            self.undock()

    def set_widget(self, widget: FramelessWindow):
        """
        Overrides base FramelessWindow set_widget function.

        :param FramelessWindow widget: frameless window widget.
        """

        self._main_widget = widget
        self._orig_widget_size = QSize(self._main_widget.size())
        self.layout().addWidget(widget)
        super().set_widget(widget)
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)

    def move_to_mouse(self):
        """
        Moves current dock widget into current mouse cursor position.
        """

        pos = QCursor.pos()
        window = self._win
        if self._win == dcc.main_window() and self._win is not None:
            logger.error('{}: Found Maya window instead of DockingContainer!'.format(
                self._workspace_control_name))
            return
        offset = qtutils.window_offset(window)
        half = qtutils.widget_center(window)
        pos += offset - half
        window.move(pos)
        window.setWindowOpacity(0.8)

    def undock(self):
        """
        Undocks container widget.
        """

        self._detach_counter = 0
        self._detaching = False

        if self.isFloating():
            frameless = self._main_widget.attach_to_frameless_window(save_window_pref=False)
            pos = self.mapToGlobal(QPoint())
            width = self._container_size.width()
            frameless.show()
            frameless.setGeometry(pos.x(), pos.y(), width, self._orig_widget_size.height())
            self._main_widget.title_bar.logo_button.delete_control()
            self._main_widget.undocked.emit()
            self._workspace_control = None

    def delete_control(self):
        """
        Deletes workspace control.
        """

        if not dcc.is_maya():
            return

        cmds.deleteUI(self._workspace_control_name)

    def _setup_ui(self):
        """
        Internal function that initializes docking widget UI.
        """

        size = 24
        ui_layout = layouts.vertical_layout(margins=(0, 0, 0, 0))
        ui_layout.addWidget(self._logo_icon)
        self.setLayout(ui_layout)
        self._logo_icon.setIcon(icon.colorize_icon('tpdcc', size=size))
        self._logo_icon.setIconSize(dpi.size_by_dpi(QSize(size, size)))
        self._logo_icon.clicked.connect(self.close)
        self._win = self.window()


class FramelessWindowContainer(QMainWindow, ContainerWidget):
    """
    Frameless window implementation.
    """

    closed = Signal()

    def __init__(
            self, width: int | None = None, height: int | None = None, save_window_pref: bool = True,
            on_top: bool = False, parent: QWidget | None =None):

        self._on_top = on_top
        if dcc.is_blender():
            self._on_top = True

        QMainWindow.__init__(self, parent=parent)

        if osplatform.is_mac():
            # macOS needs it the saveWindowPref all the time otherwise it will be behind the other windows.
            self.save_window_pref()
            qtutils.single_shot_timer(lambda: self._setup_size(width, height))
        else:
            if save_window_pref:
                self.save_window_pref()
            self._setup_size(width, height)

        self._shadow_effect = None
        self._default_window_flags = self.windowFlags()

        self._setup_ui()

    @property
    def frameless_window(self) -> FramelessWindow:
        return self.centralWidget()

    @override
    def closeEvent(self, event: QCloseEvent) -> None:
        super(FramelessWindowContainer, self).closeEvent(event)

        self.closed.emit()

    @override(check_signature=False)
    def set_widget(self, widget: FramelessWindow):
        """
        Overrides base FramelessWindow set_widget function.

        :param QWidget widget: window central widget.
        """

        self.setCentralWidget(widget)
        self.set_shadow_effect_enabled(True)

        # Disable for macOS because it seems to create an invisible window in front.
        if not osplatform.is_mac():
            self._set_new_object_name(widget)

    @override
    def set_on_top(self, flag: bool):
        """
        Sets whether container should stay on top.

        :param bool flag: True to set container on top; False otherwise.
        """

        flags = self.windowFlags()
        if flag:
            flags = flags | Qt.WindowStaysOnTopHint
        else:
            flags = flags ^ Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.hide()
        self.show()

    def set_shadow_effect_enabled(self, flag: bool) -> bool:
        """
        Sets whether frameless window shadow effect is enabled.

        :param bool flag: True to enable shadow effect; False otherwise.
        :return: True if shadow effect was set successfully; False otherwise.
        :rtype: bool
        """

        if not self.frameless_window:
            logger.warning('Cannot apply shadow effect window because no frameless window set')
            return False

        self._shadow_effect = qtutils.set_shadow_effect_enabled(self.frameless_window, flag)

        return True

    def set_transparency(self, flag: bool):
        """
        Sets whether window transparency effect is enabled.

        :param bool flag: True to enable window transparency effect; False otherwise.
        """

        window = self.window()
        if flag:
            window.setAutoFillBackground(False)
        else:
            window.setAttribute(Qt.WA_NoSystemBackground, False)

        window.setAttribute(Qt.WA_TranslucentBackground, flag)
        window.repaint()

    def save_window_pref(self):
        """
        Function that forces the window to automatically be parented to DCC main window and also to force the saving
        of the window size and position.

        ..note:: this functionality is only supported in Maya
        """

        if not dcc.is_maya():
            return

        self.setProperty('saveWindowPref', True)

    def _setup_size(self, width: int, height: int):
        """
        Internal function that initializes frameless window size.

        :param int width: initial width in pixels.
        :param int height: initial height in pixels.
        """

        if not (width is None and height is None):
            if width is None:
                width = dpi.dpi_scale(self.size().width())
            elif height is None:
                height = dpi.dpi_scale(self.size().height())
            self.resize(width, height)

    def _setup_ui(self):
        """
        Internal function that initializes frameless window UI.
        """

        self.setAttribute(Qt.WA_TranslucentBackground)
        if qtutils.is_pyside6() or qtutils.is_pyside2() or qtutils.is_pyqt5():
            window_flags = self.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        else:
            window_flags = self.windowFlags() | Qt.FramelessWindowHint
        if self._on_top:
            window_flags = window_flags | Qt.WindowStaysOnTopHint
        self._default_window_flags = window_flags ^ Qt.WindowMinMaxButtonsHint
        self.setWindowFlags(self._default_window_flags)
        self.layout().setContentsMargins(0, 0, 0, 0)

    def _set_new_object_name(self, widget: QWidget):
        """
        Internal function that updates this instance object name based on the given widget.

        :param QWidget widget: frameless window central widget.
        """

        self.setObjectName(widget.objectName() + 'Frameless')


class FramelessOverlay(overlay.OverlayWidget):

    MOVED_BUTTON = Qt.MiddleButton
    RESIZE_BUTTON = Qt.RightButton

    def __init__(
            self, parent: FramelessWindow, title_bar: FramelessWindow.TitleBar, top_left: CornerResizer | None = None,
            top_right: CornerResizer | None = None, bottom_left: CornerResizer | None = None,
            bottom_right: CornerResizer | None = None, resizable: bool = True):
        super().__init__(parent=parent)

        self._pressed_at = None                    # type: QPoint
        self._resize_direction = 0
        self._resizable = resizable
        self._title_bar = title_bar
        self._top_left = top_left
        self._top_right = top_right
        self._bottom_left = bottom_left
        self._bottom_right = bottom_right

    @classmethod
    def is_modifier(cls) -> bool:
        modifiers = QApplication.keyboardModifiers()
        return modifiers == Qt.AltModifier

    @override
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Overrides base QWidget mousePressEvent function.
        Alt + Middle click to move window.

        :param QMouseEvent event: Qt mouse press event.
        """

        self._pressed_at = QCursor.pos()
        if not self.isEnabled():
            event.ignore()
            super().mousePressEvent(event)
            return

        if self.is_modifier() and event.buttons() & self.MOVED_BUTTON:
            self._title_bar.start_move()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        if self.is_modifier() and event.buttons() & self.RESIZE_BUTTON and self._resizable:
            self._resize_direction = self._quadrant()
            if self._resize_direction == ResizerDirection.Top | ResizerDirection.Right:
                self._top_right.window_resize_start()
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif self._resize_direction == ResizerDirection.Top | ResizerDirection.Left:
                self._top_left.window_resize_start()
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            elif self._resize_direction == ResizerDirection.Bottom | ResizerDirection.Left:
                self._bottom_left.window_resize_start()
                self.setCursor(Qt.CursorShape.SizeBDiagCursor)
            elif self._resize_direction == ResizerDirection.Bottom | ResizerDirection.Right:
                self._bottom_right.window_resize_start()
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)

        if (not self.is_modifier() and event.buttons() & self.MOVED_BUTTON) or (
                not self.is_modifier() and event.buttons() & self.RESIZE_BUTTON):
            self.hide()

        event.ignore()
        return super().mousePressEvent(event)

    @override
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.isEnabled():
            event.ignore()
            super().mouseMoveEvent(event)
            return

        if not self.is_modifier():
            self.hide()
            return

        self._title_bar.mouseMoveEvent(event)

        if self._resize_direction != 0:
            if self._resize_direction == ResizerDirection.Top | ResizerDirection.Right:
                self._top_right.windowResized.emit()
            elif self._resize_direction == ResizerDirection.Top | ResizerDirection.Left:
                self._top_left.windowResized.emit()
            elif self._resize_direction == ResizerDirection.Bottom | ResizerDirection.Left:
                self._bottom_left.windowResized.emit()
            elif self._resize_direction == ResizerDirection.Bottom | ResizerDirection.Right:
                self._bottom_right.windowResized.emit()

        event.ignore()

        super().mouseMoveEvent(event)

    @override
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if not self.isEnabled():
            event.ignore()
            super().mouseReleaseEvent(event)
            return

        self._title_bar.end_move()
        self._top_left.windowResizedFinished.emit()
        self._top_right.windowResizedFinished.emit()
        self._bottom_left.windowResizedFinished.emit()
        self._bottom_right.windowResizedFinished.emit()
        self._resize_direction = 0
        event.ignore()

        if self._pressed_at - QCursor.pos() == QPoint(0, 0):
            qtutils.click_under(QCursor.pos(), 1, modifier=Qt.AltModifier)

        super().mouseReleaseEvent(event)

    @override
    def setEnabled(self, arg__1: bool) -> None:
        self.set_debug_mode(not arg__1)
        self.setVisible(arg__1)
        super().setEnabled(arg__1)

    @override(check_signature=False)
    def show(self) -> None:
        self.update_stylesheet()
        if self.isEnabled():
            super().show()
        else:
            logger.warning('FramelessOverlay.show() was called when it is disabled')

    def update_stylesheet(self):
        """
        Updates style sheet.
        """

        self.set_debug_mode(self._debug)

    def _quadrant(self):
        """
        Internal function that returns the quadrant of where the mouse is located and returns the resizer direction.

        :return: resizer direction.
        :rtype: ResizerDirection
        """

        mid_x = self.geometry().width() / 2
        mid_y = self.geometry().height() / 2
        result = 0

        pos = self.mapFromGlobal(QCursor.pos())

        if pos.x() < mid_x:
            result = result | ResizerDirection.Left
        elif pos.x() > mid_x:
            result = result | ResizerDirection.Right

        if pos.y() < mid_y:
            result = result | ResizerDirection.Top
        elif pos.y() > mid_y:
            result = result | ResizerDirection.Bottom

        return result


class ResizerDirection:
    """
    Class that defines all the available resize directions
    """

    Left = 1
    Top = 2
    Right = 4
    Bottom = 8


class Resizers:
    """
    Class that defines all the different resizer types
    """

    Vertical = 1
    Horizontal = 2
    Corners = 4
    All = Vertical | Horizontal | Corners


class WindowResizer(QObject):

    resizeFinished = Signal()

    def __init__(self, parent, install_to_layout=None):
        super().__init__(parent=parent)

        self._frameless_parent = parent
        self._layout = None
        self._is_visible = True

        self._install_to_layout(install_to_layout, parent)
        self._setup_signals()

    @property
    def top_left_resizer(self):
        return self._top_left_resizer

    @property
    def top_right_resizer(self):
        return self._top_right_resizer

    @property
    def bottom_left_resizer(self):
        return self._bottom_left_resizer

    @property
    def bottom_right_resizer(self):
        return self._bottom_right_resizer

    def show(self):
        """
        Shows the resizers.
        """

        self._is_visible = True
        for resizer in self._resizers:
            resizer.show()

    def hide(self):
        """
        Hides the resizers.
        """

        self._is_visible = False
        for resizer in self._resizers:
            resizer.hide()

    def is_visible(self):
        """
        Returns whether resizers are visible.

        :return: True if resizers are visible; False otherwise.
        :rtype: bool
        """

        return self._is_visible

    def resizer_height(self):
        """
        Calculates the total height of the resizers.

        :return: resizer height.
        :rtype: int
        """

        resizers = [self._top_resizer, self._bottom_resizer]
        result = 0
        for r in resizers:
            if not r.isHidden():
                result += r.minimumSize().height()

        return result

    def resizer_width(self):
        """
        Calculates the total widht of the resizers.

        :return: resizer width.
        :rtype: int
        """

        resizers = [self._left_resizer, self._right_resizer]
        ret = 0
        for r in resizers:
            if not r.isHidden():
                ret += r.minimumSize().width()

        return ret

    def set_resize_directions(self):
        """
        Sets the resize directions for the window resizer widgets.
        """

        self._top_resizer.set_resize_direction(ResizerDirection.Top)
        self._bottom_resizer.set_resize_direction(ResizerDirection.Bottom)
        self._right_resizer.set_resize_direction(ResizerDirection.Right)
        self._left_resizer.set_resize_direction(ResizerDirection.Left)
        self._top_left_resizer.set_resize_direction(ResizerDirection.Left | ResizerDirection.Top)
        self._top_right_resizer.set_resize_direction(ResizerDirection.Right | ResizerDirection.Top)
        self._bottom_left_resizer.set_resize_direction(ResizerDirection.Left | ResizerDirection.Bottom)
        self._bottom_right_resizer.set_resize_direction(ResizerDirection.Right | ResizerDirection.Bottom)

    def set_resizer_active(self, flag):
        """
        Sets whether resizers are active.

        :param bool flag: True to activate resizers; False otherwise.
        """

        self.show() if flag else self.hide()

    def set_enabled(self, flag):
        """
        Sets whether resizers are enabled.

        :param bool flag: True to enable resizers; False otherwise.
        """

        [resizer.setEnabled(flag) for resizer in self._resizers]

    def _install_to_layout(self, grid_layout, parent):
        """
        Internal function that install resizers into the given grid layout.

        :param QGridLayout layout: grid layout to install resizers into.
        """

        if not isinstance(grid_layout, QGridLayout):
            logger.error('Resizers only can be installed on grid layouts (QGridLayout)!')
            return

        self._layout = grid_layout

        self._top_resizer = VerticalResizer(ResizerDirection.Top, parent=parent)
        self._bottom_resizer = VerticalResizer(ResizerDirection.Bottom, parent=parent)
        self._right_resizer = HorizontalResizer(ResizerDirection.Right, parent=parent)
        self._left_resizer = HorizontalResizer(ResizerDirection.Left, parent=parent)
        self._top_left_resizer = CornerResizer(ResizerDirection.Left | ResizerDirection.Top, parent=parent)
        self._top_right_resizer = CornerResizer(ResizerDirection.Right | ResizerDirection.Top, parent=parent)
        self._bottom_left_resizer = CornerResizer(ResizerDirection.Left | ResizerDirection.Bottom, parent=parent)
        self._bottom_right_resizer = CornerResizer(ResizerDirection.Right | ResizerDirection.Bottom, parent=parent)

        self._resizers = [
            self._top_resizer, self._top_right_resizer, self._right_resizer, self._bottom_right_resizer,
            self._bottom_resizer, self._bottom_left_resizer, self._left_resizer, self._top_left_resizer
        ]

        grid_layout.addWidget(self._top_left_resizer, 0, 0, 1, 1)
        grid_layout.addWidget(self._top_resizer, 0, 1, 1, 1)
        grid_layout.addWidget(self._top_right_resizer, 0, 2, 1, 1)
        grid_layout.addWidget(self._left_resizer, 1, 0, 2, 1)
        grid_layout.addWidget(self._right_resizer, 1, 2, 2, 1)
        grid_layout.addWidget(self._bottom_left_resizer, 3, 0, 1, 1)
        grid_layout.addWidget(self._bottom_resizer, 3, 1, 1, 1)
        grid_layout.addWidget(self._bottom_right_resizer, 3, 2, 1, 1)

        self.set_resize_directions()

    def _setup_signals(self):
        """
        Internal function that setup resizer signals.
        """

        for resizer in self._resizers:
            resizer.windowResizedFinished.connect(self.resizeFinished.emit)


class Resizer(QWidget):
    """
    Base class that defines resizer widget functionality
    Those resizers can be used in windows and dialogs
    """

    windowResized = Signal()                  # signal emitted when a resize operation is being done
    windowResizedStarted = Signal()           # signal emitted when a resize operation starts
    windowResizedFinished = Signal()          # signal emitted when a resize operation ends

    def __init__(self, direction, parent, debug=False):
        super().__init__(parent)

        self._direction = direction         # resize direction
        self._widget_mouse_pos = None       # caches the position of the mouse
        self._widget_geometry = None        # caches the geometry of the resized widget

        if not debug:
            self.setStyleSheet('background-color: transparent;')
        else:
            self.setStyleSheet('background-color: #88990000')

        self.set_resize_direction(direction)

        # # make sure that resizers are invisible
        # self.setAttribute(Qt.WA_TranslucentBackground)

        self.windowResized.connect(self._on_window_resized)
        self.windowResizedStarted.connect(self._on_window_resize_started)

    def paintEvent(self, event):
        """
        Overrides base QFrame paintEvent function
        Override to make mouse events work in transparent widgets.

        :param QPaintEvente event: Qt paint event
        """

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(255, 0, 0, 0))
        painter.end()

    def mousePressEvent(self, event):
        """
        Overrides base QFrame mousePressEvent function

        :param QEvent event: Qt mouse event
        """

        self.windowResizedStarted.emit()

    def mouseMoveEvent(self, event):
        """
        Overrides base QFrame mouseMoveEvent function

        :param QEvent event: Qt mouse event
        """

        self.windowResized.emit()

    def mouseReleaseEvent(self, event):
        """
        Overrides base QFrame mouseReleaseEvent function

        :param QEvent event: Qt mouse event
        """

        self.windowResizedFinished.emit()

    def set_resize_direction(self, direction):
        """
        Sets the resize direction

        .. code-block:: python
            setResizeDirection(ResizeDirection.Left | ResizeDireciton.Top)

        :param ResizerDirection direction: resize direction.
        :return: resizer direction
        :rtype: int
        """

        self._direction = direction

    def window_resize_start(self):
        """
        Start resize operation.
        """

        self._widget_mouse_pos = self.mapFromGlobal(QCursor.pos())
        self._widget_geometry = self.window().frameGeometry()

    def _on_window_resized(self):
        """
        Internal function that resizes the frame based on the mouse position and the current direction
        """

        pos = QCursor.pos()
        new_geo = self.window().frameGeometry()

        min_width = self.window().minimumSize().width()
        min_height = self.window().minimumSize().height()

        if self._direction & ResizerDirection.Left == ResizerDirection.Left:
            left = new_geo.left()
            new_geo.setLeft(pos.x() - self._widget_mouse_pos.x())
            if new_geo.width() <= min_width:
                new_geo.setLeft(left)
        if self._direction & ResizerDirection.Top == ResizerDirection.Top:
            top = new_geo.top()
            new_geo.setTop(pos.y() - self._widget_mouse_pos.y())
            if new_geo.height() <= min_height:
                new_geo.setTop(top)
        if self._direction & ResizerDirection.Right == ResizerDirection.Right:
            new_geo.setRight(pos.x() + (self.minimumSize().width() - self._widget_mouse_pos.x()))
        if self._direction & ResizerDirection.Bottom == ResizerDirection.Bottom:
            new_geo.setBottom(pos.y() + (self.minimumSize().height() - self._widget_mouse_pos.y()))

        x = new_geo.x()
        y = new_geo.y()
        w = max(new_geo.width(), min_width)
        h = max(new_geo.height(), min_height)

        self.window().setGeometry(x, y, w, h)

    def _on_window_resize_started(self):
        """
        Internal callback function that is called when resize operation starts
        """

        self.window_resize_start()


class CornerResizer(Resizer, object):
    """
    Resizer implementation for window corners
    """

    def __init__(self, direction, parent=None):
        super().__init__(direction=direction, parent=parent)

        self.setFixedSize(dpi.size_by_dpi(QSize(10, 10)))

    def set_resize_direction(self, direction):
        super().set_resize_direction(direction)


        if direction == ResizerDirection.Left | ResizerDirection.Top or \
                direction == ResizerDirection.Right | ResizerDirection.Bottom:
            self.setCursor(Qt.SizeFDiagCursor)
        elif direction == ResizerDirection.Right | ResizerDirection.Top or \
                direction == ResizerDirection.Left | ResizerDirection.Bottom:
            self.setCursor(Qt.SizeBDiagCursor)


class VerticalResizer(Resizer, object):
    """
    Resizer implementation for top and bottom sides of the window
    """

    def __init__(self, direction=Qt.SizeVerCursor, parent=None):
        super().__init__(direction=direction, parent=parent)

        self.setFixedHeight(dpi.dpi_scale(8))

    def set_resize_direction(self, direction):
        super().set_resize_direction(direction)

        self.setCursor(Qt.SizeVerCursor)


class HorizontalResizer(Resizer, object):
    """
    Resizer implementation for left and right sides of the window
    """

    def __init__(self, direction=Qt.SizeHorCursor, parent=None):
        super().__init__(direction=direction, parent=parent)

        self.setFixedHeight(dpi.dpi_scale(8))

    def set_resize_direction(self, direction):
        super().set_resize_direction(direction)

        self.setCursor(Qt.SizeHorCursor)


class FramelessWindowContents(QFrame):
    """
    Frame that contains the contents of a window.
    For CSS purposes.
    """

    pass


class FramelessWindow(QWidget):

    class KeyboardModifierFilter(QObject):

        modifierPressed = Signal()
        windowEvent = Signal(object)

        _CURRENT_EVENT = None

        @override
        def eventFilter(self, watched: QObject, event: QEvent) -> bool:
            self._CURRENT_EVENT = event
            self.windowEvent.emit(event)

            if FramelessOverlay.is_modifier():
                self.modifierPressed.emit()

            return super().eventFilter(watched, event)

    class TitleBar(QFrame):
        """
        Title bar for frameless window that allows to click-drag this windget to move the window widget.
        """

        doubleClicked = Signal()
        moving = Signal(object, object)

        class TitleStyle:
            DEFAULT = 'DEFAULT'
            THIN = 'THIN'

        class TitleLabel(labels.ClippedLabel):
            """
            Custom label implementation with elided functionality used for the title bar title
            Used for CSS purposes.
            """

            def __init__(
                    self, text: str = '', width: int = 0, elide: bool = True, always_show_all: bool = False,
                    parent: QWidget | None = None):
                super().__init__(
                    text=text, width=width, elide=elide, always_show_all=always_show_all, parent=parent)

                self.setAttribute(Qt.WA_TransparentForMouseEvents)
                # self.setAlignment(Qt.AlignRight)

        def __init__(self, show_title: bool = True, always_show_all: bool = False, parent: FramelessWindow | None = None):
            super().__init__(parent)

            self._title_bar_height = 30
            self._pressed_at = None
            self._frameless_window = parent
            self._mouse_pos = None
            self._widget_mouse_pos = None
            self._mouse_press_pos = None
            self._theme_preference = core_interfaces.theme_preference_interface()
            self._toggle = True
            self._icon_size = 13
            self._move_enabled = True
            self._move_threshold = 5

            self._main_layout = layouts.horizontal_layout(parent=self)
            self._left_contents = QFrame(parent=self)
            self._right_contents = QWidget(parent=self)

            self._main_right_layout = layouts.horizontal_layout()
            self._contents_layout = layouts.horizontal_layout()
            self._corner_contents_layout = layouts.horizontal_layout()
            self._title_layout = layouts.horizontal_layout()
            self._title_style = self.TitleStyle.DEFAULT
            self._window_buttons_layout = layouts.horizontal_layout()
            self._split_layout = layouts.horizontal_layout()

            self._logo_button = SpawnerIcon(window=parent, parent=self)
            self._close_button = buttons.BaseButton(theme_updates=False, parent=self)
            self._minimize_button = buttons.BaseButton(theme_updates=False, parent=self)
            self._maximize_button = buttons.BaseButton(theme_updates=False, parent=self)
            self._help_button = buttons.BaseButton(theme_updates=False, parent=self)
            self._title_label = FramelessWindow.TitleBar.TitleLabel(always_show_all=always_show_all, parent=self)

            if not show_title:
                self._title_label.hide()

            self.setup_ui()
            self.setup_signals()

        @property
        def move_enabled(self) -> bool:
            return self._move_enabled

        @move_enabled.setter
        def move_enabled(self, flag: bool):
            self._move_enabled = bool(flag)

        @property
        def logo_button(self) -> SpawnerIcon:
            return self._logo_button

        @property
        def title_label(self) -> TitleLabel:
            return self._title_label

        @property
        def close_button(self) -> buttons.BaseButton:
            return self._close_button

        @property
        def right_contents(self) -> QWidget:
            return self._right_contents

        @property
        def left_contents(self) -> QFrame:
            return self._left_contents

        @property
        def title_layout(self) -> QHBoxLayout:
            return self._title_layout

        @property
        def contents_layout(self) -> QHBoxLayout:
            return self._contents_layout

        @property
        def main_right_layout(self) -> QHBoxLayout:
            return self._main_right_layout

        @property
        def corner_contents_layout(self) -> QHBoxLayout:
            return self._corner_contents_layout

        @property
        def window_buttons_layout(self) -> QHBoxLayout:
            return self._window_buttons_layout

        def setup_ui(self):
            """
            Initializes title UI.
            """

            self.setFixedHeight(dpi.dpi_scale(self._title_bar_height))
            self.setLayout(self._main_layout)

            color = self._theme_preference.FRAMELESS_TITLE_LABEL_COLOR
            self._close_button.set_icon(resources.icon(
                'close', theme='window'), colors=color, size=self._icon_size, color_offset=80)
            self._minimize_button.set_icon(resources.icon(
                'minimize', theme='window'), colors=color, size=self._icon_size, color_offset=80)
            self._maximize_button.set_icon(resources.icon(
                'maximize', theme='window'), colors=color, size=self._icon_size, color_offset=80)
            self._help_button.set_icon(resources.icon('question'), colors=color, size=self._icon_size, color_offset=80)

            # Button Setup
            for button in [self._help_button, self._close_button, self._minimize_button, self._maximize_button]:
                button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
                button.double_click_enabled = False

            # Layout setup
            self._main_right_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 5, 6, 0))
            self._contents_layout.setContentsMargins(0, 0, 0, 0)
            self._corner_contents_layout.setContentsMargins(0, 0, 0, 0)
            self._right_contents.setLayout(self._corner_contents_layout)

            # Window buttons
            self._window_buttons_layout.setContentsMargins(0, 0, 0, 0)
            self._window_buttons_layout.addWidget(self._help_button)
            self._window_buttons_layout.addWidget(self._minimize_button)
            self._window_buttons_layout.addWidget(self._maximize_button)
            self._window_buttons_layout.addWidget(self._close_button)

            # Split Layout
            self._split_layout.addWidget(self._left_contents)
            self._split_layout.addLayout(self._title_layout, 1)
            self._split_layout.addWidget(self._right_contents)

            # Title Layout
            self._left_contents.setLayout(self._contents_layout)
            self._contents_layout.setSpacing(0)
            self._title_layout.addWidget(self._title_label)
            self._title_layout.setSpacing(0)
            self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(2, 2, 2, 6))
            self._title_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
            self._title_label.setMinimumWidth(1)

            # Main Title Layout (Logo and Main Right Layout)
            self._main_layout.setContentsMargins(*dpi.margins_dpi_scale(4, 0, 0, 0))
            self._main_layout.setSpacing(0)
            self._spacing_item = QSpacerItem(8, 8)
            self._spacing_item_2 = QSpacerItem(6, 6)
            self._main_layout.addSpacerItem(self._spacing_item)
            self._main_layout.addWidget(self._logo_button)
            self._main_layout.addSpacerItem(self._spacing_item_2)
            self._main_layout.addLayout(self._main_right_layout)
            self._main_right_layout.addLayout(self._split_layout)
            self._main_right_layout.addLayout(self._window_buttons_layout)
            self._main_right_layout.setAlignment(Qt.AlignVCenter)
            self._window_buttons_layout.setAlignment(Qt.AlignVCenter)
            self._main_right_layout.setStretch(0, 1)

            QTimer.singleShot(0, self.refresh)

            self.set_title_spacing(False)

            if not self._frameless_window.HELP_URL:
                self._help_button.hide()

        @override
        def mousePressEvent(self, event: QMouseEvent) -> None:
            """
            Overrides base mousePressEvent function to cache the drag positions.

            :param QMouseEvent event: Qt mouse event.
            """

            if event.buttons() & Qt.LeftButton:
                self._mouse_press_pos = event.globalPos()
                self.start_move()

            event.ignore()

        def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
            """
            Overrides mouseDoubleClickEvent function to maximize/minimize window (if possible).

            :param QMouseEvent event: Qt mouse event.
            """

            super().mouseDoubleClickEvent(event)
            self.doubleClicked.emit()

        def mouseMoveEvent(self, event: QMouseEvent) -> None:
            """
            Overrides base mouseMoveEvent function to cache the drag positions.

            :param QMouseEvent event: Qt mouse event.
            """

            if self._widget_mouse_pos is None or not self._move_enabled:
                return

            if self._mouse_press_pos is not None:
                moved = event.globalPos() - self._mouse_press_pos
                if moved.manhattanLength() < self._move_threshold:
                    return

                pos = QCursor.pos()
                new_pos = pos
                new_pos.setX(pos.x() - self._widget_mouse_pos.x())
                new_pos.setY(pos.y() - self._widget_mouse_pos.y())
                delta = new_pos - self.window().pos()
                self.moving.emit(new_pos, delta)
                self.window().move(new_pos)

        def mouseReleaseEvent(self, event: QMouseEvent) -> None:
            """
            Overrides base mouseReleaseEvent function to cache the drag positions.

            :param QMouseEvent event: Qt mouse event.
            """

            if self._mouse_press_pos is not None:
                moved = event.globalPos() - self._mouse_press_pos
                if moved.manhattanLength() > self._move_threshold:
                    event.ignore()
                self._mouse_press_pos = None
                self.end_move()

        def start_move(self):
            """
            Starts the movement of the title bar parent window.
            """

            if self._move_enabled:
                self._widget_mouse_pos = self._frameless_window.mapFromGlobal(QCursor.pos())

        def end_move(self):
            """
            Ends the movement of the title bar parent window.
            """

            if self._move_enabled:
                self._widget_mouse_pos = None

        def refresh(self):
            """
            Refreshes title bar.
            """

            QApplication.processEvents()
            self.updateGeometry()
            self.update()

        def set_title_text(self, title: str):
            """
            Sets the title of the title bar.

            :param str title: title
            """

            self._title_label.setText(title.upper())

        def set_title_spacing(self, spacing: bool):
            """
            Set title spacing.

            :param bool spacing: whether spacing should be applied.
            """

            _spacing = consts.Sizes.INDICATOR_WIDTH * 2
            if spacing:
                self._spacing_item.changeSize(_spacing, _spacing)
                self._spacing_item_2.changeSize(_spacing - 2, _spacing - 2)
            else:
                self._spacing_item.changeSize(0, 0)
                self._spacing_item_2.changeSize(0, 0)
                self._split_layout.setSpacing(0)

        def set_title_align(self, align: Qt.AlignmentFlag):
            """
            Sets title align.

            :param Qt.AlignmentFlag align: alignment.
            """

            if align == Qt.AlignCenter:
                self._split_layout.setStretch(1, 0)
            else:
                self._split_layout.setStretch(1, 1)

        def title_style(self) -> str:
            """
            Returns title style.

            :return: title style.
            :rtype: str
            """

            return self._title_style

        def set_title_style(self, style: str):
            """
            Sets the title style.

            :param str style: title style.
            """

            self._title_style = style

            if style == self.TitleStyle.DEFAULT:
                qtutils.set_stylesheet_object_name(self, '')
                qtutils.set_stylesheet_object_name(self._title_label, '')
                self.setFixedHeight(dpi.dpi_scale(self._title_bar_height))
                self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(2, 2, 2, 6))
                # self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 5, 0, 7))
                self._main_right_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 5, 6, 0))
                self._logo_button.setIconSize(QSize(16, 16))
                self._logo_button.setFixedSize(QSize(30, 24))
                self._minimize_button.setFixedSize(QSize(28, 24))
                self._minimize_button.setIconSize(QSize(24, 24))
                self._maximize_button.setFixedSize(QSize(24, 24))
                self._maximize_button.setIconSize(QSize(24, 24))
                self._close_button.setFixedSize(QSize(24, 24))
                self._close_button.setIconSize(QSize(16, 16))
                self._window_buttons_layout.setSpacing(6)
                if self._frameless_window.HELP_URL:
                    self._help_button.show()
                self._window_buttons_layout.setSpacing(dpi.dpi_scale(6))
            elif style == self.TitleStyle.THIN:
                self.setFixedHeight(dpi.dpi_scale(int(self._title_bar_height / 2)))
                # self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 3, 15, 7))
                self._title_layout.setContentsMargins(*dpi.margins_dpi_scale(2, 0, 0, 6))
                self._main_right_layout.setContentsMargins(*dpi.margins_dpi_scale(0, 0, 6, 0))
                self._logo_button.setIconSize(QSize(12, 12))
                self._logo_button.setFixedSize(QSize(14, 16))
                self._minimize_button.setFixedSize(QSize(14, 14))
                self._maximize_button.setFixedSize(QSize(14, 14))
                self._close_button.setFixedSize(QSize(14, 14))
                self._title_label.setFixedHeight(dpi.dpi_scale(16))
                self._window_buttons_layout.setSpacing(dpi.dpi_scale(6))
                self._help_button.hide()
                qtutils.set_stylesheet_object_name(self, 'Minimized')
                qtutils.set_stylesheet_object_name(self._title_label, 'Minimized')
            else:
                logger.error(
                    '{} style does not exists for {}!'.format(style, self._frameless_window.__class__.__name__))

        def set_minimize_button_visible(self, flag: bool):
            """
            Sets whether dragger shows minimize button or not.

            :param bool flag: True to enable minimize; False otherwise.
            """

            self._minimize_button.setVisible(flag)

        def set_maximize_button_visible(self, flag: bool):
            """
            Sets whether dragger shows maximize button or not.

            :param bool flag: True to enable maximize; False otherwise.
            """

            self._maximize_button.setVisible(flag)

        def set_logo_highlight(self, flag: bool):
            """
            Sets whether logo can be highlighted.

            :param bool flag: True to enable icon highlight; False otherwise.
            """

            self._logo_button.set_logo_highlight(flag)

        def toggle_contents(self):
            """
            Shows or hides the additional contents of the title bar.
            """

            if self._contents_layout.count() > 0:
                for i in range(self._contents_layout.count()):
                    widget = self._contents_layout.itemAt(i).widget()
                    widget.show() if widget.isHidden() else widget.hide()

        def close_window(self):
            """
            Closes title bar parent window.
            """

            self._frameless_window.close()

        def open_help(self):
            """
            Opens help URL
            """

            if self._frameless_window.HELP_URL:
                webbrowser.open(self._frameless_window.HELP_URL)

        def setup_signals(self):
            """
            Creates title signals.
            """

            self._close_button.leftClicked.connect(self._on_close_button_clicked)
            self._minimize_button.leftClicked.connect(self._on_minimize_button_clicked)
            self._maximize_button.leftClicked.connect(self._on_maximize_button_clicked)
            self._help_button.leftClicked.connect(self._on_help_button_clicked)

        def _on_close_button_clicked(self):
            """
            Internal callback function that is called when close button is left-clicked by the user.
            """

            self.close_window()

        def _on_maximize_button_clicked(self):
            """
            Internal callback function that is called when maximize button is left-clicked by the user.
            """

            self._frameless_window.maximize()

        def _on_minimize_button_clicked(self):
            """
            Internal callback function that is called when minimize button is left-clicked by the user.
            """

            self._frameless_window.minimize()

        def _on_help_button_clicked(self):
            """
            Internal callback function that is called when help button is left-clicked by the user.
            """

            self.open_help()

    WINDOW_SETTINGS_PATH = 'tp'                # Window settings path (e.g: tp)
    HELP_URL = ''                            # Web URL to use when displaying the help documentation for this window
    MINIMIZED_WIDTH = 390
    _INSTANCES: list[FramelessWindow] = []

    beginClosing = Signal()
    closed = Signal()
    minimized = Signal()

    def __init__(
            self, name: str = '', title: str = '', width: int | None = None, height: int | None = None,
            resizable: bool = True, modal: bool = False, init_pos: Tuple[int, int] | None = None,
            title_bar_class: Type | None = None, overlay: bool = True, always_show_all_title: bool = False,
            on_top: bool = False, save_window_pref: bool = False, minimize_enabled: bool = True,
            minimize_button: bool = False, maximize_button: bool = False, parent: QWidget | None = None):

        super().__init__()

        # FramelessWindow.delete_instances()

        self.__class__._INSTANCES.append(weakref.proxy(self))

        self.setObjectName(name or title)
        width, height = dpi.dpi_scale(width or 0), dpi.dpi_scale(height or 0)

        self._name = name
        self._title = title
        self._on_top = on_top
        self._minimized = False
        self._settings = QSettings(
            QSettings.IniFormat, QSettings.UserScope, self.WINDOW_SETTINGS_PATH, name or self.__class__.__name__)
        self._save_window_pref = save_window_pref
        self._parent_container: DockingContainer | FramelessWindowContainer | None = None
        self._window_resizer: WindowResizer | None = None
        self._minimize_enabled = minimize_enabled
        self._modal = modal
        self._parent = parent
        self._init_width = width
        self._init_height = height
        self._always_show_all_title = always_show_all_title
        self._saved_size = QSize()
        self._filter = FramelessWindow.KeyboardModifierFilter()
        self._init_pos = init_pos

        title_bar_class = title_bar_class or FramelessWindow.TitleBar
        self._title_bar = title_bar_class(always_show_all=always_show_all_title, parent=self)

        # TODO: Keep here to keep backward compatibility. This function will be removed in the future
        self._setup_ui()
        self.set_title(title)
        self._setup_signals()
        self.set_resizable(resizable)
        self._prev_style = self.title_style()

        self._overlay = None
        if overlay:
            self._overlay = FramelessOverlay(
                parent=self, title_bar=self._title_bar, top_left=self._window_resizer.top_left_resizer,
                top_right=self._window_resizer.top_right_resizer, bottom_left=self._window_resizer.bottom_right_resizer,
                bottom_right=self._window_resizer.bottom_right_resizer, resizable=resizable)
            self._overlay.widgetMousePress.connect(self.mousePressEvent)
            self._overlay.widgetMouseMove.connect(self.mouseMoveEvent)
            self._overlay.widgetMouseRelease.connect(self.mouseReleaseEvent)

        if not minimize_button:
            self.set_minimize_button_visible(False)

        if not maximize_button:
            self.set_maximize_button_visible(False)

        self.setup_ui()
        self.setup_widgets()
        self.setup_layouts()
        self.setup_signals()

        self.set_title_style(FramelessWindow.TitleBar.TitleStyle.DEFAULT)

        self.load_settings()

        self._filter.modifierPressed.connect(self.show_overlay)
        self.installEventFilter(self._filter)

    @classmethod
    def frameless_window(cls, widget: QWidget) -> FramelessWindow | None:
        """
        Returns the frameless window based on the given widget.

        :param QWidget widget: widget to get frameless window from.
        :return: found frameless window.
        :rtype: FramelessWindow or None
        """

        while widget is not None:
            if isinstance(widget.parentWidget(), FramelessWindow):
                return widget.parentWidget()
            widget = widget.parentWidget()

        return None

    @classmethod
    def delete_instances(cls):
        for instance in cls._INSTANCES:
            logger.info(f'Deleting {instance}')
            try:
                instance.setParent(None)
                instance.deleteLater()
            except:
                pass
            cls._INSTANCES.remove(instance)
            del instance

    @property
    def title_bar(self) -> TitleBar:
        return self._title_bar

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = value

    @property
    def title(self) -> str:
        return self._title

    @property
    def parent_container(self) -> DockingContainer | FramelessWindowContainer:
        return self._parent_container

    @property
    def title_contents_layout(self) -> QHBoxLayout:
        return self._title_bar.contents_layout

    @property
    def corner_contents_layout(self) -> QHBoxLayout:
        return self._title_bar.corner_contents_layout

    @property
    def docked(self) -> Signal:
        return self._title_bar.logo_button.docked

    @property
    def undocked(self) -> Signal:
        return self._title_bar.logo_button.undocked

    @property
    def windowEvent(self) -> Signal:
        return self._filter.windowEvent

    @property
    def windowResizedFinished(self) -> Signal:
        return self._window_resizer.resizeFinished

    def setup_ui(self):
        """
        Function that can be overriden to add custom widgets and layouts.
        # TODO: This function will be removed in the future. Keep here for backward compatibility for now.
        """

        pass

    def setup_widgets(self):
        """
        Function that can be overriden to add custom widgets.
        """

        pass

    def setup_layouts(self):
        """
        Function that can be overriden to add custom layouts.
        """

        pass

    def setup_signals(self):
        """
        Function that can be overriden to set up widget signals.
        """

        pass

    @override(check_signature=False)
    def show(self, move: QPoint | None = None) -> None:
        """
        Overrides base show function to show parent container.

        :param QPoint or None move: if given, move window to specific location.
        """

        if self._parent_container:
            self._parent_container.show()
        result = super().show()
        if move is not None:
            self.move(move)
        else:
            self._move_to_init_pos()

        return result

    @override
    def hide(self) -> None:
        """
        Overrides base hide function to hide parent container.
        """

        if self._parent_container:
            self._parent_container.hide()
        return super().hide()

    @override(check_signature=False)
    def move(self, *args, **kwargs) -> None:
        """
        Overrides move function to move window and offset the resizers if they are visible.
        """

        arg1 = args[0]
        if isinstance(arg1, QPoint) and self._window_resizer.is_visible():
            arg1.setX(int(arg1.x() - self.resizer_width() * 0.5))
            arg1.setY(int(arg1.y() - self.resizer_height() * 0.5))
        if self._parent_container:
            self._parent_container.move(*args, **kwargs)

    @override
    def close(self) -> bool:
        """
        Overrides close function.
        """

        self.hide()
        self.beginClosing.emit()
        qtutils.process_ui_events()

        self.save_settings()

        result = super().close()

        self.removeEventFilter(self._filter)
        self.closed.emit()
        self._parent_container.close()

        return result

    @override
    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Overrides key press event function.
        """

        if self._overlay and event.modifiers() == Qt.AltModifier:
            self._overlay.show()

        return super().keyPressEvent(event)

    def load_settings(self):
        """
        Load settings located within window settings file path (if it exists).
        """

        position = QPoint(*(self._init_pos or ()))
        init_pos = position or self._settings.value('pos')
        self._init_pos = init_pos

        if self._parent_container:
            # self._parent_container.restoreGeometry(self._settings.value('geometry', self._parent_container.saveGeometry()))
            # self._parent_container.restoreState(self._settings.value('saveState', self._parent_container.saveState()))
            self._parent_container.resize(self._settings.value('size', self._parent_container.size()))
            # if self._settings.value('maximized', self._parent_container.isMaximized()):
            #     self._parent_container.showMaximized()

    def save_settings(self):
        """
        Saves settings into window settings file path.
        """

        if not self.is_docked() and self._parent_container:
            self._settings.setValue('geometry', self._parent_container.saveGeometry())
            self._settings.setValue('saveState', self._parent_container.saveState())
            self._settings.setValue('maximized', self._parent_container.isMaximized())
            if not self._parent_container.isMaximized():
                self._settings.setValue('pos', self._parent_container.pos())
                self._settings.setValue('size', self._parent_container.size())

    def main_layout(self) -> QVBoxLayout | QHBoxLayout | QLayout:
        """
        Returns window main content layouts instance.

        :return: contents layout.
        :rtype: QVBoxLayout or QHBoxLayout or QLayout
        ..note:: if not layout exists, a new one will be created.
        """

        if self._main_contents.layout() is None:
            self._main_contents.setLayout(layouts.vertical_layout())

        return self._main_contents.layout()

    def set_main_layout(self, layout: QVBoxLayout | QHBoxLayout) -> QVBoxLayout | QHBoxLayout | QLayout:
        """
        Sets main window layout.

        :param QVBoxLayout or QHBoxLayout layout: main window contents layout.
        :return: contents layout.
        :rtype: QVBoxLayout or QHBoxLayout or QLayout
        """

        self._main_contents.setLayout(layout)
        return self.main_layout()

    def set_title(self, title: str):
        """
        Sets title text.

        :param str title: title.
        """

        self._title_bar.set_title_text(title)
        self._title = title
        super().setWindowTitle(title)

    def set_resizable(self, flag: bool):
        """
        Sets whether window is resizable.

        :param bool flag: True to make window resizable; False otherwise.
        """

        self._window_resizer.set_enabled(flag)

    def set_on_top(self, flag: bool):
        """
        Sets whether container should stay on top.

        :param bool flag: True to set container on top; False otherwise.
        """

        if not self._parent_container:
            return

        self._parent_container.set_on_top(flag)

    def resizer_height(self) -> int:
        """
        Returns window resizer height.

        :return: resizer height.
        :rtype: int
        """

        return self._window_resizer.resizer_height()

    def resizer_width(self) -> int:
        """
        Returns window resizer width.

        :return: resizer width.
        :rtype: int
        """

        return self._window_resizer.resizer_width()

    def set_default_stylesheet(self):
        """
        Tries to set the default stylesheet for this window.
        """

        try:
            theme_interface = core_interfaces.theme_preference_interface()
            result = theme_interface.stylesheet()
            self.setStyleSheet(result.data)
        except ImportError:
            logger.error('Error while setting default stylesheet ...')

    def center_to_parent(self):
        """
        Centers container to parent.
        """

        qtutils.update_widget_sizes(self._parent_container)
        size = self.rect().size()
        if self._parent:
            widget_center = qtutils.widget_center(self._parent)
            pos = self._parent.pos()
        else:
            widget_center = qtutils.current_screen_geometry().center()
            pos = QPoint(0, 0)

        self._parent_container.move(widget_center + pos - QPoint(int(size.width() / 2), int(size.height() / 3)))

    def is_minimized(self) -> bool:
        """
        Returns whether window is minimized.

        :return: True if window is minimized; False otherwise.
        :rtype: bool
        """

        return self._minimized

    def set_minimize_enabled(self, flag: bool):
        """
        Sets whether window can be minimized.

        :param bool flag: Turn to enable minimize functionality; False otherwise.
        """

        self._minimize_enabled = flag

    def is_movable(self) -> bool:
        """
        Returns whether window is movable.

        :return: True if window is movable; False otherwise.
        :rtype: bool
        """

        return self._title_bar.move_enabled

    def set_movable(self, flag: bool):
        """
        Sets whether window is movable.

        :param bool flag: True to make window movable; False otherwise.
        """

        self._title_bar.move_enabled = flag

    def is_docked(self) -> bool:
        """
        Returns whether window is docked.

        :return: True if window is docked; False otherwise.
        :rtype: bool
        """

        return self._parent_container.is_docking_container() if self._parent_container else False

    def minimize(self):
        """
        Minimizes UI.
        """

        if not self._minimize_enabled:
            return

        self._saved_size = self.window().size()
        self._set_ui_minimized(True)
        qtutils.process_ui_events()
        qtutils.single_shot_timer(lambda: self.window().resize(dpi.dpi_scale(FramelessWindow.MINIMIZED_WIDTH), 0))

    def maximize(self):
        """
        Maximizes UI.
        """

        self._set_ui_minimized(False)
        self.window().resize(self._saved_size)

    def title_style(self) -> str:
        """
        Returns current title style.

        :return: title style.
        :rtype: str
        """

        return self._title_bar.title_style()

    def set_title_style(self, title_style: str):
        """
        Sets title style.

        :param str title_style: title style.
        """

        self._title_bar.set_title_style(title_style)

    def set_minimize_button_visible(self, flag: bool):
        """
        Sets whether minimize button is visible.

        :param bool flag: True to make minimize button visible; False otherwise.
        """

        self._title_bar.set_minimize_button_visible(flag)

    def set_maximize_button_visible(self, flag: bool):
        """
        Sets whether minimize button is visible.

        :param bool flag: True to make maximize button visible; False otherwise.
        """

        self._title_bar.set_maximize_button_visible(flag)

    def set_logo_color(self, color: QColor | Tuple[int, int, int]):
        """
        Sets the color of the window icon.

        :param QColor or Tuple[int, int, int] color: color icon.
        """

        self._title_bar.logo_button.set_icon_color(color)

    def show_overlay(self):
        """
        Shows frameless window overlay.
        """

        if self._overlay:
            self._overlay.show()

    def attach_to_frameless_window(self, save_window_pref: bool = True):
        """
        Attaches this widget to a frameless window.

        :param bool save_window_pref: whether to save window settings.
        :return: frameless window instance.
        :rtype: FramelessWindowContainer
        """

        self._parent = self._parent or dcc.main_window()
        self._parent_container = FramelessWindowContainer(
            width=self._init_width, height=self._init_height, save_window_pref=save_window_pref, on_top=self._on_top,
            parent=self._parent)
        self._parent_container.set_widget(self)
        if self._modal:
            self._parent_container.setWindowModality(Qt.ApplicationModal)
        self._move_to_init_pos() if self._init_pos else self.center_to_parent()

        return self._parent_container

    def resize_window(self, width: int = -1, height: int = -1):
        """
        Resizes window.

        :param int width: window width.
        :param int height: window height.
        """

        width = self.width() if width == -1 else width
        height = self.height() if height == -1 else height
        width += self.resizer_width() * 2
        height += self.resizer_height() * 2

        super().resize(width, height)

    def show_window(self):
        """
        Shows parent container window.
        """

        if self._parent_container:
            self._parent_container.show()

    def _setup_ui(self):
        """
        Internal function that initializes UI.
        """

        self.attach_to_frameless_window(save_window_pref=self._save_window_pref)
        self._minimized = False
        self._frameless_layout = layouts.grid_layout()
        self._setup_frameless_layout()
        self._window_resizer = WindowResizer(install_to_layout=self._frameless_layout, parent=self)

        self.set_default_stylesheet()

    def _setup_signals(self):
        """
        Internal function that initializes window signals.
        """

        self.docked.connect(self._on_docked)
        self.undocked.connect(self._on_undocked)
        self._title_bar.doubleClicked.connect(self._on_title_bar_double_clicked)

        try:
            theme_interface = core_interfaces.theme_preference_interface()
            theme_interface.updated.connect(self._on_update_theme)
        except ImportError:
            pass

    def _setup_frameless_layout(self):
        """
        Internal function that initializes frameless layout
        """

        self.setLayout(self._frameless_layout)
        self._main_contents = FramelessWindowContents(self)
        self._title_bar.set_title_text(self._title)
        self._frameless_layout.setHorizontalSpacing(0)
        self._frameless_layout.setVerticalSpacing(0)
        self._frameless_layout.setContentsMargins(0, 0, 0, 0)
        self._frameless_layout.addWidget(self._title_bar, 1, 1, 1, 1)
        self._frameless_layout.addWidget(self._main_contents, 2, 1, 1, 1)
        self._frameless_layout.setColumnStretch(1, 1)                            # title column
        self._frameless_layout.setColumnStretch(2, 1)                            # main contents row

    def _move_to_init_pos(self):
        """
        Internal function that moves widget to the internal initial position.
        """

        qtutils.update_widget_sizes(self._parent_container)
        self._init_pos = qtutils.contain_widget_in_screen(self, self._init_pos)
        self._parent_container.move(self._init_pos)

    def _set_ui_minimized(self, flag: bool):
        """
        Internal function that minimizes/maximizes UI.

        :param bool flag: True to minimize UI; False to maximize UI.
        """

        self._minimized = flag

        if flag:
            if not self._minimize_enabled:
                return
            self._prev_style = self.title_style()
            self.set_title_style(FramelessWindow.TitleBar.TitleStyle.THIN)
            self._main_contents.hide()
            self._title_bar.left_contents.hide()
            self._title_bar.right_contents.hide()
            self.minimized.emit()
        else:
            self._main_contents.show()
            self.set_title_style(self._prev_style)
            self._title_bar.left_contents.show()
            self._title_bar.right_contents.show()

    def _show_resizers(self):
        """
        Internal function that show resizers.
        """

        self._window_resizer.show()

    def _hide_resizers(self):
        """
        Internal function that hides resizers.
        """

        self._window_resizer.hide()

    def _on_docked(self, container: DockingContainer):
        """
        Internal callback function that is called when window is docked.

        :param DockContainer container: dock container instance.
        """

        if self.is_minimized():
            self._set_ui_minimized(False)

        self.set_movable(False)
        self._hide_resizers()
        self._parent_container = container

    def _on_undocked(self):
        """
        Internal callback function that is called when window is undocked.
        """

        self._show_resizers()
        self.set_movable(True)

    def _on_title_bar_double_clicked(self):
        """
        Internal callback function that is called when title bar is double-clicked by the user.
        """

        self.minimize() if not self.is_minimized() else self.maximize()

    def _on_update_theme(self, event):
        """
        Internal callback function that is called when theme is updated.

        :param ThemeUpdateEvent event: theme event.
        """

        self.setStyleSheet(event.stylesheet)


class FramelessWindowThin(FramelessWindow):
    """
    Frameless window with modified title style
    """

    @override
    def _setup_frameless_layout(self):
        super()._setup_frameless_layout()

        self.set_title_style(FramelessWindow.TitleBar.TitleStyle.THIN)
        self._title_bar.set_title_align(Qt.AlignCenter)


class SpawnerIcon(buttons.IconMenuButton):
    """
    Custom button with a menu that can spawn docked widgets.
    """

    docked = Signal(object)
    undocked = Signal()

    def __init__(self, window: FramelessWindow, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._window = window
        self._docking_container = None                        # type: DockingContainer
        self._start_pos = None                                # type: QPoint
        self._workspace_control = None                        # type: str
        self._workspace_control_name = None                    # type: str
        self._docked = False
        self._spawn_enabled = True
        self._init_dock = False

        self.set_logo_highlight(True)
        self._setup_logo_button()

    @override
    def mousePressEvent(self, e: QMouseEvent) -> None:
        if self._window.is_docked() or e.button() == Qt.RightButton:
            return

        if e.button() == Qt.LeftButton and self._spawn_enabled:
            self._init_dock = True
            self._start_pos = QCursor.pos()

        if dcc.is_maya() and self._tooltip_action:
            self._tooltip_action.setChecked(tooltips.tooltip_state())

    @override
    def mouseMoveEvent(self, e: QMouseEvent) -> None:
        if self._window.is_docked():
            return
        square_length = qtutils.get_squared_length(self._start_pos - QCursor.pos()) if self._start_pos else 0
        if self._init_dock and square_length > 1:
            self._init_dock_container()
            self._init_dock = False
        if self._workspace_control_name is not None:
            self.move_to_mouse()

    @override
    def mouseReleaseEvent(self, e: QMouseEvent) -> None:
        if self._window.is_docked():
            return
        if not self._spawn_enabled or self._init_dock:
            super().mouseReleaseEvent(e)
            return
        if e.button() == Qt.RightButton:
            return
        if not self.is_workspace_floating():
            self.dockedEvent()
        else:
            self.delete_control()

    # TODO: Move this Maya specific window implementation
    def dockedEvent(self, dock_to_main_window=None):
        if not dcc.is_maya():
            return

        frameless = self._window.parent_container
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        width = self._window.width()
        height = self._window.height()
        if dock_to_main_window:
            cmds.workspaceControl(
                self._workspace_control_name, e=True, dtm=dock_to_main_window, initialWidth=width, initialHeight=height)
        else:
            cmds.workspaceControl(self._workspace_control_name, e=True, initialWidth=width, initialHeight=height)
        self._docking_container.set_widget(self._window)
        self.docked.emit(self._docking_container)
        self._arrange_splitters(width)
        self._docking_container = None
        self._docked = True
        frameless.close()

    @override(check_signature=False)
    def update_theme(self, event):
        """
        Overrides base update_theme function to ignore it.

        :param ThemeUpdateEvent event: theme update event.
        :return:
        """

        pass

    def name(self) -> str:
        """
        Returns frameless window name.

        :return: frameless window name.
        :rtype: str

        ..note:: this should match frameless window name.
        """

        return self._window.title or self._window.name or f'Window [{str(uuid.uuid4())[:4]}]'

    def set_logo_highlight(self, flag: bool):
        """
        Sets whether logo can be highlighted.

        :param bool flag: True to enable icon highlight; False otherwise.
        """

        min_size = 0.55 if self._window.isMinimized() else 1
        size = consts.Sizes.TITLE_LOGO_ICON * min_size
        if flag:
            self.set_icon('tpdcc', colors=[None, None], size=size, scaling=[1], color_offset=40)
        else:
            self.set_icon(
                'tpdcc', colors=[None], tint_composition=QPainter.CompositionMode_Plus, size=size, scaling=[1],
                color_offset=40, grayscale=True)

    def move_to_mouse(self):
        """
        Moves window to the mouse location.
        """

        if not self._docking_container:
            return

        self._docking_container.move_to_mouse()

    def is_dock_locked(self) -> bool:
        """
        Returns whether dock functionality is locked.

        :return: True if dock functionality is locked; False otherwise.
        :rtype: bool
        """

        if not dcc.is_maya():
            return False

        return docking.is_dock_locked()

    def is_workspace_floating(self) -> bool:
        """
        Returns whether workspace is floating.

        :return: True if workspace is floating; False otherwise.
        :rtype: bool
        """

        if not dcc.is_maya() or not self._spawn_enabled:
            return False

        return docking.is_workspace_floating(self._workspace_control_name)

    def delete_control(self):
        """
        Deletes workspace control.
        """

        if not dcc.is_maya() or not self._workspace_control_name:
            return

        cmds.deleteUI(self._workspace_control_name)
        self._workspace_control = None
        self._workspace_control_name = None
        self._docking_container = None
        self._docked = False

    def _setup_logo_button(self):
        """
        Internal function that initializes logo button.
        """

        size = consts.Sizes.TITLE_LOGO_ICON
        self.setIconSize(QSize(size, size))
        self.setFixedSize(QSize(size + consts.Sizes().MARGIN / 2, size + consts.Sizes.MARGIN / 2))
        if dcc.is_maya():
            self._tooltip_action = self.addAction('Toggle Tooltips', checkable=True, connect=self._on_toggle_tooltips)
        self.menu_align = Qt.AlignLeft

    def _init_dock_container(self):
        """
        Internal function that initializes dock container for current DCC.
        """

        if not dcc.is_maya():
            return

        self._workspace_control_name, self._workspace_control, self._docking_container = docking.dock_to_container(
            workspace_name=self.name(), workspace_width=self._window.width(), workspace_height=self._window.height(),
            workspace_title=self.name(), size=35)

        self.move_to_mouse()

    def _splitter_ancestor(self, widget: QWidget) -> Tuple[QWidget, QSplitter] | Tuple[None, None]:
        """
        Internal function that returns widgets splitter ancestors.

        :param QWidget widget: widget to get splitter ancestors of.
        :return: tuple of splitter ancestors.
        :rtype: Tuple[QWidget, QSplitter] or Tuple[None, None]
        """

        if widget is None:
            return None, None
        child = widget
        parent = child.parentWidget()
        if parent is None:
            return None, None
        while parent is not None:
            if isinstance(parent, QSplitter) and parent.orientation() == Qt.Horizontal:
                return child, parent
            child = parent
            parent = parent.parentWidget()

        return None, None

    def _arrange_splitters(self, width: int):
        """
        Internal function that fixes splitter sizes, when docked into splitters.

        :param int width: width to set.
        """

        docking_container = self._docking_container
        child, splitter = self._splitter_ancestor(docking_container)
        if child and isinstance(child, QTabWidget):
            return
        if child and splitter:
            pos = splitter.indexOf(child) + 1
            if pos == splitter.count():
                sizes = splitter.sizes()
                sizes[-2] = (sizes[-2] + sizes[-1]) - width
                sizes[-1] = width
                splitter.setSizes(sizes)
            else:
                splitter.moveSplitter(width, pos)

    def _on_toggle_tooltips(self, tagged_action: QAction):
        """
        Internal callback function that is called when Tooltip action is toggled by the user.

        :param QAction tagged_action: toggled action.
        """

        if not dcc.is_maya():
            return

        tooltips.set_tooltip_state(tagged_action.isChecked())
