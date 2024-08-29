from tp.nodegraph.core.commands import AddNodeCommand, RemoveNodeCommand


def test_add_node_command(graph, node):
    """Test adding a node to the graph."""

    command = AddNodeCommand(graph, node)
    command.redo()
    assert node.id in graph.model.nodes
    command.undo()
    assert node.id not in graph.model.nodes


def test_remove_node_command(graph, node):
    """Test removing a node from the graph."""

    graph.add_node(node)
    command = RemoveNodeCommand(graph, node)
    command.redo()
    assert node.id not in graph.model.nodes
    command.undo()
    assert node.id in graph.model.nodes
