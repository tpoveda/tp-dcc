#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for preferences window
"""

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QSizePolicy, QWidget, QSplitter, QScrollArea

from tp.core.managers import resources
from tp.common.qt import base
from tp.common.qt.widgets import layouts, stack, buttons, dividers


class PreferencesWidget(base.BaseWidget, object):

    closed = Signal(bool, dict)

    def __init__(self, settings=None, parent=None):
        self._settings = settings
        super(PreferencesWidget, self).__init__(
            parent=parent
        )

        self._indexes = dict()
        self._category_buttons = dict()
        self._settings = settings

        self._try_create_defaults()

    def ui(self):
        super(PreferencesWidget, self).ui()

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._splitter = QSplitter()
        self._splitter.setOrientation(Qt.Horizontal)
        self._splitter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # self._scroll_area.setMinimumWidth(200)
        self._scroll_area_widget_contents = QWidget()
        # self._scroll_area_widget_contents.setGeometry(QRect(0, 0, 480, 595))
        self._scroll_area_layout = layouts.VerticalLayout(spacing=2, margins=(1, 1, 1, 1))
        self._scroll_area_layout.setAlignment(Qt.AlignTop)
        self._scroll_area_widget_contents.setLayout(self._scroll_area_layout)
        self._categories_layout = layouts.VerticalLayout()
        self._stack = stack.SlidingStackedWidget()
        self._stack.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._stack.set_vertical_mode()
        self._buttons_layout = layouts.HorizontalLayout(spacing=1, margins=(0, 0, 0, 0))
        self._save_prefs_close_btn = buttons.BaseButton(
            'Save and Close', icon=resources.icon('save'), parent=self)
        self._close_btn = buttons.BaseButton('Close', icon=resources.icon('cancel'), parent=self)

        self._buttons_layout.addStretch()
        self._buttons_layout.addWidget(self._save_prefs_close_btn)
        self._buttons_layout.addWidget(self._close_btn)
        self._scroll_area_layout.addLayout(self._categories_layout)
        self._scroll_area.setWidget(self._scroll_area_widget_contents)
        self._splitter.addWidget(self._scroll_area)
        self._splitter.addWidget(self._stack)
        self._splitter.setSizes([150, 450])

        self.main_layout.addWidget(self._splitter)
        self.main_layout.addWidget(dividers.Divider(parent=self))
        self.main_layout.addLayout(self._buttons_layout)

    def setup_signals(self):
        self._save_prefs_close_btn.clicked.connect(self._on_save_and_close_prefs)
        self._close_btn.clicked.connect(self._on_close)

    def showEvent(self, event):
        settings = self.settings()
        if not settings:
            return

        groups = settings.childGroups()
        for name, index_widget in self._indexes.items():
            index, widget = index_widget
            settings.beginGroup(name)
            if name not in groups:
                widget.init_defaults(settings)
            widget.show_widget(settings)
            settings.endGroup()

    def settings(self):
        return self._settings

    def set_settings(self, settings):
        if not settings:
            return
        self._settings = settings
        self._try_create_defaults()

    def add_category(self, name, widget):
        category_button = CategoryButton(text=name, parent=self)
        self._categories_layout.insertWidget(self._categories_layout.count() - 2, category_button)
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        index = self._stack.addWidget(widget)
        self._indexes[name] = (index, widget)
        self._category_buttons[index] = category_button
        category_button.clicked.connect(lambda checked=False, idx=index: self._on_switch_category_content(idx))
        widget.init_defaults(settings=self.settings())
        self.closed.connect(widget._on_reset)

    def select_by_name(self, name):
        if name not in self._indexes:
            return
        index = self._indexes[name][0]
        self._stack.setCurrentIndex(index)
        self._category_buttons[index].setChecked(True)

    def _try_create_defaults(self):
        settings = self.settings()
        if not settings:
            return

        groups = settings.childGroups()
        for name, index_widget in self._indexes.items():
            index, widget = index_widget
            init_defaults = False
            if name not in groups:
                init_defaults = True
            settings.beginGroup(name)
            if init_defaults:
                widget.init_defaults(settings)
            settings.endGroup()
        settings.sync()

    def _on_switch_category_content(self, index):
        self._stack.slide_in_index(index)
        self._category_buttons[index].toggle()

    def _on_save_prefs(self):
        settings = self.settings()
        if not settings:
            return

        stored_data = dict()

        for name, index_widget in self._indexes.items():
            index, widget = index_widget
            settings.beginGroup(name)
            data = widget.serialize(settings)
            if data:
                stored_data[name] = data
            settings.endGroup()
        settings.sync()

        return stored_data

    def _on_save_and_close_prefs(self):
        stored_data = self._on_save_prefs()
        self.closed.emit(True, stored_data)

    def _on_close(self):
        self.closed.emit(False, None)


class CategoryButton(buttons.BaseButton, object):
    def __init__(self, icon=None, text='test', parent=None):
        super(CategoryButton, self).__init__(text=text, icon=icon, parent=parent)
        self.setMinimumHeight(30)
        self.setCheckable(True)
        self.setAutoExclusive(True)


class CategoryWidgetBase(base.BaseWidget, object):

    CATEGORY = 'GeneralPrefs'

    def __init__(self, parent=None):
        super(CategoryWidgetBase, self).__init__(parent)

    def init_defaults(self, settings):
        pass

    def serialize(self, settings):
        pass

    def reset(self):
        pass

    def show_widget(self, settings):
        pass

    def _on_reset(self, flag, *args):
        if flag:
            return
        self.reset()
