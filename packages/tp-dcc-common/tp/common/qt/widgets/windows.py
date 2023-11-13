from __future__ import annotations

import os
import sys
import json
import uuid
import tempfile
from collections import defaultdict
from multiprocessing import Process

from overrides import override
from Qt.QtCore import Signal, QEvent, QPoint, QSize, QRect
from Qt.QtWidgets import (
    QApplication, QWidget, QDialog, QFrame, QPushButton, QLabel, QMainWindow, QCheckBox, QMessageBox, QVBoxLayout,
    QHBoxLayout
)

from tp.core import dcc
from tp.common.resources import palette
from tp.common.python import path, decorators, win32
from tp.common.qt import consts, dpi, qtutils
from tp.common.qt.widgets import layouts


class AbstractWindow(QMainWindow):
    """
    Base class for all DCC Qt based windows.

    Each window must be provided with a unique "ID" attribute to enable following features:
        - Saving and loading of its location.
        - Automatic closing of previous windows, if a new one is launched.
    Also, "Name" attribute will define the window title.

    Dockable windows are supported and its functionality must be implemented for each DCC.
    """

    clearedInstance = Signal()
    windowReady = Signal()

    _WINDOW_INSTANCES = dict()

    def __init__(self, parent: QWidget | None = None, **kwargs):
        super().__init__(parent, **kwargs)

        self._enable_state = True
        self._child_window = False
        self._window_closed = False
        self._window_loaded = False
        self._dockable = getattr(self, 'Dockable', False)
        self._was_docked = None
        self._initial_pos_override: tuple[int, int] | None = None
        self._window_palette: str | None = None
        self._signals = defaultdict(list)
        self._signals_cache = defaultdict(list)

        self._standalone = False
        self._batch = False
        self._maya = False
        self._nuke = False
        self._houdini = False
        self._max = False
        self._fusion = False
        self._blender = False
        self._unreal = False
        self._painter = False
        self._designer = False

        self._force_disable_saving = not hasattr(self, 'ID')
        if self._force_disable_saving:
            self.ID = str(uuid.uuid4())

        self.setWindowTitle(getattr(self, 'Name', 'New Window'))

        self._window_data_path = self.window_settings_path(self.ID)
        temp_folder = path.dirname(self._window_data_path)
        if not path.is_dir(temp_folder):
            os.makedirs(temp_folder)
        self._window_settings = self.window_settings(self.ID, settings_path=self._window_data_path)

        AbstractWindow._WINDOW_INSTANCES[self.ID] = {
            'window': self,
            'callback': dict()
        }

        self.windowReady.connect(lambda: setattr(self, '_window_loaded', True))

    @classmethod
    def window_settings_path(cls, window_id: str) -> str:
        """
        Returns the path where window settings are stored.

        :param str window_id: ID of the window we want to save settings path.
        :return: window settings absolute path.
        :rtype: str
        """

        return path.join_path(tempfile.gettempdir(), f'tp.dcc.window.{window_id}.json')

    @classmethod
    def window_settings(cls, window_id: str, settings_path: str | None = None):
        """
        Opens the window settings file and returns its contents.

        :param str window_id: ID of the window we want to open settings for.
        :param str or None settings_path: optional path where window settings are located. If not given, settings path
            will be automatically retrieved based on given window_id.
        :return: window settings.
        :rtype: dict
        """

        settings_path = settings_path or cls.window_settings_path(window_id)
        try:
            with open(settings_path, 'r') as f:
                return json.loads(f.read())
        except (IOError, ValueError):
            return dict()

    @classmethod
    def save_window_settings(cls, window_id: str, data: dict, settings_path: str | None) -> bool:
        """
        Save window settings.

        :param str window_id: ID of the window we want to save settings for.
        :param dict data: settings dictionary.
        :param str or None settings_path: optional path where window settings are located. If not given, settings path
            will be automatically retrieved based on given window_id.
        :return: True if save window settings operation was successful; False otherwise.
        :rtype: bool
        """

        settings_path = settings_path or cls.window_settings_path(window_id)
        try:
            with open(settings_path, 'w') as f:
                f.write(json.dumps(data, indent=2))
        except IOError:
            return False

        return True

    @classmethod
    def clear_window_instance(cls, window_id: str) -> dict:
        """
        Closes the lats class instance that matches its ID with the given one.

        :param str window_id: ID of the window to close.
        :return: closed window instance dictionary.
        :rtype: dict
        """

        window_to_close = cls._WINDOW_INSTANCES.pop(window_id, None)
        if window_to_close is not None and not window_to_close['window'].is_dialog():
            try:
                window_to_close['window'].clearedInstance.emit()
            except RuntimeError:
                pass

        return window_to_close

    @classmethod
    def clear_window_instances(cls):
        """
        Internal function that closes down every loaded window.
        """

        for window_id in tuple(cls._WINDOW_INSTANCES):
            cls.clear_window_instance(window_id)

    @decorators.HybridMethod
    @override(check_signature=False)
    def show(cls, self, *args, **kwargs) -> AbstractWindow:
        """
        Shows the window and loads its position.
        """

        # Window has been already initialized
        if self is not cls:
            return super(AbstractWindow, self).show()

        # Close existing windows and open a new one
        try:
            cls.clear_window_instance(cls.ID)
        except AttributeError:
            pass
        new_window = cls(*args, **kwargs)
        super(AbstractWindow, new_window).show()
        new_window.load_window_position()
        dcc.deferred_function(new_window.windowReady.emit)

        return new_window

    @override(check_signature=False)
    def closeEvent(self, event: QEvent):
        """
        Closes the window and marks it as closed.

        :param QEvent event: Qt event.
        """

        self._window_closed = True
        self.clear_window_instance(self.ID)
        if self.is_dialog():
            return self.parent().close()

        return super().closeEvent(event)

    @override(check_signature=False)
    def move(self, x: int, y: int | None = None) -> None:
        if self.is_instance():
            return
        if isinstance(x, QPoint):
            y = x.y()
            x = x.x()
        if self.dockable():
            return self._parent_override().move(x, y)
        elif self.is_dialog():
            return self.parent().move(x, y)

        return super(AbstractWindow, self).move(x, y)

    @override(check_signature=False)
    def resize(self, w: int, h: int | None = None) -> None:
        if self.is_instance():
            return
        if isinstance(w, QSize):
            h = w.height()
            w = w.width()
        if self.dockable():
            return self._parent_override().resize(w, h)
        elif self.is_dialog():
            return self.parent().resize(w, h)

        return super(AbstractWindow, self).resize(w, h)

    @override
    def geometry(self) -> QRect:
        if not self.is_instance():
            if self.dockable():
                return self._parent_override().geometry()
            elif self.is_dialog():
                return self.parent().geometry()
        return super(AbstractWindow, self).geometry()

    @override
    def frameGeometry(self) -> QRect:
        if not self.is_instance():
            if self.dockable():
                return self._parent_override().frameGeometry()
            elif self.is_dialog():
                return self.parent().frameGeometry()
        return super(AbstractWindow, self).frameGeometry()

    @override
    def rect(self) -> QRect:
        if not self.is_instance():
            if self.dockable():
                return self._parent_override().rect()
            elif self.is_dialog():
                return self.parent().rect()
        return super(AbstractWindow, self).rect()

    @override
    def width(self) -> int:
        if not self.is_instance():
            if self.dockable():
                return self._parent_override().width()
            elif self.is_dialog():
                return self.parent().width()
        return super(AbstractWindow, self).width()

    @override
    def height(self) -> int:
        if not self.is_instance():
            if self.dockable():
                return self._parent_override().height()
            elif self.is_dialog():
                return self.parent().height()
        return super(AbstractWindow, self).height()

    @override
    def x(self):
        if not self.is_instance():
            if self.dockable():
                return self._parent_override().x()
            elif self.is_dialog():
                return self.parent().x()
        return super(AbstractWindow, self).x()

    @override
    def y(self):
        if not self.is_instance():
            if self.dockable():
                return self._parent_override().y()
            elif self.is_dialog():
                return self.parent().y()
        return super(AbstractWindow, self).y()

    @override
    def setMinimumWidth(self, minw: int) -> None:
        if self.is_dialog():
            return self.parent().setMinimumWidth(minw)
        return super(AbstractWindow, self).setMinimumWidth(minw)

    @override
    def setFixedWidth(self, w: int) -> None:
        if self.is_dialog():
            return self.parent().setFixedWidth(w)
        return super(AbstractWindow, self).setFixedWidth(w)

    @override
    def setMaximumWidth(self, maxw: int) -> None:
        if self.is_dialog():
            return self.parent().setMaximumWidth(maxw)
        return super(AbstractWindow, self).setMaximumWidth(maxw)

    @override
    def setMinimumHeight(self, minh: int) -> None:
        if self.is_dialog():
            return self.parent().setMinimumHeight(minh)
        return super(AbstractWindow, self).setMinimumHeight(minh)

    @override
    def setFixedHeight(self, h: int) -> None:
        if self.is_dialog():
            return self.parent().setFixedHeight(h)
        return super(AbstractWindow, self).setFixedHeight(h)

    @override
    def setMaximumHeight(self, maxh: int) -> None:
        if self.is_dialog():
            return self.parent().setMaximumHeight(maxh)
        return super(AbstractWindow, self).setMaximumHeight(maxh)

    @override(check_signature=False)
    def setMinimumSize(self, minw: int, minh: int) -> None:
        if self.is_dialog():
            return self.parent().setMinimumSize(minw, minh)
        return super(AbstractWindow, self).setMinimumSize(minw, minh)

    @override(check_signature=False)
    def setFixedSize(self, w: int, h: int) -> None:
        if self.is_dialog():
            return self.parent().setFixedSize(w, h)
        return super(AbstractWindow, self).setFixedSize(w, h)

    @override(check_signature=False)
    def setMaximumSize(self, maxw: int, maxh: int) -> None:
        if self.is_dialog():
            return self.parent().setMaximumSize(maxw, maxh)
        return super(AbstractWindow, self).setMaximumSize(maxw, maxh)

    def exists(self) -> bool:
        """
        Returns whether this window currently exists.

        :return: True if window exists; False otherwise.
        :rtype: bool
        """

        return True

    def is_instance(self) -> bool:
        """
        Returns whether this window is a child of another window.

        :return: True if this window is a child of another window; False otherwise.
        :rtype: bool
        """

        return self._child_window

    def is_dialog(self) -> bool:
        """
        Returns whether this window is a dialog.

        :return: True if window is a dialog; False otherwise.
        :rtype: bool
        """

        try:
            return isinstance(self.parent(), QDialog)
        except RuntimeError:
            return False

    def is_closed(self) -> bool:
        """
        Returns whether window has been closed.

        :return: True if window has been closed; False otherwise.
        :rtype: bool
        """

        return self._window_closed

    def is_loaded(self) -> bool:
        """
        Returns whether window is currently loaded.

        :return: True if window is currently loaded; False otherwise.
        :rtype: bool
        """

        return self._window_loaded and not self.is_closed()

    def floating(self) -> bool:
        """
        Returns whether window is floating.

        :return: True if window is floating; False if window is docked.
        :rtype: bool
        """

        return not self.is_instance()

    def dockable(self, raw: bool = False):
        """
        Returns whether this window is dockable.

        :param bool raw: whether the current state of the window should be returned or the current setting.
        :return: True if window can be docked; False otherwise.
        :rtype: bool
        """

        if raw:
            return self._dockable
        if self.is_instance():
            return False
        if self._was_docked is not None:
            return self._was_docked

        return self._dockable

    def set_dockable(self, flag, override: bool = False):
        """
        Sets whether this window should be dockable.

        :param bool flag: True to make the window dockable; False otherwise.
        :param bool override: whether dockable raw value should be set.
        """

        if override:
            self._was_docked = self._dockable = flag
        else:
            self._was_docked = self._dockable
            self._dockable = flag
            self.save_window_position()

    def docked(self) -> bool:
        """
        Returns whether window is currently docked.

        :return: True if window is currently docked; False otherwise.
        :rtype: bool
        """

        if not self.dockable():
            return False

        raise NotImplementedError('Docked functionality not implemented.')

    def set_docked(self, flag: bool):
        """
        Sets whether window is docked.

        :param bool flag: True to dock the window; False to undock it.
        """

        raise NotImplementedError('Docked functionality not implemented.')

    def set_floating(self, flag: bool):
        """
        Sets whether window should be floating.

        :param bool flag: True to make the window floating; False otherwise.
        """

        self.set_docked(not flag)

    def set_enable_save_window_position(self, flag: bool):
        """
        Sets whether save window position should be saved.

        :param bool flag: True to save window position; False otherwise.
        """

        self._enable_state = flag

    def save_window_position(self, settings_path: str | None = None):
        """
        Saves the window position into the window settings file.

        :param str settings_path: optional settings path where window position will be stored.
        :return: True if save window settings operation was successful; False otherwise.
        :rtype: bool
        """

        if self.is_instance():
            return False

        if self._force_disable_saving or not self._enable_state:
            return False

        settings_path = settings_path or self._window_data_path

        return self.save_window_settings(self.ID, self._window_settings, settings_path=settings_path)

    def load_window_position(self):
        """
        Loads the previous position or center the window.
        """

        if self.is_instance():
            return

        if self._initial_pos_override is not None:
            x, y = self._initial_pos_override
            x, y = win32.set_coordinates_to_screen(x, y, self.width(), self.height(), padding=5)
            self.move(x, y)
        else:
            self.center()

    def center(self, parent_geometry=None, child_geometry=None):
        """
        Centers the current window to its parent.

        :param parent_geometry:
        :param child_geometry:
        """

        if parent_geometry is None or child_geometry is None:
            base = self.parent() if self.is_dialog() else self
            if parent_geometry is None:
                try:
                    parent_geometry = base.parent().frameGeometry()
                except AttributeError:
                    parent_geometry = QApplication.desktop().screenGeometry()
            child_geometry = child_geometry if child_geometry is not None else base.frameGeometry()

        self.move(
            int(parent_geometry.x() + (parent_geometry.width() - child_geometry.width()) / 2),
            int(parent_geometry.y() + (parent_geometry.height() - child_geometry.height()) / 2),
        )

    def window_palette(self) -> str | None:
        """
        Returns the current palette of the window.

        :return: window palette name.
        :rtype: str or None
        """

        return self._window_palette

    def set_window_palette(self, name: str, version: int | None, style: bool = True):
        """
        Sets palette with given name and version to this window.

        :param str name: name of the paelette to set.
        :param int or None version: optional palette version to set.
        :param bool style: whether to apply style.
        """

        palette.set_palette(name, version=version, style=style)
        self._window_palette = f'{name}.{version}' if version is not None else name

    def display_message(
            self, title: str, message: str, details: str | None = None, buttons: tuple[str, ...] = ('Ok',),
            default_button: str | None = None, cancel_button: str | None = None,
            checkbox: bool | QCheckBox | None = None) -> str | tuple[str, bool]:
        """
        Displays a popup message box.

        :param str title: title of the message box.
        :param str message: short sentence with a question or statement.
        :param str or None details: optional extra information.
        :param tuple[str] buttons: defines which buttons to use.
        :param str or None default_button: defines which button is selected by default.
        :param str or None cancel_button: defines which button acts as the no/cancel option.
        :param bool or QCheckBox or None checkbox: optional checkbox to add.
        :return: tuple with the name of  button clicked and the checkbox status if checkbox is not None else the name
            of the button clicked.
        :rtype: str | tuple[str, bool]
        """

        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        if details:
            msg.setInformativeText(details)

        buttons_dict = dict()
        for button in buttons:
            buttons_dict[getattr(QMessageBox, button)] = button
        standard_buttons = 0
        for button in buttons_dict:
            standard_buttons |= button
        msg.setStandardButtons(standard_buttons)
        msg.setDefaultButton(getattr(QMessageBox, buttons[-1] if default_button is None else default_button))
        if cancel_button is not None:
            msg.setEscapeButton(getattr(QMessageBox, cancel_button))
        if checkbox is not None:
            checkbox = QCheckBox(checkbox) if not isinstance(checkbox, QCheckBox) else checkbox
            try:
                msg.setCheckBox(checkbox)
            except AttributeError:
                pass

        result = buttons_dict[msg.exec_()]

        return result, checkbox.isChecked() if checkbox is not None else result

    def _set_child_window(self, flag: bool):
        """
        Internal function that sets whether this window is a child of another window.

        :param bool flag: True to mark this window as a child of other window; False otherwise.
        """

        self._child_window = flag

    def _get_settings_key(self) -> str:
        """
        Internal function that returns the key to use when saving settings.

        :return: settings key.
        :rtype: str
        """

        if self._batch:
            return 'batch'
        if self.dockable():
            return 'dock'
        elif self.is_dialog():
            return 'dialog'
        elif self.is_instance():
            return 'instance'
        else:
            return 'main'

    def _parent_override(self):
        return super(AbstractWindow, self)


