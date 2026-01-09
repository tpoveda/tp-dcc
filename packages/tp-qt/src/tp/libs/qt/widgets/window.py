"""Window module providing a base window class using native window decorations.

This module contains the Window class, which provides a simplified window
implementation using the native OS window decorations (frame, title bar, etc.).

For DCC-specific functionality (like Maya docking), use the appropriate
DCC-specific window class (e.g., tp.libs.maya.qt.widgets.window.MayaWindow).
"""

from __future__ import annotations

import uuid
import weakref

from loguru import logger
from Qt.QtCore import QPoint, QSettings, Qt, Signal
from Qt.QtGui import QCloseEvent
from Qt.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from tp.dcc import ui
from tp.preferences.interfaces import preferences as core_interfaces

from .. import dpi, uiconsts, utils
from .layouts import HorizontalLayout, VerticalLayout


class Window(QMainWindow):
    """Main window implementation using native window decorations.

    This class provides a window using the native OS window decorations
    (title bar, frame, etc.) with built-in settings persistence and
    common window functionality.
    """

    HELP_URL = ""  # Web URL for help documentation
    _INSTANCES: list[Window] = []

    beginClosing = Signal()
    closed = Signal()
    minimized = Signal()
    docked = Signal(object)
    undocked = Signal()

    def __init__(
        self,
        name: str = "",
        title: str = "",
        width: int | None = None,
        height: int | None = None,
        resizable: bool = True,
        modal: bool = False,
        init_pos: tuple[int, int] | None = None,
        on_top: bool = False,
        save_window_pref: bool = False,
        minimize_enabled: bool = True,
        settings_path: str = "",
        parent: QWidget | None = None,
        **kwargs,
    ) -> None:
        """Initialize a window with the specified properties.

        Args:
            name: The internal name of the window. Defaults to an empty string.
            title: The title of the window. Defaults to an empty string.
            width: The width of the window. Defaults to None.
            height: The height of the window. Defaults to None.
            resizable: Whether the window is resizable. Defaults to True.
            modal: Whether the window is modal. Defaults to False.
            init_pos: Initial position (x, y). Defaults to None.
            on_top: Whether the window should stay on top. Defaults to False.
            save_window_pref: Whether to save window preferences. Defaults to False.
            minimize_enabled: Whether minimization is enabled. Defaults to True.
            settings_path: Path for storing settings. Defaults to an empty string.
            parent: The parent widget. Defaults to None.
        """

        # Get parent from DCC if not provided
        self._parent = parent or ui.FnUi().main_window()
        super().__init__(parent=self._parent)

        # If no name is provided, generate a unique name using the class
        # name and a UUID.
        name = name or title or self.__class__.__name__ + str(uuid.uuid4())

        Window.delete_instances(name or title)

        self.__class__._INSTANCES.append(weakref.proxy(self))

        self.setObjectName(name or title)
        width, height = dpi.dpi_scale(width or 0), dpi.dpi_scale(height or 0)

        self._name = name
        self._title = title
        self._on_top = on_top
        self._minimized = False
        self._settings_path = settings_path or "tp"
        self._settings = QSettings(
            QSettings.IniFormat,
            QSettings.UserScope,
            self._settings_path,
            name or self.__class__.__name__,
        )
        self._save_window_pref = save_window_pref
        self._parent_container = None
        self._minimize_enabled = minimize_enabled
        self._modal = modal
        self._init_width = width
        self._init_height = height
        self._init_pos = init_pos
        self._main_contents: QWidget | None = None
        self._resizable = resizable

        self._setup_ui()
        self.set_title(title)
        self._setup_signals()

        if not resizable:
            self.setFixedSize(self.size())

        self.setup_widgets()
        self.setup_layouts(self.main_layout())
        self.setup_signals()

        # Check if toolbar should be shown after widgets are set up
        self._on_layout_changed()

        self.load_settings()

        # Set window flags
        if on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

        if modal:
            self.setWindowModality(Qt.ApplicationModal)

        # Initialize size
        if width and height:
            self.resize(width, height)
        elif width:
            self.resize(width, self.height())
        elif height:
            self.resize(self.width(), height)

    @classmethod
    def find_window(cls, widget: QWidget) -> Window | None:
        """Find the window containing the given widget.

        Args:
            widget: Widget to get the window from.

        Returns:
            Window or None: The found window, or None if not found.
        """

        while widget is not None:
            if isinstance(widget.parentWidget(), Window):
                return widget.parentWidget()
            if isinstance(widget, Window):
                return widget
            widget = widget.parentWidget()

        return None

    @classmethod
    def delete_instances(cls, name: str | None = None) -> None:
        """Delete window instances.

        Args:
            name: Name of the specific window to delete. If None, all windows
                will be deleted.
        """

        for instance in cls._INSTANCES[:]:
            if name and instance.name != name:
                continue
            logger.info(f"Deleting {instance}")
            try:
                instance.setParent(None)
                instance.deleteLater()
            except Exception:
                pass
            try:
                cls._INSTANCES.remove(instance)
            except ValueError:
                pass
            del instance

    @property
    def name(self) -> str:
        """Get the name of this window instance.

        Returns:
            The window name.
        """

        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """Set the name of this window instance.

        Args:
            value: The new window name.
        """

        self._name = value

    @property
    def title(self) -> str:
        """Get the title of this window instance.

        Returns:
            The window title.
        """

        return self._title

    @property
    def parent_container(self) -> QMainWindow:
        """Get the parent container instance containing this window.

        Returns:
            The parent container (self for base Window class).
        """

        return self._parent_container if self._parent_container else self

    @property
    def title_contents_layout(self) -> QHBoxLayout:
        """Get the layout for the window title contents.

        Returns:
            The title contents layout (toolbar area for widget placement).
        """

        return self._title_contents_layout

    @property
    def corner_contents_layout(self) -> QHBoxLayout:
        """Get the layout for the window corner contents.

        Returns:
            The corner contents layout (toolbar area for widget placement).
        """

        return self._corner_contents_layout

    def show_toolbar(self, flag: bool = True) -> None:
        """Show or hide the toolbar area.

        The toolbar area contains the title_contents_layout and
        corner_contents_layout. It is hidden by default but shown when
        widgets are added to either layout.

        Args:
            flag: True to show the toolbar, False to hide it.
        """

        self._toolbar_widget.setVisible(flag)

    def setup_widgets(self) -> None:
        """Set up custom widgets for the window.

        This method can be overridden in subclasses to add custom widgets
        to the window layout.
        """

        pass

    def setup_layouts(
        self, main_layout: QVBoxLayout | QHBoxLayout | QGridLayout
    ):
        """Set up custom layouts for the window.

        This method can be overridden in subclasses to customize the
        window layout.

        Args:
            main_layout: Main layout to add custom layouts to.
        """

        pass

    def setup_signals(self) -> None:
        """Set up widget signals.

        This method can be overridden in subclasses to set up custom signal
        connections between widgets.
        """

        pass

    def show(self, move: QPoint | None = None) -> None:
        """Show the window.

        Args:
            move: If provided, moves the window to the specified location.

        Returns:
            None: Result from the parent show method.
        """

        result = super().show()
        if move is not None:
            self.move(move)
        elif self._init_pos:
            self._move_to_init_pos()
        return result

    def closeEvent(self, event: QCloseEvent) -> None:
        """Override closeEvent to emit signals and save settings.

        Args:
            event: The close event.
        """

        self.beginClosing.emit()
        QApplication.processEvents()
        self.save_settings()
        super().closeEvent(event)
        self.closed.emit()

    def load_settings(self) -> None:
        """Load settings located within the window settings file
        path (if it exists).
        """

        position = QPoint(*(self._init_pos or ()))
        init_pos = position or self._settings.value("pos")
        self._init_pos = init_pos

        if not self.is_docked():
            self.restoreGeometry(
                self._settings.value("geometry", self.saveGeometry())
            )
            self.restoreState(
                self._settings.value("saveState", self.saveState())
            )

            if self._settings.value(
                "maximized", self.isMaximized(), type=bool
            ):
                self.showMaximized()
            else:
                size = self._settings.value("size")
                if size:
                    self.resize(size)

    def save_settings(self) -> None:
        """Saves settings into the window settings file path."""

        if not self.is_docked():
            self._settings.setValue("geometry", self.saveGeometry())
            self._settings.setValue("saveState", self.saveState())
            self._settings.setValue("maximized", self.isMaximized())
            if not self.isMaximized():
                self._settings.setValue("pos", self.pos())
                self._settings.setValue("size", self.size())

    def main_layout(self) -> QVBoxLayout | QHBoxLayout | QGridLayout | QLayout:
        """Returns window main content layouts instance.

        Returns:
            contents layout. If no layout exists, a new one will be created.
        """

        if self._main_contents.layout() is None:
            main_layout = self._main_layout()
            self._main_contents.setLayout(main_layout)

        return self._main_contents.layout()

    def set_title(self, title: str):
        """Sets title text.

        Args:
            title: The window title.
        """

        self._title = title
        self.setWindowTitle(title)

    def set_resizable(self, flag: bool):
        """Sets whether window is resizable.

        Args:
            flag: True to make window resizable; False otherwise.
        """

        self._resizable = flag
        if not flag:
            self.setFixedSize(self.size())
        else:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)

    def set_on_top(self, flag: bool):
        """Set whether the window should stay on top of other windows.

        Args:
            flag: True to set window on top; False otherwise.
        """

        if flag:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
        self.show()

    def apply_stylesheet(self, stylesheet: str | None = None):
        """Apply a given stylesheet to the object. If no stylesheet is
        provided, it applies the default stylesheet.

        Args:
            stylesheet: The stylesheet string to be applied. If None, the
                default stylesheet will be used.
        """

        if stylesheet:
            self.setStyleSheet(stylesheet)
        else:
            self.set_default_stylesheet()

    def set_default_stylesheet(self):
        """Tries to set the default stylesheet for this window."""

        try:
            theme_interface = core_interfaces.theme_interface()
            stylesheet = theme_interface.stylesheet()
            self.setStyleSheet(stylesheet)
        except ImportError:
            logger.error("Error while setting default stylesheet ...")

    def center_to_parent(self):
        """Centers window to parent."""

        utils.update_widget_sizes(self)
        size = self.rect().size()
        if self._parent:
            widget_center = utils.widget_center(self._parent)
            pos = self._parent.pos()
        else:
            widget_center = utils.current_screen_geometry().center()
            pos = QPoint(0, 0)

        self.move(
            widget_center
            + pos
            - QPoint(int(size.width() / 2), int(size.height() / 3))
        )

    def is_minimized(self) -> bool:
        """Returns whether window is minimized.

        Returns:
            True if window is minimized; False otherwise.
        """

        return self._minimized or super().isMinimized()

    def set_minimize_enabled(self, flag: bool):
        """Sets whether window can be minimized.

        Args:
            flag: True to enable minimize functionality; False otherwise.
        """

        self._minimize_enabled = flag

    def is_docked(self) -> bool:
        """Returns whether window is docked.

        Returns:
            True if window is docked; False otherwise.
        """

        return False  # Base Window class doesn't support docking

    def minimize(self):
        """Minimizes UI."""

        if not self._minimize_enabled:
            return

        self._minimized = True
        self.showMinimized()
        self.minimized.emit()

    def maximize(self):
        """Maximizes UI."""

        self._minimized = False
        self.showNormal()

    def resize_window(self, width: int = -1, height: int = -1):
        """Resizes window.

        Args:
            width: Window width (-1 to keep current).
            height: Window height (-1 to keep current).
        """

        width = self.width() if width == -1 else width
        height = self.height() if height == -1 else height
        self.resize(width, height)

    def show_window(self):
        """Shows window."""

        self.show()

    def _main_layout(
        self,
    ) -> QVBoxLayout | QHBoxLayout | QGridLayout | QLayout:
        """Internal function that returns window main content layout instance.
        It can be overridden to return a custom main layout.

        Returns:
            Main layout instance.
        """

        main_layout = VerticalLayout()
        main_layout.setSpacing(uiconsts.SPACING)
        main_layout.setContentsMargins(
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
            uiconsts.WINDOW_SIDE_PADDING,
            uiconsts.WINDOW_BOTTOM_PADDING,
        )

        return main_layout

    def _setup_ui(self):
        """Internal function that initializes UI."""

        self._minimized = False

        # Create a central widget with a vertical layout
        central_widget = QWidget(self)
        central_layout = VerticalLayout()
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(0)
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        # Create a toolbar-like area for title_contents_layout and
        # corner_contents_layout
        self._toolbar_widget = QWidget(self)
        self._toolbar_layout = HorizontalLayout()
        self._toolbar_layout.setContentsMargins(
            uiconsts.WINDOW_SIDE_PADDING, 4, uiconsts.WINDOW_SIDE_PADDING, 4
        )
        self._toolbar_layout.setSpacing(4)
        self._toolbar_widget.setLayout(self._toolbar_layout)

        self._title_contents_layout = HorizontalLayout()
        self._title_contents_layout.setContentsMargins(0, 0, 0, 0)
        self._corner_contents_layout = HorizontalLayout()
        self._corner_contents_layout.setContentsMargins(0, 0, 0, 0)

        self._toolbar_layout.addLayout(self._title_contents_layout, 1)
        self._toolbar_layout.addLayout(self._corner_contents_layout)

        central_layout.addWidget(self._toolbar_widget)
        self._toolbar_widget.hide()  # Hidden by default

        # Main contents area
        self._main_contents = QWidget(self)
        central_layout.addWidget(self._main_contents, 1)

        self.apply_stylesheet()

    def _setup_signals(self):
        """Internal function that initializes window signals."""

        self.docked.connect(self._on_docked)
        self.undocked.connect(self._on_undocked)

    def _move_to_init_pos(self):
        """Internal function that moves widget to the initial position."""

        utils.update_widget_sizes(self)
        self._init_pos = utils.contain_widget_in_screen(self, self._init_pos)
        self.move(self._init_pos)

    def _on_layout_changed(self) -> None:
        """Internal callback that shows toolbar if widgets were added to it."""

        has_contents = (
            self._title_contents_layout.count() > 0
            or self._corner_contents_layout.count() > 0
        )
        if has_contents:
            self.show_toolbar(True)

    def _on_docked(self, container):
        """Internal callback function that is called when window is docked.

        Args:
            container: Dock container instance.
        """

        self._parent_container = container

    def _on_undocked(self):
        """Internal callback function that is called when window is undocked."""

        self._parent_container = None


# Backward compatibility aliases
FramelessWindow = Window
FramelessWindowThin = Window
