#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to Houdini UI
"""

import hou
from hou import shelves

from tp.core import log

logger = log.tpLogger


def get_houdini_window():
    """
    Return the Houdini Qt main window
    """

    try:
        return hou.qt.mainWindow()
    except Exception:
        return hou.ui.mainQtWindow()


def get_shelf(shelf_name):
    """
    Returns shelf by name
    :param shelf_name: str
    :return: hou.Shelf
    """

    current_shelves = shelves.shelves()
    for k, v in current_shelves.items():
        if k == shelf_name:
            return v

    return None


def shelf_exists(shelf_name):
    """
    Returns whether given shelf exits or not
    :param shelf_name: str
    :return: bool
    """

    current_shelves = shelves.shelves()
    if shelf_name in current_shelves.keys():
        return True

    return False


def create_shelf(shelf_name, shelf_label):
    """
    Creates new Shelf
    :param shelf_name: str
    :param shelf_label: str
    :return: hou.Shelf
    """

    return shelves.newShelf(name=shelf_name, label=shelf_label)


def remove_shelf(name):
    """
    Removes given Shelf
    :param name: str
    """

    if not shelf_exists(shelf_name=name):
        return

    shelf = get_shelf(shelf_name=name)
    if shelf:
        shelf.destroy()


def get_shelf_set(shelf_set_name):
    """
    Returns shelf set by name
    :param shelf_set_name: str
    :return: hou.ShelfSet
    """

    current_shelve_sets = shelves.shelfSets()
    for k, v in current_shelve_sets.items():
        if k == shelf_set_name:
            return v

    return None


def shelf_set_exists(shelf_set_name):
    """
    Returns whether given shelf set exists or not
    :param shelf_set_name: str
    :return: bool
    """

    current_shelve_sets = shelves.shelfSets()
    if shelf_set_name in current_shelve_sets.keys():
        return True

    return False


def create_shelf_set(name, dock=True):
    """
    Creates a new Shelf set with the given name
    :param name: str
    :param dock: bool
    """

    new_shelf_set = shelves.newShelfSet(name=name, label=name)
    if new_shelf_set and dock:
        dock_shelf_set(shelf_set_name=name)

    return new_shelf_set


def remove_shelf_set(name):
    """
    Removes given ShelfSet
    :param name: str
    """

    if not shelf_set_exists(shelf_set_name=name):
        return

    shelf_set = get_shelf_set(shelf_set_name=name)
    if shelf_set:
        shelf_set.destroy()


def dock_shelf_set(shelf_set_name, dock_name='Build'):
    """
    Docks given shelf set into given dock name
    :param shelf_set_name: str
    :param dock_name: str
    """

    hou.hscript('shelfdock -d {} add {}'.format(dock_name, shelf_set_name))


def undock_shelf_set(shelf_set_name, dock_name='Build'):
    """
    Docks given shelf set into given dock name
    :param shelf_set_name: str
    :param dock_name: str
    """

    hou.hscript('shelfdock -d {} remove {}'.format(dock_name, shelf_set_name))


def create_shelf_tool(tool_name, tool_label, tool_script, tool_type='python', icon=None, help=None):
    """
    Creates a new Houdini Python shelf tool
    :param tool_name:
    :param tool_label:
    :param tool_script:
    :param tool_type:
    :param icon:
    :param help:
    :return:
    """

    language = None
    if tool_type == 'python':
        language = hou.scriptLanguage.Python
    elif tool_type == 'hscript':
        language = hou.scriptLanguage.HScript
    if language is None:
        logger.warning(
            'Impossible to create shelf tool {} because script language {} is not supported by Houdini'.format(
                tool_name, tool_type))
        return None

    return shelves.newTool(
        name=tool_name, label=tool_label, script=tool_script, icon=icon, help=help, language=language)


def get_current_frame():
    """
    Return current Maya frame set in time slider
    :return: int
    """

    return hou.frame()


def get_time_slider_range():
    """
    Return the time range from Maya time slider
    :return: list<float, float>, [start_frame, end_frame]
    """

    playbar_frame = hou.playbar.playbackRange()
    return [playbar_frame.x(), playbar_frame.y()]
