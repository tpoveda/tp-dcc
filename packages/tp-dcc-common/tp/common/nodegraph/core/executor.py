from __future__ import annotations

import timeit
import typing
from collections import deque

from tp.core import log

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import Node
    from tp.common.nodegraph.core.graph import NodeGraph
    from tp.common.nodegraph.nodes.node_graph_inout import GraphInputNode

logger = log.tpLogger


class GraphExecutor:
    def __init__(self, graph: NodeGraph):
        super().__init__()

        self._graph = graph
        self._step = 0
        self._exec_chain: deque[Node] = deque()
        self._exec_set: set[Node] = set()

    @property
    def graph(self) -> NodeGraph:
        return self._graph

    @property
    def exec_chain(self) -> deque[Node]:
        return self._exec_chain

    @exec_chain.setter
    def exec_chain(self, value: deque[Node]):
        self._exec_chain = value
        self._exec_set = set(value)

    @property
    def exec_set(self) -> set[Node]:
        return self._exec_set

    def reset_stepped_execution(self):
        """
        Resets executor internal variables.
        """

        self._step = 0
        self._exec_chain.clear()
        self._exec_set.clear()

    def find_input_node(self) -> GraphInputNode | None:
        """
        Returns the input node to start the graph execution from.

        :return: input node instance.
        :rtype: GraphInputNode or None
        """

        input_nodes: list[GraphInputNode] = [node for node in self.graph.nodes if node.IS_INPUT]
        if not input_nodes:
            logger.error('At least one input node is required!')
            return None
        elif len(input_nodes) > 1:
            logger.warning('More than 1 input node in the scene. Only the first one added will be executed')

        return input_nodes[0]

    def verify_graph(self) -> bool:
        """
        Returns whether all nodes within graph are valid.

        :return: True if all graph nodes are valid; False otherwise.
        :rtype: bool
        """

        logger.info('Verifying graph...')
        invalid_nodes: deque[Node] = deque()
        for node in self.exec_chain:
            result = node.verify()
            if not result:
                node.set_invalid(True)
                invalid_nodes.append(node)
        if invalid_nodes:
            for node in invalid_nodes:
                logger.warning(f'Invalid node: {node.title}')
            return False

        return True

    def ready_to_execute(self) -> bool:
        """
        Returns whether current graph is ready to be executed.

        :return: True if graph can be executed; False otherwise.
        :rtype: bool
        """

        self._reset_nodes_compiled_data()
        input_node = self.find_input_node()
        if not input_node:
            return False

        self.exec_chain = input_node.exec_queue()
        result = self.verify_graph()
        if not result:
            logger.warning('Invalid graph, execution cancelled')
            return False

        return True

    def execute_step(self):
        """
        Executes one step in the execution chain.
        """

        if self._step == len(self._exec_chain):
            self.reset_stepped_execution()

        if not self._exec_chain and not self.ready_to_execute():
            return

        try:
            self.graph.is_executing = True
            node_to_execute = self._exec_chain[self._step]
            node_to_execute.execute()
            self._step += 1
        except Exception:
            logger.exception(f'Failed to execute {node_to_execute.title}', exc_info=True)
        finally:
            self.graph.is_executing = False

    def execute_graph(self):
        """
        Executes graph.
        """

        self.reset_stepped_execution()
        if not self.ready_to_execute():
            return

        logger.info('Initializing new build...')
        start_time = timeit.default_timer()
        self.graph.is_executing = True

        try:
            for node in self.exec_chain:
                try:
                    node._exec()
                except Exception:
                    logger.exception(f'Failed to execute {node.title}', exc_info=True)
                    self.graph.is_executing = False
                    return
        finally:
            logger.info('Build finished in {0:.2f}s'.format(timeit.default_timer() - start_time))
            self.graph.is_executing = False

    def _reset_nodes_compiled_data(self):
        """
        Internal function that resets the compile status for all the nodes within the graph.
        """

        for node in self.graph.nodes:
            if not node.COMPILABLE:
                continue
            node.set_compiled(False, emit_signal=False)

