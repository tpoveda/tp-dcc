from __future__ import annotations

import enum
import typing
from typing import Any
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from .graph import NodeGraph
    from .datatypes import DataType

INTERNAL_CATEGORY = "INTERNAL"
NODE_PATHS_ENV_VAR = "TP_NODEGRAPH_NODES_PATH"
NODES_PALETTE_ITEM_MIME_DATA_FORMAT = "application/x-nodegraph-palette-item"
VARS_ITEM_MIME_DATA_FORMAT = "application/x-nodegraph-vars-item"


@dataclass
class Variable:
    """
    Class that defines a variable.
    """

    name: str
    value: Any
    data_type: DataType
    graph: NodeGraph

    def to_dict(self):
        """
        Returns the variable as a dictionary.

        :return: dictionary with the variable data.
        """

        data_type = self.data_type
        if data_type.name in self.graph.factory.runtime_data_types(names=True):
            value = data_type.default
        else:
            value = self.value

        return {
            "name": self.name,
            "value": value,
            "data_type": self.data_type.name,
        }


class PortType(enum.Enum):
    """Enum that defines the type of port."""

    Input = "in"
    Output = "out"


class LayoutDirection(enum.Enum):
    """Enum that defines the direction of the layout."""

    Horizontal = 0
    Vertical = 1


class ConnectorStyle(enum.Enum):
    """
    Enum that defines the style of the connector.
    """

    Straight = 0
    Curved = 1
    Angle = 2
