from __future__ import annotations

from ..core.ids import NodeId


class NodeModel:
    """Base class for all node models in the node graph."""

    def __init__(self):
        super().__init__()

        self.id = NodeId.new()
        self.name = "node"
