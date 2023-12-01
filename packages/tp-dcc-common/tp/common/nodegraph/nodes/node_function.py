from __future__ import annotations

from typing import Any, Callable

from overrides import override

from tp.core import log
from tp.tools.rig.noddle.builder import api

logger = log.tpLogger


class FunctionNode(api.NoddleNode):

    ID = 100
    IS_EXEC = True
    ICON = 'func.png'
    AUTO_INIT_EXECS = True
    DEFAULT_TITLE = 'Function'
    CATEGORY = 'INTERNAL'

    def __init__(self, graph: api.NodeGraph):

        self._func_signature = ''
        self._func_desc = {}

        super().__init__(graph)

    @property
    def func_signature(self) -> str:
        return self._func_signature

    @func_signature.setter
    def func_signature(self, value: str):
        self._func_signature = value
        self._func_desc = api.function_from_signature(value)
        if not self._func_signature:
            logger.warning(f'{self}: missing function signature!')
        self._setup_sockets(reset=True)

    @property
    def func_ref(self) -> callable:
        return self.func_desc.get('ref') if self.func_signature else None

    @property
    def func_desc(self) -> dict:
        return self._func_desc

    @override
    def setup_sockets(self):
        super().setup_sockets()

        if not self._func_desc:
            return

        for socket_name, socket_data_type in self._func_desc.get('inputs').items():
            if isinstance(socket_data_type, str):
                socket_data_type = api.DATA_TYPES_REGISTER[socket_data_type]
            self.add_input(socket_data_type, socket_name)
        for socket_name, socket_data_type in self._func_desc.get('outputs').items():
            if isinstance(socket_data_type, str):
                socket_data_type = api.DATA_TYPES_REGISTER[socket_data_type]
            self.add_output(socket_data_type, socket_name)

        for socket, input_value in zip(self.list_non_exec_inputs(), self._func_desc.get('default_values')):
            socket.set_value(input_value)

    @override
    def execute(self) -> Any:
        attr_values = [input_socket.value() for input_socket in self.list_non_exec_inputs()]
        func_result = self.func_ref(*attr_values)
        logger.debug(f'Function result: {func_result}')
        if not isinstance(func_result, (list, tuple)):
            func_result = [func_result]

        non_exec_outputs = self.list_non_exec_outputs()
        if non_exec_outputs and non_exec_outputs[0].data_type == api.dt.List:
            non_exec_outputs[0].set_value(func_result)
        else:
            for i, output_socket in enumerate(self.list_non_exec_outputs()):
                try:
                    output_socket.set_value(func_result[i])
                except IndexError:
                    logger.error(f'Missing return result for function {self.func_ref}, at index {i}')
                    raise

    @override
    def post_serialization(self, data: dict):
        data['func_signature'] = self.func_signature

    @override
    def pre_deserialization(self, data: dict):
        func_sign = data.get('func_signature')
        if '__builtin__' in func_sign:
            self.func_signature = func_sign.replace('__builtin__', 'builtins')
        else:
            self.func_signature = func_sign


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(FunctionNode.ID, FunctionNode)
