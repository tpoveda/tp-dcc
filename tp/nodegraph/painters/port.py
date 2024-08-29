from __future__ import annotations

import typing
from dataclasses import dataclass

from Qt.QtCore import Qt, QPointF, QRectF
from Qt.QtGui import QColor, QPen, QPainter, QPolygonF, QTransform


if typing.TYPE_CHECKING:
    pass


@dataclass
class PortPaintData:
    """
    Data class that stores information used to paint a port.
    """

    port_type: int
    color: tuple[int, int, int, int]
    border_color: tuple[int, int, int, int]
    multi_connection: bool
    connected: bool
    hovered: bool
    locked: bool


def paint_triangle_port(painter: QPainter, rect: QRectF, info: PortPaintData):
    """
    Function that paints a triangle port.

    :param painter: QPainter used to paint.
    :param rect: QRectF used to paint the port.
    :param info: PortPaintData used to paint the port.
    """

    painter.save()
    try:
        size = int(rect.height() / 2)
        triangle = QPolygonF()
        triangle.append(QPointF(-size, size))
        triangle.append(QPointF(0.0, -size))
        triangle.append(QPointF(size, size))
        transform = QTransform()
        transform.translate(rect.center().x(), rect.center().y())
        port_poly = transform.map(triangle)

        if info.hovered:
            color = QColor(14, 45, 59)
            border_color = QColor(136, 255, 35)
        elif info.connected:
            color = QColor(195, 60, 60)
            border_color = QColor(200, 130, 70)
        else:
            color = QColor(*info.color)
            border_color = QColor(*info.border_color)
        pen = QPen(border_color, 1.8)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(color)
        painter.drawPolygon(port_poly)
    finally:
        painter.restore()


def paint_square_port(painter: QPainter, rect: QRectF, info: PortPaintData):
    """
    Function that paints a square port.

    :param painter: QPainter used to paint.
    :param rect: QRectF used to paint the port.
    :param info: PortPaintData used to paint the port.
    """

    painter.save()
    try:
        if info.hovered:
            color = QColor(14, 45, 59)
            border_color = QColor(136, 255, 35, 255)
        elif info.connected:
            color = QColor(195, 60, 60)
            border_color = QColor(200, 130, 70)
        else:
            color = QColor(*info.color)
            border_color = QColor(*info.border_color)
        pen = QPen(border_color, 1.8)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        painter.setBrush(color)
        painter.drawRect(rect)
    finally:
        painter.restore()
