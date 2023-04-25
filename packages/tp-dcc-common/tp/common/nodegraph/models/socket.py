#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains socket model implementation
"""

from collections import defaultdict

from tp.common.nodegraph.core import register


class SocketModel(object):
	def __init__(self, node):
		super(SocketModel, self).__init__()

		self.node = node
		self.direction = ''
		self.name = 'port'
		self.display_name = True
		self.multi_connection = False
		self.visible = True
		self.locked = False
		self.connected_sockets = defaultdict(list)
		self.data_type = register.DataTypes.EXEC

	def __repr__(self):
		return '<{}(\'{}\') object at {}>'.format(self.__class__.__name__, self.name, hex(id(self)))

	# =================================================================================================================
	# OVERRIDES
	# =================================================================================================================

	def serialize(self):
		"""
		Function that serializes current model into a dictionary.

		:return: serialized node with node id as the key and properties as the values.
		:rtype: dict
			example:
			{
				'direction': 'in',
				'name': 'port',
				'display_name': True,
				'multi_connection': False,
				'visible': True,
				'locked': False,
				'connected_sockets': {<node_id>: [<port_name>, <port_name>]|
			}
		"""

		properties = self.__dict__.copy()
		properties.pop('node')
		properties['connected_sockets'] = dict(properties.pop('connected_sockets'))

		return properties
