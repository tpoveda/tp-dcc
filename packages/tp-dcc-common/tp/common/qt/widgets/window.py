#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for custom PySide/PyQt windows
"""

import os
from collections import defaultdict

from Qt.QtCore import Qt, Signal, QByteArray, QSettings
from Qt.QtWidgets import QApplication, QSizePolicy, QToolBar, QScrollArea, QMenuBar, QAction, QDockWidget
from Qt.QtWidgets import QMainWindow, QWidget, QFrame, QTabWidget, QTabBar

from tp.core import log, dcc
from tp.core.managers import resources
from tp.preferences import manager as preferences
from tp.common.python import helpers, path, folder
# from tp.common.resources import theme
from tp.common.qt import qtutils, animation, statusbar, dragger, resizers, settings as qt_settings
from tp.common.qt.widgets import layouts

LOGGER = log.tpLogger


class WindowContents(QFrame, object):
    """
    Widget that defines the core contents of frameless window
    Can be used to custom CSS for frameless windows contents
    """

    def __init__(self, parent=None):
        super(WindowContents, self).__init__(parent=parent)


# @theme.mixin
class BaseWindow(QMainWindow, object):

    closed = Signal()
    themeUpdated = Signal(object)
    styleReloaded = Signal(object)

    WindowName = 'New Window'

    def __init__(self, parent=None, **kwargs):

        main_window = dcc.get_main_window()
        parent = parent or main_window
        window_id = kwargs.get('id', None)
        self._theme = None
        self._docks = list()
        self._toolbars = dict()
        self._menubar = None
        self._dpi = kwargs.get('dpi', 1.0)
        self._fixed_size = kwargs.get('fixed_size', False)
        self._init_width = kwargs.get('width', 600)
        self._init_height = kwargs.get('height', 800)
        self._has_main_menu = False
        self._show_status_bar = kwargs.pop('show_statusbar', True)
        self._init_menubar = kwargs.pop('init_menubar', False)
        self._settings = kwargs.pop('settings', None)
        self._prefs_settings = kwargs.pop('preferences_settings', None)
        self._enable_save_position = True
        self._initial_pos_override = None
        self._signals = defaultdict(list)
        self._force_disable_saving = False
        win_settings = kwargs.pop('settings', None)
        auto_load = kwargs.get('auto_load', True)

        super(BaseWindow, self).__init__(parent)

        if not hasattr(self, 'WindowId'):
            if window_id:
                self.WindowId = window_id
            else:
                self._force_disable_saving = True
                self.WindowId = self.__class__.__name__

        self.setObjectName(str(self.WindowId))
        self.setWindowTitle(kwargs.get('title', self.WindowName))
        self.setWindowIcon(kwargs.get('icon', resources.icon('tpdcc')))
        # self.setFocusPolicy(Qt.ClickFocus)
        if dcc.is_standalone():
            self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.setMouseTracking(True)

        self.resize(self._init_width, self._init_height)
        self.center(self._init_width, self._init_height)

        self.setProperty('tool', self)

        # Load base generic window UI
        self._base_ui()

        # Load custom window UI
        self.ui()
        self.setup_signals()

        self.load_settings(settings=win_settings)

        if auto_load:
            self.load_theme()
        else:
            self.reload_stylesheet()

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def menuBar(self):
        return self._menubar

    def show(self, *args, **kwargs):
        """
        Shows the window and load its position
        :param self:
        :param args:
        :param kwargs:
        """

        super(BaseWindow, self).show()
        self.load_window_position()
        self.activateWindow()
        self.raise_()

        return self

    def closeEvent(self, event):
        self.save_settings()
        self.closed.emit()
        # for child in self.findChildren(QWidget):
        #     child.close()
        self.setParent(None)
        self.deleteLater()

    def addDockWidget(self, area, dock_widget, orientation=Qt.Horizontal, tabify=True):
        """
        Overrides base QMainWindow addDockWidet function
        :param QDockWidgetArea area: area where dock will be added
        :param QDockWidget dock_widget: dock widget to add
        :param Qt.Orientation orientation: orientation fo the dock widget
        :param bool tabify: Whether or not dock widget can be tabbed
        """

        self._docks.append(dock_widget)
        if self._has_main_menu:
            self._view_menu.addAction(dock_widget.toggleViewAction())

        if tabify:
            for current_dock in self._docks:
                if self.dockWidgetArea(current_dock) == area:
                    self.tabifyDockWidget(current_dock, dock_widget)
                    dock_widget.setVisible(True)
                    dock_widget.setFocus()
                    dock_widget.raise_()
                    return

        super(BaseWindow, self).addDockWidget(area, dock_widget, orientation)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def process_events(self):
        """
        Forces Qt application to update GUI between calculations
        """

        qtutils.process_ui_events()

    def center(self, width=None, height=None):
        """
        Centers window to the center of the desktop
        :param width: int
        :param height: int
        """

        geometry = self.frameGeometry()
        if width:
            geometry.setWidth(width)
        if height:
            geometry.setHeight(height)

        desktop = QApplication.desktop()
        pos = desktop.cursor().pos()
        screen = desktop.screenNumber(pos)
        center_point = desktop.screenGeometry(screen).center()
        geometry.moveCenter(center_point)
        self.window().setGeometry(geometry)

    def center_to_parent(self, parent_geometry=None, child_geometry=None):
        """
        Centers current window to its parent
        :param parent_geometry:
        :param child_geometry:
        """

        if parent_geometry is None or child_geometry is None:
            base_window = self
            if parent_geometry is None:
                try:
                    parent_geometry = base_window.parent().frameGeometry()
                except AttributeError:
                    parent_geometry = QApplication.desktop().screenGeometry()
            if child_geometry is None:
                child_geometry = base_window.frameGeometry()

        self.move(
            parent_geometry.x() + (parent_geometry.width() - child_geometry.width()) / 2,
            parent_geometry.y() + (parent_geometry.height() - child_geometry.height()) / 2
        )

    def fade_close(self):
        """
        Closes the window with a fade animation
        """

        animation.fade_window(start=1, end=0, duration=400, object=self, on_finished=self.close)

    def show_ok_message(self, message, msecs=None):
        """
        Set an ok message to be displayed in the status bar
        :param message: str
        :param msecs: int
        """

        self._self._status_bar.show_ok_message(message=message, msecs=msecs)

    def show_info_message(self, message, msecs=None):
        """
        Set an info message to be displayed in the status bar
        :param message: str
        :param msecs: int
        """

        self._status_bar.show_info_message(message=message, msecs=msecs)

    def show_warning_message(self, message, msecs=None):
        """
       Set a warning message to be displayed in the status widget
       :param message: str
       :param msecs: int
       """

        self._status_bar.show_warning_message(message=message, msecs=msecs)

    def show_error_message(self, message, msecs=None):
        """
       Set an error message to be displayed in the status widget
       :param message: str
       :param msecs: int
       """

        self._status_bar.show_error_message(message=message, msecs=msecs)

    # ============================================================================================================
    # UI
    # ============================================================================================================

    def get_main_layout(self):
        """
        Returns the main layout being used by the window
        :return: QLayout
        """

        return layouts.VerticalLayout(spacing=0, margins=(0, 0, 0, 0))

    def ui(self):
        """
        Function used to define UI of the window
        """

        pass

    def _base_ui(self):
        """
        Internal function that setup basic window UI
        """

        self.setDockNestingEnabled(True)
        self.setDocumentMode(True)
        self.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks)
        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.North)

        # Central Widget

        self._central_widget = QWidget(self)
        self.setCentralWidget(self._central_widget)
        self._central_layout = layouts.VerticalLayout(margins=(0, 0, 0, 0), spacing=0)
        self._central_widget.setLayout(self._central_layout)

        self._top_widget = QWidget(self)
        self._top_widget.setObjectName('topWindowWidget')
        self._top_layout = layouts.VerticalLayout(margins=(0, 0, 0, 0), spacing=0)
        self._top_widget.setLayout(self._top_layout)

        # Status Bar

        # self.statusBar().showMessage('')
        # self.statusBar().setSizeGripEnabled(not self._fixed_size)
        # self._status_bar = self.STATUS_BAR_WIDGET(self)
        # self.statusBar().addWidget(self._status_bar)
        # self.statusBar().setVisible(self._show_status_bar)

        # MenuBar
        self._menubar = QMenuBar(self)
        if self._init_menubar:
            self._has_main_menu = True
            self._file_menu = self.menuBar().addMenu('File')
            self._view_menu = self.menuBar().addMenu('View')
            self._exit_action = QAction(self)
            self._exit_action.setText('Close')
            self._exit_action.setShortcut('Ctrl + Q')
            self._exit_action.setIcon(resources.icon('close_window'))
            self._exit_action.setToolTip('Close application')
            self._file_menu.addAction(self._exit_action)
            self._exit_action.triggered.connect(self.fade_close)
            for i in self._docks:
                self._view_menu.addAction(i.toggleViewAction())
        self._top_layout.addWidget(self._menubar)

        self.main_widget = WindowContents(self)
        self.main_layout = self.get_main_layout()
        self.main_widget.setLayout(self.main_layout)

        self._central_layout.addWidget(self._top_widget)
        self._central_layout.addWidget(self.main_widget)

    # ============================================================================================================
    # SIGNALS
    # ============================================================================================================

    def setup_signals(self):
        """
        Override in derived class to setup signals
        This function is called after ui() function is called
        """

        pass

    def signal_connect(self, signal, fn, group=None):
        """
        Adds a new signal for the given group
        :param signal:
        :param fn:
        :param group:
        """

        self._signals[group].append((signal, fn))
        signal.connect(fn)

        return fn

    def signal_disconnect(self, group):
        """
        Disconnects and returns all functions for a current group
        :param group:
        :return: list
        """

        signals = list()
        for (signal, fn) in self._signals.pop(group, list()):
            try:
                signal.disconnect(fn)
            except RuntimeError:
                pass
            else:
                signals.append((signal, fn))

        return signals

    def signal_pause(self, *groups):
        """
        Pauses a certain set of signals during execution
        :param groups: list
        """

        if not groups:
            groups = self._signals

        signal_cache = dict()
        for group in groups:
            signal_cache[group] = self.signal_disconnect(group)

        yield

        for group in groups:
            for signal, fn in signal_cache[group]:
                self.signal_connect(signal, fn, group=group)

    # ============================================================================================================
    # SETTINGS
    # ============================================================================================================

    def settings(self):
        """
        Returns window settings
        :return: QtSettings
        """

        return self._settings

    def default_settings(self):
        """
        Returns default settings values
        :return: dict
        """

        return {}

    def set_settings(self, settings):
        """
        Set window settings
        :param settings:
        """

        self._settings = settings

        def_settings = self.default_settings()

        def_geometry = self.settings().get_default_value('geometry', self.objectName().upper())
        geometry = self.settings().getw('geometry', def_geometry)
        if geometry:
            self.restoreGeometry(geometry)

            # Reposition window in the center of the screen if the window is outside of the screen
            geometry = self.geometry()
            x = geometry.x()
            y = geometry.y()
            width = self._init_width or geometry.width()
            height = self._init_height or geometry.height()
            screen_geo = QApplication.desktop().screenGeometry()
            screen_width = screen_geo.width()
            screen_height = screen_geo.height()
            if x <= 0 or y <= 0 or x >= screen_width or y >= screen_height:
                self.center(width, height)

        def_window_state = self.settings().get_default_value('windowState', self.objectName().upper())
        window_state = self.settings().getw('windowState', def_window_state)
        if window_state:
            self.restoreState(window_state)

    def load_settings(self, settings=None):
        """
        Loads window settings from disk
        """

        settings = settings or self.settings()
        if not settings:
            settings = self._settings
            if not settings:
                self._settings = qt_settings.QtSettings(filename=self.get_settings_file(), window=self)
                self._settings.setFallbacksEnabled(False)
                if not self._prefs_settings:
                    self._prefs_settings = self._settings
            return self.set_settings(self._settings)

        return self.set_settings(settings)

    def save_settings(self, settings=None):
        """
        Saves window settings
        """

        settings = settings or self.settings()
        if not settings:
            return

        settings.setw('geometry', self.saveGeometry())
        settings.setw('saveState', self.saveState())
        settings.setw('windowState', self.saveState())

        return settings

    def get_settings_path(self):
        """
        Returns path where window settings are stored
        :return: str
        """

        return path.clean_path(os.path.join(path.get_user_data_dir(), self.WindowId))

    def get_settings_file(self):
        """
        Returns file path of the window settings file
        :return: str
        """

        return path.clean_path(os.path.expandvars(os.path.join(self.get_settings_path(), 'settings.cfg')))

    def enable_save_window_position(self, enable):
        """
        Enables or disables the storage of window position in settings
        :param enable: bool
        """

        self._enable_save_position = enable

    def load_window_position(self):
        pass
        # if self._initial_pos_override is not None:
        #     x, y = self._initial_pos_override()
        #     x, y =

    def save_window_position(self):
        print('Saving window position ...')

    # ============================================================================================================
    # DPI
    # ============================================================================================================

    def dpi(self):
        """
        Return the current dpi for the window
        :return: float
        """

        return float(self._dpi)

    def set_dpi(self, dpi):
        """
        Sets current dpi for the window
        :param dpi: float
        """

        self._dpi = dpi

    # ============================================================================================================
    # THEME
    # ============================================================================================================

    def load_theme(self, theme_name=None, theme_settings=None):
        """
        Loads window theme
        """

        theme_name = theme_name or self.settings().get('theme', 'default') if self._settings else 'default'
        theme_to_load = resources.theme(theme_name)
        if theme_to_load:
            if theme_settings:
                theme_to_load.set_settings(theme_settings)

            # def_settings = self.default_settings()
            # def_theme_settings = def_settings.get('theme', dict())
            # accent_color = self.settings().get('theme/accentColor') or def_theme_settings.get('accent_color')
            # background_color = self.settings().get('theme/backgroundColor') or def_theme_settings.get('background_color')
            # accent_color = 'rgb(%d, %d, %d, %d)' % accent_color.getRgb() if isinstance(
            #     accent_color, QColor) else accent_color
            # background_color = 'rgb(%d, %d, %d, %d)' % background_color.getRgb() if isinstance(
            #     background_color, QColor) else background_color
            #
            # theme_settings = dict()
            # if accent_color:
            #     accent_color = color.convert_2_hex(accent_color)
            #     theme_settings['accent_color'] = accent_color
            # if background_color:
            #     background_color = color.convert_2_hex(background_color)
            #     theme_settings['background_color'] = background_color
            #
            # new_theme = self.set_theme_settings(theme_settings)
            self.set_theme(theme_to_load)
        else:
            theme_preferences = preferences.get_theme_preference_interface()
            result = theme_preferences.stylesheet()
            self.setStyleSheet(result.data)

    def theme(self):
        """
        Returns the current theme
        :return: Theme
        """

        return self._theme

    def set_theme(self, theme):
        """
        Sets current window theme
        :param theme: Theme
        """

        self._theme = theme
        # self._theme.updated.connect(self.reload_stylesheet)
        # self._theme.set_dpi(self.dpi())
        self.reload_stylesheet()
        # self.themeUpdated.emit(self._theme)

    def reload_stylesheet(self):
        """
        Reloads the stylesheet to the current theme
        """

        theme_preferences = preferences.get_theme_preference_interface()
        result = theme_preferences.stylesheet(self.theme())
        self.setStyleSheet(result.data)

        # current_theme.set_dpi(self.dpi())
        # self.setStyleSheet(stylesheet)
        # self.styleReloaded.emit(current_theme)

    # ============================================================================================================
    # TOOLBAR
    # ============================================================================================================

    def add_toolbar(self, name, area=Qt.TopToolBarArea):
        """
        Adds a new toolbar to the window
        :return:  QToolBar
        """

        new_toolbar = QToolBar(name, parent=self)
        self.addToolBar(area, new_toolbar)

        return new_toolbar

    # ============================================================================================================
    # DOCK
    # ============================================================================================================

    def add_dock(self, name, widget=None, pos=Qt.LeftDockWidgetArea, tabify=True):
        """
        Adds a new dockable widget to the window
        :param name: str, name of the dock widget
        :param widget: QWidget, widget to add to the dock
        :param pos: Qt.WidgetArea
        :param tabify: bool, Wheter the new widget should be tabbed to existing docks
        :return: QDockWidget
        """

        if widget:
            dock_name = ''.join([widget.objectName(), 'Dock'])
        else:
            dock_name = name + 'Dock'

        existing_dock = self.find_dock(dock_name)
        if existing_dock:
            existing_dock.raise_()

        dock = DockWidget(title=name, parent=self, floating=False)
        dock.setObjectName(dock_name)
        if widget is not None:
            dock.setWidget(widget)
        self.addDockWidget(pos, dock, tabify=tabify)

        return dock

    def set_active_dock_tab(self, dock_widget):
        """
        Sets the current active dock tab depending on the given dock widget
        :param dock_widget: DockWidget
        """

        tab_bars = self.findChildren(QTabBar)
        for bar in tab_bars:
            count = bar.count()
            for i in range(count):
                data = bar.tabData(i)
                widget = qtutils.to_qt_object(data, qobj=type(dock_widget))
                if widget == dock_widget:
                    bar.setCurrentIndex(i)

    def find_dock(self, dock_name):
        """
        Returns the dock widget based on the object name passed
        :param str dock_name: dock objectName to find
        :return: QDockWidget or None
        """

        for dock in self._docks:
            if dock.objectName() == dock_name:
                return dock

        return None

    def _parent_override(self):
        """
        Internal function that overrides parent functionality to make sure that proper parent attributes are used
        in dockable windows
        """

        # Make sure this function is inherited
        return super(MainWindow, self)

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    def _load_ui_from_file(self, ui_file):
        """
        Internal function that loads given UI file
        :param ui_file: str
        :return: QWidget or None
        """

        if not os.path.isfile(ui_file):
            return None

        loaded_ui = qtutils.load_ui(ui_file=ui_file)

        return loaded_ui


class MainWindow(BaseWindow, object):
    """
    Main class to create windows
    """

    dockChanged = Signal(object)
    windowResizedFinished = Signal()
    framelessChanged = Signal(object)
    windowReady = Signal()
    clearedInstance = Signal()

    STATUS_BAR_WIDGET = statusbar.StatusWidget
    DRAGGER_CLASS = dragger.WindowDragger

    _WINDOW_INSTANCES = dict()

    def __init__(self, parent=None, **kwargs):

        self._setup_resizers()

        self._preference_widgets_classes = list()
        self._toolset = kwargs.get('toolset', None)
        self._transparent = kwargs.get('transparent', False)
        self._config = kwargs.pop('config', None)
        self._was_docked = False
        self._window_loaded = False
        self._window_closed = False
        self._current_docked = None

        super(MainWindow, self).__init__(parent=parent, **kwargs)

        self.setAttribute(Qt.WA_TranslucentBackground)

        self._dockable = getattr(self, 'WindowDockable', False)
        frameless = kwargs.get('frameless', True)
        self.set_frameless(frameless)
        if not frameless:
            self.set_resizers_active(False)
            self._dragger.set_dragging_enabled(False)
            self._dragger.set_window_buttons_state(False)
        else:
            self._dragger.set_dragging_enabled(True)
            self._dragger.set_window_buttons_state(True)

        self.update_dragger()

        # We set the window title after UI is created
        self.setWindowTitle(kwargs.get('title', 'tpDcc'))
        self.setWindowIcon(kwargs.get('icon', resources.icon('tpdcc')))

        MainWindow._WINDOW_INSTANCES[self.WindowId] = {
            'window': self
        }

        self.windowReady.connect(lambda: setattr(self, '_window_loaded', True))

        app = QApplication.instance()
        if app:
            app.focusChanged.connect(self._on_change_focus)

        self.clearedInstance.connect(self.close)

    # ============================================================================================================
    # PROPERTIES
    # ============================================================================================================

    @property
    def widget(self):
        """
        Returns widget
        """

        return self._widget

    # ============================================================================================================
    # CLASS METHODS
    # ============================================================================================================

    @classmethod
    def instance(cls, parent=None, **kwargs):
        pass

    @classmethod
    def clear_window_instance(cls, window_id):
        """
        Closes the last class instance
        :param window_id:
        :return:
        """

        inst = cls._WINDOW_INSTANCES.pop(window_id, None)
        if inst is not None:
            try:
                inst['window'].clearedInstance.emit()
            except RuntimeError as exc:
                LOGGER.error('Error while clearing window instance: {} | {}'.format(window_id, exc))

        return inst

    @classmethod
    def clear_window_instances(cls):
        """
        Closes every loaded window
        """

        for window_id in tuple(cls._WINDOW_INSTANCES):
            cls.clear_window_instance(window_id)

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def showEvent(self, event):

        self.clear_window_instance(self.WindowId)

        if self.docked() != self._current_docked:
            self._current_docked = self.docked()
            self.dockChanged.emit(self._current_docked)

        self._on_change_focus(None, self)

        super(MainWindow, self).showEvent(event)

    def closeEvent(self, event):
        self._window_closed = True
        self.unregister_callbacks()
        self.clear_window_instance(self.WindowId)
        super(MainWindow, self).closeEvent(event)

    def setWindowIcon(self, icon):
        if helpers.is_string(icon):
            icon = resources.icon(icon)
        if self.is_frameless() or (hasattr(self, '_dragger') and self._dragger):
            self._dragger.set_icon(icon)
        super(MainWindow, self).setWindowIcon(icon)

    def setWindowTitle(self, title):
        if self.is_frameless() or (hasattr(self, '_dragger') and self._dragger):
            self._dragger.set_title(title)
        super(MainWindow, self).setWindowTitle(title)

    def show(self, *args, **kwargs):
        """
        Shows the window and load its position
        :param self:
        :param args:
        :param kwargs:
        """

        super(MainWindow, self).show()
        self.windowReady.emit()

        return self

    # ============================================================================================================
    # UI
    # ============================================================================================================

    def ui(self):
        """
        Function used to define UI of the window
        """

        super(MainWindow, self).ui()

        for r in self._resizers:
            r.setParent(self)

        # Dragger
        self._dragger = self.DRAGGER_CLASS(window=self)
        self._top_layout.insertWidget(0, self._dragger)

        for r in self._resizers:
            r.windowResizedFinished.connect(self.windowResizedFinished)
        self.set_resize_directions()

        grid_layout = layouts.GridLayout(spacing=0, vertical_spacing=0, horizontal_spacing=0)
        grid_layout.addWidget(self._top_widget, 1, 1, 1, 1)
        grid_layout.addWidget(self.main_widget, 2, 1, 1, 1)
        grid_layout.addWidget(self._top_left_resizer, 0, 0, 1, 1)
        grid_layout.addWidget(self._top_resizer, 0, 1, 1, 1)
        grid_layout.addWidget(self._top_right_resizer, 0, 2, 1, 1)
        grid_layout.addWidget(self._left_resizer, 1, 0, 2, 1)
        grid_layout.addWidget(self._right_resizer, 1, 2, 2, 1)
        grid_layout.addWidget(self._bottom_left_resizer, 3, 0, 1, 1)
        grid_layout.addWidget(self._bottom_resizer, 3, 1, 1, 1)
        grid_layout.addWidget(self._bottom_right_resizer, 3, 2, 1, 1)
        grid_layout.setColumnStretch(1, 1)
        grid_layout.setRowStretch(2, 1)

        self._central_layout.addLayout(grid_layout)

        # Shadow effect for window
        # BUG: This causes some rendering problems when using other shadow effects in child widgets of the window
        # BUG: Also detected problems when updating wigets (tree views, web browsers, etc)
        # https://bugreports.qt.io/browse/QTBUG-35196
        # shadow_effect = QGraphicsDropShadowEffect(self)
        # shadow_effect.setBlurRadius(qtutils.dpi_scale(15))
        # shadow_effect.setColor(QColor(0, 0, 0, 150))
        # shadow_effect.setOffset(qtutils.dpi_scale(0))
        # self.setGraphicsEffect(shadow_effect)

        for r in self._resizers:
            r.windowResizedFinished.connect(self.windowResizedFinished)

        if self._toolset:
            self.main_layout.addWidget(self._toolset)

    # ============================================================================================================
    # SIGNALS
    # ============================================================================================================

    def register_callback(self, callback_type, fn):
        """
        Registers the given callback with the given function
        :param callback_type: tpDcc.DccCallbacks
        :param fn: Python function to be called when callback is emitted
        """

        if type(callback_type) in [list, tuple]:
            callback_type = callback_type[0]

        if callback_type not in dcc.callbacks():
            LOGGER.warning('Callback Type: "{}" is not valid! Aborting callback creation ...'.format(callback_type))
            return

        from tp.core.managers import callbacks
        return callbacks.CallbacksManager().register(callback_type=callback_type, fn=fn, owner=self)

    def unregister_callbacks(self):
        """
        Unregisters all callbacks registered by this window
        """

        from tp.core.managers import callbacks
        callbacks.CallbacksManager().unregister_owner_callbacks(owner=self)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def tick(self, delta_seconds, *args, **kwargs):
        """
        Function that is called taking into account DCC delta seconds
        NOTE: This function MUST be override if necessary in each DCC, by default it does nothing
        :param delta_seconds: float
        :param args:
        :param kwargs:
        :return:
        """

        # TODO: We can use QTimers to setup a tick and use QApplication event loop
        # TODO: I do not want to force the creation of a QTimer, so for now we implement this for each DCC

        pass

    def exists(self):
        """
        Returns whether or not this window exists
        :return: bool
        """

        return True

    def is_loaded(self):
        """
        Returns whether or not this window has been already loaded
        :return: bool
        """

        return self._window_loaded and not self.is_closed()

    def is_closed(self):
        """
        Returns whether or not this window has been closed
        """

        return self._window_closed

    def is_frameless(self):
        """
        Returns whether or not frameless functionality for this window is enable or not
        :return: bool
        """

        return self.window().windowFlags() & Qt.FramelessWindowHint == Qt.FramelessWindowHint

    def set_frameless(self, flag):
        """
        Sets whether frameless functionality is enabled or not
        :param flag: bool
        :param show: bool
        """

        window = self.window()

        if flag and not self.is_frameless():
            window.setAttribute(Qt.WA_TranslucentBackground)
            if qtutils.is_pyside2() or qtutils.is_pyqt5():
                window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
                window.setWindowFlags(window.windowFlags() ^ Qt.WindowMinMaxButtonsHint)
            else:
                window.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
                window.setWindowFlags(window.windowFlags() ^ Qt.WindowMinMaxButtonsHint)
            self.set_resizers_active(True)
        elif not flag and self.is_frameless():
            window.setAttribute(Qt.WA_TranslucentBackground)
            if qtutils.is_pyside2() or qtutils.is_pyqt5():
                window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
            else:
                self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
            self.set_resizers_active(False)

        window.show()

    # ============================================================================================================
    # DRAGGER
    # ============================================================================================================

    def set_window_buttons_state(self, state, show_close_button=False):
        """
        Sets the state of the dragger buttons
        :param state: bool
        :param show_close_button: bool
        """

        self._dragger.set_window_buttons_state(state, show_close_button)

    def update_dragger(self):
        """
        Updates dragger status
        """

        self._dragger._toggle_frameless.setChecked(self.is_frameless())

    # ============================================================================================================
    # RESIZERS
    # ============================================================================================================

    def set_resizers_active(self, flag, resizers_to_edit=resizers.Resizers.All):
        """
        Sets whether resizers are enable or not
        :param flag: bool
        """

        resizers_to_enable = list()
        if resizers_to_edit & resizers.Resizers.Corners == resizers.Resizers.Corners:
            resizers_to_enable += self.get_corner_resizers()
        if resizers_to_edit & resizers.Resizers.Vertical == resizers.Resizers.Vertical:
            resizers_to_enable += self.get_vertical_resizers()
        if resizers_to_edit & resizers.Resizers.Horizontal == resizers.Resizers.Horizontal:
            resizers_to_enable += self.get_horizontal_resizers()

        if flag:
            for r in resizers_to_enable:
                r.show()
        else:
            for r in resizers_to_enable:
                r.hide()

    def set_resizers_enabled(self, flag, resizers_to_edit=resizers.Resizers.All):
        """
        Enabled or disable window resizers
        :param flag: bool
        :param resizers_to_edit:
        """

        resizers_to_enable = list()
        if resizers_to_edit & resizers.Resizers.Corners == resizers.Resizers.Corners:
            resizers_to_enable += self.get_corner_resizers()
        if resizers_to_edit & resizers.Resizers.Vertical == resizers.Resizers.Vertical:
            resizers_to_enable += self.get_vertical_resizers()
        if resizers_to_edit & resizers.Resizers.Horizontal == resizers.Resizers.Horizontal:
            resizers_to_enable += self.get_horizontal_resizers()

        [resizer.setEnabled(flag) for resizer in resizers_to_enable]

    def set_resize_directions(self):
        """
        Sets the resize directions for the resizer widget of this window
        """

        self._top_resizer.set_resize_direction(resizers.ResizeDirection.Top)
        self._bottom_resizer.set_resize_direction(resizers.ResizeDirection.Bottom)
        self._right_resizer.set_resize_direction(resizers.ResizeDirection.Right)
        self._left_resizer.set_resize_direction(resizers.ResizeDirection.Left)
        self._top_left_resizer.set_resize_direction(resizers.ResizeDirection.Left | resizers.ResizeDirection.Top)
        self._top_right_resizer.set_resize_direction(resizers.ResizeDirection.Right | resizers.ResizeDirection.Top)
        self._bottom_left_resizer.set_resize_direction(resizers.ResizeDirection.Left | resizers.ResizeDirection.Bottom)
        self._bottom_right_resizer.set_resize_direction(
            resizers.ResizeDirection.Right | resizers.ResizeDirection.Bottom)

    def get_resizers_height(self):
        """
        Returns the total height of the vertical resizers
        :return: float
        """

        resizers = [self._top_resizer, self._bottom_resizer]
        total_height = 0
        for r in resizers:
            if not r.isHidden():
                total_height += r.minimumSize().height()

        return total_height

    def get_resizers_width(self):
        """
        Returns the total widht of the horizontal resizers
        :return: float
        """

        resizers = [self._left_resizer, self._right_resizer]
        total_width = 0
        for r in resizers:
            if not r.isHidden():
                total_width += r.minimumSize().width()

        return total_width

    def get_horizontal_resizers(self):
        """
        Returns all horizontal resizers
        :return: list
        """

        return [self._left_resizer, self._right_resizer]

    def get_vertical_resizers(self):
        """
        Returns all vertical resizers
        :return: list
        """

        return [self._top_resizer, self._bottom_resizer]

    def get_corner_resizers(self):
        """
        Returns all corner resizers
        :return: list
        """

        return [self._top_left_resizer, self._top_right_resizer, self._bottom_left_resizer, self._bottom_right_resizer]

    def _setup_resizers(self):
        """
        Internal function that setup window resizers
        """

        self._top_resizer = resizers.VerticalResizer()
        self._bottom_resizer = resizers.VerticalResizer()
        self._right_resizer = resizers.HorizontalResizer()
        self._left_resizer = resizers.HorizontalResizer()
        self._top_left_resizer = resizers.CornerResizer()
        self._top_right_resizer = resizers.CornerResizer()
        self._bottom_left_resizer = resizers.CornerResizer()
        self._bottom_right_resizer = resizers.CornerResizer()

        self._resizers = [
            self._top_resizer, self._top_right_resizer, self._right_resizer, self._bottom_right_resizer,
            self._bottom_resizer, self._bottom_left_resizer, self._left_resizer, self._top_left_resizer
        ]

    # ============================================================================================================
    # PREFERENCES SETTINGS
    # ============================================================================================================

    def preferences_settings(self):
        """
        Returns window preferences settings
        :return: QtSettings
        """

        return self._prefs_settings

    def set_preferences_settings(self, prefs_settings):
        """
        Sets window preference settings
        :param prefs_settings:
        """

        self._prefs_settings = prefs_settings

    def register_preference_widget_class(self, widget_class):
        """
        Function used to registere preference widgets
        """

        if not hasattr(widget_class, 'CATEGORY'):
            LOGGER.warning(
                'Impossible to register Category Wigdet Class "{}" because it does not '
                'defines a CATEGORY attribute'.format(widget_class))
            return

        registered_prefs_categories = [pref.CATEGORY for pref in self._preference_widgets_classes]
        if widget_class.CATEGORY in registered_prefs_categories:
            LOGGER.warning(
                'Impossible to register Category Widget Class "{}" because its CATEGORY "{}" its '
                'already registered!'.format(widget_class, widget_class.CATEGORY))
            return

        self._preference_widgets_classes.append(widget_class)

    # ============================================================================================================
    # DOCK
    # ============================================================================================================

    def dockable(self, raw=False):
        """
        Returns whether or not the window is dockable
        :param raw: bool, If True, get current state of the window, otherwise get current setting
        :return: bool
        """

        if not raw and self._was_docked is not None:
            return self._was_docked

        return self._dockable

    def set_dockable(self, dockable, override=False):
        """
        Sets whether or not this window is dockable
        :param dockable: bool
        :param override: bool, If the dockable raw value should be set.
            Only should be used if the dock state has changed
        """

        if override:
            self._was_docked = self._dockable = dockable
        else:
            self._was_docked = self._dockable
            self._dockable = dockable
            self.save_window_position()

    def docked(self):
        """
        Returns whether or not this window is currently docked
        :return: bool
        """

        if not self.dockable():
            return False

        return False

    def is_floating(self):
        """
        Returns whether or not this window is floating
        :return: bool
        """

        return dcc.is_window_floating(self.WindowId)

    # ============================================================================================================
    # INTERNAL
    # ============================================================================================================

    # def _settings_accepted(self, **kwargs):
    #     """
    #     Function that is called when window settings dialog are accepted
    #     :param kwargs: dict
    #     """
    #
    #     if not self.settings():
    #         return
    #
    #     theme_name = self.theme().name()
    #     accent_color = kwargs.get('accentColor', self.theme().accent_color)
    #     background_color = kwargs.get('backgroundColor', self.theme().background_color)
    #     if theme_name:
    #         self.settings().setw('theme/name', theme_name)
    #     self.settings().setw('theme/accentColor', accent_color)
    #     self.settings().setw('theme/backgroundColor', background_color)
    #     self.settings().sync()
    #
    #     self.load_theme()

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_change_focus(self, old, new):
        """
        Internal callback function that updates the current active Dcc client (if exists)
        This function is triggered each time current window focus changes
        :param old: QObject
        :param new: QObject
        """

        if not self._toolset or not self._toolset.client:
            return

        children = self.findChildren(QWidget)
        if old and dcc._CLIENTS and (old == self or old in children):
            if self._toolset:
                toolset_client = self._toolset.client
                toolset_found = None
                for client_id, client in dcc._CLIENTS.items():
                    if toolset_client == client:
                        toolset_found = client_id
                        break

                # We only remove the client if there is more active clients
                if toolset_found is not None and len(list(dcc._CLIENTS.keys())) > 1:
                    dcc._CLIENTS.pop(client_id)

        if new and (new == self or new in children):
            if self._toolset:
                toolset_client = self._toolset.client
                toolset_found = False
                for client in list(dcc._CLIENTS.values()):
                    if toolset_client == client:
                        toolset_found = True
                        break
                if not toolset_found:
                    if self._toolset.ID not in dcc._CLIENTS and not self._toolset.client._server:
                        dcc._CLIENTS[self._toolset.ID] = self._toolset.client


