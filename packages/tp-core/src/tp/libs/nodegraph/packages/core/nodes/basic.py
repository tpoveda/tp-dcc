from __future__ import annotations

from tp.libs.nodegraph import Node, InputPort, OutputPort


class AddNode(Node):
    NODE_NAME = "Add"

    a = InputPort("float", required=True, doc="First addend.")
    b = InputPort("float", required=True, doc="Second addend.")
    sum = OutputPort("float", doc="Sum of the two addends.")
