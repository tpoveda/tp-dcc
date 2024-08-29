from __future__ import annotations

import typing
import timeit
import logging
from collections import deque

from ..nodes.node_input import GraphInputNode

if typing.TYPE_CHECKING:
    from .node import Node
    from .graph import NodeGraph

logger = logging.getLogger(__name__)


class NodeGraphExecutor:
    """
    Class that defines a graph executor.
    """

    def __init__(self, graph: NodeGraph):
        super(NodeGraphExecutor, self).__init__()

        self._graph = graph
        self._step: int = 0
        self._execution_chain = deque()
        self._execution_set = set()

    @property
    def graph(self) -> NodeGraph:
        """
        Getter method that returns the graph.

        :return: graph.
        """

        return self._graph

    def verify_graph(self) -> bool:
        """
        Verifies the graph.

        :return: bool
        """

        logger.info("Verifying graph...")
        invalid_nodes: deque[Node] = deque()
        for node in self._execution_chain:
            result = node.verify()
            if not result:
                node.is_invalid = True
                invalid_nodes.append(node)
        if invalid_nodes:
            for node in invalid_nodes:
                logger.warning(f"Invalid node: {node.name}")
            return False

        return True

    def ready_to_execute(self) -> bool:
        """
        Returns whether the executor is ready to execute or not.

        :return: bool
        """

        self.reset_nodes_compiled_state()
        input_node = self.find_input_node()
        if not input_node:
            return False

        self._execution_chain = input_node.exec_queue()

        return True

    def reset_nodes_compiled_state(self):
        """
        Resets the compiled state of all nodes in the graph.
        """

        for node in self.graph.nodes():
            node.is_compiled = False

    def reset_stepped_execution(self):
        """
        Resets the stepped execution.
        """

        self._step = 0
        self._execution_chain.clear()
        self._execution_set.clear()

    def find_input_node(self) -> GraphInputNode | None:
        """
        Returns the input node of the graph.

        :return: graph input node.
        """

        input_nodes = [
            node for node in self.graph.nodes() if isinstance(node, GraphInputNode)
        ]
        if not input_nodes:
            logger.error("At least one input node is required!")
            return None
        elif len(input_nodes) > 1:
            logger.warning("More than one input node found. Using the first one.")

        return input_nodes[0]

    def execute(self):
        """
        Executes the graph.
        """

        self.reset_stepped_execution()
        if not self.ready_to_execute():
            logger.warning(f'Graph "{self.graph}" is not read to execute.')
            return

        logger.info("Initializing new build...")
        start_time = timeit.default_timer()
        self.graph.is_executing = True
        for node in self._execution_chain:
            # noinspection PyBroadException
            try:
                # noinspection PyProtectedMember
                node._execute()
            except Exception:
                logger.exception(f'Failed to execute node "{node.name}"', exc_info=True)
                self.graph.is_executing = False
                return

        logger.info(
            f"Build finished in {timeit.default_timer() - start_time:.2f} seconds"
        )
        self.graph.is_executing = False
