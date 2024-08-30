from __future__ import annotations

import typing
import logging
from typing import Callable

from ..core.node import Node
from ..core import consts, datatypes

if typing.TYPE_CHECKING:
    from ..core.factory import NodeFactory, Function

logger = logging.getLogger(__name__)


class FunctionNode(Node):
    """
    Node that represents a function.
    """

    NODE_NAME = "Function"
    CATEGORY = consts.INTERNAL_CATEGORY

    def __init__(self, *args, **kwargs):
        self._function_signature: str = ""
        self._function: Function | None = None

        super().__init__(*args, **kwargs)

    @property
    def function_signature(self) -> str:
        """
        Returns the function signature.

        :return: str
        """

        return self._function_signature

    @function_signature.setter
    def function_signature(self, value: str):
        """
        Sets the function signature.

        :param value: str
        """

        self._function_signature = value
        self._function = self.graph.factory.function_from_signature(
            self._function_signature
        )
        self._setup_ports(reset=True)

    @property
    def function(self) -> Function:
        """
        Returns the function.

        :return: Function
        """

        return self._function

    @property
    def function_reference(self) -> Callable:
        """
        Returns the function callable.

        :return: Callable
        """

        return (
            self._function.reference
            if self._function and self._function_signature
            else None
        )

    def setup_ports(self):
        """
        Sets up the ports of the node.
        """

        super().setup_ports()

        if not self._function:
            return

        for socket_name, socket_data_type in self._function.inputs.items():
            if isinstance(socket_data_type, str):
                socket_data_type = self.graph.factory.data_type_by_name(
                    socket_data_type
                )
            self.add_input(socket_data_type, socket_name)

        for socket_name, socket_data_type in self._function.outputs.items():
            if isinstance(socket_data_type, str):
                socket_data_type = self.graph.factory.data_type_by_name(
                    socket_data_type
                )
            self.add_output(socket_data_type, socket_name)

        for socket, input_value in zip(
            self.non_exec_inputs, self._function.default_values
        ):
            socket.set_value(input_value)

    def execute(self):
        """
        Executes the function node.

        :raises IndexError: If there is a missing return result for the function.
        """

        attribute_values = [socket.value() for socket in self.non_exec_inputs]
        function_result = self.function_reference(*attribute_values)
        logger.debug(f"Function result: {function_result}")

        if not isinstance(function_result, (list, tuple)):
            function_result = [function_result]

        non_exec_outputs = self.non_exec_outputs
        if non_exec_outputs and non_exec_outputs[0].data_type == datatypes.List:
            non_exec_outputs[0].set_value(function_result)
        else:
            for i, out_socket in enumerate(non_exec_outputs):
                try:
                    out_socket.set_value(function_result[i])
                except IndexError:
                    logger.error(
                        f"Missing return result for function {self.function_reference}, at index {i}"
                    )
                    raise

    def serialize(self) -> dict:
        """
        Serializes the node to a dictionary.

        :return: dict
        """

        data = super().serialize()
        data["function_signature"] = self.function_signature
        return data

    def pre_deserialize(self, data: dict):
        """
        Function that is called before deserializing the node.

        :param data: dict
        """
        super().pre_deserialize(data)

        func_signature = data.get("function_signature", "")
        if "__builtin__" in func_signature:
            self._function_signature = func_signature.replace("__builtin__", "builtins")
        else:
            self._function_signature = func_signature


def register_plugin(factory: NodeFactory):
    """
    Registers the plugin in the given factory.

    :param factory: factory instance used to register nodes.
    """

    factory.register_node(FunctionNode, "function")
