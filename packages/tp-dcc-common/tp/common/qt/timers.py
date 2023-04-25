#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different types of Qt timers
"""

from Qt.QtCore import Signal, QObject, QTimer


class ClickTimer(QObject, object):
    executed = Signal()

    def __init__(self):
        super(ClickTimer, self).__init__()
        self.timer_id = None
        self.init_data()

    def set_data(self, button, modifier, pos, selected):
        self.button = button
        self.modifiers = modifier
        self.pos = pos
        self.is_selected = selected

    def init_data(self):
        self.button = None
        self.modifiers = None
        self.pos = None
        self.is_selected = False

    def start(self, interval):
        self.timer_id = self.startTimer(interval)

    def remove_timer(self):
        if self.timer_id:
            self.killTimer(self.timer_id)
        self.timer_id = None
        return

    def timerEvent(self, event):
        if self.timer_id == event.timerId():
            self.executed.emit()
        self.remove_timer()


def defer(delay, fn, default_delay=1):
    """
    Append artificial delay to `func`
    This aids in keeping the GUI responsive, but complicates logic
    when producing tests. To combat this, the environment variable ensures
    that every operation is synchronous.
    :param delay: float, Delay multiplier; default 1, 0 means no delay
    :param fn: callable, Any callable
    :param default_delay: float
    """

    delay *= float(default_delay)
    if delay > 0:
        return QTimer.singleShot(delay, fn)
    else:
        return fn()
