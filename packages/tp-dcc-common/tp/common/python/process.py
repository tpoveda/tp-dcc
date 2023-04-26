#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that functions to retrieve info from running processes
"""

import threading

from tp.core import log

PSUTIL_AVAILABLE = True
try:
    import psutil
except Exception:
    PSUTIL_AVAILABLE = False

logger = log.tpLogger


def check_if_process_is_running(process_name):
    """
    Returns whether a process with given name is running.

    :param str process_name: name of the process we want to check.
    :return: True if a process with given name is running; False otherwise.
    :rtype: bool
    """

    if not PSUTIL_AVAILABLE:
        logger.warning(
            'Impossible to run "check_if_process_is_running" function because psutil module is not available!')
        return False

    for process in psutil.process_iter():
        try:
            if process_name.lower() in process.name().lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    return False


def processes_by_name(process_name):
    """
    Returns a list with all running processes with given name.

    :param str process_name: name of the process to retrieve.
    :return: list of found processes with given name.
    :rtype: list
    """

    if not PSUTIL_AVAILABLE:
        logger.warning('Impossible to run "get_processes_by_name" function because psutil module is not available!')
        return False

    return [process for process in psutil.process_iter() if process_name.lower() == process.name().lower()]


def kill_processes_by_name(process_name):
    """
    Kill processes with given name.

    :param str process_name: name of th process to kill.
    :return: True if process was killed; False otherwise.
    :rtype: bool
    """

    if not PSUTIL_AVAILABLE:
        logger.warning('Impossible to run "kill_process_by_name" function because psutil module is not available!')
        return False

    found_processes = processes_by_name(process_name)
    if not found_processes:
        return False

    for found_process in found_processes:
        found_process.kill()

    return True


def current_process_name():
    """
    Returns the name of the current process.

    :return: current process name.
    :rtype: str
    """

    if not PSUTIL_AVAILABLE:
        logger.warning(
            'Impossible to run "get_current_process_name" function because psutil module is not available!')
        return ''

    return psutil.Process().name()


def cpu_threading(fn):
    """
    Runs a function on a separate CPU thread.

    :param callable fn: Threaded function.
    """

    t = threading.Thread(target=fn)
    t.start()

