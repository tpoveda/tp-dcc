from tp.nodegraph.core.node import Node
from tp.nodegraph.core.port import NodePort
from tp.nodegraph.core.graph import NodeGraph
from tp.nodegraph.core.consts import PortType
from tp.nodegraph.core.validators import (
    validate_accept_connection,
    validate_reject_connection,
)


def test_invalid_accept_constraint_validation():
    """Test that a connection is rejected when the accept constraint is invalid."""

    graph = NodeGraph()
    node1 = Node(name="Node 1")
    node2 = Node(name="Node 2")
    graph.add_node(node1)
    graph.add_node(node2)

    port1 = NodePort(node1)
    port2 = NodePort(node2)
    node1.add_input_port(port1)
    node1.add_accept_port_type(
        port=port1,
        port_type_data={
            "port_name": "output 1",
            "port_type": PortType.Output.value,
            "node_type": "tp.nodegraph.nodes.Node",
        },
    )
    node2.add_output_port(port2)

    assert validate_accept_connection(port1, port2) is False


def test_accept_constraint_validation():
    """Test that a connection is accepted when the accept constraint is valid."""

    graph = NodeGraph()
    node1 = Node(name="Node 1")
    node2 = Node(name="Node 2")
    graph.add_node(node1)
    graph.add_node(node2)

    port1 = NodePort(node1)
    port2 = NodePort(node2)
    node1.add_input_port(port1)
    node1.add_accept_port_type(
        port=port1,
        port_type_data={
            "port_name": "port",
            "port_type": PortType.Output.value,
            "node_type": "tp.nodegraph.nodes.Node",
        },
    )
    node2.add_output_port(port2)

    assert validate_accept_connection(port1, port2) is True


def test_invalid_reject_constraint_validation():
    """Test that a connection is accepted when the reject constraint is invalid."""

    graph = NodeGraph()
    node1 = Node(name="Node 1")
    node2 = Node(name="Node 2")
    graph.add_node(node1)
    graph.add_node(node2)

    port1 = NodePort(node1)
    port2 = NodePort(node2)
    node1.add_input_port(port1)
    node1.add_reject_port_type(
        port=port1,
        port_type_data={
            "port_name": "port",
            "port_type": PortType.Output.value,
            "node_type": "tp.nodegraph.nodes.Node",
        },
    )
    node2.add_output_port(port2)

    assert validate_reject_connection(port1, port2) is False


def test_reject_constraint_validation():
    """Test that a connection is rejected when the reject constraint is valid."""

    graph = NodeGraph()
    node1 = Node(name="Node 1")
    node2 = Node(name="Node 2")
    graph.add_node(node1)
    graph.add_node(node2)

    port1 = NodePort(node1)
    port2 = NodePort(node2)
    node1.add_input_port(port1)
    node1.add_reject_port_type(
        port=port1,
        port_type_data={
            "port_name": "output 1",
            "port_type": PortType.Output.value,
            "node_type": "tp.nodegraph.nodes.Node",
        },
    )
    node2.add_output_port(port2)

    assert validate_reject_connection(port1, port2) is True
