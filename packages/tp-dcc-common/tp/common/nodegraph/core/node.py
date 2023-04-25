#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains node object implementation
"""

from collections import OrderedDict

from Qt.QtGui import QColor

from tp.core import log
from tp.common.python import helpers
from tp.common.nodegraph.core import consts, abstract, exceptions, register, socket
from tp.common.nodegraph.views import node as node_view
from tp.common.nodegraph.painters import socket as socket_painters
from tp.common.nodegraph.widgets import nodewidgets

logger = log.tpLogger


class BaseNode(abstract.Node):
	"""
	Base class for nodes that allow socket connections from one node to another.
	"""

	NODE_NAME = 'Node'

	def __init__(self, view=None):
		view = view or node_view.NodeView

		super(BaseNode, self).__init__(view=view)

		self._inputs = list()
		self._outputs = list()

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def update_model(self):
		"""
		Updates the node model from view.
		"""

		for name, value in self.view.properties.items():
			if name in ['inputs', 'outputs']:
				continue
			self.model.set_property(name, value)

		for name, widget in self.view.widgets.items():
			self.model.set_property(name, widget.value())

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def icon(self):
		"""
		Returns node icon path.

		:return: node icon path.
		:rtype: str or None
		"""

		return self.model.icon

	def set_icon(self, icon=None):
		"""
		Sets the node icon.

		:param str icon: path to the icon image.
		"""

		self.set_property('icon', icon)

	# ==================================================================================================================
	# SOCKETS
	# ==================================================================================================================

	# NOTE: do change function name, used by NodeGraph to access node socket easily (_on_connection_changed)
	def inputs(self):
		"""
		Returns all the input socket from the node.

		:return: all node input sockets.
		:rtype: dictionary with the input socket names as keys and the input socket objects as values.
		:rtype: dict(str, Socket)
		"""

		return {node_socket.name(): node_socket for node_socket in self._inputs}

	def input_sockets(self):
		"""
		Returns all input sockets.

		:return: list of node input sockets.
		:rtype: list[tp.common.nodegraph.core.socket.Socket]
		"""

		return self._inputs

	# NOTE: do change function name, used by NodeGraph to access node socket easily (_on_connection_changed)
	def outputs(self):
		"""
		Returns all the output socket from the node.

		:return: all node output sockets.
		:rtype: dictionary with the output socket names as keys and the output socket objects as values.
		:rtype: dict(str, Socket)
		"""

		return {node_socket.name(): node_socket for node_socket in self._outputs}

	def output_sockets(self):
		"""
		Returns all output sockets.

		:return: list of node output sockets.
		:rtype: list[tp.common.nodegraph.core.socket.Socket]
		"""

		return self._outputs

	def input(self, name_or_index):
		"""
		Returns the input socket with the matching index.

		:param int or str name_or_index: name or index of the input socket.
		:return: socket instance.
		:rtype: tp.common.nodegraph.core.socket.Socket
		"""

		if isinstance(name_or_index, int):
			if name_or_index < len(self._inputs):
				return self._inputs[name_or_index]
		elif helpers.is_string(name_or_index):
			return self.inputs().get(name_or_index, None)

	def set_input(self, index, output_socket):
		"""
		Creates a connection to the given output socket.
		:param int index: index of the input socket to connect.
		:param tp.common.nodegraph.core.socket.Socket output_socket: output socket to connect.
		"""

		input_socket = self.input(index)
		input_socket.connect_to(output_socket)

	def output(self, name_or_index):
		"""
		Returns the output socket with the matching index.

		:param int or str name_or_index: name or index of the output socket.
		:return: socket instance.
		:rtype: tp.common.nodegraph.core.socket.Socket
		"""

		if isinstance(name_or_index, int):
			if name_or_index < len(self._outputs):
				return self._outputs[name_or_index]
		elif helpers.is_string(name_or_index):
			return self.outputs().get(name_or_index, None)

	def set_output(self, index, input_socket):
		"""
		Creates a connection between the given input socket.

		:param int index: index of the output socket given input will be connected to.
		:param tp.common.nodegraph.core.socket.Socket input_socket: input socket that will be connected.
		"""

		output_socket = self.output(index)
		output_socket.connect_to(input_socket)

	def add_input(
			self, name='input', multi_input=False, display_name=True, color=None, data_type=None, locked=False,
			painter_fn=None):
		"""
		Adds a new input socket into the node.

		:param str name: name for the input socket.
		:param bool multi_input: whether to allow socket to have more than one connection.
		:param bool display_name: display the port name on the node.
		:param tuple(int, int, int) color: initial port color in 0 to 255 range.
		:param str data_type: socket data type name.
		:param bool locked: locked state of the socket.
		:param callable painter_fn: custom function to override the drawing of the socket.
		:return: newly created socket object.
		:rtype: Socket
		"""

		data_type = data_type or register.DataTypes.EXEC

		if name in self.inputs().keys():
			raise exceptions.SocketDuplicatedError('socket input name "{}" already registered!'.format(name))

		# exec inputs only can be connected to one output
		if data_type == register.DataTypes.EXEC:
			multi_input = False

		painter_fn = painter_fn or socket_painters.exec_socket_painter if data_type == register.DataTypes.EXEC else None
		socket_args = [name, multi_input, display_name, locked]
		if painter_fn and callable(painter_fn):
			socket_args.append(painter_fn)
		socket_view = self._view.add_input(*socket_args)

		# if a color is not defined we use data type specific color
		if not color:
			color = register.DataType.get_type(data_type).get('color', QColor()).toTuple()
		if color:
			socket_view.color = color
			socket_view.border_color = [min([255, max([0, i + 80])]) for i in color]

		new_socket = socket.Socket(self, socket_view)
		new_socket.model.direction = consts.SocketDirection.Input
		new_socket.model.name = name
		new_socket.display_name = display_name
		new_socket.model.multi_connection = multi_input
		new_socket.model.data_type = data_type
		new_socket.model.locked = locked
		self._inputs.append(new_socket)
		self.model.inputs[new_socket.name()] = new_socket.model

		return new_socket

	def add_output(self, name='output', multi_output=True, display_name=True, color=None, data_type=None, locked=False,
				   painter_fn=None):
		"""
		Adds a new input socket into the node.

		:param str name: name for the input socket.
		:param bool multi_output: whether to allow socket to have more than one connection.
		:param bool display_name: display the port name on the node.
		:param tuple(int, int, int) color: initial port color in 0 to 255 range.
		:param str data_type: socket data type name.
		:param bool locked: locked state of the socket.
		:param callable painter_fn: custom function to override the drawing of the socket.
		:return: newly created socket object.
		:rtype: Socket
		"""

		data_type = data_type or register.DataTypes.EXEC

		if name in self.outputs().keys():
			raise exceptions.SocketDuplicatedError('socket output name "{}" already registered!'.format(name))

		# exec outputs only can be connected to one input
		if data_type == register.DataTypes.EXEC:
			multi_output = False

		painter_fn = painter_fn or socket_painters.exec_socket_painter if data_type == register.DataTypes.EXEC else None
		socket_args = [name, multi_output, display_name, locked]
		if painter_fn and callable(painter_fn):
			socket_args.append(painter_fn)
		socket_view = self._view.add_output(*socket_args)

		# if a color is not defined we use data type specific color
		if not color:
			color = register.DataType.get_type(data_type).get('color').toTuple()
		if color:
			socket_view.color = color
			socket_view.border_color = [min([255, max([0, i + 80])]) for i in color]

		new_socket = socket.Socket(self, socket_view)
		new_socket.model.direction = consts.SocketDirection.Output
		new_socket.model.name = name
		new_socket.model.multi_connection = multi_output
		new_socket.model.data_type = data_type
		new_socket.model.locked = locked
		self._outputs.append(new_socket)
		self.model.outputs[new_socket.name()] = new_socket.model

		return new_socket

	def delete_input(self, name_or_index):
		"""
		Deletes input socket from node by its name or index.

		:param str or int name_or_index: socket name or index.
		:raises exception.SocketError: if sockets cannot be deleted for this node.
		:raises exception.SocketError: if socket to delete is locked.
		"""

		input_socket = None
		if type(name_or_index) in (int, str):
			input_socket = self.input(name_or_index)
		if input_socket is None:
			return
		if not self.socket_deletion_allowed():
			raise exceptions.SocketError(
				'Socket "{}" cannot be deleted on this node because sockets are not removable'.format(self.name()))
		if input_socket.locked():
			raise exceptions.SocketError('Cannot delete a socket that is locked!')

		self._inputs.remove(input_socket)
		self._model.inputs.pop(input_socket.name())
		self._view.delete_input(input_socket.view)
		input_socket.model.node = None
		self._view.draw()

	def delete_output(self, name_or_index):
		"""
		Deletes output socket from node by its name or index.

		:param str or int name_or_index: socket name or index.
		:raises exception.SocketError: if sockets cannot be deleted for this node.
		:raises exception.SocketError: if socket to delete is locked.
		"""

		output_socket = None
		if type(name_or_index) in (int, str):
			output_socket = self.output(name_or_index)
		if output_socket is None:
			return
		if not self.socket_deletion_allowed():
			raise exceptions.SocketError(
				'Socket "{}" cannot be deleted on this node because sockets are not removable'.format(self.name()))
		if output_socket.locked():
			raise exceptions.SocketError('Cannot delete a socket that is locked!')

		self._outputs.remove(output_socket)
		self._model.outputs.pop(output_socket.name())
		self._view.delete_output(output_socket.view)
		output_socket.model.node = None
		self._view.draw()

	def delete_all_sockets(self, force=False):
		"""
		Deletes all sockets in this node.
		"""

		if not force and not self.socket_deletion_allowed():
			raise exceptions.SocketError(
				'Socket "{}" cannot be deleted on this node because sockets are not removable'.format(self.name()))

		for input_name, _ in self.inputs():
			self.delete_input(input_name)
		for output_name, _ in self.outputs():
			self.delete_output(output_name)

	def socket_deletion_allowed(self):
		"""
		Returns whether sockets for this node can be deleted.

		:return: True if sockets can be deleted; False otherwise.
		:rtype: bool
		"""

		return self.model.dynamic_port

	def set_socket_deletion_allowed(self, flag):
		"""
		Sets whether sockets for this node can be deleted.

		:param bool flag: True to enable socket deletion; False otherwise.
		"""

		self.model.dynamic_port = flag

	def connected_input_nodes(self):
		"""
		Returns all nodes connected from the input sockets.

		:return: input nodes mapping.
		:rtype: dict(tp.common.nodegraph.core.socket.Socket: list[tp.common.nodegraph.core.node.BaseNode]]
		"""

		nodes = OrderedDict()
		for input_socket in self.input_sockets():
			nodes[input_socket] = [connected_socket.node() for connected_socket in input_socket.connected_sockets()]

		return nodes

	def connected_output_nodes(self):
		"""
		Returns all nodes connected from the output sockets.

		:return: output nodes mapping.
		:rtype: dict(tp.common.nodegraph.core.socket.Socket: list[tp.common.nodegraph.core.node.BaseNode]]
		"""

		nodes = OrderedDict()
		for output_socket in self.output_sockets():
			nodes[output_socket] = [connected_socket.node() for connected_socket in output_socket.connected_sockets()]

		return nodes

	# =================================================================================================================
	# WIDGETS
	# =================================================================================================================

	def widgets(self):
		"""
		Returns al embedded widgets from this node.

		:return: list of embedded widgets.
		:rtype: list[nodewidgets.NodeBaseWidget]
		"""

		return self.view.widgets

	def widget(self, name):
		"""
		Returns the embedded widget associated with the given property name.

		:param str name: node property name.
		:return: embedded node widget.
		:rtype: nodewidgets.NodeBaseWidget
		"""

		return self.view.widgets.get(name)

	def add_combo_menu(self, name, label='', items=None, tab=None):
		"""
		Creates a custom property and embeds a combo box widget into the node.

		:param str name: name for the custom property.
		:param str label: label to be displayed.
		:param list[str] or None items: optional list of items to be added into the menu.
		:param str or None tab: name of the widget tab to display in.
		"""

		self.create_property(
			name, value=items[0] if items else None, items=items or list(),
			widget_type=consts.PropertiesEditorWidgets.COMBOBOX, tab=tab)
		widget = nodewidgets.NodeComboBox(name=name, label=label, items=items, parent=self.view)
		widget.valueChanged.connect(lambda k, v: self.set_property(k, v))
		self.view.add_widget(widget)

	def add_text_input(self, name, label='', text='', tab=None):
		"""
		Creates a custom property and embeds a line edit widget into the node.

		:param str name: name for the custom property.
		:param str label: label to be displayed.
		:param str text: optional default text.
		:param str or None tab: name of the widget tab to display in.
		"""

		self.create_property(name, value=text, widget_type=consts.PropertiesEditorWidgets.LINE_EDIT, tab=tab)
		widget = nodewidgets.NodeLineEdit(name=name, label=label, text=text, parent=self.view)
		widget.valueChanged.connect(lambda k, v: self.set_property(k, v))
		self.view.add_widget(widget)

	def add_checkbox(self, name, label='', text='', state=False, tab=None):
		"""
		Creates a custom property and embeds a checkbox widget into the node.

		:param str name: name for the custom property.
		:param str label: label to be displayed.
		:param str text: optional checkbox text.
		:param bool state: default checkbox check state.
		:param str or None tab: name of the widget tab to display in.
		"""

		self.create_property(name, value=state, widget_type=consts.PropertiesEditorWidgets.CHECKBOX, tab=tab)
		widget = nodewidgets.NodeCheckBox(name=name, label=label, text=text, state=state, parent=self.view)
		widget.valueChanged.connect(lambda k, v: self.set_property(k, v))
		self.view.add_widget(widget)

	# =================================================================================================================
	# CALLBACKS
	# =================================================================================================================

	def _on_input_connected(self, input_socket, output_socket):
		"""
		Internal callback function that is triggered when a new connection is made.

		:param tp.common.nodegraph.core.socket.Socket input_socket: source input socket from this node.
		:param tp.common.nodegraph.core.socket.Socket output_socket: output socket that connected to this node.
		..info:: this function does nothing by default, re-implement if custom logic is required.
		"""

		pass

	def _on_input_disconnected(self, input_socket, output_socket):
		"""
		Internal callback function that is triggered when a connection has been disconnected.

		:param tp.common.nodegraph.core.socket.Socket input_socket: source input socket from this node.
		:param tp.common.nodegraph.core.socket.Socket output_socket: output socket that was disconnected from this node.
		..info:: this function does nothing by default, re-implement if custom logic is required.
		"""

		pass
