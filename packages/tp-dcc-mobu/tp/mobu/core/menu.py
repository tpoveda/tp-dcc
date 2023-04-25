#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with MotionBuilder menus
"""

from pyfbsdk import FBMenuManager

from tp.core import log

logger = log.tpLogger


def get_menu_manager():
    """
    Returns MotionBuilder menu manager
    """

    return FBMenuManager()


def get_menu(menu_path=None):
    """
    Returns Menu instance by the given name
    :param menu_path: str, path of the name to search for
    :return: nativeMenu or None
    """

    return get_menu_manager().GetMenu(menu_path)


def get_item(item_name, parent_menu):
    """
    Returns Item instance by the given name and parent menu
    :param item_name: str, name of the item to search for
    :param parent_menu: str, parent menu path
    :return: nativeItem or None
    """

    current_item = parent_menu.GetFirstItem()
    while current_item:
        if current_item.Caption == item_name:
            return current_item
            break
        current_item = parent_menu.GetNextItem(current_item)

    return None


def add_menu_item(menu_name, parent_menu_path=None):
    """
    Add and returns a menu (as an item) and its path with the name and parent provided
    :param menu_name: str, menu name
    :param parent_menu_path: str, parent menu path
    :return: (nativeItem, str), created item and its path in menu
    """

    menu_item = get_menu_manager().InsertLast(parent_menu_path, menu_name)

    if parent_menu_path:
        menu_path = parent_menu_path + '/' + menu_name
    else:
        menu_path = menu_name

    return menu_item, menu_path


def add_item(item_name, command, parent_menu_path=None):
    """
    Add and returns an item with the name, command and parent provided
    :param item_name: str, item name
    :param command: str, command written in python
    :param parent_menu_path: str, parent menu path
    :return: nativeItem, created item
    """

    # Return None if menu doesn't exist or is empty
    parent_menu = get_menu(parent_menu_path)

    # Change item name if sibling item with same name exists
    if parent_menu and get_item(item_name, parent_menu):

        origin_name = item_name
        i = 2
        while True:
            item_name = '{} ({})'.format(origin_name, i)
            if not get_item(item_name, parent_menu):
                break
            i = i + 1

        logger.warning(
            "Mobu menus do not handle sibling items with the same label. Label {} has been changed to {}.".format(
                origin_name, item_name))

    item = get_menu_manager().InsertLast(parent_menu_path, item_name)

    # We try to get parent_menu again if it was empty before
    if not parent_menu:
        parent_menu = get_menu(parent_menu_path)

    # Add the callback handling that item to menu
    def create_item_callback(item_label, item_command):
        def _function(control, event, lbl=item_label, cmd=item_command):
            if event.Name == lbl:
                exec(cmd)
        return _function

    parent_menu.OnMenuActivate.Add(create_item_callback(item_name, command))

    return item


def delete_item(item, parent_menu):
    """
    Delete an item from a menu
    :param item: nativeItem, item to delete
    :param parent_menu: nativeMenu, parent menu
    """
    parent_menu.DeleteItem(item)