class DetachedWindow(QMainWindow):
    """
    Class that incorporates functionality to create detached windows
    """

    windowClosed = Signal(object)

    class DetachPanel(QWidget, object):
        widgetVisible = Signal(QWidget, bool)

        def __init__(self, parent=None):
            super(DetachedWindow.DetachPanel, self).__init__(parent=parent)

            self.main_layout = layouts.VerticalLayout()
            self.setLayout(self.main_layout)

        def set_widget_visible(self, widget, visible):
            self.setVisible(visible)
            self.widgetVisible.emit(widget, visible)

        def set_widget(self, widget):
            qtutils.clear_layout(self.main_layout)
            self.main_layout.addWidget(widget)
            widget.show()

    class SettingGroup(object):
        global_group = ''

        def __init__(self, name):
            self.name = name
            self.settings = QSettings()

        def __enter__(self):
            if self.global_group:
                self.settings.beginGroup(self.global_group)
            self.settings.beginGroup(self.name)
            return self.settings

        def __exit__(self, *args):
            if self.global_group:
                self.settings.endGroup()
            self.settings.endGroup()
            self.settings.sync()

        @staticmethod
        def load_basic_window_settings(window, window_settings):
            window.restoreGeometry(window_settings.value('geometry', QByteArray()))
            window.restoreState(window_settings.value('windowstate', QByteArray()))
            try:
                window.split_state = window_settings.value('splitstate', '')
            except TypeError:
                window.split_state = ''

    def __init__(self, title, parent):
        self.tab_idx = -1
        super(DetachedWindow, self).__init__(parent=parent)

        self.main_widget = self.DetachPanel()
        self.setCentralWidget(self.main_widget)

        self.setWindowTitle(title)
        self.setWindowModality(Qt.NonModal)
        self.sgroup = self.SettingGroup(title)
        with self.sgroup as config:
            self.SettingGroup.load_basic_window_settings(self, config)

        self.statusBar().hide()

    def closeEvent(self, event):
        with self.sgroup as config:
            config.setValue('detached', False)
        self.windowClosed.emit(self)
        self.deleteLater()

    def moveEvent(self, event):
        super(DetachedWindow, self).moveEvent(event)
        self.save_settings()

    def resizeEvent(self, event):
        super(DetachedWindow, self).resizeEvent(event)
        self.save_settings()

    def set_widget_visible(self, widget, visible):
        self.setVisible(visible)

    def set_widget(self, widget):
        self.main_widget.set_widget(widget=widget)

    def save_settings(self, detached=True):
        with self.sgroup as config:
            config.setValue('detached', detached)
            config.setValue('geometry', self.saveGeometry())
            config.setValue('windowstate', self.saveState())


