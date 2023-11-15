#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Menu manager implementation for tp-dcc-tools framework
"""

from __future__ import annotations

from tp.core import dcc
from tp.preferences import manager


class MenusManager:
    def __init__(self):
        super().__init__()

        self._menus = list()                                                            # type: list[MenuItem]
        self._original_menus = list()                                                   # type: list[dict]
        self._menu_preference_interface = manager.preference().interface(
            'menu', dcc=dcc.current_dcc())                                              # type: MenuInterface
        self._menu_name = self._menu_preference_interface.menu_name() if self._menu_preference_interface else 'tp Tools'
        self._menu_object_name = f'{self._menu_name.replace(" ", "_")}_mainMenu'        # internal Qt object name

    def menu_by_id(self, menu_id: str ) -> MenuItem:
        """
        Recursively searches all menus looking for the MenuItem with the given ID.

        :param str menu_id: menu ID to search for.
        :return: MenuItem matched with given ID or None if no matching MenuItem was found.
        :rtype: MenuItem or None
        """

        if not menu_id:
            return None

        for menu in self._menus:
            if menu.type == MenuItem.MENU_TYPE and menu.id == menu_id:
                return menu
            for sub_menu in menu.iterate_children(recursive=True):
                if sub_menu.type == MenuItem.MENU_TYPE and sub_menu.id == menu_id:
                    return sub_menu


class HierarchyItem:
    def __init__(self, data: dict, parent: HierarchyItem or None = None):
        super().__init__()

        self._children = list()                     # list[HierarchyItem]
        self._parent = parent
        self._label = data.get('label', '')         # type: str
        self._type = data.get('type', '')           # type: str

    def __len__(self):
        return len(self._children)


class Item(HierarchyItem):

    SEPARATOR_TYPE = 'separator'
    GROUP_TYPE = 'group'
    MENU_TYPE = 'menu'
    LABEL_TYPE = 'label'
    SHELF_BUTTON = 'button'


class MenuItem(Item):
    pass
