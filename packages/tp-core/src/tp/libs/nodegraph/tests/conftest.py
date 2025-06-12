import pytest

from tp.nodegraph.core.node import Node
from tp.nodegraph.core.graph import NodeGraph
from tp.nodegraph.core.factory import NodeFactory
from tp.nodegraph.nodes.node_function import FunctionNode
from tp.nodegraph.nodes.node_function import AbsNode, MultiplyNode, SubtractNode


class DummyNode(FunctionNode):
    def __init__(self, name: str = "dummy"):
        super().__init__(
            name=name,
            func=lambda x: x,
            input_types=[float],
            output_types=float,
        )


@pytest.fixture
def factory():
    return NodeFactory()


@pytest.fixture
def graph():
    return NodeGraph()


@pytest.fixture
def node():
    return Node(name="Node 1")


@pytest.fixture
def node_in_graph():
    graph = NodeGraph()
    node = Node(name="Node 1")
    graph.add_node(node)
    return node


@pytest.fixture
def graph_with_nodes():
    graph = NodeGraph()
    graph.register_nodes(
        [
            DummyNode,
            AbsNode,
            SubtractNode,
            MultiplyNode,
        ]
    )

    graph.create_node("tp.nodegraph.nodes.DummyNode", "Dummy Node")
    graph.create_node("tp.nodegraph.nodes.MultiplyNode", "Multiply Node")
    graph.create_node("tp.nodegraph.nodes.SubtractNode", "Subtract Node")
    graph.create_node("tp.nodegraph.nodes.SubtractNode", "Subtract Node")

    return graph
