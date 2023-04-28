#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains custom Dcc progress bar classes
"""

from tp.core import dcc
from tp.core.abstract import progressbar as abstract_progressbar
from tp.common.python import decorators


class _MetaProgressBar(type):

    def __call__(cls, *args, **kwargs):
        as_class = kwargs.pop('as_class', False)
        if dcc.is_maya():
            from tp.maya.ui import progress
            if as_class:
                return progress.MayaProgressBar
            else:
                return type.__call__(progress.MayaProgressBar, *args, **kwargs)
        else:
            if as_class:
                return BaseProgressBar
            else:
                return type.__call__(BaseProgressBar, *args, **kwargs)


class BaseProgressBar(abstract_progressbar.AbstractProgressBar):

    ERROR_STATUS = 'error'
    NORMAL_STATUS = 'primary'
    SUCCESS_STATUS = 'success'
    WARNING_STATUS = 'warning'

    inc_value = 0

    def __init__(self, *args, **kwargs):
        self.progress_ui = None

    def set_count(self, count_number):
        pass

    def get_count(self):
        return 0

    def status(self, status_str):
        pass

    def end(self):
        pass

    def break_signaled(self):
        pass

    def set_progress(self, value):
        pass

    def inc(self, inc=1):
        self.__class__.inc_value += inc


@decorators.add_metaclass(_MetaProgressBar)
class ProgressBar(abstract_progressbar.AbstractProgressBar, object):
    pass
