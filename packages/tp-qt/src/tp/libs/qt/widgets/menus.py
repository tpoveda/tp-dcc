from __future__ import annotations

import typing

from Qt.QtCore import Qt, Signal, QPoint
from Qt.QtWidgets import QMenu, QAction, QWidgetAction
from Qt.QtGui import QIcon, QMouseEvent, QShowEvent

from .. import dpi
from .. import utils

if typing.TYPE_CHECKING:
    from .search import SearchFindWidget


def mixin(cls):
    """
    Decorator that can be added to custom widgets to automatize the creation of left/right/middle click menus.
    """

    original_init__ = cls.__init__

    def my__init__(self, *args, **kwargs):
        original_init__(self, *args, **kwargs)

    # noinspection PyIncorrectDocstring
    def get_menu(self, mouse_button=Qt.RightButton):
        """
        Returns the menu based on the given mouse button.

        :param Qt.ButtonClick mouse_button: the clicked mouse button.
        :return: registered menu on that mouse button.
        :rtype: QMenu or None
        """

        return self._click_menu[mouse_button]

    # noinspection PyIncorrectDocstring
    def set_menu(self, menu, action_list=None, mouse_button=Qt.RightButton):
        """
        Sets the left/middle/right click menu. If a model_list is given, then the menu will be  filled with that info.

        :param QMenu menu: Qt menu to show on left/middle/right click.
        :param list(tuple(str)) action_list: list of menu modes. Eg: [('icon1', 'menuName1'), (...), ...]
        :param Qt.ButtonClick mouse_button: the mouse button menu will be assigned to.
        """

        self._click_menu[mouse_button] = menu
        self._menu_active[mouse_button] = True
        if action_list:
            self._add_action_list(action_list, mouse_button=mouse_button)

    # noinspection PyIncorrectDocstring
    def show_context_menu(self, mouse_button):
        """
        Shows the menu depending on the given mouse click.

        :param Qt.ButtonClick mouse_button: the mouse button menu will be assigned to.
        """

        if not self._click_menu:
            return

        menu = self.get_menu(mouse_button=mouse_button)
        if menu is not None and self._menu_active[mouse_button]:
            self.setFocus()
            parent_position = self.mapToGlobal(QPoint(0, 0))
            pos = parent_position + QPoint(0, dpi.dpi_scale(self._menu_vertical_offset))
            menu.exec_(pos)

    def _setup_menu_class(self, menu_vertical_offset=20):
        """
        Internal function that handles the setup of menu creation.

        :param int menu_vertical_offset: negative vertical offset of the drawn menu
        """

        self._menu_vertical_offset = menu_vertical_offset
        self._menu_active = {
            Qt.LeftButton: False,
            Qt.MiddleButton: False,
            Qt.RightButton: False,
        }
        self._click_menu = {
            Qt.LeftButton: None,
            Qt.MiddleButton: None,
            Qt.RightButton: None,
        }
        self._menu_searchable = {
            Qt.LeftButton: False,
            Qt.MiddleButton: False,
            Qt.RightButton: False,
        }

    def _add_action_list(self, actions_list, mouse_button=Qt.RightButton):
        """
        Internal function that resets the menu and fills its with given list of actions.

        :param list(tuple(str, str)) actions_list: list of menu actions. Eg: [('icon1', 'menuName1'), (...), ...]
        :param Qt.ButtonClick mouse_button: the mouse button menu will be assigned to.

        ..warning:: this function only works with DCC Tools framework Menu class
        """

        menu = self.get_menu(mouse_button=mouse_button)
        if menu is not None:
            menu.action_connect_list(actions_list)

    setattr(cls, "__init__", my__init__)
    setattr(cls, "get_menu", get_menu)
    setattr(cls, "set_menu", set_menu)
    setattr(cls, "show_context_menu", show_context_menu)
    setattr(cls, "_setup_menu_class", _setup_menu_class)
    setattr(cls, "_add_action_list", _add_action_list)

    return cls


class BaseMenu(QMenu):
    """
    Extends standard QMenu.
    """

    mouseButtonClicked = Signal(Qt.MouseButton, QAction)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """
        Extends `mouseReleaseEvent` QMenu function.

        :param event: mouse event.
        """

        self.mouseButtonClicked.emit(event.button(), self.actionAt(event.pos()))

        return super().mouseReleaseEvent(event)


