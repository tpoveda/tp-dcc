from __future__ import annotations

import math
import typing
from typing import Any

from Qt.QtCore import Qt, Signal, QObject, QPointF, QRectF
from Qt.QtWidgets import (
    QWidget,
    QGraphicsItem,
    QGraphicsPathItem,
    QStyleOptionGraphicsItem,
)
from Qt.QtGui import (
    QColor,
    QPen,
    QPainter,
    QPainterPath,
    QPolygonF,
    QTransform,
)

from . import uiconsts
from .connector import ConnectorView

if typing.TYPE_CHECKING:
    from ..views.scene import NodeGraphScene


class Slicer(QGraphicsPathItem):
    """
    Base class for all slicers.
    """

    class Signals(QObject):
        """
        Class that defines signals for the slicer.
        """

        visibilityChanged = Signal(bool)

    def __init__(self, parent: QGraphicsItem | None = None):
        super().__init__(parent=parent)

        self.signals = Slicer.Signals()
        self.setZValue(uiconsts.Z_VALUE_NODE_WIDGET + 2)

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the slicer.

        :param painter: painter to paint the slicer.
        :param option: style option for the slicer.
        :param widget: widget to paint the slicer.
        """

        painter.save()
        try:
            color = QColor(*uiconsts.CONNECTOR_SLICER_COLOR)
            p1 = self.path().pointAtPercent(0)
            p2 = self.path().pointAtPercent(1)
            size = 6.0
            offset = size / 2
            arrow_size = 4.0

            painter.setRenderHint(QPainter.Antialiasing, True)
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            text = "slice"
            text_x = painter.fontMetrics().horizontalAdvance(text) / 2
            text_y = painter.fontMetrics().height() / 1.5
            text_pos = QPointF(p1.x() - text_x, p1.y() - text_y)
            text_color = QColor(*uiconsts.CONNECTOR_SLICER_COLOR)
            text_color.setAlpha(80)
            painter.setPen(
                QPen(text_color, uiconsts.CONNECTOR_SLICER_WIDTH, Qt.SolidLine)
            )
            painter.drawText(text_pos, text)
            painter.setPen(QPen(color, uiconsts.CONNECTOR_SLICER_WIDTH, Qt.DashLine))
            painter.drawPath(self.path())
            pen = QPen(color, uiconsts.CONNECTOR_SLICER_WIDTH, Qt.SolidLine)
            pen.setCapStyle(Qt.RoundCap)
            pen.setJoinStyle(Qt.MiterJoin)
            painter.setPen(pen)
            painter.setBrush(color)
            rect = QRectF(p1.x() - offset, p1.y() - offset, size, size)
            painter.drawEllipse(rect)
            rect = QRectF(p2.x() - offset, p2.y() - offset, size, size)
            painter.drawEllipse(rect)

            arrow = QPolygonF()
            arrow.append(QPointF(-arrow_size, arrow_size))
            arrow.append(QPointF(0.0, -arrow_size * 0.9))
            arrow.append(QPointF(arrow_size, arrow_size))
            transform = QTransform()
            transform.translate(p2.x(), p2.y())
            radians = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
            degrees = math.degrees(radians) - 90
            transform.rotate(degrees)
            painter.drawPolygon(transform.map(arrow))
        finally:
            painter.restore()

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: Any) -> Any:
        """
        Called when the item changes.

        :param change: type of change.
        :param value: value of the change.
        :return: value of the change.
        """

        if change == QGraphicsItem.ItemVisibleChange:
            self.signals.visibilityChanged.emit(bool(value))

        return super().itemChange(change, value)

    def draw_path(self, p1: QPointF, p2: QPointF):
        """
        Draw the path between two points.

        :param p1: start point.
        :param p2: end point.
        """

        path = QPainterPath()
        path.moveTo(p1)
        path.lineTo(p2)
        self.setPath(path)

    def intersected_connectors(self) -> list[ConnectorView]:
        """
        Returns a list of connectors that intersect the slicer.

        :return: list of connectors that intersect the slicer.
        """

        return [
            item
            for item in self.scene().items(self.path())
            if isinstance(item, ConnectorView)
        ]

    def cut(self) -> bool:
        """
        Cut the connectors that intersect the slicer.

        :return: whether the connectors were cut.
        """

        cut_result = False
        for item in self.intersected_connectors():
            print("Removing")
            # item.connector.remove()
            cut_result = True

        return cut_result


class FreehandSlicer(Slicer):
    def __init__(self, parent: QGraphicsItem | None = None):
        super().__init__(parent=parent)

        self._line_points: list[QPointF] = []

    def boundingRect(self) -> QRectF:
        """
        Returns the bounding rectangle of the slicer.

        :return: bounding rectangle of the slicer.
        """

        return self.shape().boundingRect()

    def shape(self) -> QPainterPath:
        """
        Returns the shape of the slicer.

        :return: shape of the slicer.
        """

        if len(self._line_points) > 1:
            path = QPainterPath(self._line_points[0])
            for pt in self._line_points[1:]:
                path.lineTo(pt)
        else:
            path = QPainterPath(QPointF(0.0, 0.0))
            path.lineTo(QPointF(1.0, 1.0))

        return path

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: QWidget | None = None,
    ):
        """
        Paint the slicer.

        :param painter: painter to paint the slicer.
        :param option: style option for the slicer.
        :param widget: widget to paint the slicer.
        """

        painter.save()
        try:
            color = QColor(*uiconsts.CONNECTOR_SLICER_COLOR)
            p1 = self.point(0)
            p2 = self.point(-1)
            size = 6.0
            offset = size / 2

            painter.setRenderHint(QPainter.Antialiasing, True)
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            text = "slice"
            text_x = painter.fontMetrics().horizontalAdvance(text) / 2
            text_y = painter.fontMetrics().height() / 1.5
            text_pos = QPointF(p1.x() - text_x, p1.y() - text_y)
            text_color = QColor(*uiconsts.CONNECTOR_SLICER_COLOR)
            text_color.setAlpha(80)
            painter.setPen(QPen(text_color, 1.5, Qt.SolidLine))
            painter.drawText(text_pos, text)
            painter.setBrush(Qt.NoBrush)
            pen = QPen(color, 1.5, Qt.DashLine)
            painter.setPen(pen)
            poly = QPolygonF(self.points())
            painter.drawPolyline(poly)
            painter.setPen(QPen(color, 1.5, Qt.SolidLine))
            painter.setBrush(color)
            rect = QRectF(p1.x() - offset, p1.y() - offset, size, size)
            painter.drawEllipse(rect)
            rect = QRectF(p2.x() - offset, p2.y() - offset, size, size)
            painter.drawEllipse(rect)
        finally:
            painter.restore()

    def intersected_connectors(self) -> list[ConnectorView]:
        """
        Returns a list of connectors that intersect the slicer.

        :return: list of connectors that intersect the slicer.
        """

        found_connectors: list[ConnectorView] = []
        for i in range(self.num_points() - 1):
            pt1 = self.point(i)
            pt2 = self.point(i + 1)
            # TODO: Should be optimized as gets slow with large scenes.
            # noinspection PyTypeChecker
            scene: NodeGraphScene = self.scene()
            for connector_view in scene.viewer().connectors():
                if connector_view.intersects_with(pt1, pt2):
                    found_connectors.append(connector_view)

        return found_connectors

    def cut(self) -> bool:
        """
        Cut the connectors that intersect the slicer.

        :return: whether the connectors were cut.
        """

        connectors_to_remove = self.intersected_connectors()
        if not connectors_to_remove:
            return False

        for connector_to_remove in connectors_to_remove:
            pass
            # connector_to_remove.delete()

        return True

    def points(self) -> list[QPointF]:
        """
        Returns the points of the slicer.

        :return: points of the slicer.
        """

        return self._line_points

    def num_points(self) -> int:
        """
        Returns the number of points of the slicer.

        :return: number of points of the slicer.
        """

        return len(self._line_points)

    def add_point(self, point: QPointF):
        """
        Add a point to the slicer.

        :param point: point to add.
        """

        self._line_points.append(point)
        self.update()

    def point(self, index: int) -> QPointF:
        """
        Returns the point at the given index.

        :param index: index of the point.
        :return: point at the given index.
        """

        try:
            return self._line_points[index]
        except IndexError:
            return QPointF(0.0, 0.0)

    def reset(self):
        """
        Reset the slicer.
        """

        self._line_points.clear()
        self.update()
