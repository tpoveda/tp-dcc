#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widgets classes related with icons
"""

from functools import partial

from Qt.QtCore import Signal, QSize
from Qt.QtWidgets import QSizePolicy, QToolButton, QMenu

from tpDcc.managers import resources
from tpDcc.libs.qt.core import base
from tpDcc.libs.qt.widgets import layouts, buttons


class IconPickerButton(QToolButton):
    def __init__(self, *args, **kwargs):
        super(IconPickerButton, self).__init__(*args, **kwargs)

        self._icon_path = None
        self.setCheckable(True)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def icon_path(self):
        """
        Returns current button icon path
        :return: str
        """

        return self._icon_path

    def set_icon_path(self, icon_path):
        """
        Sets path for the icon button
        :param icon_path: str
        """

        self._icon_path = icon_path
        self.setToolTip(icon_path)
        self.setStatusTip(icon_path)
        icon = resources.icon(icon_path)
        self.setIcon(icon)


class IconPicker(base.BaseFrame):

    iconChanged = Signal(object)

    def __init__(self, *args, **kwargs):
        super(IconPicker, self).__init__(*args, **kwargs)

        self._buttons = list()
        self._current_icon = None
        self._menu_button = None

    # ============================================================================================================
    # OVERRIDES
    # ============================================================================================================

    def get_main_layout(self):
        return layouts.GridLayout(spacing=0, margins=(0, 0, 0, 0))

    def enterEvent(self, event):
        """
        Overrides base BaseFrame enterEvent function to fix a bug with custom actions
        :param event:
        :return:
        """
        if self.parent():
            menu = self.parent().parent()
            if isinstance(menu, QMenu):
                menu.setActiveAction(None)

    # ============================================================================================================
    # BASE
    # ============================================================================================================

    def menu_button(self):
        """
        Returns the menu button used for browsing custom icons
        :return: QWidget
        """

        return self._menu_button

    def current_icon(self):
        """
        Returns current icon
        :return: QIcon
        """

        return self._current_icon

    def set_current_icon(self, icon):
        """
        Sets the current icon
        :param icon: Icon
        """

        self._current_icon = icon
        self.refresh()

    def set_icons(self, icons):
        """
        Sets the icons
        :param icons: list(str) or list(Icon)
        :return:
        """

        self.delete_buttons()

        first = True
        last = False

        positions = [(i, j) for i in range(5) for j in range(5)]
        # positions = [(i, j) for i in range(1) for j in range(5)]
        for i, (position, icon_path) in enumerate(zip(positions, icons)):
            if i == len(icons) - 1:
                last = True
            icon_callback = partial(self._on_icon_changed, icon_path)
            icon_button = IconPickerButton(self)
            icon_button.set_icon_path(icon_path)
            icon_button.setIconSize(QSize(16, 16))
            icon_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            icon_button.setProperty('first', first)
            icon_button.setProperty('last', last)
            icon_button.clicked.connect(icon_callback)
            self.main_layout.addWidget(icon_button, *position)
            self._buttons.append(icon_button)
            first = False

        self._menu_button = buttons.BaseButton(parent=self)
        self._menu_button.setIcon(resources.icon('open'))
        self._menu_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._menu_button.clicked.connect(self.browse_icon)
        self.main_layout.addWidget(self._menu_button)
        # self.main_layout.addWidget(self._menu_button, 0, len(icons))
        self.refresh()

    def browse_icon(self):
        print('NOT IMPLEMENTED YET!')
        pass

    def refresh(self):
        """
        Updates the current state of the selected icon
        """

        for button in self._buttons:
            button.setChecked(button.icon_path() == self.current_icon())

    def delete_buttons(self):
        """
        Deletes all the icon buttons
        """

        main_layout = self.main_layout
        while main_layout.count():
            item = main_layout.takeAt(0)
            item_widget = item.widget()
            if item_widget:
                item_widget.deleteLater()

    # ============================================================================================================
    # CALLBACKS
    # ============================================================================================================

    def _on_icon_changed(self, icon_path):
        """
        Internal callback function that is triggered when user selects a new icon
        :param icon_path: str
        """

        self.set_current_icon(icon_path)
        self.iconChanged.emit(icon_path)
