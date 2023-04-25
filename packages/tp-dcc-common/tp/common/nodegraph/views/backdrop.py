from Qt.QtCore import Qt, QPointF, QRectF
from Qt.QtWidgets import QGraphicsItem
from Qt.QtGui import QCursor, QColor, QPen, QBrush, QPainterPath

from tp.common.nodegraph.core import consts
from tp.common.nodegraph.views import node, socket, connector


class BackdropNodeView(node.BaseNodeView):

	def __init__(self, name='backdrop', text='', parent=None):
		super(BackdropNodeView, self).__init__(name, parent)

		self.setZValue(consts.CONNECTOR_Z_VALUE - 1)
		self._properties['backdrop_text'] = text
		self._min_size = 80, 80
		self._sizer = BackdropSizer(self, 26.0)
		self._sizer.set_pos(*self._min_size)
		self._nodes = [self]

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def minimum_size(self):
		return self._min_size

	@minimum_size.setter
	def minimum_size(self, size=(50, 50)):
		self._min_size = size

	@property
	def backdrop_text(self):
		return self._properties['backdrop_text']

	@backdrop_text.setter
	def backdrop_text(self, text):
		self._properties['backdrop_text'] = text
		self.update(self.boundingRect())

	@node.BaseNodeView.width.setter
	def width(self, width=0.0):
		node.BaseNodeView.width.fset(self, width)
		self._sizer.set_pos(self._width, self._height)

	@node.BaseNodeView.height.setter
	def height(self, height=0.0):
		node.BaseNodeView.height.fset(self, height)
		self._sizer.set_pos(self._width, self._height)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def mouseDoubleClickEvent(self, event):
		"""
		Overrides base mouseDoubleClickEvent itemChange function.

		:param QEvent event: mouse double click event.
		"""

		viewer = self.viewer()
		if viewer:
			viewer.nodeDoubleClicked.emit(self.id)

		super(BackdropNodeView, self).mouseDoubleClickEvent(event)

	def mousePressEvent(self, event):
		"""
		Overrides base mousePressEvent itemChange function.

		:param QEvent event: mouse press event.
		"""

		if event.button() == Qt.LeftButton:
			pos = event.scenePos()
			rect = QRectF(pos.x() - 5, pos.y() - 5, 10, 10)
			item = self.scene().items(rect)[0]

			if isinstance(item, (socket.SocketView, connector.ConnectorView)):
				self.setFlag(self.ItemIsMovable, False)
				return
			if self.selected:
				return

			viewer = self.viewer()
			[n.setSelected(False) for n in viewer.selected_nodes()]

			self._nodes += self.get_nodes(False)
			[n.setSelected(True) for n in self._nodes]

	def mouseReleaseEvent(self, event):
		"""
		Overrides base mouseReleaseEvent itemChange function.

		:param QEvent event: mouse press event.
		"""

		super(BackdropNodeView, self).mouseReleaseEvent(event)

		self.setFlag(self.ItemIsMovable, True)
		[n.setSelected(True) for n in self._nodes]
		self._nodes = [self]

	def paint(self, painter, option, widget):
		"""
		Draws the backdrop rect.
		Args:
			painter (QtGui.QPainter): painter used for drawing the item.
			option (QtGui.QStyleOptionGraphicsItem):
				used to describe the parameters needed to draw.
			widget (QtWidgets.QWidget): not used.
		"""
		painter.save()
		painter.setPen(Qt.NoPen)
		painter.setBrush(Qt.NoBrush)

		margin = 1.0
		rect = self.boundingRect()
		rect = QRectF(
			rect.left() + margin, rect.top() + margin,
			rect.width() - (margin * 2), rect.height() - (margin * 2))

		radius = 2.6
		color = (self.color[0], self.color[1], self.color[2], 50)
		painter.setBrush(QColor(*color))
		painter.setPen(Qt.NoPen)
		painter.drawRoundedRect(rect, radius, radius)

		top_rect = QRectF(rect.x(), rect.y(), rect.width(), 26.0)
		painter.setBrush(QBrush(QColor(*self.color)))
		painter.setPen(Qt.NoPen)
		painter.drawRoundedRect(top_rect, radius, radius)
		for pos in [top_rect.left(), top_rect.right() - 5.0]:
			painter.drawRect(QRectF(pos, top_rect.bottom() - 5.0, 5.0, 5.0))

		if self.backdrop_text:
			painter.setPen(QColor(*self.text_color))
			txt_rect = QRectF(
				top_rect.x() + 5.0, top_rect.height() + 3.0,
				rect.width() - 5.0, rect.height())
			painter.setPen(QColor(*self.text_color))
			painter.drawText(txt_rect, Qt.AlignLeft | Qt.TextWordWrap, self.backdrop_text)

		if self.selected:
			sel_color = [x for x in consts.NODE_SELECTED_COLOR]
			sel_color[-1] = 15
			painter.setBrush(QColor(*sel_color))
			painter.setPen(Qt.NoPen)
			painter.drawRoundedRect(rect, radius, radius)

		txt_rect = QRectF(top_rect.x(), top_rect.y(), rect.width(), top_rect.height())
		painter.setPen(QColor(*self.text_color))
		painter.drawText(txt_rect, Qt.AlignCenter, self.name)

		border = 0.8
		border_color = self.color
		if self.selected and consts.NODE_SELECTED_BORDER_COLOR:
			border = 1.0
			border_color = consts.NODE_SELECTED_BORDER_COLOR
		painter.setBrush(Qt.NoBrush)
		painter.setPen(QPen(QColor(*border_color), border))
		painter.drawRoundedRect(rect, radius, radius)

		painter.restore()

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def on_sizer_pos_changed(self, pos):
		self._width = pos.x() + self._sizer.size
		self._height = pos.y() + self._sizer.size

	def on_sizer_pos_mouse_release(self):
		size = {
			'pos': self.xy_pos,
			'width': self._width,
			'height': self._height}
		self.viewer().nodeBackdropUpdated.emit(self.id, 'sizer_mouse_release', size)

	def on_sizer_double_clicked(self):
		size = self.calc_backdrop_size()
		self.viewer().nodeBackdropUpdated.emit(self.id, 'sizer_double_clicked', size)

	def get_nodes(self, inc_intersects=False):
		mode = {True: Qt.IntersectsItemShape, False: Qt.ContainsItemShape}
		nodes = list()
		if self.scene():
			polygon = self.mapToScene(self.boundingRect())
			rect = polygon.boundingRect()
			items = self.scene().items(rect, mode=mode[inc_intersects])
			for item in items:
				if item == self or item == self._sizer:
					continue
				if isinstance(item, node.BaseNodeView):
					nodes.append(item)
		return nodes

	def calc_backdrop_size(self, nodes=None):
		nodes = nodes or self.get_nodes(True)
		padding = 40
		nodes_rect = self._combined_rect(nodes)
		return {
			'pos': [
				nodes_rect.x() - padding, nodes_rect.y() - padding
			],
			'width': nodes_rect.width() + (padding * 2),
			'height': nodes_rect.height() + (padding * 2)
		}

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _combined_rect(self, nodes):
		group = self.scene().createItemGroup(nodes)
		rect = group.boundingRect()
		self.scene().destroyItemGroup(group)
		return rect


