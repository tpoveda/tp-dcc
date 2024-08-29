from __future__ import annotations

import typing

from tp.nodegraph.core.node import datatypes
from tp.nodegraph.core.port import NodePort
from tp.nodegraph.nodes.node_input import GraphInputNode

if typing.TYPE_CHECKING:
    from tp.nodegraph.core.factory import NodeFactory


class GraphAssetInputNode(GraphInputNode):
    """
    Node that represents an asset input.
    """

    NODE_NAME = "Asset Input"
    CATEGORY = "Utils"

    @property
    def out_asset_name(self) -> NodePort:
        """
        Getter method that returns the asset name port.

        :return: asset name port.
        """

        return self._out_asset_name

    # noinspection PyAttributeOutsideInit
    def setup_ports(self):
        """
        Setup node ports.
        """

        super().setup_ports()

        self._out_asset_name = self.add_output(datatypes.String, "Asset Name", value="")


def register_plugin(factory: NodeFactory):
    """
    Registers the plugin in the given factory.

    :param factory: factory instance used to register nodes.
    """

    factory.register_node(GraphAssetInputNode, "input_asset")
