from __future__ import annotations

import uuid
import enum
import typing
from typing import Any

from overrides import override

from tp.core import log
from tp.common.qt import api as qt
from tp.common.nodegraph import registers, datatypes
from tp.common.nodegraph.graphics import socket

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.node import Node
    from tp.common.nodegraph.core.edge import Edge

logger = log.rigLogger


class Socket:

    class Signals(qt.QObject):
        valueChanged = qt.Signal()
        connectionChanged = qt.Signal()

    class Position(enum.IntEnum):
        LeftTop = 1
        LeftCenter = 2
        LeftBottom = 3
        RightTop = 4
        RightCenter = 5
        RightBottom = 6

    LABEL_VERTICAL_PADDING = -10.0

    def __init__(
            self, node: Node, index: int = 0, position: Position = Position.LeftTop,
            data_type: dict = datatypes.Numeric, label: str | None = None, max_connections: int = 0, value: Any = None,
            count_on_this_side: int = 0):
        super().__init__()

        self._uuid = str(uuid.uuid4())
        self._node = node
        self._index = index
        self._node_position = position if isinstance(position, Socket.Position) else Socket.Position(position)
        self._data_type = data_type
        self._label = label or self._data_type.get('label')
        self._max_connections = max_connections
        self._count_on_this_side = count_on_this_side
        self._edges: list[Edge] = []
        self._value = value or self._data_type.get('default')
        self._default_value = self.value()
        self._signals = Socket.Signals()
        self._affected_sockets: list[Socket] = []

        self._graphics_socket = socket.GraphicsSocket(self)
        self.update_positions()

        self._setup_signals()

    def __str__(self) -> str:
        return f'<{self.__class__.__name__} {hex(id(self))[2:5]}..{hex(id(self))[-3]}>'

    @property
    def signals(self) -> Signals:
        return self._signals

    @property
    def uuid(self) -> str:
        return self._uuid

    @uuid.setter
    def uuid(self, value: str):
        self._uuid = value

    @property
    def node(self) -> Node:
        return self._node

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, value: int):
        self._index = value

    @property
    def node_position(self) -> Socket.Position:
        return self._node_position

    @property
    def data_type(self) -> dict:
        return self._data_type

    @data_type.setter
    def data_type(self, value: str | dict):
        if isinstance(value, str):
            self._data_type = registers.DATA_TYPES_REGISTER[value]
        elif isinstance(value, dict):
            self._data_type = value
        else:
            logger.error(f'Cannot set data type to "{value}"')
            raise ValueError
        if hasattr(self, '_graphics_socket'):
            self._graphics_socket.color_background = self._data_type.get('color')
            self._graphics_socket.update()
        self.node.view.update_size()

    @property
    def data_class(self) -> type:
        return self.data_type.get('class')

    @property
    def max_connections(self) -> int:
        return self._max_connections

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, value: str):
        self._label = value
        self._graphics_socket.text_item.setPlainText(self._label)

    @property
    def default_value(self) -> Any:
        return self._default_value

    @default_value.setter
    def default_value(self, value: Any):
        self._default_value = value

    @property
    def edges(self) -> list[Edge]:
        return self._edges

    @property
    def graphics_socket(self) -> socket.GraphicsSocket:
        return self._graphics_socket

    def is_runtime_data(self) -> bool:
        """
        Returns whether data contained by this socket is runtime data.

        :return: True if socket data is runtime; False otherwise.
        :rtype: bool
        """

        runtime_classes = datatypes.runtime_types(classes=True)
        return self.data_class in runtime_classes or self.value().__class__ in runtime_classes

    def value(self) -> Any:
        """
        Returns socket internal value.

        :return: socket value.
        :rtype: Any
        """

        return self._value

    def set_value(self, value: Any):
        """
        Sets socket internal value.

        :param Any value: internal value.
        """

        if self.data_type == datatypes.Exec:
            return
        if self._value == value:
            return

        self._value = value
        self._signals.valueChanged.emit()

    def reset_value_to_default(self):
        """
        Resets socket internal value to its default value.
        """

        self.set_value(self.default_value)

    def affects(self, other_socket: Socket):
        """
        Adds given socket into the list of affect sockets by this one.
        This means, that if this socket value changes, given socket will be processed too.

        :param Socket other_socket: affected socket.
        """

        self._affected_sockets.append(other_socket)

    def can_be_connected(self, other_socket: Socket) -> bool:
        """
        Returns whether this socket can be connected to the given one.

        :param Socket other_socket: socket to connect.
        :return: True if this socket can be connected to the given one; False otherwise.
        :rtype: bool
        """

        # Clicking on socket edge is dragging from
        if self is other_socket:
            return False

        # Trying to connect output->output or input->input
        if isinstance(other_socket, self.__class__):
            logger.warning('Cannot connect two sockets of the same type')
            return False

        if self.node is other_socket.node:
            logger.warning('Cannot connect sockets on the same node')
            return False

        return True

    def list_connections(self) -> list[Socket]:
        """
        Returns list of sockets that are connected to this one.

        :return: list of connected sockets.
        :rtype: list[Socket]
        """

        connected_sockets = []
        for edge in self.edges:
            for found_socket in [edge.start_socket, edge.end_socket]:
                if found_socket and found_socket != self:
                    connected_sockets.append(found_socket)

        return connected_sockets

    def update_affected(self):
        """Updates affected nodes with the current node value.
        """

        for affected_socket in self._affected_sockets:
            affected_socket.set_value(self.value())

    def has_edge(self) -> bool:
        """
        Returns whether this socket is connected.

        :return: True if socket is connected; False otherwise.
        :rtype: bool
        """

        return bool(self._edges)

    def update_edges(self):
        """
        Updates connected edge positions.
        """

        for connected_edge in self._edges:
            connected_edge.update_positions()

    def position(self) -> list[int, int]:
        """
        Returns the position of the socket at given index.

        :return: node position.
        :rtype: list[int, int]
        """
        return self.node.socket_position(self.index, self.node_position, self._count_on_this_side)

    def update_positions(self):
        """
        Updates the position of the graphics socket.
        """

        def _label_position():
            text_width = self._graphics_socket.text_item.boundingRect().width()
            if self._node_position in [Socket.Position.LeftTop, Socket.Position.LeftBottom]:
                return [self.node.view.width / 25.0, Socket.LABEL_VERTICAL_PADDING]
            else:
                return [-text_width - self.node.view.width / 25, Socket.LABEL_VERTICAL_PADDING]

        self._graphics_socket.setPos(
            *self.node.socket_position(self._index, self._node_position, self._count_on_this_side))
        self._graphics_socket.text_item.setPos(*_label_position())

    def label_width(self) -> float:
        """
        Returns width for sockets label.

        :return: sockets label width.
        :rtype: float
        """

        return self._graphics_socket.text_item.boundingRect().width()

    def set_connected_edge(self, edge: Edge, silent: bool = False):
        """
        Connects this socket to given edge.

        :param Edge edge: edge to connect to.
        :param bool silent: whether to emit remove signals, so listeners are notified.
        """

        if not edge:
            logger.warning(f'{self}: Given edge {edge}')
            return

        if self.edges and self.max_connections and len(self.edges) >= self.max_connections:
            self.edges[-1].remove()
        self.edges.append(edge)

        if not silent:
            self._signals.connectionChanged.emit()

    def remove_edge(self, edge: Edge, silent: bool = False):
        """
        Removes given edge from this socket.

        :param Edge edge: edge instance to remove.
        :param bool silent: whether to emit remove signals, so listeners are notified.
        """

        self._edges.remove(edge)
        if not silent:
            self._signals.connectionChanged.emit()

    def remove_all_edges(self, silent: bool = False):
        """
        Removes all edges connected to this socket.

        :param bool silent: whether to emit remove signals, so listeners are notified.
        """

        while self._edges:
            self._edges[0].remove(silent=silent)
        self._edges.clear()

    def remove(self, silent: bool = False):
        """
        Deletes socket.

        :param bool silent: whether to emit remove signals, so listeners are notified.
        """

        self.remove_all_edges(silent=silent)
        self.node.graph.graphics_scene.removeItem(self._graphics_socket)

    def _setup_signals(self):
        """
        Internal function that setup socket signals.
        """

        pass


