#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya menus
"""

import os
import json
from collections import OrderedDict

import maya.cmds
import maya.mel

from tp.core import log
from tp.core.abstract import menu as abstract_menu

logger = log.tpLogger


class MayaMenu(abstract_menu.AbstractMenu, object):
    def __init__(self, name='MayaMenu'):
        super(MayaMenu, self).__init__()

        self.name = name

    def create_menu(self, file_path=None, parent_menu=None):
        """
        Creates a new DCC menu app
        If file path is not given the menu is created without items
        :param name: str, name for the menu
        :param file_path: str, path where JSON menu file is located
        :param parent_menu: str, Name of the menu to append this menu to
        :return: variant, nativeMenu || None
        """

        if check_menu_exists(self.name):
            return

        menu_created = False

        if parent_menu:
            m = find_menu(parent_menu)
            if m:
                self._native_pointer = maya.cmds.menuItem(subMenu=True, parent=m, tearOff=True, label=self.name)
                menu_created = True

        s_menu = None
        if not menu_created:
            s_menu = maya.cmds.menu(parent=main_menu(), tearOff=True, label=self.name)

        if not file_path or not s_menu:
            return

        if not os.path.isfile(file_path):
            logger.warning('Menu was not created because menu file is not valid or does not exists!')
            return

        with open(file_path, 'r') as f:
            menu_data = json.load(f, object_pairs_hook=OrderedDict)

        if menu_data:
            menu_categories = list(menu_data.keys())
            for category in menu_categories:
                self.create_category(category_name=category, category_items=menu_data[category], parent_menu=s_menu)

    @staticmethod
    def create_category(category_name, category_items, parent_menu):
        """
        Creates a new category on the passed menu. If not menu specified this menu is used, if exists
        :param parent_menu: str, menu to add category to
        :param category_name: str, name of the category
        :param category_items: list<str>, list of items to add to the category
        :return: variant, nativeMenu || None
        """

        submenu = maya.cmds.menuItem(subMenu=True, tearOff=True, parent=parent_menu, label=category_name)
        for item in category_items:
            maya.cmds.menuItem(parent=submenu, label=item['label'], command=item['command'])


def main_menu():
    """
    Returns Maya main menu
    """

    return maya.mel.eval('$tmp=$gMainWindow')


def get_menus():
    """
    Return a list with all Maya menus
    :return: list<str>
    """

    return maya.cmds.lsUI(menus=True)


def remove_menu(menu_name):
    """
    Removes, if exists, a menu of Max
    :param menu_name: str, menu name
    """

    for m in get_menus():
        lbl = maya.cmds.menu(m, query=True, label=True)
        if lbl == menu_name:
            maya.cmds.deleteUI(m, menu=True)


def check_menu_exists(menu_name):
    """
    Returns True if a menu with the given name already exists
    :param menu_name: str, menu name
    :return: bol
    """

    for m in get_menus():
        lbl = maya.cmds.menu(m, query=True, label=True)
        if lbl == menu_name:
            return True

    return False


def find_menu(menu_name):
    """
    Returns Menu instance by the given name
    :param menu_name: str, menu of the name to search for
    :return: nativeMenu
    """

    for m in get_menus():
        lbl = maya.cmds.menu(m, query=True, label=True)
        if lbl == menu_name:
            return m

    return None
