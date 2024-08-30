from __future__ import annotations

import os
import logging
import pathlib
import numbers
from types import ModuleType
from typing import Type, Any
from dataclasses import dataclass

from Qt.QtGui import QColor

from . import consts, exceptions
from .node import BaseNode, Node
from .datatypes import DataType
from ..nodes.node_logger import LoggerNode
from ..nodes.node_branch import BranchNode
from ..nodes.node_backdrop import BackdropNode
from ...python import modules

logger = logging.getLogger(__name__)


@dataclass
class Function:
    """
    Class that defines all functions.
    """

    reference: callable
    inputs: dict
    outputs: dict
    doc: str
    icon: str
    nice_name: str
    category: str
    default_values: list[Any]


class NodeFactory:
    """Class that handles the registration and creation of all the nodes in the application."""

    def __init__(self):
        super().__init__()

        self._node_classes: dict[str, Type[BaseNode]] = {}
        self._node_names: dict[str, list[str]] = {}
        self._node_aliases: dict[str, str] = {}
        self._data_types: dict[str, DataType] = {}
        self._functions: dict[str, dict[str, Function]] = {}

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

    @property
    def function_data_types(self) -> list[str]:
        """
        Getter method that returns the function data types.

        :return: function data types.
        """

        return list(self._functions.keys())

    def is_data_type_registered(self, name: str) -> bool:
        """
        Returns whether data type is registered.

        :param name: Name of the data type to check.
        :return: True if the data type is registered; False otherwise.
        """

        return name.upper() in self._data_types

    def register_data_type(
        self,
        type_name: str | DataType,
        type_class: Type | None = None,
        color: tuple[int, int, int, int] | QColor | None = None,
        label: str | None = "custom_data",
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

        if isinstance(type_name, DataType):
            if type_name.name in self._data_types:
                logger.error(f'Data type "{type_name.name}" is already registered.')
                raise exceptions.DataTypeAlreadyRegisteredError(type_name.name)
            self._data_types[type_name.name.upper()] = type_name
        else:
            if type_name in self._data_types:
                logger.error(f'Data type "{type_name}" is already registered.')
                raise exceptions.DataTypeAlreadyRegisteredError(type_name)

            color = color if isinstance(color, QColor) else QColor(*color)
            data_type = DataType(type_name, type_class, color, label, default_value)
            self._data_types[type_name.upper()] = data_type

    def runtime_data_types(
        self, names: bool = False, classes: bool = False
    ) -> list[str, Type[DataType] | DataType]:
        """
        Returns all runtime data types.

        :param names: whether to include names of the data types.
        :param classes: whether to include classes of the data types.
        :return: runtime data types.
        """

        result: list[str, Type[DataType] | DataType] = []
        for data_type in self._data_types.values():
            if not data_type.is_runtime:
                continue
            if names:
                result.append(data_type.name)
            elif classes:
                result.append(data_type.type_class)
            else:
                result.append(data_type)

        return result

    def data_type_name(self, data_type: DataType) -> str:
        """
        Returns the name of the data type.

        :param data_type: Data type to get name of.
        :return: str
        :raises IndexError: If data type is not found.
        """

        try:
            type_name = [
                data_type_name
                for data_type_name, _data_type in self._data_types.items()
                if _data_type == data_type
            ][0]
        except IndexError:
            logger.error(f"Failed to find data type for class {data_type.type_class}")
            raise IndexError

        return type_name

    def data_type_by_name(self, type_name: str) -> DataType:
        """
        Returns the data type by its name.

        :param type_name: Name of the data type to get.
        :return: data type.
        :raises KeyError: If data type is not found.
        """

        try:
            return self._data_types[type_name.upper()]
        except KeyError:
            logger.exception(f"Unregistered data type: {type_name}")
            raise

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

    def register_function(
        self,
        func: callable,
        source_data_type: DataType,
        inputs_dict: dict | None = None,
        outputs_dict: dict | None = None,
        default_values: list[Any] | None = None,
        nice_name: str | None = None,
        subtype: str | None = None,
        category: str = "General",
        docstring: str = "",
        icon_path: str | None = None,
    ):
        """
        Register a new function in the registry.

        :param func: function to register.
        :param source_data_type: data type of the function to register.
        :param inputs_dict: inputs of the function to register.
        :param outputs_dict: outputs of the function to register.
        :param default_values: default values of the function to register.
        :param nice_name: nice name of the function to register.
        :param subtype: subtype of the function to register.
        :param category: category of the function to register.
        :param docstring: docstring of the function to register.
        :param icon_path: icon path of the function to register.
        """

        inputs_dict = inputs_dict or {}
        outputs_dict = outputs_dict or {}
        default_values = default_values or []

        if source_data_type:
            data_type_name = self.data_type_name(source_data_type)
            source_class: Type = source_data_type.type_class
            if source_class:
                signature = (
                    f"{source_class.__module__}.{source_class.__name__}.{func.__name__}"
                )
            else:
                signature = f"{func.__module__}.{func.__name__}"
        else:
            data_type_name = "UNBOUND"
            signature = f"{func.__module__}({func.__name__})"

        if subtype:
            signature = f"{signature}({subtype})"

        new_function = Function(
            reference=func,
            inputs=inputs_dict,
            outputs=outputs_dict,
            doc=docstring,
            icon=icon_path or "",
            nice_name=nice_name,
            category=category,
            default_values=default_values,
        )

        if data_type_name not in self._functions:
            self._functions[data_type_name] = {}

        self._functions[data_type_name][signature] = new_function

    def function_from_signature(self, signature: str) -> Function | None:
        """
        Returns the function by its signature.

        :param signature: function signature.
        :return: function that matches given signature.
        """

        for functions in self._functions.values():
            if signature in functions:
                return functions[signature]

        return None

    def function_signatures_by_type_name(self, type_name: str) -> list[str]:
        """
        Returns all function signatures.

        :param type_name: Name of the data type to get function signatures of.
        :return: function signatures.
        """

        return list(self._functions.get(type_name, {}).keys())

    def function_by_type_name_and_signature(
        self, type_name: str, signature: str
    ) -> Function | None:
        """
        Returns the function by its type name and signature.

        :param type_name: data type name.
        :param signature: function signature.
        :return: function that matches give ntype name and signature.
        """

        return self._functions.get(type_name, {}).get(signature, None)

    def clear_registered_functions(self):
        """
        Clear all registered functions.
        """

        self._functions.clear()

    def clear(self):
        """
        Resets the factory to its initial state.
        """

        self.clear_registered_nodes()
        self.clear_registered_data_types()
        self.clear_registered_functions()

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

        basic_data_types = [
            DataType("Exec", type(None), QColor("#FFFFFF"), "", None),
            DataType("String", str, QColor("#A203F2"), "Name", ""),
            DataType("Numeric", numbers.Complex, QColor("#DEC017"), "Number", 0.0),
            DataType("Boolean", bool, QColor("#C40000"), "Condition", False),
            DataType("List", list, QColor("#0BC8F1"), "List", [], is_runtime=True),
            DataType("Dict", dict, QColor("#0BC8F1"), "Dict", {}),
        ]

        for data_type in basic_data_types:
            self.register_data_type(data_type)

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

        # First pass: Add files starting with "node_core"
        for nodes_path in nodes_paths:
            if not nodes_path:
                continue
            if not os.path.isdir(nodes_path):
                logger.warning(f'Nodes path "{nodes_path}" does not exist.')
                continue
            for file_name_with_ext in os.listdir(nodes_path):
                if file_name_with_ext.endswith(".py") and file_name_with_ext.startswith(
                    "node_core_"
                ):
                    file_name = os.path.splitext(file_name_with_ext)[0]
                    plugin_files[file_name] = pathlib.Path(
                        nodes_path, file_name_with_ext
                    ).as_posix()

        # Second pass: Add other files starting with "node_" but not "node_core"
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
                if hasattr(module, "register_plugin") and callable(
                    module.register_plugin
                ):
                    module.register_plugin(self)
                    success_count += 1
            except Exception:
                logger.exception(f"Failed to register plugin: {file_path}")

        logger.info(f"Successfully registered {success_count} node graph plugins.")
