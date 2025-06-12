from __future__ import annotations

from ..core.node import BaseNode


class PortInputNode(BaseNode):
    """
    Node that represents an input port from a GroupNode when expanded in a SubGraph.
    """

    NODE_NAME = "InputPort"


class PortOutputNode(BaseNode):
    """
    Node that represents an output port from a GroupNode when expanded in a SubGraph.
    """

    NODE_NAME = "OutputPort"
