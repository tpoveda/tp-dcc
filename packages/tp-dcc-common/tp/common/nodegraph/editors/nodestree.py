from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QTreeWidget, QAbstractItemView, QTreeWidgetItem
from Qt.QtGui import QPalette, QBrush

from tp.common.nodegraph.core import consts

TYPE_NODE = QTreeWidgetItem.UserType + 1
TYPE_CATEGORY = QTreeWidgetItem.UserType + 2


class NodesTreeWidget(QTreeWidget):
	"""
	Widget that allows to display all registered nodes from this node in a tree and allow drag and drop them
	into the viewer.
	"""

	def __init__(self, node_graph=None, parent=None):
		super(NodesTreeWidget, self).__init__(parent=parent)

		self.setDragDropMode(QAbstractItemView.DragOnly)
		self.setSelectionMode(self.ExtendedSelection)
		self.setHeaderHidden(True)
		self.setWindowTitle('Nodes')

		self._factory = node_graph.nodes_factory if node_graph else None
		self._category_items = dict()
		self._custom_labels = dict()

		self._build_tree()

	def __repr__(self):
		return '<{} object at {}>'.format(self.__class__.__name__, hex(id(self)))

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def mimeData(self, items):
		node_ids = ['node:{}'.format(i.toolTip(0)) for i in items]
		node_urn = consts.URN_SCHEME + ';'.join(node_ids)
		mime_data = super(NodesTreeWidget, self).mimeData(items)
		mime_data.setUrls([node_urn])
		return mime_data

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def set_graph(self, graph):
		"""
		Sets the graph whose registered nodes we want to show.

		:param tp.common.nodegraph.core.graph.NodeGraph graph: node graph instance.
		"""

		self._factory = graph.nodes_factory if graph else None
		self.update()

	def update(self):
		"""
		Updates and refreshes the node tree widget.
		"""

		self._build_tree()

	def set_category_label(self, category, label):
		"""
		Overrides the label for a node category root item.

		:param str category: node identifier category.
		:param str label: custom display label.
		"""

		self._custom_labels[category] = label
		if category in self._category_items:
			item = self._category_items[category]
			item.setText(0, label)

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _build_tree(self):
		"""
		Internal fucntion that populate the node tree.
		"""
		self.clear()
		palette = QPalette()
		categories = set()
		node_types = dict()

		if not self._factory:
			return

		for name, node_ids in self._factory.names.items():
			for nid in node_ids:
				categories.add('.'.join(nid.split('.')[:-1]))
				node_types[nid] = name

		self._category_items = dict()
		for category in sorted(categories):
			if category in self._custom_labels.keys():
				label = self._custom_labels[category]
			else:
				label = '{}'.format(category)
			cat_item = BaseNodeTreeItem(self, [label], type=TYPE_CATEGORY)
			cat_item.setFirstColumnSpanned(True)
			cat_item.setFlags(Qt.ItemIsEnabled)
			cat_item.setBackground(0, QBrush(palette.midlight().color()))
			cat_item.setSizeHint(0, QSize(100, 26))
			self.addTopLevelItem(cat_item)
			cat_item.setExpanded(True)
			self._category_items[category] = cat_item

		for node_id, node_name in node_types.items():
			category = '.'.join(node_id.split('.')[:-1])
			category_item = self._category_items[category]

			item = BaseNodeTreeItem(category_item, [node_name], type=TYPE_NODE)
			item.setToolTip(0, node_id)
			item.setSizeHint(0, QSize(100, 26))

			category_item.addChild(item)

	def _set_nodes_factory(self, factory):
		"""
		Internal function that sets current node factory.

		:param tp.common.nodegraph.core.factory.NodesFactory factory: nodes factory.
		"""

		self._factory = factory
		self.update()


class BaseNodeTreeItem(QTreeWidgetItem):

	def __eq__(self, other):
		"""
		Workaround fix for QTreeWidgetItem "operator not implemented error".
		see link: https://bugreports.qt.io/browse/PYSIDE-74
		"""
		return id(self) == id(other)