#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains basic graph object implementation
"""

import os
import re
import sys
import json
import importlib.util

from Qt.QtCore import Signal, QObject, QPoint, QMimeData
from Qt.QtWidgets import QApplication, QUndoStack, QUndoView

from tp.core import log
from tp.common.python import path
from tp.common.nodegraph.core import consts, utils, factory, abstract, node, socket, commands, menus
from tp.common.nodegraph.models import graph as graph_model
from tp.common.nodegraph.views import graph as graph_view
from tp.common.nodegraph.widgets import graph as graph_widget
from tp.common.nodegraph.nodes import backdrop, inout, branch, logger as logger_node

logger = log.tpLogger


class NodeGraph(QObject):
	"""
	Base NodeGraph class main controller that handles all nodes within a node graph.
	"""

	nodeCreated = Signal(abstract.Node)  # Signal triggered when a node is created in the node graph.
	nodeSelected = Signal(abstract.Node)  # signal triggered when a node is clicked with the left mouse button.
	nodeSelectionChanged = Signal(list, list)  # signal triggered when the node selection has changed.
	nodeDoubleClicked = Signal(abstract.Node)  # signal triggered when a node is double clicked.
	nodesDeleted = Signal(list)  # signal triggered when nodes have been delete from the node graph.
	socketConnected = Signal(socket.Socket, socket.Socket)  # signal triggered when a node socket is connected.
	socketDisconnected = Signal(socket.Socket, socket.Socket)  # signal triggered when a node socket is disconnected.
	propertyChanged = Signal(abstract.Node, str, object)  # signal triggered when a node property changes.
	sessionChanged = Signal(str)  # signal that is triggered when session has been changed.
	dataDropped = Signal(QMimeData, QPoint)  # signal triggered when data has been dropped to the graph.

	def __init__(
			self, parent=None, model=None, graph_viewer=None, layout_direction=None, nodes_factory=None,
			undo_stack=None):
		super(NodeGraph, self).__init__(parent=parent)

		self.setObjectName('NodeGraph')

		self._model = model or graph_model.NodeGraphModel()
		if layout_direction:
			if layout_direction not in (consts.GraphLayoutDirection.HORIZONTAL, consts.GraphLayoutDirection.VERTICAL):
				layout_direction = consts.GraphLayoutDirection.HORIZONTAL
			self._model.layout_direction = layout_direction
		else:
			layout_direction = self._model.layout_direction
		self._nodes_factory = nodes_factory or factory.NodesFactory()
		self._undo_view = None
		self._undo_stack = undo_stack or QUndoStack(parent=self)
		self._widget = None
		self._editable = True
		self._is_executing = False
		self._sub_graphs = dict()
		self._viewer = graph_viewer or graph_view.NodeGraphView(undo_stack=self._undo_stack)
		self._viewer.set_layout_direction(layout_direction)
		self._auto_update = True

		self._context_menu = dict()
		self._register_context_menu()
		self._register_builtin_nodes()
		self._setup_signals()

	def __repr__(self):
		return '<{}("root") object at {}>'.format(self.__class__.__name__, hex(id(self)))

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def model(self):
		"""
		Returns the model used for storing the graph data.

		:return:  graph scene model.
		:rtype: GraphSceneModel
		"""

		return self._model

	@property
	def widget(self):
		"""
		Returns the graph widget that can be added into a Qt layout.

		:return: node graph widget.
		:rtype: NodeGraphWidget
		"""

		if self._widget is None:
			self._widget = graph_widget.NodeGraphWidget()
			self._widget.addTab(self._viewer, 'Node Graph')
			tab_bar = self._widget.tabBar()
			for button_flag in [tab_bar.RightSide, tab_bar.LeftSide]:
				tab_button = tab_bar.tabButton(0, button_flag)
				if tab_button:
					tab_button.deleteLater()
					tab_bar.setTabButton(0, button_flag, None)
			self._widget.tabCloseRequested.connect(self._on_close_sub_graph_tab)

		return self._widget

	@property
	def nodes_factory(self):
		"""
		Returns the nodes factory object used by the node graph to create new nodes.

		:return: node factory.
		:rtype: NodeFactory
		"""

		return self._nodes_factory

	@property
	def editable(self):
		"""
		Returns whether node graph is editable.

		:return: True if node graph is editable; False otherwise.
		:rtype: bool
		"""

		return self._editable

	@editable.setter
	def editable(self, flag):
		"""
		Sets whether node graph is editable.

		:param bool flag: True if node graph is editable; False otherwise.
		"""

		self._editable = bool(flag)
		self._viewer.editable = self._editable

	@property
	def undo_view(self):
		"""
		Returns the node graph undo history list widget.

		:return: graph udno view.
		:rtype: QUndoView
		"""

		if self._undo_view is None:
			self._undo_view = QUndoView(self._undo_stack)
			self._undo_view.setWindowTitle('Undo History')

		return self._undo_view

	@property
	def auto_update(self):
		"""
		Returns whether this graph can be auto updated.

		:return: True if graph can be auto updated; False otherwise.
		:rtype: bool
		"""

		return self._auto_update

	@property
	def is_executing(self):
		"""
		Returns whether graph is being executed.

		:return: True if graph is being executed; False otherwise.
		:rtype: bool
		"""

		return self._is_executing

	@is_executing.setter
	def is_executing(self, flag):
		"""
		Sets whether graph is being executed.

		:param bool flag: True if graph is being executed; False otherwise.
		"""

		self._is_executing = flag

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def show(self):
		"""
		Shows the node graph widget.
		"""

		self.widget.show()

	def close(self):
		"""
		Closes node graph view widget.
		"""

		self.widget.close()

	def viewer(self):
		"""
		Returns the internal view interface used bvy the node graph.

		:return: node graph viewer.
		:rtype: NodeGraphViewer
		"""

		return self._viewer

	def scene(self):
		"""
		Returns graphics scene used in the node graph.

		:return: node graph scene.
		:rtype: NodeGraphScene
		"""

		return self._viewer.scene()

	def is_acyclic(self):
		"""
		Returns True if the current node graph is acyclic.

		:return: True if graph is acyclic; False otherwise.
		:rtype: bool
		"""

		return self._model.acyclic

	def set_acyclic(self, flag):
		"""
		Sets whether this graph is acyclic.

		:param bool flag: True to make graph acyclic; False otherwise.
		"""

		self._model.acyclic = flag
		self._viewer.acyclic = flag

	def background_color(self):
		"""
		Returns node graph background color.

		:return: RGB background color.
		:rtype: tuple(float, float, float)
		"""

		return self.scene().background_color

	def set_background_color(self, r, g, b):
		"""
		Sets RGB background color.

		:param float r: red channel color value.
		:param float g: green channel color value.
		:param float b: blue channel color value.
		"""

		self.scene().background_color = (r, g, b)
		self._viewer.force_update()

	def grid_color(self):
		"""
		Returns node graph grid color.

		:return: RGB grid color.
		:rtype: tuple(float, float, float)
		"""

		return self.scene().grid_color

	def set_grid_color(self, r, g, b):
		"""
		Sets node graph grid color.

		:param float r: red channel color value.
		:param float g: green channel color value.
		:param float b: blue channel color value.
		"""

		self.scene().grid_color = (r, g, b)
		self._viewer.force_update()

	def set_grid_mode(self, mode):
		"""
		Sets node graph grid mode. Grid modes:
			* 0: none.
			* 1: dots.
			* 2: lines.

		:param nit mode: grid mode.
		"""

		display_types = [
			consts.NodeGraphViewStyle.GRID_DISPLAY_NONE,
			consts.NodeGraphViewStyle.GRID_DISPLAY_DOTS,
			consts.NodeGraphViewStyle.GRID_DISPLAY_LINES,
		]
		if mode not in display_types:
			mode = consts.NodeGraphViewStyle.GRID_DISPLAY_LINES

		self.scene().grid_mode = mode
		self._viewer.force_update()

	def add_properties_editor(self, properties_editor):
		"""
		Wires up a properties editor widget to this node graph instance.

		:param tp.common.nodegraph.editors.propertieseditor.PropertiesEditorWidget. properties_editor: properties editor
			widget instance.
		"""

		properties_editor.propertyChanged.connect(self._on_properties_editor_property_changed)

	def remove_properties_editor(self, properties_editor):
		"""
		Disconnects a properties editor from this graph instance.

		:param tp.common.nodegraph.editors.propertieseditor.PropertiesEditorWidget properties_editor: properties edidtor
			widget to disconnect.
		"""

		properties_editor.propertyChanged.disconnect(self._on_properties_editor_property_changed)

	def current_session(self):
		"""
		Returns the file path pointing to the current loaded session.

		:return: session file path.
		:rtype: str
		"""

		return self._model.session

	def load_session(self, file_path):
		"""
		Loads node graph session layout file.

		:param str file_path: path to the serialized layout file.
		:raises IOError: if the given file path does not exist.
		"""

		file_path = file_path.strip()
		if not path.is_file(file_path):
			raise IOError('File does not exist: {}'.format(file_path))

		self.clear_selection()
		self.import_session(file_path)

	def import_session(self, file_path):
		"""
		Imports node graph session layout file.

		:param str file_path: path to the serialized layout file.
		:raises IOError: if the given file path does not exist.
		"""

		file_path = file_path.strip()
		if not path.is_file(file_path):
			raise IOError('File does not exist: {}'.format(file_path))

		try:
			with open(file_path) as data_file:
				data = json.load(data_file)
		except Exception as exc:
			data = None
			logger.error('Cannot read data from file: {}'.format(exc))
		if not data:
			return

		self._deserialize(data)
		self._undo_stack.clear()
		self._model.session = file_path

		self.sessionChanged.emit(file_path)

	def save_session(self, file_path):
		"""
		Saves current node graph session layout into a JSON compatible file.

		:param str file_path: path to save node layout.
		"""

		data = self._serialize(self.all_nodes())
		file_path = file_path.strip()
		with open(file_path, 'w') as file_out:
			json.dump(data, file_out, indent=1, separators=(',', ':'))

	def clear_session(self):
		"""
		Clears the current node graph session.
		"""

		for n in self.all_nodes():
			if isinstance(n, node.BaseNode):
				for input_socket in n.input_sockets():
					if input_socket.locked():
						input_socket.set_locked(False, connected_sockets=False)
					input_socket.clear_connections()
				for output_socket in n.output_sockets():
					if output_socket.locked():
						output_socket.set_locked(False, connected_sockets=False)
					output_socket.clear_connections()
			self._undo_stack.push(commands.NodeRemovedCommand(self, n))
		self._undo_stack.clear()
		self._model.session = ''

	def toggle_node_search(self):
		"""
		Toggles node search widget visibility.
		"""

		if not self._viewer or not self._viewer.underMouse():
			return

		self._viewer.tab_search_set_nodes(self._nodes_factory.names)
		self._viewer.tab_search_toggle()

	# ==================================================================================================================
	# NODES
	# ==================================================================================================================

	def register_node(self, node_class, alias=None):
		"""
		Registers the given node class within this graph node factory.

		:param class node_class: BaseNode class to register.
		:param str alias: optional custom alias name for the node type.
		"""

		self._nodes_factory.register_node(node_class, alias=alias)
		self._viewer.rebuild_tab_search()

	def register_nodes(self, node_classes):
		"""
		Registers the given nodes within this graph node factory.

		:param list node_classes: list of node classes to register.
		"""

		[self._nodes_factory.register_node(node_class) for node_class in node_classes]
		self._viewer.rebuild_tab_search()

	def get_registered_nodes(self):
		"""
		Returns a list of all node types that have been registered within this graph.

		:return: list of node type identifiers.
		:rtype: list(str)
		"""

		return sorted(list(self._nodes_factory.nodes.keys()))

	def unique_name(self, name):
		"""
		Returns a unique node name to avoid having nodes with the same name within a graph.

		:param str name: base node name.
		:return: unique node name.
		:rtype: str
		"""

		name = ' '.join(name.split())
		node_names = [n.name() for n in self.all_nodes()]
		if name not in node_names:
			return name

		regex = re.compile(r'[\w ]+(?: )*(\d+)')
		search = regex.search(name)
		if not search:
			for i in range(1, len(node_names) + 2):
				new_name = '{} {}'.format(name, i)
				if new_name not in node_names:
					return new_name

		version = search.group(1)
		name = name[:len(version) * -1].strip()
		for i in range(1, len(node_names) + 2):
			new_name = '{} {}'.format(name, i)
			if new_name not in node_names:
				return new_name

		return name + '_'

	def create_node(self, node_type, name=None, selected=True, color=None, text_color=None, pos=None, push_undo=True):
		"""
		Creates a new node within the node graph.

		:param str node_type: type of the node we want to create.
		:param str name: name of the node.
		:param bool selected: whether node will be selected by default once created.
		:param tuple(int, int, int) or str color: node color in 0 to 255 range or as a hexadecimal color.
		:param tuple(int, int, int) or str text_color: node text color in 0 to 255 range or as a hexadecimal color.
		:param tuple(int, int) pos: initial X, Y position of the node withing the graph scene.
		:param bool push_undo: whether creat node operation should be added into the undo queue.
		:return: newly created instance node.
		:rtype: BaseNode
		"""

		if not self._editable:
			return None

		new_node = self._nodes_factory.create_node_instance(node_type)
		if not new_node:
			raise Exception('\n\nCannot create new node of type:\t{}\n'.format(node_type))

		new_node.graph = self
		new_node.model.graph_model = self.model

		# update node internal attributes
		widget_types = new_node.model.__dict__.pop('_TEMP_property_widget_types', None)
		property_attributes = new_node.model.__dict__.pop('_TEMP_property_attributes', None)
		if self.model.get_node_common_properties(new_node.type_) is None:
			node_attributes = {new_node.type_: {n: {'widget_type': wgt} for n, wgt in widget_types.items()}}
			for property_name, attributes in property_attributes.items():
				node_attributes[new_node.type_][property_name].update(attributes)
			self.model.set_node_common_properties(node_attributes)

		# update base model attributes
		new_node.NODE_NAME = self.unique_name(name or new_node.NODE_NAME)
		new_node.model.name = new_node.NODE_NAME
		new_node.model.selected = selected

		# update color and position node model values
		if color:
			new_node.model.color = utils.format_color(color)
		if text_color:
			new_node.model.text_color = utils.format_color(text_color)
		if pos:
			new_node.model.pos = [float(pos[0]), float(pos[1])]

		# update node view from model
		new_node.update()

		if push_undo:
			undo_command = commands.NodeAddedCommand(graph=self, node=new_node, pos=new_node.model.pos)
			undo_command.setText('Create Node: "{}"'.format(new_node.NODE_NAME))
			self._undo_stack.push(undo_command)
		else:
			commands.NodeAddedCommand(graph=self, node=new_node, pos=new_node.model.pos).redo()

		self.nodeCreated.emit(new_node)

		return new_node

	def node_by_id(self, node_id):
		"""
		Returns the node from the given node ID string.

		:param str node_id: node id.
		:return: found node with given id within this graph.
		:rtype: Node or None
		"""

		return self._model.nodes.get(node_id, None)

	def node_by_name(self, name):
		"""
		Returns node that matches given name.

		:param str name: name of the node.
		:return: found node with given name within this graph.
		:rtype: Node or None
		"""

		for node_found in self._model.nodes.items():
			if node_found.name() == name:
				return node_found

		return None

	def nodes_by_type(self, node_type):
		"""
		Returns all nodes by their given node type.

		:param str node_type: node type to look for.
		:return: found nodes with given type.
		:rtype: list(NodeObject)
		"""

		return [found_node for found_node in self._model.nodes.values() if found_node.type_ == node_type]

	def all_nodes(self):
		"""
		Returns all nodes within this node graph.

		:return: list of nodes.
		:rtype: list(BaseNode)
		"""

		return list(self._model.nodes.values())

	def selected_nodes(self):
		"""
		Returns all selected nodes that are withing this node graph.

		:return: list of selected nodes.
		:rtype: list(BaseNode)
		"""

		selected_nodes = list()
		for node_view in self._viewer.selected_nodes():
			selected_node = self._model.nodes[node_view.id]
			selected_nodes.append(selected_node)

		return selected_nodes

	def select_all_nodes(self):
		"""
		Select all the nodes in the node graph.
		"""

		self._undo_stack.beginMacro('Select All Nodes')
		[node_found.set_selected(True) for node_found in self.all_nodes()]
		self._undo_stack.endMacro()

	def clear_selection(self):
		"""
		Clears the selection in the node graph.
		"""

		self._undo_stack.beginMacro('Clear Selection')
		[node_found.set_selected(False) for node_found in self.all_nodes()]
		# [connector.setSelected(False) for connector in self._viewer.get_all_connectors()]
		self._undo_stack.endMacro()

	def fit_to_selection(self):
		"""
		Sets the zoom level to fit the current selected nodes. If no nodes are selected, then all nodes in the graph
		will be framed.
		"""

		nodes = self.selected_nodes() or self.all_nodes()
		if not nodes:
			return
		self._viewer.zoom_to_nodes([n.view for n in nodes])

	def set_zoom(self, zoom):
		"""
		Sets the zoom factor of the node graph viewer.

		:param float zoom: zoom factor.
		"""

		self._viewer.set_zoom(zoom)

	def reset_zoom(self):
		"""
		Resets zoom level.
		"""

		self._viewer.reset_zoom()

	def get_zoom(self):
		"""
		Returns current zoom level on the node graph.

		:return: current zoom level.
		:rtype: float
		"""

		return self._viewer.get_zoom()

	def center_on(self, nodes=None):
		"""
		Centers the node graph on teh given nodes or all nodes by default.

		:param list[tp.common.nodegraph.core.nodeBaseNode] nodes: list of nodes to center on.
		"""

		nodes = nodes or list()
		self._viewer.center_selection([n.view for n in nodes])

	def center_selection(self):
		"""
		Centers on the current selected nodes.
		"""

		self._viewer.center_selection(self._viewer.selected_nodes())

	def auto_layout_nodes(self, nodes=None, down_stream=True, start_nodes=None):
		"""
		Auto layout nodes in the node graph.

		:param list[tp.common.nodegraph.core.node.BaseNode] nodes: list of nodes to auto layout.
		:param bool down_stream: whether to layout down stream or upstream.
		:param list[tp.common.nodegraph.core.node.BaseNode] start_nodes: optional list of nodes to start the auto layout
			from.
		"""

		self.begin_undo('Auto Layout Nodes')

		viewer = self.viewer()
		nodes = nodes or self.all_nodes()

		# filter out the backdrops.
		backdrops = {n: n.nodes() for n in nodes if isinstance(n, backdrop.BackdropNode)}
		filtered_nodes = [n for n in nodes if not isinstance(n, backdrop.BackdropNode)]

		start_nodes = start_nodes or list()
		if down_stream:
			start_nodes += [n for n in filtered_nodes if not any(n.connected_input_nodes().values())]
		else:
			start_nodes += [n for n in filtered_nodes if not any(n.connected_output_nodes().values())]
		if not start_nodes:
			return

		node_views = [n.view for n in nodes]
		nodes_center_0 = self.viewer().nodes_rect_center(node_views)
		nodes_rank = utils.compute_node_rank(start_nodes, down_stream)

		rank_map = {}
		for node, rank in nodes_rank.items():
			if rank in rank_map:
				rank_map[rank].append(node)
			else:
				rank_map[rank] = [node]

		if viewer.layout_direction() is consts.GraphLayoutDirection.HORIZONTAL:
			current_x = 0
			node_height = 120
			for rank in sorted(range(len(rank_map)), reverse=not down_stream):
				ranked_nodes = rank_map[rank]
				max_width = max([node.view.width for node in ranked_nodes])
				current_x += max_width
				current_y = 0
				for idx, node in enumerate(ranked_nodes):
					dy = max(node_height, node.view.height)
					current_y += 0 if idx == 0 else dy
					node.set_pos(current_x, current_y)
					current_y += dy * 0.5 + 10

				current_x += max_width * 0.5 + 100
		elif viewer.layout_direction() is consts.GraphLayoutDirection.VERTICAL:
			current_y = 0
			node_width = 250
			for rank in sorted(range(len(rank_map)), reverse=not down_stream):
				ranked_nodes = rank_map[rank]
				max_height = max([node.view.height for node in ranked_nodes])
				current_y += max_height
				current_x = 0
				for idx, node in enumerate(ranked_nodes):
					dx = max(node_width, node.view.width)
					current_x += 0 if idx == 0 else dx
					node.set_pos(current_x, current_y)
					current_x += dx * 0.5 + 10

				current_y += max_height * 0.5 + 100

		nodes_center_1 = self.viewer().nodes_rect_center(node_views)
		dx = nodes_center_0[0] - nodes_center_1[0]
		dy = nodes_center_0[1] - nodes_center_1[1]
		[n.set_pos(n.x_pos() + dx, n.y_pos() + dy) for n in nodes]

		# wrap the backdrop nodes.
		for backdrop_node, contained_nodes in backdrops.items():
			backdrop_node.wrap_nodes(contained_nodes)

		self.end_undo()

	def add_node(self, node_to_add, pos=None, selected=True, push_undo=True):
		"""
		Adds given node into the graph.

		:param tp.common.nodegraph.core.node.BaseNode node_to_add: node instance to add into the node graph.
		:param list(float) or None pos: node X,Y position.
		:param bool or None selected: whether added node should be selected.
		:param bool push_undo: whether to push add node command into undo stack.
		:return:
		"""

		assert isinstance(node_to_add, abstract.Node), 'Node must be instance of Node'

		widget_types = node_to_add.model.__dict__.pop('_TEMP_property_widget_types')
		property_attrs = node_to_add.model.__dict__.pop('_TEMP_property_attributes')

		if self.model.get_node_common_properties(node_to_add.type_) is None:
			node_attrs = {node_to_add.type_: {n: {'widget_type': wt} for n, wt in widget_types.items()}}
			self.model.set_node_common_properties(node_attrs)

		node_to_add.graph = self
		node_to_add.NODE_NAME = self.unique_name(node_to_add.NODE_NAME)
		node_to_add.model.graph_model = self.model
		node_to_add.model.name = node_to_add.NODE_NAME
		node_to_add.update()

		if push_undo:
			self._undo_stack.beginMacro('Add Node: {}'.format(node_to_add.name()))
			self._undo_stack.push(commands.NodeAddedCommand(self, node_to_add, pos))
			if selected:
				node_to_add.set_selected(True)
			self._undo_stack.endMacro()
		else:
			commands.NodeAddedCommand(self, node_to_add, pos).redo()

	def copy_nodes(self, nodes=None):
		"""
		Copies nodes to the clipboard.

		:param list[tp.common.nodegraph.core.node.BaseNode] nodes: list of nodes to copy. If not given, currently
			selected nodes will be copied.
		:return: True if the copy nodes operation was successful; False otherwise.
		:rtype: bool
		"""

		nodes = nodes or self.selected_nodes()
		if not nodes:
			return False

		clipboard = QApplication.clipboard()
		serial_data = self._serialize(nodes)
		serial_str = json.dumps(serial_data)
		if not serial_str:
			return False

		clipboard.setText(serial_str)
		return True

	def cut_nodes(self, nodes=None):
		"""
		Cuts nodes to the clipboard.

		:param list[tp.common.nodegraph.core.node.BaseNode] nodes: list of nodes to cut. If not given, currently
			selected nodes will be copied.
		:return: True if the cut nodes operation was successful; False otherwise.
		:rtype: bool
		"""

		nodes = nodes or self.selected_nodes()
		if not nodes:
			return False

		result = self.copy_nodes(nodes)
		if not result:
			return False

		self._undo_stack.beginMacro('Cut Nodes')
		[self._undo_stack.push(commands.NodeRemovedCommand(self, n)) for n in nodes]
		self._undo_stack.endMacro()

		return True

	def paste_nodes(self):
		"""
		Paste nodes copied from the clipboard into this node graph.
		"""

		clipboard = QApplication.clipboard()
		clipboard_text = clipboard.text() if clipboard else ''
		if not clipboard_text:
			return

		try:
			data = json.loads(clipboard_text)
		except json.decoder.JSONDecodeError as exc:
			logger.error('Canont decode clipboard data:\n{}'.format(clipboard_text))
			return

		self._undo_stack.beginMacro('Paste Nodes')
		self.clear_selection()
		nodes = self._deserialize(data, relative_pos=True)
		[n.set_selected(True) for n in nodes]
		self._undo_stack.endMacro()

	def duplicate_nodes(self, nodes):
		"""
		Creates a duplicate copy from the given list of nodes.

		:param list[tp.common.nodegraph.core.node.BaseNode] nodes: list of nodes to duplicate.
		:return: list of duplicated nodes instances.
		:rtype: list[tp.common.nodegraph.core.node.BaseNode]
		"""

		if not nodes:
			return

		self._undo_stack.beginMacro('Duplicate Nodes')
		data = self._serialize(nodes)
		new_nodes = self._deserialize(data)
		offset = 50
		for n in new_nodes:
			x, y = n.pos()
			n.set_pos(x + offset, y + offset)
			n.set_property('selected', True)
		self._undo_stack.endMacro()

		return new_nodes

	def disable_nodes(self, nodes, mode=None):
		"""
		Sets whether to disable or enable given nodes.

		:param list[tp.common.nodegraph.core.node.BaseNode] nodes: list of nodes to enable/disable.
		:param bool mode: optional disable state of the nodes.
		"""

		if not nodes:
			return

		if mode is None:
			mode = not nodes[0].disabled()

		if len(nodes) > 1:
			text = {False: 'enable', True: 'disable'}[mode]
			text = '{} ({}) Nodes'.format(text, len(nodes))
			self._undo_stack.beginMacro(text)
			[n.set_disabled(mode) for n in nodes]
			self._undo_stack.endMacro()
			return
		nodes[0].set_disabled(mode)

	def delete_node(self, node_to_delete, push_undo=True):
		"""
		Removes given node from the node graph.

		:param tp.common.nodegraph.core.node.BaseNode node_to_delete: node to delete.
		:param bool push_undo: whether to push delete nodes command into undo stack.
		"""

		assert isinstance(node_to_delete, abstract.Node), 'Node must be a instance of Node'

		if push_undo:
			self._undo_stack.beginMacro('Delete Node: {}'.format(node_to_delete.name()))

		if isinstance(node_to_delete, node.BaseNode):
			for input_socket in node_to_delete.input_sockets():
				if input_socket.locked():
					input_socket.set_locked(False, connected_sockets=False, push_undo=push_undo)
				input_socket.clear_connections(push_undo=push_undo)
			for output_socket in node_to_delete.output_sockets():
				if output_socket.locked():
					output_socket.set_locked(False, connected_sockets=False, push_undo=push_undo)
				output_socket.clear_connections(push_undo=push_undo)

		if push_undo:
			self._undo_stack.push(commands.NodeRemovedCommand(self, node_to_delete))
			self._undo_stack.endMacro()
		else:
			commands.NodeRemovedCommand(self, node_to_delete).redo()

		self.nodesDeleted.emit([node_to_delete.id])

	def delete_nodes(self, nodes, push_undo=True):
		"""
		Deletes given list of nodes from the node graph.

		:param list[tp.common.nodegraph.core.node.BaseNode] nodes: list of nodes to delete.
		:param bool push_undo: whether to push delete nodes command into undo stack.
		"""

		if not nodes:
			return

		if len(nodes) == 1:
			self.delete_node(nodes[0], push_undo=push_undo)
			return

		node_ids = [n.id for n in nodes]
		if push_undo:
			self._undo_stack.beginMacro('Deleted "{}" nodes'.format(len(nodes)))

		for node_to_delete in nodes:
			if isinstance(node_to_delete, node.BaseNode):
				for input_socket in node_to_delete.input_sockets():
					if input_socket.locked():
						input_socket.set_locked(False, connected_sockets=False, push_undo=push_undo)
					input_socket.clear_connections(push_undo=push_undo)
				for output_socket in node_to_delete.output_sockets():
					if output_socket.locked():
						output_socket.set_locked(False, connected_sockets=False, push_undo=push_undo)
					output_socket.clear_connections(push_undo=push_undo)
			if push_undo:
				self._undo_stack.push(commands.NodeRemovedCommand(self, node_to_delete))
			else:
				commands.NodeRemovedCommand(self, node_to_delete)

		if push_undo:
			self._undo_stack.endMacro()

		self.nodesDeleted.emit(node_ids)

	# ==================================================================================================================
	# CONNECTORS
	# ==================================================================================================================

	def connector_collision(self):
		"""
		Returns whether connector collision is enabled.

		:return: True if connectro collision is enabled; False otherwise.
		:rtype: bool
		"""

		return self._model.connector_collision

	def set_connector_collision(self, flag):
		"""
		Sets whether connector collision is enabled. If True, dragging a node over a connector will allow the node
		to be inserted as a new connection between the connector.

		:param bool flag: True to enable connector collision; False otherwise.
		"""

		self._model.connector_collision = flag
		self._viewer.connector_collision = flag

	def set_connector_style(self, style):
		"""
		Sets node graph connectors draw style. Available styles are:
			* 0: straight.
			* 1: curve.
			* 2: angle.

		:param int style: connector style.
		"""

		connector_max = max(
			[consts.ConnectorLayoutStyles.CURVED, consts.ConnectorLayoutStyles.STRAIGHT,
			 consts.ConnectorLayoutStyles.ANGLE])
		style = style if 0 <= style <= connector_max else consts.ConnectorLayoutStyles.CURVED
		self._viewer.set_connector_layout(style)

	# ==================================================================================================================
	# UNDO STACK
	# ==================================================================================================================

	def undo_stack(self):
		"""
		Returns undo stack used in the node graph.

		:return: node graph undo stack.
		:rtype: QUndoStack
		"""

		return self._undo_stack

	def clear_undo_stack(self):
		"""
		Clears the node graph undo stack history.
		"""

		self._undo_stack.clear()

	def begin_undo(self, name):
		"""
		Starts an undo block.

		:param str name: name for the undo block.

		..warning:: must be followed by an end_undo call.
		"""

		self._undo_stack.beginMacro(name)

	def end_undo(self):
		"""
		Ends of an undo block started by begin_undo function call.
		"""

		self._undo_stack.endMacro()

	# ==================================================================================================================
	# CONTEXT MENUS
	# ==================================================================================================================

	def context_menu(self):
		"""
		Returns the context menu for the node graph.

		:return: context menu object.
		:rtype: tp.common.nodegraph.core.menus.NodeGraphMenu
		"""

		return self.context_menu_by_name('graph')

	def context_nodes_menu(self):
		"""
		Returns the context menu for the nodes.

		:return: context menu object.
		:rtype: tp.common.nodegraph.core.menus.NodesMenu
		"""

		return self.context_menu_by_name('nodes')

	def context_menu_by_name(self, menu_name):
		"""
		Returns the context menu specified by the given name. Supported menu types are:
			- "graph": context menu from the node graph.
			- "nodes": context menu for the nodes.

		:param str menu_name: menu name.
		:return: context menu object.
		:rtype: tp.common.nodegraph.core.menus.NodeGraphMenu or tp.common.nodegraph.core.menus.NodesMenu or None
		"""

		return self._context_menu.get(menu_name)

	def set_context_menu(self, menu_name, data):
		"""
		Populates a context menu from the given serialized data. Example of menu

		:param str menu_name: name of the parent context menu to populate under.
		:param dict data: serialized menu data.
		"""

		context_menu = self.context_menu_by_name(menu_name)
		self._deserialize_context_menu(context_menu, data)

	def set_context_menu_from_file(self, file_path, menu_name=None):
		"""
		Populates a context menu from given serialized JSON file.

		:param str file_path: menu commands JSON file.
		:param str menu_name: optional name of the parent context menu to populate under.
		:raises IOError: if given file path does not exist.
		"""

		file_path = os.path.abspath(file_path)
		menu_name = menu_name or 'graph'
		if not os.path.isfile(file_path):
			raise IOError('File does not exist: {}'.format(file_path))

		with open(file_path) as open_file:
			data = json.load(open_file)

		context_menu = self.context_menu_by_name(menu_name)
		self._deserialize_context_menu(context_menu, data, root_path=os.path.dirname(file_path))

	def disable_context_menu(self, disabled=True, name='all'):
		"""
		Disables/Enables context menus from the node graph. Menu types:
			- all: all context menus from the node graph.
			- graph: context menu from the node graph.
			- nodes: context menu for the nodes.

		:param bool disabled: whether to enable or disable the context menus.
		:param str name: context menu to disable.
		"""

		if name == 'all':
			for _, menu in self._viewer.context_menus().items():
				menu.setDisabled(disabled)
				menu.setVisible(not disabled)
			return
		context_menus = self._viewer.context_menus()
		if context_menus.get(name):
			context_menus[name].setDisabled(disabled)
			context_menus[name].setVisible(not disabled)

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _setup_signals(self):
		"""
		Internal function that connects all signals for this graph.
		"""

		self._viewer.searchTriggered.connect(self._on_search_triggered)
		self._viewer.nodesMoved.connect(self._on_nodes_moved)
		self._viewer.connectionChanged.connect(self._on_connection_changed)
		self._viewer.connectionSliced.connect(self._on_connection_sliced)
		self._viewer.nodeDoubleClicked.connect(self._on_node_double_clicked)
		self._viewer.nodeNameChanged.connect(self._on_node_name_changed)
		self._viewer.nodeSelected.connect(self._on_node_selected)
		self._viewer.nodesSelectionChanged.connect(self._on_node_selection_changed)
		self._viewer.nodeBackdropUpdated.connect(self._on_node_backdrop_updated)
		self._viewer.dataDropped.connect(self._on_node_data_dropped)

	def _register_builtin_nodes(self):
		"""
		Internal function that register the default builtin nodes.
		"""

		self.register_node(backdrop.BackdropNode, alias='Backdrop')
		self.register_nodes([
			logger_node.PrintNode, logger_node.LoggerNode, branch.BranchNode
		])

	def _register_context_menu(self):
		"""
		Internal function that builds the menu commands for the graph context menu.
		"""

		if not self._viewer:
			return

		context_menus = self._viewer.context_menus()
		if context_menus.get('graph'):
			self._context_menu['graph'] = menus.NodeGraphMenu(self, context_menus['graph'])
		if context_menus.get('nodes'):
			self._context_menu['nodes'] = menus.NodesMenu(self, context_menus['nodes'])

	# =================================================================================================================
	# DIALOGS
	# =================================================================================================================

	def question_dialog(self, text, title='Node Graph'):
		"""
		Prompts a question dialog with "Yes" and "No" buttons in the node graph.

		:param str text: question text.
		:param str title: dialog window title.
		:return: True if "Yes" button was pressed; False otherwise.
		:rtype: bool
		"""

		return self._viewer.question_dialog(text, title)

	def message_dialog(self, text, title='Node Graph'):
		"""
		Prompts a message dialog in the node graph.

		:param str text: message text.
		:param str title: dialog window title.
		"""

		self._viewer.message_dialog(text, title)

	def load_dialog(self, current_directory=None, ext=None):
		"""
		Prompts a file open dialog in the node graph.

		:param str or None current_directory: optional path to a directory.
		:param str or NOne ext: optional custom file extension.
		:return: selected file path.
		:rtype: str
		"""

		return self._viewer.load_dialog(current_directory, ext)

	def save_dialog(self, current_directory=None, ext=None):
		"""
		Prompts a save file dialog in the node graph.

		:param str or None current_directory: optional path to a directory.
		:param str or NOne ext: optional custom file extension.
		:return: saved file path.
		:rtype: str
		"""

		return self._viewer.save_dialog(current_directory, ext)

	# =================================================================================================================
	# INTERNAL
	# =================================================================================================================

	def _serialize(self, nodes):
		"""
		Intenral function that serializes given nodes.

		:param list[tp.common.nodegraph.core.abstract.Node] nodes: nodes to serialize.
		:return: serialized graph data.
		"""

		data = {'graph': dict(), 'nodes': dict(), 'connections': list()}

		data['graph']['acyclic'] = self.is_acyclic()
		data['graph']['connector_collision'] = self.connector_collision()

		nodes_data = dict()
		for node_to_serialize in nodes:
			node_to_serialize.update_model()
			node_data = node_to_serialize.model.to_dict()
			nodes_data.update(node_data)

		for node_id, node_data in nodes_data.items():
			data['nodes'][node_id] = node_data

			inputs = node_data.pop('inputs', dict())
			outputs = node_data.pop('outputs', dict())
			for socket_name, connection_data in inputs.items():
				for connection_id, socket_names in connection_data.items():
					for connected_socket in socket_names:
						connection_data = {
							consts.SocketDirection.Input: [node_id, socket_name],
							consts.SocketDirection.Output: [connection_id, connected_socket]
						}
						if connection_data not in data['connections']:
							data['connections'].append(connection_data)
			for socket_name, connection_data in outputs.items():
				for connection_id, socket_names in connection_data.items():
					for connected_socket in socket_names:
						connection_data = {
							consts.SocketDirection.Output: [node_id, socket_name],
							consts.SocketDirection.Input: [connection_id, connected_socket]
						}
						if connection_data not in data['connections']:
							data['connections'].append(connection_data)

		if not data['connections']:
			data.pop('connections')

		return data

	def _deserialize(self, data, relative_pos=False, pos=None):
		"""
		Internal function that deserializes node data.

		:param dict data: node data.
		:param bool relative_pos: whether to position nodes relative to the cursor.
		:param tuple or list or None pos: custom X,Y position.
		"""

		for attr_name, attr_value in data.get('graph', dict()).items():
			if attr_name == 'acyclic':
				self.set_acyclic(attr_value)
			elif attr_name == 'connector_collision':
				self.set_connector_collision(attr_value)

		nodes = dict()
		for node_id, node_data in data.get('nodes', dict()).items():
			node_type = node_data['type_']
			name = node_data.get('name')
			new_node = self._nodes_factory.create_node_instance(node_type)
			if not new_node:
				continue
			new_node.NODE_NAME = name or new_node.NODE_NAME
			for property_name in new_node.model.properties.keys():
				if property_name in node_data.keys():
					new_node.model.set_property(property_name, node_data[property_name])
			for property_name, value in node_data.get('custom', dict()).items():
				new_node.model.set_property(property_name, value)
			nodes[node_id] = new_node
			self.add_node(new_node, node_data.get('pos'))
			if node_data.get('socket_deletion_allowed', None):
				new_node.set_sockets({
					'input_sockets': node_data['input_sockets'],
					'output_sockets': node_data['output_sockets']
				})

		for connection in data.get('connections', list()):
			node_id, socket_name = connection.get('in', ('', ''))
			in_node = nodes.get(node_id) or self.node_by_id(node_id)
			if not in_node:
				continue
			in_socket = in_node.inputs().get(socket_name) if in_node else None
			node_id, socket_name = connection.get('out', ('', ''))
			out_node = nodes.get(node_id) or self.node_by_id(node_id)
			if not out_node:
				continue
			out_socket = out_node.outputs().get(socket_name) if out_node else None
			if in_socket and out_socket:
				allow_connection = any([not in_socket.model.connected_sockets, in_socket.model.multi_connection])
				if allow_connection:
					self._undo_stack.push(commands.SocketConnectedCommand(in_socket, out_socket))

		node_objs = list(nodes.values())
		if relative_pos:
			self._viewer.move_nodes([n.view for n in node_objs])
			[setattr(n.model, 'pos', n.view.xy_pos) for n in node_objs]
		elif pos:
			self._viewer.move_nodes([n.view for n in node_objs], pos=pos)
		[setattr(n.model, 'pos', n.view.xy_pos) for n in node_objs]

		return node_objs

	def _deserialize_context_menu(self, menu, menu_data, root_path=None):
		"""
		Internal function that populates with given instance from the given data.

		:param tp.common.nodegraph.core.menus.NodeGraphMenu or tp.common.nodegraph.core.menus.NodesMenu menu:menu to
			populate.
		:param dict or list menu_data: serialized menu data.
		:param str or None root_path: optional root path used to find context menu action file paths.
		:raises ValueError: if no context menu is given.
		"""

		def _build_menu_command(_menu, _data, _root_path):

			if not _root_path:
				full_path = os.path.abspath(_data['file'])
			else:
				full_path = os.path.abspath(os.path.join(_root_path, _data['file']))
			if not path.is_file(full_path):
				logger.warning('Context menu file does not exist: {}'.format(full_path))
				return
			base_dir, file_name = os.path.split(full_path)
			base_name = os.path.basename(base_dir)
			file_name, _ = file_name.split('.')
			mod_name = '{}.{}'.format(base_name, file_name)
			spec = importlib.util.spec_from_file_location(mod_name, full_path)
			mod = importlib.util.module_from_spec(spec)
			sys.modules[mod_name] = mod
			spec.loader.exec_module(mod)
			if not hasattr(mod, _data['function_name']):
				logger.warning('Function {} not defined within Python file: {}'.format(_data['function_name'], full_path))
				return
			cmd_fn = getattr(mod, _data['function_name'])
			cmd_name = _data.get('label') or '<command>'
			cmd_shortcut =_data.get('shortcut')
			cmd_kwargs = {'fn': cmd_fn, 'shortcut': cmd_shortcut}
			if _menu == nodes_menu and _data.get('node_type'):
				cmd_kwargs['node_type'] = _data['node_type']
			_menu.add_command(name=cmd_name, **cmd_kwargs)

		if not menu:
			raise ValueError('No context menu given!')

		nodes_menu = self.context_menu_by_name('nodes')

		if isinstance(menu_data, dict):
			item_type = menu_data.get('type')
			if item_type == 'separator':
				menu.add_separator()
			elif item_type == 'command':
				_build_menu_command(menu, menu_data, root_path)
			elif item_type == 'menu':
				sub_menu = menu.add_menu(menu_data['label'])
				items = menu_data.get('items', list())
				self._deserialize_context_menu(sub_menu, items, root_path)
		elif isinstance(menu_data, list):
			for item_data in menu_data:
				self._deserialize_context_menu(menu, item_data, root_path)

	# =================================================================================================================
	# CALLBACKS
	# =================================================================================================================

	def _on_close_sub_graph_tab(self):
		pass

	def _on_properties_editor_property_changed(self, node_id, property_name, property_value):
		"""
		Internal callback function that is called each time a property is changed using properties editor widget
		linked to this node graph instance.

		:param str node_id: node id.
		:param str property_name: node property name.
		:param object property_value: node property value.
		"""

		found_node = self.node_by_id(node_id)
		if not found_node:
			return

		if found_node.get_property(property_name) != property_value:
			found_node.set_property(property_name, property_value)

	def _on_search_triggered(self, node_type, pos):
		"""
		Internal callback function that is called when the tab search widget is triggered in the viewer.

		:param str node_type: node identifier to create.
		:param tuple(float, float) pos: tuple with the X, Y position where the node should be created within the viewer.
		"""

		self.create_node(node_type, pos=pos)

	def _on_nodes_moved(self, node_data):
		"""
		Internal callback function that is called when selected nodes in the viewer has changed position.

		:param dict node_data: moved nodes data.
		"""

		self._undo_stack.beginMacro('Move Nodes')
		for node_view, prev_pos in node_data.items():
			moved_node = self._model.nodes[node_view.id]
			self._undo_stack.push(commands.NodeMovedCommand(moved_node, moved_node.pos(), prev_pos))
		self._undo_stack.endMacro()

	def _on_connection_changed(self, disconnected, connected):
		"""
		Internal callback function that is called when a connection between two nodes has been changed in the viewer.

		:param list[tp.common.nodegraph.views.socket.SocketView] disconnected: list of disconnected socket views.
		:param list[tp.common.nodegraph.views.socket.SocketView] connected: list of connected socket views.
		"""

		if not (disconnected or connected):
			return

		socket_types = {consts.SocketDirection.Input: 'inputs', consts.SocketDirection.Output: 'outputs'}

		self._undo_stack.beginMacro('Connect node(s)' if connected else 'Disconnet node(s)')
		for socket1_view, socket2_view in disconnected:
			node1 = self._model.nodes[socket1_view.node.id]
			node2 = self._model.nodes[socket2_view.node.id]
			socket1 = getattr(node1, socket_types[socket1_view.direction])()[socket1_view.name]
			socket2 = getattr(node2, socket_types[socket2_view.direction])()[socket2_view.name]
			socket1.disconnect_from(socket2)
		for socket1_view, socket2_view in connected:
			node1 = self._model.nodes[socket1_view.node.id]
			node2 = self._model.nodes[socket2_view.node.id]
			socket1 = getattr(node1, socket_types[socket1_view.direction])()[socket1_view.name]
			socket2 = getattr(node2, socket_types[socket2_view.direction])()[socket2_view.name]
			socket1.connect_to(socket2)
		self._undo_stack.endMacro()

	def _on_connection_sliced(self, socket_views):
		"""
		Internal callback function that is called when connectors have been sliced.

		:param list[tp.common.nodegraph.views.socket.SocketView] socket_views: sockets that need to be disconnected.
		"""

		if not socket_views:
			return

		socket_types = {consts.SocketDirection.Input: 'inputs', consts.SocketDirection.Output: 'outputs'}

		self._undo_stack.beginMacro('Slice Connections')
		for socket1_view, socket2_view in socket_views:
			node1 = self._model.nodes[socket1_view.node.id]
			node2 = self._model.nodes[socket2_view.node.id]
			socket1 = getattr(node1, socket_types[socket1_view.direction])()[socket1_view.name]
			socket2 = getattr(node2, socket_types[socket2_view.direction])()[socket2_view.name]
			socket1.disconnect_from(socket2)
		self._undo_stack.endMacro()

	def _on_node_double_clicked(self, node_id):
		"""
		Internal callback function that is called each time a node is double-clicked by the user.

		:param str node_id: double-clicked node ID.
		"""

		found_node = self.node_by_id(node_id)
		if not found_node:
			return

		self.nodeDoubleClicked.emit(found_node)

	def _on_node_name_changed(self, node_id, name):
		"""
		Internal callback function that is called when a node name is changed though node view.

		:param str node_id: ID of node that was renamed.
		:param str name: new node name.
		"""

		found_node = self.node_by_id(node_id)
		if not found_node:
			return

		found_node.set_name(name)
		found_node.view.draw()

	def _on_node_selected(self, node_id):
		"""
		Internal callback function that is called when a node is selected in the graph viewer.

		:param str node_id: selected node ID.
		"""

		found_node = self.node_by_id(node_id)
		if not found_node:
			return

		self.nodeSelected.emit(found_node)

	def _on_node_selection_changed(self, selected_ids, deselected_ids):
		"""
		Internal callback function that is called when the node selection changes.

		:param list[str] selected_ids: list of selected node IDs.
		:param list[str] deselected_ids: list of deselected node IDs.
		"""

		selected_nodes = [self.node_by_id(node_id) for node_id in selected_ids]
		deselected_nodes = [self.node_by_id(node_id) for node_id in deselected_ids]
		self.nodeSelectionChanged.emit(selected_nodes, deselected_nodes)

	def _on_node_backdrop_updated(self, node_id, update_property, value):
		"""
		Internal callback function that is called each time a backdrop node is updated.

		:param str node_id: backdrop node ID.
		:param str update_property: updated property.
		:param object value: updated property value.
		"""

		backdrop_node = self.node_by_id(node_id)
		if backdrop_node and isinstance(backdrop_node, backdrop.BackdropNode):
			backdrop_node.update_property(update_property, value)

	def _on_node_data_dropped(self, data, pos):
		"""
		Internal callback function that is called when data has been dropped on the viewer. Example identifiers:
			URI = ngqt://path/to/node/session.graph
			URN = ngqt::node:com.nodes.MyNode1;node:com.nodes.MyNode2

		:param Qt.QtCore.QMimeData data: mime data.
		:param Qt.QtCore.QPoint pos: scene position relative to the drop.
		"""

		uri_regex = re.compile(r'{}(?:/*)([\w/]+)(\.\w+)'.format(consts.URI_SCHEME))
		urn_regex = re.compile(r'{}([\w\.:;]+)'.format(consts.URN_SCHEME))
		if data.hasFormat('text/uri-list'):
			for url in data.urls():
				local_file = url.toLocalFile()
				if local_file:
					try:
						self.import_session(local_file)
						continue
					except Exception as e:
						pass

				url_str = url.toString()
				uri_search = uri_regex.search(url_str)
				urn_search = urn_regex.search(url_str)
				if uri_search:
					file_path = uri_search.group(1)
					ext = uri_search.group(2)
					self.import_session('{}{}'.format(file_path, ext))
				elif urn_search:
					search_str = urn_search.group(1)
					node_ids = sorted(re.findall('node:([\w\\.]+)', search_str))
					x, y = pos.x(), pos.y()
					for node_id in node_ids:
						self.create_node(node_id, pos=[x, y])
						x += 80
						y += 80


class SubGraph(NodeGraph):
	def __init__(self, parent=None, group_node=None, nodes_factory=None):
		super(SubGraph, self).__init__(parent=parent, nodes_factory=nodes_factory)

		self._node = group_node
		self._parent_graph = parent
		self._sub_viewer_widget = None

	def __repr__(self):
		return '<{}("{}") object at {}>'.format(self.__class__.__name__, self._node.name(), hex(id(self)))

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def _deserialize(self, data, relative_pos=False, pos=None):
		"""
		Intenral function that deserializes node data.

		:param dict data: node data.
		:param bool relative_pos: whether to position nodes relative to the cursor.
		:param tuple or list or None pos: custom X,Y position.
		"""

		for attr_name, attr_value in data.get('graph', dict()).items():
			if attr_name == 'acyclic':
				self.set_acyclic(attr_value)
			elif attr_name == 'connector_collision':
				self.set_connector_collision(attr_value)

		input_nodes, output_nodes = self._build_socket_nodes()

		nodes = dict()
		for node_id, node_data in data.get('nodes', dict()).items():
			node_type = node_data['type_']
			name = node_data.get('name')
			if node_type == inout.SocketInputNode.type_:
				nodes[node_id] = input_nodes[name]
				nodes[node_id].set_pos(*(node_data.get('pos') or [0, 0]))
				continue
			elif node_type == inout.SocketOutputNode.type_:
				nodes[node_id] = output_nodes[name]
				nodes[node_id].set_pos(*(node_data.get('pos') or [0, 0]))
				continue

			new_node = self._nodes_factory.create_node_instance(node_type)
			if not new_node:
				continue
			new_node.NODE_NAME = name or new_node.NODE_NAME
			for property_name in new_node.model.properties.keys():
				if property_name in node_data.keys():
					new_node.model.set_property(property_name, node_data[property_name])
			for property_name, value in node_data.get('custom', dict()).items():
				new_node.model.set_property(property_name, value)
			nodes[node_id] = new_node
			self.add_node(new_node, node_data.get('pos'))
			if node_data.get('socket_deletion_allowed', None):
				new_node.set_sockets({
					'input_sockets': node_data['input_sockets'],
					'output_sockets': node_data['output_sockets']
				})

		for connection in data.get('connections', list()):
			node_id, socket_name = connection.get('in', ('', ''))
			in_node = nodes.get(node_id)
			if not in_node:
				continue
			in_socket = in_node.inputs().get(socket_name) if in_node else None
			node_id, socket_name = connection.get('out', ('', ''))
			out_node = nodes.get(node_id)
			if not out_node:
				continue
			out_socket = out_node.outputs().get(socket_name) if out_node else None
			if in_socket and out_socket:
				self._undo_stack.push(commands.SocketConnectedCommand(in_socket, out_socket))

		node_objs = list(nodes.values())
		if relative_pos:
			self._viewer.move_nodes([n.view for n in node_objs])
			[setattr(n.model, 'pos', n.view.xy_pos) for n in node_objs]
		elif pos:
			self._viewer.move_nodes([n.view for n in node_objs], pos=pos)
		[setattr(n.model, 'pos', n.view.xy_pos) for n in node_objs]

		return node_objs

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _build_socket_nodes(self):
		"""
		Internal function that builds the corresponding input and output socket nodes from the parent node sockets
		and remove any socket nodes that are outdated.

		:return: input ndoes and output nodes created.
		:rtype: tuple(dict, dict)
		"""

		return dict(), dict()
