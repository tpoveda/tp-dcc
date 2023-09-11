#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract implementation for DCC menus
"""

from __future__ import annotations

import re
from typing import Callable, Any
from pathlib import Path

from tp.core import log
from tp.common.python import helpers, decorators

logger = log.tpLogger


class AbstractMenuItem:
    def __init__(
            self, label: str = '', command: str | Callable = '', icon: str = '', tooltip: str = '',
            separator: bool = False, items: list[dict] | None = None, parent: AbstractMenuItem | None = None,
            parent_path: str = '', native_node: Any = None, kwargs: dict | None = None, data: dict | None = None,
            id: str | None = None):
        super().__init__()

        self._name = ''
        self._label = label
        self._command = command
        self._icon = icon
        self._tooltip = tooltip
        self._separator = separator
        self._kwargs = kwargs or {}
        self._data = data or {}
        self._id = id
        self._parent = parent
        self._parent_path = parent_path.replace(' ', '_') if parent_path else None
        self._native_node = native_node
        self._config_path = None

        self._generate_default_id()
        self._children = [self.__class__(**item, parent=self) for item in items] if items else []

    def __dict__(self) -> dict:
        config = {}
        if self._label:
            config['label'] = self._label
        if self._command:
            config['command'] = self._command
        if self._icon:
            config['icon'] = self._icon
        if self._tooltip:
            config['tooltip'] = self._tooltip
        if self._separator:
            config['separator'] = self._separator
        if self._children:
            child_configs = []
            for child in self._children:
                child_config = child.__dict__()
                child_config.pop('parent', None)        # only parent of the top node if necessary
                child_configs.append(child_config)
            config['children'] = child_configs
        if self._parent_path and helpers.is_string(self._parent_path):
            config['parent_path'] = self._parent_path
        if self._kwargs:
            config['kwargs'] = self._kwargs
        if self._data:
            config['data'] = self._data

        return config

    @property
    def id(self) -> str:
        return self._id

    @property
    def label(self) -> str:
        return self._label

    @property
    def parent(self) -> AbstractMenuItem:
        return self._parent

    @property
    def parent_path(self) -> str:
        return self._parent_path

    @property
    def children(self) -> list[AbstractMenuItem]:
        return self._children

    @children.setter
    def children(self, value: list[AbstractMenuItem]):
        self._children = value

    @property
    def command(self) -> str | Callable:
        return self._command

    @property
    def tooltip(self) -> str:
        return self._tooltip

    @property
    def icon(self) -> str:
        return self._icon

    @classmethod
    def load(cls, arg: dict | str | AbstractMenuItem) -> AbstractMenuItem:
        """
        Loads menu from given dictionary, configuration file or another already created menu (a copy of that menu will
        be created).

        :param dict or str or type data: menu data to load.
        :return: loaded menu instance.
        :rtype: AbstractMenu
        """

        if isinstance(arg, (str, Path)):
            return cls.load_config(arg)
        elif isinstance(arg, dict):
            return cls(**arg)
        elif isinstance(arg, AbstractMenuItem):
            return cls(**arg.__dict__())

    @classmethod
    def load_config(cls, config_path: str) -> AbstractMenuItem:
        """
        Loads menu from given configuration file.

        :param str config_path: absolute file path pointing to a valid configuration file containing the data of the
            menu to create.
        :return: newly created menu instance.
        :rtype: AbstractMenu
        """

        raise NotImplementedError

    def root(self) -> AbstractMenuItem:
        """
        Returns the root menu.

        :return: root menu.
        :rtype: AbstractMenu
        """

        if self.parent and isinstance(self.parent, AbstractMenuItem):
            return self.parent.root()

        return self

    def setup(self, parent_native_node: Any = None, backlink: bool = True) -> Any:
        """
        Instantiates a menu item in the DCC from the menu node data.

        :param Any parent_native_node: DCC specific menu node to parent to. This will depend on the specific DCC. For
            example, in Maya, we should pass the full menu path.
        :param bool backlink: whether to add an attribute to the DCC native node instance to this instance.
        :return: DCC native node that holds the newly created menu item.
        :rtype: Any
        """

        parent_native_node = parent_native_node or self._default_root_parent()
        if self._separator:
            self._native_node = self._setup_separator(parent_native_node=parent_native_node)
        elif self._command:
            self._native_node = self._setup_menu_item(parent_native_node=parent_native_node)
        elif self._children:
            self._native_node = self._setup_sub_menu(parent_native_node=parent_native_node)
            for child in self._children:
                child.setup(parent_native_node=self._native_node)
        else:
            logger.warning(f'Cannot create a MenuItem that has no command or children: {self._label}')

        if backlink:
            try:
                self._native_node.menu_node = self
            except AttributeError:
                logger.warning(f'Could not set backlink on {self._native_node} to {self}')

        return self._native_node

    def run(self, *args: tuple[Any]):
        """
        Executes the command.

        :param tuple[Any] args: optional arguments to pass to the command.
        """

        try:
            if helpers.is_string(self._command):
                exec(self._command)
            else:
                self._command()
        except Exception as err:
            logger.error(err, exc_info=True)

    def _default_root_parent(self) -> Any:
        """
        Internal function that returns the default parent for the root node.

        :return: root parent instance.
        :rtype: Any
        """

        return None

    def _generate_default_id(self):
        """
        Internal function that generates a unique identifier for this menu.
        """

        if self._id:
            return
        label = self._label if self._label else 'TODO'
        label = re.sub('[^0-9a-zA-Z]+', '_', label)

        # ID is generated using the parent paths.
        # TODO: if the parent changes, this ID also should change
        parent_names = []
        parent = self._parent
        while parent:
            parent_names.append(parent.id)
            parent = parent.parent
        parent_names.reverse()
        parent_names.append(label)
        self._id = '_'.join(parent_names)

    @decorators.abstractmethod
    def teardown(self):
        """
        Teardown menu item.
        """

        raise NotImplementedError('abstract DCC menu function teardown() not implemented!')

    @decorators.abstractmethod
    def _setup_separator(self, parent_native_node: Any) -> Any:
        """
        Internal function that creates a separator.

        :param Any parent_native_node: DCC native node that points to the parent separator.
        :return: DCC native node of the newly created separator.
        :rtype: Any
        """

        raise NotImplementedError('abstract DCC menu function _setup_separator() not implemented!')

    @decorators.abstractmethod
    def _setup_menu_item(self, parent_native_node: Any) -> Any:
        """
        Internal function that creates a menu item.

        :param Any parent_native_node: DCC native node that points to the parent menu item.
        :return: DCC native node of the newly created menu item.
        :rtype: Any
        """

        raise NotImplementedError('abstract DCC menu function _setup_menu_item() not implemented!')

    @decorators.abstractmethod
    def _setup_sub_menu(self, parent_native_node: Any) -> Any:
        """
        Internal function that creates a sub menu.

        :param Any parent_native_node: DCC native node that points to the parent menu item.
        :return: DCC native node of the newly created sub menu.
        :rtype: Any
        """

        raise NotImplementedError('abstract DCC menu function _setup_sub_menu() not implemented!')
