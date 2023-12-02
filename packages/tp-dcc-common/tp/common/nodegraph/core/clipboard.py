from __future__ import annotations

import typing

from tp.common.nodegraph.core import edge, serializer


if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.graph import NodeGraph
    from tp.common.nodegraph.core.node import Node
    from tp.common.nodegraph.core.socket import Socket


class SceneClipboard:
    def __init__(self, graph: NodeGraph):
        super().__init__()

        self._graph = graph

    def serialize_selected(self, delete: bool = False) -> dict:
        """
        Serialize current scene selected nodes.

        :param bool delete: whether to delete serialized nodes from scene.
        :return: nodes serialization data.
        :rtype: dict
        """

        selected_nodes: list[dict] = []
        selected_sockets: dict[str, Socket] = {}
        selected_edges: list[edge.Edge] = self._graph.selected_edges

        # Sort edges and nodes
        for node in self._graph.selected_nodes:
            selected_nodes.append(serializer.serialize_node(node))
            for input_socket in node.inputs:
                selected_sockets[input_socket.uuid] = input_socket
            for output_socket in node.outputs:
                selected_sockets[output_socket.uuid] = output_socket

        # Remove all edges not connected to a node in selected list
        edges_to_remove = []
        for selected_edge in selected_edges:
            if selected_edge.start_socket.uuid not in selected_sockets or \
                    selected_edge.end_socket.uuid not in selected_sockets:
                edges_to_remove.append(selected_edge)
        for edge_to_remove in edges_to_remove:
            selected_edges.remove(edge_to_remove)
        edges_final = []
        for selected_edge in selected_edges:
            edges_final.append(serializer.serialize_edge(selected_edge))

        data = {
            'nodes': selected_nodes,
            'edges': edges_final
        }

        if delete:
            self._graph.delete_selected(store_history=False)
            self._graph.history.store_history('Cut items', set_modified=True)

        return data

    def deserialize_data(self, data: dict) -> list[Node]:
        """
        Deserializes data generate by serialize_selected function.

        :param dict data: serialized nodes data.
        :return: created nodes from deserialization process.
        :rtype: list[Node]
        """

        hashmap = {}

        # Calculate mouse pointer - paste position
        view = self._graph.view
        mouse_scene_pos = view.last_scene_mouse_pos
        mouse_x, mouse_y = mouse_scene_pos.x(), mouse_scene_pos.y()

        # Calculate selected objects bbox and center
        minx, maxx, miny, maxy = 10000000, -10000000, 10000000, -10000000
        for node_data in data['nodes']:
            x, y = node_data['pos_x'], node_data['pos_y']
            minx = min(x, minx)
            maxx = max(x, maxx)
            miny = min(y, miny)
            maxy = max(y, maxy)

        created_nodes: list[Node] = []
        # Create each node
        for node_data in data['nodes']:
            node_class = self._graph.class_from_node_data(node_data)
            new_node = node_class(self._graph)      # type: Node
            serializer.deserialize_node(new_node, node_data, hashmap, restore_id=False)
            created_nodes.append(new_node)

            # Adjust node position
            pos_x, pos_y = new_node.x_position(), new_node.y_position()
            new_x, new_y = mouse_x + pos_x - minx, mouse_y + pos_y - miny
            new_node.set_position(new_x, new_y)

        # Create each edge
        for edge_data in data['edges']:
            new_edge = edge.Edge(self._graph)
            serializer.deserialize_edge(new_edge, edge_data, hashmap, restore_id=False)

        self._graph.history.store_history('Paste items', set_modified=True)

        return created_nodes
