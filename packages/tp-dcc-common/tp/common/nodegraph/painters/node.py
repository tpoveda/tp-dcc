from __future__ import annotations

import typing

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.graphics.node import GraphicsNode


def node_painter(
        node_view: GraphicsNode, painter: qt.QPainter, option: qt.QStyleOptionGraphicsItem,
        widget: qt.QWidget | None = None, debug_mode: bool = False):

    painter.save()

    background_border = 0.5
    border_width = 0.4 if not node_view.isSelected() else 1.2
    background_border *= border_width
    radius = 3
    title_color = qt.QColor(*node_view.header_color)
    background_color = qt.QColor(*node_view.color)
    border_color = qt.QColor(*node_view.border_color)

    if node_view.isSelected():
        background_color = background_color.lighter(150)
        title_color = title_color.lighter(150)
    # if node_view.get_is_temporal():
    #     background_color.setAlpha(50)
    #     background_color = background_color.lighter(50)

    show_details = node_view.viewer().show_details()

    # rect used for both background and border
    rect = qt.QRectF(
        background_border, background_border,
        node_view.width - (background_border * 2), node_view.height - (background_border * 2))
    left = rect.left()
    top = rect.top()

    background_path = qt.QPainterPath()

    painter.setBrush(background_color)
    painter.setPen(qt.Qt.NoPen)
    painter.drawRoundedRect(rect, radius, radius) if show_details else painter.drawRect(rect)

    title_height = node_view.title_height
    label_rect = qt.QRectF(
        background_border, background_border,
        node_view.width - (background_border * 2), node_view.title_height)
    border_path = qt.QPainterPath()
    border_path.setFillRule(qt.Qt.WindingFill)
    if show_details:
        border_path.addRoundedRect(label_rect, radius, radius)
        square_size = node_view.title_height / 2
        # Fill bottom rounded borders
        border_path.addRect(qt.QRectF(left, top + title_height - square_size, square_size, square_size))
        border_path.addRect(qt.QRectF(
            (left + node_view.width) - square_size, top + title_height - square_size,
            square_size - (background_border * 2), square_size))
    else:
        border_path.addRect(label_rect)
    painter.setBrush(title_color)
    painter.fillPath(border_path, painter.brush())

    # if not node_view.is_valid():
    # 	pen = QPen(consts.INVALID_NODE_PEN_COLOR, 1.5, Qt.DashLine)
    # else:
    # 	pen = QPen(border_color, border_width)
    pen = qt.QPen(border_color, border_width)

    pen.setCosmetic(show_details and node_view.viewer().zoom_value() < 0.0)
    background_path.addRoundedRect(rect, radius, radius) if show_details else background_path.addRect(rect)
    painter.setBrush(qt.Qt.NoBrush)
    painter.setPen(pen)

    if debug_mode:
        painter.setPen(qt.QPen(qt.Qt.blue, 0.75))
        painter.drawRect(rect)
        painter.setPen(qt.QPen(qt.Qt.green, 0.75))
        painter.drawRect(label_rect)
    else:
        painter.drawPath(background_path)

    painter.restore()
