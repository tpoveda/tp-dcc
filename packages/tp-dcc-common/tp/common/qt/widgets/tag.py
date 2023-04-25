#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Qt tag widgets
"""

from Qt.QtCore import Signal
from Qt.QtWidgets import QLabel


class Tag(QLabel, object):
    closed = Signal()
    clicked = Signal()

    def __init__(self, text='', parent=None):
        super(Tag, self).__init__(text=text, parent=parent)

        self._is_pressed = False
