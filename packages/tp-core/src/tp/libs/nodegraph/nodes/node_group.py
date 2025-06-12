from __future__ import annotations

from ..core.node import BaseNode


class GroupNode(BaseNode):
    """
    Node that represents a group of nodes.
    """

    NODE_NAME = "Group"
    NODE_CATEGORY = "Core"
