import time
import copy
import traceback
from collections import deque

from tp.core import log
from tp.common.qt import api as qt
from tp.common.nodegraph.nodes import backdrop
from tp.common.nodegraph.core import consts, node, register, socket

logger = log.tpLogger


def _has_input_node(node):
    for p in node.input_sockets():
        if p.view.connectors:
            return True
    return False


def _has_output_node(node):
    for p in node.output_sockets():
        if p.view.connectors:
            return True
    return False


def __remove_backdrop_node(nodes):
    for found_node in nodes[:]:
        if isinstance(node, backdrop.BackdropNode):
            nodes.remove(node)
    return nodes


def _sort_nodes(graph, start_nodes, reverse=True):
    if not graph:
        return []

    visit = dict((node, False) for node in graph.keys())

    sorted_nodes = []

    def dfs(start_node):
        for end_node in graph[start_node]:
            if not visit[end_node]:
                visit[end_node] = True
                dfs(end_node)
        sorted_nodes.append(start_node)

    for start_node in start_nodes:
        if not visit[start_node]:
            visit[start_node] = True
            dfs(start_node)

    if reverse:
        sorted_nodes.reverse()

    return sorted_nodes


def get_output_nodes(node, cook=True):
    nodes = dict()
    for p in node.output_sockets():
        for cp in p.connected_sockets():
            n = cp.node()
            if cook and n.has_property('graph_rect'):
                n.mark_node_to_be_cooked(cp)
            nodes[n.id] = n
    return list(nodes.values())


def get_input_nodes(node):
    nodes = dict()
    for p in node.input_sockets():
        for cp in p.connected_sockets():
            n = cp.node()
            nodes[n.id] = n
    return list(nodes.values())


def _build_down_stream_graph(start_nodes):
    graph = dict()
    for node in start_nodes:
        output_nodes = get_output_nodes(node)
        graph[node] = output_nodes
        while output_nodes:
            _output_nodes = []
            for n in output_nodes:
                if n not in graph:
                    nodes = get_output_nodes(n)
                    graph[n] = nodes
                    _output_nodes.extend(nodes)
            output_nodes = _output_nodes
    return graph


def _build_up_stream_graph(start_nodes):
    graph = dict()
    for node in start_nodes:
        input_nodes = get_input_nodes(node)
        graph[node] = input_nodes
        while input_nodes:
            _input_nodes = []
            for n in input_nodes:
                if n not in graph:
                    nodes = get_input_nodes(n)
                    graph[n] = nodes
                    _input_nodes.extend(nodes)
            input_nodes = _input_nodes
    return graph


def topological_sort_by_down(start_nodes=None, all_nodes=None):

    if not start_nodes and not all_nodes:
        return []
    if start_nodes:
        start_nodes = __remove_backdrop_node(start_nodes)
    if all_nodes:
        all_nodes = __remove_backdrop_node(all_nodes)

    if not start_nodes:
        start_nodes = [n for n in all_nodes if not _has_input_node(n)]
    if not start_nodes:
        return []
    if not [n for n in start_nodes if _has_output_node(n)]:
        return start_nodes

    graph = _build_down_stream_graph(start_nodes)

    return _sort_nodes(graph, start_nodes, True)


def topological_sort_by_up(start_nodes=None, all_nodes=None):

    if not start_nodes and not all_nodes:
        return []
    if start_nodes:
        start_nodes = __remove_backdrop_node(start_nodes)
    if all_nodes:
        all_nodes = __remove_backdrop_node(all_nodes)

    if not start_nodes:
        start_nodes = [n for n in all_nodes if not _has_output_node(n)]
    if not start_nodes:
        return []
    if not [n for n in start_nodes if _has_input_node(n)]:
        return start_nodes

    graph = _build_up_stream_graph(start_nodes)

    return _sort_nodes(graph, start_nodes, False)


