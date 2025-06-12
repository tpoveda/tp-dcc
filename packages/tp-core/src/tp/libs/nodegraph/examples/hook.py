from __future__ import annotations

import typing

from ..core.graph import NodeGraph
from ...python import paths

if typing.TYPE_CHECKING:
    from .model import CreateNewGraphEvent


class NodeGraphHook:
    """
    Class that defines a hook for Node Graph tool.
    """

    @staticmethod
    def new_build_graph(event: CreateNewGraphEvent):
        """
        Function that creates a new build graph.

        :param event: create new graph event.
        """

        menu_path = paths.canonical_path("menu.json")
        node_graph = NodeGraph()
        node_graph.set_context_menu_from_file(menu_path)
        event.node_graph = node_graph
        event.success = True
