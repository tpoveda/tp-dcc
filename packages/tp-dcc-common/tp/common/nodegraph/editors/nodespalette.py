from collections import defaultdict

from Qt.QtCore import Qt, QRectF, QSize, QSortFilterProxyModel
from Qt.QtWidgets import QWidget, QTabWidget, QVBoxLayout, QListView, QStyle, QStyledItemDelegate
from Qt.QtGui import QFontMetrics, QStandardItemModel, QStandardItem, QPen, QBrush, QPainter

from tp.common.nodegraph.core import consts


class NodesPalette(QWidget):
	"""
	Widget that displays all registered nodes in a grid layout.
	"""

	def __init__(self, node_graph, parent=None):
		super(NodesPalette, self).__init__(parent=parent)

		self._category_tabs = dict()
		self._custom_labels = dict()
		self._factory = node_graph.nodes_factory if node_graph else None

		self._tab_widget = QTabWidget(parent=self)
		self._tab_widget.setMovable(True)
		layout = QVBoxLayout()
		self.setLayout(layout)
		layout.addWidget(self._tab_widget)

		self.setWindowTitle('Nodes')

		self._setup_ui()

	def __repr__(self):
		return '<{} object at {}>'.format(self.__class__.__name__, hex(id(self)))

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def set_category_label(self, category, label):
		"""
		Sets the tab label for the given category tab.

		:param str category: node identifier category.
		:param str label: custom label.
		"""

		if label in self._custom_labels.values():
			labels = {v: k for k, v in self._custom_labels.items()}
			raise ValueError('label "{}" already in use for "{}"'.format(label, labels[label]))
		previous_label = self._custom_labels.get(category, '')
		for idx in range(self._tab_widget.count()):
			tab_text = self._tab_widget.tabText(idx)
			if tab_text in [category, previous_label]:
				self._tab_widget.setTabText(idx, label)
				break
		self._custom_labels[category] = label

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _setup_ui(self):
		"""
		Internal function that populates nodes palette UI.
		"""

		categories = set()
		node_types = defaultdict(list)

		if not self._factory:
			return

		for name, node_ids in self._factory.names.items():
			for node_id in node_ids:
				category = '.'.join(node_id.split('.')[:-1])
				categories.add(category)
				node_types[category].append((node_id, name))

			for category, nodes_list in node_types.items():
				grid_view = self._add_category_tab(category)
				for node_id, node_name in nodes_list:
					grid_view.add_item(node_name, node_id)

	def _add_category_tab(self, category):
		"""
		Internal function that adds a new tab to the node palette widget.

		:param str category: node identifier category.
		:return: newly created node grid view widget.
		:rtype: NodesGridView
		"""

		if category not in self._category_tabs:
			grid_widget = NodesGridView(parent=self)
			self._tab_widget.addTab(grid_widget, category)
			self._category_tabs[category] = grid_widget

		return self._category_tabs[category]


class NodesGridView(QListView):
	def __init__(self, parent=None):
		super(NodesGridView, self).__init__(parent=parent)

		self.setSelectionMode(self.ExtendedSelection)
		self.setUniformItemSizes(True)
		self.setResizeMode(self.Adjust)
		self.setViewMode(self.IconMode)
		self.setDragDropMode(self.DragOnly)
		self.setDragEnabled(True)
		self.setMinimumSize(450, 300)
		self.setSpacing(4)

		model = QStandardItemModel()
		proxy_model = NodesGridProxyModel()
		proxy_model.setSourceModel(model)
		self.setModel(proxy_model)
		self.setItemDelegate(NodesGridDelegate(self))

	def clear(self):
		"""
		Clears nodes grid model.
		"""

		self.model().sourceMode().clear()

	def add_item(self, label, tooltip=''):
		"""
		Adds a new item into the model.

		:param str label: item label.
		:param str tooltip: item tooltip
		"""

		item = QStandardItem(label)
		item.setSizeHint(QSize(130, 40))
		item.setToolTip(tooltip)
		model = self.model().sourceModel()
		model.appendRow(item)


