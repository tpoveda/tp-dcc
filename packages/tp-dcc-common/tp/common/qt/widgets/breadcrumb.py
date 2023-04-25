#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes to create breadcrumb widgets
"""

import os

from Qt.QtWidgets import QSizePolicy, QButtonGroup, QFrame

from tp.common.python import helpers, path
from tp.common.resources import theme
from tp.common.qt import mixin, base
from tp.common.qt.widgets import layouts, buttons, labels


class Breadcrumb(object):
    def __init__(self, label):
        """
        Constructor
        :param label: QLabel, label used in this breadcrumb
        """

        self._label = label

    @property
    def label(self):
        return self._label


@theme.mixin
class BreadcrumbWidget(base.BaseWidget, object):
    """
    Widget that display current location withing a hierarchy
    It allows going back/forward inside a hierarchy
    """

    def __init__(self, separator=None, parent=None):
        super(BreadcrumbWidget, self).__init__(parent=parent)

        current_theme = self.theme()

        separator_color = current_theme.accent_color if current_theme else '#E2AC2C'

        self._separator = separator or "<span style='color:{}'> &#9656; </span>".format(separator_color)
        self._separators = list()

        self.setObjectName('BreadcrumbWidget')
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

    def get_main_layout(self):
        main_layout = layouts.HorizontalLayout(spacing=0, margins=(0, 0, 0, 0))
        main_layout.addStretch()

        return main_layout

    def ui(self):
        super(BreadcrumbWidget, self).ui()

        self._button_group = QButtonGroup()

    def set_items(self, data_list):
        """
        Sets the the items of the breadcrumb cleaning old ones
        :param data_list:
        :return:
        """

        for btn in self._button_group.buttons():
            self._button_group.removeButton(btn)
            self.main_layout.removeWidget(btn)
            btn.setVisible(False)
            btn.deleteLater()
        for sep in self._separators:
            self.main_layout.removeWidget(sep)
            sep.setVisible(False)
            sep.deleteLater()
        helpers.clear_list(self._separators)

        for index, data_dict in enumerate(data_list):
            self.add_item(data_dict, index)

    def add_item(self, data_dict, index=None):
        """
        Adds a new item to the breadcrumb
        :param data_dict: dict
        :param index: int
        """

        btn = buttons.BaseToolButton()
        btn.setText(data_dict.get('text'))
        if data_dict.get('image'):
            btn.image(data_dict.get('image'))
        if data_dict.get('tooltip'):
            btn.setProperty('toolTip', data_dict.get('tooltip'))
        if data_dict.get('clicked'):
            btn.clicked.connect(data_dict.get('clicked'))
        if data_dict.get('text'):
            if data_dict.get('svg') or data_dict.get('icon'):
                btn.text_beside_icon()
            else:
                btn.text_only()
        else:
            btn.icon_only()

        if self._button_group.buttons():
            separator = label.BaseLabel(self._separator).secondary()
            self._separators.append(separator)
            self.main_layout.insertWidget(self.main_layout.count() - 1, separator)
        self.main_layout.insertWidget(self.main_layout.count() - 1, btn)

        if index is None:
            self._button_group.addButton(btn)
        else:
            self._button_group.addButton(btn, index)

    def set_from_path(self, file_path):
        """
        Creates a proper Breadcrumb list for given path and sets the text
        """

        self._widgets = list()
        file_path = os.path.dirname(file_path)
        folders = path.get_folders_from_path(file_path)
        data_list = list()
        for folder in folders:
            data_list.append({'text': folder})
        self.set_items(data_list)

    def get_breadcumbs(self):
        """
        Returns current list of breadcumb texts
        :return: list(str)
        """

        return [btn.text() for btn in self._button_group.buttons()]


class BreadcrumbFrame(QFrame, object):
    def __init__(self, separator=None, parent=None):
        super(BreadcrumbFrame, self).__init__(parent)

        self.setObjectName('TaskFrame')
        self.setFrameStyle(QFrame.StyledPanel)

        main_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
        self.setLayout(main_layout)

        self._breadcrumb = BreadcrumbWidget(separator=separator, parent=self)

        title_layout = layouts.HorizontalLayout()
        title_layout.addStretch()
        title_layout.addWidget(self._breadcrumb)
        title_layout.addStretch()

        main_layout.addLayout(title_layout)

    def set_items(self, data_list):
        """
        Sets the the items of the breadcrumb cleaning old ones
        :param data_list:
        :return:
        """

        self._breadcrumb.set_items(data_list)

    def set_from_path(self, file_path):
        """
        Creates a proper Breadcrumb list for given path and sets the text
        """

        self._breadcrumb.set_from_path(file_path)

    def get_breadcumbs(self):
        """
        Returns current
        :return: list(str)
        """

        return self._breadcrumb.get_breadcumbs()
