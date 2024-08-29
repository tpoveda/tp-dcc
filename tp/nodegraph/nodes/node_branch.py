from __future__ import annotations

from ..core.node import Node
from ..core import datatypes as dt


class BranchNode(Node):
    """
    Node that branches the execution flow.
    """

    NODE_NAME = "Branch"
    CATEGORY = "Utils"

    def setup_ports(self):
        super().setup_ports()

        self.exec_in_socket = self.add_input(dt.Exec, "exec_in")
        self.in_condition = self.add_input(dt.Boolean, "condition")

        self.exec_out_socket = self.add_output(dt.Exec, "True")
        self.out_true = self.exec_out_socket
        self.out_false = self.add_output(dt.Exec, "False")
