#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to plugins
"""

import uuid
import inspect

from Qt.QtCore import Qt, Signal, QSize, QEvent
from Qt.QtWidgets import QWidget, QDockWidget, QGroupBox, QLabel, QLineEdit, QToolButton, QMenu

from tp.core import log, dcc
from tp.common.resources import api as resources
from tp.common.qt.widgets import layouts

logger = log.tpLogger


class BasePlugin:
    """
    Base class used by all  editor tools
    """

    SUPPORTED_SOFTWARES = ['any']
    TOOLTIP = 'Default Tooltip'
    NAME = 'BasePlugin'

    def __init__(self):
        super(BasePlugin, self).__init__()

        self._uid = uuid.uuid4()
        self._app = None

    @property
    def uid(self):
        """
        Returns unique identifier of the tool
        :return: uuid
        """

        return self._uid

    @property
    def app(self):
        """
        Returns app that manages this tool
        :return:
        """

        return self._app

    @app.setter
    def app(self, tool_app):
        """
        Sets the app that manages this tool
        :param tool_app:
        """

        self._app = tool_app

    @staticmethod
    def icon():
        """
        Returns the icon of the tool
        :return: QIcon or None
        """

        return resources.icon('tpRigToolkit')

    def unique_name(self):
        """
        Returns unique name of the tool
        When a tool is not singleton, we need to store separate data for each instance.
        We use unique identifier for that
        :return: str
        """

        return '{}::{}'.format(self.NAME, str(self.uid))

    def show_plugin(self):
        """
        Internal function that is called when the tool pops up
        """

        pass

    def save_state(self, settings):
        """
        Saves the settings of the tool in the given settings
        NOTE: Tool Settings group is already selected when this function is called, so there is no need
        to open/end tool settings group in this function
        :param settings: QtSettings
        """

        settings.setValue('uid', str(self.uid))

    def restore_state(self, settings):
        """
        Restore any save state from given settings
        NOTE: Tool Settings group is already selected when this function is called, so there is no need
        to open/end tool settings group in this function
        :param settings: QtSettings
        """

        uid_str = settings.value(str(self.uid))
        if uid_str:
            self._uid = uuid.UUID(uid_str)
        else:
            self._uid = uuid.uuid4()

    def close_plugin(self):
        """
        Function that is called when tol is closed
        """

        pass


class ShelfPlugin(BasePlugin, object):
    def __init__(self):
        super(ShelfPlugin, self).__init__()

    @staticmethod
    def icon():
        return resources.icon('home')

    def context_menu_builder(self):
        return None

    def do(self):
        print(self.NAME, 'called!')


class DockPlugin(QDockWidget, BasePlugin):

    closed = Signal(object)

    DEFAULT_DOCK_AREA = Qt.LeftDockWidgetArea
    IS_SINGLETON = False

    def __init__(self):
        BasePlugin.__init__(self)
        QDockWidget.__init__(self)

        self.setToolTip(self.TOOLTIP)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(
            Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea)
        self.setObjectName(self.unique_name())
        self.setTitleBarWidget(DockTitleBar(self))
        self.setFloating(False)
        self.setWindowIcon(self.icon())

    def restore_state(self, settings):
        super(DockPlugin, self).restore_state(settings)

        self.setObjectName(self.unique_name())

    def closeEvent(self, event):
        """
        Overrides base QDockWidget closeEvent function
        :param event: QEvent
        """

        from tp.core.managers import plugins

        self.close_plugin()
        plugins.unregister_plugin_instance(self)
        self.closed.emit(self)
        event.accept()

    def add_button(self, button):
        self.titleBarWidget().add_button(button)

    def show_plugin(self):
        """
        Overrides base BaseTool _on_show function
        """

        super(DockPlugin, self).show_plugin()
        self.setWindowTitle(self.NAME)
        self.show()


class DockTitleBar(QWidget, object):
    def __init__(self, dock_widget, renamable=False):
        super(DockTitleBar, self).__init__(dock_widget)

        self._renamable = renamable

        main_layout = layouts.HorizontalLayout(margins=(0, 0, 0, 1))
        self.setLayout(main_layout)

        self._buttons_box = QGroupBox('')
        self._buttons_box.setObjectName('Docked')
        self._buttons_layout = layouts.HorizontalLayout(spacing=1, margins=(2, 2, 2, 2))
        self._buttons_box.setLayout(self._buttons_layout)
        main_layout.addWidget(self._buttons_box)

        self._icon_label = QLabel(self)
        self._title_label = QLabel(self)
        self._title_label.setStyleSheet('background: transparent')
        self._title_edit = QLineEdit(self)
        self._title_edit.setVisible(False)

        self._button_size = QSize(14, 14)

        self._dock_btn = QToolButton(self)
        self._dock_btn.setIcon(resources.icon('restore_window', theme='color'))
        self._dock_btn.setMaximumSize(self._button_size)
        self._dock_btn.setAutoRaise(True)
        self._close_btn = QToolButton(self)
        self._close_btn.setIcon(resources.icon('close_window', theme='color'))
        self._close_btn.setMaximumSize(self._button_size)
        self._close_btn.setAutoRaise(True)

        self._buttons_layout.addSpacing(2)
        self._buttons_layout.addWidget(self._icon_label)
        self._buttons_layout.addWidget(self._title_label)
        self._buttons_layout.addWidget(self._title_edit)
        self._buttons_layout.addStretch()
        self._buttons_layout.addSpacing(5)
        self._buttons_layout.addWidget(self._dock_btn)
        self._buttons_layout.addWidget(self._close_btn)

        self._buttons_box.mouseDoubleClickEvent = self.mouseDoubleClickEvent
        self._buttons_box.mousePressEvent = self.mousePressEvent
        self._buttons_box.mouseMoveEvent = self.mouseMoveEvent
        self._buttons_box.mouseReleaseEvent = self.mouseReleaseEvent

        dock_widget.featuresChanged.connect(self._on_dock_features_changed)
        self._title_edit.editingFinished.connect(self._on_finish_edit)
        self._dock_btn.clicked.connect(self._on_dock_btn_clicked)
        self._close_btn.clicked.connect(self._on_close_btn_clicked)

        self._on_dock_features_changed(dock_widget.features())
        self.set_title(dock_widget.windowTitle())
        dock_widget.installEventFilter(self)
        dock_widget.topLevelChanged.connect(self._on_change_floating_style)

        if hasattr(dock_widget, 'icon') and callable(dock_widget.icon):
            self._icon_label.setPixmap(dock_widget.icon().pixmap(QSize(16, 16)))

    @property
    def renamable(self):
        return self._renamable

    @renamable.setter
    def renamable(self, flag):
        self._renamable = flag

    def eventFilter(self, obj, event):
        try:
            if event.type() == QEvent.WindowTitleChange:
                self.set_title(obj.windowTitle())
            return super(DockTitleBar, self).eventFilter(obj, event)
        except Exception as exc:
            event.accept()
            return True

    def mouseMoveEvent(self, event):
        event.ignore()

    def mousePressEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mouseDoubleClickEvent(self, event):
        if event.pos().x() <= self._title_label.width() and self._renamable:
            self._start_edit()
        else:
            super(DockTitleBar, self).mouseDoubleClickEvent(event)

    def update(self, *args, **kwargs):
        self._on_change_floating_style(self.parent().isFloating())
        super(DockTitleBar, self).update(*args, **kwargs)

    def set_title(self, title):
        self._title_label.setText(title)
        self._title_edit.setText(title)

    def add_button(self, button):
        button.setAutoRaise(True)
        button.setMaximumSize(self._button_size)
        self._buttons_layout.insertWidget(5, button)

    def _start_edit(self):
        self._title_label.hide()
        self._title_edit.show()
        self._title_edit.setFocus()

    def _finish_edit(self):
        self._title_edit.hide()
        self._title_label.show()
        self.parent().setWindowTitle(self._title_edit.text())

    def _on_dock_features_changed(self, features):
        if not features & QDockWidget.DockWidgetVerticalTitleBar:
            self._close_btn.setVisible(features & QDockWidget.DockWidgetClosable)
            self._dock_btn.setVisible(features & QDockWidget.DockWidgetFloatable)
        else:
            raise ValueError('Vertical title bar is not supported!')

    def _on_finish_edit(self):
        self._finish_edit()

    def _on_dock_btn_clicked(self):
        self.parent().setFloating(not self.parent().isFloating())

    def _on_close_btn_clicked(self):
        self.parent().toggleViewAction().setChecked(False)
        self.parent().close()

    def _on_change_floating_style(self, state):
        pass


class PluginContextMenuGenerator(object):
    def __init__(self, menu_data_builder):
        super(PluginContextMenuGenerator, self).__init__()
        self._builder = menu_data_builder

    def build(self):
        menu_data = self._builder.get()
        menu = QMenu()
        for menu_entry in menu_data:
            self._create_menu_entry(menu, menu_entry)

        return menu

    def _create_menu_entry(self, parent_menu, menu_entry_data):
        if 'separator' in menu_entry_data:
            parent_menu.addSeparator()
            return
        icon = menu_entry_data['icon']
        if 'sub_menu' in menu_entry_data:
            sub_menu_data = menu_entry_data['sub_men']
            sub_menu = parent_menu.addMenu(menu_entry_data['title'])
            if icon:
                sub_menu.setIcon(icon)
            self._create_menu_entry(sub_menu, sub_menu_data)
        else:
            action = parent_menu.addAction(menu_entry_data['title'])
            if icon:
                action.setIcon(icon)
            action.triggered.connect(menu_entry_data['callback'])


def create_plugin_instance(plugin_class, already_registered_plugins=None, **kwargs):
    """
    Creates a tool instance of the given class
    :param plugin_class: cls
    :param already_registered_plugins: list
    :return:
    """

    if already_registered_plugins is None:
        already_registered_plugins = list()

    if not plugin_class:
        return

    is_singleton = plugin_class.IS_SINGLETON
    if is_singleton:
        if plugin_class.NAME in [t.NAME for t in already_registered_plugins]:
            for registered_plugin in already_registered_plugins:
                if registered_plugin.NAME == plugin_class.NAME:
                    registered_plugin.show()
                    registered_plugin.show_plugin()
                    return registered_plugin
            return None

    supported_softwares = plugin_class.SUPPORTED_SOFTWARES
    if 'any' not in supported_softwares:
        if dcc.name() not in supported_softwares:
            logger.warning(
                'Plugin {} is not suppported in current software: "{}"'.format(plugin_class.NAME, dcc.name()))
            return None

    # if python.is_python2():
    #     plugin_kwargs = inspect.getargspec(plugin_class.__init__)
    #     # plugin_kwargs = plugin_kwargs.keywords
    #     plugin_kwargs = plugin_kwargs.args
    # else:
    #     plugin_kwargs = inspect.signature(plugin_class.__init__)
    #     plugin_kwargs = plugin_kwargs.kwargs
    plugin_kwargs = inspect.getargspec(plugin_class.__init__)
    # plugin_kwargs = plugin_kwargs.keywords
    plugin_kwargs = plugin_kwargs.args
    if not plugin_kwargs:
        return plugin_class()

    valid_kwargs = dict()
    for kwarg_name, kwarg_value in kwargs.items():
        if kwarg_name in plugin_kwargs:
            valid_kwargs[kwarg_name] = kwarg_value
    if not valid_kwargs:
        return plugin_class()

    return plugin_class(**valid_kwargs)
