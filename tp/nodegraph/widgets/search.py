from __future__ import annotations

import re

from Qt.QtCore import Qt, Signal, QObject
from Qt.QtWidgets import QLineEdit, QMenu, QAction, QWidgetAction
from Qt.QtGui import QCursor, QKeyEvent

from ..views import uiconsts


class NodesTabSearchWidget(QMenu):
    """
    Custom QMenu that is used to show the search widget menu.
    """

    searchSubmitted = Signal(str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._rebuild: bool = False
        self._block_submit: bool = False
        self._node_dict: dict[str, str] = {}
        self._menus: dict[str, QMenu] = {}
        self._actions: dict[str, QAction] = {}
        self._searched_actions: list[QAction] = []

        self._line_edit = NodesTabSearchLineEdit(parent=self)
        self._search_widget = QWidgetAction(self)
        self._search_widget.setDefaultWidget(self._line_edit)
        self.addAction(self._search_widget)

        self._setup_signals()

        text_color = tuple(
            map(
                lambda i, j: i - j,
                (255, 255, 255),
                uiconsts.NODE_GRAPH_BACKGROUND_COLOR,
            )
        )
        selected_color = self.palette().highlight().color().getRgb()
        style_dict = {
            "QMenu": {
                "color": "rgb({0},{1},{2})".format(*text_color),
                "background-color": "rgb({0},{1},{2})".format(
                    *uiconsts.NODE_GRAPH_BACKGROUND_COLOR
                ),
                "border": "1px solid rgba({0},{1},{2},30)".format(*text_color),
                "border-radius": "3px",
            },
            "QMenu::item": {
                "padding": "5px 18px 2px",
                "background-color": "transparent",
            },
            "QMenu::item:selected": {
                "color": "rgb({0},{1},{2})".format(*text_color),
                "background-color": "rgba({0},{1},{2},200)".format(*selected_color),
            },
            "QMenu::separator": {
                "height": "1px",
                "background": "rgba({0},{1},{2}, 50)".format(*text_color),
                "margin": "4px 8px",
            },
        }
        self._menu_stylesheet = ""
        for css_class, css in style_dict.items():
            style = "{} {{\n".format(css_class)
            for elm_name, elm_val in css.items():
                style += "  {}:{};\n".format(elm_name, elm_val)
            style += "}\n"
            self._menu_stylesheet += style
        self.setStyleSheet(self._menu_stylesheet)

    def __repr__(self) -> str:
        """
        Returns the string representation of the search widget menu.

        :return: string representation.
        """

        return f"<{self.__class__.__name__}( at {hex(id(self))})"

    def keyPressEvent(self, event: QKeyEvent):
        """
        Overrides QMenu key press event.

        :param event: key event.
        """

        super().keyPressEvent(event)

        self._line_edit.keyPressEvent(event)

    def set_nodes(self, node_names: dict[str, list[str]] | None = None):
        """
        Sets the nodes to search for.

        :param node_names: dictionary of node names to search for.
        """

        if not self._node_dict or self._rebuild:
            self._node_dict.clear()
            self._clear_actions()
            self._set_menus_visible(False)
            for menu in self._menus.values():
                self.removeAction(menu.menuAction())
            self._actions.clear()
            self._menus.clear()
            for name, node_types in node_names.items():
                if len(node_types) == 1:
                    self._node_dict[name] = node_types[0]
                    continue
                for node_id in node_types:
                    self._node_dict[f"{name} ({node_id})"] = node_id
            self._build_menu()
            self._rebuild = False

        self._show()

    def _setup_signals(self):
        """
        Internal function that sets up signals.
        """

        self._line_edit.tabPressed.connect(self._close)
        self._line_edit.textChanged.connect(self._on_search_text_changed)
        self._line_edit.returnPressed.connect(self._on_search_submitted)

    def _set_menus_visible(self, flag: bool):
        """
        Internal function that sets the menus visible or not.

        :param flag: flag to set.
        """

        for menu in self._menus.values():
            menu.menuAction().setVisible(flag)

    def _show(self):
        """
        Internal function that shows the search widget.
        """

        self._line_edit.setText("")
        self._line_edit.setFocus()
        self._set_menus_visible(True)
        self._block_submit = False
        self.exec_(QCursor.pos())

    def _close(self):
        """
        Internal function that closes the search widget.
        """

        self._set_menus_visible(False)
        self.setVisible(False)
        self.menuAction().setVisible(False)
        self._block_submit = True

    def _clear_actions(self):
        """
        Internal function that clears all actions.
        """

        for action in self._searched_actions:
            self.removeAction(action)
            # action.triggered.connect(self._on_search_submitted)
        del self._searched_actions[:]

    def _build_menu(self):
        """
        Internal function that builds the search menu.
        """

        node_names = list(self._node_dict.keys())
        node_types = list(self._node_dict.values())

        menu_tree: dict[int, dict[str, QMenu]] = {}
        max_depth: int = 0
        for node_type in node_types:
            trees = ".".join(node_type.split(".")[:-1]).split("::")
            for depth, menu_name in enumerate(trees):
                new_menu = None
                menu_path = "::".join(trees[: depth + 1])
                if depth in menu_tree.keys():
                    if menu_name not in menu_tree[depth].keys():
                        new_menu = QMenu(menu_name)
                        new_menu.keyPressEvent = self.keyPressEvent
                        new_menu.setStyleSheet(self._menu_stylesheet)
                        menu_tree[depth][menu_path] = new_menu
                else:
                    new_menu = QMenu(menu_name)
                    new_menu.setStyleSheet(self._menu_stylesheet)
                    menu_tree[depth] = {menu_path: new_menu}
                if depth > 0 and new_menu:
                    new_menu.setProperty("parent_path", "::".join(trees[:depth]))
                max_depth = max(max_depth, depth)

        for i in range(max_depth + 1):
            menus = menu_tree[i]
            for menu_path, menu in menus.items():
                self._menus[menu_path] = menu
                if i == 0:
                    self.addMenu(menu)
                else:
                    parent_menu = self._menus[menu.property("parent_path")]
                    parent_menu.addMenu(menu)

        for name in node_names:
            action = QAction(name, self)
            action.setText(name)
            action.triggered.connect(self._on_search_submitted)
            self._actions[name] = action
            menu_name = self._node_dict[name]
            menu_path = ".".join(menu_name.split(".")[:-1])
            if menu_path in self._menus.keys():
                self._menus[menu_path].addAction(action)
            else:
                self.addAction(action)

    @staticmethod
    def _fuzzy_finder(key: str, collection: list[str]) -> list[str]:
        """
        Internal function that performs a fuzzy search for a given key within a collection of strings.

        This function searches for strings in the collection that contain the characters of the key in order,
        but not necessarily consecutively. The search is case-insensitive.

        :param key: The search key used for matching against the collection.
        :param collection: The list of strings to search within.
        :return: a list of matching strings sorted by the quality of the match, with shorter and earlier matches
            prioritized.
        """

        suggestions: list[tuple[int, int, str]] = []
        pattern = ".*?".join(key.lower())
        regex = re.compile(pattern)
        for item in collection:
            match = regex.search(item.lower())
            if match:
                suggestions.append((len(match.group()), match.start(), item))

        return [x for _, _, x in sorted(suggestions)]

    def _on_search_text_changed(self, text: str):
        """
        Internal callback function that is called when search text is changed.

        :param text: search text.
        """

        self._clear_actions()
        if not text:
            self._set_menus_visible(True)
            return

        self._set_menus_visible(False)

        self._searched_actions = []
        for action in self._actions.values():
            if text.lower() in action.text().lower():
                self._searched_actions.append(action)
                self.addAction(action)

        action_names = self._fuzzy_finder(text, list(self._actions.keys()))
        self._searched_actions = [self._actions[name] for name in action_names]
        self.addActions(self._searched_actions)

        if self._searched_actions:
            self.setActiveAction(self._searched_actions[0])

    def _on_search_submitted(self):
        """
        Internal callback function that is called when search is submitted.
        """

        if self._block_submit:
            self._close()
            return

        action = self.sender()
        if not isinstance(action, QAction):
            if self._searched_actions:
                action = self._searched_actions[0]
            else:
                self._close()
                return

        text = action.text()
        node_type = self._node_dict.get(text)
        if node_type:
            self.searchSubmitted.emit(node_type)

        self._close()


class NodesTabSearchLineEdit(QLineEdit):
    """
    Custom QLineEdit that is used to show the search line edit.
    """

    tabPressed = Signal()

    def __init__(self, parent: NodesTabSearchWidget | None = None):
        super().__init__(parent=parent)

        self.setMinimumSize(200, 22)
        self.setAttribute(Qt.WA_MacShowFocusRect, False)

        text_color = tuple(
            map(
                lambda i, j: i - j,
                (255, 255, 255),
                uiconsts.NODE_GRAPH_BACKGROUND_COLOR,
            )
        )
        selected_color = self.palette().highlight().color().getRgb()
        style_dict = {
            "QLineEdit": {
                "color": "rgb({0},{1},{2})".format(*text_color),
                "border": "1px solid rgb({0},{1},{2})".format(*selected_color),
                "border-radius": "3px",
                "padding": "2px 4px",
                "margin": "2px 4px 8px 4px",
                "background": "rgb({0},{1},{2})".format(
                    *uiconsts.NODE_GRAPH_BACKGROUND_COLOR
                ),
                "selection-background-color": "rgba({0},{1},{2},200)".format(
                    *selected_color
                ),
            }
        }
        stylesheet = ""
        for css_class, css in style_dict.items():
            style = "{} {{\n".format(css_class)
            for elm_name, elm_val in css.items():
                style += "  {}:{};\n".format(elm_name, elm_val)
            style += "}\n"
            stylesheet += style
        self.setStyleSheet(stylesheet)

    def keyPressEvent(self, event: QKeyEvent):
        """
        Overrides QLineEdit key press event to emit tab pressed signal.

        :param event: key event.
        """

        super().keyPressEvent(event)

        if event.key() == Qt.Key_Tab:
            self.tabPressed.emit()