class SearchableMenu(BaseMenu):
    """
    Extends BaseMenu to make it searchable.
    First action is a QLineEdit used to recursively search on all actions.
    """

    class SearchableTaggedAction(QAction):
        """
        Class that defines a searchable tag action.
        """

        def __init__(
            self,
            label: str,
            icon: QIcon | None = None,
            parent: SearchableMenu | None = None,
        ):
            super().__init__(label, parent)

            self._tags = set()  # Set[str]

            if icon:
                self.setIcon(icon)

        @property
        def tags(self) -> set[str]:
            """
            Getter method that returns set of searchable tags.
            :return: searchable tags.
            """

            return self._tags

        @tags.setter
        def tags(self, new_tags: set[str]):
            """
            Setter method that sets searchable tags.

            :param set[str] new_tags: searchable tags.
            """

            self._tags = new_tags

        def has_tag(self, tag: str) -> bool:
            """
            Searches this instance tags. Returns True if the tag is valid or False otherwise

            :param tag: partial or full tag to search for
            """

            for t in self._tags:
                if tag in t:
                    return True

            return False

        def has_any_tag(self, tags: list[str]) -> bool:
            """
            Returns True if current action has some given tags; False otherwise.

            :param tags: list of tags to check.
            """

            for t in tags:
                for i in self._tags:
                    if t in i:
                        return True

            return False

    def __init__(self, *args, **kwargs):
        self._search_visible = (
            kwargs.pop("search_visible")
            if kwargs.get("search_visible", None) is not None
            else True
        )
        super(SearchableMenu, self).__init__(*args, **kwargs)

        self._search_action: QWidgetAction | None = None
        self._search_edit: SearchFindWidget | None = None

        self.setObjectName(kwargs.get("objectName", ""))
        self.setTitle(kwargs.get("title", ""))
        self._init_search_edit()
        self.set_search_visible(self._search_visible)

        self.setAttribute(Qt.WA_TranslucentBackground, False)

        # When menu is hidden we make that search text is cleared out
        self.aboutToShow.connect(self._on_about_to_show_menu)

    def clear(self) -> None:
        """
        Overrides base `clear` function.
        """

        super().clear()

        self._init_search_edit()

    def showEvent(self, event: QShowEvent):
        """
        Overrides base `showEvent` function to set the search visible or not.

        :param event: Qt show event.
        """

        if self.search_visible():
            self._search_edit.setFocus()

    def search_visible(self) -> bool:
        """
        Returns whether search edit is visible.
        """

        return self._search_action.isVisible()

    def set_search_visible(self, flag: bool):
        """
        Sets the visibility of the search edit.

        :param flag: True to make search visible; False otherwise.
        """

        self._search_visible = flag
        if not self._search_edit:
            return

        self._search_action.setVisible(flag)
        self._search_edit.setVisible(flag)

    def update_search(self, search_string: str | None = None):
        """
        Search all actions for a string tag.

        :param search_string: tag names separated by spaces (for example, "elem1 elem2")
        """

        def _recursive_search(_menu: QMenu, _search_str: str):
            """
            Internal function that recursively searches for menu actions.

            :param _menu: menu to search actions for.
            :param _search_str: search string.
            """

            for action in _menu.actions():
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
                elif isinstance(
                    action, SearchableMenu.SearchableTaggedAction
                ) and not action.has_tag(search_str):
                    action.setVisible(False)

            for sub_menu in _menu.findChildren(QMenu):
                _recursive_search(sub_menu, search_str)

            actions = [action for action in _menu.actions() if not action.isSeparator()]
            menu_vis = any(action.isVisible() for action in actions)
            _menu.menuAction().setVisible(menu_vis)

        def _recursive_search_by_tags(_menu: QMenu, _tags: list[str]):
            """
            Internal function that recursively searches for menu actions.

            :param _menu: menu to search actions for.
            :param _tags: list of tags.
            """

            for action in _menu.actions():
                sub_menu = action.menu()
                if sub_menu:
                    _recursive_search_by_tags(sub_menu, _tags)
                    continue
                elif action.isSeparator():
                    continue
                elif isinstance(action, SearchableMenu.SearchableTaggedAction):
                    action.setVisible(action.has_any_tag(_tags))

            actions = [action for action in _menu.actions() if not action.isSeparator()]
            menu_vis = any(action.isVisible() for action in actions)
            _menu.menuAction().setVisible(menu_vis)

        search_str = str(search_string or "").lower()
        tags = search_str.split()
        if not search_str:
            utils.recursively_set_menu_actions_visibility(menu=self, state=True)
            return
        elif len(tags) > 1:
            _recursive_search_by_tags(self, tags)
            return

        _recursive_search(self, tags[0])

    def _init_search_edit(self):
        """
        Internal function that adds a QLineEdit as the first action in the menu.
        """

        # To avoid cyclic imports
        from . import search

        self._search_action = QWidgetAction(self)
        self._search_action.setObjectName("SearchAction")
        self._search_edit = search.SearchFindWidget(parent=self)
        self._search_edit.setStyleSheet(
            "QPushButton {background-color: transparent; border: none;}"
        )
        self._search_edit.set_placeholder_text("Search ...")
        self._search_edit.textChanged.connect(self._on_update_search)
        self._search_action.setDefaultWidget(self._search_edit)
        self.addAction(self._search_action)
        self.addSeparator()

    def _on_update_search(self, search_string):
        """
        Internal callback function that is called when the user interacts with the search line edit.
        """

        self.update_search(search_string)

    def _on_about_to_show_menu(self):
        """
        Internal callback function that is called when the menu is about to be showed.
        """

        self._search_edit.clear()
