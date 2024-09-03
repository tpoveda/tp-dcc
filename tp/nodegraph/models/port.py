from __future__ import annotations

import typing
from typing import Any
from collections import defaultdict

from ..core import datatypes

if typing.TYPE_CHECKING:
    from ..core.node import Node


class PortModel:
    """Base model class for all ports in the node graph."""

    def __init__(self, node: Node):
        super().__init__()

        self.node = node
        self.name = "port"
        self.type: str = ""
        self.data_type: datatypes.DataType = datatypes.Numeric
        self.visible: bool = True
        self.locked: bool = False
        self.display_name: bool = True
        self.multi_connection: bool = False
        self.connected_ports: defaultdict[str, list[str]] = defaultdict(list)
        self.max_connections: int = 1
        self.value: Any = None

    def __repr__(self) -> str:
        """
        Returns a string representation of the port model.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self.name}") object at {hex(id(self))}>'

    def is_runtime_data(self) -> bool:
        """
        Returns whether the port is runtime data.

        :return: whether the port is runtime data.
        """

        runtime_classes = self.node.graph.factory.runtime_data_types(classes=True)
        return (
            self.data_type.type_class in runtime_classes
            or self.value.__class__ in runtime_classes
        )

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the port model.

        :return: dictionary representation.
        """

        port_dict = self.__dict__.copy()
        port_dict.pop("node")
        port_dict["connected_ports"] = dict(port_dict["connected_ports"])
        port_dict["value"] = None if self.is_runtime_data() else self.value
        port_dict["data_type"] = self.node.graph.factory.data_type_name(self.data_type)

        return port_dict
