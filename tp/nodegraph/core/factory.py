from __future__ import annotations

import os
import logging
import pathlib
from types import ModuleType
from typing import Type, Any

from Qt.QtGui import QColor

from . import consts, exceptions
from .node import BaseNode, Node
from .datatypes import DataType, Exec, String, Numeric, Boolean, List, Dict
from ..nodes.node_logger import LoggerNode
from ..nodes.node_branch import BranchNode
from ..nodes.node_backdrop import BackdropNode
from ...python import modules

logger = logging.getLogger(__name__)


class NodeFactory:
    """Class that handles the registration and creation of all the nodes in the application."""

    def __init__(self):
        super().__init__()

        self._node_classes: dict[str, Type[BaseNode]] = {}
        self._node_names: dict[str, list[str]] = {}
        self._node_aliases: dict[str, str] = {}
        self._data_types: dict[str, DataType] = {}

        self._load()

    @property
    def data_types(self) -> dict[str, DataType]:
        """
        Getter method that returns the data types.

        :return: data types.
        """

        return self._data_types

    @property
    def node_classes(self) -> dict[str, Type[BaseNode]]:
        """
        Getter method that returns the node classes.

        :return: node classes.
        """

        return self._node_classes

    @property
    def node_names(self) -> dict[str, list[str]]:
        """
        Getter method that returns the node names.

        :return: node names.
        """

        return self._node_names

    @property
    def node_aliases(self) -> dict[str, str]:
        """
        Getter method that returns the node aliases.

        :return: node aliases.
        """

        return self._node_aliases

    def is_data_type_registered(self, name: str) -> bool:
        """
        Returns whether data type is registered.

        :param name: Name of the data type to check.
        :return: True if the data type is registered; False otherwise.
        """

        return name.upper() in self._data_types

    def register_data_type(
        self,
        type_name: str,
        type_class: Type,
        color: tuple[int, int, int, int] | QColor,
        label: str = "custom_data",
        default_value: Any = None,
    ):
        """
        Register a new data type in the registry.

        :param type_name: Name of the data type to register.
        :param type_class: Class of the data type to register.
        :param color: Color of the data type to register.
        :param label: Label of the data type to register.
        :param default_value: Default value of the data type to register.
        """

        if type_name in self._data_types:
            logger.error(f'Data type "{type_name}" is already registered.')
            raise exceptions.DataTypeAlreadyRegisteredError(type_name)

        color = color if isinstance(color, QColor) else QColor(*color)
        self._data_types[type_name.upper()] = DataType(
            type_name, type_class, color, label, default_value
        )

    def clear_registered_data_types(self):
        """
        Clear all registered data types.
        """

        self._data_types.clear()

    def register_node(self, node_class: Type[BaseNode], alias: str | None = None):
        """
        Register a new node in the registry.

        :param node_class: Class of the node to register.
        :param alias: optional alias of the node to register.
        """

        if node_class is None:
            return

        name = node_class.NODE_NAME
        # noinspection PyTypeChecker
        node_id: str = node_class.type

        if node_id in self._node_classes:
            raise exceptions.NodeAlreadyRegisteredError(node_id)

        self._node_classes[node_id] = node_class

        if self._node_names.get(name):
            self._node_names[name].append(node_id)
        else:
            self._node_names[name] = [node_id]

        if alias:
            if alias in self._node_aliases:
                raise exceptions.NodeAliasAlreadyRegisteredError(alias)
            self._node_aliases[alias] = node_id

    def node_class_by_id(self, node_id: str) -> Type[BaseNode | Node]:
        """
        Returns the node class by its ID.

        :param node_id: ID of the node to get.
        :return: node class.
        """

        node_class = self._node_classes.get(node_id)
        if not node_class:
            node_id_from_alias = self._node_aliases.get(node_id)
            if node_id_from_alias:
                node_class = self._node_classes.get(node_id_from_alias)
        if not node_class:
            raise exceptions.NodeNotFoundError(node_id)

        return node_class

    def create_node(self, node_id: int | str) -> BaseNode:
        """
        Creates a new node.

        :param node_id: ID of the node to create.
        :return: created node.
        """

        if node_id in self._node_aliases:
            node_id = self._node_aliases[node_id]

        node_class = self._node_classes.get(node_id)
        if not node_class:
            raise exceptions.NodeNotFoundError(node_id)

        return node_class()

    def clear_registered_nodes(self):
        """
        Clear all registered nodes.
        """

        self._node_classes.clear()
        self._node_names.clear()
        self._node_aliases.clear()

    def clear(self):
        """
        Resets the factory to its initial state.
        """

        self.clear_registered_nodes()
        self.clear_registered_data_types()

    def _register_basic_nodes(self):
        """
        Internal function that register basic nodes.
        """

        self.register_node(BackdropNode, "backdrop")
        self.register_node(LoggerNode, "logger")
        self.register_node(BranchNode, "branch")

    def _register_basic_data_types(self):
        """
        Internal function that register basic data types.
        """

        for data_type in [Exec, String, Numeric, Boolean, List, Dict]:
            self._data_types[data_type.name] = data_type

    def _load(self):
        """
        Internal function that handles the initial loading of the factory.
        """

        self.clear()

        self._register_basic_nodes()
        self._register_basic_data_types()

        # Load of custom nodes and data types.
        success_count: int = 0
        plugin_files: dict[str, str] = {}
        nodes_paths = os.environ.get(consts.NODE_PATHS_ENV_VAR, "").split(os.pathsep)
        for nodes_path in nodes_paths:
            if not nodes_path:
                continue
            if not os.path.isdir(nodes_path):
                logger.warning(f'Nodes path "{nodes_path}" does not exist.')
                continue
            for file_name_with_ext in os.listdir(nodes_path):
                if file_name_with_ext.endswith(".py") and file_name_with_ext.startswith(
                    "node_"
                ):
                    file_name = os.path.splitext(file_name_with_ext)[0]
                    plugin_files[file_name] = pathlib.Path(
                        nodes_path, file_name_with_ext
                    ).as_posix()
        for file_name, file_path in plugin_files.items():
            module: ModuleType | None = None
            # noinspection PyBroadException
            try:
                module = modules.import_module(
                    modules.file_path_to_module_path(file_path)
                )
                if not module:
                    module = modules.import_module(file_path)
            except Exception:
                logger.exception(
                    f'Error while importing module: "{file_path}"', exc_info=True
                )
            if not module:
                continue
            # noinspection PyBroadException
            try:
                module.register_plugin(self)
                success_count += 1
            except AttributeError:
                continue
            except Exception:
                logger.exception(f"Failed to register plugin: {file_path}")

        logger.info(f"Successfully registered {success_count} node graph plugins.")
