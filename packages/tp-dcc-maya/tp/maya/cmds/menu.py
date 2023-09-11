#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya menus
"""

from __future__ import annotations

import re

import maya.cmds as cmds
import maya.mel as mel

from tp.core import log

logger = log.tpLogger


def main_menu() -> str:
    """
    Returns Maya main menu name.

    :return: main menu name.
    :rtype: str
    """

    return mel.eval('$tmp=$gMainWindow')


def menus(long_path: bool = False) -> list[str]:
    """
    Return a list with all Maya menus.

    :param bool long_path: whether to return menu names or menu paths.
    :return: list of all Maya menu names.
    :rtype: list[str]
    """

    return cmds.lsUI(menus=True, long=long_path)


def compatible_name(name: str) -> str:
    """
    Returns a compatible Maya menu internal name from given one.

    :param str name: Maya menu name.
    :return: compatible Maya menu name.
    :rtype: str
    """

    return re.sub('[^0-9a-zA-Z]+', '_', name).strip('_')


def unique_compatible_name(name: str, parent: str) -> str:
    """
    Recursive function that returns a unique compatible Maya menu internal name from given one.

    :param str name: Maya menu name.
    :param str parent: parent menu name.
    :return: unique compatible Maya menu name.
    :rtype: str
    """

    name = compatible_name(name)
    long_name = f'{parent}|{name}'
    long_menu_names = menus(long_path=True)
    long_menu_item_names = cmds.lsUI(menuItems=True, long=True)
    if any(long_name == long_menu_name for long_menu_name in long_menu_names + long_menu_item_names):
        name = f'{name}_1'
        name = unique_compatible_name(name, parent)

    return name


def create_root_menu(label: str, window_name: str | None = None, kwargs: dict | None = None) -> str:
    """
    Creates a new root menu in Maya.

    :param str label: label for the menu.
    :param str or None window_name: optional name of the window where we want to create the root menu in.
    :param dict or None kwargs: optional keyword arguments.
    :return: newly created root menu path.
    :rtype: str
    """

    # TODO: Add support for menus in other windows (e.g: Script Editor).
    # window_name = window_name or "gMainWindow"  # default value
    # menu_path = mel.eval(f'$temp=${window_name}')

    menu_path = main_menu()
    kwargs = kwargs or {}
    kwargs.setdefault('parent', menu_path)
    kwargs.setdefault('tearOff', True)
    name = label.replace('_', ' ')
    return cmds.menu(name, **kwargs)


def remove_menu(menu_name: str):
    """
    Removes, if exists, menu with given name.

    :param str menu_name: name of the menu to delete.
    """

    for m in menus():
        lbl = cmds.menu(m, query=True, label=True)
        if lbl == menu_name:
            cmds.deleteUI(m, menu=True)


def check_menu_exists(menu_name: str) -> bool:
    """
    Returns whether a menu with the given name already exists.

    :param str menu_name: name of the menu to check.
    :return: True if menu with given name exists; False otherwise.
    :rtype: bool
    """

    for m in menus():
        lbl = cmds.menu(m, query=True, label=True)
        if lbl == menu_name:
            return True

    return False


def find_menu_by_path(menu_name: str) -> str | None:
    """
    Returns full name of the menu with given path.

    :param str menu_name: path of the menu to search.
    :return: found menu path.
    :rtype: str or None
    """

    long_name = f'{main_menu()}|{menu_name}'        # for now, we assume menu is a child of the main window
    for long_menu_name in menus(long_path=True):
        if long_menu_name == long_name:
            return long_menu_name

    return None


def find_menu_by_label(menu_label: str) -> str | None:
    """
    Returns full name of the menu with given name.

    :param str menu_label: label of the menu to search.
    :return: found menu path.
    :rtype: str or None
    """

    for m in menus(long_path=True):
        lbl = cmds.menu(m, query=True, label=True)
        if lbl == menu_label:
            return m

    return None
