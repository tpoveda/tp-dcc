import pytest

from tp.nodegraph.core.port import NodePort
from tp.nodegraph.core.consts import PortType
from tp.nodegraph.core.exceptions import NodePortNotFoundError


def test_node_initialization(node):
    """Test initializing a node."""

    assert node.name == "Node 1"
    assert node.inputs == []
    assert node.outputs == []


def test_add_input_port(node):
    """Test adding an input port to a node."""

    port = NodePort(node)
    node.add_input_port(port)
    assert port in node.inputs


def test_add_output_port(node):
    """Test adding an output port to a node."""

    port = NodePort(node)
    node.add_output_port(port)
    assert port in node.outputs


def test_remove_input_port(node):
    """Test removing an input port from a node."""

    port = NodePort(node)
    node.add_input_port(port)
    node.delete_input_port(port)
    assert port not in node.inputs


def test_remove_output_port(node):
    """Test removing an output port from a node."""

    port = NodePort(node)
    node.add_output_port(port)
    node.delete_output_port(port)
    assert port not in node.outputs


def test_add_non_existent_port_with_accept_constraint(node):
    """Test adding a non-existent input port with constraints to a node."""

    port = NodePort(node)
    with pytest.raises(
        NodePortNotFoundError,
        match='Port "port" not found in node "tp.nodegraph.nodes.Node".',
    ):
        node.add_accept_port_type(
            port=port,
            port_type_data={
                "port_name": "output 1",
                "port_type": PortType.Output.value,
                "node_type": "tp.nodegraph.nodes.BasicNodeA",
            },
        )


def test_add_port_with_accept_constraint_without_graph(node):
    """Test adding an input port with constraints to a node without a graph."""

    port = NodePort(node)
    node.add_input_port(port)
    node.add_accept_port_type(
        port=port,
        port_type_data={
            "port_name": "output 1",
            "port_type": PortType.Output.value,
            "node_type": "tp.nodegraph.nodes.BasicNodeA",
        },
    )
    assert port in node.inputs
    assert port.accepted_port_types() == {
        "tp.nodegraph.nodes.BasicNodeA": {"out": {"output 1"}}
    }


def test_add_port_with_accept_constraint(node_in_graph):
    """Test adding an input port with constraints to a node."""

    port = NodePort(node_in_graph)
    node_in_graph.add_input_port(port)
    node_in_graph.add_accept_port_type(
        port=port,
        port_type_data={
            "port_name": "output 1",
            "port_type": PortType.Output.value,
            "node_type": "tp.nodegraph.nodes.BasicNodeA",
        },
    )
    assert port in node_in_graph.inputs
    assert port.accepted_port_types() == {
        "tp.nodegraph.nodes.BasicNodeA": {"out": {"output 1"}}
    }


def test_add_port_with_reject_constraint_without_graph(node):
    """Test adding an input port with constraints to a node without a graph."""

    port = NodePort(node)
    node.add_input_port(port)
    node.add_reject_port_type(
        port=port,
        port_type_data={
            "port_name": "output 1",
            "port_type": PortType.Output.value,
            "node_type": "tp.nodegraph.nodes.BasicNodeA",
        },
    )
    assert port in node.inputs
    assert port.rejected_port_types() == {
        "tp.nodegraph.nodes.BasicNodeA": {"out": {"output 1"}}
    }
