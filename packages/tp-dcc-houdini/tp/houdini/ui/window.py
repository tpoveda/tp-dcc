#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functionality for Houdini windows
"""

from __future__ import print_function, division, absolute_import

from tpDcc.libs.qt.widgets import window


class HoudiniWindow(window.BaseWindow, object):
    def __init__(self, *args, **kwargs):
        super(HoudiniWindow, self).__init__(*args, **kwargs)
