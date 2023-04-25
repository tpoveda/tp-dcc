from tp.common.nodegraph.core import consts
from tp.common.nodegraph.views import node
from tp.common.nodegraph.painters import node as node_painters


class GroupNodeView(node.NodeView):
	def __init__(self, name='group', parent=None):
		super(GroupNodeView, self).__init__(name=name, parent=parent)

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
			node_painters.group_node_painter_horizontal(self, painter, option, widget)
		elif self.layout_direction == consts.GraphLayoutDirection.VERTICAL:
			node_painters.group_node_painter_vertical(self, painter, option, widget)
		else:
			raise RuntimeError('Node graph layout direction is not valid!')

	def _align_icon_vertical(self, horizontal_offset=0.0, vertical_offset=0.0):
		y = self._height / 2
		y -= self._icon_item.boundingRect().height()
		self._icon_item.setPos(self._width + horizontal_offset, y + vertical_offset)

	def _align_icon_horizontal(self, horizontal_offset=0.0, vertical_offset=0.0):
		y = self._height / 2
		y -= self._title_item.boundingRect().height() / 2
		self._title_item.setPos(self._width + horizontal_offset, y + vertical_offset)

	def _align_sockets_horizontal(self, vertical_offset=0.0):
		width = self._width
		text_offset = consts.SOCKET_FALLOFF - 2
		spacing = 1

		input_views = [input_view for input_view in self.inputs if input_view.isVisible()]
		if input_views:
			socket_width = input_views[0].boundingRect().width()
			socket_height = input_views[0].boundingRect().height()
			socket_x = socket_width / 2 * -1
			socket_x += 3.0
			socket_y = vertical_offset
			for input_view in input_views:
				input_view.setPos(socket_x, socket_y)
				socket_y += socket_height + spacing
		for socket_view, text in self._input_views.items():
			if socket_view.isVisible():
				text_x = socket_view.boundingRect().width() / 2 - text_offset
				text_x += 3.0
				text.setPos(text_x, socket_view.y() - 1.5)

		output_views = [output_view for output_view in self.outputs if output_view.isVisible()]
		if output_views:
			socket_width = output_views[0].boundingRect().width()
			socket_height = output_views[0].boundingRect().height()
			socket_x = width - (socket_width / 2)
			socket_x -= 9.0
			socket_y = vertical_offset
			for input_view in input_views:
				input_view.setPos(socket_x, socket_y)
				socket_y += socket_height + spacing
		for socket_view, text in self._output_views.items():
			if socket_view.isVisible():
				text_width = text.boundingRect().width() - text_offset
				text_x = socket_view.x() - text_width
				text.setPos(text_x, socket_view.y() - 1.5)

	def _align_sockets_vertical(self, vertical_offset=0.0):
		input_views = [input_view for input_view in self.inputs if input_view.isVisible()]
		if input_views:
			socket_width = input_views[0].boundingRect().width()
			socket_height = input_views[0].boundingRect().height()
			half_width = socket_width / 2
			delta = self._width / (len(input_views) + 1)
			socket_x = delta
			socket_y = -socket_height / 2 + 3.0
			for socket_view in input_views:
				socket_view.setPos(socket_x - half_width, socket_y)
				socket_x += delta

		output_views = [output_view for output_view in self.outputs if output_view.isVisible()]
		if output_views:
			socket_width = output_views[0].boundingRect().width()
			socket_height = output_views[0].boundingRect().height()
			half_width = socket_width / 2
			delta = self._width / (len(output_views) + 1)
			socket_x = delta
			socket_y = self._height - (socket_height / 2) - 9.0
			for socket_view in output_views:
				socket_view.setPos(socket_x - half_width, socket_y)
				socket_x += delta

	def _draw_node_horizontal(self):
		height = self._title_item.boundingRect().height() + 4.0

		for input_view, text in self._input_views.items():
			text.setVisible(input_view.display_name)
		for output_view, text in self._output_views.items():
			text.setVisible(output_view.display_name)

		self._set_base_size(add_height=height + 10, add_width=8.0)
		self._set_text_color(self.text_color)
		self._tooltip_disable(self.disabled)
		self._align_title()
		self._align_icon(horizontal_offset=2.0, vertical_offset=3.0)
		self._align_sockets(vertical_offset=height)
		self._align_widgets(vertical_offset=height)

		self.update()

	def _draw_node_vertical(self):
		height = self._title_item.boundingRect().height() + 4.0

		for _, text in self._input_views.items():
			text.setVisible(False)
		for _, text in self._output_views.items():
			text.setVisible(False)

		self._set_base_size(add_width=8.0)
		self._set_text_color(self.text_color)
		self._tooltip_disable(self.disabled)
		self._align_title(horizontal_offset=7.0, vertical_offset=6.0)
		self._align_icon(horizontal_offset=4.0, vertical_offset=-2.0)
		self._align_sockets(vertical_offset=height + (height / 2))
		self._align_widgets(vertical_offset=height / 2)

		self.update()