class BackdropSizer(QGraphicsItem):
	def __init__(self, parent=None, size=6.0):
		super(BackdropSizer, self).__init__(parent)

		self._size = size

		self.setFlag(self.ItemIsSelectable, True)
		self.setFlag(self.ItemIsMovable, True)
		self.setFlag(self.ItemSendsScenePositionChanges, True)
		self.setCursor(QCursor(Qt.SizeFDiagCursor))
		self.setToolTip('double-click auto resize')

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def size(self):
		return self._size

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def boundingRect(self):
		"""
		Overrides base QGraphicsItem boundingRect function.

		:return: bounding rect rectangle area.
		:rtype: QRectF
		"""

		return QRectF(0.5, 0.5, self._size, self._size)

	def itemChange(self, change, value):
		"""
		Overrides base QGraphicsItem itemChange function.

		:param QGraphicsItem.GraphicsItemChange change: type of change.
		:param object value: change value.
		"""

		if change == self.ItemPositionChange:
			item = self.parentItem()
			mx, my = item.minimum_size
			x = mx if value.x() < mx else value.x()
			y = my if value.y() < my else value.y()
			value = QPointF(x, y)
			item.on_sizer_pos_changed(value)
			return value
		return super(BackdropSizer, self).itemChange(change, value)

	def mouseDoubleClickEvent(self, event):
		"""
		Overrides base mouseDoubleClickEvent itemChange function.

		:param QEvent event: mouse double click event.
		"""

		item = self.parentItem()
		item.on_sizer_double_clicked()

		super(BackdropSizer, self).mouseDoubleClickEvent(event)

	def mousePressEvent(self, event):
		"""
		Overrides base mousePressEvent itemChange function.

		:param QEvent event: mouse double click event.
		"""

		self._prev_xy = (self.pos().x(), self.pos().y())

		super(BackdropSizer, self).mousePressEvent(event)

	def mouseReleaseEvent(self, event):
		"""
		Overrides base mouseReleaseEvent itemChange function.

		:param QEvent event: mouse double click event.
		"""

		current_xy = (self.pos().x(), self.pos().y())
		if current_xy != self._prev_xy:
			item = self.parentItem()
			item.on_sizer_pos_mouse_release()

		del self._prev_xy

		super(BackdropSizer, self).mouseReleaseEvent(event)

	def paint(self, painter, option, widget):
		"""
		Draws the backdrop sizer in the bottom right corner.

		:param Qt.QtGui.QPainter painter: painter used for drawing the item.
		:param Qt.QtGui.QStyleOptionGraphicsItem option: used to describe the parameters needed to draw.
		:param Qt.QtWidgets.QWidget widget: not used.
		"""

		painter.save()

		margin = 1.0
		rect = self.boundingRect()
		rect = QRectF(
			rect.left() + margin, rect.top() + margin,
			rect.width() - (margin * 2), rect.height() - (margin * 2))

		item = self.parentItem()
		if item and item.selected:
			color = QColor(*consts.NODE_SELECTED_COLOR)
		else:
			color = QColor(*item.color)
			color = color.darker(110)
		path = QPainterPath()
		path.moveTo(rect.topRight())
		path.lineTo(rect.bottomRight())
		path.lineTo(rect.bottomLeft())
		painter.setBrush(color)
		painter.setPen(Qt.NoPen)
		painter.fillPath(path, painter.brush())

		painter.restore()

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def set_pos(self, x, y):
		"""
		Set the position of the node within the node graph view.

		:param float x: X position.
		:param float y: Y position.
		"""

		x -= self._size
		y -= self._size
		self.setPos(x, y)
