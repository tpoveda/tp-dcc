from collections import defaultdict

from Qt.QtCore import Qt, Signal, QRect
from Qt.QtWidgets import (
	QWidget, QSpinBox, QTableWidget, QStyle, QStyledItemDelegate, QAbstractItemView, QHeaderView, QPushButton,
	QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidgetItem, QTabWidget, QLabel
)
from Qt.QtGui import QPen, QBrush, QPainter, QIcon

from tp.common.python import helpers
from tp.common.nodegraph.editors.propertieseditor.properties import base, factory


class PropertiesEditorWidget(QWidget):

	propertyChanged = Signal(str, str, object)

	def __init__(self, graph=None, parent=None):
		super(PropertiesEditorWidget, self).__init__(parent=parent)

		self.setWindowTitle('Properties Editor')

		self._block_signal = False
		self._lock = False
		self._graph = None

		self._prop_list = PropertiesList()
		self._limit = QSpinBox()
		self._limit.setToolTip('Set display nodes limit.')
		self._limit.setMaximum(10)
		self._limit.setMinimum(0)
		self._limit.setValue(2)
		self.btn_lock = QPushButton('Lock')
		self.btn_lock.setToolTip('Lock the properties editor prevent nodes from being loaded.')
		btn_clr = QPushButton('Clear')
		btn_clr.setToolTip('Clear the properties editor.')
		top_layout = QHBoxLayout()
		top_layout.setSpacing(2)
		top_layout.addWidget(self._limit)
		top_layout.addStretch(1)
		top_layout.addWidget(self.btn_lock)
		top_layout.addWidget(btn_clr)
		layout = QVBoxLayout(self)
		layout.addLayout(top_layout)
		layout.addWidget(self._prop_list, 1)

		self.resize(450, 400)

		self._limit.valueChanged.connect(self._on_limit_value_changed)
		self.btn_lock.clicked.connect(self._on_lock_button_clicked)
		btn_clr.clicked.connect(self._on_clear_button_clicked)

		self.set_graph(graph)

	def __repr__(self):
		return '<{} object at {}>'.format(self.__class__.__name__, hex(id(self)))

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def set_graph(self, graph):
		"""
		Sets the graph this properties editor is linked to.

		:param tp.common.nodegraph.core.grpah.NodeGraph graph: node graph instance.
		"""

		if self._graph:
			graph.remove_properties_editor(self)
			graph.nodeDoubleClicked.disconnect(self._on_graph_node_double_clicked)
			graph.nodesDeleted.disconnect(self._on_graph_node_deleted)
			graph.propertyChanged.disconnect(self._on_graph_node_property_changed)
			self._graph = None

		if graph:
			graph.add_properties_editor(self)
			graph.nodeDoubleClicked.connect(self._on_graph_node_double_clicked)
			graph.nodesDeleted.connect(self._on_graph_node_deleted)
			graph.propertyChanged.connect(self._on_graph_node_property_changed)
		self._graph = graph

	def limit(self):
		"""
		Returns the limit for how many nodes can load into the properties editor.

		:return: node limit.
		:rtype: int
		"""

		return int(self._limit.value())

	def set_limit(self, value):
		"""
		Sets the limit for how many nodes can be load.

		:param int value: node limit.
		"""

		self._limit.setValue(value)

	def remove_node(self, node):
		"""
		Removes node from the properties editor.

		:param str or tp.common.nodegraph.core.node.BaseNode node: node ID or node object.
		"""

		node_id = node if helpers.is_string(node) else node.id
		self._on_property_closed(node_id)

	def property_widget(self, node):
		"""
		Returns the node property widget.

		:param str or tp.common.nodegraph.core.node.BaseNode node: node ID or node object.
		:return: node property widget.
		:rtype: NodePropWidget
		"""

		node_id = node if helpers.is_string(node) else node.id
		item_find = self._prop_list.findItems(node_id, Qt.MatchExactly)
		if item_find:
			item = item_find[0]
			return self._prop_list.cellWidget(item.row(), 0)

	# ==================================================================================================================
	# CALLBACKS
	# ==================================================================================================================

	def _on_property_closed(self, node_id):
		"""
		Internal callback function that is called each time a property is closed.

		:param str node_id: node ID of the property.
		"""

		items = self._prop_list.findItems(node_id, Qt.MatchExactly)
		[self._prop_list.removeRow(i.row()) for i in items]

	def _on_limit_value_changed(self, value):
		"""
		Internal callback function that is called each time limit value changes.

		:param int value: node limit.
		"""

		rows = self._prop_list.rowCount()
		if rows > value:
			self._prop_list.removeRow(rows - 1)

	def _on_lock_button_clicked(self):
		"""
		Internal callback fucntion that is called each time lock button is clicked by the user.
		"""

		self._lock = not self._lock
		if self._lock:
			self.btn_lock.setText('UnLock')
		else:
			self.btn_lock.setText('Lock')

	def _on_clear_button_clicked(self):
		"""
		Internal callback function that is called each time clear button is clicked by the user.
		"""

		self._prop_list.setRowCount(0)

	def _on_graph_node_double_clicked(self, node):
		"""
		Internal callback function that is called each time a node within the linked graph is double clicked.

		:param tp.common.nodegraph.core.node.BaseNode node: double clicked node.
		"""

		if self.limit() == 0 or self._lock:
			return

		rows = self._prop_list.rowCount()
		if rows >= self.limit():
			self._prop_list.removeRow(rows - 1)

		itm_find = self._prop_list.findItems(node.id, Qt.MatchExactly)
		if itm_find:
			self._prop_list.removeRow(itm_find[0].row())

		self._prop_list.insertRow(0)
		prop_widget = NodePropWidget(node=node)
		prop_widget.propertyChanged.connect(self._on_property_widget_changed)
		prop_widget.propertyClosed.connect(self._on_property_closed)
		self._prop_list.setCellWidget(0, 0, prop_widget)

		item = QTableWidgetItem(node.id)
		self._prop_list.setItem(0, 0, item)
		self._prop_list.selectRow(0)

	def _on_graph_node_deleted(self, nodes):
		"""
		Internal callback function that is called each time nodes are deleted in the linked graph.

		:param list[str] nodes: list of deleted node IDs.
		"""

		[self._on_property_closed(n) for n in nodes]

	def _on_graph_node_property_changed(self, node, property_name, property_value):
		"""
		Internal callback function that is called each time a node property is changed.

		:param tp.common.nodegraph.core.node.BaseNode node: node.
		:param property_name: node property name.
		:param property_value: node property value.
		"""

		properties_widget = self.property_widget(node)
		if not properties_widget:
			return

		property_window = properties_widget.get_widget(property_name)

		if property_window and property_value != property_window.value():
			self._block_signal = True
			property_window.set_value(property_value)
			self._block_signal = False

	def _on_property_widget_changed(self, node_id, property_name, property_value):
		"""
		Internal callback function that is called when a property widget value has changed.

		:param str node_id: node id.
		:param str property_name: node property name.
		:param object property_value: node property value.
		"""

		if not self._block_signal:
			self.propertyChanged.emit(node_id, property_name, property_value)


