#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains contexts for Qt
"""

import sys
import contextlib

from Qt.QtWidgets import QApplication, QWidget

from tp.core import dcc
from tp.common.qt import qtutils


@contextlib.contextmanager
def application():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        yield app
        app.exec_()
    else:
        yield app
        if dcc.is_standalone():
            app.exec_()


@contextlib.contextmanager
def block_signals(widget, children=False):
    widget.blockSignals(True)
    child_widgets = widget.findChildren(QWidget) if children else list()
    for child_widget in child_widgets:
        child_widget.blockSignals(True)
    try:
        yield widget
    finally:
        widget.blockSignals(False)
        for child_widget in child_widgets:
            child_widget.blockSignals(False)


@contextlib.contextmanager
def show_window(widget):

    from tp.core import window

    with application():
        new_window = window.Window()
        new_window.main_layout.addWidget(widget)
        new_window.adjustSize()
        new_window.show()
        yield new_window


@contextlib.contextmanager
def waiting_cursor():
    """
    Custom Python context manager that allow to enable waiting cursor while a function is being processed.
    """

    qtutils.set_cursor(Qt.WaitCursor)
    try:
        yield
    finally:
        qtutils.set_cursor(Qt.ArrowCursor)
