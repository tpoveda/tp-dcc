import pytest

from tp.nodegraph.nodes.node_function import FunctionNode
from tp.nodegraph.core.exceptions import (
    NodeNotFoundError,
    NodeAlreadyRegisteredError,
    NodeAliasAlreadyRegisteredError,
)


class DummyNode(FunctionNode):
    def __init__(self, name: str = "dummy"):
        super().__init__(
            name=name,
            func=lambda x: x,
            input_types=[float],
            output_types=float,
        )


class DummyNode2(FunctionNode):
    def __init__(self, name: str = "dummy"):
        super().__init__(
            name=name,
            func=lambda x: x,
            input_types=[float],
            output_types=float,
        )


def test_register_node(factory):
    """Test registering a node in the factory."""

    factory.register_node(DummyNode)
    assert "tp.nodegraph.nodes.DummyNode" in factory._node_classes


def test_register_invalid_node(factory):
    """Test registering an invalid node in the factory."""

    factory.register_node(None)
    assert "tp.nodegraph.nodes.DummyNode" not in factory._node_classes


def test_register_node_with_alias(factory):
    """Test registering a node in the factory with an alias."""

    factory.register_node(DummyNode, "dummy")
    assert "dummy" in factory._node_aliases


# noinspection PyTypeChecker
def test_already_registered(factory):
    """Test registering a node that is already registered."""
    factory.register_node(DummyNode)
    with pytest.raises(
        NodeAlreadyRegisteredError,
        match='Node with ID "tp.nodegraph.nodes.DummyNode" is already registered.',
    ):
        factory.register_node(DummyNode)


def test_already_registered_with_alias(factory):
    """Test registering a node that is already registered with an alias."""

    factory.register_node(DummyNode, "dummy")
    with pytest.raises(
        NodeAliasAlreadyRegisteredError,
        match='Node with alias "dummy" is already registered.',
    ):
        factory.register_node(DummyNode2, "dummy")


def test_node_class_by_id_found_in_classes(factory):
    """Test getting a node class by its ID."""

    factory.register_node(DummyNode)
    node_class = factory.node_class_by_id("tp.nodegraph.nodes.DummyNode")
    assert node_class is DummyNode


def test_node_class_by_id_found_in_aliases(factory):
    """Test getting a node class by its ID from aliases."""

    factory.register_node(DummyNode, "dummy")
    node_class = factory.node_class_by_id("dummy")
    assert node_class is DummyNode


def test_node_class_by_id_not_found(factory):
    """Test getting a node class by its ID when not found."""

    with pytest.raises(NodeNotFoundError) as exc_info:
        factory.node_class_by_id("non_existent_node")
    assert str(exc_info.value) == 'Node with ID "non_existent_node" not found.'
    assert exc_info.value.node_id == "non_existent_node"


def test_node_class_by_id_alias_not_found(factory):
    """Test getting a node class by its ID when the alias is not found."""

    factory._node_aliases["alias_for_non_existent_node"] = "non_existent_node"
    with pytest.raises(NodeNotFoundError) as exc_info:
        factory.node_class_by_id("alias_for_non_existent_node")
    assert (
        str(exc_info.value) == 'Node with ID "alias_for_non_existent_node" not found.'
    )
    assert exc_info.value.node_id == "alias_for_non_existent_node"


def test_create_unrecognized_node(factory):
    """Test creating a node with an unrecognized ID."""

    with pytest.raises(
        NodeNotFoundError, match='Node with ID "unrecognized" not found.'
    ):
        factory.create_node("unrecognized")


def test_create_node(factory):
    """Test creating a node from the registry."""

    factory.register_node(DummyNode, "dummy")
    node1 = factory.create_node("dummy")
    assert isinstance(node1, FunctionNode)


def test_clear_registered_nodes(factory):
    """Test clearing registered nodes."""

    factory.register_node(DummyNode)
    factory.clear_registered_nodes()
    assert factory._node_classes == {}
    assert factory._node_aliases == {}
