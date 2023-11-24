from __future__ import annotations

from typing import Callable

from overrides import override

from tp.core import log
from tp.common.nodegraph import api

logger = log.tpLogger


class GraphInputNode(api.NoddleNode):

    ID = 101
    IS_EXEC = True
    AUTO_INIT_EXECS = False
    ICON = 'input.png'
    DEFAULT_TITLE = 'Input'
    CATEGORY = 'Utils'
    UNIQUE = True
    IS_INPUT = True

    @override
    def _setup_sockets(self, reset: bool = True):
        self._exec_in_socket = None
        self._exec_out_socket = self.add_output(api.dt.Exec)
        self.setup_sockets()


class GraphOutputNode(api.NoddleNode):

    ID = 102
    IS_EXEC = True
    AUTO_INIT_EXECS = False
    ICON = 'output.png'
    DEFAULT_TITLE = 'Output'
    CATEGORY = 'Utils'
    UNIQUE = True


    @override
    def _setup_sockets(self, reset: bool = True):
        self._exec_in_socket = self.add_input(api.dt.Exec)
        self._exec_out_socket = None


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(GraphInputNode.ID, GraphInputNode)
    register_node(GraphOutputNode.ID, GraphOutputNode)
