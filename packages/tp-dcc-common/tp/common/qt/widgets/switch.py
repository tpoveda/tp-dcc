#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for switch widget
"""

from Qt.QtCore import Property, QSize
from Qt.QtWidgets import QRadioButton

from tpDcc.libs.resources.core import theme


@theme.mixin
# @mixin.cursor_mixin
class SwitchWidget(QRadioButton, object):
    def __init__(self, parent=None):
        super(SwitchWidget, self).__init__(parent)

        self._size = self.theme_default_size()

        self.setAutoExclusive(False)

    # =================================================================================================================
    # PROPERTIES
    # =================================================================================================================

    def _get_size(self):
        """
        Returns switch size
        :return: float
        """

        return self._size

    def _set_size(self, value):
        """
        Sets switch size
        :param value: float
        """

        self._size = value
        self.style().polish(self)

    theme_size = Property(int, _get_size, _set_size)

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def minimumSizeHint(self):
        """
        Overrides base QRadioButton minimumSizeHint functino
        We do not need text space
        :return: QSize
        """

        height = self._size * 1.2
        return QSize(height, height / 2)

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def tiny(self):
        """
        Sets button to tiny size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.tiny if widget_theme else theme.Theme.Sizes.TINY

        return self

    def small(self):
        """
        Sets button to small size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.small if widget_theme else theme.Theme.Sizes.SMALL

        return self

    def medium(self):
        """
        Sets button to medium size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.medium if widget_theme else theme.Theme.Sizes.MEDIUM

        return self

    def large(self):
        """
        Sets button to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.large if widget_theme else theme.Theme.Sizes.LARGE

        return self

    def huge(self):
        """
        Sets button to large size
        """

        widget_theme = self.theme()
        self.theme_size = widget_theme.huge if widget_theme else theme.Theme.Sizes.HUGE

        return self