class PropertiesList(QTableWidget):

	def __init__(self, parent=None):
		super(PropertiesList, self).__init__(parent)
		self.setItemDelegate(PropertiesListDelegate())
		self.setColumnCount(1)
		self.setShowGrid(False)
		self.verticalHeader().hide()
		self.horizontalHeader().hide()

		QHeaderView.setSectionResizeMode(self.verticalHeader(), QHeaderView.ResizeToContents)
		QHeaderView.setSectionResizeMode(self.horizontalHeader(), 0, QHeaderView.Stretch)
		self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def wheelEvent(self, event):
		delta = event.delta() * 0.2
		self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta)


class PropertiesListDelegate(QStyledItemDelegate):

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def paint(self, painter, option, index):

		painter.save()
		painter.setRenderHint(QPainter.Antialiasing, False)
		painter.setPen(Qt.NoPen)

		bg_clr = option.palette.midlight().color()
		painter.setBrush(QBrush(bg_clr))
		painter.drawRect(option.rect)

		border_width = 1
		if option.state & QStyle.State_Selected:
			bdr_clr = option.palette.highlight().color()
			painter.setPen(QPen(bdr_clr, 1.5))
		else:
			bdr_clr = option.palette.alternateBase().color()
			painter.setPen(QPen(bdr_clr, 1))

		painter.setBrush(Qt.NoBrush)
		painter.drawRect(QRect(
			option.rect.x() + border_width,
			option.rect.y() + border_width,
			option.rect.width() - (border_width * 2),
			option.rect.height() - (border_width * 2))
		)
		painter.restore()


