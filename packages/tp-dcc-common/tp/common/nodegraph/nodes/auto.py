import time
import hashlib
import traceback

from tp.core import log
from tp.common.qt import api as qt
from tp.common.nodegraph.nodes import exec

logger = log.tpLogger


def _update_nodes(nodes):
	for found_node in nodes:
		if found_node.disabled():
			continue
		found_node.cook()
		if found_node.is_invalid:
			break


def update_node_down_stream(nodes):
	if not isinstance(nodes, list):
		nodes = [nodes]
	_update_nodes(exec.topological_sort_by_down(start_nodes=nodes))


def update_node_up_stream(nodes):
	if not isinstance(nodes, list):
		nodes = [nodes]
	_update_nodes(exec.topological_sort_by_up(start_nodes=nodes))


def get_data_type(data_type):
	if not isinstance(data_type, str):
		if hasattr(data_type, '__name__'):
			data_type = data_type.__name__
		else:
			data_type = type(data_type).__name__
	return data_type


class AutoNode(exec.ExecNode):

	NODE_NAME = 'Auto'

	def __init__(self, default_input_type=None, default_output_type=None):
		super(AutoNode, self).__init__()

		self._default_input_type = default_input_type
		self._default_output_type = default_output_type

		self.create_property('auto_cook', True)

	# ==================================================================================================================
	# PROPERTIES
	# ==================================================================================================================

	@property
	def auto_cook(self):
		return self.get_property('auto_cook')

	@auto_cook.setter
	def auto_cook(self, flag):
		if self.auto_cook == flag:
			return
		self.model.set_property('auto_cook', flag)
		self._color_effect.setEnabled(not flag)
		if not flag:
			self._color_effect.setColor(qt.QColor(*self.STOP_COOK_COLOR))

	# ==================================================================================================================
	# OVERRIDES
	# ==================================================================================================================

	def set_property(self, name, value, push_undo=True):
		super(AutoNode, self).set_property(name=name, value=value, push_undo=push_undo)

		self.set_socket_type(name, type(value).__name__)
		if name in self.model.custom_properties.keys():
			self.update_stream()

	def add_input(
			self, name='input', multi_input=False, display_name=True, color=None, data_type=None, locked=False,
			painter_fn=None):
		new_input = super(AutoNode, self).add_input(
			name=name, multi_input=multi_input, display_name=display_name, color=color, data_type=data_type,
			locked=locked, painter_fn=painter_fn)

		if not data_type:
			data_type = self._default_input_type
		self.set_socket_type(new_input, get_data_type(data_type))

		return new_input

	def add_output(self, name='output', multi_output=True, display_name=True, color=None, data_type=None, locked=False,
				   painter_fn=None):
		new_output = super(AutoNode, self).add_output(
			name=name, multi_output=multi_output, display_name=display_name, color=color, data_type=data_type,
			locked=locked, painter_fn=painter_fn)

		if not data_type:
			data_type = self._default_output_type
		self.set_socket_type(new_output, get_data_type(data_type))

		return new_output

	def set_disabled(self, flag):
		super(AutoNode, self).set_disabled(flag)

		self.update_stream()

	def _on_input_connected(self, input_socket, output_socket):
		if self.check_socket_type(input_socket, output_socket):
			self.update_stream()
		else:
			self._need_cook = False
			input_socket.disconnect_from(output_socket)

	def _on_input_disconnected(self, input_socket, output_socket):
		if not self._need_cook:
			self._need_cook = True
			return
		self.update_stream()

	def cook(self):
		"""
		Internal function that executes the node.
		"""

		_temp_cook = self.auto_cook
		self.model.set_property('auto_cook', False)

		if self._is_invalid:
			self._close_error()

		start_time = time.time()
		logger.info('Cooking {}...'.format(self))
		try:
			self.execute()
		except Exception:
			logger.exception('Failed to cook {} {}'.format(self.name(), self))
			self.error(traceback.format_exc())
			raise
		finally:
			self.model.set_property('auto_cook', _temp_cook)

		if self._is_invalid:
			return

		self._cook_time = time.time() - start_time
		self._need_cook = False

		return 0

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def update_stream(self, force_cook=False):
		if not force_cook:
			if not self.auto_cook or not self._need_cook:
				return
			if self.graph is not None and not self.graph.auto_update:
				return
		update_node_up_stream(self)

	# ==================================================================================================================
	# SOCKETS
	# ==================================================================================================================

	def check_socket_type(self, to_socket, from_socket):
		if to_socket.data_type != from_socket.data_type:
			if to_socket.data_type == 'NoneType' or from_socket.data_type == 'NoneType':
				return True
			# for types in self.matchTypes:
			# 	if to_socket.data_type in types and from_socket.data_type in types:
			# 		return True
			return False

		return True

	def set_socket_type(self, socket_to_set, data_type: str):
		"""
		Set the data_type of the port.

		Args:
			port(Port): the port to set the data_type.
			data_type(str): port new data_type.
		"""

		current_socket = None

		if type(socket_to_set) is socket.Socket:
			current_socket = socket_to_set
		elif type(socket_to_set) is str:
			inputs = self.inputs()
			outputs = self.outputs()
			if socket_to_set in inputs.keys():
				current_socket = inputs[socket_to_set]
			elif socket_to_set in outputs.keys():
				current_socket = outputs[socket_to_set]

		if current_socket:
			if current_socket.data_type == data_type:
				return
			else:
				current_socket.data_type = data_type

			current_socket.border_color = current_socket.color = CryptoColors.get(data_type)
			conn_type = 'multi' if current_socket.multi_connection() else 'single'
			current_socket.view.setToolTip('{}: {} ({}) '.format(current_socket.name(), data_type, conn_type))


class CryptoColors(object):
	"""
	Generate random color based on strings
	"""

	colors = {}

	@staticmethod
	def get(text, Min=50, Max=200):
		if text in CryptoColors.colors:
			return CryptoColors.colors[text]
		h = hashlib.sha256(text.encode('utf-8')).hexdigest()
		d = int('0xFFFFFFFFFFFFFFFF', 0)
		r = int(Min + (int("0x" + h[:16], 0) / d) * (Max - Min))
		g = int(Min + (int("0x" + h[16:32], 0) / d) * (Max - Min))
		b = int(Min + (int("0x" + h[32:48], 0) / d) * (Max - Min))
		# a = int(Min + (int("0x" + h[48:], 0) / d) * (Max - Min))
		CryptoColors.colors[text] = (r, g, b, 255)
		return CryptoColors.colors[text]
