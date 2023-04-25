#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains graph scene implementation
"""

from Qt.QtCore import Qt, QPoint, QLineF
from Qt.QtWidgets import QGraphicsScene
from Qt.QtGui import QFont, QColor, QPen, QPainter, QPainterPath

from tp.common.nodegraph.core import consts


class NodeGraphScene(QGraphicsScene):
	"""
	Scene class that is displayed within a NodeGraphView
	"""

	def __init__(self, parent=None):
		super(NodeGraphScene, self).__init__(parent=parent)

		self._editable = True
		self._secondary_grid_enabled = True
		self._grid_mode = consts.NodeGraphViewStyle.GRID_DISPLAY_LINES
		self._grid_color = consts.NodeGraphViewStyle.GRID_COLOR
		self._grid_size = consts.NodeGraphViewStyle.GRID_SIZE
		self._grid_spacing = consts.NodeGraphViewStyle.GRID_SPACING
		self._secondary_grid_color = consts.NodeGraphViewStyle.SECONDARY_GRID_COLOR
		self._background_color = consts.NodeGraphViewStyle.BACKGROUND_COLOR
		self.setBackgroundBrush(QColor(*self._background_color))

		self._setup_resources()

	def __repr__(self):
		return '<{}("{}") object at {}>'.format(str(self.__class__.__name__), self.viewer(), hex(id(self)))

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def editable(self):
		"""
		Returns whether node graph scene is editable.

		:return: True if node graph scene is editable; False otherwise.
		:rtype: bool
		"""

		return self._editable

	@editable.setter
	def editable(self, flag):
		"""
		Sets whether node graph scene is editable.

		:param bool flag: True if node graph scene is editable; False otherwise.
		"""

		self._editable = bool(flag)

	@property
	def secondary_grid_enabled(self):
		"""
		Returns whether secondary grid should be drawn.

		:return: True if secondary grid is drawn; False otherwise.
		:rtype: bool
		"""

		return self._secondary_grid_enabled

	@property
	def background_color(self):
		"""
		Returns scene background color.

		:return: scene RGB background color in 0 to 255 range.
		:rtype: list(int, int, int)
		"""

		return self._background_color

	@background_color.setter
	def background_color(self, value):
		"""
		Sets scene background color.

		:param tuple(int, int, int) value: RGB scene background color.
		"""

		self._background_color = value
		self.setBackgroundBrush(QColor(*self._background_color))

	@property
	def grid_color(self):
		"""
		Returns scene grid color.

		:return: scene RGB grid color in 0 to 255 range.
		:rtype: list(int, int, int)
		"""

		return self._grid_color

	@property
	def secondary_grid_color(self):
		"""
		Returns scene secondary grid color.

		:return: scene RGB secondary grid color in 0 to 255 range.
		:rtype: list(int, int, int)
		"""

		return self._secondary_grid_color

	@property
	def grid_size(self):
		"""
		Returns graph scene grid size.

		:return: grid size.
		:rtype: float
		"""

		return self._grid_size

	@grid_size.setter
	def grid_size(self, value):
		"""
		Sets graph grid size.

		:param float value: grid size.
		"""

		self._grid_size = value

	@property
	def grid_spacing(self):
		"""
		Returns graph scene grid spacing.

		:return: grid size.
		:rtype: float
		"""

		return self._grid_spacing

	@grid_spacing.setter
	def grid_spacing(self, value):
		"""
		Sets graph grid size.

		:param float value: grid spacing.
		"""

		self._grid_spacing = value

	@property
	def grid_mode(self):
		"""
		Return scene graph grid mode.

		:return: grid mode.
		:rtype: GridSceneBackgroundModes
		"""

		return self._grid_mode

	@grid_mode.setter
	def grid_mode(self, value):
		"""
		Sets scene graph grid mode.

		:param GridSceneBackgroundModes value: grid mode.
		"""

		value = value if value is not None else consts.NodeGraphViewStyle.GRID_DISPLAY_LINES
		self._grid_mode = value

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def mousePressEvent(self, event):
		"""
		Overrides base mousePressEvent function.
		Here we handle the update of the selection status of the nodes in the scene view.
		Also make sure that specific custom view scene event function calls are handled.

		:param QEvent event: Qt mouse event.
		"""

		modifiers = event.modifiers()
		selected_nodes = list()
		view = self.viewer()
		if view:
			selected_nodes = view.selected_nodes()
			view.sceneMousePressEvent(event)

		super(NodeGraphScene, self).mousePressEvent(event)

		keep_selection = any([event.button() in [Qt.MiddleButton, Qt.RightButton], modifiers == Qt.AltModifier])
		if keep_selection:
			for node in selected_nodes:
				node.setSelected(True)

	def mouseReleaseEvent(self, event):
		"""
		Overrides mouseReleaseEvent function.
		Make sure that specific custom view scene event function calls are handled.

		:param QEvent event: Qt mouse event.
		"""

		view = self.viewer()
		if view:
			view.sceneMouseReleaseEvent(event)

		super(NodeGraphScene, self).mouseReleaseEvent(event)

	def mouseMoveEvent(self, event):
		"""
		Overrides mouseMoveEvent function.
		Make sure that specific custom view scene event function calls are handled.

		:param QEvent event: Qt mouse event.
		"""

		view = self.viewer()
		if view:
			view.sceneMouseMoveEvent(event)

		super(NodeGraphScene, self).mouseMoveEvent(event)

	def drawBackground(self, painter, rect):
		"""
		Overrides base drawBackground function.

		:param QPainter painter: painter used for the background.
		:param QRect rect: painter rectangle.
		"""

		super(NodeGraphScene, self).drawBackground(painter, rect)

		# if graph viewer is not defined, we skip custom background painting
		viewer = self.viewer()
		if not viewer:
			return

		painter.save()

		painter.setRenderHint(QPainter.Antialiasing)
		painter.setBrush(self.backgroundBrush())

		if self._grid_mode == consts.NodeGraphViewStyle.GRID_DISPLAY_DOTS:
			self._draw_dots(painter, rect, self._grid_pen, self._grid_size)
		elif self._grid_mode == consts.NodeGraphViewStyle.GRID_DISPLAY_LINES:
			zoom = viewer.get_zoom()
			if zoom > -0.5:
				self._draw_grid(painter, rect, self._grid_pen, self._grid_size)
			if self._secondary_grid_enabled:
				color = QColor(*self._secondary_grid_color) or self.backgroundBrush().color().darker(150)
				if zoom <= 0.0:
					color = color.darker(100 - int(zoom * 110))
				secondary_grid_pen = QPen(color, 0.65)
				self._draw_grid(painter, rect, secondary_grid_pen, self._grid_size * self._grid_spacing)

		if not self._editable:
			self._draw_non_editable_text(painter, self._non_editable_pen)

		# draw view border
		path = QPainterPath()
		path.addRect(rect)
		painter.setBrush(Qt.NoBrush)
		painter.setPen(self._border_pen)
		painter.drawPath(path)

		painter.restore()

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def viewer(self):
		"""
		Returns node graph view this scene is linked to.

		:return: node graph viewer.
		:rtype: NodeGraphViewer or None
		"""

		return self.views()[0] if self.views() else None

	# =================================================================================================================
	# INTERNAL
	# =================================================================================================================

	def _setup_resources(self):
		"""
		Internal function that setups all the resources used by the scene.
		"""

		self._grid_pen = QPen(QColor(*self._grid_color), 0.65)
		self._non_editable_pen = QPen(QColor(*(90, 90, 90)))
		self._border_pen = QPen(self.backgroundBrush().color().lighter(100))
		self._border_pen.setCosmetic(True)

	def _draw_grid(self, painter, rect, pen, grid_size):
		"""
		Internal function that draws the scene background grid as lines.

		:param QPainter painter: painter used for the background grid.
		:param QRect rect: painter rectangle.
		:param QPen pen: QPen used to draw background grid.
		:param int grid_size: grid sze
		:return:
		"""

		# if graph viewer is not defined, we skip background grid painting.
		view = self.viewer()
		if not view:
			return

		left = int(rect.left())
		right = int(rect.right())
		top = int(rect.top())
		bottom = int(rect.bottom())

		first_left = left - (left % grid_size)
		first_top = top - (top % grid_size)

		lines = list()
		lines.extend(QLineF(x, top, x, bottom) for x in range(first_left, right, grid_size))
		lines.extend(QLineF(left, y, right, y) for y in range(first_top, bottom, grid_size))

		painter.setPen(pen)
		painter.drawLines(lines)

	def _draw_dots(self, painter, rect, pen, grid_size):
		"""
		Internal function that draws the scene background grid as dots.

		:param QPainter painter: painter used for the background grid.
		:param QRect rect: painter rectangle.
		:param QPen pen: QPen used to draw background grid.
		:param int grid_size: grid sze
		:return:
		"""

		# if graph viewer is not defined, we skip background dots painting.
		view = self.viewer()
		if not view:
			return

		zoom = view.get_zoom()
		if zoom < 0:
			grid_size = int(abs(zoom) / 0.3 + 1) * grid_size

		left = int(rect.left())
		right = int(rect.right())
		top = int(rect.top())
		bottom = int(rect.bottom())

		first_left = left - (left % grid_size)
		first_top = top - (top % grid_size)

		pen.setWidth(grid_size / 10)
		painter.setPen(pen)

		[painter.drawPoint(int(x), int(y)) for x in range(
			first_left, right, grid_size) for y in range(first_top, bottom, grid_size)]

	def _draw_non_editable_text(self, painter, pen):
		"""
		Internal function that draws non editable scene background text.

		:param QPainter painter: painter used for the background non editable text.
		:param QPen pen: QPen used to draw background non editable text.
		"""

		# if graph viewer is not defined, we skip background non editable text painting
		parent = self.viewer()
		if not parent:
			return

		font = QFont()
		font.setPixelSize(48)
		painter.setFont(font)
		pos = QPoint(20, parent.height() - 20)
		painter.setPen(pen)
		painter.drawText(parent.mapToScene(pos), 'Not Editable')