class NodesGridProxyModel(QSortFilterProxyModel):

	def mimeData(self, indexes):
		node_ids = ['node:{}'.format(i.data(Qt.ToolTipRole)) for i in indexes]
		node_urn = consts.URN_SCHEME + ';'.join(node_ids)
		mime_data = super(NodesGridProxyModel, self).mimeData(indexes)
		mime_data.setUrls([node_urn])
		return mime_data


class NodesGridDelegate(QStyledItemDelegate):

	def paint(self, painter, option, index):

		if index.column() != 0:
			super(NodesGridDelegate, self).paint(painter, option, index)
			return

		model = index.model().sourceModel()
		item = model.item(index.row(), index.column())

		sub_margin = 2
		radius = 5

		base_rect = QRectF(
			option.rect.x() + sub_margin,
			option.rect.y() + sub_margin,
			option.rect.width() - (sub_margin * 2),
			option.rect.height() - (sub_margin * 2)
		)

		painter.save()
		painter.setRenderHint(QPainter.Antialiasing, True)

		# background.
		bg_color = option.palette.window().color()
		pen_color = option.palette.midlight().color().lighter(120)
		if option.state & QStyle.State_Selected:
			bg_color = bg_color.lighter(120)
			pen_color = pen_color.lighter(160)

		pen = QPen(pen_color, 3.0)
		pen.setCapStyle(Qt.RoundCap)
		painter.setPen(pen)
		painter.setBrush(QBrush(bg_color))
		painter.drawRoundRect(base_rect, int(base_rect.height()/radius), int(base_rect.width()/radius))

		if option.state & QStyle.State_Selected:
			pen_color = option.palette.highlight().color()
		else:
			pen_color = option.palette.midlight().color().darker(130)
		pen = QPen(pen_color, 1.0)
		pen.setCapStyle(Qt.RoundCap)
		painter.setPen(pen)
		painter.setBrush(Qt.NoBrush)

		sub_margin = 6
		sub_rect = QRectF(
			base_rect.x() + sub_margin,
			base_rect.y() + sub_margin,
			base_rect.width() - (sub_margin * 2),
			base_rect.height() - (sub_margin * 2)
		)
		painter.drawRoundRect(sub_rect, int(sub_rect.height() / radius), int(sub_rect.width() / radius))
		painter.setBrush(QBrush(pen_color))
		edge_size = 2, sub_rect.height() - 6
		left_x = sub_rect.left()
		right_x = sub_rect.right() - edge_size[0]
		pos_y = sub_rect.center().y() - (edge_size[1] / 2)

		for pos_x in [left_x, right_x]:
			painter.drawRect(QRectF(pos_x, pos_y, edge_size[0], edge_size[1]))

		# painter.setPen(QtCore.Qt.NoPen)
		painter.setBrush(QBrush(bg_color))
		dot_size = 4
		left_x = sub_rect.left() - 1
		right_x = sub_rect.right() - (dot_size - 1)
		pos_y = sub_rect.center().y() - (dot_size / 2)
		for pos_x in [left_x, right_x]:
			painter.drawEllipse(QRectF(pos_x, pos_y, dot_size, dot_size))
			pos_x -= dot_size + 2

		# text
		pen_color = option.palette.text().color()
		pen = QPen(pen_color, 0.5)
		pen.setCapStyle(Qt.RoundCap)
		painter.setPen(pen)

		font = painter.font()
		font_metrics = QFontMetrics(font)
		font_width = font_metrics.horizontalAdvance(item.text().replace(' ', '_'))
		font_height = font_metrics.height()
		text_rect = QRectF(
			sub_rect.center().x() - (font_width / 2),
			sub_rect.center().y() - (font_height * 0.55),
			font_width, font_height)
		painter.drawText(text_rect, item.text())
		painter.restore()
