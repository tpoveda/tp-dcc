from Qt.QtCore import Qt, QObject, Signal, QPointF, QLineF
from Qt.QtWidgets import QGraphicsPathItem, QGraphicsEllipseItem
from Qt.QtGui import QColor, QPen, QPainterPath, QPolygonF, QPainterPathStroker

from tp.common.nodegraph.core import consts
from tp.common.nodegraph.views import socket as socket_view
from tp.common.nodegraph.painters import connector


class ConnectorView(QGraphicsPathItem):
	def __init__(self, input_socket_view=None, output_socket_view=None):
		super(ConnectorView, self).__init__()

		self.setZValue(consts.CONNECTOR_Z_VALUE)
		self.setAcceptHoverEvents(True)
		# self.setAcceptedMouseButtons(Qt.LeftButton)
		self.setFlags(QGraphicsPathItem.ItemIsSelectable)
		self.setCacheMode(consts.ITEM_CACHE_MODE)

		self._color = consts.CONNECTOR_COLOR
		self._style = consts.ConnectorStyles.DEFAULT
		self._thickness = consts.CONNECTOR_THICKNESS
		self._active = False
		self._highlight = False
		self._ready_to_slice = False
		self._pen = QPen(QColor(*self._color), self._thickness, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
		self._input_socket_view = input_socket_view
		self._output_socket_view = output_socket_view

		size = 4.0
		self._arrow = QPolygonF()
		self._arrow.append(QPointF(-size, size))
		self._arrow.append(QPointF(0.0, -size * 1.5))
		self._arrow.append(QPointF(size, size))

	def __repr__(self):
		in_name = self._input_socket_view.name if self._input_socket_view else ''
		out_name = self._output_socket_view.name if self._output_socket_view else ''
		return '{}.ConnectorView(\'{}\', \'{}\')'.format(self.__module__, in_name, out_name)

	# ==============================================================================================
	# PROPERTIES
	# ==============================================================================================

	@property
	def color(self):
		return self._color

	@color.setter
	def color(self, value):
		self._color = value

	@property
	def thickness(self):
		return self._thickness

	@property
	def input_socket(self):
		return self._input_socket_view

	@input_socket.setter
	def input_socket(self, socket):
		if socket and isinstance(socket, socket_view.SocketView):
			self._input_socket_view = socket
		else:
			self._input_socket_view = None

	@property
	def output_socket(self):
		return self._output_socket_view

	@output_socket.setter
	def output_socket(self, socket):
		if socket and isinstance(socket, socket_view.SocketView):
			self._output_socket_view = socket
		else:
			self._output_socket_view = None

	@property
	def style(self):
		return self._style

	@style.setter
	def style(self, value):
		self._style = value

	@property
	def ready_to_slice(self):
		return self._ready_to_slice

	@ready_to_slice.setter
	def ready_to_slice(self, value):
		if value != self._ready_to_slice:
			self._ready_to_slice = value
			self.update()

	@property
	def active(self):
		return self._active

	@property
	def highlighted(self):
		return self._highlight

	@property
	def arrow(self):
		return self._arrow

	# ==============================================================================================
	# OVERRIDES
	# ==============================================================================================

	def hoverEnterEvent(self, event):
		self.activate()

	def hoverLeaveEvent(self, event):
		self.reset()
		if self._input_socket_view and self._output_socket_view:
			pass

	def paint(self, painter, option, widget):
		connector.draw_default_connector(self, painter, option, widget)

	# ==============================================================================================
	# BASE
	# ==============================================================================================

	def set_connections(self, socket1, socket2):
		"""
		Sets the socket views this connector is linked to.

		:param tp.common.nodegraph.views.socket.SocketView socket1: first socket.
		:param tp.common.nodegraph.views.socket.SocketView socket2: second socket.
		"""

		sockets = {socket1.direction: socket1, socket2.direction: socket2}
		self._input_socket_view = sockets[consts.SocketDirection.Input]
		self._output_socket_view = sockets[consts.SocketDirection.Output]
		sockets[consts.SocketDirection.Input].add_connector(self)
		sockets[consts.SocketDirection.Output].add_connector(self)

	def activate(self):
		"""
		Activates connector.
		"""

		self._active = True
		self.setPen(QPen(QColor(*self.color).lighter(125), self._thickness, consts.ConnectorStyles.get(self._style)))

	def highlight(self):
		"""
		Highlights current connector.
		"""

		self._highlight = True
		self.setPen(QPen(QColor(*self.color).lighter(225), self._thickness, consts.ConnectorStyles.get(self._style)))

	def reset(self):
		"""
		Resets connector.
		"""

		self._active = False
		self._highlight = False
		self.setPen(QPen(QColor(*self._color), self._thickness, consts.ConnectorStyles.get(self._style)))

	def viewer(self):
		"""
		Returns graph viewer this connector is attached.

		:return: node graph view.
		:rtype: tp.common.nodegraph.views.graph.NodeGraphView or None
		"""

		current_scene = self.scene()
		if not current_scene:
			return None

		return current_scene.viewer()

	def draw_path(self, start_socket, end_socket=None, cursor_pos=None):
		"""
		Draws path between ports.

		:param start_socket: tp.common.nodegraph.views.SocketView, socket used to draw the starting point.
		:param end_socket: tp.common.nodegraph.views.SocketView or None, socket used to draw the end point.
		:param cursor_pos: QPointF or None, if specified cursor this position will be used to raw the end point
		"""

		if not start_socket:
			return

		pos1 = start_socket.scenePos()
		pos1.setX(pos1.x() + (start_socket.boundingRect().width() / 2))
		pos1.setY(pos1.y() + (start_socket.boundingRect().height() / 2))
		if cursor_pos:
			pos2 = cursor_pos
		elif end_socket:
			pos2 = end_socket.scenePos()
			pos2.setX(pos2.x() + (start_socket.boundingRect().width() / 2))
			pos2.setY(pos2.y() + (start_socket.boundingRect().height() / 2))
		else:
			return

		line = QLineF(pos1, pos2)
		path = QPainterPath()
		path.moveTo(line.x1(), line.y1())

		viewer = self.viewer()
		if not viewer:
			return

		if viewer.connector_layout() == consts.ConnectorLayoutStyles.STRAIGHT:
			path.lineTo(pos2)
			self.setPath(path)
		else:
			if viewer.layout_direction() == consts.GraphLayoutDirection.HORIZONTAL:
				self._draw_path_horizontal(start_socket, pos1, pos2, path)
			elif viewer.layout_direction() == consts.GraphLayoutDirection.VERTICAL:
				self._draw_path_vertical(start_socket, pos1, pos2, path)

	def reset_path(self):
		"""
		Resets path.
		"""

		path = QPainterPath(QPointF(0.0, 0.0))
		self.setPath(path)

	def delete(self):
		"""
		Deletes this connector from its scene.
		"""

		if self._input_socket_view and self._input_socket_view.connectors:
			self._input_socket_view.remove_connector(self)
		if self._output_socket_view and self._output_socket_view.connectors:
			self._output_socket_view.remove_connector(self)
		if self.scene():
			self.scene().removeItem(self)

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _draw_path_vertical(self, start_socket, pos1, pos2, path):
		"""
		Internal function that draws the vertical path between sockets.

		:param tp.common.nodegraph.views.SocketView start_socket: start socket.
		:param QPointF pos1: start socket position
		:param QPointF pos2: end socket position.
		:param QPainterPath path: draw path.
		"""

		if self.connector_layout() == consts.ConnectorLayoutStyles.CURVED:
			ctr_offset_y1, ctr_offset_y2 = pos1.y(), pos2.y()
			tangent = abs(ctr_offset_y1 - ctr_offset_y2)
			max_height = start_socket.node.boundingRect().height()
			tangent = min(tangent, max_height)
			if start_socket.port_type == consts.SocketDirection.Input:
				ctr_offset_y1 -= tangent
				ctr_offset_y2 += tangent
			else:
				ctr_offset_y1 += tangent
				ctr_offset_y2 -= tangent
			ctr_point1 = QPointF(pos1.x(), ctr_offset_y1)
			ctr_point2 = QPointF(pos2.x(), ctr_offset_y2)
			path.cubicTo(ctr_point1, ctr_point2, pos2)
			self.setPath(path)
		elif self.connector_layout() == consts.ConnectorLayoutStyles.ANGLE:
			ctr_offset_y1, ctr_offset_y2 = pos1.y(), pos2.y()
			distance = abs(ctr_offset_y1 - ctr_offset_y2)/2
			if start_socket.port_type == consts.SocketDirection.Input:
				ctr_offset_y1 -= distance
				ctr_offset_y2 += distance
			else:
				ctr_offset_y1 += distance
				ctr_offset_y2 -= distance
			ctr_point1 = QPointF(pos1.x(), ctr_offset_y1)
			ctr_point2 = QPointF(pos2.x(), ctr_offset_y2)
			path.lineTo(ctr_point1)
			path.lineTo(ctr_point2)
			path.lineTo(pos2)
			self.setPath(path)

	def _draw_path_horizontal(self, start_socket, pos1, pos2, path):
		"""
		Internal function that draws the horizontal path between sockets.

		:param tp.common.nodegraph.views.SocketView start_socket: start socket.
		:param QPointF pos1: start socket position
		:param QPointF pos2: end socket position.
		:param QPainterPath path: draw path.
		"""

		viewer = self.viewer()
		if not viewer:
			return

		if viewer.connector_layout() == consts.ConnectorLayoutStyles.CURVED:
			ctr_offset_x1, ctr_offset_x2 = pos1.x(), pos2.x()
			tangent = abs(ctr_offset_x1 - ctr_offset_x2)
			max_width = start_socket.node.boundingRect().width()
			tangent = min(tangent, max_width)
			if start_socket.direction == consts.SocketDirection.Input:
				ctr_offset_x1 -= tangent
				ctr_offset_x2 += tangent
			else:
				ctr_offset_x1 += tangent
				ctr_offset_x2 -= tangent
			ctr_point1 = QPointF(ctr_offset_x1, pos1.y())
			ctr_point2 = QPointF(ctr_offset_x2, pos2.y())
			path.cubicTo(ctr_point1, ctr_point2, pos2)
			self.setPath(path)
		elif viewer.connector_layout() == consts.ConnectorLayoutStyles.ANGLE:
			ctr_offset_x1, ctr_offset_x2 = pos1.x(), pos2.x()
			distance = abs(ctr_offset_x1 - ctr_offset_x2) / 2
			if start_socket.direction == consts.SocketDirection.Input:
				ctr_offset_x1 -= distance
				ctr_offset_x2 += distance
			else:
				ctr_offset_x1 += distance
				ctr_offset_x2 -= distance
			ctr_point1 = QPointF(ctr_offset_x1, pos1.y())
			ctr_point2 = QPointF(ctr_offset_x2, pos2.y())
			path.lineTo(ctr_point1)
			path.lineTo(ctr_point2)
			path.lineTo(pos2)
			self.setPath(path)


class RealtimeConnector(ConnectorView, object):
	def __init__(self):
		super(RealtimeConnector, self).__init__()

		self.name = 'RealTimeLine'

		self.setZValue(consts.WIDGET_Z_VALUE + 1)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def paint(self, painter, option, widget):
		connector.draw_realtime_connector(self, painter, option, widget)

	def tick(self, delta_time):
		pass

	def pre_create(self):
		pass

	def post_create(self):
		pass


class ConnectorSliderSignals(QObject):
	visibilityChanged = Signal(bool)


class ConnectorSlicer(QGraphicsPathItem, object):
	def __init__(self):
		super(ConnectorSlicer, self).__init__()

		self.signals = ConnectorSliderSignals()
		self.setZValue(consts.WIDGET_Z_VALUE + 2)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def paint(self, painter, option, widget):
		connector.draw_slicer_connector(self, painter, option, widget)

	def itemChange(self, change, value):
		if change == self.ItemVisibleChange:
			self.signals.visibilityChanged.emit(bool(value))

		return super(ConnectorSlicer, self).itemChange(change, value)

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def draw_path(self, p1, p2):
		path = QPainterPath()
		path.moveTo(p1)
		path.lineTo(p2)
		self.setPath(path)
