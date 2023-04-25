#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains graph node model implementation
"""

import json

from tp.common.nodegraph.core import consts, exceptions


class NodeModel(object):
	def __init__(self):
		super(NodeModel, self).__init__()

		self.type_ = None
		self.id = hex(id(self))
		self.name = 'node'
		self.icon = None
		self.color = consts.NODE_COLOR
		self.border_color = consts.NODE_BORDER_COLOR
		self.header_color = consts.NODE_HEADER_COLOR
		self.text_color = consts.NODE_TEXT_COLOR
		self.disabled = False
		self.selected = False
		self.visible = True
		self.dynamic_port = False
		self.width = 100.0
		self.height = 80.0
		self.pos = [0.0, 0.0]
		self.layout_direction = consts.GraphLayoutDirection.HORIZONTAL
		self.inputs = dict()
		self.outputs = dict()
		self.subgraph_session = dict()

		self._custom_properties = dict()
		self._graph_model = None                          # node graph model set node added time
		self._graph_model = None                          # node graph model set node added time
		self._TEMP_property_attributes = dict()           # property attributes (delete when node is added to graph)
		self._TEMP_property_widget_types = {              # property widget types (deleted when node is added to graph)
			'type': consts.PropertiesEditorWidgets.LABEL,
			'id': consts.PropertiesEditorWidgets.LABEL,
			'icon': consts.PropertiesEditorWidgets.HIDDEN,
			'name': consts.PropertiesEditorWidgets.LINE_EDIT,
			'color': consts.PropertiesEditorWidgets.COLOR_PICKER,
			'border_color': consts.PropertiesEditorWidgets.COLOR_PICKER,
			'header_color': consts.PropertiesEditorWidgets.COLOR_PICKER,
			'text_color': consts.PropertiesEditorWidgets.COLOR_PICKER,
			'disabled': consts.PropertiesEditorWidgets.CHECKBOX,
			'selected': consts.PropertiesEditorWidgets.HIDDEN,
			'width': consts.PropertiesEditorWidgets.HIDDEN,
			'height': consts.PropertiesEditorWidgets.HIDDEN,
			'pos': consts.PropertiesEditorWidgets.HIDDEN,
			'layout_direction': consts.PropertiesEditorWidgets.HIDDEN,
			'inputs': consts.PropertiesEditorWidgets.HIDDEN,
			'outputs': consts.PropertiesEditorWidgets.HIDDEN
		}

	def __repr__(self):
		return '<{}(\'{}\') object at {}>'.format(self.__class__.__name__, self.name, self.id)

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def graph_model(self):
		"""
		Returns graph model (which is set when node is added into a graph).

		:return: GraphSceneModel
		"""

		return self._graph_model

	@graph_model.setter
	def graph_model(self, value):
		"""
		Sets graph model this node belongs to.

		:param GraphSceneModel value: graph model.
		"""

		self._graph_model = value

	@property
	def properties(self):
		"""
		Returns all default node properties.

		:return: default node properties.
		:rtype: dict
		"""

		default_properties = self.__dict__.copy()
		exclude = ['_graph_model', 'graph_model', '_custom_properties', '_TEMP_property_attributes',
				   '_TEMP_property_widget_types']
		[default_properties.pop(i) for i in exclude if i in default_properties.keys()]

		return default_properties

	@property
	def custom_properties(self):
		"""
		Returns all custom properties specified by the user.

		:return: user defined properties.
		:rtype: dict
		"""

		return self._custom_properties

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def serialize(self):
		"""
		Function that serializes current model into a dictionary.
		"""

		model_dict = self.to_dict()
		return json.dumps(model_dict)

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def to_dict(self):
		"""
		Function that converts current node model into a dictionary.

		:return: serialized node with node id as the key and properties as the values.
		:rtype: dict
			example:
			{
				0x100ff80f0
				{
					'name': 'foo node',
					'color' (50, 50, 50, 255),
					'border_color': (100, 100, 100, 255),
					'text_color': (255, 255, 255, 255),
					'type': 'base.FooNode',
					'selected': False,
					'disabled': False,
					'visible': True,
					'inputs': { <port_name>: {<node_id>: [<port_name>, <port_name>]},
					'outputs': { <port_name>: {<node_id>: [<port_name>, <port_name>]},
					'input_sockets': [<port_name>, <port_name>],
					'output_sockets': [<port_name>, <port_name>],
					width: 0.0,
					height: 0.0,
					pos: (0.0, 0.0),
					'custom': {}
				}
			}
		"""

		node_dict = self.__dict__.copy()
		node_id = node_dict.pop('id')

		inputs = dict()
		outputs = dict()
		input_sockets = list()
		output_sockets = list()

		# serialize input and output sockets
		for name, model in node_dict.pop('inputs').items():
			if self.dynamic_port:
				input_sockets.append(
					dict(name=name, multi_connection=model.multi_connection, display_name=model.display_name,
						 data_type=model.data_type))
			connected_sockets = model.serialize()['connected_sockets']
			if connected_sockets:
				inputs[name] = connected_sockets
		for name, model in node_dict.pop('outputs').items():
			if self.dynamic_port:
				output_sockets.append(
					dict(name=name, multi_connection=model.multi_connection, display_name=model.display_name,
						 data_type=model.data_type))
			connected_sockets = model.serialize()['connected_sockets']
			if connected_sockets:
				outputs[name] = connected_sockets
		if inputs:
			node_dict['inputs'] = inputs
		if outputs:
			node_dict['outputs'] = outputs

		if self.dynamic_port:
			node_dict['input_sockets'] = input_sockets
			node_dict['output_sockets'] = output_sockets

		if self.subgraph_session:
			node_dict['subgraph_sessions'] = self.subgraph_session

		# serialize custom properties (excluding data that cannot be serialized)
		custom_properties = node_dict.pop('_custom_properties', dict())
		if custom_properties:
			to_remove = list()
			supported_types = [float, str, int, list, dict, bool, None, complex, tuple]
			for k, v in custom_properties.items():
				if type(v) not in supported_types:
					try:
						json.dumps(v)
					except:
						to_remove.append(k)
			[custom_properties.pop(k) for k in to_remove]
			node_dict['custom'] = custom_properties

		# exclude internal properties
		exclude = ['_graph_model', 'graph_model', '_custom_properties', '_TEMP_property_attributes',
				   '_TEMP_property_widget_types']
		[node_dict.pop(i) for i in exclude if i in node_dict.keys()]

		return {node_id: node_dict}

	def add_property(self, name, value, items=None, range=None, widget_type=None, tab=None):
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
		tab = tab or 'Properties'

		if name in self.properties.keys():
			raise exceptions.NodePropertyError('"{}" reserved for default property'.format(name))
		if name in self._custom_properties.keys():
			raise exceptions.NodePropertyError('"{}" property already exists'.format(name))

		self._custom_properties[name] = value

		if self._graph_model is None:
			self._TEMP_property_widget_types[name] = widget_type
			self._TEMP_property_attributes[name] = {'tab': tab}
			if items:
				self._TEMP_property_attributes[name]['items'] = items
			if range:
				self._TEMP_property_attributes[name]['range'] = range
		else:
			attributes = {self.type_: {name: {'widget_type': widget_type, 'tab': tab}}}
			if items:
				attributes[self.type_][name]['items'] = items
			if range:
				attributes[self.type_][name]['range'] = range
			self._graph_model.set_node_common_properties(attributes)

	def get_property(self, name):
		"""
		Returns the node custom property value.

		:param str name: name of the custom property value to retrieve.
		:return: property value.
		:rtype: object
		"""

		if name in self.properties.keys():
			return self.properties[name]

		return self._custom_properties.get(name, None)

	def set_property(self, name, value):
		"""
		Sets the value on the node custom property.

		:param str name: name of the property.
		:param object value: property data value.
		:return: True if property was set successfully; False otherwise.
		:rtype: bool
		:raises NodePropertyError: if an accessed property does not exist.
		"""

		if name in self.properties.keys():
			setattr(self, name, value)
		elif name in self._custom_properties.keys():
			self._custom_properties[name] = value
		else:
			raise exceptions.NodePropertyError('No property "{}"'.format(name))

		return True

	def get_widget_type(self, name):
		"""
		Returns the widget type used by the property with given name.

		:param str name: property name.
		:return: property widget type.
		:rtype: str
		"""

		model = self._graph_model
		if model is None:
			return self._TEMP_property_widget_types.get(name)
		return model.get_node_common_properties(self.type_)[name]['widget_type']

	def get_tab_name(self, name):
		"""
		Returns the tab name where property with given name should be located within the properties editor.

		:param str name: property name.
		:return: properties editor tab name.
		:rtype: str or None
		"""

		model = self._graph_model
		if model is None:
			attrs = self._TEMP_property_attributes.get(name)
			if attrs:
				return attrs[name].get('tab')
			return
		return model.get_node_common_properties(self.type_)[name]['tab']