class DockWindow(QMainWindow, object):
    """
    Class that with dock functionality. It's not intended to use as main window (use MainWindow for that) but for
    being inserted inside a window and have a widget with dock functionality in the main layout of that window
    """

    class DockWidget(QDockWidget, object):
        def __init__(self, name, parent=None, window=None):
            super(DockWindow.DockWidget, self).__init__(name, parent)

            self.setWidget(window)

        def setWidget(self, widget):
            """
            Sets the window instance of the dockable main window
            """

            super(DockWindow.DockWidget, self).setWidget(widget)

            if widget and issubclass(widget.__class__, MainWindow):
                # self.setFloating(True)
                self.setWindowTitle(widget.windowTitle())
                self.visibilityChanged.connect(self._visibility_changed)

                widget.setWindowFlags(Qt.Widget)
                widget.setParent(self)
                widget.windowTitleChanged.connect(self._window_title_changed)

        def _visibility_changed(self, state):
            """
            Process QDockWidget's visibilityChanged signal
            """

            # TODO: Implement export widget properties functionality
            # widget = self.widget()
            # if widget:
            #     widget.export_settings()

        def _window_title_changed(self, title):
            """
            Process BaseWindow's windowTitleChanged signal
            :param title: str, new title
            """

            self.setWindowTitle(title)

    _last_instance = None

    def __init__(self, name='BaseWindow', title='DockWindow', use_scrollbar=False, parent=None):
        self.main_layout = self.get_main_layout()
        self.__class__._last_instance = self
        super(DockWindow, self).__init__(parent)

        self.docks = list()
        self.connect_tab_change = True
        self.use_scrollbar = use_scrollbar

        self.setObjectName(name)
        self.setWindowTitle(title)
        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().hide()

        self.ui()

        self.tab_change_hide_show = True

    def keyPressEvent(self, event):
        return

    def get_main_layout(self):
        """
        Function that generates the main layout used by the widget
        Override if necessary on new widgets
        :return: QLayout
        """

        main_layout = layouts.VerticalLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(2)

        return main_layout

    def ui(self):
        """
        Function that sets up the ui of the widget
        Override it on new widgets (but always call super)
        """

        main_widget = QWidget()
        if self.use_scrollbar:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(main_widget)
            self._scroll_widget = scroll
            main_widget.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
            self.setCentralWidget(scroll)
        else:
            self.setCentralWidget(main_widget)

        main_widget.setLayout(self.main_layout)
        self.main_widget = main_widget

        self.main_layout.expandingDirections()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # ==========================================================================================

        # TODO: Check if we should put this on constructor
        # self.main_widget.setSizePolicy(QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum))
        # self.centralWidget().hide()

        self.setTabPosition(Qt.TopDockWidgetArea, QTabWidget.West)
        self.setDockOptions(self.AnimatedDocks | self.AllowTabbedDocks | self.AllowNestedDocks)

    def set_active_dock_tab(self, dock_widget):
        """
        Sets the current active dock tab depending on the given dock widget
        :param dock_widget: DockWidget
        """

        tab_bars = self.findChildren(QTabBar)
        for bar in tab_bars:
            count = bar.count()
            for i in range(count):
                data = bar.tabData(i)
                widget = qtutils.to_qt_object(data, qobj=type(dock_widget))
                if widget == dock_widget:
                    bar.setCurrentIndex(i)

    def add_dock(self, widget, name, pos=Qt.TopDockWidgetArea, tabify=True):
        docks = self._get_dock_widgets()
        for dock in docks:
            if dock.windowTitle() == name:
                dock.deleteLater()
                dock.close()
        dock_widget = self.DockWidget(name=name, parent=self)
        # dock_widget.setSizePolicy(QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Minimum))
        dock_widget.setAllowedAreas(pos)
        dock_widget.setWidget(widget)

        self.addDockWidget(pos, dock_widget)

        if docks and tabify:
            self.tabifyDockWidget(docks[-1], dock_widget)

        dock_widget.show()
        dock_widget.raise_()

        tab_bar = self._get_tab_bar()
        if tab_bar:
            if self.connect_tab_change:
                tab_bar.currentChanged.connect(self._on_tab_changed)
                self.connect_tab_change = False

        return dock_widget

    def _get_tab_bar(self):
        children = self.children()
        for child in children:
            if isinstance(child, QTabBar):
                return child

    def _get_dock_widgets(self):
        found = list()
        for child in self.children():
            if isinstance(child, QDockWidget):
                found.append(child)

        return found

    def _on_tab_changed(self, index):
        if not self.tab_change_hide_show:
            return

        docks = self._get_dock_widgets()

        docks[index].hide()
        docks[index].show()


