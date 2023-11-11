from __future__ import annotations

import typing
from typing import Any

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.tools.rig.noddle.builder.graph import registers
from tp.tools.rig.noddle.builder.graph.core import serializable


if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.graph.core.scene import Scene
    from tp.tools.rig.noddle.builder.graph.nodes.node_getset import GetNode, SetNode

logger = log.tpLogger


class SceneVars(serializable.Serializable):

    class Signals(qt.QObject):
        valueChanged = qt.Signal(str)
        dataTypeChanged = qt.Signal(str)

    def __init__(self, scene: Scene):
        super().__init__()

        self._scene = scene
        self._signals = SceneVars.Signals()
        self._vars = {}
        self._setup_signals()

    @property
    def scene(self) -> Scene:
        return self._scene

    @property
    def signals(self) -> Signals:
        return self._signals

    @property
    def vars(self) -> dict:
        return self._vars

    @override
    def serialize(self) -> dict:
        try:
            result = {}
            for var_name, value_type_pair in self._vars.items():
                value, type_name = value_type_pair
                if type_name in registers.DataType.runtime_types(names=True):
                    result[var_name] = [registers.DATA_TYPES_REGISTER[type_name]['default'], type_name]
                else:
                    result[var_name] = [value, type_name]
        except Exception:
            logger.exception('SceneVars serialize exception!', exc_info=True)
            raise

        return result

    @override(check_signature=False)
    def deserialize(self, data: dict, hashmap: dict | None = None):
        self._vars.clear()
        self._vars.update(data)

    def value(self, name) -> Any:
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
        self.scene.history.store_history(f'Variable {name} data type changed to {type_name}')

    def list_getters(self, var_name: str) -> list[GetNode]:
        """
        Returns list of all getter nodes for the given variable.

        :param str var_name: name of the variable we want to get getter nodes of.
        :return: list of getter nodes.
        :rtype: list[GetNode]
        """

        return [getter_node for getter_node in self.scene.nodes if getter_node.ID == 103
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

        return [setter_node for setter_node in self.scene.nodes if setter_node.ID == 104
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

    def _on_data_type_changed(self):
        """
        Internal callback function that is called each time dataTypeChanged signal is emitted.
        Updates getters and setters.
        """

        self.update_getters()
        self.update_setters()
