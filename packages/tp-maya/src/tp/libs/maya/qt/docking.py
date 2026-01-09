"""Maya-specific docking functionality for Qt windows.

This module provides docking support for Qt windows within Maya's workspace
control system. It allows windows to be docked, undocked, and integrated
with Maya's UI layout system.
"""

from __future__ import annotations

import uuid

from loguru import logger
from Qt.QtCore import QEvent, QPoint, QSize, Qt, Signal
from Qt.QtGui import QCursor, QPainter
from Qt.QtWidgets import (
    QMainWindow,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QToolButton,
    QWidget,
)

from maya import OpenMayaUI, cmds
from maya.app.general import mayaMixin
from tp.dcc import ui
from tp.libs.maya.cmds.ui import docking as maya_docking
from tp.libs.qt import dpi, icons, uiconsts, utils
from tp.libs.qt.icon import colorize_icon
from tp.libs.qt.widgets.buttons import IconMenuButton
from tp.libs.qt.widgets.layouts import VerticalLayout


class DockingContainer(mayaMixin.MayaQWidgetDockableMixin, QWidget):
    """Custom widget container that can be docked within Maya.

    This container allows widgets to be docked within Maya's workspace control
    system, providing integration with the host application's UI system.
    """

    def __init__(
        self,
        parent: QMainWindow | None = None,
        workspace_control_name: str | None = None,
        show_dock_tabs: bool = True,
        *args,
        **kwargs,
    ) -> None:
        """Initialize a docking container widget.

        Args:
            parent: The parent window for this container.
            workspace_control_name: Name of the workspace control in Maya.
            show_dock_tabs: Whether to show dock tabs in the UI.
            *args: Additional positional arguments for parent classes.
            **kwargs: Additional keyword arguments for parent classes.
        """
        super().__init__(parent=parent, *args, **kwargs)

        self._main_widget: QWidget | None = None
        self._orig_widget_size: QSize | None = None
        self._win: QWidget | None = None
        self._prev_floating = True
        self._detaching = False
        self._show_dock_tabs = show_dock_tabs
        self._workspace_control = parent
        self._workspace_control_name = workspace_control_name
        self._detach_counter = 0
        self._logo_icon = QToolButton(parent=self)
        self._container_size = self.size()

        self._setup_ui()

    def enterEvent(self, event: QEvent) -> None:
        """Overrides base QWidget enterEvent function.

        Args:
            event: Qt enter event.
        """

        if self._detaching:
            self.undock()

    def resizeEvent(self, event) -> None:
        """Overrides base QWidget resizeEvent function.

        Args:
            event: Qt resize event.
        """

        if not self._detaching and not self.isFloating():
            self._container_size = self.size()

        return super().resizeEvent(event)

    def showEvent(self, event) -> None:
        """Overrides base QWidget showEvent function.

        Args:
            event: Qt show event.
        """

        floating = self.isFloating()
        if not floating:
            self._logo_icon.hide()

        if not self._prev_floating and floating:
            self._detaching = True
            self.layout().setContentsMargins(0, 0, 0, 0)
        else:
            if cmds.workspaceControl(
                self._workspace_control_name, horizontal=True, query=True
            ):
                self.layout().setContentsMargins(8, 0, 0, 0)
            else:
                self.layout().setContentsMargins(0, 8, 0, 0)

        self._prev_floating = floating

    def moveEvent(self, event) -> None:
        """Overrides base QWidget moveEvent function.

        Args:
            event: Qt move event.
        """

        if not self._detaching:
            return

        # Use the detach counter to workaround issue where detaching would
        # prematurely run the undock command.
        self._detach_counter += 1
        new_size = QSize(
            self._container_size.width(), self._orig_widget_size.height()
        )
        self.setFixedSize(new_size)

        # Check the detach event twice before undocking because sometimes
        # when you drag off the window does not stay on the mouse.
        if self._detach_counter == 2:
            self.undock()

    def set_widget(self, widget: QWidget) -> None:
        """Sets the container widget.

        Args:
            widget: Window widget to set as the container's content.
        """

        self._main_widget = widget
        self._orig_widget_size = QSize(self._main_widget.size())
        self.layout().addWidget(widget)
        self.setObjectName(widget.objectName())
        self.setMinimumWidth(0)
        self.setMinimumHeight(0)

    def move_to_mouse(self) -> None:
        """Moves current dock widget to the current mouse cursor position.

        Positions the dock widget at the current mouse position with appropriate
        offsets to ensure good visual placement.
        """

        pos = QCursor.pos()
        window = self._win
        if self._win == ui.FnUi().main_window() and self._win is not None:
            logger.error(
                f"{self._workspace_control_name}: Found window instead of DockingContainer!"
            )
            return
        offset = utils.window_offset(window)
        half = utils.widget_center(window)
        pos += offset - half
        window.move(pos)
        window.setWindowOpacity(0.8)

    def undock(self) -> None:
        """Undocks container widget.

        Detaches the container from its docked position and converts it to a
        floating window.
        """

        self._detach_counter = 0
        self._detaching = False

        if not self.isFloating():
            return

        # Show the main widget as a standalone window
        pos = self.mapToGlobal(QPoint())
        width = self._container_size.width()
        self._main_widget.show()
        self._main_widget.setGeometry(
            pos.x(), pos.y(), width, self._orig_widget_size.height()
        )

        # Try to clean up the spawner icon if it exists
        if hasattr(self._main_widget, "_spawner_icon"):
            self._main_widget._spawner_icon.delete_control()

        # Emit undocked signal if the widget has one
        if hasattr(self._main_widget, "undocked"):
            self._main_widget.undocked.emit()

        self._workspace_control = None

    def delete_control(self) -> None:
        """Deletes workspace control."""

        ui.FnUi().delete_ui(self._workspace_control_name)

    def _setup_ui(self) -> None:
        """Internal function that initializes docking widget UI.

        Sets up the logo icon and layout for the docking container.
        """

        size = 24
        ui_layout = VerticalLayout()
        ui_layout.setContentsMargins(0, 0, 0, 0)
        ui_layout.addWidget(self._logo_icon)
        self.setLayout(ui_layout)
        self._logo_icon.setIcon(colorize_icon(icons.icon("tpdcc"), size=size))
        self._logo_icon.setIconSize(dpi.size_by_dpi(QSize(size, size)))
        self._logo_icon.clicked.connect(self.close)
        self._win = self.window()


