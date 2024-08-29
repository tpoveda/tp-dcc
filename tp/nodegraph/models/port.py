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
        self.value: Any = None

    def __repr__(self) -> str:
        """
        Returns a string representation of the port model.

        :return: string representation.
        """

        return f'<{self.__class__.__name__}("{self.name}") object at {hex(id(self))}>'

    def to_dict(self) -> dict:
        """
        Returns a dictionary representation of the port model.

        :return: dictionary representation.
        """

        port_dict = self.__dict__.copy()
        port_dict.pop("node")
        port_dict["connected_ports"] = dict(port_dict["connected_ports"])

        return port_dict
