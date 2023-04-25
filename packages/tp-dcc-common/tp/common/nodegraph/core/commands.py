from Qt.QtWidgets import QUndoCommand

from tp.core import log
from tp.common.nodegraph.core import consts

logger = log.tpLogger


class NodeAddedCommand(QUndoCommand):
	"""
	Node added command.

	:param NodeGraph graph: graph object where node will be added.
	:param Node node: node object that will be added within the graph.
	:param tuple(float, float) pos: initial node position.
	"""

	def __init__(self, graph, node, pos=None):
		super(NodeAddedCommand, self).__init__()

		self.setText('Added Node')
		self._viewer = graph.viewer()
		self._model = graph.model
		self._node = node
		self._pos = pos

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		self._pos = self._pos or self._node.pos()
		self._model.nodes.pop(self._node.id)
		self._node.view.delete()

	def redo(self):
		self._model.nodes[self._node.id] = self._node
		self._viewer.add_node(self._node.view, self._pos)


class NodeMovedCommand(QUndoCommand):
	"""
	Node moved command.

	:param NodeGraph graph: graph object where node will be added.
	:param Node node: node object that will be moved within the graph.
	:param tuple(float, float) pos: new node position.
	:param tuple(float, float) prev_pos: previous node position.
	"""

	def __init__(self, node, pos, prev_pos):
		super(NodeMovedCommand, self).__init__()

		self._node = node
		self._pos = pos
		self._prev_pos = prev_pos

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		self._node.view.xy_pos = self._prev_pos
		self._node.model.pos = self._prev_pos

	def redo(self):
		if self._pos == self._prev_pos:
			return
		self._node.view.xy_pos = self._pos
		self._node.model.pos = self._pos


class NodeRemovedCommand(QUndoCommand):
	"""
	Node delete command.

	:param NodeGraph graph: graph object where node will be added.
	:param Node node: node object that will be moved within the graph.
	"""

	def __init__(self, graph, node):
		super(NodeRemovedCommand, self).__init__()

		self.setText('Deleted node')

		self._scene = graph.scene()
		self._model = graph.model
		self._node = node

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		self._model.nodes[self._node.id] = self._node
		self._scene.addItem(self._node.view)

	def redo(self):
		self._model.nodes.pop(self._node.id)
		self._node.view.delete()


class PropertyChangedCommand(QUndoCommand):
	"""
	Node property changed command.

	:param BaseNode node: node
	:param str name: property name
	:param object value: property value
	"""

	def __init__(self, node, name, value):
		super(PropertyChangedCommand, self).__init__()

		if name == 'name':
			self.setText('renamed "{}" to "{}"'.format(node.name(), value))
		else:
			self.setText('property "{}:{}'.format(node.name(), name))
		self._node = node
		self._name = name
		self._old_value = node.get_property(name)
		self._new_value = value
		self._error_message = None

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def error_message(self):
		return self._error_message

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		do_undo = False
		try:
			if self._old_value != self._new_value:
				do_undo = True
		except Exception:
			do_undo = True

		if do_undo:
			self._set_node_property(self._name, self._old_value)
			graph = self._node.graph
			graph.propertyChanged.emit(self._node, self._name, self._old_value)

	def redo(self):
		do_redo = False
		try:
			if self._old_value != self._new_value:
				do_redo = True
		except Exception:
			do_redo = True

		if do_redo:
			valid = self._set_node_property(self._name, self._new_value)
			if not valid:
				self._error_message = 'Was not possible property {}: {}'.format(self._name, self._new_value)
				return
			graph = self._node.graph
			graph.propertyChanged.emit(self._node, self._name, self._new_value)

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _set_node_property(self, name, value):
		"""
		Internal function that updates node view and model.

		:param str name: attribute name.
		:param object value: attribute value.
		:return: True if property was set successfully; False otherwise.
		:rtype: bool
		"""

		# update model
		model = self._node.model
		valid = model.set_property(name, value)
		if not valid:
			logger.warning('Was not possible to set node {} property {} to {}'.format(self._node, name, value))
			return False

		# update view
		view = self._node.view

		# update view widgets
		if hasattr(view, 'widgets') and name in view.widgets.keys():
			if view.widgets[name].value() != value:
				view.widgets[name].set_value(value)

		# update view properties
		if name in view.properties.keys():
			if name == 'pos':
				name = 'xy_pos'
			setattr(view, name, value)

		return True


class NodeInputConnectedCommand(QUndoCommand):
	"""
	Node input connected command.

	:param Socket source_socket: source socket.
	:param Socket target_socket: target socket.
	"""

	def __init__(self, source_socket, target_socket):
		super(NodeInputConnectedCommand, self).__init__()

		if source_socket.direction() == consts.SocketDirection.Input:
			self._source = source_socket
			self._target = target_socket
		else:
			self._source = target_socket
			self._target = source_socket

	def undo(self):
		node = self._source.node()
		node._on_input_disconnected(self._source, self._target)

	def redo(self):
		node = self._source.node()
		node._on_input_connected(self._source, self._target)


