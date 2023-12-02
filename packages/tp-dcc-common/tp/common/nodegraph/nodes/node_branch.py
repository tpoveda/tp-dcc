from __future__ import annotations

from typing import Callable

from overrides import override

from tp.tools.rig.noddle.builder import api


class BranchNode(api.NoddleNode):
    ID = 1
    ICON = 'branch.png'
    IS_EXEC = True
    AUTO_INIT_EXECS = False
    DEFAULT_TITLE = 'Branch'
    CATEGORY = 'Utils'

    @override
    def setup_sockets(self):
        super().setup_sockets()

        self._exec_in_socket = self.add_input(api.DataType.EXEC)
        self.in_condition = self.add_input(api.DataType.BOOLEAN)

        self._exec_out_socket = self.add_output(api.DataType.EXEC, label='True')
        self.out_true = self.exec_out_socket
        self.out_false = self.add_output(api.DataType.EXEC, label='False')

        self.update_title()

    @override
    def _setup_signals(self):
        super()._setup_signals()

        self.in_condition.signals.valueChanged.connect(self.update_title)

    @override
    def list_exec_outputs(self) -> list[api.OutputSocket]:
        return [self.out_true if self.in_condition.value() else self.out_false]

    def update_title(self):
        """
        Updates node title.
        """

        self.title = f'{self.DEFAULT_TITLE}: {self.in_condition.value()}'


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(BranchNode.ID, BranchNode)
