from __future__ import annotations

import typing
from typing import Union

from overrides import override

from tp.common.qt import api as qt
from tp.common.python import decorators

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.graph.core.edge import Edge


class GraphicsEdge(qt.QGraphicsPathItem):

    MAX_WIDTH = 6.0
    MIN_WIDTH = 2.0
    WIDTH = 2.0

    def __init__(self, edge: Edge, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._edge = edge
        self._source_position = [0, 0]
        self._destination_position = [200, 100]

        self._color = qt.QColor("#001000")
        self._color_selected = qt.QColor("#00ff00")
        self._pen = qt.QPen(self._color)
        self._pen_selected = qt.QPen(self._color_selected)
        self._pen_dragging = qt.QPen(self._color)
        self._pen_dragging.setStyle(qt.Qt.DashLine)
        self._pen_selected.setWidthF(3.0)
        self._pen_dragging.setWidthF(2.0)

        self._setup_ui()

    @override
    def shape(self) -> qt.QPainterPath:
        return self._calculate_path()

    @override
    def boundingRect(self) -> qt.QRectF:
        return self.shape().boundingRect()

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:

        self.setPath(self._calculate_path())
        self._pen.setWidthF(self.WIDTH)

        if self._edge.end_socket and self._edge.start_socket:
            self._pen.setColor(self._edge.start_socket.graphics_socket.color_background)

        if not self._edge.end_socket or not self._edge.start_socket:
            painter.setPen(self._pen_dragging)
        else:
            painter.setPen(self._pen if not self.isSelected() else self._pen_selected)

        painter.setBrush(qt.Qt.NoBrush)
        painter.drawPath(self.path())

    def set_source(self, x: int, y: int):
        self._source_position = [x, y]

    def set_destination(self, x: int, y: int):
        self._destination_position = [x, y]

    def intersects_with(self, pt1: qt.QPointF, pt2: qt.QPointF) -> bool:
        cut_path = qt.QPainterPath(pt1)
        cut_path.lineTo(pt2)
        path = self._calculate_path()
        return cut_path.intersects(path)

    def _setup_ui(self):
        """
        Internal function that setup graphics edge settings.
        """

        self.setFlag(qt.QGraphicsItem.ItemIsSelectable)
        self.setZValue(-1)

    @decorators.abstractmethod
    def _calculate_path(self) -> qt.QPainterPath:
        """
        Internal function that calculates the edge path.
        Must be override in derived classes.

        :return: edge path.
        :rtype: qt.QPainterPath
        """

        raise NotImplementedError


class GraphicsEdgeDirect(GraphicsEdge):

    @override
    def _calculate_path(self) -> qt.QPainterPath:
        path = qt.QPainterPath(qt.QPointF(*self._source_position))
        path.lineTo(*self._destination_position)
        return path


class GraphicsEdgeBezier(GraphicsEdge):
    @override
    def _calculate_path(self) -> qt.QPainterPath:
        distance = (self._destination_position[0] - self._source_position[0]) * 0.5
        if self._source_position[0] > self._destination_position[0]:
            distance *= -1
        ctl_point1 = [self._source_position[0] + distance, self._source_position[1]]
        ctl_point2 = [self._destination_position[0] - distance, self._destination_position[1]]

        path = qt.QPainterPath(qt.QPointF(*self._source_position))
        path.cubicTo(qt.QPointF(*ctl_point1), qt.QPointF(*ctl_point2), qt.QPointF(*self._destination_position))

        return path


class GraphicsEdgeSquare(GraphicsEdge):

    HANDLE_WEIGHT = 0.5

    @override
    def _calculate_path(self) -> qt.QPainterPath:
        mid_x = self._source_position[0] + (
                (self._destination_position[0] - self._source_position[0]) * self.HANDLE_WEIGHT)

        path = qt.QPainterPath(qt.QPointF(*self._source_position))
        path.lineTo(mid_x, self._source_position[1])
        path.lineTo(mid_x, self._destination_position[1])
        path.lineTo(*self._destination_position)

        return path