class NodeInputDisconnectedCommand(QUndoCommand):
	"""
	Node input disconnected command.

	:param Socket source_socket: source socket.
	:param Socket target_socket: target socket.
	"""

	def __init__(self, source_socket, target_socket):
		super(NodeInputDisconnectedCommand, self).__init__()

		if source_socket.direction() == consts.SocketDirection.Input:
			self._source = source_socket
			self._target = target_socket
		else:
			self._source = target_socket
			self._target = source_socket

	def undo(self):
		node = self._source.node()
		node._on_input_connected(self._source, self._target)

	def redo(self):
		node = self._source.node()
		node._on_input_disconnected(self._source, self._target)


class SocketConnectedCommand(QUndoCommand):
	"""
	Socket connected command.

	:param Socket source_socket: source socket.
	:param Socket target_socket: target socket.
	"""

	def __init__(self, source_socket, target_socket):
		super(SocketConnectedCommand, self).__init__()

		self._source = source_socket
		self._target = target_socket

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		source_model = self._source.model
		target_model = self._target.model
		source_id = self._source.node().id
		target_id = self._target.node().id

		socket_names = source_model.connected_sockets.get(target_id)
		if socket_names is list():
			del source_model.connected_sockets[target_id]
		if socket_names and self._target.name() in socket_names:
			socket_names.remove(self._target.name())

		socket_names = target_model.connected_sockets.get(source_id)
		if socket_names is list():
			del target_model.connected_sockets[source_id]
		if socket_names and self._source.name() in socket_names:
			socket_names.remove(self._source.name())

		self._source.view.disconnect_from(self._target.view)

	def redo(self):
		source_model = self._source.model
		target_model = self._target.model
		source_id = self._source.node().id
		target_id = self._target.node().id

		source_model.connected_sockets[target_id].append(self._target.name())
		target_model.connected_sockets[source_id].append(self._source.name())

		self._source.view.connect_to(self._target.view)


class SocketDisconnectedCommand(QUndoCommand):
	"""
	Socket disconnected command.

	:param Socket source_socket: source socket.
	:param Socket target_socket: target socket.
	"""

	def __init__(self, source_socket, target_socket):
		super(SocketDisconnectedCommand, self).__init__()

		self._source = source_socket
		self._target = target_socket

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		source_model = self._source.model
		target_model = self._target.model
		source_id = self._source.node().id
		target_id = self._target.node().id

		source_model.connected_sockets[target_id].append(self._target.name())
		target_model.connected_sockets[source_id].append(self._source.name())

		self._source.view.connect_to(self._target.view)

	def redo(self):
		source_model = self._source.model
		target_model = self._target.model
		source_id = self._source.node().id
		target_id = self._target.node().id

		socket_names = source_model.connected_sockets.get(target_id)
		if socket_names is list():
			del source_model.connected_sockets[target_id]
		if socket_names and self._target.name() in socket_names:
			socket_names.remove(self._target.name())

		socket_names = target_model.connected_sockets.get(source_id)
		if socket_names is list():
			del target_model.connected_sockets[source_id]
		if socket_names and self._source.name() in socket_names:
			socket_names.remove(self._source.name())

		self._source.view.disconnect_from(self._target.view)


class SocketLockedCommand(QUndoCommand):
	"""
	Socket locked command.

	:param Socket socket: node socket.
	"""

	def __init__(self, socket):
		super(SocketLockedCommand, self).__init__()

		self.setText('Lock Socket "{}"'.format(socket.name()))
		self._socket = socket

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		self._socket.model.locked = False
		self._socket.view.locked = False

	def redo(self):
		self._socket.model.locked = True
		self._socket.view.locked = True


from Qt.QtWidgets import QUndoCommand


class SocketUnlockedCommand(QUndoCommand):
	"""
	Socket locked command.

	:param Socket socket: node socket.
	"""

	def __init__(self, socket):
		super(SocketUnlockedCommand, self).__init__()

		self.setText('Unlock Socket "{}"'.format(socket.name()))
		self._socket = socket

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		self._socket.model.locked = True
		self._socket.view.locked = True

	def redo(self):
		self._socket.model.locked = False
		self._socket.view.locked = False


class SocketVisibleCommand(QUndoCommand):
	def __init__(self, socket):
		super(SocketVisibleCommand, self).__init__()

		self._socket = socket
		self._visible = socket.visbile

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def undo(self):
		self._set_visible(not self._visible)

	def redo(self):
		self._set_visible(self._visible)

	# ==================================================================================================================
	# INTERNAL
	# ==================================================================================================================

	def _set_visible(self, flag):
		"""
		Internal function that sets socket visibility.

		:param bool flag: True to make socket visible; False otherwise.
		"""

		self._socket.model.visible = flag
		self._socket.view.setVisible(flag)
		node_view = self._socket.node().view
		text_item = None
		if self._socket.direction() == consts.SocketDirection.Input:
			text_item = node_view.input_text_item(self._socket.view)
		elif self._socket.direction() == consts.SocketDirection.Output:
			text_item = node_view.output_text_item(self._socket.view)
		if text_item:
			text_item.setVisible(flag)
		node_view.post_init()
