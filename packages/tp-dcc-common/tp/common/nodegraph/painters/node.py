#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains node painter functions
"""

from Qt.QtCore import Qt, QPointF, QRectF, QSizeF
from Qt.QtGui import QColor, QPainterPath, QPen, QFontMetrics, QPolygonF, QTransform

from tp.common.nodegraph.core import consts


def node_painter_horizontal(node_view, painter, option, widget, debug_mode=False):
	painter.save()

	background_border = 0.5
	border_width = 0.4 if not node_view.isSelected() else 1.2
	background_border *= border_width
	radius = 3
	title_color = QColor(*node_view.header_color)
	background_color = QColor(*node_view.color)
	border_color = QColor(*node_view.border_color)
	if node_view.isSelected():
		background_color = background_color.lighter(150)
		title_color = title_color.lighter(150)
	# if node_view.get_is_temporal():
	#     background_color.setAlpha(50)
	#     background_color = background_color.lighter(50)

	lod = node_view.viewer().get_lod_value_from_scale()
	show_details = lod < 4

	# rect used for both background and border
	rect = QRectF(
		background_border, background_border,
		node_view.width - (background_border * 2), node_view.height - (background_border * 2))
	left = rect.left()
	top = rect.top()

	background_path = QPainterPath()

	painter.setBrush(background_color)
	painter.setPen(Qt.NoPen)
	painter.drawRoundedRect(rect, radius, radius) if show_details else painter.drawRect(rect)

	title_height = node_view.title_height
	label_rect = QRectF(
		background_border, background_border,
		node_view.width - (background_border * 2), node_view.title_height)
	border_path = QPainterPath()
	border_path.setFillRule(Qt.WindingFill)
	if show_details:
		border_path.addRoundedRect(label_rect, radius, radius)
		square_size = node_view.title_height / 2
		# Fill bottom rounded borders
		border_path.addRect(QRectF(left, top + title_height - square_size, square_size, square_size))
		border_path.addRect(QRectF(
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
	pen = QPen(border_color, border_width)

	pen.setCosmetic(show_details and node_view.viewer().get_zoom() < 0.0)
	background_path.addRoundedRect(rect, radius, radius) if show_details else background_path.addRect(rect)
	painter.setBrush(Qt.NoBrush)
	painter.setPen(pen)

	if debug_mode:
		painter.setPen(QPen(Qt.blue, 0.75))
		painter.drawRect(rect)
		painter.setPen(QPen(Qt.green, 0.75))
		painter.drawRect(label_rect)
	else:
		painter.drawPath(background_path)

	painter.restore()


def node_painter_vertical(node_view, painter, option, widget, debug_mode=False):

	painter.save()

	print('Vertical Layout not implemented')

	painter.restore()


def disabled_node_painter(node_view, painter, option, widget):
	painter.save()

	margin = 20
	half_margin = margin / 2
	rect = node_view.boundingRect()
	distance_rect = QRectF(
		rect.left() - half_margin, rect.top() - half_margin, rect.width() + margin, rect.height() + margin)
	pen = QPen(QColor(*node_view.color), 8)
	pen.setCapStyle(Qt.RoundCap)
	painter.setPen(pen)
	painter.drawLine(distance_rect.topLeft(), distance_rect.bottomRight())
	painter.drawLine(distance_rect.topRight(), distance_rect.bottomLeft())

	background_color = QColor(*node_view.color)
	background_color.setAlpha(100)
	bg_margin = -0.5
	half_bg_margin = bg_margin / 2
	background_rect = QRectF(
		distance_rect.left() - half_bg_margin, distance_rect.top() - half_bg_margin,
		distance_rect.width() + bg_margin, distance_rect.height() + bg_margin)
	painter.setPen(QPen(QColor(0, 0, 0, 0)))
	painter.setBrush(background_color)
	painter.drawRoundedRect(background_rect, 5, 5)

	pen = QPen(QColor(155, 0, 0, 255), 0.7)
	painter.setPen(pen)
	painter.drawLine(distance_rect.topLeft(), distance_rect.bottomRight())
	painter.drawLine(distance_rect.topRight(), distance_rect.bottomLeft())

	point_size = 4.0
	half_size = point_size / 2
	point_pos = (
		distance_rect.topLeft(), distance_rect.topRight(), distance_rect.bottomLeft(), distance_rect.bottomRight())
	painter.setBrush(QColor(255, 0, 0, 255))
	for p in point_pos:
		p.setX(p.x() - half_size)
		p.setY(p.y() - half_size)
		point_rect = QRectF(p, QSizeF(point_size, point_size))
		painter.drawEllipse(point_rect)

	disabled_text = node_view.text
	if disabled_text:
		font = painter.font()
		font.setPointSize(10)
		painter.setFont(font)
		font_metrics = QFontMetrics(font)
		font_width = font_metrics.width(disabled_text)
		font_height = font_metrics.height()
		text_width = font_width * 1.25
		text_height = font_height * 2.25
		text_bg_rect = QRectF(
			(rect.width() / 2) - (text_width / 2), (rect.height() / 2) - (text_height / 2), text_width, text_height)
		painter.setPen(QPen(QColor(255, 0, 0), 0.5))
		painter.setBrush(QColor(*node_view.color))
		painter.drawRoundedRect(text_bg_rect, 2, 2)
		text_rect = QRectF(
			(rect.width() / 2) - (font_width / 2),
			(rect.height() / 2) - (font_height / 2),
			text_width * 2, font_height * 2)
		painter.setPen(QPen(QColor(255, 0, 0), 1))
		painter.drawText(text_rect, disabled_text)

	painter.restore()


def input_node_painter_horizontal(node_view, painter, option, widget, debug_mode=False):

	painter.save()

	painter.setBrush(Qt.NoBrush)
	painter.setPen(Qt.NoPen)

	margin = 2.0
	rect = node_view.boundingRect()
	rect = QRectF(rect.left() + margin, rect.top() + margin, rect.width() - (margin * 2), rect.height() - (margin * 2))

	text_rect = node_view.title_item.boundingRect()
	text_rect = QRectF(
	rect.center().x() - (text_rect.width() / 2) - 5,
		rect.center().y() - (text_rect.height() / 2),
		text_rect.width() + 10,
		text_rect.height()
	)

	painter.setBrush(QColor(255, 255, 255, 20))
	painter.drawRoundedRect(rect, 20, 20)

	painter.setBrush(QColor(0, 0, 0, 100))
	painter.drawRoundedRect(text_rect, 3, 3)

	size = int(rect.height() / 4)
	triangle = QPolygonF()
	triangle.append(QPointF(-size, size))
	triangle.append(QPointF(0.0, 0.0))
	triangle.append(QPointF(size, size))

	transform = QTransform()
	transform.translate(rect.width() - (size / 6), rect.center().y())
	transform.rotate(90)
	poly = transform.map(triangle)

	if node_view.selected:
		pen = QPen(QColor(*consts.NODE_SELECTED_BORDER_COLOR), 1.3)
		painter.setBrush(QColor(*consts.NODE_SELECTED_COLOR))
	else:
		pen = QPen(QColor(*node_view.border_color), 1.2)
		painter.setBrush(QColor(0, 0, 0, 50))

	pen.setJoinStyle(Qt.MiterJoin)
	painter.setPen(pen)
	painter.drawPolygon(poly)

	edge_size = 30
	edge_rect = QRectF(
		rect.width() - (size * 1.7), rect.center().y() - (edge_size / 2), 4, edge_size)
	painter.drawRect(edge_rect)

	painter.restore()


def input_node_painter_vertical(node_view, painter, option, widget, debug_mode=False):

	painter.save()

	painter.setBrush(Qt.NoBrush)
	painter.setPen(Qt.NoPen)

	margin = 2.0
	rect = node_view.boundingRect()
	rect = QRectF(rect.left() + margin, rect.top() + margin, rect.width() - (margin * 2), rect.height() - (margin * 2))

	text_rect = node_view.title_item.boundingRect()
	text_rect = QRectF(
		rect.center().x() - (text_rect.width() / 2) - 5,
		rect.top() + margin,
		text_rect.width() + 10,
		text_rect.height()
	)

	painter.setBrush(QColor(255, 255, 255, 20))
	painter.drawRoundedRect(rect, 20, 20)

	painter.setBrush(QColor(0, 0, 0, 100))
	painter.drawRoundedRect(text_rect, 3, 3)

	size = int(rect.height() / 4)
	triangle = QPolygonF()
	triangle.append(QPointF(-size, size))
	triangle.append(QPointF(0.0, 0.0))
	triangle.append(QPointF(size, size))

	transform = QTransform()
	transform.translate(rect.center().x(), rect.bottom() - (size / 3))
	transform.rotate(180)
	poly = transform.map(triangle)

	if node_view.selected:
		pen = QPen(QColor(*consts.NODE_SELECTED_BORDER_COLOR), 1.3)
		painter.setBrush(QColor(*consts.NODE_SELECTED_COLOR))
	else:
		pen = QPen(QColor(*node_view.border_color), 1.2)
		painter.setBrush(QColor(0, 0, 0, 50))

	pen.setJoinStyle(Qt.MiterJoin)
	painter.setPen(pen)
	painter.drawPolygon(poly)

	edge_size = 30
	edge_rect = QRectF(rect.center().x() - (edge_size / 2), rect.bottom() - (size * 1.9), edge_size, 4)
	painter.drawRect(edge_rect)

	painter.restore()


def group_node_painter_horizontal(node_view, painter, option, widget, debug_mode=False):

	painter.save()

	painter.setBrush(Qt.NoBrush)
	painter.setPen(Qt.NoPen)

	margin = 6.0
	rect = node_view.boundingRect()
	rect = QRectF(rect.left() + margin, rect.top() + margin, rect.width() - (margin * 2), rect.height() - (margin * 2))

	offset = 3.0
	rect_1 = QRectF(rect.x() + (offset / 2), rect.y() + offset + 2.0, rect.width(), rect.height())
	rect_2 = QRectF(rect.x() - offset, rect.y() - offset, rect.width(), rect.height())
	poly = QPolygonF()
	poly.append(rect_1.topRight())
	poly.append(rect_2.topRight())
	poly.append(rect_2.bottomLeft())
	poly.append(rect_1.bottomLeft())

	painter.setBrush(QColor(*node_view.color).darker(180))
	painter.drawRect(rect_1)
	painter.drawPolygon(poly)

	painter.setBrush(QColor(*node_view.color))
	painter.drawRect(rect_2)

	if node_view.selected:
		border_color = QColor(*consts.NODE_SELECTED_BORDER_COLOR)
		painter.setBrush(QColor(*consts.NODE_SELECTED_COLOR))
		painter.drawRect(rect_2)
	else:
		border_color = QColor(*node_view.border_color)

	padding = 2.0, 2.0
	text_rect = node_view.title_item.boundingRect()
	text_rect = QRectF(
		rect_2.left() + padding[0], rect_2.top() + padding[1],
		rect.right() - (padding[0] * 2) - margin, text_rect.height() - (padding[1] * 2))

	if node_view.selected:
		painter.setBrush(QColor(*consts.NODE_SELECTED_COLOR))
	else:
		painter.setBrush(QColor(0, 0, 0, 80))
	painter.setPen(Qt.NoPen)
	painter.drawRect(text_rect)

	# draw the outlines.
	pen = QPen(border_color.darker(120), 0.8)
	pen.setJoinStyle(Qt.RoundJoin)
	pen.setCapStyle(Qt.RoundCap)
	painter.setBrush(Qt.NoBrush)
	painter.setPen(pen)
	painter.drawLines(
		[rect_1.topRight(), rect_2.topRight(), rect_1.topRight(), rect_1.bottomRight(),
		 rect_1.bottomRight(), rect_1.bottomLeft(), rect_1.bottomLeft(), rect_2.bottomLeft()])
	painter.drawLine(rect_1.bottomRight(), rect_2.bottomRight())

	pen = QPen(border_color, 0.8)
	pen.setJoinStyle(Qt.MiterJoin)
	pen.setCapStyle(Qt.RoundCap)
	painter.setPen(pen)
	painter.drawRect(rect_2)

	painter.restore()


def group_node_painter_vertical(node_view, painter, option, widget, debug_mode=False):

	painter.save()

	painter.setBrush(Qt.NoBrush)
	painter.setPen(Qt.NoPen)

	margin = 6.0
	rect = node_view.boundingRect()
	rect = QRectF(rect.left() + margin, rect.top() + margin, rect.width() - (margin * 2), rect.height() - (margin * 2))

	offset = 3.0
	rect_1 = QRectF(rect.x() + offset, rect.y() + (offset / 2), rect.width(), rect.height())
	rect_2 = QRectF(rect.x() - offset, rect.y() - offset, rect.width(), rect.height())
	poly = QPolygonF()
	poly.append(rect_1.topRight())
	poly.append(rect_2.topRight())
	poly.append(rect_2.bottomLeft())
	poly.append(rect_1.bottomLeft())

	painter.setBrush(QColor(*node_view.color).dark(180))
	painter.drawRect(rect_1)
	painter.drawPolygon(poly)
	painter.setBrush(QColor(*node_view.color))
	painter.drawRect(rect_2)

	if node_view.selected:
		border_color = QColor(*consts.NODE_SELECTED_BORDER_COLOR)
		painter.setBrush(QColor(*consts.NODE_SELECTED_COLOR))
		painter.drawRect(rect_2)
	else:
		border_color = QColor(*node_view.border_color)

	# top & bottom edge background.
	padding = 2.0
	height = 10
	if node_view.selected:
		painter.setBrush(QColor(*consts.NODE_SELECTED_COLOR))
	else:
		painter.setBrush(QColor(0, 0, 0, 80))

	painter.setPen(Qt.NoPen)
	for y in [rect_2.top() + padding, rect_2.bottom() - height - padding]:
		top_rect = QRectF(rect.x() + padding - offset, y, rect.width() - (padding * 2), height)
		painter.drawRect(top_rect)

	pen = QPen(border_color.darker(120), 0.8)
	pen.setJoinStyle(Qt.MiterJoin)
	pen.setCapStyle(Qt.RoundCap)
	painter.setBrush(Qt.NoBrush)
	painter.setPen(pen)
	painter.drawLines(
		[rect_1.topRight(), rect_2.topRight(), rect_1.topRight(), rect_1.bottomRight(),
		 rect_1.bottomRight(), rect_1.bottomLeft(), rect_1.bottomLeft(), rect_2.bottomLeft()])
	painter.drawLine(rect_1.bottomRight(), rect_2.bottomRight())

	pen = QPen(border_color, 0.8)
	pen.setJoinStyle(Qt.MiterJoin)
	pen.setCapStyle(Qt.RoundCap)
	painter.setPen(pen)
	painter.drawRect(rect_2)

	painter.restore()
