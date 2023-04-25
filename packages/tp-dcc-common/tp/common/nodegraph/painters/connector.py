#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains connector painter functions
"""

import math

from Qt.QtCore import Qt, QPointF, QRectF
from Qt.QtGui import QColor, QPen, QBrush, QLinearGradient, QTransform

from tp.common.nodegraph.core import consts


def draw_default_connector(connector_view, painter, option, widget):
	painter.save()

	lod = connector_view.viewer().get_lod_value_from_scale()
	start = connector_view.path().pointAtPercent(0.0)
	end = connector_view.path().pointAtPercent(1.0)

	linear_gradient = QLinearGradient(start.x(), start.y(), end.x(), end.y())
	start_color = QColor(*connector_view.color)
	end_color = None

	pen_style = connector_view.style
	pen_width = connector_view.thickness
	if connector_view.ready_to_slice:
		start_color = QColor(155, 0, 0, 255)
		pen_style = consts.ConnectorStyles.DOTTED
		pen_width = 1.5
	elif connector_view.active:
		start_color = start_color.lighter(125)
		if pen_style == Qt.DashDotDotLine:
			pen_width += 1
		else:
			pen_width += 0.35
	elif connector_view.highlighted:
		start_color = start_color.lighter(225)
		pen_style = consts.ConnectorStyles.DEFAULT
	else:
		if connector_view.input_socket and connector_view.output_socket:
			start_color = QColor(*connector_view.input_socket.color)
			end_color = QColor(*connector_view.output_socket.color)

	end_color = end_color or start_color

	linear_gradient.setColorAt(0.0, start_color)
	linear_gradient.setColorAt(1.0, end_color)
	gradient_brush = QBrush(linear_gradient)

	pen = QPen(gradient_brush, pen_width)
	pen.setStyle(pen_style)
	pen.setCapStyle(Qt.RoundCap)
	painter.setPen(pen)
	painter.setRenderHint(painter.Antialiasing, True)
	painter.drawPath(connector_view.path())

	if connector_view.input_socket and connector_view.output_socket:
		center_x = connector_view.path().pointAtPercent(0.5).x()
		center_y = connector_view.path().pointAtPercent(0.5).y()
		loc_point = connector_view.path().pointAtPercent(0.49)
		target_point = connector_view.path().pointAtPercent(0.51)

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
		painter.setPen(QPen(gradient_brush, pen_width))
		painter.setBrush(gradient_brush)

		transform = QTransform()
		transform.translate(center_x, center_y)
		radians = math.atan2(target_point.y() - loc_point.y(), target_point.x() - loc_point.x())
		degrees = math.degrees(radians) - 90
		transform.rotate(degrees)
		if distance < 1.0:
			transform.scale(distance, distance)
		painter.drawPolygon(transform.map(connector_view.arrow))

	painter.restore()


def draw_realtime_connector(connector_view, painter, option, widget):
	painter.save()

	color = QColor(*connector_view.color)
	pen_style = consts.ConnectorStyles.DASHED
	pen_width = connector_view.thickness + 0.35

	pen = QPen(color, pen_width)
	pen.setStyle(pen_style)
	pen.setCapStyle(Qt.RoundCap)
	painter.setPen(pen)
	painter.setRenderHint(painter.Antialiasing, True)
	painter.drawPath(connector_view.path())

	center_point = connector_view.path().pointAtPercent(0.5)
	center_x = center_point.x()
	center_y = center_point.y()
	start_point = connector_view.path().pointAtPercent(0.0)
	loc_point = connector_view.path().pointAtPercent(0.9)
	target_point = connector_view.path().pointAtPercent(1.0)

	distance = math.hypot(target_point.x() - center_x, target_point.y() - center_y)
	if distance < 0.05:
		painter.restore()
		return

	start_circle_size = 5.0
	half_start_size = start_circle_size / 2
	start_circle_rect = QRectF(
		start_point.x() - half_start_size, start_point.y() - half_start_size, start_circle_size, start_circle_size)
	painter.setBrush(color)
	painter.setPen(Qt.NoPen)
	painter.drawEllipse(start_circle_rect)

	end_circle_size = 8.0
	half_end_circle = end_circle_size / 2
	end_circle_rect = QRectF(
		target_point.x() - half_end_circle, target_point.y() - half_end_circle, end_circle_size, end_circle_size)
	painter.setBrush(color)
	painter.setPen(QPen(color.darker(130), pen_width))
	painter.drawEllipse(end_circle_rect)

	color.setAlpha(255)
	painter.setBrush(color.darker(200))
	pen_width = 0.6
	if distance < 1.0:
		pen_width *= 1.0 + distance
	painter.setPen(QPen(color, pen_width))
	transform = QTransform()
	transform.translate(center_point.x(), center_point.y())
	radians = math.atan2(center_point.y() - loc_point.y(), center_point.x() - loc_point.x())
	degrees = math.degrees(radians) - 90
	transform.rotate(degrees)
	scale = 1.0
	if distance < 20.0:
		scale = distance / 20.0
	transform.scale(scale, scale)
	painter.drawPolygon(transform.map(connector_view.arrow))

	painter.restore()


def draw_slicer_connector(slicer_view, painter, option, widget):
	painter.save()

	color = QColor(*consts.CONNECTOR_SLICER_COLOR)
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
	text_pos = QPointF(p1.x() - text_x, p1.y() - text_y)
	text_color = QColor(*consts.CONNECTOR_SLICER_COLOR)
	text_color.setAlpha(80)
	painter.setPen(QPen(text_color, 1.5, Qt.SolidLine))
	painter.drawText(text_pos, text)
	painter.setPen(QPen(color, 1.5, Qt.DashLine))
	painter.drawPath(slicer_view.path())
	painter.setPen(QPen(color, 1.5, Qt.SolidLine))
	painter.setBrush(color)
	rect = QRectF(p1.x() - offset, p1.y() - offset, size, size)
	painter.drawEllipse(rect)
	rect = QRectF(p2.x() - offset, p2.y() - offset, size, size)
	painter.drawEllipse(rect)

	painter.restore()
