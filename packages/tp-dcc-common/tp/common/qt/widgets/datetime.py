#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt date and time related widgets
"""

from Qt.QtCore import Property
from Qt.QtWidgets import QDateEdit, QTimeEdit, QDateTimeEdit

from tp.common.qt import mixin
from tp.common.resources import theme


@theme.mixin
# @mixin.cursor_mixin
class BaseDateTimeEdit(QDateTimeEdit, object):
    def __init__(self, parent=None):
        super(BaseDateTimeEdit, self).__init__(parent=parent)

        self._size = self.theme_default_size()

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns the date time edit height size
        :return: float
        """

        return self._size

    def _set_size(self, value):
        """
        Sets date time edit height size
        :param value: float
        """

        self._size = value
        self.style().polish(self)

    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def tiny(self):
        """
        Sets date time edit to tiny size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.tiny if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets date time edit to small size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets date time edit to medium size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets date time edit to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets date time edit to huge size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.huge if widget_theme else theme.Theme.Sizes.HUGE

        return self


@mixin.theme_mixin
# @mixin.cursor_mixin
class BaseDateEdit(QDateEdit, object):
    def __init__(self, parent=None):
        super(BaseDateEdit, self).__init__(parent=parent)

        self._size = self.theme_default_size()

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns the date edit height size
        :return: float
        """

        return self._size

    def _set_size(self, value):
        """
        Sets date edit height size
        :param value: float
        """

        self._size = value
        self.style().polish(self)

    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def tiny(self):
        """
        Sets date edit to tiny size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.tiny if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets date edit to small size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets date edit to medium size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets date edit to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets date edit to huge size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.huge if widget_theme else theme.Theme.Sizes.HUGE

        return self


@mixin.theme_mixin
# @mixin.cursor_mixin
class BaseTimeEdit(QTimeEdit, object):
    def __init__(self, parent=None):
        super(BaseTimeEdit, self).__init__(parent=parent)

        self._size = self.theme_default_size()

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns the time edit height size
        :return: float
        """

        return self._size

    def _set_size(self, value):
        """
        Sets time edit height size
        :param value: float
        """

        self._size = value
        self.style().polish(self)

    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def tiny(self):
        """
        Sets time edit to tiny size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.tiny if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets time edit to small size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets time edit to medium size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets time edit to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets time edit to huge size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.huge if widget_theme else theme.Theme.Sizes.HUGE

        return self
