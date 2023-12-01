from __future__ import annotations

from typing import Any, Callable

from overrides import override

from tp.core import log
from tp.common.python import decorators
from tp.tools.rig.noddle.builder import api

logger = log.tpLogger


class VarNode(api.NoddleNode):
    ID = None
    IS_EXEC = True
    AUTO_INIT_EXECS = False
    DEFAULT_TITLE = ''
    CATEGORY = 'INTERNAL'

    def __init__(self, graph: api.NodeGraph):
        self._var_name = ''
        super().__init__(graph)

    @property
    def var_name(self) -> str:
        return self._var_name

    def set_var_name(self, name: str, init_sockets: bool = False):
        """
        Sets the variable name to use.

        :param str name: variable name.
        :param bool init_sockets: whether to initialize sockets after setting new variable name.
        """

        self._var_name = name
        var_exists = name in self.graph.vars._vars.keys()
        self.set_invalid(not var_exists)
        if not var_exists:
            logger.warning(f'Variable "{name}" no longer exists.')
            return

        self.title = f'{self.DEFAULT_TITLE} {self._var_name}'
        if init_sockets:
            self._setup_sockets()

    def var_value(self) -> Any:
        """
        Returns variable value from scene.

        :return: variable value.
        :rtype: Any
        """

        try:
            return self.graph.vars.value(self._var_name)
        except KeyError:
            return None

    def set_var_value(self, value: Any):
        """
        Sets variable value in the scene.

        :param Any value: variable value to set.
        """

        try:
            self.graph.vars.set_value(self._var_name, value)
        except KeyError:
            logger.error(f'Variable "{self._var_name}" does not exist!')
            raise

    @decorators.abstractmethod
    def update(self):
        """
        Updates variable internal value.
        """

        raise NotImplementedError

    @override
    def verify(self) -> bool:
        result = super().verify()
        if self._var_name not in self.graph.vars._vars.keys():
            self.append_tooltip(f'Variable "{self._var_name}" does not exist')
            result = False

        return result

    @override
    def pre_deserialization(self, data: dict):
        self.set_var_name(data.get('var_name'), init_sockets=True)

    @override
    def post_serialization(self, data: dict):
        data['var_name'] = self.var_name

    def attributes_widgets(self):
        return None


class GetNode(VarNode):
    ID = 103
    IS_EXEC = False
    ICON = None
    STATUS_ICON = False
    AUTO_INIT_EXECS = False
    MIN_WIDTH = 110
    OUTPUT_POSITION = 5
    DEFAULT_TITLE = 'Get'

    @override
    def setup_sockets(self):
        if not self.var_name:
            return

        super().setup_sockets()

        self.out_value = self.add_output(
            self.graph.vars.data_type(self.var_name, as_dict=True),
            value=self.graph.vars.value(self.var_name))
        self.out_value.value = self.var_value

    @override
    def update(self):
        var_type = self.graph.vars.data_type(self.var_name, as_dict=True)
        if not self.out_value.data_type == var_type:
            self.out_value.label = var_type['label']
            self.out_value.data_type = var_type
            self.out_value.update_positions()


class SetNode(VarNode):
    ID = 104
    IS_EXEC = True
    AUTO_INIT_EXECS = True
    ICON = None
    DEFAULT_TITLE = 'Set'

    @override
    def setup_sockets(self):
        super().setup_sockets()

        if not self.var_name:
            return

        self.in_value = self.add_input(self.graph.vars.data_type(self.var_name, as_dict=True))
        self.out_value = self.add_output(self.graph.vars.data_type(self.var_name, as_dict=True), label='')
        self.out_value.value = self.var_value
        self.mark_input_as_required(self.in_value)

    @override
    def update(self):
        var_type = self.graph.vars.data_type(self.var_name, as_dict=True)
        if not self.in_value.data_type == var_type:
            self.in_value.label = var_type['label']
            self.in_value.data_type = var_type
            self.out_value.data_type = var_type
            self.in_value.update_positions()

    @override
    def execute(self) -> Any:
        if not self.var_name:
            logger.error(f'{self}: var_name is not set')
            raise ValueError

        self.set_var_value(self.in_value.value())


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(GetNode.ID, GetNode)
    register_node(SetNode.ID, SetNode)
