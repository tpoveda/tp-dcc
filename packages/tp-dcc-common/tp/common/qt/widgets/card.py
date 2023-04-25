#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for card widgets
"""

from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QLabel

from tpDcc.libs.qt.core import base, mixin, theme
from tpDcc.libs.qt.widgets import layouts, label, avatar, buttons, dividers


@mixin.theme_mixin
# @mixin.cursor_mixin
class BaseCard(base.BaseWidget, object):
    def __init__(self, title=None, image=None, size=None, extra=None, type=None, parent=None):

        self._title = title
        self._size = size
        self._image = image
        self._extra = extra

        super(BaseCard, self).__init__(parent=parent)

        self.setAttribute(Qt.WA_StyledBackground)
        self.setProperty('border', False)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout(spacing=0, margins=(1, 1, 1, 1))

        return main_layout

    def ui(self):
        super(BaseCard, self).ui()

        widget_theme = self.theme()

        map_label = {
            widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL: (label.BaseLabel.Levels.H4, 10),
            widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM: (label.BaseLabel.Levels.H3, 15),
            widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE: (label.BaseLabel.Levels.H2, 20)
        }
        size = self._size or widget_theme.default if widget_theme else theme.Theme.Sizes.MEDIUM
        padding = map_label.get(size)[-1]

        self._title_layout = layouts.HorizontalLayout(margins=(padding, padding, padding, padding))
        self._title_label = label.BaseLabel(text=self._title, parent=self)
        self._title_label.level = map_label.get(size)[0]
        if self._image:
            self._title_icon = avatar.Avatar()
            self._title_icon.image = self._image
            self._title_icon.theme_size = size
            self._title_layout.addWidget(self._title_icon)
        self._title_layout.addWidget(self._title_label)
        self._title_layout.addStretch()
        if self._extra:
            self._extra_button = buttons.BaseToolButton(parent=self).image('more').icon_only()
            self._title_layout.addWidget(self._extra_button)

        self._content_layout = layouts.VerticalLayout()

        if self._title:
            self.main_layout.addLayout(self._title_layout)
            self.main_layout.addWidget(dividers.Divider())
        self.main_layout.addLayout(self._content_layout)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def get_more_button(self):
        """
        Returns more button
        :return: buttons.BaseToolButton
        """

        return self._extra_button

    def set_widget(self, widget):
        """
        Adds a new widget to the card contents layout
        :param widget: QWidget
        """

        self._content_layout.addWidget(widget)

    def border(self):
        """
        Enables card border style
        :return: self
        """

        self.setProperty('border', True)
        self.style().polish(self)

        return self


# @mixin.cursor_mixin
class MetaCard(base.BaseWidget, object):
    def __init__(self, extra=False, parent=None):

        self._extra = extra

        super(MetaCard, self).__init__(parent=parent)

        self.setAttribute(Qt.WA_StyledBackground)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def get_main_layout(self):
        main_layout = layouts.VerticalLayout(spacing=0, margins=(1, 1, 1, 1))

        return main_layout

    def ui(self):
        super(MetaCard, self).ui()

        self._title_layout = layouts.HorizontalLayout()
        self._cover_label = QLabel()
        self._cover_label.setFixedSize(QSize(200, 200))
        self._avatar = avatar.Avatar()
        self._title_label = label.BaseLabel().h4()
        self._description_label = label.BaseLabel().secondary()
        self._description_label.setWordWrap(True)
        self._description_label.theme_elide_mode = Qt.ElideRight
        self._extra_btn = buttons.BaseToolButton(parent=self).image('more').icon_only()
        self._title_layout.addWidget(self._title_label)
        self._title_layout.addStretch()
        self._title_layout.addWidget(self._extra_btn)
        self._extra_btn.setVisible(self._extra)

        content_lyt = layouts.FormLayout(margins=(5, 5, 5, 5))
        content_lyt.addRow(self._avatar, self._title_layout)
        content_lyt.addRow(self._description_label)
        self._btn_lyt = layouts.HorizontalLayout()

        self.main_layout.addWidget(self._cover_label)
        self.main_layout.addLayout(content_lyt)
        self.main_layout.addLayout(self._btn_lyt)
        self.main_layout.addStretch()

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def get_more_button(self):
        """
        Returns more button
        :return: buttons.BaseToolButton
        """

        return self._extra_button

    def setup_data(self, data_dict):
        if data_dict.get('title'):
            self._title_label.setText(data_dict.get('title'))
            self._title_label.setVisible(True)
        else:
            self._title_label.setVisible(False)

        if data_dict.get('description'):
            self._description_label.setText(data_dict.get('description'))
            self._description_label.setVisible(True)
        else:
            self._description_label.setVisible(False)

        if data_dict.get('avatar'):
            self._avatar.image = data_dict.get('avatar')
            self._avatar.setVisible(True)
        else:
            self._avatar.setVisible(False)

        if data_dict.get('cover'):
            fixed_height = self._cover_label.width()
            self._cover_label.setPixmap(data_dict.get('cover').scaledToWidth(fixed_height, Qt.SmoothTransformation))
            self._cover_label.setVisible(True)
        else:
            self._cover_label.setVisible(False)
