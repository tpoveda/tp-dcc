from __future__ import annotations

import typing
from typing import Any
from collections import OrderedDict

from tp.core import log
from tp.common.qt import api as qt
from tp.common.nodegraph import registers


if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.graph import NodeGraph
    from tp.common.nodegraph.nodes.node_getset import GetNode, SetNode

logger = log.tpLogger


class SceneVars:

    class Signals(qt.QObject):
        valueChanged = qt.Signal(str)
        dataTypeChanged = qt.Signal(str)

    def __init__(self, graph: NodeGraph):
        super().__init__()

        self._graph = graph
        self._signals = SceneVars.Signals()
        self._vars = {}
        self._setup_signals()

    @property
    def graph(self) -> NodeGraph:
        return self._graph

    @property
    def signals(self) -> Signals:
        return self._signals

    @property
    def vars(self) -> dict:
        return self._vars

    def unique_variable_name(self, name: str) -> str:
        """
        Returns unique variable name.

        :param str name: variable name.
        :return: unique variable name.
        :rtype: str
        """

        index = 1
        if name in self._vars:
            while f'{name}{index}' in self._vars:
                index += 1
            name = f'{name}{index}'

        return name

    def add_new_variable(self, name: str):
        """
        Adds a new variable.

        :param str name: variable name.
        """

        name = self.unique_variable_name(name)
        self._vars[name] = [0.0, 'NUMERIC']
        self.graph.history.store_history(f'Added variable {name}')

    def rename_variable(self, old_name: str, new_name: str):
        """
        Renames existing variable with new given name.

        :param str old_name: variable to rename.
        :param str new_name: new variable name.
        """

        new_name = self.unique_variable_name(new_name)
        old_value = self._vars[old_name]
        self._vars = OrderedDict(
            [(new_name, old_value) if k == old_name else (k, v) for k, v in self._vars.items()])
        for node in self.list_setters(old_name) + self.list_getters(old_name):
            node.set_var_name(new_name)
        self.graph.history.store_history(f'Renamed variable {old_name} -> {new_name}')

    def delete_variable(self, name: str):
        """
        Removes variable.

        :param str name: name of the variable to delete.
        """

        if name not in self._vars:
            logger.error(f'Cannot delete non existing variable: {name}')
            return
        for node in self.list_setters(name) + self.list_getters(name):
            node.set_invalid(True)
        self._vars.pop(name)
        self.graph.history.store_history(f'Deleted variable: {name}')

    def value(self, name: str) -> Any:
        """
        Returns value of the variable with given name.

        :param str name: name of the variable to get value of.
        :return: variable value.
        :rtype: Any
        """

        return self._vars[name][0]

    def set_value(self, name: str, value: Any):
        """
        Sets the value of the variable with given name.

        :param str name: name of the variable to set value of.
        :param Any value: new variable value.
        """

        self._vars[name][0] = value
        self.signals.valueChanged.emit(name)

    def data_type(self, name: str, as_dict: bool = False) -> str | dict:
        """
        Returns the data type of the variable with given name.

        :param str name: name of the variable to get data type of.
        :param bool as_dict: whether to return data type as a dictionary.
        :return: variable data type.
        :rtype: str or dict
        """

        type_name = self._vars[name][1]
        return registers.DATA_TYPES_REGISTER[type_name] if as_dict else type_name

    def set_data_type(self, name: str, type_name: str):
        """
        Sets the data type of the variable with given name.

        :param str name: name of the variable to set data type of.
        :param str type_name: new variable data type.
        """

        self._vars[name][0] = registers.DATA_TYPES_REGISTER[type_name]['default']
        self._vars[name][1] = type_name
        self.signals.dataTypeChanged.emit(name)
        self.graph.history.store_history(f'Variable {name} data type changed to {type_name}')

    def list_getters(self, var_name: str) -> list[GetNode]:
        """
        Returns list of all getter nodes for the given variable.

        :param str var_name: name of the variable we want to get getter nodes of.
        :return: list of getter nodes.
        :rtype: list[GetNode]
        """

        return [getter_node for getter_node in self.graph.nodes if getter_node.ID == 103
                and getter_node.var_name == var_name]

    def update_getters(self, var_name: str):
        """
        Updates all getter nodes for the specific given variable.

        :param str var_name: name of the variable we want to update getters node of.
        """

        try:
            for getter_node in self.list_getters(var_name):
                getter_node.update()
        except Exception:
            logger.exception('Failed to update getters', exc_info=True)

    def list_setters(self, var_name: str) -> list[SetNode]:
        """
        Returns list of all setter nodes for the given variable.

        :param str var_name: name of the variable we want to get setter nodes of.
        :return: list of setter nodes.
        :rtype: list[SetNode]
        """

        return [setter_node for setter_node in self.graph.nodes if setter_node.ID == 104
                and setter_node.var_name == var_name]

    def update_setters(self, var_name: str):
        """
        Updates all setter nodes for the specific given variable.

        :param str var_name: name of the variable we want to update setter nodes of.
        """

        try:
            for setter_node in self.list_setters(var_name):
                setter_node.update()
        except Exception:
            logger.exception('Failed to update setters', exc_info=True)

    def _setup_signals(self):
        """
        Internal function that setup menu actions signal connections.
        """

        self._signals.dataTypeChanged.connect(self._on_data_type_changed)

    def _on_data_type_changed(self, variable_name: str):
        """
        Internal callback function that is called each time dataTypeChanged signal is emitted.
        Updates getters and setters.
        """

        self.update_getters(variable_name)
        self.update_setters(variable_name)
