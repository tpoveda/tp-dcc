#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains packages manager implementation
"""

from tp.core import log
from tp.common.nodegraph.core import exceptions

logger = log.tpLogger


class NodesFactory(object):
	"""
	Node factory class that stores all the node types.
	"""

	def __init__(self):
		super(NodesFactory, self).__init__()

		self._aliases = dict()
		self._names = dict()
		self._nodes = dict()

	# =================================================================================================================
	# PROPERTIES
	# =================================================================================================================

	@property
	def names(self):
		"""
		Returns all currently registered node type identifiers.

		:return: list(str)
		"""

		return self._names

	@property
	def aliases(self):
		"""
		Returns aliases assigned to the node types.

		:return: aliases dict with aliases as keys and node types as values.
		:rtype: dict(str, str)
		"""

		return self._aliases

	@property
	def nodes(self):
		"""
		Returns all registered nodes.

		:return: registered nodes dictionary with identifiers as keys and node classes as values.
		:rtype: dict
		"""

		return self._nodes

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def register_node(self, node_class, alias=None):
		"""
		Registers a new node within this node factory.

		:param class node_class: NodeObject class.
		:param str alias: custom alias for the node identifier
		"""

		if not node_class:
			return

		name = node_class.NODE_NAME
		node_type = node_class.type_

		if self._nodes.get(node_type):
			raise exceptions.NodeRegistrationError('id "{}" already registered!'.format(node_type))
		self._nodes[node_type] = node_class
		if self._names.get(name):
			self._names[name].append(node_type)
		else:
			self._names[name] = [node_type]

		if alias:
			if self._aliases.get(alias):
				raise exceptions.NodeRegistrationError('Alias: {} already registered to "{}"'.format(
					alias, self._aliases.get(alias)))
			self._aliases[alias] = node_type

	def get_node_class(self, node_type=None, alias=None):
		"""
		Creates a node object by the node identifier or alias.

		:param str node_type: node type.
		:param str alias: optional alias name.
		:return: newly created node object.
		:rtype: Base Node
		"""

		if alias and alias in self._aliases.get(alias):
			node_type = self._aliases[alias]

		node_class = self._nodes.get(node_type)
		if not node_class:
			logger.error('Cannot find node type: {}'.format(node_type))

		return node_class

	def create_node_instance(self, node_type):
		"""
		Creates a new node instance based on the node type identifier or alias.

		:param str node_type:  node type or optional alias name.
		:return: newly created node instance.
		"""

		if node_type in self._aliases:
			node_type = self._aliases[node_type]

		_node_class = self._nodes.get(node_type)
		if not _node_class:
			logger.error('Cannot find node type: {}'.format(node_type))

		return _node_class()

	def clear_registered_nodes(self):
		"""
		Clears out all registered nodes.
		"""

		self._nodes.clear()
		self._names.clear()
		self._aliases.clear()
