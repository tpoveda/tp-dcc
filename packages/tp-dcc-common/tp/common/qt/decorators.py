#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains decorators for Qt
"""

from functools import wraps

from Qt.QtCore import Qt
from Qt.QtWidgets import QApplication
from Qt.QtGui import QCursor


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
