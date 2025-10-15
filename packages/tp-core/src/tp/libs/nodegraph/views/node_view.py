from __future__ import annotations


from Qt.QtWidgets import QAbstractItemView


class AbstractNodeView(QAbstractItemView):
    """Abstract base class for node views in the node graph.

    This class provides a common interface for all node views, ensuring that
    they implement the necessary methods for displaying and interacting with
    nodes in the graph.
    """


class NodeView(AbstractNodeView):
    """Concrete implementation of a node view in the node graph.

    This class extends the `AbstractNodeView` and provides specific
    implementations for the methods required to display and interact with
    nodes in the graph.
    """