class NodePropWidget(QWidget):
	"""
	Node properties widget for display a Node object.
	"""

	propertyChanged = Signal(str, str, object)
	propertyClosed = Signal(str)

	def __init__(self, parent=None, node=None):
		super(NodePropWidget, self).__init__(parent)
		self._node_id = node.id
		self.__tab_windows = {}
		self.__tab = QTabWidget()

		close_btn = QPushButton()
		close_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCancelButton))
		close_btn.setMaximumWidth(40)
		close_btn.setToolTip('close property')
		close_btn.clicked.connect(self._on_close_button_clicked)

		self.name_wgt = base.PropLineEdit()
		self.name_wgt.setToolTip('name')
		self.name_wgt.set_value(node.name())
		self.name_wgt.valueChanged.connect(self._on_property_changed)

		self.type_wgt = QLabel(node.type_)
		self.type_wgt.setAlignment(Qt.AlignRight)
		self.type_wgt.setToolTip('type_')
		font = self.type_wgt.font()
		font.setPointSize(10)
		self.type_wgt.setFont(font)

		name_layout = QHBoxLayout()
		name_layout.setContentsMargins(0, 0, 0, 0)
		name_layout.addWidget(QLabel('name'))
		name_layout.addWidget(self.name_wgt)
		name_layout.addWidget(close_btn)
		layout = QVBoxLayout(self)
		layout.setSpacing(4)
		layout.addLayout(name_layout)
		layout.addWidget(self.__tab)
		layout.addWidget(self.type_wgt)
		self._read_node(node)

	def __repr__(self):
		return '<{} object at {}>'.format(self.__class__.__name__, hex(id(self)))

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def add_tab(self, name):
		"""
		Adds a new tab.

		:param str name: tab name.
		"""

		if name in self.__tab_windows.keys():
			raise AssertionError('Tab name {} already taken!'.format(name))
		self.__tab_windows[name] = PropertiesContainer(self)
		self.__tab.addTab(self.__tab_windows[name], name)
		return self.__tab_windows[name]

	def node_id(self):
		"""
		Returns the node ID linked to this widget.

		:return: node ID.
		:rtype: str
		"""

		return self._node_id

	def add_widget(self, name, widget, tab='Properties'):
		"""
		Adds a new node property widget.

		:param str name: property name.
		:param base.BaseProperty widget: property widget.
		:param str tab: tab name.
		"""

		if tab not in self._widgets.keys():
			tab = 'Properties'
		window = self.__tab_windows[tab]
		window.add_widget(name, widget)
		widget.valueChanged.connect(self._on_property_changed)

	def get_widget(self, name):
		"""
		Returns the property widget with given name.

		:param str name: property name.
		:return: property widget.
		:rtype: base.BaseProperty or None
		"""

		if name == 'name':
			return self.name_wgt
		for _, prop_win in self.__tab_windows.items():
			widget = prop_win.get_widget(name)
			if widget:
				return widget

		return None

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _read_node(self, node):
		"""
		Internal function that populates widget UI based on the given node data.

		:param tp.common.nodegraph.core.node.BaseNode node: node instance.
		"""

		model = node.model
		graph_model = node.graph.model

		common_properties = graph_model.get_node_common_properties(node.type_)

		# sort tabs and properties.
		tab_mapping = defaultdict(list)
		for prop_name, prop_val in model.custom_properties.items():
			tab_name = model.get_tab_name(prop_name)
			tab_mapping[tab_name].append((prop_name, prop_val))

		# add tabs.
		for tab in sorted(tab_mapping.keys()):
			if tab != 'Node':
				self.add_tab(tab)

		# property widget factory.
		widget_factory = factory.NodePropertyWidgetFactory()

		# populate tab properties.
		for tab in sorted(tab_mapping.keys()):
			prop_window = self.__tab_windows[tab]
			for prop_name, value in tab_mapping[tab]:
				wid_type = model.get_widget_type(prop_name)
				if wid_type == 0:
					continue

				widget = widget_factory.get_widget(wid_type)
				if prop_name in common_properties.keys():
					if 'items' in common_properties[prop_name].keys():
						widget.set_items(common_properties[prop_name]['items'])
					if 'range' in common_properties[prop_name].keys():
						prop_range = common_properties[prop_name]['range']
						widget.set_min(prop_range[0])
						widget.set_max(prop_range[1])

				prop_window.add_widget(prop_name, widget, value, prop_name.replace('_', ' '))
				widget.valueChanged.connect(self._on_property_changed)

		# add "Node" tab properties.
		self.add_tab('Node')
		default_props = ['color', 'text_color', 'disabled', 'id']
		prop_window = self.__tab_windows['Node']
		for prop_name in default_props:
			wid_type = model.get_widget_type(prop_name)
			widget = widget_factory.get_widget(wid_type)
			prop_window.add_widget(prop_name, widget, model.get_property(prop_name), prop_name.replace('_', ' '))
			widget.valueChanged.connect(self._on_property_changed)

		self.type_wgt.setText(model.get_property('type_'))

	# ==================================================================================================================
	# CALLBACKS
	# ==================================================================================================================

	def _on_close_button_clicked(self):
		"""
		Internal callback function that is called when close button is clicked by the user.
		"""

		self.propertyClosed.emit(self._node_id)

	def _on_property_changed(self, name, value):
		"""
		Internal callback function that is called each time a property value changes.

		:param str name: name of the property.
		:param object value: new value of the property.
		"""

		self.propertyChanged.emit(self._node_id, name, value)


