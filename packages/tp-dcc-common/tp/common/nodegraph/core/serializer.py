from __future__ import annotations

import typing

from tp.core import log
from tp.common.nodegraph import datatypes
from tp.common.nodegraph import registers
from tp.common.nodegraph.core import edge

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.socket import Socket, OutputSocket, InputSocket
    from tp.common.nodegraph.core.node import Node
    from tp.common.nodegraph.core.vars import SceneVars
    from tp.common.nodegraph.core.graph import NodeGraph


logger = log.tpLogger


def serialize_socket(socket_to_serialize: Socket) -> dict:
    value = socket_to_serialize.value() if not socket_to_serialize.is_runtime_data() else None
    return {
        'id': socket_to_serialize.uuid,
        'index': socket_to_serialize.index,
        'position': socket_to_serialize.node_position.value,
        'data_type': datatypes.type_name(socket_to_serialize.data_type),
        'max_connections': socket_to_serialize.max_connections,
        'label': socket_to_serialize.label,
        'value': value
    }


def deserialize_socket(
        socket_instance: Socket, data: dict, hashmap: dict | None = None, restore_id: bool = True):
    if restore_id:
        socket_instance.uuid = data['id']

    data_type = datatypes.type_from_name(data['data_type'])
    value = data.get('value', data_type['default'])
    socket_instance.data_type = data_type
    socket_instance.set_value(value)
    hashmap[data['id']] = socket_instance


def serialize_node(node_to_serialize: Node) -> dict:

    node_to_serialize.pre_serialization()

    try:
        inputs = [serialize_socket(input_socket) for input_socket in node_to_serialize.inputs]
    except AttributeError:
        inputs = []
    try:
        outputs = [serialize_socket(output_socket) for output_socket in node_to_serialize.outputs]
    except AttributeError:
        outputs = []

    data = {
        'id': node_to_serialize.uuid,
        'node_id': node_to_serialize.__class__.ID,
        'title': node_to_serialize.title,
        'pos_x': node_to_serialize.view.scenePos().x(),
        'pos_y': node_to_serialize.view.scenePos().y(),
        'inputs': inputs,
        'outputs': outputs
    }

    node_to_serialize.post_serialization(data)

    return data


def deserialize_node(node_instance: Node, data: dict, hashmap: dict | None = None, restore_id: bool = True):

    node_instance.pre_deserialization(data)

    if restore_id:
        node_instance.uuid = data.get('id')
    hashmap[data['id']] = node_instance

    node_instance.set_position(data['pos_x'], data['pos_y'])
    node_instance.title = data.get('title')

    # Sockets
    data['inputs'].sort(key=lambda in_socket: in_socket['index'] + in_socket['position'] * 10000)
    data['outputs'].sort(key=lambda out_socket: out_socket['index'] + out_socket['position'] * 10000)

    # Deserialize sockets
    for socket_data in data.get('inputs'):
        found_input_socket: InputSocket | None = None
        for input_socket in node_instance.inputs:
            if input_socket.index == socket_data['index']:
                found_input_socket = input_socket
                break
        if found_input_socket is None:
            logger.warning(
                f'Deserialization of input socket data for node {node_instance.title} has not found socket with '
                f'index {socket_data["index"]}')
            logger.debug(f'Missing socket data: {socket_data}')
            data_type = datatypes.type_from_name(socket_data['data_type'])
            value = socket_data.get('value', data_type['default'])
            found_input_socket = node_instance.add_input(data_type, socket_data['label'], value=value)
        deserialize_socket(found_input_socket, socket_data, hashmap, restore_id)

    for socket_data in data.get('outputs'):
        found_output_socket: OutputSocket | None = None
        for output_socket in node_instance.outputs:
            if output_socket.index == socket_data['index']:
                found_output_socket = output_socket
                break
        if found_output_socket is None:
            logger.warning(
                f'Deserialization of output socket data for node {node_instance.title} has not found socket with '
                f'index {socket_data["index"]}')
            logger.debug(f'Missing socket data: {socket_data}')
            # we can create new socket for this
            data_type = datatypes.type_from_name(socket_data['data_type'])
            value = socket_data.get('value', data_type['default'])
            found_output_socket = node_instance.add_output(data_type, socket_data['label'], value=value)
        deserialize_socket(found_output_socket, socket_data, hashmap, restore_id)

    node_instance.post_deserialization(data)


