from __future__ import annotations

import typing

from tp.core import log
from tp.common.qt import api as qt

from tp.common.nodegraph.core import socket, edge
from tp.common.nodegraph.graphics import socket as socket_view


if typing.TYPE_CHECKING:
    from tp.common.nodegraph.graphics.view import GraphicsView

logger = log.rigLogger


class EdgeDrag:
    def __init__(self, graphics_view: GraphicsView):
        super().__init__()

        self._graphics_view = graphics_view
        self._drag_edge: edge.Edge | None = None
        self._drag_start_socket: socket.Socket | None = None

    @property
    def drag_edge(self) -> edge.Edge:
        return self._drag_edge

    def source_socket_datatype(self) -> dict | None:
        if not self._drag_start_socket:
            return None
        return self._drag_start_socket.data_type

    def update_positions(self, x: int, y: int):

        if self._drag_edge is not None and self._drag_edge.graphics_edge is not None:
            if self._drag_edge.start_socket:
                self._drag_edge.graphics_edge.set_destination(x, y)
            else:
                self._drag_edge.graphics_edge.set_source(x, y)
            self._drag_edge.graphics_edge.update()
        else:
            logger.error('Tried to update self._drag_edge.graphics_edge, but it is None')

    def start_edge_drag(self, item: qt.QGraphicsItem):
        try:
            logger.debug('Start dragging edge: {}'.format(self._graphics_view.edge_mode))
            self._drag_start_socket = item.socket
            if isinstance(item.socket, socket.OutputSocket):
                logger.debug('Assign start socket to: {0}'.format(item.socket))
                self._drag_edge = edge.Edge(
                    self._graphics_view.graphics_scene.graph, start_socket=item.socket, end_socket=None, silent=True)
            else:
                logger.debug('Assign end socket to: {0}'.format(item.socket))
                self._drag_edge = edge.Edge(
                    self._graphics_view.graphics_scene.graph, start_socket=None, end_socket=item.socket, silent=True)
        except Exception:
            logger.exception('Start edge drag exception')
            self._drag_edge.remove(silent=True)
            self._drag_edge = None
            self._drag_start_socket = None

    def end_edge_drag(self, item: qt.QGraphicsItem) -> bool:
        if isinstance(item, socket.Socket):
            item = item.graphics_socket

        self._graphics_view.reset_edge_mode()
        self._drag_edge.remove(silent=True)
        self._drag_edge = None

        # Non socket click or can't be connected
        if not isinstance(item, socket_view.GraphicsSocket) or not item.socket.can_be_connected(
                self._drag_start_socket):
            logger.debug('Canceling edge dragging')
            self._drag_start_socket = None
            return False

        # Another connectable socket clicked
        start_socket = None
        end_socket = None
        if isinstance(item.socket, socket.OutputSocket):
            logger.debug(f'Assign start socket: {item.socket}')
            start_socket = item.socket
            end_socket = self._drag_start_socket
        elif isinstance(item.socket, socket.InputSocket):
            logger.debug(f'Assign end socket: {item.socket}')
            start_socket = self._drag_start_socket
            end_socket = item.socket
        try:
            new_edge = edge.Edge(self._graphics_view.graphics_scene.graph, start_socket=start_socket, end_socket=end_socket)
            self._drag_start_socket = None
            logger.debug(f'EdgeDrag: created new edge {new_edge.start_socket} -> {new_edge.end_socket}')
            self._graphics_view.graphics_scene.graph.history.store_history('Edge created by dragging', set_modified=True)
            return True
        except Exception:
            self._drag_start_socket = None
            logger.exception('End edge drag exception')
            return False
