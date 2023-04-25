#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that functions to retrieve info from running processes
"""

from tp.core import log

PSUTIL_AVAILABLE = True
try:
    import psutil
except Exception:
    PSUTIL_AVAILABLE = False

logger = log.tpLogger


def check_if_process_is_running(process_name):
    """
    Returns whether or not a process with given name is running
    :param process_name: str
    :return: bool
    """

    if not PSUTIL_AVAILABLE:
        logger.warning(
            'Impossible to check is process "{}" is running because psutil is not available!'.format(process_name))
        return False

    for process in psutil.process_iter():
        try:
            if process_name.lower() in process.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False