class ExecNode(node.BaseNode):

    NODE_NAME = 'Exec'
    IS_EXEC = True
    AUTO_INIT_EXECS = True
    ERROR_COLOR = (200, 50, 50)
    STOP_COOK_COLOR = (200, 200, 200)

    def __init__(self):
        super(ExecNode, self).__init__()

        self._required_inputs = deque()
        self._need_cook = True
        self._is_invalid = False
        self._cook_time = 0.0
        self._tooltip = self._setup_tooltip()
        self._default_value = None

        self.exec_input_socket = None
        self.exec_output_socket = None
        self.init_sockets()

        self._color_effect = qt.QGraphicsColorizeEffect()
        self._color_effect.setStrength(0.7)
        self._color_effect.setEnabled(False)
        self.view.setGraphicsEffect(self._color_effect)

    # ==================================================================================================================
    # PROPERTIES
    # ==================================================================================================================

    @property
    def cook_time(self):
        return self._cook_time

    @cook_time.setter
    def cook_time(self, value):
        self._cook_time = value
        self._update_tooltip()

    @property
    def is_invalid(self):
        return self._is_invalid

    @is_invalid.setter
    def is_invalid(self, flag):
        self._is_invalid = flag

    # ==================================================================================================================
    # BASE
    # ==================================================================================================================

    def exec_queue(self):
        """
        Returns a deque of nodes that should be executed, starting from this node.

        :return: deque of executable nodes.
        :rtype: deque[BaseNode]
        """

        exec_deque = deque([self])

        for exec_out in self.exec_output_sockets():
            if not exec_out.connected_sockets():
                continue
            exec_deque.extend(exec_out.connected_sockets()[0].node().exec_queue())

        return exec_deque

    def verify(self):
        """
        Returns whether this node is valid to be executed.

        :return: True if node can be executed; False otherwise.
        :rtype: bool
        """

        self.view.setToolTip('')
        result = self.verify_input_sockets()

        return result

    def input_data(self, input_socket):
        to_socket = input_socket
        if not isinstance(input_socket, socket.Socket):
            to_socket = self.input(input_socket)
        if to_socket is None:
            return copy.deepcopy(self._default_value)
        from_sockets = to_socket.connected_sockets()
        if not from_sockets:
            if self.has_property(to_socket.name()):
                return self.get_property(to_socket.name())
            return copy.deepcopy(self._default_value)
        for from_socket in from_sockets:
            data = from_socket.node().data(from_socket)
            return copy.deepcopy(data)

        return None

    def data(self, output_socket):
        if self.disabled() and self.input_sockets():
            output_sockets = self.output_sockets()
            if output_socket in output_sockets:
                index = output_sockets.index(output_socket)
                max_index = max(0, len(self.input_sockets()) - 1)
                return self.input_data(min(index, max_index))

        return self.get_property(output_socket.name())

    def cook(self):
        """
        Internal function that executes the node.
        """

        if self._is_invalid:
            self._close_error()

        start_time = time.time()
        logger.info('Cooking {}...'.format(self))
        try:
            self.execute()
            self.update_affected_outputs()
        except Exception:
            logger.exception('Failed to cook {} {}'.format(self.name(), self))
            self.error(traceback.format_exc())
            raise

        if self._is_invalid:
            return

        self._cook_time = time.time() - start_time
        self._need_cook = False

        return 0

    def execute(self):
        """
        Main node execution function. This function should be overriden in custom nodes.
        """

        return 0

    # ==================================================================================================================
    # SOCKETS
    # ==================================================================================================================

    def init_sockets(self, reset=True):
        """
        Initialize the sockets for this node.
        """

        self._required_inputs.clear()
        self.exec_input_socket = None
        self.exec_output_socket = None
        if reset:
            self.delete_all_sockets(force=True)

        if self.__class__.IS_EXEC and self.__class__.AUTO_INIT_EXECS:
            self.exec_input_socket = self.add_input(name='input', data_type=register.DataTypes.EXEC)
            self.exec_output_socket = self.add_output(name='output', data_type=register.DataTypes.EXEC, multi_output=False)

    def exec_output_sockets(self):
        """
        Returns all output sockets which are executable.

        :return: list of executable node output sockets.
        :rtype: list[tp.common.nodegraph.core.socket.Socket]
        """

        return [found_socket for found_socket in self.output_sockets() if found_socket.data_type == register.DataTypes.EXEC]

    def mark_inputs_as_required(self, input_sockets):
        """
        Marks given list of input sockets as required.

        :param list[tp.common.nodegraph.core.socket.Socket] input_sockets: input sockets.
        """

        for input_socket in input_sockets:
            self.mark_input_as_required(input_socket)

    def mark_input_as_required(self, input_socket):
        """
        Marks given input socket as a required input.

        :param tp.common.nodegraph.core.socket.Socket input_socket: input socket.
        """

        if isinstance(input_socket, socket.Socket):
            if not input_socket.direction() == consts.SocketDirection.Input:
                logger.error('Given socket is not an input')
                return
            self._required_inputs.append(input_socket)
        elif isinstance(input_socket, (str, int)):
            found_socket = self.input(input_socket)
            if not found_socket:
                logger.error('Cannot mark given input {} as required@'.format(input_socket))
                return
            self._required_inputs.append(found_socket)
        else:
            logger.error('Invalid required "input socket" argument: {}'.format(input_socket))

    def update_affected_outputs(self):
        """
        Updates all affected outputs of this node.
        """

        for input_socket in self.input_sockets():
            input_socket.update_affected()

    def verify_input_sockets(self):
        """
        Returns whether all input sockets for this node are valid.

        :return: True if all input sockets are valid; False otherwise.
        :rtype: bool
        """

        invalid_input_sockets = deque()
        for input_socket in self._required_inputs:
            if not input_socket.is_connected() and not self.input_data(input_socket):
                invalid_input_sockets.append(input_socket)
        if invalid_input_sockets:
            tool_tip = ''
            for invalid_input_socket in invalid_input_sockets:
                tool_tip += 'Invalid input: {}\n'.format(invalid_input_socket.name())
            self.view.setToolTip(self.view.toolTip() + tool_tip)
            return False

        return True

    def error(self, message):
        self.is_invalid = True
        self._color_effect.setEnabled(True)
        self._color_effect.setColor(qt.QColor(*self.ERROR_COLOR))
        self._update_tooltip('<font color="red"><br>({})</br></font>'.format(message))

    # ==================================================================================================================
    # INTERNAL
    # ==================================================================================================================

    def _setup_tooltip(self):
        tooltip = '<br> last cook used: {}s</br>'
        return self._update_tooltip(tooltip)

    def _update_tooltip(self, message=None):
        if message is None:
            tooltip = self._tooltip.format(self._cook_time)
        else:
            tooltip = '<b>{}</b>'.format(self.name())
            tooltip += message
            tooltip += '<br/>{}<br/>'.format(self._view.type_)
        self.view.setToolTip(tooltip)

        return tooltip

    def _close_error(self):
        self._is_invalid = False
        self._color_effect.setEnabled(False)
        self._update_tooltip()



