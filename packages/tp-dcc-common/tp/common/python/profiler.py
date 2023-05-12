#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to profile Python code
"""

import os
import time
import pstats
import timeit
import cProfile as profile
from functools import wraps
from collections import defaultdict

from tp.core import log
from tp.common.python import folder

logger = log.tpLogger


def profile_function(sort_key='time', rows=30):
    def _(fn):
        @wraps(_)
        def __(*fargs, **fkwargs):
            prof = profile.Profile()
            ret = prof.runcall(fn, *fargs, **fkwargs)
            pstats.Stats(prof).strip_dirs().sort_stats(sort_key).print_stats(rows)
            return ret
        return __
    return _


def profile_it(file_path):
    """
    cProfile decorator to profile a function by passing a valid file to write the information into.

    :param str file_path: file path to store profile information into.
    """

    def inner(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            prof = profile.Profile()
            result = prof.runcall(fn, *args, **kwargs)
            abs_path = os.path.expanduser(os.path.expandvars(file_path))
            folder.ensure_folder_exists(os.path.dirname(abs_path))
            prof.dump_stats(abs_path)
            return result
        return wrapper
    return inner


def fn_timer(fn):
    def function_timer(*args, **kwargs):
        t0 = timeit.default_timer()
        result = fn(*args, **kwargs)
        t1 = timeit.default_timer()
        logger.debug('Total time running {}: {} seconds'.format(
            '.'.join((fn.__module__, fn.__name__)), str(t1 - t0)))
        return result

    return function_timer


class LapCounter(object):
    LapTimes = 0
    LapList = list()

    def __init__(self):
        current_time = time.time()
        self._all_start = current_time
        self._start = current_time
        self._end = current_time

    def count(self, string=''):
        self._end = time.time()
        lap_str = 'lap_time : ', string, self.LapTimes, ':', self._end - self._start
        self.LapList.append(lap_str)
        self.LapTimes += 1
        self._start = time.time()

    def lap_print(self, print_flag=True, window=None):
        total_time = time.time() - self._all_start
        if window:
            out_time = '{:.5f}'.format(total_time)
            try:
                window.time_label.setText('- Calculation Time - ' + out_time + ' sec')
            except Exception as e:
                pass

        if print_flag:
            print('----------------------------------')
            for lap_time in self.LapList:
                print(lap_time)
            print('Total time : {}'.format(total_time))

    def reset(self):
        self._all_start = time.time()
        self._start = time.time()
        self.LapList = list()


class IntegrationCounter(object):
    def __init__(self):
        current_time = time.time()
        self._all_start = current_time
        self._start = current_time
        self._end = current_time
        self._integration_dict = defaultdict(lambda: 0)

    def count(self, string=''):
        self._end = time.time()
        self._integration_dict[string] += self._end - self._start
        self._start = time.time()

    def integration_print(self):
        for string, integration in self._integration_dict.items():
            print('Integration time : ', string, integration)

    def reset(self):
        self._all_start = time.time()
        self._start = time.time()
        self._integration_dict = defaultdict(lambda: 0)
