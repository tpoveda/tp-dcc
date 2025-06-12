from __future__ import annotations

import typing
from collections import deque

from tp.nodegraph.core import datatypes
from tp.nodegraph.core.node import Node
from tp.nodegraph.core.port import NodePort

if typing.TYPE_CHECKING:
    from tp.nodegraph.core.factory import NodeFactory


class ForEachNode(Node):
    """
    Node that represents a for each loop.
    """

    IS_EXEC = True
    AUTO_INIT_EXECS = True
    NODE_NAME = "For Each"
    CATEGORY = "Collections"
    COLLECTION_DATA_TYPE: datatypes.DataType | None = None

    @property
    def exec_outputs(self) -> list[NodePort]:
        """
        Returns the output ports that are executed.
        Override default function, so we do not return the loop body output port.

        :return: list[NodePort]
        """

        return [self._exec_out_socket]

    def verify(self) -> bool:
        """
        Verifies the node.

        :return: whether the node is valid or not.
        """

        result = super().verify()
        if not result:
            return False

        for node in self.loop_body():
            result = node.verify()
            if not result:
                return False

        return True

    def setup_ports(self):
        """
        Sets up the ports of the node.
        """

        super().setup_ports()

        self.in_collection = self.add_input(datatypes.List, "List")
        self.mark_input_as_required(self.in_collection)

        self.out_loop_body = self.add_output(
            datatypes.Exec, "Loop Body", max_connections=1
        )
        self.out_item = self.add_output(self.COLLECTION_DATA_TYPE, "Item")

    def loop_body(self):
        """
        Returns the loop body nodes.

        :return: list[Node]
        """

        loop_body: deque[Node] = deque()
        if self.out_loop_body.connected_ports():
            loop_body.extend(self.out_loop_body.connected_ports()[0].node.exec_queue())

        return loop_body

    def execute(self):
        """
        Executes the node.
        """

        for item in self.in_collection.value():
            self.out_item.set_value(item)
            for node in self.loop_body():
                node._execute()


class ForEachName(ForEachNode):
    """
    Node that represents a for each loop over names.
    """

    NODE_NAME = "For Each Name"
    COLLECTION_DATA_TYPE = datatypes.String


def register_plugin(factory: NodeFactory):
    """
    Registers the plugin in the given factory.

    :param factory: factory instance used to register nodes.
    """

    factory.register_node(ForEachName, "for_each_name")
