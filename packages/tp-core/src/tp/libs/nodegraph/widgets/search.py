from __future__ import annotations

import re
import typing

from Qt.QtCore import Qt, Signal, QObject
from Qt.QtWidgets import QLineEdit, QMenu, QAction, QWidgetAction
from Qt.QtGui import QCursor, QPixmap, QIcon, QKeyEvent

from ..core import consts
from ..views import uiconsts

if typing.TYPE_CHECKING:
    from ..core.graph import NodeGraph
    from ..core.datatypes import DataType


class NodesTabSearchWidget(QMenu):
    """
    Custom QMenu that is used to show the search widget menu.
    """

    searchSubmitted = Signal(str, str, str)

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._rebuild: bool = True
        self._block_submit: bool = False
        self._menus: dict[str, QMenu] = {}
        self._category_menus: dict[str, dict[str, QMenu]] = {}
        self._actions: dict[str, QAction] = {}
        self._searched_actions: list[QAction] = []
        self._data_type_filter: DataType | None = None
        self._functions_first: bool = False

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

    def populate(
        self,
        graph: NodeGraph | None,
        force: bool = False,
        data_type_filter: DataType | None = None,
        functions_first: bool | None = None,
    ):
        """
        Populates the popup menu with the given graph nodes and functions.

        :param graph: graph to search for nodes.
        :param force: force the rebuilding of the menu.
        :param data_type_filter: data type filter.
        :param functions_first: flag to show functions first
        """

        if not graph:
            return

        self._data_type_filter = data_type_filter

        if functions_first is not None:
            self._functions_first = functions_first

        if self._rebuild or force:
            self._clear_actions()
            self._set_menus_visible(False)
            for menu in self._menus.values():
                self.removeAction(menu.menuAction())
            self._actions.clear()
            self._menus.clear()
            self._category_menus.clear()

            self._build_menu(graph)
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
        del self._searched_actions[:]

    def _add_registered_nodes(self, graph: NodeGraph, search_filter: str = ""):
        """
        Internal function that adds registered nodes to the search widget.

        :param graph: node graph.
        :param search_filter: search filter.
        """

        for node_id, node_class in graph.factory.node_classes.items():
            if node_class.CATEGORY == consts.INTERNAL_CATEGORY:
                continue
            node_label = node_class.PALETTE_LABEL or node_class.NODE_NAME
            filter_matched = search_filter and (
                re.search(search_filter, node_label, re.IGNORECASE) is not None
                or re.search(search_filter, node_class.CATEGORY, re.IGNORECASE)
                is not None
            )
            if search_filter and not filter_matched:
                continue
            self._add_node_action(
                node_id,
                node_label,
                category=node_class.CATEGORY,
                icon_path=node_class.ICON_PATH,
            )

    def _add_registered_functions(self, graph: NodeGraph, search_filter: str = ""):
        """
        Internal function that adds registered functions to the search widget.

        :param graph: node graph.
        :param search_filter: search filter.
        """

        keys = list(graph.factory.function_data_types)
        keys.sort()

        for data_type_name in keys:
            # If data type filter is set, skip if data type does not match filter type class.
            if data_type_name != "UNBOUND" and self._data_type_filter:
                if not issubclass(
                    self._data_type_filter.type_class,
                    graph.factory.data_type_by_name(data_type_name).type_class,
                ):
                    continue

            function_signatures = graph.factory.function_signatures_by_type_name(
                data_type_name
            )
            for function_signature in function_signatures:
                function = graph.factory.function_by_type_name_and_signature(
                    data_type_name, function_signature
                )
                if not function:
                    continue
                icon_path = function.icon
                nice_name = function.nice_name
                sub_category_name = function.category or "General"
                function_name = nice_name or function_signature

                # If search filter is set, skip if search filter does not match palette name or sub category name.
                filter_matched = bool(search_filter) and (
                    re.search(search_filter, function_name, re.IGNORECASE) is not None
                    or re.search(
                        search_filter, sub_category_name, re.IGNORECASE is not None
                    )
                )
                if search_filter and not filter_matched:
                    continue

                self._add_node_action(
                    "tp.nodegraph.nodes.FunctionNode",
                    function_name,
                    func_signature=function_signature,
                    category=f"Functions/{sub_category_name}",
                    icon_path=icon_path,
                )

    def _build_menu(self, graph: NodeGraph):
        """
        Internal function that builds the search menu.

        :param graph: node graph.
        """

        node_types = list(graph.factory.node_classes.keys())
        node_types.sort()

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
            menus = menu_tree.get(i, {})
            for menu_path, menu in menus.items():
                self._menus[menu_path] = menu
                if i == 0:
                    self.addMenu(menu)
                else:
                    parent_menu = self._menus[menu.property("parent_path")]
                    parent_menu.addMenu(menu)

        self._add_registered_nodes(graph)
        self._add_registered_functions(graph)

    def add_category_menu(
        self, name: str, parent_menu_path: str, parent: QMenu | None = None
    ) -> QMenu:
        """
        Adds a category menu.

        :param name: name of the category.
        :param parent_menu_path: parent menu path.
        :param parent: parent menu.
        :return: category menu.
        """

        parent = parent or self
        new_menu = QMenu(name)
        new_menu.keyPressEvent = self.keyPressEvent
        new_menu.setStyleSheet(self._menu_stylesheet)
        self._category_menus.setdefault(parent_menu_path, {})[name] = new_menu
        if parent:
            parent.addMenu(new_menu)

        return new_menu

    def get_or_create_category_menu(
        self, name: str, parent_menu_path: str, parent: QMenu | None = None
    ) -> QMenu:
        """
        Returns the category menu with the given name. If the category menu does not exist, it is created.


        :param name: name of the category.
        :param parent_menu_path: parent menu path.
        :param parent:  parent menu.
        :return: category menu.
        """

        found_category = self._category_menus.get(parent_menu_path, {}).get(name, None)
        return found_category or self.add_category_menu(
            name, parent_menu_path=parent_menu_path, parent=parent
        )

    def _add_node_action(
        self,
        node_id: str,
        label_text: str,
        func_signature: str = "",
        category: str = "",
        icon_path: str | None = None,
    ) -> QAction:
        """
        Internal function that adds a node action.

        :param node_id: node id.
        :param label_text: label text.
        :param func_signature: function signature.
        :param category: category of the node.
        :param icon_path: icon path.
        :return: newly created node action.
        """

        menu_path = ".".join(node_id.split(".")[:-1])

        parent_menu = self._menus[menu_path]
        if category:
            category_path = category.split("/")
            for category_name in category_path:
                parent_menu = self.get_or_create_category_menu(
                    category_name, menu_path, parent=parent_menu
                )

        pixmap = QPixmap(icon_path) if icon_path else QPixmap()
        action = QAction(self)
        action.setText(label_text)
        action.setIcon(QIcon(pixmap))
        action.triggered.connect(self._on_search_submitted)
        self._actions[label_text] = action
        if parent_menu:
            parent_menu.addAction(action)
        else:
            self.addAction(action)
        json_data = {
            "title": action.text(),
            "func_signature": func_signature,
            "node_id": node_id,
        }
        action.setData(json_data)

        return action

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

        :param node_type: node type.
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

        node_data = action.data()
        node_id = node_data.get("node_id")
        func_signature = node_data.get("func_signature")
        func_name = node_data.get("title", "")
        text = action.text()
        if node_id:
            self.searchSubmitted.emit(node_id, func_signature, func_name)

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
