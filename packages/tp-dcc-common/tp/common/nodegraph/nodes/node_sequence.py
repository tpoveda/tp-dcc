from __future__ import annotations

from typing import Callable

from tp.tools.rig.noddle.builder import api

from overrides import override


class SequenceNode(api.NoddleNode):

    ID = 5
    IS_EXEC = True
    ICON = 'sequence.png'
    TITLE_EDITABLE = True
    AUTO_INIT_EXECS = False
    DEFAULT_TITLE = 'Sequence'
    CATEGORY = 'Utils'

    @override
    def _setup_sockets(self, reset: bool = True):
        self._exec_in_socket = self.add_input(api.dt.Exec)
        self._exec_out_socket = self.add_output(api.dt.Exec, label='Then 0')
        for i in range(1, 6):
            self.add_output(api.dt.Exec, label=f'Then {i}')


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(SequenceNode.ID, SequenceNode)