class PropertiesContainer(QWidget):
	"""
	Node properties container widget that displays nodes properties under a tab in the ``NodePropWidget`` widget.
	"""

	def __init__(self, parent=None):
		super(PropertiesContainer, self).__init__(parent)

		self.__layout = QGridLayout()
		self.__layout.setColumnStretch(1, 1)
		self.__layout.setSpacing(6)

		layout = QVBoxLayout(self)
		layout.setAlignment(Qt.AlignTop)
		layout.addLayout(self.__layout)

	def __repr__(self):
		return '<{} object at {}>'.format(self.__class__.__name__, hex(id(self)))

	def add_widget(self, name, widget, value, label=None):
		"""
		Adds a property widget to the window.

		:param str name: property name to be displayed.
		:param base.BaseProperty widget: property widget instance.
		:param object value: property value.
		:param str or None label: optional custom label to display.
		:return:
		"""

		widget.setToolTip(name)
		widget.set_value(value)
		if label is None:
			label = name
		row = self.__layout.rowCount()
		if row > 0:
			row += 1

		label_flags = Qt.AlignCenter | Qt.AlignRight
		if widget.__class__.__name__ == 'PropTextEdit':
			label_flags = label_flags | Qt.AlignTop

		self.__layout.addWidget(QLabel(label), row, 0, label_flags)
		self.__layout.addWidget(widget, row, 1)

	def get_widget(self, name):
		"""
		Returns the property widget from given name.

		:param str name: property name.
		:return: property widget.
		:rtype: QWidget
		"""

		for row in range(self.__layout.rowCount()):
			item = self.__layout.itemAtPosition(row, 1)
			if item and name == item.widget().toolTip():
				return item.widget()
