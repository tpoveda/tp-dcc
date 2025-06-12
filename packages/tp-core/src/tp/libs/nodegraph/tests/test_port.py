import pytest
from unittest.mock import create_autospec

from tp.nodegraph.core.port import NodePort
from tp.nodegraph.core.exceptions import NodePortLockedError


def test_connect_invalid_port():
    """Test connecting an invalid port to another port."""

    node_port = create_autospec(NodePort, instance=True, name="MockNodePort")
    node_port.connect_to(None)

    # Since the method should return immediately, no further interaction should occur
    # Verify that no methods were called on the mock object.
    node_port.connected_ports.assert_not_called()
    node_port.locked.assert_not_called()


def test_connect_port_to_already_connected_port(node):
    """Test connecting a port to another port that is already connected."""

    port1 = NodePort(node)
    port2 = create_autospec(NodePort, instance=True, name="MockNodePort")
    port2.connected_ports.return_value = [port1]
    port1.connect_to(port2)
    port2.connected_ports.assert_called_once()


def test_connect_port_with_source_port_locked(node):
    """Test connecting a port with a source port that is locked."""

    port1 = NodePort(node)
    port2 = NodePort(node)
    port1.lock()

    with pytest.raises(
        NodePortLockedError,
        match='Port "port" in node "tp.nodegraph.nodes.Node" is locked.',
    ):
        port1.connect_to(port2)


def test_connect_port_with_target_port_locked(node):
    """Test connecting a port with a target port that is locked."""

    port1 = NodePort(node)
    port2 = NodePort(node)
    port2.lock()

    with pytest.raises(
        NodePortLockedError,
        match='Port "port" in node "tp.nodegraph.nodes.Node" is locked.',
    ):
        port1.connect_to(port2)


# def test_connect_ports():
#     """Test connecting two ports together."""
#
#     node_a = Node()
#     node_b = Node()
#     port_a = NodePort(node_a)
#     port_b = NodePort(node_b)
#
#     port_a.connect_to(port_b)
#     assert port_a.connected_ports == {node_b.id: [port_b.name]}
#     assert port_b.connected_ports == {node_a.id: [port_a.name]}


# port_a.disconnect_from(port_b)
# assert port_a.connected_ports == {}
# assert port_b.connected_ports == {}
