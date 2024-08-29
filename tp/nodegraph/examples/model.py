from __future__ import annotations

import typing
import logging
from dataclasses import dataclass

from Qt.QtCore import Signal

from ...qt import mvc

if typing.TYPE_CHECKING:
    from ..core.graph import NodeGraph

logger = logging.getLogger(__name__)


@dataclass
class CreateNewGraphEvent:
    """
    Event class that defines a new graph created event.
    """

    node_graph: NodeGraph | None = None
    success: bool = False


class NodeGraphModel(mvc.Model):
    """
    Model class for NodeGraph application.
    """

    createNewGraph = Signal(CreateNewGraphEvent)

    def __init__(self):
        super().__init__()

        self.state["title"]: str = "Noddle Builder v0.0.1"
        self.state["node_graphs"]: list[NodeGraph] = []
        self.state["active_node_graph"]: NodeGraph | None = None

    def set_active_node_graph(self, node_graph: NodeGraph | None):
        """
        Function that sets the active node graph.

        :param node_graph: Node graph to set as active.
        """

        self.update("active_node_graph", node_graph, force=True)
        if not node_graph:
            self.update("title", "Noddle Builder v0.0.1")
        else:
            self.update("title", "Noddle Builder v0.0.1 - Untitled")

    def new_graph(self):
        """
        Function that creates a new graph.
        """

        event = CreateNewGraphEvent()
        self.createNewGraph.emit(event)
        if not event.success or not event.node_graph:
            logger.warning("Was not possible to create a new build graph.")
            return

        node_graphs = self.state["node_graphs"]
        node_graphs.append(event.node_graph)
        self.update("node_graphs", node_graphs, force=True)

    def execute_graph(self):
        """
        Function that executes the active graph.
        """

        active_graph: NodeGraph | None = self.state["active_node_graph"]
        if not active_graph:
            logger.warning("No active graph to execute.")
            return

        active_graph.executor.execute()
