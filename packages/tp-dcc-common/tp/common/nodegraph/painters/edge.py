from __future__ import annotations

import math
import typing

from tp.common.qt import api as qt
from tp.common.nodegraph.core import consts

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.graphics.edge import GraphicsEdge
    from tp.common.nodegraph.graphics.slicer import Slicer, FreehandSlicer


def draw_default_edge(
        edge_view: GraphicsEdge, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
        widget: qt.QWidget | None = None):

    if not edge_view.edge.end_socket or not edge_view.edge.start_socket:
        draw_realtime_edge(edge_view, painter, option, widget=widget)
        return

    painter.save()

    edge_view.update_path()

    start = edge_view.path().pointAtPercent(0.0)
    end = edge_view.path().pointAtPercent(1.0)

    linear_gradient = qt.QLinearGradient(start.x(), start.y(), end.x(), end.y())
    start_color = qt.QColor(*edge_view.color)
    end_color = None

    pen_style = edge_view.style
    pen_width = edge_view.thickness
    if edge_view.ready_to_slice:
        start_color = qt.QColor(155, 0, 0, 255)
        pen_style = consts.EDGE_DOTTED_STYLE
        pen_width = 1.5
    elif edge_view.isSelected():
        end_color = start_color
    elif edge_view.active:
        start_color = start_color.lighter(125)
        if pen_style == qt.Qt.DashDotDotLine:
            pen_width += 1
        else:
            pen_width += 0.35
    elif edge_view.highlighted:
        start_color = start_color.lighter(225)
        pen_style = consts.EDGE_DEFAULT_STYLE
    else:
        if edge_view.edge.start_socket and edge_view.edge.end_socket:
            start_color = edge_view.edge.start_socket.graphics_socket.color_background
            end_color = edge_view.edge.end_socket.graphics_socket.color_background

    end_color = end_color or start_color

    linear_gradient.setColorAt(0.0, start_color)
    linear_gradient.setColorAt(1.0, end_color)
    gradient_brush = qt.QBrush(linear_gradient)

    pen = qt.QPen(gradient_brush, pen_width)
    pen.setStyle(pen_style)
    pen.setCapStyle(qt.Qt.RoundCap)
    painter.setPen(pen)
    painter.setRenderHint(painter.Antialiasing, True)
    painter.drawPath(edge_view.path())

    if edge_view.edge.start_socket and edge_view.edge.end_socket:
        center_x = edge_view.path().pointAtPercent(0.5).x()
        center_y = edge_view.path().pointAtPercent(0.5).y()
        loc_point = edge_view.path().pointAtPercent(0.51)
        target_point = edge_view.path().pointAtPercent(0.49)

        distance = math.hypot(target_point.x() - center_x, target_point.y() - center_y)
        if distance < 0.5:
            painter.restore()
            return
        # color.setAlpha(255)
        # painter.setBrush(QBrush(color.darker(130)))
        pen_width = 0.6
        if distance < 1.0:
            pen_width *= (1.0 + distance)
        # painter.setPen(QPen(color, pen_width))
        painter.setPen(qt.QPen(gradient_brush, pen_width))
        painter.setBrush(gradient_brush)
        transform = qt.QTransform()
        transform.translate(center_x, center_y)
        radians = math.atan2(target_point.y() - loc_point.y(), target_point.x() - loc_point.x())
        degrees = math.degrees(radians) - 90
        transform.rotate(degrees)
        if distance < 1.0:
            transform.scale(distance, distance)
        painter.drawPolygon(transform.map(edge_view.arrow))

    # pen = qt.QPen(qt.QColor(*edge_view.color), edge_view.thickness)
    # pen_selected = qt.QPen(qt.QColor("#00ff00"))
    # pen_dragging = qt.QPen(qt.QColor(*edge_view.color))
    # pen_dragging.setStyle(qt.Qt.DashLine)
    # if edge_view.edge.end_socket and edge_view.edge.start_socket:
    #     pen.setColor(edge_view.edge.start_socket.graphics_socket.color_background)
    # if not edge_view.edge.end_socket or not edge_view.edge.start_socket:
    #     painter.setPen(pen_dragging)
    # else:
    #     painter.setPen(pen if not edge_view.isSelected() else pen_selected)
    #
    # painter.setBrush(qt.Qt.NoBrush)
    # painter.drawPath(edge_view.path())

    painter.restore()


