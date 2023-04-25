#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains graph model implementation
"""

from tp.common.nodegraph.core import consts


class NodeGraphModel(object):
	"""
	Class that defines the model of a node graph
	"""

	def __init__(self):
		super(NodeGraphModel, self).__init__()

		self.nodes = dict()
		self.session = ''
		self.acyclic = True
		self.connector_collision = False
		self.layout_direction = consts.GraphLayoutDirection.HORIZONTAL

		self._common_node_properties = dict()

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def get_common_properties(self):
		"""
		Returns all common node properties.

		:return: common node properties.
		:rtype: dict
			example:
			{
				'base.FooNode':
				{
					'my_property':
					{
						'widget_type': 0,
						'tab': 'Properties',
						'items': ['foo', 'bar', 'test'],
						'range': (0, 100)
					}
				}
			}
		"""

		return self._common_node_properties

	def set_node_common_properties(self, attributes_dict):
		"""
		Stores common node properties internally.

		:param dict attributes_dict: common node properties.
			example:
			{
				'base.FooNode':
				{
					'my_property':
					{
						'widget_type': 0,
						'tab': 'Properties',
						'items': ['foo', 'bar', 'test'],
						'range': (0, 100)
					}
				}
			}
		"""

		for node_type in attributes_dict.keys():
			node_properties = attributes_dict[node_type]
			if node_type not in self._common_node_properties.keys():
				self._common_node_properties[node_type] = node_properties
				continue
			for property_name, property_attributes in node_properties.items():
				common_properties = self._common_node_properties[node_type]
				if property_name not in common_properties.keys():
					common_properties[property_name] = property_attributes
					continue
				common_properties[property_name].update(property_attributes)

	def get_node_common_properties(self, node_type):
		"""
		Returns all the common properties for a registered node.

		:param str node_type: node type.
		:return: node common properties.
		:rtype: dict
		"""

		return self._common_node_properties.get(node_type, None)
