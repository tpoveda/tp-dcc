#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract definition of basic DCC progress bar
"""

from tp.common.python import decorators


class AbstractProgressBar(object):

    @decorators.abstractmethod
    def set_count(self, count_number):
        pass

    @decorators.abstractmethod
    def get_count(self):
        return 0

    @decorators.abstractmethod
    def status(self, status_str):
        pass

    @decorators.abstractmethod
    def end(self):
        pass

    @decorators.abstractmethod
    def break_signaled(self):
        pass

    @decorators.abstractmethod
    def set_progress(self, value):
        pass

    @decorators.abstractmethod
    def inc(self, inc=1):
        pass
