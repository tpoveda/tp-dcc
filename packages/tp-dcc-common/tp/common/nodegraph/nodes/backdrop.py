from tp.common.nodegraph.core import consts, abstract
from tp.common.nodegraph.views import backdrop


class BackdropNode(abstract.Node):
	"""
	Custom node that allows other node objects to be nested inside.
	"""

	NODE_NAME = 'Backdrop'

	def __init__(self, view=None):
		super(BackdropNode, self).__init__(view=view or backdrop.BackdropNodeView)

		self.model.color = (5, 129, 138, 255)
		self.create_property('backdrop_text', '', widget_type=consts.PropertiesEditorWidgets.TEXT_EDIT, tab='Backdrop')

	# ==================================================================================================================
	# BASE
	# ==================================================================================================================

	def update_property(self, update_property, value=None):
		"""
		Updates background property with given value.

		:param str update_property: updated property type.
		:param object or None value: optional updated value.
		"""

		if update_property == 'sizer_mouse_release':
			self.graph.begin_undo('Resized {}'.format(self.name()))
			self.set_property('width', value['width'])
			self.set_property('height', value['height'])
			self.set_pos(*value['pos'])
			self.graph.end_undo()
		elif update_property == 'sizer_double_clicked':
			self.graph.begin_undo('Auto Resize {}'.format(self.name()))
			self.set_property('width', value['width'])
			self.set_property('height', value['height'])
			self.set_pos(*value['pos'])
			self.graph.end_undo()

	def nodes(self):
		"""
		Returns a list nodes wrapped within this backdrop node instance.

		:return: list nodes.
		:rtype: list[tp.common.nodegraph.core.node.BaseNode]
		"""

		node_ids = [n.id for n in self.view.nodes()]
		return [self.graph.node_by_id(node_id) for node_id in node_ids]

	def text(self):
		"""
		Returns the text on the backdrop node.

		:return: backdrop text.
		:rtype: str
		"""

		return self.get_property('backdrop_text')

	def set_text(self, value):
		"""
		Sets text to be displayed in the backdrop node.

		:param str value: backdrop text.
		"""

		self.set_property('backdrop_text', value)

	def size(self):
		"""
		Returns the current size of the node.

		:return: node size.
		:rtype: tuple(float, float)
		"""

		self.model.width = self.view.width
		self.model.height = self.view.height
		return self.model.width, self.model.height

	def set_size(self, width, height):
		"""
		Sets the backdrop size.

		:param float width: backdrop width size.
		:param float height: backdrop height size.
		"""

		if self.graph:
			self.graph.begin_undo('Backdrop Set Size')
			self.set_property('width', width)
			self.set_property('height', height)
			self.graph.end_undo()
			return
		self.view.width, self.view.height = width, height
		self.model.width, self.model.height = width, height

	def auto_size(self):
		"""
		Auto resize the backdrop node to fit around the intersecting nodes.
		"""
		self.graph.begin_undo('"{}" auto resize'.format(self.name()))
		size = self.view.calc_backdrop_size()
		self.set_property('width', size['width'])
		self.set_property('height', size['height'])
		self.set_pos(*size['pos'])
		self.graph.end_undo()

	def wrap_nodes(self, nodes):
		"""
		Set the backdrop size to fit around specified nodes.

		Args:
			nodes (list[NodeGraphQt.NodeObject]): list of nodes.
		"""
		if not nodes:
			return
		self.graph.begin_undo('"{}" wrap nodes'.format(self.name()))
		size = self.view.calc_backdrop_size([n.view for n in nodes])
		self.set_property('width', size['width'])
		self.set_property('height', size['height'])
		self.set_pos(*size['pos'])
		self.graph.end_undo()
