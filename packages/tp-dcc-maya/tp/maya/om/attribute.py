#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with OpenMaya attributes
"""

import re

import maya.api.OpenMaya as OpenMaya

from tp.core import log
from tp.common.python import helpers

logger = log.tpLogger


def attr_mplug(attr):
	"""
	Returns the MPlug object for the given attribute.

	:param attr: str, the attribute to return the MPlug for
	:return: attribute plug.
	:rtype: OpenMaya.MPlug
	"""

	# import here to avoid cyclic imports
	from tp.maya.om import node

	attr_elem_list = attr.split('.')
	attr_obj = node.mobject(node_name=attr_elem_list[0])
	attr_obj_fn = OpenMaya.MFnDependencyNode(attr_obj)

	# get attribute element components (name, index)
	attr_elem = re.findall(r'\w+', attr_elem_list[1])

	# get MPlug to top level attribute
	attr_mplug = attr_obj_fn.findPlug(attr_elem[0], True)
	if len(attr_elem) == 2:
		attr_mplug = attr_mplug.elementByLogicalIndex(int(attr_elem[1]))

	# traverse to lowest child attribute
	for i in range(2, len(attr_elem_list)):
		attr_elem = re.findall(r'\w+', attr_elem_list[i])
		for n in range(attr_mplug.numChildren()):
			child_plug = attr_mplug.child(n)
			logger.debug('Looking for "{}", found "{}"'.format(attr_elem[0], child_plug.partialName()))

	return attr_mplug


def connection_index(attr, as_source=True, connected_to=None):
	"""
	Return the index of the connection
	:param attr: name, attribute we want to check connection index of
	:param as_source: bool, Whether to check source connection
	:param connected_to:
	:return: int
	"""

	attr_plug = attr_mplug(attr)

	# get connectced plugs
	attr_plug_connections = OpenMaya.MPlugArray()
	connected = attr_plug.connectedTo(attr_plug_connections, not as_source, as_source)
	if not connected:
		connection_type = 'outgoinhg' if as_source else 'incoming'
		raise Exception('No {} connections found for attribute "{}"'.format(connection_type, attr))

	# get connected index
	for i in range(len(attr_plug_connections)):
		connected_plug = attr_plug_connections[i]
		connected_node = connected_plug.partialName(True, False, False, False, False).split('.')[0]
		if connected_to and not connected_to == connected_node:
			continue
		return connected_plug.logicalIndex()

	return -1


def connected_nodes(attr, as_source=True, connected_to=None):
	"""
	Returns a list of all connected nodes to given attribute.

	:param attr: str
	:param as_source: bool
	:param connected_to: str or None
	:return: list(str)
	"""

	connected_nodes = list()

	attr_plug = attr_mplug(attr)
	attr_plug_connections = OpenMaya.MPlugArray()
	connected = attr_plug.connectedTo(attr_plug_connections, not as_source, as_source)
	if not connected:
		return connected_nodes

	num_connections = len(attr_plug_connections)
	for i in range(num_connections):
		connected_plug = attr_plug_connections[i]
		connected_node = connected_plug.partialName(True, False, False, False, False)
		if connected_to and not connected_to == connected_node:
			continue
		connected_nodes.append(connected_node)

	return connected_nodes


def set_lock_state_on_attributes(mobj, attributes, state=True):
	"""
	Locks and unlocks the given attributes.

	:param OpenMaya.MObject mobj: node whose attributes we want to lock/unlock.
	:param list(str) attributes: list of attributes names to lock/unlock.
	:param bool state: whether to lock or unlock the attributes.
	:return: True if the attributes lock/unlock operation was successful; False otherwise.
	:rtype: bool
	"""

	attributes = helpers.force_list(attributes)
	dep = OpenMaya.MFnDependencyNode(mobj)
	for attr in attributes:
		found_plug = dep.findPlug(attr, False)
		if found_plug.isLocked != state:
			found_plug.isLocked = state

	return True


def show_hidde_attributes(mobj, attributes, state=False):
	"""
	Shows or hides given attributes in the channel box.

	:param OpenMaya.MObject mobj: node whose attributes we want to show/hide.
	:param list(str) attributes: list of attributes names to lock/unlock
	:param bool state: whether to hide or show the attributes.
	:return: True if the attributes show/hide operation was successful; False otherwise.
	:rtype: bool
	"""

	dep = OpenMaya.MFnDependencyNode(mobj)
	attributes = helpers.force_list(attributes)
	for attr in attributes:
		found_plug = dep.findPlug(attr, False)
		if found_plug.isChannelBox != state:
			found_plug.isChannelBox = state

	return True