def serialize_edge(edge_to_serialize: edge.Edge) -> dict:
    return {
        'id': edge_to_serialize.uuid,
        'start': edge_to_serialize.start_socket.uuid,
        'end': edge_to_serialize.end_socket.uuid
    }


def deserialize_edge(edge_instance: edge.Edge, data: dict, hashmap: dict | None = None, restore_id: bool = True):
    if restore_id:
        edge_instance.uuid = data.get('id')
    edge_instance.start_socket = hashmap[data['start']]
    edge_instance.end_socket = hashmap[data['end']]
    edge_instance.update_edge_graphics_type()


def serialize_graph(graph_to_serialize: NodeGraph) -> dict:
    nodes: list[dict] = []
    edges: list[dict] = []
    for n in graph_to_serialize.nodes:
        nodes.append(serialize_node(n))
    for e in graph_to_serialize.edges:
        if not e.start_socket or not e.end_socket:
            continue
        edges.append(serialize_edge(e))

    return {
        'id': graph_to_serialize.uuid,
        'vars': serialize_vars(graph_to_serialize.vars),
        'scene_width': graph_to_serialize._scene_width,
        'scene_height': graph_to_serialize._scene_height,
        'nodes': nodes,
        'edges': edges,
        'edge_type': graph_to_serialize.edge_type.name
    }


def serialize_vars(vars_instance: SceneVars) -> dict:
    try:
        result = {}
        for var_name, value_type_pair in vars_instance.vars.items():
            value, type_name = value_type_pair
            if type_name in registers.DataType.runtime_types(names=True):
                result[var_name] = [registers.DATA_TYPES_REGISTER[type_name]['default'], type_name]
            else:
                result[var_name] = [value, type_name]
    except Exception:
        logger.exception('SceneVars serialize exception!', exc_info=True)
        raise

    return result


def deserialize_vars(vars_instance: SceneVars, data: dict):
    vars_instance.vars.clear()
    vars_instance.vars.update(data)


def deserialize_graph(graph_instance: NodeGraph, data: dict, hashmap: dict | None = None, restore_id: bool = True):
    hashmap = hashmap or {}

    if restore_id:
        graph_instance.uuid = data['id']

    # Deserialize variables
    deserialize_vars(graph_instance.vars, data.get('vars', {}))

    # Deserialize nodes
    all_nodes = graph_instance.nodes[:]
    for node_data in data['nodes']:
        found = False
        for scene_node in all_nodes:
            if scene_node.uuid == node_data['id']:
                found = scene_node
                break
        if not found:
            new_node = graph_instance.class_from_node_data(node_data)(graph_instance)
            deserialize_node(new_node, node_data, hashmap, restore_id=restore_id)
        else:
            deserialize_node(found, node_data, hashmap, restore_id=restore_id)
            all_nodes.remove(found)
    while all_nodes:
        node_to_remove = all_nodes.pop()
        node_to_remove.remove()

    # Deserialize edges
    all_edges = graph_instance.edges[:]
    for edge_data in data['edges']:
        found = False
        for scene_edge in all_edges:
            if scene_edge.uuid == edge_data['id']:
                found = scene_edge
                break
        if not found:
            new_edge = edge.Edge(graph_instance)
            deserialize_edge(new_edge, edge_data, hashmap, restore_id)
        else:
            deserialize_edge(found, edge_data, hashmap, restore_id)
            all_edges.remove(found)
    while all_edges:
        edge_to_delete = all_edges.pop()
        try:
            graph_instance.edges.index(edge_to_delete)
        except ValueError:
            continue
        edge_to_delete.remove()

    # Set edge type
    graph_instance.edge_type = data.get('edge_type', edge.Edge.Type.BEZIER)
