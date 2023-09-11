#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Unreal Engine DCC implementation
"""

from __future__ import annotations

from typing import List, Callable, Any

from Qt.QtWidgets import QMainWindow, QMenuBar

from tp.core import dccs
from tp.unreal.core import helpers


def name() -> str:
    """
    Returns the name of the DCC.

    :return: DCC name ('maya', 'mobu', ...).
    :rtype: str
    """

    return dccs.Unreal


def file_extensions() -> List[str]:
    """
    Returns supported file extensions of the DCC.

    :return: list of DCC file extensions (['.mb', '.ma'], ['.max'], ...).
    :rtype: List[str]
    """

    return ['.uproject']


def version() -> int | float:
    """
    Returns integer version of the DCC.

    :return: DCC version (2022, 2023.5, ...).
    :rtype: int or float
    """

    return helpers.unreal_version()[0]


def version_name() -> str:
    """
    Returns name version of the DCC.

    :return: DCC version ('2022', '2023.5', ...).
    :rtype: str
    """

    return helpers.unreal_version_name()


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

    return 1.0


def dpi_scale(value: int | float) -> int | float:
    """
    Returns current DPI scale used by DCC.

    :param int or float value: base value to apply DPI of.
    :return: DPI scale value.
    :rtype: int or float
    """

    return value


def main_window() -> QMainWindow | None:
    """
    Returns Qt object that references to the main DCC window.

    :return: Qt main window instance.
    :rtype: QMainWindow or None
    """

    return None


def main_menubar() -> QMenuBar | None:
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


# =================================================================================================================
# SCENE
# =================================================================================================================

def current_time() -> int:
    """
    Returns current scene time.

    :return: scene time.
    :rtype: int
    """

    raise NotImplementedError


def new_scene(force: bool = True, do_save: bool = True) -> bool:
    """
    Creates a new DCC scene.

    :param bool force: True if we want to save the scene without any prompt dialog
    :param bool do_save: True if you want to save the current scene before creating new scene
    :return: True if new scene operation was completed successfully; False otherwise.
    :rtype: bool
    """

    raise NotImplementedError


def scene_is_modified() -> bool:
    """
    Returns whether current opened DCC file has been modified by the user or not.

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    raise NotImplementedError


def scene_name() -> str:
    """
    Returns the name of the current scene.

    :return: scene name.
    :rtype: str
    """

    raise NotImplementedError


def clear_selection():
    """
    Clears current scene selection.
    """

    raise NotImplementedError


def fit_view(animation: bool = True):
    """
    Fits current viewport to current selection.

    :param bool animation: whether fit should be animated.
    """

    raise NotImplementedError
