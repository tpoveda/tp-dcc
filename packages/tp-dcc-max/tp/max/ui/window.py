#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for 3ds Max windows
"""

from tp.common.qt.widgets import window


class MaxWindow(window.MainWindow, object):
    def __init__(self, *args, **kwargs):
        super(MaxWindow, self).__init__(*args, **kwargs)
