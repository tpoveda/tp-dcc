#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementations for Signal
"""


class Signal(object):
    """
    Simple single emission mechanism to allow for events withing functions to trigger mid-call callbacks
    """

    def __init__(self):
        self._callables = list()

    def connect(self, item):
        self._callables.append(item)

    def emit(self, *args, **kwargs):
        for item in self._callables:
            item(*args, **kwargs)
