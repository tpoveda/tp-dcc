#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for page widgets
"""

import math
from functools import partial

from Qt.QtCore import Qt, Signal

from tpDcc.libs.qt.core import mixin, base, menu, theme
from tpDcc.libs.qt.widgets import layouts, label, buttons, combobox, spinbox


@mixin.theme_mixin
class Page(base.BaseWidget, mixin.FieldMixin):
    """
    Widget that allows to divide long list of items in several pages.
    Only one page will be loaded at a time
    """

    pageChanged = Signal(int, int)

    def __init__(self, parent=None):
        super(Page, self).__init__(parent=parent)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(Page, self).ui()

        current_theme = self.theme()

        self._page_setting_menu = menu.BaseMenu(parent=self)

        self._display_label = label.BaseLabel()
        self._display_label.setAlignment(Qt.AlignCenter)
        self._change_page_size_btn = combobox.BaseComboBox().small()
        self._change_page_size_btn.setFixedWidth(110)
        self._change_page_size_btn.set_menu(self._page_setting_menu)
        self._change_page_size_btn.set_formatter(lambda x: '{} per page'.format(x))

        self._pre_btn = buttons.BaseToolButton().image('arrow_left').icon_only().small()
        self._next_btn = buttons.BaseToolButton().image('arrow_right').icon_only().small()
        self._current_page_spin_box = spinbox.BaseSpinBox()
        self._current_page_spin_box.setMinimum(1)
        self._current_page_spin_box.theme_size = current_theme.small if current_theme else theme.Theme.Sizes.SMALL
        self._total_page_lbl = label.BaseLabel()

        self.main_layout.addStretch()
        self.main_layout.addWidget(self._display_label)
        self.main_layout.addStretch()
        self.main_layout.addWidget(label.BaseLabel('|').secondary())
        self.main_layout.addWidget(self._change_page_size_btn)
        self.main_layout.addWidget(label.BaseLabel('|').secondary())
        self.main_layout.addWidget(self._pre_btn)
        self.main_layout.addWidget(label.BaseLabel('Page'))
        self.main_layout.addWidget(self._current_page_spin_box)
        self.main_layout.addWidget(label.BaseLabel('/'))
        self.main_layout.addWidget(self._total_page_lbl)
        self.main_layout.addWidget(self._next_btn)

    def setup_signals(self):

        self.register_field('page_size_selected', 25)
        self.register_field('page_size_list', [
            {'label': '25 - Fastest', 'value': 25},
            {'label': '50 - Fast', 'value': 50},
            {'label': '75 - Medium', 'value': 75},
            {'label': '100 - Slow', 'value': 100},
        ])
        self.register_field('total', 0)
        self.register_field('current_page', 0)
        self.register_field('total_page', lambda: self._get_total_pages(
            self.field('total'), self.field('page_size_selected')))
        self.register_field('total_page_text', lambda: str(self.field('total_page')))
        self.register_field('display_text', lambda: self._get_page_display_string(
            self.field('current_page'), self.field('page_size_selected'), self.field('total')))
        self.register_field('can_pre', lambda: self.field('current_page') > 1)
        self.register_field('can_next', lambda: self.field('current_page') < self.field('total_page'))

        self._change_page_size_btn.valueChanged.connect(self._on_page_changed)
        self._current_page_spin_box.valueChanged.connect(self._on_page_changed)
        self._pre_btn.clicked.connect(partial(self._on_change_current_page, -1))
        self._next_btn.clicked.connect(partial(self._on_change_current_page, 1))

        self.bind('page_size_list', self._page_setting_menu, 'data')
        self.bind('page_size_selected', self._page_setting_menu, 'value', signal='valueChanged')
        self.bind('page_size_selected', self._change_page_size_btn, 'value', signal='valueChanged')
        self.bind('current_page', self._current_page_spin_box, 'value', signal='valueChanged')
        self.bind('total_page', self._current_page_spin_box, 'maximum')
        self.bind('total_page_text', self._total_page_lbl, 'label_text')
        self.bind('display_text', self._display_label, 'label_text')
        self.bind('can_pre', self._pre_btn, 'enabled')
        self.bind('can_next', self._next_btn, 'enabled')

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def set_total(self, value):
        """
        Sets the total amount of pages
        :param value: int
        """

        self.set_field('total', value)
        self.set_field('current_page', 1)

    def set_page_config(self, data_list):
        """
        Sets page component per page settings
        :param data_list: list(dict)
        """

        self.set_field('page_size_list', [
            {'label': str(data), 'value': data} if isinstance(data, int) else data for data in data_list])

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _get_total_pages(self, total, count_per_page):
        """
        Internal function that returns the total amount of pages available
        :param total: int
        :param count_per_page: int
        :return: int
        """

        return int(math.ceil(1.0 * total / count_per_page))

    def _get_page_display_string(self, current, count_per_page, total):
        """
        Returns the page string in proper format (x - x of xx)
        :param current: int
        :param count_per_page: int
        :param total: int
        :return: str
        """

        return '{} - {} of {}'.format(
            (current - 1) * count_per_page + 1 if current else 0, min(total, current * count_per_page), total)

    # =================================================================================================================
    # CALLBACKS
    # =================================================================================================================

    def _on_change_current_page(self, offset):
        """
        Internal callback function that is called when a page is changed
        :param offset: int
        """

        self.set_field('current_page', self.field('current_page') + offset)
        self._on_page_changed()

    def _on_page_changed(self):
        """
        Internal callback function that is called when a page is changed. Emits pageChanged signal.
        """

        self.pageChanged.emit(self.field('page_size_selected'), self.field('current_page'))
