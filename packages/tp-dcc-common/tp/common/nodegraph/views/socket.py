#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains socket view implementation
"""

from Qt.QtCore import QRectF
from Qt.QtWidgets import QGraphicsItem

from tp.common.nodegraph.core import consts
from tp.common.nodegraph.painters import socket


class SocketView(QGraphicsItem):
	"""
	Base socket view implementation
	"""

	def __init__(self, parent=None):
		super(SocketView, self).__init__(parent=parent)

		self._connectors = list()
		self._name = 'socket'
		self._display_name = True
		self._width = consts.SOCKET_DEFAULT_SIZE
		self._height = consts.SOCKET_DEFAULT_SIZE
		self._color = consts.SOCKET_DEFAULT_COLOR
		self._border_color = consts.SOCKET_DEFAULT_BORDER_COLOR
		self._border_size = 1
		self._direction = None
		self._multi_connection = False
		self._locked = False
		self._hovered = False

		self.setAcceptHoverEvents(True)
		self.setCacheMode(consts.ITEM_CACHE_MODE)
		self.setFlag(self.ItemIsSelectable, True)
		self.setFlag(self.ItemSendsScenePositionChanges, True)
		self.setZValue(consts.SOCKET_Z_VALUE)

	def __str__(self):
		return '{}.SocketView("{}")'.format(self.__module__, self.name)

	def __repr__(self):
		return '{}.SocketView("{}")'.format(self.__module__, self.name)

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def node(self):
		return self.parentItem()

	@property
	def name(self):
		return self._name

	@name.setter
	def name(self, value):
		self._name = str(value).strip()

	@property
	def display_name(self):
		return self._display_name

	@display_name.setter
	def display_name(self, flag):
		self._display_name = flag

	@property
	def direction(self):
		return self._direction

	@direction.setter
	def direction(self, value):
		self._direction = value

	@property
	def width(self):
		return self._width

	@property
	def height(self):
		return self._height

	@property
	def multi_connection(self):
		return self._multi_connection

	@multi_connection.setter
	def multi_connection(self, flag):
		connection_type = 'multi' if flag else 'single'
		self.setToolTip('{}: ({})'.format(self.name, connection_type))
		self._multi_connection = flag

	@property
	def color(self):
		return self._color

	@color.setter
	def color(self, value):
		self._color = value
		self.update()

	@property
	def border_color(self):
		return self._border_color

	@border_color.setter
	def border_color(self, value):
		self._border_color = value

	@property
	def border_size(self):
		return self._border_size

	@border_size.setter
	def border_size(self, value):
		self._border_size = value

	@property
	def locked(self):
		return self._locked

	@locked.setter
	def locked(self, flag):
		self._locked = flag
		connection_type = 'multi' if self._multi_connection else 'single'
		tooltip = '{}: ({})'.format(self.name, connection_type)
		if flag:
			tooltip += ' (L)'
		self.setToolTip(tooltip)

	@property
	def hovered(self):
		return self._hovered

	@hovered.setter
	def hovered(self, flag):
		self._hovered = flag

	@property
	def connectors(self):
		return self._connectors

	@property
	def connected_sockets(self):
		sockets = list()
		socket_types = {consts.SocketDirection.Input: 'output_socket', consts.SocketDirection.Output: 'input_socket'}
		for connector in self.connectors:
			sockets.append(getattr(connector, socket_types[self.direction]))

		return sockets

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def boundingRect(self):
		"""
		Overrides base QGraphicsItem boundingRect function.

		:return: socket view bounding rectangle.
		:rtype: QRectF
		"""

		return QRectF(0.0, 0.0, self._width + consts.SOCKET_FALLOFF, self._height)

	def itemChange(self, change, value):
		"""
		Overrides base QGraphicsItem itemChange function.

		:param change:
		:param value:
		"""

		if change == self.ItemScenePositionHasChanged:
			self.redraw_connectors()
		return super(SocketView, self).itemChange(change, value)

	def hoverEnterEvent(self, event):
		"""
		Overrides base QGraphicsItem hoverEnterEvent function.

		:param QEvent event: Qt hover event.
		"""

		self._hovered = True
		super(SocketView, self).hoverEnterEvent(event)

	def hoverLeaveEvent(self, event):
		"""
		Overrides base QGraphicsItem hoverLeaveEvent function.

		:param QEvent event: Qt hover event.
		"""

		self._hovered = False
		super(SocketView, self).hoverLeaveEvent(event)

	def paint(self, painter, option, widget):
		"""
		Overrides base QGraphicsItem paint function.

		:param QPainter painter: painter used to draw the node.
		:param QStyleOption option: optional style.
		:param QWidget widget: optional widget.
		"""

		socket.value_socket_painter(self, painter, option, widget)

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def is_connected(self):
		"""
		Returns whether this socket is connected through a connector to other sockets.

		:return: True if the socket is connected to other sockets through connectors; False otherwise.
		:rtype: bool
		"""

		return bool(self.connectors)

	def add_connector(self, connector):
		"""
		Adds a new connector to this socket.

		:param ConnectorView connector: connector view.
		"""

		self._connectors.append(connector)

	def remove_connector(self, connector):
		"""
		Removes a connector frm this socket.

		:param ConnectorView connector: connector to remove
		"""

		self._connectors.remove(connector)

	def redraw_connectors(self):
		"""
		Forces redraw of the connectors connected to this socket.
		"""

		if not self.connectors:
			return
		for connector in self.connectors:
			if self.direction == consts.SocketDirection.Input:
				connector.draw_path(self, connector.output_socket)
			elif self.direction == consts.SocketDirection.Output:
				connector.draw_path(connector.input_socket, self)

	def connect_to(self, node_socket):
		"""
		Connects this socket to the given socket.

		:param SocketView node_socket:
		"""

		if not node_socket:
			for connector in self.connectors:
				connector.delete()
			return
		if self.scene():
			viewer = self.scene().viewer()
			viewer.establish_connection(self, node_socket)
		node_socket.update()
		self.update()

	def disconnect_from(self, node_socket):
		"""
		Disconnects this socket from the given one.

		:param SocketView node_socket: socket we want to disconnect this one from.
		"""

		socket_types = {consts.SocketDirection.Input: 'output_socket', consts.SocketDirection.Output: 'input_socket'}
		for connector in self.connectors:
			connected_socket = getattr(connector, socket_types[self.direction])
			if connected_socket == node_socket:
				connector.delete()
				break
		node_socket.update()
		self.update()


class CustomSocketView(SocketView):
	"""
	Custom socket view for drawing custom sockets
	"""

	def __init__(self, parent=None, paint_fn=None):
		super(CustomSocketView, self).__init__(parent=parent)

		self._port_painter = paint_fn

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def painter(self):
		"""
		Returns custom paint function for drawing.

		:return: custom painter function.
		:rtype: callable
		"""

		return self._port_painter

	@painter.setter
	def painter(self, painter_fn):
		"""
		Sets custom paint function for drawing.

		:param callable painter_fn: custom painter function.
		"""

		self._port_painter = painter_fn

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def paint(self, painter, option, widget):
		"""
		Overrides base QGraphicsItem paint function.

		:param QPainter painter: painter used to draw the node.
		:param QStyleOption option: optional style.
		:param QWidget widget: optional widget.
		"""

		if self._port_painter:
			rect_w = self._width / 1.8
			rect_h = self._height / 1.8
			rect_x = self.boundingRect().center().x() - (rect_w / 2)
			rect_y = self.boundingRect().center().y() - (rect_h / 2)
			socket_rect = QRectF(rect_x, rect_y, rect_w, rect_h)
			socket_info = {
				'node': self.node,
				'direction': self.direction,
				'color': self.color,
				'border_color': self.border_color,
				'multi_connection': self.multi_connection,
				'connected': bool(self.connectors),
				'hovered': self.hovered,
				'locked': self.locked,
			}
			self._port_painter(painter, socket_rect, socket_info)
		else:
			super(CustomSocketView, self).paint(painter, option, widget)
