from __future__ import annotations

import re
import typing
from typing import Callable

from Qt.QtCore import Qt
from Qt.QtWidgets import QShortcut
from Qt.QtGui import QKeySequence

from .exceptions import NodeGraphMenuError
from ..widgets.actions import BaseMenu, NodeGraphAction

if typing.TYPE_CHECKING:
    from .graph import NodeGraph


class NodeGraphMenu:
    """
    Class used to trigger node graphs menus.
    """

    def __init__(self, graph: NodeGraph, menu: BaseMenu):
        super().__init__()

        self._graph = graph
        self._menu = menu
        self._name = menu.title()
        self._menus: dict[str, NodeGraphMenu] = {}
        self._commands: dict[str, NodeGraphMenuCommand] = {}
        self._items: list[NodeGraphMenuCommand | NodeGraphMenu | None] = []

    def __repr__(self) -> str:
        """
        Returns a string representation of the object.

        :return: object string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object {hex(id(self))}>'

    @property
    def menu(self) -> BaseMenu:
        """
        Returns the menu object.

        :return: BaseMenu
        """

        return self._menu

    @property
    def name(self) -> str:
        """
        Returns the menu name.

        :return: str
        """

        return self._name

    def add_separator(self):
        """
        Adds a separator to the menu.
        """

        self._menu.addSeparator()
        self._items.append(None)

    def add_command(
        self, name: str, func: Callable, shortcut: str | None = None
    ) -> NodeGraphMenuCommand:
        """
        Adds a command to the menu.

        :param name: command name.
        :param func: command function.
        :param shortcut: optional shortcut key
        :return: added node graph menu command.
        """

        action = NodeGraphAction(name, parent=self._graph.viewer)
        action.graph = self._graph
        action.setShortcutVisibleInContextMenu(True)
        if shortcut:
            self._set_shortcut(action, shortcut)
        if func:
            action.executed.connect(func)
        self._menu.addAction(action)
        command = NodeGraphMenuCommand(self._graph, action, func)
        self._commands[name] = command
        self._items.append(command)

        return command

    def add_menu(self, name: str) -> NodeGraphMenu:
        """
        Adds a child menu to the current menu.

        :param name: menu name.
        :return: added menu.
        """

        if name in self._menus:
            raise NodeGraphMenuError(name)

        base_menu = BaseMenu(name, parent=self._menu)
        self._menu.addMenu(base_menu)
        menu = NodeGraphMenu(self._graph, menu=base_menu)
        self._menus[name] = menu
        self._items.append(menu)

        return menu

    @staticmethod
    def _set_shortcut(action: NodeGraphAction, shortcut: str | QShortcut):
        """
        Sets the shortcut of the given action.

        :param action: action to set the shortcut to.
        :param shortcut: shortcut to set.
        """

        if isinstance(shortcut, str):
            search = re.search(r"(?:\.|)QKeySequence\.(\w+)", shortcut)
            if search:
                shortcut = getattr(QKeySequence, search.group(1))
            elif all([i in ["Alt", "Enter"] for i in shortcut.split("+")]):
                # noinspection PyTypeChecker
                shortcut = QKeySequence(Qt.ALT | Qt.Key_Return)
            elif all([i in ["Return", "Enter"] for i in shortcut.split("+")]):
                shortcut = Qt.Key_Return
        if shortcut:
            action.setShortcut(shortcut)


class NodesMenu(NodeGraphMenu):
    """
    Class used to trigger nodes menus.
    """

    pass


class NodeGraphMenuCommand:
    """
    Class used to trigger node graph menu commands.
    """

    def __init__(self, graph: NodeGraph, action: NodeGraphAction, func: Callable):
        super().__init__()

        self._graph = graph
        self._action = action
        self._name = action.text()
        self._func = func

    def __repr__(self) -> str:
        """
        Returns a string representation of the object.

        :return: object string representation.
        """

        return f'<{self.__class__.__name__}("{self._name}") object {hex(id(self))}>'

    @property
    def action(self) -> NodeGraphAction:
        """
        Returns the action object.

        :return: NodeGraphAction
        """

        return self._action

    @property
    def name(self) -> str:
        """
        Returns the command name.

        :return: str
        """

        return self._name

    @property
    def slot_function(self) -> Callable:
        """
        Returns the slot function executed by this command.

        :return: Callable
        """

        return self._func
