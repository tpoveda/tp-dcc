#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains socket painter functions
"""

from Qt.QtCore import Qt, QPointF, QRectF
from Qt.QtGui import QColor, QPolygonF, QPen, QTransform


def value_socket_painter(port_view, painter, option, widget):

	painter.save()

	rect_width = port_view.width / 1.5
	rect_height = port_view.height / 1.5
	rect_x = port_view.boundingRect().center().x() - (rect_width / 2)
	rect_y = port_view.boundingRect().center().y() - (rect_height / 2)
	socket_rect = QRectF(rect_x, rect_y, rect_width, rect_height)

	color = QColor(*port_view.color)
	border_color = QColor(*port_view.border_color) if port_view.border_color else color.darker(200)
	if port_view.hovered:
		border_color = border_color.lighter(250)

	pen = QPen(border_color, 1.8)
	painter.setPen(pen)
	painter.setBrush(color)
	painter.drawEllipse(socket_rect)

	if port_view.hovered or port_view.is_connected():
		painter.setBrush(border_color)
		inner_width = socket_rect.width() / 3.5
		inner_height = socket_rect.height() / 3.5
		inner_rect = QRectF(
			socket_rect.center().x() - inner_width / 2, socket_rect.center().y() - inner_height / 2,
			inner_width, inner_height)
		painter.drawEllipse(inner_rect)

	painter.restore()


def exec_socket_painter(painter, socket_ret, socket_info):
	painter.save()

	node = socket_info['node']

	color = QColor(*socket_info['color'])
	border_color = QColor(*socket_info['border_color']) if socket_info['border_color'] else color.darker(200)
	if socket_info['hovered']:
		border_color = border_color.lighter(250)

	pen = QPen(border_color, 1.8)
	painter.setPen(pen)
	painter.setBrush(color)

	lod = node.viewer().get_lod_value_from_scale()

	if lod < 3:
		pass

	rect_x = socket_ret.x()
	rect_y = socket_ret.y()
	rect_width = socket_ret.width()

	arrow = QPolygonF(
		[QPointF(rect_x, rect_y), QPointF(
			rect_x + rect_width / 2.0, rect_y), QPointF(rect_x + rect_width, rect_y + rect_width / 2.0),
		 QPointF(rect_x + rect_width / 2.0, rect_y + rect_width), QPointF(rect_x, rect_y + rect_width)])
	painter.drawPolygon(arrow)

	if socket_info['hovered']:
		painter.setPen(Qt.NoPen)
		painter.setBrush(QColor(128, 128, 128, 30))
		painter.drawRoundedRect(socket_ret, 3, 3)

	painter.restore()


def triangle_socket_painter(painter, socket_rect, socket_info):

	painter.save()

	size = int(socket_rect.height() / 2)
	triangle = QPolygonF()
	triangle.append(QPointF(-size, size))
	triangle.append(QPointF(0.0, -size))
	triangle.append(QPointF(size, size))

	transform = QTransform()
	transform.translate(socket_rect.center().x(), socket_rect.center().y())
	port_poly = transform.map(triangle)

	if socket_info['hovered']:
		color = QColor(14, 45, 59)
		border_color = QColor(136, 255, 35)
	elif socket_info['connected']:
		color = QColor(195, 60, 60)
		border_color = QColor(200, 130, 70)
	else:
		color = QColor(*socket_info['color'])
		border_color = QColor(*socket_info['border_color'])

	pen = QPen(border_color, 1.8)
	pen.setJoinStyle(Qt.MiterJoin)

	painter.setPen(pen)
	painter.setBrush(color)
	painter.drawPolygon(port_poly)

	painter.restore()


def square_socket_painter(painter, socket_rect, socket_info):

	painter.save()

	if socket_info['hovered']:
		color = QColor(14, 45, 59)
		border_color = QColor(136, 255, 35, 255)
	elif socket_info['connected']:
		color = QColor(195, 60, 60)
		border_color = QColor(200, 130, 70)
	else:
		color = QColor(*socket_info['color'])
		border_color = QColor(*socket_info['border_color'])

	pen = QPen(border_color, 1.8)
	pen.setJoinStyle(Qt.MiterJoin)

	painter.setPen(pen)
	painter.setBrush(color)
	painter.drawRect(socket_rect)

	painter.restore()
