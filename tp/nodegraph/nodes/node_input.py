from __future__ import annotations


from tp.nodegraph.core import datatypes
from tp.nodegraph.core.node import Node


class GraphInputNode(Node):
    """
    Node that represents a graph input.
    """

    NODE_NAME = "Input"
    CATEGORY = "Utils"
    IS_EXEC = True
    AUTO_INIT_EXECS = False

    # noinspection PyAttributeOutsideInit
    def setup_ports(self):
        super().setup_ports()

        self._exec_out_socket = self.add_output(datatypes.Exec)