class SpawnerIcon(IconMenuButton):
    """Custom button with a menu that can spawn docked widgets in Maya."""

    docked = Signal(object)
    undocked = Signal()

    def __init__(
        self,
        window: QWidget,
        show_dock_tabs: bool = True,
        parent: QWidget | None = None,
    ):
        """Custom button with a menu that can spawn docked widgets.

        Args:
            window: The window instance associated with the button.
            show_dock_tabs: Whether to show dock tabs. Default is True.
            parent: The parent widget, if any. Default is None.
        """

        super().__init__(parent=parent)

        self._window = window
        self._show_dock_tabs = show_dock_tabs
        self._docking_container: DockingContainer | None = None
        self._pressed_pos: QPoint | None = None
        self._workspace_control: QMainWindow | None = None
        self._workspace_control_name: str | None = None
        self._docked = False
        self._spawn_enabled = True
        self._init_dock = False

        self.set_logo_highlight(True)
        self._setup_logo_button()
        self.hide()  # Hidden by default

    def mousePressEvent(self, event) -> None:
        """Handle the mouse press event for the SpawnerIcon.

        Args:
            event: The QMouseEvent object.
        """

        if self._is_window_docked() or event.button() == Qt.RightButton:
            return

        if event.button() == Qt.LeftButton and self._spawn_enabled:
            self._init_dock = True
            self._pressed_pos = QCursor.pos()

    def mouseMoveEvent(self, event) -> None:
        """Handle the mouse move event for the SpawnerIcon.

        Args:
            event: The QMouseEvent object.
        """

        if self._is_window_docked():
            return
        square_length = 0

        if self._pressed_pos:
            point = self._pressed_pos - QCursor.pos()
            square_length = point.dotProduct(point, point)
        if self._init_dock and square_length > 1:
            self._init_dock_container()
            self._init_dock = False
        if self._workspace_control_name:
            self.move_to_mouse()

    def mouseReleaseEvent(self, event) -> None:
        """Handle the mouse release event for the SpawnerIcon.

        Args:
            event: The QMouseEvent object.
        """

        if self._is_window_docked():
            return
        if not self._spawn_enabled or self._init_dock:
            super().mouseReleaseEvent(event)
            return
        if event.button() == Qt.RightButton:
            return

        if not self.is_workspace_floating():
            self._handle_docked_event()
        else:
            self.delete_control()

    def _is_window_docked(self) -> bool:
        """Check if the window is currently docked.

        Returns:
            True if docked, False otherwise.
        """

        if hasattr(self._window, "is_docked"):
            return self._window.is_docked()
        return False

    def _handle_docked_event(self):
        """Handle docking event for Maya."""

        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Set workspace control width and height.
        width = self._window.width()
        height = self._window.height()
        cmds.workspaceControl(
            self._workspace_control_name,
            edit=True,
            initialWidth=width,
            initialHeight=height,
        )
        # Move the window to the docking container.
        self._docking_container.set_widget(self._window)
        self.docked.emit(self._docking_container)

        # Emit docked signal on window if it has one
        if hasattr(self._window, "docked"):
            self._window.docked.emit(self._docking_container)

        self._arrange_splitters(width)
        self._docking_container = None
        self._docked = True

    def name(self) -> str:
        """Returns window name.

        Returns:
            Window name.
        """

        title = getattr(self._window, "title", None)
        name = getattr(self._window, "name", None)
        return title or name or f"Window [{str(uuid.uuid4())[:4]}]"

    def set_logo_highlight(self, flag: bool):
        """Sets whether logo can be highlighted.

        Args:
            flag: True to enable icon highlight; False otherwise.
        """

        min_size = 0.55 if self._window.isMinimized() else 1
        size = uiconsts.Sizes.TitleLogoIcon * min_size
        logo_icon = icons.icon("tpdcc")

        if flag:
            self.set_icon(
                logo_icon,
                colors=[None, None],
                size=size,
                scaling=[1],
                color_offset=40,
            )
        else:
            self.set_icon(
                logo_icon,
                colors=[None],
                tint_composition=QPainter.CompositionMode_Plus,
                size=size,
                scaling=[1],
                color_offset=40,
                grayscale=True,
            )

    def move_to_mouse(self):
        """Moves window to the mouse location."""

        if not self._docking_container:
            return

        self._docking_container.move_to_mouse()

    @staticmethod
    def is_dock_locked() -> bool:
        """Returns whether dock functionality is locked.

        Returns:
            True if dock functionality is locked; False otherwise.
        """

        return maya_docking.is_dock_locked()

    def is_workspace_floating(self) -> bool:
        """Returns whether workspace is floating.

        Returns:
            True if workspace is floating; False otherwise.
        """

        return (
            False
            if not self._spawn_enabled
            else maya_docking.is_workspace_floating(
                self._workspace_control_name
            )
        )

    def delete_control(self):
        """Deletes the workspace control.

        Removes the workspace control from Maya's interface.
        """

        if not self._workspace_control_name:
            return

        cmds.deleteUI(self._workspace_control_name)
        self._workspace_control = None
        self._workspace_control_name = None
        self._docking_container = None
        self._docked = False

    @staticmethod
    def _update_layout_direction():
        """Internal method for workspace control actLikeMayaUIElement."""

        pass

    def _setup_logo_button(self):
        """Initialize the logo button."""

        size = uiconsts.Sizes.TitleLogoIcon
        self.setIconSize(QSize(size, size))
        self.setFixedSize(
            QSize(
                int(size + uiconsts.Sizes.Margin / 2),
                int(size + uiconsts.Sizes.Margin / 2),
            )
        )
        self.menu_align = Qt.AlignLeft

    def _init_dock_container(self):
        """Internal function that initializes dock container for Maya."""

        size = 35

        locked = self.is_dock_locked()
        if locked:
            logger.warning(
                "Maya docking is locked. You can unlock it on the top right of Maya"
            )
            return None

        kwargs = {
            "loadImmediately": True,
            "label": self.name(),
            "retain": False,
            "initialWidth": self._window.width(),
            "initialHeight": self._window.height(),
            "vis": True,
            "actLikeMayaUIElement": False,
            "layoutDirectionCallback": "_update_layout_direction",
        }
        self._workspace_control_name = cmds.workspaceControl(
            f"{self.name()} [{str(uuid.uuid4())[:4]}]", **kwargs
        )
        ptr = OpenMayaUI.MQtUtil.getCurrentParent()
        self._workspace_control = utils.wrapinstance(ptr, QMainWindow)

        w = self._workspace_control.window()
        w.setFixedSize(dpi.size_by_dpi(QSize(size, size)))
        w.layout().setContentsMargins(0, 0, 0, 0)
        w.setWindowOpacity(0)
        window_flags = w.windowFlags() | Qt.FramelessWindowHint
        w.setWindowFlags(window_flags)
        cmds.workspaceControl(
            self._workspace_control_name,
            resizeWidth=size,
            resizeHeight=size,
            e=1,
        )
        w.show()
        w.setWindowOpacity(1)
        self._docking_container = DockingContainer(
            self._workspace_control,
            self._workspace_control_name,
            self._show_dock_tabs,
        )
        # Attach it to the workspaceControl.
        widget_ptr = OpenMayaUI.MQtUtil.findControl(
            self._docking_container.objectName()
        )
        OpenMayaUI.MQtUtil.addWidgetToMayaLayout(int(widget_ptr), int(ptr))
        self.move_to_mouse()

    @staticmethod
    def _splitter_ancestor(
        widget: QWidget,
    ) -> tuple[QWidget, QWidget] | tuple[None, None]:
        """Internal function that returns widgets splitter ancestors.

        Args:
            widget: Widget to get splitter ancestors of.

        Returns:
            Tuple of splitter ancestors.
        """

        if widget is None:
            return None, None
        child = widget
        parent = child.parentWidget()
        if parent is None:
            return None, None
        while parent is not None:
            if (
                isinstance(parent, QSplitter)
                and parent.orientation() == Qt.Horizontal
            ):
                return child, parent
            child = parent
            parent = parent.parentWidget()

        return None, None

    def _arrange_splitters(self, width: int):
        """Internal function that fixes splitter sizes when docked into splitters.

        Args:
            width: Width to set.
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