class InputSocket(Socket):

    @override
    def can_be_connected(self, other_socket: Socket) -> bool:
        result = super().can_be_connected(other_socket)
        if not issubclass(other_socket.data_class, self.data_class):
            return False
        return result

    @override
    def value(self) -> Any:
        if self.has_edge():
            output_socket = self.edges[0].other_socket(self)
            if output_socket:
                return output_socket.value()
        return self._value

    @override
    def _setup_signals(self):
        super()._setup_signals()

        self._signals.valueChanged.connect(self.node.set_compiled)
        self._signals.connectionChanged.connect(self._on_connection_changed)

    def _on_connection_changed(self):
        """
        Internal callback function that is called each time connection changes.
        """

        if not self.has_edge() and self.is_runtime_data():
            self.set_value(self.data_type['default'])


class OutputSocket(Socket):

    @override
    def can_be_connected(self, other_socket: Socket) -> bool:
        result = super().can_be_connected(other_socket)
        if not issubclass(self.data_class, other_socket.data_class):
            return False
        return result

    @override
    def _setup_signals(self):
        super()._setup_signals()

        self._signals.valueChanged.connect(self._on_value_changed)

    def _on_value_changed(self):
        """
        Internal callback function that is called each time socket value changes.
        """

        for connected_socket in self.list_connections():
            connected_socket.signals.valueChanged.emit()
