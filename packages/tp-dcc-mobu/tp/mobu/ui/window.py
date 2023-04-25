#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for MotionBuilder windows
"""

from tp.common.qt.widgets import window


class MobuWindow(window.MainWindow, object):
    def __init__(self, *args, **kwargs):
        # We make sure that window is not parented to Mobu window
        if 'parent' in kwargs:
            kwargs.pop('parent')
        super(MobuWindow, self).__init__(*args, **kwargs, parent=None)
