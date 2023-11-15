from __future__ import annotations

import typing
from typing import Union

from overrides import override

from tp.common.qt import api as qt
from tp.common.python import decorators
from tp.common.nodegraph.core import consts
from tp.common.nodegraph.painters import edge as edge_painters

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.edge import Edge


class GraphicsEdge(qt.QGraphicsPathItem):

    MAX_WIDTH = 6.0
    MIN_WIDTH = 2.0
    WIDTH = 2.0

    def __init__(self, edge: Edge, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._edge = edge
        self._source_position = [0, 0]
        self._destination_position = [200, 100]

        self._color = consts.EDGE_COLOR
        self._style = consts.EDGE_DEFAULT_STYLE
        self._thickness = consts.EDGE_THICKNESS
        self._active = False
        self._highlight = False
        self._ready_to_slice = False
        self._pen = qt.QPen(qt.QColor(*self._color), self._thickness, qt.Qt.SolidLine, qt.Qt.RoundCap, qt.Qt.RoundJoin)

        size = 4.0
        self._arrow = qt.QPolygonF()
        self._arrow.append(qt.QPointF(-size, size))
        self._arrow.append(qt.QPointF(0.0, -size * 1.5))
        self._arrow.append(qt.QPointF(size, size))

        self._setup_ui()

    @property
    def edge(self) -> Edge:
        return self._edge

    @property
    def color(self) -> tuple[int, int, int, int]:
        return self._color

    @color.setter
    def color(self, value: tuple[int, int, int, int]):
        self._color = value

    @property
    def thickness(self) -> float:
        return self._thickness

    @thickness.setter
    def thickness(self, value: float):
        self._thickness = value

    @property
    def style(self) -> qt.Qt.PenStyle:
        return self._style

    @style.setter
    def style(self, value: qt.Qt.PenStyle):
        self._style = value

    @property
    def ready_to_slice(self) -> bool:
        return self._ready_to_slice

    @ready_to_slice.setter
    def ready_to_slice(self, flag: bool):
        if flag != self._ready_to_slice:
            self._ready_to_slice = flag
            self.update()

    @property
    def active(self) -> bool:
        return self._active

    @property
    def highlighted(self) -> bool:
        return self._highlight

    @property
    def arrow(self) -> qt.QPolygonF:
        return self._arrow

    @override
    def shape(self) -> qt.QPainterPath:
        return self._calculate_path()

    @override
    def boundingRect(self) -> qt.QRectF:
        return self.shape().boundingRect()

    @override
    def hoverEnterEvent(self, event: qt.QGraphicsSceneHoverEvent) -> None:
        self.activate()

    def hoverLeaveEvent(self, event: qt.QGraphicsSceneHoverEvent) -> None:
        self.reset()

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:

        edge_painters.draw_default_edge(self, painter, option, widget=widget)

    def set_source(self, x: int, y: int):
        """
        Sets source/start point.

        :param int x: X start point coordinate.
        :param int y: Y start point coordinate.
        """

        self._source_position = [x, y]

    def set_destination(self, x: int, y: int):
        """
        Sets destination/end point.

        :param int x: X end point coordinate.
        :param int y: Y end point coordinate.
        """

        self._destination_position = [x, y]

    def intersects_with(self, pt1: qt.QPointF, pt2: qt.QPointF) -> bool:
        """
        Returns whether edge path intersects with path formed by given start and end points.

        :param qt.QPointF pt1: start point.
        :param qt.QPointF pt2: end point.
        :return: True if path intersects with path both points belongs to; False otherwise.
        :rtype: bool
        """

        cut_path = qt.QPainterPath(pt1)
        cut_path.lineTo(pt2)
        path = self._calculate_path()
        return cut_path.intersects(path)

    def update_path(self):
        """
        Updates internal path.
        """

        self.setPath(self._calculate_path())

    def activate(self):
        """
        Activates edge.
        """

        self._active = True
        self.setPen(qt.QPen(qt.QColor(*self.color).lighter(125), self._thickness, self._style))

    def highlight(self):
        """
        Highlights current connector.
        """

        self._highlight = True
        self.setPen(qt.QPen(qt.QColor(*self.color).lighter(225), self._thickness, self._style))

    def reset(self):
        """
        Resets connector.
        """

        self._active = False
        self._highlight = False
        self.setPen(qt.QPen(qt.QColor(*self._color), self._thickness, self._style))

    def _setup_ui(self):
        """
        Internal function that setup graphics edge settings.
        """

        self.setZValue(consts.EDGE_Z_VALUE)
        self.setFlag(qt.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCacheMode(consts.ITEM_CACHE_MODE)

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
