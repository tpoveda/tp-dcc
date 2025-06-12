from __future__ import annotations

import typing

from .graph import NodeGraph
from .commands import PortConnectedCommand
from ..nodes.node_port import PortInputNode, PortOutputNode

if typing.TYPE_CHECKING:
    from .node import BaseNode, Node


class SubGraph(NodeGraph):
    """
    Custom node graph that is the main controller for managing the expanded node graph for a GroupNode
    """

    def _build_port_nodes(self) -> tuple[dict, dict]:
        """
        Internal function that builds the graph input and output nodes from the parent node ports.
        This function also handles the removal of any port nodes that are outdated.

        :return: tuple with input and output nodes.
        """

        input_nodes = {}
        output_nodes = {}

        return input_nodes, output_nodes

    def _deserialize(
        self,
        session_data: dict,
        relative_pos: bool = False,
        position: tuple | list | None = None,
    ) -> list[BaseNode]:
        """
        Internal function that deserializes node graph from a dictionary.

        :param session_data: node graph session data.
        :param relative_pos: position node relative to the cursor.
        :param position: custom X, Y position.
        :return: list of deserialized node instances.
        """

        # Update node graph properties
        for attr_name, attr_value in session_data.get("graph", {}).items():
            if attr_name == "acyclic":
                self.acyclic = attr_value
            elif attr_name == "connector_collision":
                self.connector_collision = attr_value

        # Build input and output port nodes.
        input_nodes, output_nodes = self._build_port_nodes()

        # Deserialize nodes.
        nodes: dict[str, BaseNode | Node] = {}
        for node_id, node_data in session_data.get("nodes", {}).items():
            identifier = node_data["type"]
            name = node_data.get("name")
            if identifier == PortInputNode.type:
                nodes[node_id] = input_nodes[name]
                nodes[node_id].xy_pos = node_data.get("pos") or [0.0, 0.0]
                continue
            elif identifier == PortOutputNode.type:
                nodes[node_id] = output_nodes[name]
                nodes[node_id].xy_pos = node_data.get("pos") or [0.0, 0.0]
                continue
            # Create node
            node = self.create_node(identifier)
            if not node:
                continue
            node.NODE_NAME = name or node.NODE_NAME
            # Set node properties and custom properties
            for property_name, property_value in node.model.properties.items():
                if property_name in node_data:
                    node.model.set_property(property_name, property_value)
            for property_name, property_value in node_data.get("custom", {}).items():
                node.model.set_property(property_name, property_value)
            # Add node into scene
            nodes[node_id] = node
            self.add_node(node, node_data.get("xy_pos"))

            if node_data.get("port_deletion_allowed", False):
                node.set_ports(
                    {
                        "input_ports": node_data["input_ports"],
                        "output_ports": node_data["output_ports"],
                    }
                )

        # Deserialize connections.
        for connection in session_data.get("connections", []):
            node_id, port_name = connection.get("in", ("", ""))
            in_node: Node = nodes.get(node_id)
            if not in_node:
                continue
            in_port = in_node.input_ports().get(port_name) if in_node else None
            node_id, port_name = connection.get("out", ("", ""))
            out_node = nodes.get(node_id)
            if not out_node:
                continue
            out_port = out_node.output_ports().get(port_name) if out_node else None
            if in_port and out_port:
                self._undo_stack.push(
                    PortConnectedCommand(in_port, out_port, emit_signal=False)
                )

        created_nodes: list[BaseNode | Node] = list(nodes.values())

        if relative_pos:
            self._viewer.move_nodes([n.view for n in created_nodes])
            [setattr(n.model, "xy_pos", n.view.xy_pos) for n in created_nodes]
        elif position:
            self._viewer.move_nodes([n.view for n in created_nodes], position=position)
            [setattr(n.model, "xy_pos", n.view.xy_pos) for n in created_nodes]

        return created_nodes
