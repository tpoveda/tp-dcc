#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya DCC implementation
"""

from __future__ import annotations

import os
from typing import List, Callable, Any

import maya.cmds as cmds
import maya.utils as utils

from Qt.QtWidgets import QApplication, QMainWindow, QMenuBar

from tp.core import dccs
from tp.common.python import path, folder
from tp.maya.cmds import helpers, gui, scene


def name() -> str:
    """
    Returns the name of the DCC.

    :return: DCC name ('maya', 'mobu', ...).
    :rtype: str
    """

    return dccs.Maya


def file_extensions() -> List[str]:
    """
    Returns supported file extensions of the DCC.

    :return: list of DCC file extensions (['.mb', '.ma'], ['.max'], ...).
    :rtype: List[str]
    """

    return ['.ma', '.mb']


def version() -> int | float:
    """
    Returns integer version of the DCC.

    :return: DCC version (2022, 2023.5, ...).
    :rtype: int or float
    """

    return helpers.maya_version()


def version_name() -> str:
    """
    Returns name version of the DCC.

    :return: DCC version ('2022', '2023.5', ...).
    :rtype: str
    """

    return str(helpers.maya_version())


def is_batch() -> bool:
    """
    Returns whether DCC is being executed in batch mode.

    :return: True if DCC is being executed in batch mode; False otherwise.
    :rtype: bool
    """

    return cmds.about(batch=True)


def execute_deferred(fn: Callable) -> Any:
    """
    Executes given function in deferred mode

    :param Callable fn: function to defer execution of.
    :return: function result.
    :rtype: Any
    """

    return utils.executeDeferred(fn)


def deferred_function(fn, *args, **kwargs) -> Any:
    """
    Calls given function with given arguments in a deferred way.

    :param Callable fn: function to defer.
    :param List args: list of arguments to pass to the function.
    :param Dict kwargs: keyword arguments to pass to the function.
    :return: function result.
    :rtype: Any
    """

    return cmds.evalDeferred(fn, *args, **kwargs)


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

    qt_dpi = QApplication.devicePixelRatio() if cmds.about(batch=True) else QMainWindow().devicePixelRatio()

    return max(qt_dpi * value, dpi_scale(value))


def dpi_scale(value: int | float) -> int | float:
    """
    Returns current DPI scale used by DCC.

    :param int or float value: base value to apply DPI of.
    :return: DPI scale value.
    :rtype: int or float
    """

    maya_scale = 1.0
    try:
        maya_scale = cmds.mayaDpiSetting(query=True, realScaleValue=True)
    except AttributeError:
        pass

    return maya_scale * value


def main_window() -> QMainWindow | None:
    """
    Returns Qt object that references to the main DCC window.

    :return: Qt main window instance.
    :rtype: QMainWindow or None
    """

    return gui.maya_window()


def main_menubar() -> QMenuBar | None:
    """
    Returns Qt object that references to the main DCC menubar.

    :return: Qt menu bar instance.
    :rtype: QMenuBar or None
    """

    win = main_window()
    return win.menuBar() if win else None


def register_resource_path(resources_path: str):
    """
    Registers path into given DCC, so it can find specific resources (such as icons).

    :param str resources_path: path we want DCC to register.
    .note:: some DCCs such us Maya need to register resource paths to load plug icons for example.
    """

    if not resources_path or not path.is_dir(resources_path):
        return

    resources_path = path.clean_path(resources_path)
    resources_paths = [resources_path]
    resources_paths.extend(folder.get_folders(resources_path, recursive=True, full_path=True) or list())

    for resource_path in resources_paths:
        if not os.environ.get('XBMLANGPATH', None):
            os.environ['XBMLANGPATH'] = resource_path
        else:
            paths = os.environ['XBMLANGPATH'].split(os.pathsep)
            if resource_path not in paths and os.path.normpath(resource_path) not in paths:
                os.environ['XBMLANGPATH'] = os.environ['XBMLANGPATH'] + os.pathsep + resource_path


# =================================================================================================================
# SCENE
# =================================================================================================================

def current_time() -> int:
    """
    Returns current scene time.

    :return: scene time.
    :rtype: int
    """

    return cmds.currentTime(query=True)


def new_scene(force: bool = True, do_save: bool = True) -> bool:
    """
    Creates a new DCC scene.

    :param bool force: True if we want to save the scene without any prompt dialog
    :param bool do_save: True if you want to save the current scene before creating new scene
    :return: True if new scene operation was completed successfully; False otherwise.
    :rtype: bool
    """

    return scene.new_scene(force=force, do_save=do_save)


def scene_is_modified() -> bool:
    """
    Returns whether current opened DCC file has been modified by the user or not.

    :return: True if current DCC file has been modified by the user; False otherwise
    :rtype: bool
    """

    return cmds.file(query=True, modified=True)


def scene_name() -> str:
    """
    Returns the name of the current scene.

    :return: scene name.
    :rtype: str
    """

    return cmds.file(query=True, sceneName=True)


def clear_selection():
    """
    Clears current scene selection.
    """

    cmds.select(clear=True)


def fit_view(animation: bool = True):
    """
    Fits current viewport to current selection.

    :param bool animation: whether fit should be animated.
    """

    cmds.viewFit(an=animation)
