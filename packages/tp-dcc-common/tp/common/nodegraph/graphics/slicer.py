from __future__ import annotations

from typing import Union, Any

from overrides import override

from tp.common.qt import api as qt
from tp.common.nodegraph.core import consts
from tp.common.nodegraph.graphics import edge
from tp.common.nodegraph.painters import edge as edge_painters


class Slicer(qt.QGraphicsPathItem):

    class Signals(qt.QObject):
        visibilityChanged = qt.Signal(bool)

    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self.signals = Slicer.Signals()
        self.setZValue(consts.WIDGET_Z_VALUE + 2)

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:
        edge_painters.draw_slicer_edge(self, painter, option, widget)

    def itemChange(self, change: qt.QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        if change == self.ItemVisibleChange:
            self.signals.visibilityChanged.emit(bool(value))
        return super().itemChange(change, value)

    def draw_path(self, p1: qt.QPointF, p2: qt.QPointF):
        """
        Sets path between two given points.

        :param qt.QPoint p1: start point.
        :param qt.QPoint p2: end point.
        """

        path = qt.QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        self.setPath(path)

    def intersected_edges(self) -> list[edge.GraphicsEdge]:
        """
        Returns list of intersected edge graphics.

        :return: list of intersected edge graphics.
        :rtype: list[edge.GraphicsEdge]
        """

        return [item for item in self.scene().items(self.path()) if isinstance(item, edge.GraphicsEdge)]

    def cut(self) -> bool:
        """
        Cuts intersected edges by this slicer.

        :return: True if one or multiple edges were intersected; False otherwise.
        :rtype: bool
        """

        cut_result = False
        for item in self.scene().items(self.path()):
            if isinstance(item, edge.GraphicsEdge):
                item.edge.remove()
                cut_result = True

        return cut_result


class FreehandSlicer(Slicer):
    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._line_points: list[qt.QPointF] = []

    @override
    def boundingRect(self) -> qt.QRectF:
        return self.shape().boundingRect()

    @override
    def shape(self) -> qt.QPainterPath:
        if len(self._line_points) > 1:
            path = qt.QPainterPath(self._line_points[0])
            for pt in self._line_points[1:]:
                path.lineTo(pt)
        else:
            path = qt.QPainterPath(qt.QPointF(0.0, 0.0))
            path.lineTo(qt.QPointF(1.0, 1.0))
        return path

    @override
    def paint(
            self, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
            widget: Union[qt.QWidget, None] = ...) -> None:
        edge_painters.draw_freehand_slicer_edge(self, painter, option, widget)

    @override
    def intersected_edges(self) -> list[edge.GraphicsEdge]:
        """
        Returns list of intersected edge graphics.

        :return: list of intersected edge graphics.
        :rtype: list[edge.GraphicsEdge]
        """

        found_edges: list[edge.GraphicsEdge] = []
        for i in range(self.num_points() - 1):
            pt1 = self.point(i)
            pt2 = self.point(i + 1)
            # TODO: Should be optimized as gets slow with large scenes.
            for scene_edge in self.scene().graph.edges[:]:
                if scene_edge.graphics_edge.intersects_with(pt1, pt2):
                    found_edges.append(scene_edge.graphics_edge)

        return found_edges

    @override
    def cut(self) -> bool:
        edges_to_remove = self.intersected_edges()
        if not edges_to_remove:
            return False
        for edge_to_remove in edges_to_remove:
            edge_to_remove.edge.remove()

        return True

    def points(self) -> list[qt.QPointF]:
        """
        Returns list of points.

        :return: list of points.
        :rtype: list[qt.QPointF]
        """

        return self._line_points

    def num_points(self) -> int:
        """
        Returns the total amount of points.

        :return: points count.
        :rtype: int
        """

        return len(self._line_points)

    def add_point(self, point: qt.QPointF):
        """
        Adds new position to the cutline.

        :param qt.QPointF point: position.
        """

        self._line_points.append(point)
        self.update()

    def point(self, index: int) -> qt.QPointF:
        """
        Returns point at given index.

        :param int index: point index.
        :return: found point.
        :rtype: qt.QPointF
        """

        try:
            return self._line_points[index]
        except IndexError:
            return qt.QPointF(0.0, 0.0)

    def reset(self):
        """
        Resets cutline.
        """

        self._line_points.clear()
        self.update()
