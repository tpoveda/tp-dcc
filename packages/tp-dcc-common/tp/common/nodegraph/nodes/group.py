from tp.common.nodegraph.core import node
from tp.common.nodegraph.nodes import inout
from tp.common.nodegraph.views import group


class GroupNode(node.BaseNode):

	NODE_NAME = 'Group'

	def __init__(self, view=None):
		super(GroupNode, self).__init__(view or group.GroupNodeView)

		self._input_socket_nodes = dict()
		self._output_socket_nodes = dict()

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def is_expanded(self):
		"""
		Returns whether this node is expanded or collapsed.

		:return: True if node is expanded; False otherwise.
		:rtype: bool
		"""

		return False if not self.graph else self.id in self.graph.sub_graphs

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def add_input(
			self, name='input', multi_input=False, display_name=True, color=None, data_type=None, locked=False,
			painter_fn=None):
		"""
		Adds a new input socket into the node.

		:param str name: name for the input socket.
		:param bool multi_input: whether to allow socket to have more than one connection.
		:param str display_name: display the port name on the node.
		:param tuple(int, int, int) color: initial port color in 0 to 255 range.
		:param str data_type: socket data type name.
		:param bool locked: locked state of the socket.
		:param callable painter_fn: custom function to override the drawing of the socket.
		:return: newly created socket object.
		:rtype: Socket
		"""

		new_socket = super(GroupNode, self).add_input(
			name=name, multi_input=multi_input, display_name=display_name, color=color, data_type=data_type,
			locked=locked, painter_fn=painter_fn)

		if self.is_expanded:
			input_socket = inout.SocketInputNode(parent_socket=new_socket)
			input_socket.NODE_NAME = new_socket.name()
			input_socket.model.set_property('name', new_socket.name())
			input_socket.add_output(new_socket.name())
			sub_graph = self.sub_graph()
			sub_graph.add_node(input_socket, selected=False, push_undo=False)

		return new_socket

	def add_output(self, name='output', multi_output=True, display_name=True, color=None, data_type=None, locked=False,
				   painter_fn=None):
		"""
		Adds a new input socket into the node.

		:param str name: name for the input socket.
		:param bool multi_output: whether to allow socket to have more than one connection.
		:param str display_name: display the port name on the node.
		:param tuple(int, int, int) color: initial port color in 0 to 255 range.
		:param str data_type: socket data type name.
		:param bool locked: locked state of the socket.
		:param callable painter_fn: custom function to override the drawing of the socket.
		:return: newly created socket object.
		:rtype: Socket
		"""

		new_socket = super(GroupNode, self).add_output(
			name=name, multi_output=multi_output, display_name=display_name, color=color, data_type=data_type,
			locked=locked, painter_fn=painter_fn)

		if self.is_expanded:
			output_socket = inout.SocketOutputNode(parent_socket=new_socket)
			output_socket.NODE_NAME = new_socket.name()
			output_socket.model.set_property('name', new_socket.name())
			output_socket.add_input(new_socket.name())
			sub_graph = self.sub_graph()
			sub_graph.add_node(output_socket, selected=False, push_undo=False)

		return new_socket

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def sub_graph(self):
		"""
		Returns the sub graph controller to the group node.

		:return: sub graph instance.
		:rtype: tp.common.node.core.graph.SubGraph or None
		"""

		return self.graph.sub_graphs.get(self.id)

	def expand(self):
		"""
		Expands the group node session.
		"""

		self.graph.expand_group_node(self)

	def collapse(self):
		"""
		Collapses the group node session.
		"""

		self.graph.collapse_group_node(self)
