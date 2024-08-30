from __future__ import annotations

import typing

from tp.nodegraph.core.node import Node
from tp.nodegraph.core import datatypes

if typing.TYPE_CHECKING:
    from tp.nodegraph.core.graph import NodeGraph
    from tp.nodegraph.core.factory import NodeFactory


# noinspection PyAttributeOutsideInit
class ConstantNode(Node):
    """
    Node that represents a constant value.
    """

    IS_EXEC = False
    NODE_NAME = "Constant"
    CATEGORY = "Constants"
    DEFAULT_TITLE: str = "Constant"
    CONSTANT_DATA_TYPE: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.update_title()

    @property
    def data_type(self) -> datatypes.DataType:
        """
        Returns the data type of the node.
        """

        return self.graph.factory.data_type_by_name(self.CONSTANT_DATA_TYPE)

    @Node.graph.setter
    def graph(self, value: NodeGraph):
        Node.graph.fset(self, value)
        if value:
            self.out_value.data_type = self.data_type

    def setup_ports(self):
        """
        Function that sets up the default ports for the node.
        """

        super().setup_ports()

        self.out_value = self.add_output(datatypes.Numeric, "Value")

    def setup_signals(self):
        """
        Sets up the signals for the node.
        """

        super().setup_signals()

        self.out_value.signals.valueChanged.connect(self.update_title)

    def update_title(self):
        """
        Updates the title of the node.
        """

        self.set_property("name", f"{self.DEFAULT_TITLE}: {self.out_value.value}")


class ConstantFloatNode(ConstantNode):
    """
    Node that represents a constant float value.
    """

    NODE_NAME = "Number"
    DEFAULT_TITLE = "Number"
    CONSTANT_DATA_TYPE = datatypes.Numeric.name


class ConstantStringNode(ConstantNode):
    """
    Node that represents a constant string value.
    """

    NODE_NAME = "String"
    DEFAULT_TITLE = "String"
    CONSTANT_DATA_TYPE = datatypes.String.name


class ConstantBoolNode(ConstantNode):
    """
    Node that represents a constant boolean value.
    """

    NODE_NAME = "Boolean"
    DEFAULT_TITLE = "Boolean"
    CONSTANT_DATA_TYPE = datatypes.Boolean.name


def register_plugin(factory: NodeFactory):
    """
    Registers the plugin in the given factory.

    :param factory: factory instance used to register nodes.
    """

    factory.register_node(ConstantFloatNode, "float")
    factory.register_node(ConstantStringNode, "string")
    factory.register_node(ConstantBoolNode, "bool")
