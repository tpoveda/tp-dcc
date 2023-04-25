#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract object implementations
"""

from tp.common.nodegraph.core import consts, utils, exceptions, commands
from tp.common.nodegraph.models import node as node_model


class Node(object):
	"""
	Main class that all nodes should inherit from
	"""

	__identifier__ = 'tp.common.nodegraph.nodes'		# unique node identifier
	NODE_NAME = None									# base node name

	def __init__(self, view):
		super(Node, self).__init__()

		self._graph = None
		self._model = node_model.NodeModel()
		self._model.type_ = self.type_
		self._model.name = self.NODE_NAME

		_node_item = view
		if _node_item is None:
			raise RuntimeError('No node view specified node')

		self._view = _node_item()
		self._view.type_ = self.type_
		self._view.name = self.model.name
		self._view.id = self._model.id
		self._view.layout_direction = self._model.layout_direction

	def __repr__(self):
		return '<{}("{}") object at {}>'.format(self.__class__.__name__, self.NODE_NAME, hex(id(self)))

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@utils.ClassProperty
	def type_(cls):
		"""
		Returns node type identifier followed by the class name. For example "com.tp.NodeObject"

		:return: node type.
		:rtype: str
		"""

		return '{}.{}'.format(cls.__identifier__, cls.__name__)

	@property
	def id(self):
		"""
		Returns node unique id
		:return: node unique id.
		:rtype: str
		"""

		return self.model.id

	@property
	def graph(self):
		"""
		Returns parent node graph.

		:return: node graph object.
		:rtype: NodeGraph
		"""

		return self._graph

	@graph.setter
	def graph(self, value):
		"""
		Sets parent node graph.

		:param NodeGraph value: node graph object this node belongs to.
		"""

		self._graph = value

	@property
	def model(self):
		"""
		Returns node model.

		:return: node model.
		:rtype: NodeModel
		"""

		return self._model

	@model.setter
	def model(self, value):
		"""
		Sets the node model.

		:param NodeModel value: node model object.
		"""

		self._model = value
		self._model.type = self.type_
		self._model.id = self.view.id

		# update the view
		self.update()

	@property
	def view(self):
		"""
		Returns node view used in the scene for this node.

		:return: node view item.
		:rtype: NodeView
		"""

		return self._view

	@view.setter
	def view(self, value):
		"""
		Sets the node view used in the scene for this node.

		:param NodeView value: node view item.
		"""

		if self._view:
			old_view = self._view
			scene = self._view.scene()
			scene.removeItem(old_view)
			self._view = value
			scene.addItem(self._view)
		else:
			self._view = value

		self._view.id = self.model.id
		self.NODE_NAME = self._view.name

		# update the view
		self.update()

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def update(self):
		"""
		Updates the node view from model.
		"""

		settings = self.model.to_dict()[self.model.id]
		settings['id'] = self.model.id
		if settings.get('custom'):
			settings['widgets'] = settings.pop('custom')

		self.view.from_dict(settings)

	def name(self):
		"""
		Returns node name.

		:return: node name.
		:rtype: str
		"""

		return self._model.name

	def set_name(self, name):
		"""
		Sets node name.

		:param str name: node name
		"""

		self.set_property('name', name)

	def path(self):
		"""
		Returns node path.

		:return: node path.
		:rtype: str
		"""

		return '/' + self.name() if self._parent is None else self._parent.path() + '/' + self.name()

	def disabled(self):
		"""
		Returns whether the node is enabled.

		:return: True if the node is disabled; False otherwise.
		:rtype: bool
		"""

		return self._model.disabled

	def set_disabled(self, flag):
		"""
		Sets whether the node is disabled.

		:param bool flag: True to disable the node; False otherwise.
		"""

		self.set_property('disabled', flag)

	def selected(self):
		"""
		Returns whether the node is selected.

		:return: True if the node is selected; False otherwise.
		:rtype: bool
		"""

		self._model.selected = self.view.isSelected()
		return self._model.selected

	def set_selected(self, flag=True):
		"""
		Sets whether the node is selected.

		:param bool flag: True to select the node.
		"""

		self.set_property('selected', flag)

	def color(self):
		"""
		Returns the node RGB color.

		:return: RGB color in 0 to 25 range.
		:rtype: tuple(int, int, int)
		"""

		r, g, b, a = self._model.color
		return r, g, b

	def set_color(self, r, g, b):
		"""
		Sets the RGB color of the node.

		:param int r: red channel color in 0 to 255 range.
		:param int g: green channel color in 0 to 255 range.
		:param int b: blue channel color in 0 to 255 range.
		"""

		self.set_property('color', (r, g, b, 255))

	def x_pos(self):
		"""
		Returns the node X position in the node graph.

		:return: X position.
		:rtype: float
		"""

		return self.model.pos[0]

	def set_x_pos(self, x):
		"""
		Sets the node X position in the node graph.

		:param float x: node X position.
		"""

		y = self.pos()[1]
		self.set_pos(float(x), y)

	def y_pos(self):
		"""
		Returns the node Y position in the node graph.

		:return: Y position.
		:rtype: float
		"""

		return self.model.pos[1]

	def set_y_pos(self, y):
		"""
		Sets the node Y position in the node graph.

		:param float y: node Y position.
		"""

		x = self.pos()[0]
		self.set_pos(x, float(y))

	def pos(self):
		"""
		Returns the node XY position in the node graph.

		:return: X, Y position.
		:rtype: tuple(float, float)
		"""

		if self.view.xy_pos and self.view.xy_pos != self.model.pos:
			self.model.pos = self.view.xy_pos

		return self.model.pos

	def set_pos(self, x, y):
		"""
		Sets the node X and Y position in the node graph.

		:param float x: node X position.
		:param float y: node Y position.
		"""

		self.set_property('pos', [float(x), float(y)])

	def create_property(self, name, value, items=None, range=None, widget_type=None, tab=None):
		"""
		Creates a custom property to the node.

		:param str  name: name of the property.
		:param object value: property data.
		:param list(str) items: list of items used by COMBO widget type.
		:param tuple(int, int) or tuple(float, float) range: min and max values used by SLIDER widget type.
		:param int widget_type: widget flag to display in the properties editor.
		:param str tab: name of the widget tab to display in the properties editor.
		"""

		widget_type = widget_type or consts.PropertiesEditorWidgets.HIDDEN
		self._model.add_property(name, value, items, range, widget_type, tab)

	def has_property(self, name):
		"""
		Returns whether node custom property exists.

		:param str name: name of the property to check.
		:return: True if the custom property exists in this node; False otherwise.
		:rtype: bool
		"""

		return name in self._model.custom_properties.keys()

	def get_properties(self):
		"""
		Returns all the node properties.

		:return: node properties.
		:rtype: dict
		"""

		properties = self._model.to_dict()[self.id].copy()
		properties['id'] = self.id

		return properties

	def get_property(self, name):
		"""
		Returns the node custom property value.

		:param str name: name of the custom property value to retrieve.
		:return: property value.
		:rtype: object
		"""

		if self.graph and name == 'selected':
			self._model.set_property(name, self.view.selected)

		return self._model.get_property(name)

	def set_property(self, name, value, push_undo=True):
		"""
		Sets the value on the node custom property.

		:param str name: name of the property.
		:param object value: property data value.
		:param bool push_undo: whether to register the command to the undo stack.
		"""

		try:
			if self.get_property(name) == value:
				return
		except Exception:
			pass

		if self.graph and name == 'name':
			if len(value) == 0:
				value = '_'
			value = self.graph.unique_name(value)
			self.NODE_NAME = value

		if self.graph:
			if push_undo:
				undo_stack = self.graph.undo_stack()
				property_change_command = commands.PropertyChangedCommand(self, name, value)
				undo_stack.push(property_change_command)
				if property_change_command.error_message:
					raise exceptions.NodePropertyError(property_change_command.error_message)
			else:
				commands.PropertyChangedCommand(self, name, value)
		else:
			if hasattr(self.view, name):
				setattr(self.view, name, value)
			self.model.set_property(name, value)

	def update_model(self):
		"""
		Updates the node model from view.
		"""

		for name, value in self.view.properties.items():
			if name in self.model.properties.keys():
				setattr(self.model, name, value)
			if name in self.model.custom_properties.keys():
				self.model.custom_properties[name] = value

	def show(self):
		"""
		Shows this node.
		"""

		self.view.visible = True
		self.model.visible = True

	def hide(self):
		"""
		Hides this node.
		"""

		self.view.visible = False
		self.model.visible = False
