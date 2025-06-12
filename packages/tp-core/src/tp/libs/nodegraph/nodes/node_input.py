from __future__ import annotations

import typing

from tp.python import paths
from tp.nodegraph.core import datatypes
from tp.nodegraph.core.node import Node

if typing.TYPE_CHECKING:
    from tp.nodegraph.core.factory import NodeFactory


class GraphInputNode(Node):
    """
    Node that represents a graph input.
    """

    NODE_NAME = "Input"
    CATEGORY = "Utils"
    IS_EXEC = True
    AUTO_INIT_EXECS = False
    ICON_PATH = paths.canonical_path("../resources/icons/input.svg")

    # noinspection PyAttributeOutsideInit
    def setup_ports(self):
        super().setup_ports()

        self._exec_out_socket = self.add_output(datatypes.Exec)


def register_plugin(factory: NodeFactory):
    """
    Registers the plugin in the given factory.

    :param factory: factory instance used to register nodes.
    """

    factory.register_node(GraphInputNode, "input")
