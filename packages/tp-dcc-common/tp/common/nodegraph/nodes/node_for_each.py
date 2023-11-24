from __future__ import annotations

from collections import deque
from typing import Any, Callable

from overrides import override

from tp.tools.rig.noddle.builder import api


class ForEachNode(api.NoddleNode):
    ID = None
    IS_EXEC = True
    AUTO_INIT_EXECS = True
    DEFAULT_TITLE = 'For Each'
    CATEGORY = 'Collections'
    COLLECTION_DATA_TYPE = None

    @override
    def setup_sockets(self):
        self.in_collection = self.add_input(api.dt.List, label='List')
        self.out_loop_body = self.add_output(api.dt.Exec, label='Loop Body', max_connections=1)
        self.out_item = self.add_output(self.COLLECTION_DATA_TYPE, label='Item')
        self.mark_input_as_required(self.in_collection)

    @override
    def list_exec_outputs(self) -> list[api.OutputSocket]:
        return [self.exec_out_socket]

    @override
    def verify(self) -> bool:
        result = super().verify()
        if not result:
            return False
        for node in self.loop_body():
            result = node.verify()
            if not result:
                return False

        return True

    @override
    def execute(self) -> Any:
        for item in self.in_collection.value():
            self.out_item.set_value(item)
            for node in self.loop_body():
                node._exec()

    def loop_body(self) -> deque[api.NoddleNode]:
        loop_body = deque()
        if self.out_loop_body.list_connections():
            loop_body.extend(self.out_loop_body.list_connections()[0].node.exec_queue())
        return loop_body


class ForEachName(ForEachNode):
    ID = 106
    DEFAULT_TITLE = 'For Each Name'
    COLLECTION_DATA_TYPE = api.dt.String


def register_plugin(register_node: Callable, register_function: Callable, register_data_type: Callable):
    register_node(ForEachName.ID, ForEachName)
