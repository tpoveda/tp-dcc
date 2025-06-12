from __future__ import annotations

import typing
import logging
from typing import Any
from abc import abstractmethod

from tp.nodegraph.core import consts
from tp.nodegraph.core.node import Node

if typing.TYPE_CHECKING:
    from tp.nodegraph.core.factory import NodeFactory

logger = logging.getLogger(__name__)


class VariableNode(Node):
    """
    Node that represents a variable.
    """

    IS_EXEC = True
    AUTO_INIT_EXECS = False
    CATEGORY = consts.INTERNAL_CATEGORY

    def __init__(self, *args, **kwargs):
        self._variable_name: str = ""
        super().__init__(*args, **kwargs)

    @property
    def variable_name(self) -> str:
        """
        Getter method that returns the name of the variable.

        :return: name of the variable.
        """

        return self._variable_name

    def verify(self) -> bool:
        """
        Verifies the node.

        :return: whether the node is valid or not.
        """

        result = super().verify()
        if not result:
            return False

        if not self.graph.variable(self._variable_name):
            self.view.setToolTip(
                self.view.toolTip()
                + f'\nVariable "{self._variable_name}" does not exist'
            )
            return False

        return True

    def variable_value(self) -> Any:
        """
        Returns the value of the variable.

        :return: value of the variable.
        """

        try:
            return self.graph.variable_value(self._variable_name)
        except KeyError:
            return None

    def set_variable_value(self, value: Any):
        """
        Sets the value of the variable.

        :param value: value to set.
        :raises KeyError: When the variable does not exist in the graph.
        """

        try:
            self.graph.set_variable_value(self._variable_name, value)
        except KeyError:
            logger.warning(
                f'Variable "{self._variable_name}" does not exist in the graph'
            )
            raise

    @abstractmethod
    def update(self):
        """
        Updates the node.
        """

        raise NotImplementedError

    def set_variable_name(self, name: str, init_ports: bool = False):
        """
        Sets the variable name for the node.

        :param name: name of the variable.
        :param init_ports: whether to initialize the ports of the node or not.
        """

        self._variable_name = name
        variable_exists = bool(self.graph.variable(name))
        self.is_invalid = not variable_exists
        if not variable_exists:
            logger.warning(f'Variable "{name}" does not exist in the graph')
            return

        if init_ports:
            self._setup_ports()

    def serialize(self) -> dict:
        """
        Serializes the node.

        :return: serialized node data.
        """

        data = super().serialize()
        data[self.id]["variable_name"] = self._variable_name
        return data

    def pre_deserialize(self, data: dict):
        """
        Function that is called before deserializing the node.

        :param data: data to deserialize.
        """

        super().pre_deserialize(data)

        self.set_variable_name(data.get("variable_name", ""), init_ports=True)


# noinspection PyAttributeOutsideInit
class GetNode(VariableNode):
    """
    Node that represents a get variable node.
    """

    NODE_NAME = "Get"
    IS_EXEC = False
    AUTO_INIT_EXECS = False

    def setup_ports(self):
        """
        Sets up the ports of the node.
        """

        super().setup_ports()

        if not self._variable_name:
            return

        data_type = self.graph.variable_data_type(
            self._variable_name, as_data_type=True
        )
        self.out_value = self.add_output(
            data_type,
            data_type.label,
            value=self.graph.variable_value(self._variable_name),
        )
        self.out_value.value = self.variable_value

    def update(self):
        """
        Updates the node.
        """

        variable_type = self.graph.variable_data_type(
            self._variable_name, as_data_type=True
        )

        if not self.out_value.data_type == variable_type:
            self.view.output_text_item(self.out_value.view).setPlainText(
                variable_type.label
            )
            self.out_value.data_type = variable_type
            self.out_value.view.update()
            self.view.draw()

    def set_variable_name(self, name: str, init_ports: bool = False):
        """
        Sets the variable name for the node.

        :param name: name of the variable.
        :param init_ports: whether to initialize the ports of the node or not.
        """

        super().set_variable_name(name, init_ports)

        self.set_property("name", f"Get {self._variable_name}", push_undo=False)


# noinspection PyAttributeOutsideInit
class SetNode(VariableNode):
    """
    Node that represents a set variable node.
    """

    NODE_NAME = "Set"
    IS_EXEC = True
    AUTO_INIT_EXECS = True

    def setup_ports(self):
        """
        Sets up the ports of the node.
        """

        super().setup_ports()

        if not self._variable_name:
            return

        data_type = self.graph.variable_data_type(
            self._variable_name, as_data_type=True
        )
        self.in_value = self.add_input(
            data_type,
            data_type.label,
        )
        self.mark_input_as_required(self.in_value)

        self.out_value = self.add_output(
            self.graph.variable_data_type(self._variable_name, as_data_type=True),
            "out",
            display_name=False,
        )
        self.out_value.value = self.variable_value

        self.in_value.affects(self.out_value)

    def update(self):
        """
        Updates the node.
        """

        variable_type = self.graph.variable_data_type(
            self._variable_name, as_data_type=True
        )
        if self.out_value.data_type != variable_type:
            self.in_value.name = variable_type.label
            self.out_value.name = variable_type.label
            self.in_value.data_type = variable_type
            self.out_value.data_type = variable_type
            self.view.draw()

    def set_variable_name(self, name: str, init_ports: bool = False):
        """
        Sets the variable name for the node.

        :param name: name of the variable.
        :param init_ports: whether to initialize the ports of the node or not.
        """

        super().set_variable_name(name, init_ports)

        self.set_property("name", f"Set {self._variable_name}", push_undo=False)

    def execute(self):
        """
        Executes the node.

        :raises ValueError: When the variable name is not set.
        """

        if not self._variable_name:
            logger.error(f"{self}: Variable name is not set!")
            raise ValueError

        self.set_variable_value(self.in_value.value())


def register_plugin(factory: NodeFactory):
    """
    Registers the plugin in the given factory.

    :param factory: factory instance used to register nodes.
    """

    factory.register_node(GetNode, "getter")
    factory.register_node(SetNode, "setter")
