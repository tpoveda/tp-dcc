from __future__ import annotations

import enum

INTERNAL_CATEGORY = "INTERNAL"
NODE_PATHS_ENV_VAR = "TP_NODEGRAPH_NODES_PATH"
NODES_PALETTE_ITEM_MIME_DATA_FORMAT = "application/x-nodegraph-palette-item"
VARS_ITEM_MIME_DATA_FORMAT = "application/x-nodegraph-vars-item"


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