class StandaloneWindow(AbstractWindow):
    """
    Window intended to be used in standalone Python applications.
    """

    class MultiAppLaunch(Process):
        """
        Launch multiple QApplications in separated processes
        """

        def __init__(self, cls, *args, **kwargs):
            self.cls = cls
            self.args = args
            self.kwargs = kwargs
            super().__init__()

        @override
        def run(self) -> None:
            """
            Launches the app once the process has started.
            """

            try:
                app = QApplication(sys.argv)
            except RuntimeError:
                app = QApplication.instance()
            new_window = super(StandaloneWindow, self.cls).show(*self.args, **self.kwargs)
            if isinstance(app, QApplication):
                app.setActiveWindow(new_window)
            sys.exit(app.exec_())

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._standalone = True

    @classmethod
    @override
    def clear_window_instance(cls, window_id: str) -> dict:
        previous_instance = super(StandaloneWindow, cls).clear_window_instance(window_id)
        if previous_instance is None:
            return

        if not previous_instance['window'].is_closed():
            try:
                previous_instance['window'].close()
            except (RuntimeError, ReferenceError):
                pass

        return previous_instance

    @decorators.HybridMethod
    @override(check_signature=False)
    def show(cls, self, *args, **kwargs) -> StandaloneWindow:

        if self is not cls:
            return super(StandaloneWindow, self).show()

        # Open a new window
        instance = kwargs.pop('instance', False)
        exec_ = kwargs.pop('exec_', True)

        new_window = None
        try:
            app = QApplication(sys.argv)
            new_window = super(StandaloneWindow, cls).show(*args, **kwargs)
            if isinstance(app, QApplication):
                app.setActiveWindow(new_window)
        except RuntimeError:
            if instance:
                app = QApplication.instance()
                new_window = super(StandaloneWindow, cls).show(*args, **kwargs)
                if isinstance(app, QApplication):
                    app.setActiveWindow(new_window)
                if exec_:
                    app.exec_()
            else:
                StandaloneWindow.MultiAppLaunch(cls, *args, **kwargs).start()
        else:
            if exec_:
                sys.exit(app.exec_())

        return new_window

    @override
    def closeEvent(self, event: QEvent):
        """
        Overrides closeEvent function to save the window location on window close.

        :param QEvent event: Qt event.
        """

        self.save_window_position()
        self.clear_window_instance(self.ID)
        return super(StandaloneWindow, self).closeEvent(event)

    @override
    def save_window_position(self, settings_path: str | None = None):
        if 'standalone' not in self._window_settings:
            self._window_settings['standalone'] = dict()
        settings = self._window_settings['standalone']

        key = self._get_settings_key()
        if key not in settings:
            settings[key] = dict()

        settings[key]['width'] = self.width()
        settings[key]['height'] = self.height()
        settings[key]['x'] = self.x()
        settings[key]['y'] = self.y()

        return super(StandaloneWindow, self).save_window_position()

    @override
    def load_window_position(self):
        key = self._get_settings_key()
        try:
            x = self._window_settings['standalone'][key]['x']
            y = self._window_settings['standalone'][key]['y']
            width = self._window_settings['standalone'][key]['width']
            height = self._window_settings['standalone'][key]['height']
        except KeyError:
            super(StandaloneWindow, self).load_window_position()
        else:
            x, y = win32.set_coordinates_to_screen(x, y, width, height, padding=5)
            self.resize(width, height)
            self.move(x, y)

    @override
    def window_palette(self) -> str | None:
        current_palette = super(StandaloneWindow, self).window_palette()
        if current_palette is None:
            if qtutils.is_pyside() or qtutils.is_pyqt4():
                return 'Qt.4'
            elif qtutils.is_pyside2() or qtutils.is_pyqt5():
                return 'Qt.5'

        return current_palette

    @override(check_signature=False)
    def set_window_palette(self, name: str, version: int | None, style: bool = True, force: bool = False):
        """
        Sets the palette of the window. If the window is parented to another StandaloneWindow, then skip to avoid
        overriding its color scheme.

        :param str name: name of the paelette to set.
        :param int or None version: optional palette version to set.
        :param bool style: whether to apply style.
        """

        if not force:
            for widget in QApplication.topLevelWidgets():
                if widget != self and isinstance(widget, AbstractWindow) and not widget.is_instance():
                    return

        super(StandaloneWindow, self).set_window_palette(name, version=version, style=style)


