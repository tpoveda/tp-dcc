#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains decorators for Qt
"""

import sys
import traceback
from functools import wraps

from Qt.QtCore import Qt
from Qt.QtWidgets import QApplication
from Qt.QtGui import QCursor

from tp.core import dcc

if dcc.is_maya():
    import maya.cmds as cmds


def show_wait_cursor(fn):
    """
    Decorator that shows wait cursor during function execution
    :param fn:
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        cursor = QCursor(Qt.WaitCursor)
        QApplication.setOverrideCursor(cursor)
        try:
            return fn(*args, **kwargs)
        finally:
            QApplication.restoreOverrideCursor()

    return wrapper


def show_arrow_cursor(fn):
    """
    Decorator that shows arrow cursor during function execution
    :param fn:
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        cursor = QCursor(Qt.ArrowCursor)
        QApplication.setOverrideCursor(cursor)
        try:
            return fn(*args, **kwargs)
        finally:
            QApplication.restoreOverrideCursor()

    return wrapper


def show_error_on_slot_function(fn):
    """
    Decorators to wrap Qt slots in some DCCs (such as Maya) so exceptions are reported to script editor.
    :param fn:
    :return:
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except:
            error_type, error, tb = sys.exc_info()
            tb = tb[1:]  # pop this current wrapper from info
            lines = traceback.format_exception_only(error_type, error)
            lines.extend(traceback.format_list(tb))
            err = "Exception occurred in Qt slot:\n%s" % ''.join(lines)
            if dcc.is_maya():
                cmds.warning(err, noContext=True)

    return wrapper
