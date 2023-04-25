from tp.common.nodegraph.core import consts
from tp.common.nodegraph.views import node
from tp.common.nodegraph.painters import node as node_painters


class SocketInputNodeView(node.NodeView):
	def __init__(self, name='group socket', parent=None):
		super(SocketInputNodeView, self).__init__(name=name, parent=parent)

		self._icon_item.setVisible(False)
		self._title_item.setVisible(False)
		self._disabled_item.text = 'Socket Locked'

	def set_proxy_mode(self, proxy_mode):
		if proxy_mode == self._proxy_mode:
			return
		self._proxy_mode = proxy_mode
		visible = not proxy_mode
		self._item_shadow.setEnabled(visible)

		# self._disabled_item.proxy_mode = self._proxy_mode

		for widget in self._widgets.values():
			widget.widget().setVisible(visible)

		for input_socket, text in self._input_views.items():
			if input_socket.display_name:
				text.setVisible(visible)
		for output_socket, text in self._output_views.items():
			if output_socket.display_name:
				text.setVisible(visible)

		self._title_item.setVisible(visible)

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
			node_painters.input_node_painter_horizontal(self, painter, option, widget)
		elif self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			node_painters.input_node_painter_vertical(self, painter, option, widget)
		else:
			raise RuntimeError('Node graph layout direction is not valid!')

	def _set_base_size(self, add_width=0.0, add_height=0.0):
		width, height = self._calculate_size(add_width, add_height)
		self._width = width + 60
		self._height = height if height >= 60 else 60

	def _align_title_horizontal(self, horizontal_offset=0.0, vertical_offset=0.0):
		rect = self.boundingRect()
		title_rect = self._title_item.boundingRect()
		x = rect.center().x() - (title_rect.width() / 2)
		y = rect.center().y() - (title_rect.height() / 2)
		self._title_item.setPos(x + horizontal_offset, y + vertical_offset)

	def _align_title_vertical(self, horizontal_offset=0.0, vertical_offset=0.0):
		rect = self.boundingRect()
		title_rect = self._title_item.boundingRect()
		x = rect.center().x() - (title_rect.width() / 1.5) - 2.0
		y = rect.center().y() - title_rect.height() - 2.0
		self._title_item.setPos(x + horizontal_offset, y + vertical_offset)

	def _align_sockets_horizontal(self, vertical_offset=0.0):
		vertical_offset = self.boundingRect().height() / 2
		if self._input_views or self._output_views:
			for socket_views in [self.inputs, self.outputs]:
				if socket_views:
					vertical_offset -= socket_views[0].boundingRect().height() / 2
					break
		super(SocketInputNodeView, self)._align_sockets_horizontal(vertical_offset)

	def _draw_node_horizontal(self):
		self._set_base_size()
		self._set_text_color(self.text_color)
		self._tooltip_disable(self.disabled)
		self._align_title()
		self._align_icon()
		self._align_sockets()
		self._align_widgets()

		self.update()
