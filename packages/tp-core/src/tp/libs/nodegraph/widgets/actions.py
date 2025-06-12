from __future__ import annotations

import typing
from typing import Type

from Qt.QtCore import Signal
from Qt.QtWidgets import QMenu, QAction

from ..views import uiconsts

if typing.TYPE_CHECKING:
    from ..core.node import BaseNode
    from ..core.graph import NodeGraph


class BaseMenu(QMenu):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._graph: NodeGraph | None = None
        self._node_class: Type[BaseNode] | None = None

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
            "QMenu::item:disabled": {
                "color": "rgba({0},{1},{2},60)".format(*text_color),
                "background-color": "rgba({0},{1},{2},200)".format(
                    *uiconsts.NODE_GRAPH_BACKGROUND_COLOR
                ),
            },
            "QMenu::separator": {
                "height": "1px",
                "background": "rgba({0},{1},{2}, 50)".format(*text_color),
                "margin": "4px 8px",
            },
        }
        stylesheet = ""
        for css_class, css in style_dict.items():
            style = "{} {{\n".format(css_class)
            for element_Name, element_value in css.items():
                style += f"  {element_Name}:{element_value};\n"
            style += "}\n"
            stylesheet += style
        self.setStyleSheet(stylesheet)

    @property
    def graph(self) -> NodeGraph | None:
        """
        Returns the graph linked with this menu.

        :return: node graph.
        """

        return self._graph

    @graph.setter
    def graph(self, value: NodeGraph | None):
        """
        Sets the graph linked with this menu.

        :param value: node graph.
        """

        self._graph = value

    @property
    def node_class(self) -> Type[BaseNode] | None:
        """
        Returns the node class linked with this menu.

        :return: node class.
        """

        return self._node_class

    @node_class.setter
    def node_class(self, value: Type[BaseNode] | None):
        """
        Sets the node class linked with this menu.

        :param value: node class.
        """

        self._node_class = value

    def menu(self, name: str, node_id: str | None = None) -> BaseMenu:
        """
        Returns the menu with the given name.

        :param name: name of the menu to retrieve.
        :param node_id: optional node ID to filter the menu by node class.
        :return: found menu.
        """

        found_menu: BaseMenu | None = None
        for action in self.actions():
            # noinspection PyTypeChecker
            menu: BaseMenu = action.menu()
            if not menu:
                continue
            if menu.title() == name:
                found_menu = menu
                break
            if node_id and menu.node_class:
                node = menu.graph.node_by_id(node_id)
                if isinstance(node, menu.node_class):
                    found_menu = menu
                    break

        return found_menu

    def menus(self, node_class: Type[BaseNode] | None = None) -> list[BaseMenu]:
        """
        Returns the menus linked with this menu.

        :param node_class: optional node class to filter the menus.
        :return: list[BaseMenu]
        """

        found_menus: list[BaseMenu] = []
        for action in self.actions():
            # noinspection PyTypeChecker
            menu: BaseMenu = action.menu()
            if not menu or not menu.node_class:
                continue
            if issubclass(menu.node_class, node_class):
                found_menus.append(menu)

        return found_menus


class NodeGraphAction(QAction):
    """
    Class used to trigger node graph actions.
    """

    executed = Signal(object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._graph: NodeGraph | None = None

        self.triggered.connect(self._on_triggered)

    @property
    def graph(self) -> NodeGraph | None:
        """
        Returns the graph linked with this action.

        :return: node graph.
        """

        return self._graph

    @graph.setter
    def graph(self, value: NodeGraph | None):
        """
        Sets the graph linked with this action.

        :param value: node graph.
        """

        self._graph = value

    def action(self, name: str) -> QAction:
        """
        Returns the action with the given name.

        :param name: name of the action to retrieve.
        :return: found action.
        """

        found_action: QAction | None = None
        for action in self.actions():
            if action.text() == name:
                found_action = action
                break

        return found_action

    def _on_triggered(self):
        """
        Internal function that is called when the action is triggered.
        """

        self.executed.emit(self.graph)


class NodeAction(NodeGraphAction):
    """
    Class used to trigger node actions.
    """

    executed = Signal(object, object)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._node_id: str | None = None

    @property
    def node_id(self) -> str | None:
        """
        Returns the node ID linked with this action.

        :return: str
        """

        return self._node_id

    @node_id.setter
    def node_id(self, value: str | None):
        """
        Sets the node ID linked with this action.

        :param value: str
        """

        self._node_id = value

    def _on_triggered(self):
        """
        Internal function that is called when the action is triggered.
        """

        node = self.graph.node_by_id(self.node_id)
        self.executed.emit(self.graph, node)