class EmbeddedWindow(QFrame):
    """
    QFrame that appears like a window inside another UI.
    """

    def __init__(
            self, title: str = '', default_visibility: bool = True, uppercase: bool = False,
            close_button: QPushButton | None = None, margins: tuple[int, int, int, int] = (0, 0, 0, 0),
            resize_target: QWidget | None = None, parent: QWidget | None = None):
        super().__init__(parent)

        self._title = title
        self._uppercase = uppercase
        self._margins = margins
        self._parent_widget = parent
        self._resize_target: QWidget | None = None
        self._target_saved_height: int | None = None
        self._inner_frame: QFrame | None = None
        self._outer_layout: QHBoxLayout | None = None
        self._properties_layout: QVBoxLayout | None = None
        self._properties_label: QLabel | None = None

        self._setup_ui()
        self._setup_signals()

    def _setup_ui(self):
        """
        Internal function that setup widgets.
        """

        self._inner_frame = QFrame(parent=self)
        self._inner_frame.setFrameStyle(QFrame.Box | QFrame.Plain)
        self._outer_layout = layouts.horizontal_layout(margins=(dpi.margins_dpi_scale(*self._margins)), parent=self)
        qtutils.set_stylesheet_object_name(self._inner_frame, 'embededWindowBG')
        self._outer_layout.addWidget(self._inner_frame)
        self._properties_layout = layouts.vertical_layout(
            margins=(consts.WINDOW_SIDE_PADDING, 4, consts.WINDOW_SIDE_PADDING, consts.WINDOW_TOP_PADDING),
            spacing=consts.DEFAULT_SPACING)

    def _setup_signals(self):
        """
        Internal function that setup widget connection signals.
        """

        pass
