from __future__ import annotations

import uuid
import enum
import typing

from tp.core import log
from tp.common.nodegraph.core import socket
from tp.common.nodegraph.graphics import edge

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.graph import NodeGraph

logger = log.rigLogger


class Edge:

    class Type(enum.Enum):
        DIRECT = edge.GraphicsEdgeDirect
        BEZIER = edge.GraphicsEdgeBezier
        SQUARE = edge.GraphicsEdgeSquare

    def __init__(
            self, graph: NodeGraph, start_socket: socket.Socket | None = None, end_socket: socket.Socket | None = None,
            silent: bool = False):
        super().__init__()

        self._uuid = str(uuid.uuid4())
        self._graph = graph
        self._start_socket: socket.Socket | None = None
        self._end_socket: socket.Socket | None = None
        self._graphics_edge: edge.GraphicsEdge | None = None

        self.set_start_socket(start_socket, silent=silent)
        self.set_end_socket(end_socket, silent=silent)
        self.update_edge_graphics_type()
        self._graph.add_edge(self)

    def __str__(self) -> str:
        return f'<{self.__class__.__name__} {hex(id(self))[2:5]}..{hex(id(self))[-3]}>'

    @property
    def uuid(self) -> str:
        return self._uuid

    @uuid.setter
    def uuid(self, value: str):
        self._uuid = value

    @property
    def start_socket(self) -> socket.Socket:
        return self._start_socket

    @start_socket.setter
    def start_socket(self, value: socket.Socket):
        self.set_start_socket(value, silent=False)

    @property
    def end_socket(self) -> socket.Socket:
        return self._end_socket

    @end_socket.setter
    def end_socket(self, value):
        self.set_end_socket(value, silent=False)

    @property
    def edge_type(self) -> Edge.Type:
        return self._edge_type

    @edge_type.setter
    def edge_type(self, value: int | str | Edge.Type):
        if isinstance(value, int):
            self._edge_type = list(Edge.Type)[value]
        elif isinstance(value, str):
            self._edge_type = Edge.Type[value]
        elif isinstance(value, Edge.Type):
            self._edge_type = value
        else:
            logger.error(f'Invalid edge type value: {value}')
            self._edge_type = Edge.Type.BEZIER

        if hasattr(self, '_graphics_edge') and self._graphics_edge is not None:
            self._graph.graphics_scene.removeItem(self._graphics_edge)

        self._graphics_edge = self._edge_type.value(self)
        self._graph.graphics_scene.addItem(self._graphics_edge)
        if self.start_socket or self.end_socket:
            self.update_positions()

    @property
    def graphics_edge(self) -> edge.GraphicsEdge:
        return self._graphics_edge

    def set_start_socket(self, value: socket.Socket | None, silent: bool = False):
        """
        Sets start socket instance this edge is connected to.

        :param Socket value: start socket.
        :param bool silent: whether to emit remove signals, so listeners are notified.
        :raises ValueError: if given socket is not valid
        """

        if value is not None and not isinstance(value, socket.Socket):
            logger.error(f'Invalid value passed as start socket: {value}')
            raise ValueError

        if self._start_socket is not None:
            self._start_socket.remove_edge(self, silent=silent)

        self._start_socket = value
        if self._start_socket is not None:
            self._start_socket.set_connected_edge(self, silent=silent)

    def set_end_socket(self, value: socket.Socket | None, silent: bool = False):
        """
        Sets end socket instance this edge is connected to.

        :param Socket value: end socket.
        :param bool silent: whether to emit remove signals, so listeners are notified.
        :raises ValueError: if given socket is not valid
        """

        if value is not None and not isinstance(value, socket.Socket):
            logger.error(f'Invalid value passed as end socket: {value}')
            raise ValueError

        if self._end_socket is not None:
            self._end_socket.remove_edge(self, silent=silent)

        self._end_socket = value
        if self._end_socket is not None:
            self._end_socket.set_connected_edge(self, silent=silent)

    def other_socket(self, this_socket: socket.Socket):
        result = None
        if this_socket is self.start_socket:
            result = self.end_socket
        elif this_socket is self.end_socket:
            result = self.start_socket
        return result

    def assigned_socket(self) -> socket.Socket | tuple[socket.Socket, socket.Socket]:
        if self.start_socket and self.end_socket:
            return self.start_socket, self.end_socket
        elif not self.end_socket:
            return self.start_socket
        else:
            return self.end_socket

    def update_positions(self):
        """
        Updates edge positions.
        """

        if not self._graphics_edge:
            return

        if self.start_socket is not None:
            source_pos = self.start_socket.position()
            source_pos[0] += self.start_socket.node.view.pos().x()
            source_pos[1] += self.start_socket.node.view.pos().y()
            self._graphics_edge.set_source(*source_pos)

        if self.end_socket is not None:
            end_pos = self.end_socket.position()
            end_pos[0] += self.end_socket.node.view.pos().x()
            end_pos[1] += self.end_socket.node.view.pos().y()
            self._graphics_edge.set_destination(*end_pos)

        if not self.start_socket:
            self._graphics_edge.set_source(*end_pos)
        if not self.end_socket:
            self._graphics_edge.set_destination(*source_pos)
        self._graphics_edge.update()

    def update_edge_graphics_type(self):
        """
        Internal function that forces the update of the graphics type.
        """

        self.edge_type = self._graph.edge_type

    def remove_from_sockets(self, silent: bool = False):
        """
        Removes this edge from current start and end sockets.

        :param bool silent: whether to emit remove signals, so listeners are notified.
        """

        self.set_start_socket(None, silent=silent)
        self.set_end_socket(None, silent=silent)

    def remove(self, silent: bool = False):
        """
        Deletes edge.

        :param bool silent: whether to emit remove signals, so listeners are notified.
        """

        self.remove_from_sockets(silent=silent)
        self._graph.graphics_scene.removeItem(self._graphics_edge)
        self._graphics_edge = None
        if self in self._graph.edges:
            self._graph.remove_edge(self)
