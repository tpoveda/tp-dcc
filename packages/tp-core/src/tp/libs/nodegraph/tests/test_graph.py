import pytest

from tp.nodegraph.core.node import BaseNode
from tp.nodegraph.nodes.node_function import FunctionNode
from tp.nodegraph.core.exceptions import NodeCreationError


class DummyNode(FunctionNode):
    def __init__(self, name: str = "dummy"):
        super().__init__(
            name=name,
            func=lambda x: x,
            input_types=[float],
            output_types=float,
        )


def test_graph_initialization(graph):
    """Test initializing a node graph."""

    assert graph.nodes() == []


def test_register_node(graph):
    """Test registering a node in the graph."""

    graph.register_node(DummyNode, "dummy")
    assert "dummy" in graph.factory._node_aliases


def test_register_nodes(graph):
    """Test registering multiple nodes in the graph."""

    graph.register_nodes([DummyNode])
    assert "tp.nodegraph.nodes.DummyNode" in graph.factory._node_classes


def test_create_unrecognized_node(graph):
    """Test creating a node with an unrecognized ID."""

    with pytest.raises(
        NodeCreationError, match='Node with ID "unrecognized" cannot be created.'
    ):
        graph.create_node("unrecognized")


def test_create_node(graph):
    """Test creating a node from the registry."""

    graph.register_node(DummyNode, "dummy")
    node1 = graph.create_node("dummy", "Dummy Node")
    assert isinstance(node1, FunctionNode)
    assert node1.model.selected is True


def test_create_node_with_custom_text_color_and_disabled(graph):
    """Test creating a node with custom text color and disabled."""

    graph.register_node(DummyNode, "dummy")
    node1 = graph.create_node("dummy", text_color=(0, 0, 0, 255))
    node1.enabled = True
    assert node1.text_color == (0, 0, 0)
    assert node1.enabled is True
    assert node1.disabled is False


def test_create_node_with_custom_icon(graph):
    """Test creating a node with a custom icon."""

    graph.register_node(DummyNode, "dummy")
    node1 = graph.create_node("dummy", name="custom icon")
    assert node1.icon_path is None
    node1.icon_path = "icon.png"
    assert node1.icon_path == "icon.png"


def test_create_node_unique_name(graph):
    """Test creating a node with a unique name."""

    graph.register_node(DummyNode, "dummy")
    node1 = graph.create_node("dummy", "Dummy Node")
    assert node1.name == "Dummy Node"
    node2 = graph.create_node("dummy", "Dummy Node")
    assert node2.name == "Dummy Node 1"


def test_unique_node_name(graph_with_nodes):
    """Test getting a unique node name."""

    assert graph_with_nodes.unique_node_name("Unique Node") == "Unique Node"


def test_unique_node_name_duplicate_no_number(graph_with_nodes):
    """Test getting a unique node name with a duplicate name but no number."""

    assert graph_with_nodes.unique_node_name("Dummy Node") == "Dummy Node 1"


def test_unique_node_name_duplicate_with_number(graph):
    """Test getting a unique node name with a duplicate name and number."""

    graph.add_node(BaseNode("Node 1"))
    graph.add_node(BaseNode("Node 2"))
    graph.add_node(BaseNode("Node 3"))
    assert graph.unique_node_name("Node 2") == "Node 4"


def test_unique_node_name_whitespace_handling(graph):
    """Test getting a unique node name with whitespace."""

    assert graph.unique_node_name("   Node  3  ") == "Node 3"


def test_add_node(graph):
    """Test adding a node to a graph."""

    assert graph.model.nodes == {}
    node = BaseNode(name="Test Node")
    assert node.graph is None
    graph.add_node(node)
    assert node.graph == graph
    assert node.graph.model == graph.model
    assert graph.model.nodes == {node.id: node}


def test_remove_node(graph):
    """Test removing a node from a graph."""

    node = BaseNode(name="Test Node")
    graph.add_node(node)
    assert graph.model.nodes == {node.id: node}
    graph.remove_node(node)
    assert graph.model.nodes == {}
