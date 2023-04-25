#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains widget used to handle theme related preferences (PreferencesWidget)
"""

from functools import partial

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QScrollArea
from Qt.QtGui import QColor, QPixmap, QIcon, QPainter

from tp.core.managers import resources
from tp.common.resources import color
from tp.common.qt import preferences
from tp.common.qt.widgets import layouts, accordion, comboboxes, labels, color as qt_color


class ThemePreferenceWidget(preferences.CategoryWidgetBase, object):
    """
    Widget used to handle theme related preferences (PreferencesWidget)
    """

    CATEGORY = 'Theme'

    def __init__(self, theme, parent=None):

        self._theme = theme
        self._original_options = self._theme.options().copy()
        self._color_buttons = list()

        super(ThemePreferenceWidget, self).__init__(parent=parent)

    def ui(self):
        super(ThemePreferenceWidget, self).ui()

        theme_accordion = accordion.AccordionWidget(parent=self)
        theme_accordion.rollout_style = accordion.AccordionStyle.SQUARE
        self.main_layout.addWidget(theme_accordion)

        theme_accordion.add_item('General', self._setup_general_tab(), icon=resources.icon('settings'))
        theme_accordion.add_item('Colors', self._setup_colors_tab(), True, icon=resources.icon('palette'))
        theme_accordion.add_item('Fonts', self._setup_fonts_tab(), True, icon=resources.icon('font_size'))

    def _setup_general_tab(self):
        general_widget = QWidget()
        general_layout = layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))
        general_widget.setLayout(general_layout)

        self._themes_combobox = combobox.BaseComboBox(parent=self)
        all_themes = resources.get_all_resources_of_type(resources.ResourceTypes.THEME)

        for i, theme in enumerate(all_themes):
            accent_color_hex = theme.accent_color
            accent_color = color.Color.hex_to_qcolor(
                accent_color_hex[1:] if accent_color_hex.startswith('#') else accent_color_hex)
            background_color_hex = theme.background_color
            background_color = color.Color.hex_to_qcolor(
                background_color_hex[1:] if accent_color_hex.startswith('#') else background_color_hex)
            accent_color_pixmap = QPixmap(25, 25)
            background_color_pixmap = QPixmap(25, 25)
            accent_color_pixmap.fill(accent_color)
            background_color_pixmap.fill(background_color)
            color_pixmap = QPixmap(50, 25)
            painter = QPainter(color_pixmap)
            painter.drawPixmap(0, 0, 25, 25, accent_color_pixmap)
            painter.drawPixmap(25, 0, 25, 25, background_color_pixmap)
            painter.end()

            color_icon = QIcon(color_pixmap)
            self._themes_combobox.addItem(color_icon, theme.name())

        general_layout.addWidget(self._themes_combobox)
        general_layout.addStretch()

        return general_widget

    def setup_signals(self):
        self._themes_combobox.currentIndexChanged.connect(self._on_current_theme_changed)

    def show_widget(self, settings):
        if not settings or not self._theme:
            return

        theme_settings = dict()
        attributes_to_load = self._theme.get_color_attribute_names()

        theme_name = settings.get('name', setting_group=self.CATEGORY)
        for attr_name in attributes_to_load:
            value = settings.get(attr_name, setting_group=self.CATEGORY)
            if not value:
                continue
            theme_settings[attr_name] = value

        if theme_name:
            self._theme.set_name(theme_name)
        self._theme.set_settings(theme_settings)

        self._update_color_buttons_color()

    def serialize(self, settings):
        if not settings or not self._theme:
            return

        theme_options = self._theme.options()
        attributes_to_save = self._theme.get_color_attribute_names()
        theme_name = self.theme().name()
        settings.set('name', theme_name)
        for attribute_to_save in attributes_to_save:
            if attribute_to_save not in theme_options:
                continue
            settings.set(attribute_to_save, theme_options[attribute_to_save])
        # settings.endGroup()

        return theme_options

    def reset(self):
        self._theme.set_settings(self._original_options)
        self._update_color_buttons_color()
        theme_name = self._theme.name()
        theme_index = self._themes_combobox.findText(theme_name)
        if theme_index == -1:
            return

        self._themes_combobox.blockSignals(True)
        try:
            self._themes_combobox.setCurrentIndex(theme_index)
        finally:
            self._themes_combobox.blockSignals(False)
        self._themes_combobox.repaint()
        self._themes_combobox.update()

    def _setup_colors_tab(self):
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        colors_widget = QWidget()
        colors_layout = layouts.GridLayout(spacing=2, margins=(2, 2, 2, 2))
        colors_layout.setAlignment(Qt.AlignTop)
        colors_widget.setLayout(colors_layout)
        scroll_area.setWidget(colors_widget)

        color_attribute_names = self._theme.get_color_attribute_names() or list()
        for i, color_attribute_name in enumerate(color_attribute_names):
            if not hasattr(self._theme, color_attribute_name):
                continue
            label, selector = self._add_color_widget(color_attribute_name, getattr(self._theme, color_attribute_name))
            colors_layout.addWidget(label, i, 0, Qt.AlignRight)
            colors_layout.addWidget(selector, i, 1)

        return scroll_area

    def _setup_fonts_tab(self):
        fonts_widget = QWidget()
        fonts_layout = layouts.VerticalLayout(spacing=2, margins=(2, 2, 2, 2))
        fonts_widget.setLayout(fonts_layout)

        return fonts_widget

    def _add_color_widget(self, color_name, color_value):
        color_label = label.BaseLabel('{}: '.format(color_name.replace('_', ' ').title()), parent=self)
        color_button = qt_color.ColorSelector(parent=self)
        color_button.setProperty('color_attribute', color_name)
        # color_button.setProperty('tooltip_help', {'title': 'Color', 'description': 'This is a color'})
        color_button.set_color(QColor(color_value))
        color_button.colorChanged.connect(partial(self._on_color_changed, color_name))
        self._color_buttons.append(color_button)

        return color_label, color_button

    def _update_color_buttons_color(self):
        if not self._color_buttons or not self._theme:
            return

        theme_name = self._theme.name()
        theme_index = self._themes_combobox.findText(theme_name)
        if theme_index > -1:
            self._themes_combobox.blockSignals(True)
            try:
                self._themes_combobox.setCurrentIndex(theme_index)
            finally:
                self._themes_combobox.blockSignals(False)

        for color_button in self._color_buttons:
            color_attribute = color_button.property('color_attribute')
            if not color_attribute:
                continue
            if hasattr(self._theme, color_attribute):
                color_button.blockSignals(True)
                try:
                    color_button.set_color(QColor(getattr(self._theme, color_attribute)))
                finally:
                    color_button.blockSignals(False)

    def _on_color_changed(self, property_name, new_color):
        if not self._theme:
            return

        hex_color = new_color.name()

        if hasattr(self._theme, property_name):
            setattr(self._theme, property_name, hex_color)
            self._theme.update()

    def _on_current_theme_changed(self, theme_index):

        theme_name = self._themes_combobox.itemText(theme_index)
        all_themes = resources.get_all_resources_of_type(resources.ResourceTypes.THEME)
        for theme_found in all_themes:
            if not theme_found or not theme_found.name() == theme_name:
                continue
            theme_options = theme_found.options()
            self._theme.set_name(theme_name)
            self._theme.set_settings(theme_options)
            self._update_color_buttons_color()
            break

        return True

    #                 "name": "accent_color",
    #                 "type": "color",
    #                 "value": accent_color,
    #                 "colors": [
    #                     "rgb(230, 80, 80, 255)",
    #                     "rgb(230, 125, 100, 255)",
    #                     "rgb(230, 120, 40)",
    #                     "rgb(240, 180, 0, 255)",
    #                     "rgb(80, 200, 140, 255)",
    #                     "rgb(50, 180, 240, 255)",
    #                     "rgb(110, 110, 240, 255)",
    #                 ]
    #                 "name": "background_color",
    #                 "type": "color",
    #                 "value": background_color,
    #                 "colors": [
    #                     "rgb(40, 40, 40)",
    #                     "rgb(68, 68, 68)",
    #                     "rgb(80, 60, 80)",
    #                     "rgb(85, 60, 60)",
    #                     "rgb(60, 75, 75)",
    #                     "rgb(60, 64, 79)",
    #                     "rgb(245, 245, 255)",
    #                 ]
