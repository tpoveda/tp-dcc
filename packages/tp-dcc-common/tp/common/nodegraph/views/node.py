#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains node view implementation
"""

from collections import OrderedDict

from Qt.QtCore import Qt, QRectF, QSize
from Qt.QtWidgets import QGraphicsItem, QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsDropShadowEffect
from Qt.QtGui import QFont, QColor, QPixmap

from tp.core import log
from tp.core.managers import resources
from tp.common.python import helpers, path
from tp.common.nodegraph.core import consts, exceptions
from tp.common.nodegraph.views import socket
from tp.common.nodegraph.painters import node as node_painters

logger = log.tpLogger


class BaseNodeView(QGraphicsItem):
	"""
	Base class for all node views.
	"""

	def __init__(self, name='node', parent=None):
		super(BaseNodeView, self).__init__(parent=parent)

		self.setFlags(self.ItemIsSelectable | self.ItemIsMovable)
		self.setCacheMode(consts.ITEM_CACHE_MODE)
		self.setZValue(consts.NODE_Z_VALUE)
		self._properties = {
			'id': None,
			'name': name.strip(),
			'color': consts.NODE_COLOR,
			'border_color': consts.NODE_BORDER_COLOR,
			'text_color': consts.NODE_TEXT_COLOR,
			'header_color': consts.NODE_HEADER_COLOR,
			'type_': 'BaseNodeView',
			'selected': False,
			'disabled': False,
			'visible': False,
			'layout_direction': consts.GraphLayoutDirection.HORIZONTAL
		}
		self._width = consts.NODE_WIDTH
		self._height = consts.NODE_HEIGHT

		self._item_shadow = QGraphicsDropShadowEffect()
		self._item_shadow.setBlurRadius(35)
		self._item_shadow.setXOffset(3)
		self._item_shadow.setYOffset(3)
		self._item_shadow.setColor(QColor(0, 0, 0, 200))
		self.setGraphicsEffect(self._item_shadow)
		self._item_shadow.setEnabled(True)

		self.setup_ui()

	def __repr__(self):
		return '{}.{}(\'{}\')'.format(self.__module__, self.__class__.__name__, self.name)

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def properties(self):
		props = dict(
			width=self.width,
			height=self.height,
			pos=self.xy_pos
		)
		props.update(self._properties)

		return props

	@property
	def id(self):
		return self._properties['id']

	@id.setter
	def id(self, value):
		self._properties['id'] = value

	@property
	def type_(self):
		return self._properties['type_']

	@type_.setter
	def type_(self, value):
		self._properties['type_'] = value

	@property
	def name(self):
		return self._properties['name']

	@name.setter
	def name(self, value):
		self._properties['name'] = value
		self.setToolTip('node: {}'.format(value))

	@property
	def width(self):
		return self._width

	@width.setter
	def width(self, value):
		self._width = value

	@property
	def height(self):
		return self._height

	@height.setter
	def height(self, value):
		self._height = value

	@property
	def size(self):
		return self._width, self._height

	@property
	def xy_pos(self):
		return [float(self.scenePos().x()), float(self.scenePos().y())]

	@xy_pos.setter
	def xy_pos(self, pos):
		pos = pos or [0.0, 0.0]
		self.setPos(pos[0], pos[1])

	@property
	def color(self):
		return self._properties['color']

	@color.setter
	def color(self, value):
		self._properties['color'] = helpers.force_list(value)

	@property
	def text_color(self):
		return self._properties['text_color']

	@text_color.setter
	def text_color(self, value):
		self._properties['text_color'] = helpers.force_list(value)

	@property
	def border_color(self):
		return self._properties['border_color']

	@border_color.setter
	def border_color(self, value):
		self._properties['border_color'] = helpers.force_list(value)

	@property
	def header_color(self):
		return self._properties['header_color']

	@header_color.setter
	def header_color(self, value):
		self._properties['header_color'] = helpers.force_list(value)

	@property
	def disabled(self):
		return self._properties['disabled']

	@disabled.setter
	def disabled(self, flag):
		self._properties['disabled'] = flag

	@property
	def selected(self):
		if self._properties['selected'] != self.isSelected():
			self._properties['selected'] = self.isSelected()
		return self._properties['selected']

	@selected.setter
	def selected(self, flag=False):
		self.setSelected(flag)

	@property
	def visible(self):
		return self._properties['visible']

	@visible.setter
	def visible(self, visible=False):
		self._properties['visible'] = visible
		self.setVisible(visible)

	@property
	def layout_direction(self):
		return self._properties['layout_direction']

	@layout_direction.setter
	def layout_direction(self, value):
		self._properties['layout_direction'] = value

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def boundingRect(self):
		"""
		Overrides base QGraphicsItem boundingRect function.

		:return: bounding rect rectangle area.
		:rtype: QRectF
		"""

		return QRectF(0.0, 0.0, self._width, self._height)

	def mousePressEvent(self, event):
		"""
		Overrides base QGraphicsItem mousePressEvent function.

		:param QQGraphicsSceneMouseEvent event: mouse event.
		"""

		self._properties['selected'] = True
		super(BaseNodeView, self).mousePressEvent(event)

	def setSelected(self, selected):
		"""
		Overrides base QGraphicsItem setSelected function.

		:param bool selected: whether or not graphics item is selected.
		"""

		self._properties['selected'] = selected
		super(BaseNodeView, self).setSelected(selected)

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def setup_ui(self):
		"""
		Setups node UI.

		..note:: this function should be override in derived classes.
		"""

		pass

	def viewer(self):
		"""
		Returns graph viewer this node belongs to.

		:return: node graph viewer.
		:rtype: NodeGraphViewer or None
		"""

		return self.scene().viewer() if self.scene() else None

	def from_dict(self, node_dict):
		"""
		Updates the view data from the contents withing the given node dictionary.

		:param dict node_dict: serialized node dictionary.
		"""

		node_attributes = list(self._properties.keys()) + ['width', 'height', 'pos']
		for name, value in node_dict.items():
			if name in node_attributes:
				if name == 'pos':
					name = 'xy_pos'     # to avoid conflicts with QGrahpicsItem pos attribute
				try:
					setattr(self, name, value)
				except Exception as exc:
					logger.warning('Was not possible to set attribute: {} for node: {} --> {}'.format(name, self, exc))

	def pre_init(self, viewer, pos=None):
		"""
		Function that is called before node has been added into the scene.

		:param NodeGraphViewer viewer: main node graph viewer.
		:param tuple(float, float) pos: cursor position if node is called with nodes palette.
		"""

		pass

	def post_init(self, viewer=None, pos=None):
		"""
		Function that is called after node has been added into the scene.

		:param NodeGraphViewer viewer: main node graph viewer.
		:param tuple(float, float) pos: cursor position if node is called with nodes palette.
		"""

		pass

	def delete(self):
		"""
		Removes the node from the scene.
		"""

		if not self.scene():
			return

		# We call it to properly delete item with QGraphicsEffected attached to it
		# https://forum.qt.io/topic/75510/deleting-qgraphicsitem-with-qgraphicseffect-leads-to-segfault
		self.prepareGeometryChange()
		self.setGraphicsEffect(None)
		self._item_shadow = None

		self.scene().removeItem(self)
		del(self)


class NodeView(BaseNodeView):
	"""
	Base node view all node views should use.
	"""

	def __init__(self, name='node', parent=None):
		super(NodeView, self).__init__(name=name, parent=parent)

		self._input_views = OrderedDict()
		self._output_views = OrderedDict()
		self._widgets = OrderedDict()
		self._proxy_mode = False
		self._proxy_mode_threshold = 70

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@BaseNodeView.name.setter
	def name(self, value):
		BaseNodeView.name.fset(self, value)
		if value == self._title_item.toPlainText():
			return
		self._title_item.setPlainText(value)
		if self.scene():
			self._align_title()
		self.update()

	@BaseNodeView.width.setter
	def width(self, value):
		width, _ = self._calculate_size()
		value = value if value > width else width
		BaseNodeView.width.fset(self, value)

	@BaseNodeView.height.setter
	def height(self, value):
		_, height = self._calculate_size()
		height = 70 if value < 70 else height
		value = value if value > height else height
		BaseNodeView.height.fset(self, value)

	@BaseNodeView.color.setter
	def color(self, value):
		BaseNodeView.color.fset(self, value)
		if self.scene():
			self.scene().update()
		self.update()

	@BaseNodeView.text_color.setter
	def text_color(self, value):
		BaseNodeView.text_color.fset(self, value)
		self._set_text_color(value)
		self.update()

	@BaseNodeView.disabled.setter
	def disabled(self, flag):
		BaseNodeView.disabled.fset(self, flag)
		for _, w in self._widgets.items():
			w.widget().setDisabled(flag)
		self._tooltip_disable(flag)
		self._disabled_item.setVisible(flag)

	@BaseNodeView.selected.setter
	def selected(self, flag=False):
		BaseNodeView.selected.fset(self, flag)
		if flag:
			self.highlight_connectors()

	@BaseNodeView.layout_direction.setter
	def layout_direction(self, value):
		BaseNodeView.layout_direction.fset(self, value)
		self.draw()

	@property
	def title_item(self):
		return self._title_item

	@property
	def icon(self):
		return self._properties['icon']

	@icon.setter
	def icon(self, value):
		value = value or consts.NODE_ICON_NAME
		if path.is_file(value):
			pixmap = QPixmap(value)
		else:
			pixmap = resources.icon(value).pixmap(QSize(consts.NODE_ICON_SIZE, consts.NODE_ICON_SIZE))
		if pixmap.size().height() > consts.NODE_ICON_SIZE:
			pixmap = pixmap.scaledToHeight(consts.NODE_ICON_SIZE, Qt.SmoothTransformation)
		self._properties['icon'] = value
		self._icon_item.setPixmap(pixmap)
		if self.scene():
			self.post_init()
		self.update()

	@property
	def title_height(self):
		return self._title_item.boundingRect().height()

	@property
	def inputs(self):
		return list(self._input_views.keys())

	@property
	def outputs(self):
		return list(self._output_views.keys())

	@property
	def widgets(self):
		return self._widgets

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def setup_ui(self):
		"""
		Overrides BaseNodeView setup_ui function.
		"""

		pixmap = resources.icon(consts.NODE_ICON_NAME).pixmap(QSize(consts.NODE_ICON_SIZE, consts.NODE_ICON_SIZE))
		if pixmap.size().height() > consts.NODE_ICON_SIZE:
			pixmap = pixmap.scaledToHeight(consts.NODE_ICON_SIZE, Qt.SmoothTransformation)
		self._properties['icon'] = consts.NODE_ICON_NAME
		self._icon_item = QGraphicsPixmapItem(pixmap, self)
		self._icon_item.setTransformationMode(Qt.SmoothTransformation)

		self._title_item = NodeTitle(self.name, parent=self)
		self._disabled_item = NodeDisabled('DISABLED', parent=self)

	def mousePressEvent(self, event):
		"""
		Overrides mousePressEvent function to ignore event if left mouse button is over socket collision area.

		:param Qt.QtWidgets.QGraphicsSceneMouseEvent event: scene mouse event.
		"""

		if event.button() == Qt.LeftButton:
			for input_socket in self._input_views.keys():
				if input_socket.hovered:
					event.ignore()
					return
			for output_socket in self._output_views.keys():
				if output_socket.hovered:
					event.ignore()
					return

		super(NodeView, self).mousePressEvent(event)

	def mouseDoubleClickEvent(self, event):
		"""
		Overrides mouseDoubleClickEvent to emit nodeDoubleClicked signal in graph viewer or to enter title edit mode.

		:param Qt.QtWidgets.QGraphicsSceneMouseEvent event: scene mouse event.
		"""

		if event.button() == Qt.LeftButton:
			items = self.scene().items(event.scenePos())
			if self._title_item in items:
				self._title_item.set_editable(True)
				self._title_item.setFocus()
				event.ignore()
				return

			viewer = self.viewer()
			if viewer:
				viewer.nodeDoubleClicked.emit(self.id)

		super(NodeView, self).mouseDoubleClickEvent(event)

	def mouseReleaseEvent(self, event):
		"""
		Overrides mouseReleaseEvent to ignore event if alt modifier is pressed.

		:param Qt.QtWidgets.QGraphicsSceneMouseEvent event: scene mouse event.
		"""

		if event.modifiers() == Qt.AltModifier:
			event.ignore()
			return

		super(NodeView, self).mouseReleaseEvent(event)

	def itemChange(self, change, value):
		"""
		Overrides itemChange function to update connectors on selection changed.

		:param QGraphicsItem.GraphicsItemChange change: type of change.
		:param object value: change value.
		"""

		if change == self.ItemSelectedChange and self.scene():
			self.reset_connectors()
			if value:
				self.highlight_connectors()
			self.setZValue(consts.NODE_Z_VALUE)
			if not self.selected:
				self.setZValue(consts.NODE_Z_VALUE + 1)

		return super(NodeView, self).itemChange(change, value)

	def paint(self, painter, option, widget):
		"""
		Overrides base QGraphicsItem paint function.

		:param QPainter painter: painter used to draw the node.
		:param QStyleOption option: optional style.
		:param QWidget widget: optional widget.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		self.auto_switch_proxy_mode()

		if self.layout_direction == consts.GraphLayoutDirection.HORIZONTAL:
			node_painters.node_painter_horizontal(self, painter, option, widget)
		elif self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			node_painters.node_painter_vertical(self, painter, option, widget)
		else:
			raise RuntimeError('Node graph layout direction is not valid!')

	def post_init(self, viewer=None, pos=None):
		"""
		Overrides base BaseNodeView post_init function.
		Function that is called after node has been added into the scene.

		:param NodeGraphViewer viewer: main node graph viewer.
		:param tuple(float, float) pos: cursor position if node is called with nodes palette.
		"""

		if self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			font = QFont()
			font.setPointSize(15)
			self._title_item.setFont(font)

			for text_item in self._input_views.values():
				text_item.setVisible(False)
			for text_item in self._output_views.values():
				text_item.setVisible(False)

		self.draw()

		if pos:
			self.xy_pos = pos

	def from_dict(self, node_dict):
		"""
		Updates the view data from the contents withing the given node dictionary.

		:param dict node_dict: serialized node dictionary.
		"""

		super(NodeView, self).from_dict(node_dict)

		widgets = node_dict.pop('widgets', dict())
		for name, value in widgets.items():
			if self._widgets.get(name):
				self._widgets[name].set_value(value)

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def draw(self):
		"""
		Draws the node view in the scene.
		"""

		if self.layout_direction == consts.GraphLayoutDirection.HORIZONTAL:
			self._draw_node_horizontal()
		elif self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			self._draw_node_vertical()
		else:
			raise RuntimeError('Node graph layout direction is not valid!')

	# =================================================================================================================
	# CONNECTORS
	# =================================================================================================================

	def activate_connectors(self):
		"""
		Activates connectors colors.
		"""

		sockets = self.inputs + self.outputs
		for node_socket in sockets:
			for connector in node_socket.connectors:
				connector.activate()

	def highlight_connectors(self):
		"""
		Highlight connectors color.
		"""

		sockets = self.inputs + self.outputs
		for node_socket in sockets:
			for connector in node_socket.connectors:
				connector.highlight()

	def reset_connectors(self):
		"""
		Reset all the connectors colors.
		"""

		sockets = self.inputs + self.outputs
		for node_socket in sockets:
			for connector in node_socket.connectors:
				connector.reset()

	# ==================================================================================================================
	# SOCKETS
	# ==================================================================================================================

	def add_input(self, name='input', multi_port=False, display_name=True, locked=False, painter_fn=None):
		"""
		Adds a new input socket view item into the node view.

		:param str name: name for the input socket view.
		:param bool multi_port: whether socket view will allow multiple connections.
		:param str display_name: socket view display name.
		:param bool locked: whether port view will be locked.
		:param callable painter_fn: custom socket input view painter function.
		:return: newly created socket input view.
		:rtype: SocketView
		"""

		socket_view = socket.SocketView(self) if not painter_fn else socket.CustomSocketView(self, painter_fn)
		socket_view.name = name
		socket_view.direction = consts.SocketDirection.Input
		socket_view.multi_connection = multi_port
		socket_view.display_name = display_name
		socket_view.locked = locked

		return self._add_socket(socket_view)

	def add_output(self, name='output', multi_port=False, display_name=True, locked=False, painter_fn=None):
		"""
		Adds a new output socket view item into the node view.

		:param str name: name for the output socket view.
		:param bool multi_port: whether socket view will allow multiple connections.
		:param str display_name: socket view display name.
		:param bool locked: whether port view will be locked.
		:param callable painter_fn: custom socket input view painter function.
		:return: newly created socket output view.
		:rtype: SocketView
		"""

		socket_view = socket.SocketView(self) if not painter_fn else socket.CustomSocketView(self, painter_fn)
		socket_view.name = name
		socket_view.direction = consts.SocketDirection.Output
		socket_view.multi_connection = multi_port
		socket_view.display_name = display_name
		socket_view.locked = locked

		return self._add_socket(socket_view)

	def input_text_item(self, socket_view):
		"""
		Returns text item used to display given input socket view text.

		:param SocketView socket_view: input socket view whose text we want to retrieve.
		:return: graphic item used for the socket text.
		:rtype: QGraphicsTextItem
		"""

		return self._input_views[socket_view]

	def output_text_item(self, socket_view):
		"""
		Returns text item used to display given output socket view text.

		:param SocketView socket_view: output socket view whose text we want to retrieve.
		:return: graphic item used for the socket text.
		:rtype: QGraphicsTextItem
		"""

		return self._output_views[socket_view]

	def delete_input(self, socket_view):
		"""
		Deletes given input socket view from this node.

		:param SocketView socket_view: input socket view to delete.
		"""

		self._delete_socket(socket_view, self._input_views.pop(socket_view))

	def delete_output(self, socket_view):
		"""
		Deletes given output socket view from this node.

		:param SocketView socket_view: output socket view to delete.
		"""

		self._delete_socket(socket_view, self._output_views.pop(socket_view))

	# ==================================================================================================================
	# LEVEL OF DETAIL
	# ==================================================================================================================

	def set_proxy_mode(self, proxy_mode):
		"""
		Sets whether node view should be drawn in proxy mode.

		:param bool proxy_mode: True to enabled proxy mode; False otherwise.

		..note:: proxy mode toggles visibility for some graphic items in the node.
		"""

		if proxy_mode == self._proxy_mode:
			return
		self._proxy_mode = proxy_mode
		visible = not proxy_mode

		# shadow visibility
		# if not self._item_shadow:
		#     self._item_shadow = QGraphicsDropShadowEffect()
		#     self._item_shadow.setBlurRadius(35)
		#     self._item_shadow.setXOffset(3)
		#     self._item_shadow.setYOffset(3)
		#     self._item_shadow.setColor(QColor(0, 0, 0, 200))
		#     self.prepareGeometryChange()
		#     self.setGraphicsEffect(self._item_shadow)
		self._item_shadow.setEnabled(visible)

		# self._disabled_item.proxy_mode = self._proxy_mode

		# node widgets visibility
		for widget in self._widgets.values():
			widget.widget().setVisible(visible)

		# node sockets visibility
		for input_socket, text in self._input_views.items():
			if input_socket.display_name:
				text.setVisible(visible)
		for output_socket, text in self._output_views.items():
			if output_socket.display_name:
				text.setVisible(visible)

		# node text and icon visibility
		self._title_item.setVisible(visible)
		self._icon_item.setVisible(visible)

	def auto_switch_proxy_mode(self):
		"""
		Updates proxy mode based on how much the node occupy within scene view.
		"""

		if self.cacheMode() == QGraphicsItem.ItemCoordinateCache:
			return
		rect = self.sceneBoundingRect()
		top_left = self.viewer().mapToGlobal(self.viewer().mapFromScene(rect.topLeft()))
		top_right = self.viewer().mapToGlobal(self.viewer().mapFromScene(rect.topRight()))
		with_in_screen = top_right.x() - top_left.x()
		self.set_proxy_mode(with_in_screen < self._proxy_mode_threshold)

	# ==================================================================================================================
	# WIDGETS
	# ==================================================================================================================

	def add_widget(self, widget):
		self._widgets[widget.name()] = widget

	def widget(self, name):
		found_widget = self._widgets.get(name)
		if not found_widget:
			raise exceptions.NodeWidgetError('node has no widget "{}"'.format(name))
		return found_widget

	def has_widget(self, name):
		return name in self._widgets

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _calculate_size(self, add_width=0.0, add_height=0.0):
		"""
		Internal function that calculates the minimum node size.

		:param float add_width: additional width.
		:param float add_height: additional height.
		:return: minimum node size.
		:rtype: tuple(float, float)
		"""

		# the initial size is defined by the title
		text_w = self._title_item.boundingRect().width()
		text_h = self._title_item.boundingRect().height()

		# width, height from node ports.
		port_width = 0.0
		socket_input_text_width = 0.0
		socket_output_text_width = 0.0
		socket_input_height = 0.0
		socket_output_height = 0.0
		for socket_view, text in self._input_views.items():
			if not socket_view.isVisible():
				continue
			if not port_width:
				port_width = socket_view.boundingRect().width()
			t_width = text.boundingRect().width()
			if text.isVisible() and t_width > socket_input_text_width:
				socket_input_text_width = text.boundingRect().width()
			socket_input_height += socket_view.boundingRect().height()
		for socket_view, text in self._output_views.items():
			if not socket_view.isVisible():
				continue
			if not port_width:
				port_width = socket_view.boundingRect().width()
			t_width = text.boundingRect().width()
			if text.isVisible() and t_width > socket_output_text_width:
				socket_output_text_width = text.boundingRect().width()
			socket_output_height += socket_view.boundingRect().height()

		socket_text_width = socket_input_text_width + socket_output_text_width

		# width, height from node embedded widgets.
		widget_width = 0.0
		widget_height = 0.0
		for widget in self._widgets.values():
			w_width = widget.boundingRect().width()
			w_height = widget.boundingRect().height()
			if w_width > widget_width:
				widget_width = w_width
			widget_height += w_height

		side_padding = 0.0
		if all([widget_width, socket_input_text_width, socket_output_text_width]):
			socket_text_width = max([socket_input_text_width, socket_output_text_width])
			socket_text_width *= 2
		elif widget_width:
			side_padding = 10

		width = port_width + max([text_w, socket_text_width]) + side_padding
		height = max([text_h, socket_input_height, socket_output_height, widget_height])
		if widget_width:
			# add additional width for node widget.
			width += widget_width
		if widget_height:
			# add bottom margin for node widget.
			height += 4.0
		height *= 1.05

		# additional width, height.
		width += add_width
		height += add_height

		return width, height

	def _align_icon(self, horizontal_offset=0.0, vertical_offset=0.0):
		"""
		Internal function that aligns node icon to the default top left of the node.

		:param float horizontal_offset: extra horizontal offset.
		:param float vertical_offset: extra vertical offset.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		if self.layout_direction == consts.GraphLayoutDirection.HORIZONTAL:
			self._align_icon_horizontal(horizontal_offset, vertical_offset)
		elif self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			self._align_icon_vertical(horizontal_offset, vertical_offset)
		else:
			raise RuntimeError('Node graph layout direction is not valid!')

	def _align_icon_horizontal(self, horizontal_offset=0.0, vertical_offset=0.0):
		"""
		Internal function that aligns node icon to the default top left of the node horizontally.

		:param float horizontal_offset: extra horizontal offset.
		:param float vertical_offset: extra vertical offset.
		"""

		icon_rect = self._icon_item.boundingRect()
		title_rect = self._title_item.boundingRect()
		x = self.boundingRect().left() + 2.0
		y = title_rect.center().y() - (icon_rect.height() / 2)
		self._icon_item.setPos(x + horizontal_offset, y + vertical_offset)

	def _align_icon_vertical(self, horizontal_offset=0.0, vertical_offset=0.0):
		"""
		Internal function that aligns node icon to the default top left of the node vertically.

		:param float horizontal_offset: extra horizontal offset.
		:param float vertical_offset: extra vertical offset.
		"""

		center_y = self.boundingRect().center().y()
		icon_rect = self._icon_item.boundingRect()
		title_rect = self._title_item.boundingRect()
		x = self.boundingRect().right() + horizontal_offset
		y = center_y - title_rect.height() - (icon_rect.height() / 2) + vertical_offset
		self._icon_item.setPos(x, y)

	def _align_title(self, horizontal_offset=0.0, vertical_offset=0.0):
		"""
		Internal function that aligns node label to the top of the node.

		:param float horizontal_offset: extra horizontal offset.
		:param float vertical_offset: extra vertical offset.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		if self.layout_direction == consts.GraphLayoutDirection.HORIZONTAL:
			self._align_title_horizontal(horizontal_offset, vertical_offset)
		elif self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			self._align_title_vertical(horizontal_offset, vertical_offset)
		else:
			raise RuntimeError('Node graph layout direction is not valid!')

	def _align_title_horizontal(self, horizontal_offset=0.0, vertical_offset=0.0):
		"""
		Internal function that aligns node label to the top of the node horizontally.

		:param float horizontal_offset: extra horizontal offset.
		:param float vertical_offset: extra vertical offset.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		rect = self.boundingRect()
		text_rect = self._title_item.boundingRect()
		x = rect.center().x() - (text_rect.width() / 2)
		self._title_item.setPos(x + horizontal_offset, rect.y() + vertical_offset)

	def _align_title_vertical(self, horizontal_offset=0.0, vertical_offset=0.0):
		"""
		Internal function that aligns node label to the top of the node vertically.

		:param float horizontal_offset: extra horizontal offset.
		:param float vertical_offset: extra vertical offset.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		rect = self._title_item.boundingRect()
		x = self.boundingRect().right() + horizontal_offset
		y = self.boundingRect().center().y() - (rect.height() / 2) + vertical_offset
		self._title_item.setPos(x, y)

	def _align_sockets(self, vertical_offset=0.0):
		"""
		Internal function that aligns input and output socket views within node layout.

		:param float vertical_offset: extra vertical offset.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		if self.layout_direction == consts.GraphLayoutDirection.HORIZONTAL:
			self._align_sockets_horizontal(vertical_offset)
		elif self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			self._align_sockets_vertical(vertical_offset)
		else:
			raise RuntimeError('Node graph layout direction is not valid!')

	def _align_sockets_horizontal(self, vertical_offset=0.0):
		"""
		Internal function that aligns input and output socket views within node layout horizontally.

		:param float vertical_offset: extra vertical offset.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		width = self._width
		text_offset = consts.SOCKET_OFFSET - 2
		spacing = 1
		input_views = [input_view for input_view in self._input_views if input_view.isVisible()]
		if input_views:
			socket_width = input_views[0].boundingRect().width()
			socket_height = input_views[0].boundingRect().height()
			socket_x = (socket_width / 2) * -1
			socket_y = vertical_offset
			for input_view in input_views:
				input_view.setPos(socket_x, socket_y)
				socket_y += socket_height + spacing
		for socket_view, text_item in self._input_views.items():
			if socket_view.isVisible():
				text_x = socket_view.boundingRect().width() / 2 - text_offset
				text_item.setPos(text_x, socket_view.y() - 1.5)
		output_views = [output_view for output_view in self._output_views if output_view.isVisible()]
		if output_views:
			socket_width = output_views[0].boundingRect().width()
			socket_height = output_views[0].boundingRect().height()
			socket_x = width - (socket_width / 2)
			socket_y = vertical_offset
			for output_view in output_views:
				output_view.setPos(socket_x, socket_y)
				socket_y += socket_height + spacing
		for socket_view, text_item in self._output_views.items():
			if socket_view.isVisible():
				text_x = socket_view.x() - (text_item.boundingRect().width() - text_offset)
				text_item.setPos(text_x, socket_view.y() - 1.5)

	def _align_sockets_vertical(self, vertical_offset=0.0):
		"""
		Internal function that aligns input and output socket views within node layout vertically.

		:param float vertical_offset: extra vertical offset.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		input_views = [input_view for input_view in self._input_views if input_view.isVisible()]
		if input_views:
			socket_width = input_views[0].boundingRect().width()
			socket_height = input_views[0].boundingRect().height()
			half_width = socket_width / 2
			delta = self._width / (len(input_views) + 1)
			socket_x = delta
			socket_y = (socket_height / 2) * -1
			for input_view in input_views:
				input_view.setPos(socket_x - half_width, socket_y)
				socket_x += delta
		output_views = [output_view for output_view in self._output_views if output_view.isVisible()]
		if output_views:
			socket_width = output_views[0].boundingRect().width()
			socket_height = output_views[0].boundingRect().height()
			half_width = socket_width / 2
			delta = self._width / (len(output_views) + 1)
			socket_x = delta
			socket_y = self._height - (socket_height / 2)
			for output_view in output_views:
				output_view.setPos(socket_x - half_width, socket_y)
				socket_x += delta

	def _align_widgets(self, vertical_offset=0.0):
		"""
		Internal function that aligns node widgets to the default center of the node.

		:param float vertical_offset: extra vertical offset.
		:raises RuntimeError: if current node graph layout is not valid.
		"""

		if not self._widgets:
			return

		if self.layout_direction == consts.GraphLayoutDirection.HORIZONTAL:
			rect = self.boundingRect()
			y = rect.y() + vertical_offset
			input_views = [input_view for input_view in self._input_views if input_view.isVisible()]
			output_views = [output_view for output_view in self._output_views if output_view.isVisible()]
			for widget in self._widgets.values():
				widget_rect = widget.boundingRect()
				if not input_views:
					x = rect.left() + 10
					widget.widget().set_title_align('left')
				elif not output_views:
					x = rect.right() - widget_rect.width() - 10
					widget.widget().set_title_align('right')
				else:
					x = rect.center().x() - (widget_rect.width() / 2)
					widget.widget().set_title_align('center')
				widget.setPos(x, y)
				y += widget_rect.height()
		elif self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			rect = self.boundingRect()
			y = rect.center().y() + vertical_offset
			widget_height = 0.0
			for widget in self._widgets.values():
				widget_rect = widget.boundingRect()
				widget_height += widget_rect.height()
			y -= widget_height / 2
			for widget in self._widgets.values():
				widget_rect = widget.boundingRect()
				x = rect.center().x() - (widget_rect.width() / 2)
				widget.widget().set_title_align('center')
				widget.setPos(x, y)
				y += widget_rect.height()
		else:
			raise RuntimeError('Node graph layout direction is not valid!')

	def _draw_node_horizontal(self):
		"""
		Internal function that draws the node in the scene horizontally.
		"""

		height = self._title_item.boundingRect().height() + 4.0

		for input_view, text in self._input_views.items():
			text.setVisible(input_view.display_name)
		for output_view, text in self._output_views.items():
			text.setVisible(output_view.display_name)

		self._set_base_size(add_height=height)
		self._set_text_color(self.text_color)
		self._tooltip_disable(self.disabled)
		self._align_title()
		self._align_icon(horizontal_offset=2.0, vertical_offset=1.0)
		self._align_sockets(vertical_offset=height)
		self._align_widgets(vertical_offset=height)

		self.update()

	def _draw_node_vertical(self):
		"""
		Internal function that draws the node in the scene vertically.
		"""

		for _, text in self._input_views.items():
			text.setVisible(False)
		for _, text in self._output_views.items():
			text.setVisible(False)

		self._set_base_size()
		self._set_text_color(self.text_color)
		self._tooltip_disable(self.disabled)
		self._align_title(horizontal_offset=6.0)
		self._align_icon(horizontal_offset=6.0, vertical_offset=4.0)
		self._align_sockets()
		self._align_widgets()

		self.update()

	def _set_base_size(self, add_width=0.0, add_height=0.0):
		"""
		Internal function used to initialize node size while drawing it
		:param add_width: float, additional width
		:param add_height: float, additional height
		"""

		self._width = consts.NODE_WIDTH
		self._height = consts.NODE_HEIGHT
		new_width, new_height = self._calculate_size(add_width, add_height)
		if new_width > self._width:
			self._width = new_width
		if new_height > self._height:
			self._height = new_height

	def _set_text_color(self, color):
		"""
		Internal function that sets text color.

		:param tuple(int, int, int, int) color: RGBA color in 0 to 255 range.
		"""

		text_color = QColor(*color)
		for _, text in self._input_views.items():
			text.setDefaultTextColor(text_color)
		for _, text in self._output_views.items():
			text.setDefaultTextColor(text_color)
		self._title_item.setDefaultTextColor(text_color)

	def _tooltip_disable(self, flag):
		"""
		Internal function that updates the node tooltip with the node is enabled/disabled.

		:param bool flag: node disable state.
		"""

		tooltip = '<b>{}</b>'.format(self.name)
		if flag:
			tooltip += ' <font color="red"><b>(DISABLED)</b></font>'
		tooltip += '<br/>{}<br/>'.format(self.type)
		self.setToolTip(tooltip)

	def _add_socket(self, socket_view):
		"""
		Internal function that adds given socket view item into the node.

		:param SocketView socket_view: socket view item.
		:return: added socket view item.
		:rtype: SocketView
		"""

		text = QGraphicsTextItem(socket_view.name, self)
		text.font().setPointSize(8)
		text.setFont(text.font())
		text.setVisible(socket_view.display_name)
		text.setCacheMode(consts.ITEM_CACHE_MODE)
		if socket_view.direction == consts.SocketDirection.Input:
			self._input_views[socket_view] = text
		elif socket_view.direction == consts.SocketDirection.Output:
			self._output_views[socket_view] = text
		if self.scene():
			self.post_init()

		return socket_view

	def _delete_socket(self, socket_view, text_item):
		"""
		Internal function that removes socket view and socket text from current node.

		:param SocketView socket_view: socket view.
		:param QGraphicsTextItem text_item: node view text object.
		"""

		# socket_view.delete()
		socket_view.setParentItem(None)
		text_item.setParentItem(None)
		self.scene().removeItem(socket_view)
		self.scene().removeItem(text_item)
		del socket_view
		del text_item


class NodeTitle(QGraphicsTextItem, object):
	def __init__(self, text, parent=None):
		super(NodeTitle, self).__init__(text, parent)

		self.setFlags(QGraphicsItem.ItemIsFocusable)
		self.setCursor(Qt.IBeamCursor)
		self.setTextInteractionFlags(Qt.NoTextInteraction)
		self.setToolTip('double-click to edit node name.')
		self.set_editable(False)

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def node(self):
		"""
		Returns parent node item.

		:return: node item view.
		:rtype: NodeView
		"""

		return self.parentItem()

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def mouseDoubleClickEvent(self, event):
		"""
		Overrides base QGraphicsTextItem mouseDoubleClickEvent function.
		Jumps into edit mode when the user double-click on the node text.

		:param QGraphicsSceneMouseEvent event: mouse event.
		"""

		if event.button() == Qt.LeftButton:
			self.set_editable(True)
			event.ignore()
			return

		super(NodeTitle, self).mouseDoubleClickEvent(event)

	def keyPressEvent(self, event):
		"""
		Overrides base QGraphicsTextItem keyPressEvent function.
		Catch the return and escape keys when in edit mode.

		:param QKeyEvent event: key event.
		"""

		if event.key() == Qt.Key_Return:
			current_text =self.toPlainText()
			self.set_node_name(current_text)
			self.set_editable(False)
		elif event.key() == Qt.Key_Escape:
			self.setPlainText(self.node.name)
			self.set_editable(False)

		super(NodeTitle, self).keyPressEvent(event)

	def focusOutEvent(self, event):
		"""
		Overrides base QGraphicsTextItem focusOutEvent function.
		Jump out of edit mode.

		:param QFocusEvent event: focus event.
		"""

		current_text = self.toPlainText()
		self.set_node_name(current_text)
		self.set_editable(False)

		super(NodeTitle, self).focusOutEvent(event)

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def set_editable(self, flag):
		"""
		Sets text is editable.

		:param bool flag: True if text is editable; False otherwise.
		"""

		if flag:
			self.setTextInteractionFlags(Qt.TextEditable | Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
		else:
			self.setTextInteractionFlags(Qt.NoTextInteraction)
			cursor = self.textCursor()
			cursor.clearSelection()
			self.setTextCursor(cursor)

	def set_node_name(self, name):
		"""
		Updates the node name.

		:param str name: new node name.

		..note:: this function uses nodeNameChanged signal to rename the node (which also supports undo)
		"""

		if name == self.node.name:
			return
		viewer = self.node.viewer()
		if not viewer:
			return
		viewer.nodeNameChanged.emit(self.node.id, name)


class NodeDisabled(QGraphicsItem):
	def __init__(self, text=None, parent=None):
		super(NodeDisabled, self).__init__(parent)

		self.setZValue(consts.WIDGET_Z_VALUE + 2)
		self.setVisible(False)
		self._color = (0, 0, 0, 255)
		self._text = text

	# ==============================================================================================
	# PROPERTIES
	# ==============================================================================================

	@property
	def color(self):
		return self._color

	@property
	def text(self):
		return self._text

	# ==============================================================================================
	# OVERRIDES
	# ==============================================================================================

	def boundingRect(self):
		"""
		Overrides base QGraphicsItem boundingRect function.

		:return: bounding rect rectangle area.
		:rtype: QRectF
		"""

		return self.parentItem().boundingRect()

	def paint(self, painter, option, widget):
		"""
		Overrides base QGraphicsItem paint function.

		:param QPainter painter: painter used to draw the node.
		:param QStyleOption option: optional style.
		:param QWidget widget: optional widget.
		"""

		node_painters.disabled_node_painter(self, painter, option, widget)