def draw_realtime_edge(
        edge_view: GraphicsEdge, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
        widget: qt.QWidget | None = None):

    edge_view.update_path()

    painter.save()

    color = qt.QColor(*edge_view.color)
    pen_style = consts.EDGE_DASHED_STYLE
    pen_width = edge_view.thickness

    if edge_view.edge.start_socket:
        color = edge_view.edge.start_socket.graphics_socket.color_background
    elif edge_view.edge.end_socket:
        color = edge_view.edge.end_socket.graphics_socket.color_background

    pen = qt.QPen(color, pen_width)
    pen.setStyle(pen_style)
    pen.setCapStyle(qt.Qt.RoundCap)
    painter.setPen(pen)
    painter.setRenderHint(painter.Antialiasing, True)
    painter.drawPath(edge_view.path())

    center_point = edge_view.path().pointAtPercent(0.5)
    center_x = center_point.x()
    center_y = center_point.y()
    start_point = edge_view.path().pointAtPercent(0.0)
    loc_point = edge_view.path().pointAtPercent(0.9)
    target_point = edge_view.path().pointAtPercent(1.0)

    distance = math.hypot(target_point.x() - center_x, target_point.y() - center_y)
    if distance < 0.05:
        painter.restore()
        return

    start_circle_size = 5.0
    half_start_size = start_circle_size / 2
    start_circle_rect = qt.QRectF(
        start_point.x() - half_start_size, start_point.y() - half_start_size, start_circle_size, start_circle_size)
    painter.setBrush(color)
    painter.setPen(qt.Qt.NoPen)
    painter.drawEllipse(start_circle_rect)

    end_circle_size = 8.0
    half_end_circle = end_circle_size / 2
    end_circle_rect = qt.QRectF(
        target_point.x() - half_end_circle, target_point.y() - half_end_circle, end_circle_size, end_circle_size)
    painter.setBrush(color)
    painter.setPen(qt.QPen(color.darker(130), pen_width))
    painter.drawEllipse(end_circle_rect)

    color.setAlpha(255)
    painter.setBrush(color.darker(200))
    pen_width = 0.6
    if distance < 1.0:
        pen_width *= 1.0 + distance
    painter.setPen(qt.QPen(color, pen_width))
    transform = qt.QTransform()
    transform.translate(center_point.x(), center_point.y())
    radians = math.atan2(center_point.y() - loc_point.y(), center_point.x() - loc_point.x())
    degrees = math.degrees(radians) - 90
    transform.rotate(degrees)
    scale = 1.0
    if distance < 20.0:
        scale = distance / 20.0
    transform.scale(scale, scale)
    painter.drawPolygon(transform.map(edge_view.arrow))

    painter.restore()


def draw_slicer_edge(
        slicer_view: Slicer, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
        widget: qt.QWidget | None = None):
    """
    Draws slicer edge.

    :param Slicer slicer_view: slicer view
    :param qt.QPainter painter: painter used.
    :param qt.QStyleOptionGraphicsItem option: style option graphics item instance.
    :param qt.QWidget or None widget: optional widget.
    """

    painter.save()

    color = qt.QColor(*consts.EDGE_SLICER_COLOR)
    p1 = slicer_view.path().pointAtPercent(0)
    p2 = slicer_view.path().pointAtPercent(1)
    size = 6.0
    offset = size / 2

    painter.setRenderHint(painter.Antialiasing, 2)
    font = painter.font()
    font.setPointSize(12)
    painter.setFont(font)
    text = 'slice'
    text_x = painter.fontMetrics().width(text) / 2
    text_y = painter.fontMetrics().height() / 1.5
    text_pos = qt.QPointF(p1.x() - text_x, p1.y() - text_y)
    text_color = qt.QColor(*consts.EDGE_SLICER_COLOR)
    text_color.setAlpha(80)
    painter.setPen(qt.QPen(text_color, 1.5, qt.Qt.SolidLine))
    painter.drawText(text_pos, text)
    painter.setPen(qt.QPen(color, 1.5, qt.Qt.DashLine))
    painter.drawPath(slicer_view.path())
    painter.setPen(qt.QPen(color, 1.5, qt.Qt.SolidLine))
    painter.setBrush(color)
    rect = qt.QRectF(p1.x() - offset, p1.y() - offset, size, size)
    painter.drawEllipse(rect)
    rect = qt.QRectF(p2.x() - offset, p2.y() - offset, size, size)
    painter.drawEllipse(rect)

    painter.restore()


def draw_freehand_slicer_edge(
        slicer_view: FreehandSlicer, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
        widget: qt.QWidget | None = None):
    """
    Draws freehand slicer edge.

    :param FreehandSlicer slicer_view: freehand slicer view
    :param qt.QPainter painter: painter used.
    :param qt.QStyleOptionGraphicsItem option: style option graphics item instance.
    :param qt.QWidget or None widget: optional widget.
    """

    painter.save()

    color = qt.QColor(*consts.EDGE_SLICER_COLOR)
    p1 = slicer_view.point(0)
    p2 = slicer_view.point(-1)
    size = 6.0
    offset = size / 2

    painter.setRenderHint(painter.Antialiasing, 2)
    font = painter.font()
    font.setPointSize(12)
    painter.setFont(font)
    text = 'slice'
    text_x = painter.fontMetrics().width(text) / 2
    text_y = painter.fontMetrics().height() / 1.5
    text_pos = qt.QPointF(p1.x() - text_x, p1.y() - text_y)
    text_color = qt.QColor(*consts.EDGE_SLICER_COLOR)
    text_color.setAlpha(80)
    painter.setPen(qt.QPen(text_color, 1.5, qt.Qt.SolidLine))
    painter.drawText(text_pos, text)
    painter.setBrush(qt.Qt.NoBrush)
    pen = qt.QPen(color, 1.5, qt.Qt.DashLine)
    painter.setPen(pen)
    poly = qt.QPolygonF(slicer_view.points())
    painter.drawPolyline(poly)
    painter.setPen(qt.QPen(color, 1.5, qt.Qt.SolidLine))
    painter.setBrush(color)
    rect = qt.QRectF(p1.x() - offset, p1.y() - offset, size, size)
    painter.drawEllipse(rect)
    rect = qt.QRectF(p2.x() - offset, p2.y() - offset, size, size)
    painter.drawEllipse(rect)

    painter.restore()
