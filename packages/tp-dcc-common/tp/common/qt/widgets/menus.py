#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains classes that extends default behaviour of QMenu
"""

from functools import partial

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QMenu, QAction, QWidgetAction
from Qt.QtGui import QIcon

from tp.common.python import helpers
from tp.common.resources import api as resources
from tp.common.qt import qtutils


def menu(label='', icon=None, parent=None):
    """
    Creates a new menu with extended functionality.

    :param str label: label text of the menu.
    :param QIcon icon: optional menu icon.
    :param QWidget parent: parent widget.
    :return: newly created menu.
    :rtype: Menu
    """

    new_menu = Menu(label, parent=parent)
    if icon and not icon.isNull():
        new_menu.setIcon(icon)

    return new_menu


def searchable_menu(label='', icon=None, search_visible=True, parent=None):
    """
    Creates a new searchable menu.

    :param str label: label text of the menu.
    :param QIcon icon: optional menu icon.
    :param bool search_visible: whether or not search widget is visible.
    :param QWidget parent: parent widget.
    :return: newly created menu.
    :rtype: SearchableMenu
    """

    new_menu = SearchableMenu(label, search_visible=search_visible, parent=parent)
    if icon and not icon.isNull():
        new_menu.setIcon(icon)

    return new_menu


class Menu(QMenu):

    menuChanged = Signal()
    mouseButtonClicked = Signal(object, object)     # mouseButton, QAction

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._menu_items_list = list()          # internal list that contains item names read from actions list
        self._menu_icons_list = list()          # internal list that contains icon names read from the actions list
        self._current_menu_item = ''            # current item menu
        self._current_menu_index = 0            # current menu index

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def mouseReleaseEvent(self, event):
        """
        Extends mouseReleaseEvent QMenu function

        :param event: QMouseEvent
        """

        self.mouseButtonClicked.emit(event.button(), self.actionAt(event.pos()))

        return super(Menu, self).mouseReleaseEvent(event)

    def insertAction(self, before, *args):
        """
        Extends insertAction QMenu function
        Add supports for finding the before action by the given string

        :param before: str or QAction
        :param args: list
        :return: QAction
        """

        if helpers.is_string(before):
            before = self.find_action(before)

        return super().insertAction(before, *args)

    def insertMenu(self, before, menu):
        """
        Extends insertMenu QMenu function
        Add supports for finding the before action by the given string

        :param before: str or QAction
        :param menu: QMenu
        :return: QAction
        """

        if helpers.is_string(before):
            before = self.find_action(before)

        return super().insertMenu(before, menu)

    def insertSeparator(self, before):
        """
        Extends insertSeparator QMenu function

        :param before: str or QAction
        :return: QAction
        """

        if helpers.is_string(before):
            before = self.find_action(before)

        return super().insertSeparator(before)

    def current_menu_item(self):
        """
        Returns the current selected menu name.

        :return: current menu name
        :rtype: str
        """

        return self._current_menu_item

    def set_current_menu_item(self, menu_item_name):
        """
        Sets both menu states for the given menu item name (without triggering a menu action).

        :param str menu_item_name: name of a men uname within the menu.
        """

        self._current_menu_item = menu_item_name
        self._current_menu_index = self._menu_items_list.index(menu_item_name)

    def current_menu_index(self):
        """
        Returns the current selected menu index.

        :return: current menu index.
        :rtype: int
        """

        return self._current_menu_index

    def set_current_menu_index(self, menu_item_index):
        """
        Sets both menu states for the given menu item index (without triggering a menu action).

        :param int menu_item_index: index of a menu name within the menu.
        """

        self._current_menu_index = menu_item_index
        self._current_menu_item = self._menu_items_list[menu_item_index]

    def add_text_separator(self, text):
        """
        Adds a new QWidgetAction that acts as separator with text.

        :param str text: text to add to the widget action.
        :return: text widget action
        :rtype: QWidgetAction
        """

        # Import here to avoid cyclic imports
        from tp.common.qt.widgets import dividers

        separator = QWidgetAction(self)
        text_label = dividers.divider(text, alignment=Qt.AlignLeft, shadow=False, parent=self)
        text_label._first_line.setVisible(False)
        separator.setDefaultWidget(text_label)
        self.addAction(separator)

        return separator

    def add_action(self, name, connect=None, checkable=False, checked=True, action=None, icon=None):
        """
        Creates a new QAction and adds it into this menu.

        :param str name: text for the new menu item.
        :param callable connect: optional function to connect when the menu item is clicked.
        :param bool checkable: whether the menu item is checkable.
        :param bool checked: whether the menu item is checked by default.
        :param QAction action: set the action directly (without creating a new one).
        :param str or QIcon icon: icon to set to the menu item.
        :return: newly added action.
        :rtype: QAction
        """

        if action is not None:
            self.addAction(action)
            return action

        new_action = self._get_action(name)
        new_action.setCheckable(checkable)
        new_action.setChecked(checked)
        self.addAction(new_action)

        icon = resources.icon(icon) if helpers.is_string(icon) else icon
        if icon and not icon.isNull():
            new_action.setIcon(icon)

        if connect is not None:
            if checkable:
                new_action.triggered.connect(partial(connect, new_action))
            else:
                new_action.triggered.connect(connect)

        return new_action

    def find_action(self, text):
        """
        Returns the action that contains the given text

        :param str text: action text.
        :return: QAction
        """

        for child in self.children():
            action = None
            if isinstance(child, QMenu):
                action = child.menuAction()
            elif isinstance(child, QAction):
                action = child
            if action and action.text().lower() == text.lower():
                return action

        return None

    def find_menu(self, text):
        """
        Returns the menu that contains given text.

        :param str text: menu text.
        :return: QMenu
        """

        for child in self.children():
            menu = None
            if isinstance(child, QMenu) and child.text().lower() == text.lower():
                return menu

        return None

    def action_connect_list(self, actions_list, default_menu_item=None):
        """
        Fills the menu with the given icons and action names from the list.

        :param list(tuple(str, str)) actions_list: list of menu actions. Eg: [('icon1', 'menuName1'), (...), ...]
        :param str default_menu_item: optional default menu item name.
        """

        self.clear()
        self._set_icon_and_menu_name_from_actions_list(actions_list)
        for i, menu_item_name in enumerate(self._menu_items_list):
            if menu_item_name != 'separator':
                item_icon = self._menu_icons_list[i]
                item_icon = resources.icon(item_icon) if helpers.is_string(item_icon) else item_icon
                self.add_action(menu_item_name, icon=item_icon or QIcon(), connect=partial(
                    self._action_connect, self._menu_icons_list[i], menu_item_name, i))
            else:
                self.addSeparator()

        if default_menu_item is None:
            self._current_menu_item = self._menu_items_list[0]
            self._current_menu_index = 0

    def _get_action(self, name):
        """
        Internal function that returns a new action for this menu with given name.
        This function can be overriden in custom classes to create custom actions by default.

        :param str name: name of the action.
        :return: action instance.
        :rtype: QAction
        """

        return QAction(name, parent=self)

    def _set_icon_and_menu_name_from_actions_list(self, actions_list):
        """
        Internal function that set up the variables that stores the list of icons and their names from the given
        actions list.

        :param list(tuple(str, str)) actions_list: list of menu actions. Eg: [('icon1', 'menuName1'), (...), ...]
        """

        self._menu_icons_list = list()
        self._menu_items_list = list()
        for i, action_tuple in enumerate(actions_list):
            self._menu_icons_list.append(action_tuple[0])
            self._menu_items_list.append(action_tuple[1])

    def _action_connect(self, icon_name, current_menu_item, current_menu_index):
        """
        Internal f unction that creates a single IconMenuButton item in one menu entry. Also sets the icon to switch
        when a menu item is clicked.

        :param str icon_name: icon that will be changed to when the menu is clicked.
        :param str current_menu_item: the current menu name.
        :param int current_menu_index: index of the menu item within menu, being 0 the first menu item.
        """

        self._current_menu_item = current_menu_item
        self._current_menu_index = current_menu_index
        self.menuChanged.emit()


class SearchableTaggedAction(QAction, object):
    def __init__(self, label, icon=None, parent=None):
        super().__init__(label, parent)

        self._tags = set()

        if icon:
            self.setIcon(icon)

    @property
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, new_tags):
        self._tags = helpers.force_list(new_tags)

    def has_tag(self, tag):
        """
        Searches this instance tags. Returns True if the tag is valid or False otherwise

        :param str tag: partial or full tag to search for
        :return: bool
        """

        for t in self._tags:
            if tag in t:
                return True

        return False

    def has_any_tag(self, tags):
        """
        Returns True if current action has some given tags; False otherwise.

        :param tags: list(str)
        :return: bool
        """

        for t in tags:
            for i in self._tags:
                if t in i:
                    return True

        return False


class SearchableMenu(Menu):
    """
    Extends standard QMenu to make it searchable.
    First action is a QLineEdit used to recursively search on all actions.
    """

    def __init__(self, *args, **kwargs):

        self._search_visible = kwargs.pop('search_visible') if kwargs.get('search_visible', None) is not None else True

        super(SearchableMenu, self).__init__(*args, **kwargs)

        self._search_action = None
        self._search_edit = None

        self.setObjectName(kwargs.get('objectName', ''))
        self.setTitle(kwargs.get('title', ''))
        self._init_search_edit()
        self.set_search_visible(self._search_visible)

        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # When menu is hidden we make that search text is cleared out
        self.aboutToShow.connect(self._on_about_to_show_menu)

    def clear(self):
        """
        Overrides base clear function.
        """

        super(SearchableMenu, self).clear()

        self._init_search_edit()

    def showEvent(self, event):
        """
        Overrides base showEvent function to set the search visible or not.

        :param QEvent event: Qt show event.
        """

        if self.search_visible():
            self._search_edit.setFocus()

    def _get_action(self, name):
        """
        Overrides _get_action internal function.
        Internal function that returns a new action for this menu with given name.

        :param str name: name of the action.
        :return: action instance.
        :rtype: SearchableTaggedAction
        """

        new_action = SearchableTaggedAction(name, parent=self)
        tags = list()
        tags += name.split(" ")
        tags += [s.lower() for s in name.split(" ")]
        new_action.tags = str(tags)

        return new_action

    def set_search_visible(self, flag):
        """
        Sets the visibility of the search edit

        :param flag: bool
        """

        self._search_visible = flag
        if not self._search_edit:
            return

        self._search_action.setVisible(flag)
        self._search_edit.setVisible(flag)

    def search_visible(self):
        """
        Returns whether search edit is visible

        :return: bool
        """

        return self._search_action.isVisible()

    def update_search(self, search_string=None):
        """
        Search all actions for a string tag

        :param str search_string: tag names separated by spaces (for example, "elem1 elem2")
        :return: str
        """

        def _recursive_search(menu, search_str):
            search_str = str(search_str).lower()

            # loop through menu actions
            for action in menu.actions():
                if not search_str:
                    action.setVisible(True)
                    continue
                # This is not valid because for some reason accession QAction menu() attributes makes Qt to
                # not display the menu anymore. The bug was noticeable in the following scenario:
                # 1) Type something in the menu search
                # 2) Navigate inside a Menu
                # 3) Execute one of the menu items
                # 4) Now when you open the main menu again all the menus inside it will not appear.
                # sub_menu = action.menu() if hasattr(action, 'menu') else None
                # if sub_menu:
                    # _recursive_search(sub_menu, search_str)
                    # continue
                if action.isSeparator():
                    continue
                elif isinstance(action, SearchableTaggedAction) and not action.has_tag(search_str):
                    action.setVisible(False)

            # loop through menu sub menus
            for menu in menu.findChildren(QMenu):
                _recursive_search(menu, search_str)

            actions = [action for action in menu.actions() if not action.isSeparator()]
            menu_vis = any(action.isVisible() for action in actions)
            menu.menuAction().setVisible(menu_vis)

        def _recursive_search_by_tags(menu, tags):
            for action in menu.actions():
                sub_menu = action.menu()
                if sub_menu:
                    _recursive_search_by_tags(sub_menu, tags)
                    continue
                elif action.isSeparator():
                    continue
                elif isinstance(action, SearchableTaggedAction):
                    action.setVisible(action.has_any_tag(tags))

            actions = [action for action in menu.actions() if not action.isSeparator()]
            menu_vis = any(action.isVisible() for action in actions)
            menu.menuAction().setVisible(menu_vis)

        search_str = search_string or ''
        tags = search_str.split()
        if not search_str:
            qtutils.recursively_set_menu_actions_visibility(menu=self, state=True)
            return
        elif len(tags) > 1:
            _recursive_search_by_tags(menu=self, tags=tags)
            return

        _recursive_search(menu=self, search_str=tags[0])

    def _init_search_edit(self):
        """
        Internal function that adds a QLineEdit as the first action in the menu
        """

        from tp.common.qt.widgets import search

        self._search_action = QWidgetAction(self)
        self._search_action.setObjectName('SearchAction')
        self._search_edit = search.SearchFindWidget(parent=self)
        self._search_edit.setStyleSheet('QPushButton {background-color: transparent; border: none;}')
        self._search_edit.set_placeholder_text('Search ...')
        self._search_edit.textChanged.connect(self._on_update_search)
        self._search_action.setDefaultWidget(self._search_edit)
        self.addAction(self._search_action)
        self.addSeparator()

    def _on_update_search(self, search_string):
        """
        Internal callback function that is called when the user interacts with the search line edit
        """

        self.update_search(search_string)

    def _on_about_to_show_menu(self):
        """
        Internal callback function that is called when the menu is about to be showed
        :return:
        """

        self._search_edit.clear()
