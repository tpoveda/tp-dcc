#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC functionality for standalone applications
"""

from __future__ import annotations

from typing import List, Callable, Any

from tp.core import log, dccs

logger = log.tpLogger


# ======================================================================================================================
# GENERAL
# ======================================================================================================================

def name() -> str:
    """
    Returns the name of the DCC.

    :return: DCC name ('maya', 'mobu', ...).
    :rtype: str
    """

    return dccs.Standalone


def file_extensions() -> List[str]:
    """
    Returns supported file extensions of the DCC.

    :return: list of DCC file extensions (['.mb', '.ma'], ['.max'], ...).
    :rtype: List[str]
    """

    return []


def version() -> int | float:
    """
    Returns integer version of the DCC.

    :return: DCC version (2022, 2023.5, ...).
    :rtype: int or float
    """

    return 0


def version_name() -> str:
    """
    Returns name version of the DCC.

    :return: DCC version ('2022', '2023.5', ...).
    :rtype: str
    """

    return '0.0.0'


def is_batch() -> bool:
    """
    Returns whether DCC is being executed in batch mode.

    :return: True if DCC is being executed in batch mode; False otherwise.
    :rtype: bool
    """

    return False


def execute_deferred(fn: Callable) -> Any:
    """
    Executes given function in deferred mode

    :param Callable fn: function to defer execution of.
    :return: function result.
    :rtype: Any
    """

    return fn()


def deferred_function(fn, *args, **kwargs) -> Any:
    """
    Calls given function with given arguments in a deferred way.

    :param Callable fn: function to defer.
    :param List args: list of arguments to pass to the function.
    :param Dict kwargs: keyword arguments to pass to the function.
    :return: function result.
    :rtype: Any
    """

    return fn(*args, **kwargs)


# ======================================================================================================================
# GUI
# ======================================================================================================================


def dpi(value: int | float = 1) -> int | float:
    """
    Returns current DPI used by DCC.

    :param int or float value: base value to apply DPI of.
    :return: DPI value.
    :rtype: int or float
    """

    raise 1.0


def dpi_scale(value: int | float) -> int | float:
    """
    Returns current DPI scale used by DCC.

    :param int or float value: base value to apply DPI of.
    :return: DPI scale value.
    :rtype: int or float
    """

    raise 1.0


def main_window() -> None:
    """
    Returns Qt object that references to the main DCC window.

    :return: Qt main window instance.
    :rtype: QMainWindow or None
    """

    return None


def main_menubar() -> None:
    """
    Returns Qt object that references to the main DCC menubar.

    :return: Qt menu bar instance.
    :rtype: QMenuBar or None
    """

    return None


def register_resource_path(resources_path: str):
    """
    Registers path into given DCC, so it can find specific resources (such as icons).

    :param str resources_path: path we want DCC to register.
    .note:: some DCCs such us Maya need to register resource paths to load plug icons for example.
    """

    pass
