#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains socket controller implementation
"""

from tp.common.nodegraph.core import consts, utils, exceptions, register, commands
from tp.common.nodegraph.models import socket as socket_model


class Socket(object):
	"""
	Clas that allows to connect one node to another.
	"""

	def __init__(self, node, view):
		self._view = view
		self._model = socket_model.SocketModel(node)
		self._affected_sockets = list()

	def __repr__(self):
		port = str(self.__class__.__name__)
		return '<{}("{}") object at {}>'.format(port, self.name(), hex(id(self)))

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def model(self):
		"""
		Returns socket model.

		:return: socket model.
		:rtype: SocketModel
		"""

		return self._model

	@property
	def view(self):
		"""
		Returns socket view.

		:return: socket view.
		:rtype: SocketView
		"""

		return self._view

	@property
	def data_type(self):
		return self._model.data_type

	@data_type.setter
	def data_type(self, value):
		self._model.data_type = value

	@property
	def color(self):
		return self._view.color

	@color.setter
	def color(self, value):
		self._view.color = value

	@property
	def border_color(self):
		return self._view.border_color

	@border_color.setter
	def border_color(self, value):
		self._view.border_color = value

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def direction(self):
		"""
		Returns socket direction.

		:return: socket direction.
		:rtype: str
		"""

		return self._model.direction

	def multi_connection(self):
		"""
		Returns whether socket is single connection;

		:return: True if socket is multi connection; False otherwise.
		:rtype: bool
		"""

		return self._model.multi_connection

	def name(self):
		"""
		Returns the socket name.

		:return: socket name.
		:rtype: str
		"""

		return self._model.name

	def node(self):
		"""
		Returns the socket parent node.

		:return: parent node.
		:rtype: BaseNode
		"""

		return self._model.node

	def visible(self):
		"""
		Returns whether socket is visible within node graph.

		:return: True if socket is visible; False otherwise.
		:rtype: bool
		"""

		return self._model.visible

	def set_visible(self, flag):
		"""
		Sets whether socket is visible within node graph.

		:param bool flag: True to make socket visible; False otherwise.
		"""

		self._model.visible = flag
		label = 'Show' if flag else 'Hide'
		undo_stack = self.node().graph.undo_stack()
		undo_stack.beginMacro('{} Socket {}'.format(label, self.name()))
		for node_socket in self.connected_sockets():
			undo_stack.push(commands.SocketDisconnectedCommand(self, node_socket))
		undo_stack.push(commands.SocketVisibleCommand(self))
		undo_stack.endMacro()

	def locked(self):
		"""
		Returns socket locked state.

		:return: True if socket is locked; False otherwise.
		:rtype: bool

		..note:: if sockets are locked the new connectors cannot be connected and current connectors cannot be
			disconnected .
		"""

		return self._model.locked

	def set_locked(self, flag=False, connected_sockets=True, push_undo=True):
		"""
		Sets the socket locked state.

		:param bool flag: socket lock state.
		:param bool connected_sockets: whether apply to lock state to connected sockets.
		:param bool push_undo: whether to push lock operation to the undo stack.
		"""

		graph = self.node().graph
		undo_stack = graph.undo_stack()
		if flag:
			undo_command = commands.SocketLockedCommand(self)
		else:
			undo_command = commands.SocketUnlockedCommand(self)
		if push_undo:
			undo_stack.push(undo_command)
		else:
			undo_command.redo()

		if connected_sockets:
			for connected_socket in self.connected_sockets():
				connected_socket.set_locked(flag, connected_sockets=False, push_undo=push_undo)

	def lock(self):
		"""
		Locks the socket so new connectors cannot be connected and current connectors cannot be disconnected.
		"""

		self.set_locked(True, connected_sockets=True)

	def unlock(self):
		"""
		Unlocks the socket so new connectors can be connected and existing connectors can be disconnected.
		"""

		self.set_locked(False, connected_sockets=True)

	def is_connected(self):
		"""
		Returns whether this socket is connected to other sockets.

		:return: True if socket is connected to other sockets; False otherwise.
		:rtype: bool
		"""

		return len(self.connected_sockets()) > 0

	def connected_sockets(self):
		"""
		Returns all connected sockets.

		:return: list of connected sockets.
		:rtype: list(Socket)
		"""

		sockets = list()

		graph = self.node().graph
		for node_id, socket_names in self._model.connected_sockets.items():
			for socket_name in socket_names:
				node_found = graph.node_by_id(node_id)
				if self.direction() == consts.SocketDirection.Input:
					sockets.append(node_found.outputs()[socket_name])
				elif self.direction() == consts.SocketDirection.Output:
					sockets.append(node_found.inputs()[socket_name])

		return sockets

	def connect_to(self, node_socket=None, push_undo=True):
		"""
		Creates a connection to the given socket and emits portConnected signal from the parent node graph.

		:param Socket node_socket: socket object.
		:param bool push_undo: whether connect socket operation should be pushed into undo stack.
		"""

		if not node_socket or self in node_socket.connected_sockets():
			return

		if self.locked() or node_socket.locked():
			name = [_socket.name() for _socket in [self, node_socket] if _socket.locked()][0]
			raise exceptions.SocketError('Cannot connect socket because "{}" is locked'.format(name))

		graph = self.node().graph
		viewer = graph.viewer()

		if push_undo:
			undo_stack = graph.undo_stack()
			undo_stack.beginMacro('Connect Socket')

		pre_connector_socket = None
		source_connector_sockets = self.connected_sockets()
		if not self.multi_connection() and source_connector_sockets:
			pre_connector_socket = source_connector_sockets[0]

		if not node_socket:
			if pre_connector_socket:
				if push_undo:
					undo_stack.push(commands.SocketDisconnectedCommand(self, node_socket))
					undo_stack.push(commands.NodeInputDisconnectedCommand(self, node_socket))
				else:
					commands.SocketDisconnectedCommand(self, node_socket).redo()
					commands.NodeInputDisconnectedCommand(self, node_socket).redo()
			return

		if graph.is_acyclic() and utils.acyclic_check(self._view, node_socket.view):
			if pre_connector_socket:
				if push_undo:
					undo_stack.push(commands.SocketDisconnectedCommand(self, pre_connector_socket))
					undo_stack.push(commands.NodeInputDisconnectedCommand(self, pre_connector_socket))
					undo_stack.endMacro()
				else:
					commands.SocketDisconnectedCommand(self, pre_connector_socket).redo()
					commands.NodeInputDisconnectedCommand(self, pre_connector_socket).redo()
				return

		target_connector_sockets = node_socket.connected_sockets()
		if not node_socket.multi_connection() and target_connector_sockets:
			detached_socket = target_connector_sockets[0]
			if push_undo:
				undo_stack.push(commands.SocketDisconnectedCommand(node_socket, detached_socket))
				undo_stack.push(commands.NodeInputDisconnectedCommand(node_socket, detached_socket))
			else:
				commands.SocketDisconnectedCommand(node_socket, detached_socket).redo()
				commands.NodeInputDisconnectedCommand(node_socket, detached_socket).redo()

		if pre_connector_socket:
			if push_undo:
				undo_stack.push(commands.SocketDisconnectedCommand(self, pre_connector_socket))
				undo_stack.push(commands.NodeInputDisconnectedCommand(self, pre_connector_socket))
			else:
				commands.SocketDisconnectedCommand(self, pre_connector_socket).redo()
				commands.NodeInputDisconnectedCommand(self, pre_connector_socket).redo()

		if push_undo:
			undo_stack.push(commands.SocketConnectedCommand(self, node_socket))
			undo_stack.push(commands.NodeInputConnectedCommand(self, node_socket))
			undo_stack.endMacro()
		else:
			commands.SocketConnectedCommand(self, node_socket).redo()
			commands.NodeInputConnectedCommand(self, node_socket).redo()

		sockets = {_socket.direction(): _socket for _socket in [self, node_socket]}
		graph.socketConnected.emit(sockets[consts.SocketDirection.Input], sockets[consts.SocketDirection.Output])

	def disconnect_from(self, node_socket=None, push_undo=True):
		"""
		Disconnects from the given socket and emits portDisconnected signal from the parent node graph.

		:param Socket node_socket: socket object.
		:param bool push_undo: whether disconnect socket operation should be pushed into undo stack.
		"""

		if not node_socket:
			return

		if self.locked() or node_socket.locked():
			name = [_socket.name() for _socket in [self, node_socket] if _socket.locked()][0]
			raise exceptions.SocketError('Cannot disconnect socket because "{}" is locked'.format(name))

		graph = self.node().graph
		if push_undo:
			undo_stack = graph.undo_stack()
			undo_stack.beginMacro('Disconnect Socket')
			undo_stack.push(commands.SocketDisconnectedCommand(self, node_socket))
			undo_stack.push(commands.NodeInputDisconnectedCommand(self, node_socket))
			undo_stack.endMacro()
		else:
			commands.SocketDisconnectedCommand(self, node_socket).redo()
			commands.NodeInputDisconnectedCommand(self, node_socket).redo()

		sockets = {_socket.direction(): _socket for _socket in [self, node_socket]}
		graph.socketDisconnected.emit(sockets[consts.SocketDirection.Input], sockets[consts.SocketDirection.Output])

	def clear_connections(self, push_undo=True):
		"""
		Disconnects from all the socket connections and emit the portDisconnected signals from the node graph.

		:param bool push_undo: whether clear socket connections operation should be pushed into undo stack.
		"""

		if self.locked():
			raise exceptions.SocketError(
				'Cannot clear connections because socket "{}" is locked'.format(self.name()))

		if not self.connected_sockets():
			return

		if push_undo:
			graph = self.node().graph
			undo_stack = graph.undo_stack()
			undo_stack.beginMacro('"{}" Clear Connections'.format(self.name()))
			for connected_socket in self.connected_sockets():
				self.disconnect_from(connected_socket, push_undo=True)
			undo_stack.endMacro()
		else:
			for connected_socket in self.connected_sockets():
				self.disconnect_from(connected_socket, push_undo=False)

	def affects(self, other_socket):
		"""
		Adds given socket within the list of affected sockets by this one.

		:param Socket other_socket: affected socket.
		"""

		self._affected_sockets.append(other_socket)

	def update_affected(self):
		"""
		Updates affect sockets with the value of this socket.
		"""

		for affected_socket in self._affected_sockets:
			if not affected_socket.node().has_property(affected_socket.name()):
				return
			if not self.node().has_property(self.name()):
				return
			affected_socket.node().set_property(affected_socket.name(), self.node().get_property(self.name()))
