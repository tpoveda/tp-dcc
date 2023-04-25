#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for avatar/user widgets
"""

from Qt.QtCore import Qt, Property
from Qt.QtWidgets import QSizePolicy, QPushButton

from tp.common.qt import base, formatters
from tp.common.qt.widgets import layouts


class Badge(base.BaseWidget, object):
    """
    Widget that can be located near notification or user avatars to display unread messages count
    We support 3 types of styles:
        1. dof: show a dot
        2. count: show a number
        3. text: show a string
    """

    def __init__(self, widget=None, parent=None):

        self._dot = None
        self._text = None
        self._count = None
        self._widget = widget
        self._overflow_count = 99

        super(Badge, self).__init__(parent=parent)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    @property
    def overflow(self):
        """
        Returns current overflow number
        :return: int
        """

        return self._overflow_count

    @overflow.setter
    def overflow(self, value):
        """
        Sets overflow number
        :param value: int
        """

        self._overflow_count = value
        self._update_number()

    @property
    def count(self):
        """
        Returns current badge count number
        :return: int
        """

        return self._count

    @count.setter
    def count(self, value):
        """
        Sets current badge count number
        :param value: int
        """

        self._count = value
        self._update_number()

    @property
    def text(self):
        """
        Returns current badge text
        :return: str
        """

        return self._text

    @text.setter
    def text(self, value):
        """
        Sets current badge text
        :param value: str
        """

        self._text = value
        self._badge_btn.setText(self._text)
        self._badge_btn.setVisible(bool(self._text))
        self._dot = None
        self.style().polish(self)

    def _get_dot(self):
        """
        Returns whether or not current badge style is dot
        :return: bool
        """

        return self._dot

    def _set_dot(self, flag):
        """
        Sets whether or not current badge style is dot
        :param flag: bool
        """

        self._dot = flag
        self._badge_btn.setText('')
        self._badge_btn.setVisible(flag)
        self.style().polish(self)

    dot = Property(bool, _get_dot, _set_dot)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def get_main_layout(self):
        main_layout = layouts.GridLayout(margins=(0, 0, 0, 0))

        return main_layout

    def ui(self):
        super(Badge, self).ui()

        self._badge_btn = QPushButton()
        self._badge_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

        if self._widget is not None:
            self.main_layout.addWidget(self._widget, 0, 0)
        self.main_layout.addWidget(self._badge_btn, 0, 0, Qt.AlignTop | Qt.AlignRight)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    @classmethod
    def create_dot(cls, show=False, widget=None, parent=None):
        """
        Creates a new badge with dot style
        :param show: bool
        :param widget: QWidget
        :param parent: QWidget
        :return: Badge
        """

        inst = cls(widget=widget, parent=parent)
        inst.dot = show

        return inst

    @classmethod
    def create_count(cls, count=0, widget=None, parent=None):
        """
        Creates a new badge with count style
        :param count: int
        :param widget: QWidget
        :param parent: QWidget
        :return: Badge
        """

        inst = cls(widget=widget, parent=parent)
        inst.count = count

        return inst

    @classmethod
    def create_text(cls, text='', widget=None, parent=None):
        """
        Creates a new badge with dot style
        :param text: str
        :param widget: QWidget
        :param parent: QWidget
        :return: Badge
        """

        inst = cls(widget=widget, parent=parent)
        inst.text = text

        return inst

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _update_number(self):
        """
        Internal function that updates overflow number
        """

        self._badge_btn.setText(formatters.overflow_format(self._count, self._overflow_count))
        self._badge_btn.setVisible(self._count > 0)
        self._dot = None
        self.style().polish(self)
