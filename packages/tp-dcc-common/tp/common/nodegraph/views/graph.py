#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains graph view implementation
"""

import math
from distutils.version import LooseVersion

from Qt import QtCore
from Qt.QtCore import Qt, Signal, QObject, QSize, QPoint, QPointF, QRect, QRectF, QMimeData
from Qt.QtWidgets import QMenuBar, QGraphicsView, QGraphicsTextItem, QRubberBand
from Qt.QtGui import QFont, QColor, QPainter, QPainterPath, QKeySequence

from tp.common.python import helpers
from tp.common.math import scalar
from tp.common.nodegraph.core import consts, utils
from tp.common.nodegraph.widgets import scene, actions, autopanner, tabsearch, dialogs
from tp.common.nodegraph.views import (
	node as node_view, socket as socket_view, connector as connector_view, backdrop as backdrop_view
)


class NodeGraphView(QGraphicsView):
	"""
	Widget used to display the scene and the nodes within it.
	"""

	nodeSelected = Signal(str)
	nodesMoved = Signal(dict)
	nodeDoubleClicked = Signal(str)
	nodesSelectionChanged = Signal(list, list)
	connectionChanged = Signal(list, list)
	connectionSliced = Signal(list)
	nodeNameChanged = Signal(str, str)
	nodeBackdropUpdated = Signal(object, str, dict)
	searchTriggered = Signal(str, tuple)
	dataDropped = Signal(QMimeData, QPoint)

	def __init__(self, undo_stack=None, parent=None):
		super(NodeGraphView, self).__init__(parent=parent)

		self.setScene(scene.NodeGraphScene(parent=self))

		self.setRenderHint(QPainter.Antialiasing, True)
		self.setRenderHint(QPainter.TextAntialiasing, True)             # NOTE: this is expensive
		self.setRenderHint(QPainter.HighQualityAntialiasing, True)      # NOTE: this is expensive
		self.setRenderHint(QPainter.SmoothPixmapTransform, True)        # NOTE: this is expensive
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
		self.setCacheMode(QGraphicsView.CacheBackground)
		self.setOptimizationFlag(QGraphicsView.DontAdjustForAntialiasing)
		self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
		# self.setDragMode(QGraphicsView.RubberBandDrag)
		self.setAttribute(Qt.WA_AlwaysShowToolTips)
		self.setAcceptDrops(True)
		self.resize(850, 800)

		self._num_lods = 5
		self._acyclic = True
		self._connector_collision = False
		self._left_mouse_button_state = False							# cache left mouse button press status.
		self._right_mouse_button_state = False							# cache right mouse button press status.
		self._middle_mouse_button_state = False							# cache middle mouse button press status.
		self._alt_state = False
		self._ctrl_state = False
		self._shift_state = False
		self._current_pressed_key = None
		self._origin_mouse_pos = QPointF(0.0, 0.0)                            # origin position when user click on the scene.
		self._mouse_pos = QPointF(0.0, 0.0)                             # current mouse position.
		self._prev_mouse_pos = QPointF(self.width(), self.height())     # previous click operation mouse position.
		self._colliding_state = False
		self._minimum_zoom = consts.NodeGraphViewStyle.MINIMUM_ZOOM
		self._maximum_zoom = consts.NodeGraphViewStyle.MAXIMUM_ZOOM
		self._prev_selection_nodes = list()
		self._prev_selection_connectors = list()
		self._node_positions = dict()
		self._start_socket = None
		self._detached_socket = None
		self._over_slicer_connectors = list()
		self._connector_layout = consts.ConnectorLayoutStyles.CURVED
		self._layout_direction = consts.GraphLayoutDirection.HORIZONTAL

		self._scene_rect = QRectF(0, 0, self.size().width(), self.size().height())

		self._rubber_band = QRubberBand(QRubberBand.Rectangle, self)
		self._rubber_band.isActive = False

		self._graph_label = GraphTitleLabel()
		self._graph_label.setFlags(QGraphicsTextItem.ItemIgnoresTransformations)
		self._graph_label.setDefaultTextColor(QColor(255, 255, 255, 50))
		self._graph_label.setFont(QFont('Impact', 20, 1))
		self._graph_label.setZValue(5)

		self._realtime_line = connector_view.RealtimeConnector()
		self._realtime_line.setVisible(False)

		self._slicer_line = connector_view.ConnectorSlicer()
		self._slicer_line.setVisible(False)

		self._search_widget = tabsearch.TabSearchMenuWidget()
		self._search_widget.searchSubmitted.connect(self._on_search_submitted)

		# workaround to use shortcuts from the non-native menu actions.
		# do not use setVisible(False) because shortcuts will not work.
		self._context_menu_bar = QMenuBar(self)
		self._context_menu_bar.setNativeMenuBar(False)
		self._context_menu_bar.setMaximumSize(0, 0)

		self._context_graph_menu = actions.BaseMenu('NodeGraph', self)
		self._context_nodes_menu = actions.BaseMenu('Nodes', self)

		self._auto_panner = autopanner.AutoPanner()

		self._nodes_searcher = None

		self.scene().addItem(self._graph_label)
		self.scene().addItem(self._slicer_line)
		self._update_scene()
		self._last_size = self.size()

		self._graph_label.setPlainText('BUILDER')

		self._undo_action = None
		self._redo_action = None
		if undo_stack:
			self._undo_action = undo_stack.createUndoAction(self, '&Undo')
			self._redo_action = undo_stack.createRedoAction(self, '&Redo')

		self._build_context_menus()

	def __repr__(self):
		return '<{}() object at {}>'.format(self.__class__.__name__, hex(id(self)))

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def focusInEvent(self, event):
		"""
		Overrides base focusInEvent.

		:param QEvent event: focus in event.
		"""

		# populate qmenubar so qactions should not conflict with parent existing DCC app.
		self._context_menu_bar.addMenu(self._context_graph_menu)
		self._context_menu_bar.addMenu(self._context_nodes_menu)
		return super(NodeGraphView, self).focusInEvent(event)

	def focusOutEvent(self, event):
		"""
		Overrides base focusOutEvent.

		:param QEvent event: focus in event.
		"""

		# clear qmenubar so qactions should not conflict with parent existing DCC app.
		self._context_menu_bar.clear()
		return super(NodeGraphView, self).focusOutEvent(event)

	def scale(self, scale_x, scale_y, pos=None):
		"""
		Overrides base scale function to scale view taking into account current scene rectangle.

		:param float scale_x: scale in X coordinate.
		:param float scale_y: scale in Y coordinate.
		:param QPointF pos: position from where the scaling is applied.
		:return:
		"""

		scale = [scale_x, scale_y]
		center = pos or self._scene_rect.center()
		width = self._scene_rect.width() / scale[0]
		height = self._scene_rect.height() / scale[1]
		self._scene_rect = QRectF(
			center.x() - (center.x() - self._scene_rect.left()) / scale[0],
			center.y() - (center.y() - self._scene_rect.top()) / scale[1], width, height)
		self._update_scene()

	def resizeEvent(self, event):
		"""
		Overrides base resizeEvent function to update view zoom when view is resized.

		:param QEvent event: Qt resize event.
		"""

		width = self.size().width()
		height = self.size().height()

		# make sure that width and height are not 0.
		# if that's the scale we automatically resize view to last valid size.
		if 0 in [width, height]:
			self.resize(self._last_size)

		delta = max(width / self._last_size.width(), height / self._last_size.height())
		self._set_zoom(delta, sensitivity=None)
		self._last_size = self.size()

		super(NodeGraphView, self).resizeEvent(event)

	def mousePressEvent(self, event):
		"""
		Overrides base mousePressEvent function to handle graph viewer behaviour when user presses a mouse button.

		:param QEvent event: Qt mouse press event.
		"""

		if event.button() == Qt.LeftButton:
			self._left_mouse_button_state = True
		if event.button() == Qt.RightButton:
			self._right_mouse_button_state = True
		if event.button() == Qt.MiddleButton:
			self._middle_mouse_button_state = True

		self._origin_mouse_pos = event.pos()
		self._prev_mouse_pos = event.pos()
		self._prev_selection_nodes, self._prev_selection_connectors = self.selected_items()

		if self._search_widget.isVisible():
			self.tab_search_toggle()

		map_pos = self.mapToScene(event.pos())

		slicer_mode = all([self._alt_state, self._shift_state, self._left_mouse_button_state])
		if slicer_mode:
			self._slicer_line.draw_path(map_pos, map_pos)
			self._slicer_line.setVisible(True)
			return

		# If we are panning we ignore mouse press event
		if self._alt_state:
			return

		items = self._find_items_near_scene_pos(map_pos, None, 20, 20)
		nodes = [item for item in items if isinstance(item, node_view.BaseNodeView)]
		if nodes:
			self._middle_mouse_button_state = False

		if self._left_mouse_button_state:
			if self._shift_state:
				for node in nodes:
					node.selected = not node.selected
			elif self._ctrl_state:
				for node in nodes:
					node.selected = False

		self._node_positions.update({n: n.xy_pos for n in self.selected_nodes()})

		# Show selection rubber band
		if self._left_mouse_button_state and not items:
			rect = QRect(self._prev_mouse_pos, QSize()).normalized()
			map_rect = self.mapToScene(rect).boundingRect()
			self.scene().update(map_rect)
			self._rubber_band.setGeometry(rect)
			self._rubber_band.isActive = True

		if self._left_mouse_button_state and (self._shift_state or self._ctrl_state):
			return

		if not self._realtime_line.isVisible():
			super(NodeGraphView, self).mousePressEvent(event)

	def mouseMoveEvent(self, event):
		"""
		Overrides base mouseMoveEvent function to handle graph viewer behaviour when user presses a mouse button.

		:param QEvent event: Qt mouse move event.
		"""

		if self._alt_state and self._shift_state:
			if self._left_mouse_button_state and self._slicer_line.isVisible():
				p1 = self._slicer_line.path().pointAtPercent(0)
				p2 = self.mapToScene(self._prev_mouse_pos)
				self._slicer_line.draw_path(p1, p2)
				self._slicer_line.show()
				self._connectors_ready_to_slice(self._slicer_line.path())
			self._prev_mouse_pos = event.pos()
			super(NodeGraphView, self).mouseMoveEvent(event)
			return

		if self._middle_mouse_button_state and self._alt_state:
			pos_x = (event.x() - self._prev_mouse_pos.x())
			zoom = 0.1 if pos_x > 0 else -0.1
			self._set_zoom(zoom, 0.05, pos=event.pos())
		elif self._middle_mouse_button_state or (self._left_mouse_button_state and self._alt_state):
			previous_pos = self.mapToScene(self._prev_mouse_pos)
			current_pos = self.mapToScene(event.pos())
			delta = previous_pos - current_pos
			self._set_pan(delta.x(), delta.y())

		if self._left_mouse_button_state and self._rubber_band.isActive:
			rect = QRect(self._origin_mouse_pos, event.pos()).normalized()
			if max(rect.width(), rect.height()) > 5:
				if not self._rubber_band.isVisible():
					self._rubber_band.show()
				map_rect = self.mapToScene(rect).boundingRect()
				path = QPainterPath()
				path.addRect(map_rect)
				self._rubber_band.setGeometry(rect)
				self.scene().setSelectionArea(path, Qt.IntersectsItemShape)
				self.scene().update(map_rect)
				if self._shift_state or self._ctrl_state:
					node_views, connector_views = self.selected_items()
					for _node_view in self._prev_selection_nodes:
						_node_view.selected = True
					if self._ctrl_state:
						for _connector_view in connector_views:
							_connector_view.setSelected(False)
						for _node_view in node_views:
							_node_view.selected = False
		elif self._left_mouse_button_state:
			self._colliding_state = False
			node_views, connector_views = self.selected_items()
			if len(node_views) == 1:
				_node_view = node_views[0]
				[_connector_view.setSelected(False) for _connector_view in connector_views]
				if self._connector_collision:
					colliding_connectors = [i for i in _node_view.collidingItems() if isinstance(
						i, connector_view.ConnectorView) and i.isVisible()]
					for colliding_connector in colliding_connectors:
						if not colliding_connector.input_socket:
							continue
						socket_node_check = all(
							[not colliding_connector.input_socket.node is _node_view,
							 not colliding_connector.output_socket.nodee is _node_view])
						if socket_node_check:
							colliding_connector.setSelected(True)
							self._colliding_state = True
							break


		self._prev_mouse_pos = event.pos()

		super(NodeGraphView, self).mouseMoveEvent(event)

	def mouseReleaseEvent(self, event):
		"""
		Overrides base mouseReleaseEvent function to handle graph viewer behaviour when user releases a mouse button.

		:param QEvent event: Qt mouse release event.
		"""

		self._auto_panner.stop()

		if event.button() == Qt.LeftButton:
			self._left_mouse_button_state = False
		if event.button() == Qt.RightButton:
			self._right_mouse_button_state = False
		if event.button() == Qt.MiddleButton:
			self._middle_mouse_button_state = False

		if self._slicer_line.isVisible():
			self._connectors_sliced(self._slicer_line.path())
			self._slicer_line.draw_path(QPointF(0.0, 0.0), QPointF(0.0, 0.0))
			self._slicer_line.setVisible(False)

		# Hide selection rubber band
		if self._rubber_band.isActive:
			self._rubber_band.isActive = False
			if self._rubber_band.isVisible():
				rect = self._rubber_band.rect()
				map_rect = self.mapToScene(rect).boundingRect()
				self._rubber_band.hide()
				rect = QRect(self._origin_mouse_pos, event.pos()).normalized()
				rect_items = self.scene().items(self.mapToScene(rect).boundingRect())
				node_ids = list()
				for item in rect_items:
					if isinstance(item, node_view.BaseNodeView):
						node_ids.append(item.id)
				if node_ids:
					prev_ids = [n.id for n in self._prev_selection_nodes if not n.selected]
					self.nodeSelected.emit(node_ids[0])
					self.nodesSelectionChanged.emit(node_ids, prev_ids)
				self.scene().update(map_rect)
				return

		# find position changed nodes and emit signal only if node is not colliding with a connector
		moved_nodes = {n: xy_pos for n, xy_pos in self._node_positions.items() if n.xy_pos != xy_pos}
		if moved_nodes and not self._colliding_state:
			self.nodesMoved.emit(moved_nodes)
		self._node_positions.clear()

		node_views, connector_views = self.selected_items()
		if self._colliding_state and node_views and connector_views:
			self.insertNode.emit(connector_views[0], node_views[0].id, moved_nodes)

		prev_ids = [n.id for n in self._prev_selection_nodes if not n.selected]
		node_ids = [n.id for n in node_views if n not in self._prev_selection_nodes]
		self.nodesSelectionChanged.emit(node_ids, prev_ids)

		super(NodeGraphView, self).mouseReleaseEvent(event)

	def keyPressEvent(self, event):
		"""
		Overrides base keyPressEvent function to handle graph viewer behaviour when user presses a keyboard button.

		:param QEvent event: Qt keyboard press event.
		"""

		modifiers = event.modifiers()

		self._alt_state = modifiers == Qt.AltModifier
		self._ctrl_state = modifiers == Qt.ControlModifier
		self._shift_state = modifiers == Qt.ShiftModifier

		if modifiers == (Qt.AltModifier | Qt.ShiftModifier):
			self._alt_state = True
			self._shift_state = True

		super(NodeGraphView, self).keyPressEvent(event)

	def keyReleaseEvent(self, event):
		"""
		Overrides base keyReleaseEvent function to handle graph viewer behaviour when user releases a keyboard button.

		:param QEvent event: Qt keyboard release event.
		"""

		modifiers = event.modifiers()

		self._alt_state = modifiers == Qt.AltModifier
		self._ctrl_state = modifiers == Qt.ControlModifier
		self._shift_state = modifiers == Qt.ShiftModifier

		super(NodeGraphView, self).keyReleaseEvent(event)

	def wheelEvent(self, event):
		"""
		Overrides base wheelEvent function. Allow users to scale view zoom using mouse wheel.

		:param QEvent event: Qt wheel event.

		..note:: zoom is done based on the location of the cursor inside the view.
		"""

		# this is to support older PySide/PyQt versions
		try:
			delta = event.delta()
		except AttributeError:
			delta = event.angleDelta().y()
			if delta == 0:
				delta = event.angleDelta().x()

		self._set_zoom(delta, pos=event.pos())

		super(NodeGraphView, self).wheelEvent(event)

	def dragEnterEvent(self, event):
		"""
		Overrides base dragEnterEvent function to allow dragging nodes from custom UIs.

		:param QEvent event: Qt drag enter event.
		"""

		if event.mimeData().hasFormat('text/uri-list'):
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		"""
		Overrides base dragMoveEvent function to allow dragging nodes from custom UIs.

		:param QEvent event: Qt drag move event.
		"""

		if event.mimeData().hasFormat('text/uri-list'):
			event.accept()
		else:
			event.ignore()

	def dragLeaveEvent(self, event):
		"""
		Overrides base dragLeaveEvent function to allow dragging nodes from custom UIs.

		:param QEvent event: Qt drag leave event.
		"""

		event.ignore()

	def dropEvent(self, event):
		"""
		Overrides base dropEvent function to allow dropping nodes from custom UIs.

		:param QEvent event: Qt drop event.
		"""

		pos = self.mapToScene(event.pos())
		event.setDropAction(Qt.CopyAction)
		self.dataDropped.emit(event.mimeData(), QPoint(pos.x(), pos.y()))

	def contextMenuEvent(self, event):
		"""
		Overrides base contextMenuEvent function to show the graph or nodes context menu based on current selection.

		:param QEvent event: context menu event.
		"""

		self._right_mouse_button_state = False

		context_menu = None
		context_menus = self.context_menus()

		if context_menus['nodes'].isEnabled():
			items = self._find_items_near_scene_pos(self.mapToScene(self._prev_mouse_pos))
			nodes = [i for i in items if isinstance(i, node_view.BaseNodeView)]
			if nodes:
				node = nodes[0]
				context_menu = context_menus['nodes'].get_menu(node.type, node.id)
				if context_menu:
					for action in context_menu.actions():
						if not action.menu():
							action.node_id = node.id

		context_menu = context_menu or context_menus['graph']
		if len(context_menu.actions()) > 0:
			if context_menu.isEnabled():
				context_menu.exec_(event.globalPos())
			else:
				return super(NodeGraphView, self).contextMenuEvent(event)

		return super(NodeGraphView, self).contextMenuEvent(event)

	def drawBackground(self, painter, rect):
		"""
		Overrides base drawBackground function to ensure that graph label is always located in the top left corner
		of the view.

		:param QPainter painter: painter used to draw the view background.
		:param QRect rect: rectangle that defines view background area.
		"""

		super(NodeGraphView, self).drawBackground(painter, rect)
		polygon = self.mapToScene(self.viewport().rect())
		self._graph_label.setPos(polygon[0])

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def layout_direction(self):
		"""
		Returns  the layout direction set on the node graph viewer.

		:return: graph layout direction.
		:rtype: int
		"""

		return self._layout_direction

	def set_layout_direction(self, direction):
		"""
		Sets the node graph viewer layout direction.
			* 0: horizontal.
			* 1: vertical

		:param int direction: graph layout direction.
		"""

		self._layout_direction = direction
		for connector_view in self.all_connectors():
			connector_view.draw_path(connector_view.input_socket, connector_view.output_socket)

	def get_zoom(self):
		"""
		Returns the zoom level currently applied to this graph view.

		:return: graph view zoom level.
		:rtype: float
		"""

		transform = self.transform()
		current_scale = (transform.m11(), transform.m22())
		return float('{:0.2f}'.format(current_scale[0] - 1.0))

	def set_zoom(self, value=0.0):
		"""
		Sets the viewer zoom level.

		:param float value: zoom level.
		"""

		if value == 0.0:
			self.reset_zoom()
			return

		zoom = self.get_zoom()
		if zoom < 0.0:
			if not self._minimum_zoom <= zoom <= self._maximum_zoom:
				return
		else:
			if not self._minimum_zoom <= value <= self._maximum_zoom:
				return
		value = value - zoom
		self._set_zoom(value, 0.0)

	def zoom_in(self):
		"""
		Sets the node graph zoom in by 0.1.
		"""

		zoom = self.get_zoom() + 100
		self._set_zoom(zoom)

	def zoom_out(self):
		"""
		Sets the node graph zoom out by 0.1.
		"""

		zoom = self.get_zoom() - 100
		self._set_zoom(zoom)

	def zoom_to_nodes(self, nodes):
		"""
		Zoom viewer to given nodes.

		:param list(BaseNodeView) nodes: list of node views to zoom on.
		"""

		self._scene_rect = self._combined_rect(nodes)
		self._update_scene()
		if self.get_zoom() > 0.1:
			self.reset_zoom(self._scene_rect.center())

	def reset_zoom(self, center=None):
		"""
		Resets the viewer zoom level based on the given center point.

		:param QPoint center: optional zoom center point.
		"""

		self._scene_rect = QRectF(0, 0, self.size().width(), self.size().height())
		if center:
			self._scene_rect.translate(center - self._scene_rect.center())

		self._update_scene()

	def center_selection(self, nodes=None):
		"""
		Center on the given node views or all nodes by default.

		:param list[tp.common.nodegraph.views.node.BaseNodeView] nodes: list of node views.
		"""

		if not nodes:
			if self.selected_nodes():
				nodes = self.selected_nodes()
			elif self.all_nodes():
				nodes = self.all_nodes()
			if not nodes:
				return

		if len(nodes) == 1:
			self.centerOn(nodes[0])
		else:
			rect = self._combined_rect(nodes)
			self.centerOn(rect.center().x(), rect.center().y())

	def force_update(self):
		"""
		Redraws the current node graph scene.
		"""

		self._update_scene()

	def get_current_view_scale(self):
		"""
		Returns current transform scale of the graph view.

		:return: transform scale.
		"""

		return self.transform().m22()

	def reset_scale(self):
		"""
		Resets current transform scale of the graph view.
		"""

		self.resetMatrix()

	def nodes_rect_center(self, nodes):
		"""
		Returns the center X, Y pos from the given nodes.

		:param list[tp.common.nodegraph.views.node.BaseNodeView] nodes: list of node views.
		:return: X, Y center position.
		:rtype: list(float, float)
		"""

		center = self._combined_rect(nodes).center()
		return [center.x(), center.y()]

	def get_lod_value_from_scale(self, scale=None):
		"""
		Returns the current view LOD value taking into account view scale.

		:param scale: float or None, scale to get LOD of. If not given, current view scale will be used instead.
		:return: int, lod index
		"""

		scale = scale if scale is not None else self.get_current_view_scale()
		scale_percentage = scalar.get_range_percentage(self._minimum_zoom, self._maximum_zoom, scale)
		lod = scalar.lerp(self._num_lods, 1, scale_percentage)
		return int(round(lod))

	def selected_items(self):
		"""
		Returns selected items in the scene.

		:return: list of selected items.
		:rtype: list[tp.common.nodegraph.views.node.BaseNodeView or tp.common.nodegraph.views.connector.ConnectorView]
		"""

		node_views = list()
		connector_views = list()
		for item in self.scene().selectedItems():
			if isinstance(item, node_view.BaseNodeView):
				node_views.append(item)
			elif isinstance(item, connector_view.ConnectorView):
				connector_views.append(item)

		return node_views, connector_views

	def establish_connection(self, start_socket, end_socket):
		"""
		Establishes a new connection between the two given socket views.

		:param tp.common.nodegraph.views.socket.SocketView start_socket: start socket view.
		:param tp.common.nodegraph.views.socket.SocketView end_socket: end socket view.
		"""

		new_connector = connector_view.ConnectorView()
		self.scene().addItem(new_connector)
		new_connector.set_connections(start_socket, end_socket)
		new_connector.draw_path(new_connector.input_socket, new_connector.output_socket)
		if start_socket.node.selected or end_socket.node.selected:
			new_connector.highlight()
		if not start_socket.node.visible or not end_socket.node.visible:
			new_connector.hide()

	def tab_search_set_nodes(self, nodes):
		"""
		Sets the node names for the tab search to use.

		:param dict nodes: list of nodes to show in the search widget.
		"""

		self._search_widget.set_nodes(nodes)

	def tab_search_toggle(self):
		"""
		Toggles search widget visibility.
		"""

		state = self._search_widget.isVisible()
		if not state:
			self._search_widget.setVisible(state)
			self.setFocus()
			return

		pos = self._prev_mouse_pos
		rect = self._search_widget.rect()
		new_pos = QPoint(int(pos.x() - rect.width() / 2), int(pos.y() - rect.height() / 2))
		self._search_widget.move(new_pos)
		self._search_widget.setVisible(state)
		self._search_widget.setFocus()

		rect = self.mapToScene(rect).boundingRect()
		self.scene().update(rect)

	def rebuild_tab_search(self):
		"""
		Marks tab search to be rebuild.
		"""

		if self._search_widget:
			self._search_widget.rebuild = True

	def context_menus(self):
		"""
		Returns dictionary with the different available context menus for this graph view.

		:return: context menus mapping dictionary.
		:rtype: dict
		"""

		return {'graph': self._context_graph_menu, 'nodes': self._context_nodes_menu}

	# =================================================================================================================
	# SCENE EVENTS
	# =================================================================================================================

	def sceneMousePressEvent(self, event):
		"""
		viewer scene mouse press event. Takes priority over viewer event.

		:param QEvent event: Qt mouse event.
		"""

		# connector slicer or viewer pan mode enabled
		if self._alt_state or (self._alt_state and self._shift_state):
			return

		if self._realtime_line.isVisible():
			self._apply_realtime_connection(event)
			return

		pos = event.scenePos()
		items = self._find_items_near_scene_pos(pos, None, 5, 5)

		# filter from the selection stack in the following order
		# "node, port, pipe" this is to avoid selecting items under items.
		node, socket, connector = None, None, None
		for item in items:
			if isinstance(item, node_view.BaseNodeView):
				node = item
			elif isinstance(item, socket_view.SocketView):
				socket = item
			elif isinstance(item, connector_view.ConnectorView):
				connector = item
			if any([node, socket, connector]):
				break

		if socket:
			if socket.locked:
				return
			if not socket.multi_connection and socket.connected_sockets:
				self._detached_socket = socket.connected_sockets[0]
			self._start_realtime_connection(socket)
			if not socket.multi_connection:
				[socket_to_delete.delete() for socket_to_delete in socket.connectors]
			return

		if node:
			node_views = self._find_items_near_scene_pos(pos, node_view.BaseNodeView, 3, 3)
			for node_item in node_views:
				self._node_positions[node_item] = node_item.xy_pos
			if event.button() == Qt.LeftButton:
				self.nodeSelected.emit(node.id)
			if not isinstance(node, backdrop_view.BackdropNodeView):
				return

		if connector:
			if not self._left_mouse_button_state:
				return
			from_socket = connector.socket_from_pos(pos, True)
			if from_socket.locked:
				return
			from_socket.hovered = True
			attr = {consts.SocketDirection.Input: 'output_socket', consts.SocketDirection.Output: 'input_socket'}
			self._detached_socket = getattr(connector, attr[from_socket.direction])
			self._start_realtime_connection(from_socket)
			self._realtime_line.draw_path(self._start_socket, cursor_pos=pos)
			if self._shift_state:
				self._realtime_line.shift_selected = True
				return
			connector.delete()

	def sceneMouseMoveEvent(self, event):
		"""
		viewer scene mouse move event. Takes priority over viewer event.

		:param QEvent event: Qt mouse event.
		"""

		if not self._realtime_line.isVisible() or not self._start_socket:
			return

		pos = self.mapFromScene(event.scenePos())
		mouse_rect = QRect(QPoint(pos.x() - 3, pos.y() - 2), QPoint(pos.x() + 3, pos.y() + 2))
		hover_items = self.items(mouse_rect)
		hovered_sockets = [hover_item for hover_item in hover_items if isinstance(hover_item, socket_view.SocketView)]
		ports_can_be_connected = False
		if hovered_sockets and self._start_socket:
			hovered_socket = hovered_sockets[0]
			ports_can_be_connected = utils.can_connect_ports(self._start_socket, hovered_socket)
			if ports_can_be_connected:
				self._realtime_line.draw_path(self._start_socket, hovered_socket)

		if not ports_can_be_connected:
			pos = event.scenePos()
			self._realtime_line.draw_path(self._start_socket, cursor_pos=pos)

	def sceneMouseReleaseEvent(self, event):
		"""
		viewer scene mouse release event. Takes priority over viewer event.

		:param QEvent event: Qt mouse event.
		"""

		if event.button() != Qt.MiddleButton:
			self._apply_realtime_connection(event)

	# ==================================================================================================================
	# NODES
	# ==================================================================================================================

	def add_node(self, node, pos=None):
		"""
		Adds a new node view item into the graph scene.

		:param BaseNodeView node: node item instance.
		:param tuple(float, float) pos: node scene position.
		"""

		pos = pos or (self._prev_mouse_pos.x(), self._prev_mouse_pos.y())
		node.pre_init(self, pos)
		self.scene().addItem(node)
		node.post_init(self, pos)

	def move_nodes(self, nodes, pos=None, offset=None):
		"""
		Moves globally given nodes.

		:param list[tp.common.nodegraph.views.node.BaseNodeView] nodes: node views to move.
		:param tuple or list or None pos: optional custom X, Y position.
		:param tuple or list or None offset: optional X, Y position offset.
		"""

		group = self.scene().createItemGroup(nodes)
		group_rect = group.boundingRect()
		if pos:
			x, y = pos
		else:
			pos = self.mapToScene(self._prev_mouse_pos)
			x = pos.x() - group_rect.center().x()
			y = pos.y() - group_rect.center().y()
		if offset:
			x += offset[0]
			y += offset[1]
		group.setPos(x, y)
		self.scene().destroyItemGroup(group)

	def get_all_nodes(self, filtered_classes=None):
		"""
		Returns all nodes in current graph.

		:param filtered_classes: If given, only nodes with given classes will be taken into account
		:return: all node views within the scene.
		:rtype: list(BaseNodeView)
		"""

		all_nodes = list()
		current_scene = self.scene()
		if not current_scene:
			return all_nodes

		filtered_classes = helpers.force_list(filtered_classes or [node_view.BaseNodeView])
		if node_view.BaseNodeView not in filtered_classes:
			filtered_classes.append(node_view.BaseNodeView)
		filtered_classes = helpers.force_tuple(filtered_classes)

		for item_view in current_scene.items():
			if not item_view or not isinstance(item_view, filtered_classes):
				continue
			all_nodes.append(item_view)

		return all_nodes

	def selected_nodes(self, filtered_classes=None):
		"""
		Returns current selected nodes in view. Allows the filtering of specific node classes.

		:param list(class) filtered_classes: list of node classes we want to filter by.
		:return:  list of selected node views.
		:rtype: list(BaseNodeView)
		"""

		selected_nodes = list()

		# if no scene is available, no nodes can be selected
		current_scene = self.scene()
		if not current_scene:
			return selected_nodes

		filtered_classes = helpers.force_list(filtered_classes or [node_view.BaseNodeView])
		if node_view.BaseNodeView not in filtered_classes:
			filtered_classes.append(node_view.BaseNodeView)
		filtered_classes = helpers.force_tuple(filtered_classes)

		for item in current_scene.selectedItems():
			if not item or not isinstance(item, filtered_classes):
				continue
			selected_nodes.append(item)

		return selected_nodes

	# ==================================================================================================================
	# CONNECTORS
	# ==================================================================================================================

	def connector_layout(self):
		"""
		Returns the connector layout mode.

		:return: connector layout mode.
		:rtype: int
		"""

		return self._connector_layout

	def set_connector_layout(self, mode):
		"""
		Sets the connector layout mode and redraw all connectors in the scene. Available modes are:
			* 0: straight.
			* 1: curve.
			* 2: angle.

		:param int mode: connector layout mode.
		"""

		self._connector_layout = mode
		for connector in self.all_connectors():
			connector.draw_path(connector.input_socket, connector.output_socket)

	def selected_connectors(self):
		"""
		Returns selected connector views.

		:return: list of selected connector views.
		:rtype: list[tp.common.nodegraph.views.connector.ConnectorView]
		"""

		return [i for i in self.scene().selectedItems() if isinstance(i, connector_view.ConnectorView)]

	def all_connectors(self):
		"""
		Returns all connector views.

		:return: list of connector views.
		:rtype: list[tp.common.nodegraph.views.connector.ConnectorView]
		"""

		excluded_connectors = [self._realtime_line, self._slicer_line]
		return [i for i in self.scene().items() if isinstance(
			i, connector_view.ConnectorView) and i not in excluded_connectors]

	# ==================================================================================================================
	# DIALOGS
	# ==================================================================================================================

	def question_dialog(self, text, title='Node Graph'):
		"""
		Prompts a question dialog with "Yes" and "No" buttons in the node graph.

		:param str text: question text.
		:param str title: dialog window title.
		:return: True if "Yes" button was pressed; False otherwise.
		:rtype: bool
		"""

		self._clear_key_state()
		return dialogs.question_dialog(text, title)

	def message_dialog(self, text, title='Node Graph'):
		"""
		Prompts a message dialog in the node graph.

		:param str text: message text.
		:param str title: dialog window title.
		"""

		self._clear_key_state()
		dialogs.message_dialog(text, title)

	def load_dialog(self, current_directory=None, ext=None):
		"""
		Prompts a file open dialog in the node graph.

		:param str or None current_directory: optional path to a directory.
		:param str or NOne ext: optional custom file extension.
		:return: selected file path.
		:rtype: str
		"""

		self._clear_key_state()
		ext = '*{} '.format(ext) if ext else ''
		ext_filter = ';;'.join(['Node Graph ({}*json)'.format(ext), 'All Files (*)'])
		file_dlg = dialogs.get_open_filename(self, 'Open File', current_directory, ext_filter)
		file_path = file_dlg[0] or ''

		return file_path

	def save_dialog(self, current_directory=None, ext=None):
		"""
		Prompts a save file dialog in the node graph.

		:param str or None current_directory: optional path to a directory.
		:param str or NOne ext: optional custom file extension.
		:return: saved file path.
		:rtype: str
		"""

		self._clear_key_state()
		ext_label = '*{} '.format(ext) if ext else ''
		ext_type = '.{}'.format(ext) if ext else '.json'
		ext_map = {'Node Graph ({}*json)'.format(ext_label): ext_type, 'All Files (*)': ''}
		file_dlg = dialogs.get_save_filename(self, 'Save Session', current_directory, ';;'.join(ext_map.keys()))
		file_path = file_dlg[0]
		if not file_path:
			return ''
		ext = ext_map[file_dlg[1]]
		if ext and not file_path.endswith(ext):
			file_path += ext

		return file_path

	# =================================================================================================================
	# INTERNAL
	# =================================================================================================================

	def _build_context_menus(self):
		"""
		Internal function that builds the context menus for this graph view.
		"""

		self._context_nodes_menu.setEnabled(False)
		self._context_menu_bar.addMenu(self._context_graph_menu)
		self._context_menu_bar.addMenu(self._context_nodes_menu)

		if self._undo_action and self._redo_action:
			self._undo_action.setShortcuts(QKeySequence.Undo)
			self._redo_action.setShortcuts(QKeySequence.Redo)
			if LooseVersion(QtCore.qVersion()) >= LooseVersion('5.10'):
				self._undo_action.setShortcutVisibleInContextMenu(True)
				self._redo_action.setShortcutVisibleInContextMenu(True)
			self._context_graph_menu.addAction(self._undo_action)
			self._context_graph_menu.addAction(self._redo_action)
			self._context_graph_menu.addSeparator()

	def _update_scene(self):
		"""
		Internal function that forces redraw of the scene.
		"""

		self.setSceneRect(self._scene_rect)
		self.fitInView(self._scene_rect, Qt.KeepAspectRatio)

	def _set_zoom(self, value, sensitivity=0.0, pos=None):
		"""
		Internal function that sets the zoom of the graph view.

		:param float value: zoom value.
		:param float or None sensitivity: zoom sensitivity value.
		:param QPointF pos: position from where the zoom is applied.
		"""

		# if zoom position is given, we make sure to convert to scene coordinates
		if pos:
			pos = self.mapToScene(pos)

		# if no sensitivity given we just scale the view
		if sensitivity is None:
			scale = 1.001 ** value
			self.scale(scale, scale, pos)
			return

		# if not zoom value given we just skip zoom operation
		if value == 0.0:
			return

		# scale view taking into account the minimum and maximum levels
		scale = (0.9 + sensitivity) if value < 0.0 else (1.1 - sensitivity)
		zoom = self.get_zoom()

		if self._minimum_zoom >= zoom:
			if scale == 0.9:
				return
		if self._maximum_zoom <= zoom:
			if scale == 1.1:
				return

		self.scale(scale, scale, pos)

	def _set_pan(self, pos_x, pos_y):
		"""
		Internal function that sets the panning of the graph view
		:param pos_x: QPointF
		:param pos_y: QPointF
		:return:
		"""

		# speed = self._scene_rect.width() * 0.0015
		# x = -pos_x * speed
		# y = -pos_y * speed
		# self._scene_rect.adjust(x, y, x, y)
		#
		self._scene_rect.adjust(pos_x, pos_y, pos_x, pos_y)
		self._update_scene()

	def _combined_rect(self, nodes):
		"""
		Internal function that returns a QRectF with the combined size of the given node views.

		:param list[tp.common.nodegraphv.views.node.BaseNodeView] nodes: list of node views.
		:return: combined rect.
		:rtype: QRectF
		"""

		group = self.scene().createItemGroup(nodes)
		rect = group.boundingRect()
		self.scene().destroyItemGroup(group)

		return rect

	def _find_items_near_scene_pos(self, scene_pos, item_type=None, width=20, height=20):
		"""
		Internal function that filters node graph items from the given position, width and height area.

		:param QQPoint scene_pos: scene position.
		:param type or None item_type: optional item type to filter.
		:param int width: width area.
		:param int height: height area.
		:return: list of items from teh scene.
		:rtype: list(QGraphicsItem)
		"""

		current_scene = self.scene()
		if not current_scene:
			return list()

		items = list()
		x, y = scene_pos.x() - width, scene_pos.y() - height
		rect = QRectF(x, y, width, height)
		items_to_exclude = [self._realtime_line, self._slicer_line]
		for item in current_scene.items(rect):
			if item in items_to_exclude:
				continue
			if not item_type or isinstance(item, item_type):
				items.append(item)

		return items

	def _start_realtime_connection(self, selected_socket):
		"""
		Internal function that creates a new connector for the connection and shows the live connector following
		the cursor position.

		:param tp.common.nodegraph.views.SocketView selected_socket: selected socket view.
		"""

		if not selected_socket:
			return

		if self._realtime_line not in self.scene().items():
			self.scene().addItem(self._realtime_line)

		self._start_socket = selected_socket
		if self._start_socket.direction == consts.SocketDirection.Input:
			self._realtime_line.input_socket = self._start_socket
		elif self._start_socket == consts.SocketDirection.Output:
			self._realtime_line.output_socket = self._start_socket
		self._realtime_line.setVisible(True)

		self._auto_panner.start()

	def _end_realtime_connection(self):
		"""
		Internal function that hides live connection connector and reset start socket.
		"""

		self._realtime_line.reset_path()
		self._realtime_line.setVisible(False)
		self._realtime_line.shift_selected = False
		self._start_socket = None
		if self._realtime_line in self.scene().items():
			self.scene().removeItem(self._realtime_line)

	def _apply_realtime_connection(self, event):
		"""
		Internal function that triggers the mouse press/release event for the scene and:
			- Verifies the raltime connection connector.
			- Makes a connector if valid.
			- Emites the connectionChanged signal.

		:param QGraphicsSceneMouseEvent event: event handler from the QGraphicsScene.
		"""

		if not self._realtime_line.isVisible():
			return

		self._start_socket.hovered = False

		end_socket = None
		for item in self.scene().items(event.scenePos()):
			if isinstance(item, socket_view.SocketView):
				end_socket = item
				break

		connected, disconnected = list(), list()

		if end_socket is None:
			if self._detached_socket and not self._realtime_line.shift_selected:
				distance = math.hypot(
					self._prev_mouse_pos.x() - self._origin_mouse_pos.x(),
					self._prev_mouse_pos.y() - self._origin_mouse_pos.y())
				if distance <= 2.0:
					self.establish_connection(self._start_socket, self._detached_socket)
					self._detached_socket = None
				else:
					disconnected.append((self._start_socket, self._detached_socket))
					self.connectionChanged.emit(disconnected, connected)
			self._detached_socket = None
			self._end_realtime_connection()
			return
		else:
			if self._start_socket is end_socket:
				return

		# restore connection check.
		restore_connection = any([
			# if the end port is locked.
			end_socket.locked,
			# if same port type.
			end_socket.direction == self._start_socket.direction,
			# if connection to itself.
			end_socket.node == self._start_socket.node,
			# if end port is the start port.
			end_socket == self._start_socket,
			# if detached port is the end port.
			self._detached_socket == end_socket
		])
		if restore_connection:
			if self._detached_socket:
				to_socket = self._detached_socket or end_socket
				self.establish_connection(self._start_socket, to_socket)
				self._detached_socket = None
			self._end_realtime_connection()
			return

		# end connection if starting port is already connected.
		if self._start_socket.multi_connection and self._start_socket in end_socket.connected_sockets:
			self._detached_socket = None
			self._end_realtime_connection()
			return

		# register as disconnected if not acyclic.
		if self._acyclic and not utils.acyclic_check(self._start_socket, end_socket):
			if self._detached_socket:
				disconnected.append((self._start_socket, self._detached_socket))

			self.connection_changed.emit(disconnected, connected)

			self._detached_socket = None
			self._end_realtime_connection()
			return

		# make connection.
		if not end_socket.multi_connection and end_socket.connected_sockets:
			detached_end = end_socket.connected_sockets[0]
			disconnected.append((end_socket, detached_end))

		if self._detached_socket:
			disconnected.append((self._start_socket, self._detached_socket))

		connected.append((self._start_socket, end_socket))

		self.connectionChanged.emit(disconnected, connected)

		self._detached_socket = None
		self._end_realtime_connection()

	def _connectors_ready_to_slice(self, slicer_path):
		"""
		Internal function that updates connectors painter depending whether a connector it's ready to be sliced or not

		:param QPainterPath path: slicer path.
		"""

		over_connectors = [item for item in self.scene().items(slicer_path) if isinstance(
			item, connector_view.ConnectorView)]
		if not over_connectors:
			for over_connector in self._over_slicer_connectors:
				over_connector.ready_to_slice = False
			self._over_slicer_connectors = list()
		else:
			for over_connector in over_connectors:
				over_connector.ready_to_slice = True
				if over_connector not in self._over_slicer_connectors:
					self._over_slicer_connectors.append(over_connector)
			connectors_to_clean = list()
			for over_connector in self._over_slicer_connectors:
				if over_connector not in over_connectors:
					connectors_to_clean.append(over_connector)
			for over_connector in connectors_to_clean:
				over_connector.ready_to_slice = False

	def _connectors_sliced(self, path):
		"""
		Internal function that emits the connectionSliced signal with all the sockets that need to be
		disconnected.

		:param QPainterPath path: slicer path.
		"""

		sockets = list()
		for item in self.scene().items(path):
			if isinstance(item, connector_view.ConnectorView) and item != self._realtime_line:
				if any([item.input_socket.locked, item.output_socket.locked]):
					continue
				sockets.append([item.input_socket, item.output_socket])
		self.connectionSliced.emit(sockets)

	def _clear_key_state(self):
		"""
		Internal function that resets teh Ctrl, Shift, Alt modifiers key states.
		"""

		self._ctrl_state = False
		self._shift_state = False
		self._alt_state = False

	# ==================================================================================================================
	# CALLBACKS
	# ==================================================================================================================

	def _on_search_submitted(self, node_type):
		"""
		Internal callback function that is called when tab search widget search is submitted.

		:param str node_type: node type identifier.
		"""

		pos = self.mapToScene(self._prev_mouse_pos)
		self.searchTriggered.emit(node_type, (pos.x(), pos.y()))


class GraphTitleLabelSignals(QObject):
	"""
	Class that contains signals used by GraphTitleLabel
	We need to use this because QGrahpicsTextItem does not inherits from QObject, hence cannot define Signals
	"""

	textChanged = Signal(str)


class GraphTitleLabel(QGraphicsTextItem):

	def __init__(self):
		super(GraphTitleLabel, self).__init__()

		self.signals = GraphTitleLabelSignals()

		self.setFlags(QGraphicsTextItem.ItemIgnoresTransformations)
		self.setDefaultTextColor(QColor(255, 255, 255, 50))
		self.setFont(QFont('Impact', 20, 1))
		self.setZValue(5)

	def setPlainText(self, *args, **kwargs):
		"""
		Overrides base setPlainText function to emit textChanged signal.

		:param list args: positional arguments.
		:param dict kwargs: keyword arguments.
		"""

		super(GraphTitleLabel, self).setPlainText(*args, **kwargs)
		self.signals.textChanged.emit(self.toPlainText())
