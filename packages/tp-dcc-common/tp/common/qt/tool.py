#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create editor tools inside Qt apps
"""

from Qt.QtCore import Qt, QSize, QEvent
from Qt.QtWidgets import QWidget, QDockWidget, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QToolButton, QMenu

from tp.core import tool
from tp.core.managers import resources


class ShelfTool(tool.DccTool, object):
    def __init__(self):
        super(ShelfTool, self).__init__()

    @staticmethod
    def icon():
        return resources.icon('home')

    def context_menu_builder(self):
        return None

    def do(self):
        print(self.NAME, 'called!')


class DockTool(QDockWidget, tool.DccTool):

    DEFAULT_DOCK_AREA = Qt.LeftDockWidgetArea
    IS_SINGLETON = False

    def __init__(self):
        tool.DccTool.__init__(self)
        QDockWidget.__init__(self)

        self.setToolTip(self.TOOLTIP)
        self.setFeatures(QDockWidget.AllDockWidgetFeatures)
        self.setAllowedAreas(
            Qt.BottomDockWidgetArea | Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.TopDockWidgetArea)
        self.setObjectName(self.unique_name())
        self.setTitleBarWidget(DockTitleBar(self))
        self.setFloating(False)

    def restore_state(self, settings):
        super(DockTool, self).restore_state(settings)

        self.setObjectName(self.unique_name())

    def closeEvent(self, event):
        """
        Overrides base QDockWidget closeEvent function
        :param event: QEvent
        """

        self.close_tool()
        self.parent().unregister_tool_instance(self)
        event.accept()

    def add_button(self, button):
        self.titleBarWidget().add_button(button)

    def show_tool(self):
        """
        Overrides base DccTool _on_show function
        """

        super(DockTool, self).show_tool()
        self.setWindowTitle(self.NAME)


class DockTitleBar(QWidget, object):
    def __init__(self, dock_widget, renamable=False):
        super(DockTitleBar, self).__init__(dock_widget)

        self._renamable = renamable

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 1)
        self.setLayout(main_layout)

        self._buttons_box = QGroupBox('')
        self._buttons_box.setObjectName('Docked')
        self._buttons_layout = QHBoxLayout()
        self._buttons_layout.setSpacing(1)
        self._buttons_layout.setMargin(2)
        self._buttons_box.setLayout(self._buttons_layout)
        main_layout.addWidget(self._buttons_box)

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

    @property
    def renamable(self):
        return self._renamable

    @renamable.setter
    def renamable(self, flag):
        self._renamable = flag

    def eventFilter(self, obj, event):
        if event.type() == QEvent.WindowTitleChange:
            self.set_title(obj.windowTitle())
        return super(DockTitleBar, self).eventFilter(obj, event)

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


class ToolContextMenuGenerator(object):
    def __init__(self, menu_data_builder):
        super(ToolContextMenuGenerator, self).__init__()
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
