from __future__ import annotations

from Qt.QtCore import QObject, Signal

from .graph import Graph
from ..utils.naming import unique_name_from_list

ROOT_GRAPH_NAME = "root"


class GraphManager(QObject):
    """Class that holds a graph tree that allows to switch to different graphs."""

    graphChanged = Signal(Graph)

    def __init__(self):
        super().__init__()

        self._graphs: dict[str, Graph] = {}
        self._active_graph = Graph(self, name=ROOT_GRAPH_NAME)
        self._active_graph.is_root = True

    # === Graph Queries === #

    def register_graph(self, graph: Graph) -> None:
        """Registers a new graph in the graph manager.

        Args:
            graph: The graph to register.
        """

        graph.name = self.unique_graph_name(graph.name)
        self._graphs[graph.id] = graph

    # === Graph Queries === #

    def list_graphs(self) -> list[Graph]:
        """Returns the list of graphs in the graph manager.

        Returns:
            List of graphs.
        """

        return list(self._graphs.values())

    def graphs_by_name(self) -> dict[str, Graph]:
        """Returns a dictionary of graphs in the graph manager indexed by
        their names.

        Returns:
            Dictionary of graphs indexed by their names.
        """

        return {graph.name: graph for graph in self.list_graphs()}

    def find_root_graph(self) -> Graph:
        """Returns the root graphs of the graph manager.

        Returns:
            The root graph.
        """

        root_graphs = [graph for graph in self.list_graphs() if graph.is_root]
        assert len(root_graphs) == 1, "There should be only one root graph"
        return root_graphs[0]

    def find_graph(self, name: str) -> Graph | None:
        """Finds a graph by its name.

        Args:
            name: The name of the graph to find.

        Returns:
            The graph if found; `None` otherwise.
        """

        return self.graphs_by_name().get(name, None)

    # === Graph Management === #

    def clear(self, keep_root: bool = True):
        self.select_graph_by_name(ROOT_GRAPH_NAME)
        self.remove_graph_by_name(ROOT_GRAPH_NAME)
        self._active_graph = None
        self._graphs.clear()

        if keep_root:
            self._active_graph = Graph(self, name=ROOT_GRAPH_NAME)
            self._active_graph.is_root = True
            self.select_graph(self._active_graph)

    @property
    def active_graph(self) -> Graph:
        """The currently active graph."""

        return self._active_graph

    def select_graph(self, active_graph: Graph) -> bool:
        """Set the given graph as the active graph.

        Args:
            active_graph: The graph to set as active.

        Returns:
            `True` if the graph was set as active; `False` otherwise.
        """

        found_graph: Graph | None = None
        for graph in self.list_graphs():
            if active_graph.name == graph.name:
                if graph.name != self._active_graph.name:
                    found_graph = graph
                    break

        if found_graph is None:
            return False

        self._active_graph = found_graph
        self.graphChanged.emit(self._active_graph)

        return True

    def select_graph_by_name(self, name: str) -> bool:
        """Set the graph with the given name as the active graph.

        Args:
            name: The name of the graph to set as active.

        Returns:
            `True` if the graph was set as active; `False` otherwise.
        """

        graphs_by_name = self.graphs_by_name()
        if name not in graphs_by_name:
            return False

        if name == self._active_graph.name:
            return False

        found_graph = graphs_by_name[name]
        self._active_graph = found_graph
        self.graphChanged.emit(self._active_graph)

        return True

    def select_root_graph(self):
        """Set the root graph as the active graph."""

        root_graph = self.find_root_graph()
        self.select_graph(root_graph)

    def remove_graph(self, graph: Graph) -> bool:
        """Removes the given graph from the graph manager.

        Args:
            graph: The graph to remove.

        Returns:
            `True` if the graph was removed; `False` otherwise.
        """

        if graph.id not in self._graphs:
            return False

        graph.clear()
        self._graphs.pop(graph.id)
        if graph.parent_graph is not None:
            graph.parent_graph.child_graphs.remove(graph)
        del graph

        return True

    def remove_graph_by_name(self, name: str) -> bool:
        """Removes the graph with the given name from the graph manager.

        Args:
            name: The name of the graph to remove.

        Returns:
            `True` if the graph was removed; `False` otherwise.
        """

        graph = self.find_graph(name)
        if graph is None:
            return False

        return self.remove_graph(graph)

    # === Unique Names ===

    def unique_graph_name(self, name: str):
        """Generates a unique graph name based on the given name.

        Args:
            name: The base name to generate a unique name from.

        Returns:
            A unique graph name.
        """

        existing_names = [graph.name for graph in self.list_graphs()]
        return unique_name_from_list(existing_names, name)