class SubWindow(MainWindow, object):
    """
    Class to create sub windows
    """

    def __init__(self, parent=None, **kwargs):
        super(SubWindow, self).__init__(parent=parent, frameless=False, **kwargs)


class DirectoryWindow(MainWindow, object):
    """
    Window that stores variable to store current working directory
    """

    def __init__(self, parent=None, **kwargs):
        self.directory = None
        super(DirectoryWindow, self).__init__(parent=parent, frameless=False, **kwargs)

    def set_directory(self, directory):
        """
        Sets the directory of the window. If the given folder does not exists, it will created automatically
        :param directory: str, new directory of the window
        """

        self.directory = directory

        if not path.is_dir(directory=directory):
            folder.create_folder(name=None, directory=directory)


class DockWidget(QDockWidget, object):
    """
    Base docked widget
    """

    def __init__(self, title, parent=None, floating=False):
        super(DockWidget, self).__init__(title, parent)

        self.setFloating(floating)
        self.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetClosable)


class DockWindowContainer(DockWidget, object):
    """
    Docked Widget used to dock windows inside other windows
    """

    def __init__(self, title):
        super(DockWindowContainer, self).__init__(title)

    def closeEvent(self, event):
        if self.widget():
            self.widget().close()
        super(DockWindowContainer, self).closeEvent(event)
