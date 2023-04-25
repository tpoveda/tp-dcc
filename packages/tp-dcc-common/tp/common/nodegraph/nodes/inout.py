from tp.common.nodegraph.core import exceptions, node
from tp.common.nodegraph.views import inout


class SocketInputNode(node.BaseNode):

	NODE_NAME = 'InputSocket'

	def __init__(self, view=None, parent_socket=None):
		super(SocketInputNode, self).__init__(view or inout.SocketInputNodeView)

		self._parent_socket = parent_socket

	@property
	def parent_socket(self):
		"""
		Returns the parent group node socket representing this node.

		:return: socket instance.
		:rtype: tp.common.nodegraph.core.socket.Socket
		"""

		return self._parent_socket

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

		raise exceptions.SocketRegistrationError(
			'{}.add_input() is not available for {}'.format(self.__class__.__name__, self))

	def add_output(
			self, name='output', multi_output=True, display_name=True, color=None, data_type=None, locked=False,
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

		if self._outputs:
			raise exceptions.SocketRegistrationError(
				'{}.add_output() only one output is allowed for this node: {}'.format(self.__class__.__name__, self))

		super(SocketInputNode, self).add_output(
			name=name, multi_output=multi_output, display_name=display_name, color=color, data_type=data_type,
			locked=locked, painter_fn=painter_fn)


class SocketOutputNode(node.BaseNode):

	NODE_NAME = 'OutputSocket'

	def __init__(self, view=None, parent_socket=None):
		super(SocketOutputNode, self).__init__(view or inout.SocketInputNodeView)

		self._parent_socket = parent_socket

	@property
	def parent_socket(self):
		"""
		Returns the parent group node socket representing this node.

		:return: socket instance.
		:rtype: tp.common.nodegraph.core.socket.Socket
		"""

		return self._parent_socket

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

		if self._inputs:
			raise exceptions.SocketRegistrationError(
				'{}.add_output() only one input is allowed for this node: {}'.format(self.__class__.__name__, self))

		super(SocketOutputNode, self).add_input(
			name=name, multi_input=multi_input, display_name=display_name, color=color, data_type=data_type,
			locked=locked, painter_fn=painter_fn)

	def add_output(
			self, name='output', multi_output=True, display_name=True, color=None, data_type=None, locked=False,
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

		raise exceptions.SocketRegistrationError(
			'{}.add_output() is not available for {}'.format(self.__class__.__name__, self))
