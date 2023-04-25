# ! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with animation nodes in Maya
"""

import maya.cmds as cmds

from tp.common.python import helpers
from tp.maya.cmds import node


def is_node_animated(nodes_list, filter_joints=True, recursive=True):
	"""
	Returns whether the list of given joints are animated or not. A joint, to be considered animated, it must being
	moved either by animation keys, constraints, or any motion up its hierarchy.

	:param list[str] nodes_list: list of node names to check.
	:param bool filter_joints: whether to only look at joint objects in the list.
	:param bool recursive: whether the check is done recursively.
	:return: True if any of the given nodes are animated; False otherwise.
	:rtype: bool
	"""

	nodes_list = helpers.force_list(nodes_list)

	if filter_joints:
		nodes_list = [x for x in nodes_list if cmds.nodeType(x) == 'joint']

	for node in nodes_list:
		if cmds.listConnections(node, type='animCurve') or \
				cmds.listConnections(node, type='constraint', s=True, d=False) or \
				cmds.listConnections(node, type='animLayer', s=False, d=True):
			return True
		else:
			if recursive:
				return is_node_animated([node.getParent()])
			else:
				return False

	return False


def filter_animated_nodes(nodes):
	"""
	Filters given nodes, returning a new list with only the nodes that have key frames.

	:param list[str] nodes: list of node names
	:return: list of animated nodes.
	:rtype: list[str]
	"""

	animated_nodes = list()
	for node in nodes:
		if cmds.keyframe(node, query=True, keyframeCount=True, time=(-100000, 10000000)):
			animated_nodes.append(node)

	return animated_nodes


def animated_nodes(nodes_flag='all', select=True):
	"""
	Returns and optionally selects animated nodes with keyframes.

	:param str nodes_flag: selection flag.
	:param bool select: whether to selected animated nodes.
	:return: list of animated nodes.
	:rtype: list(str)
	"""

	node_names = node.nodes_from_nodes_flag(nodes_flag=nodes_flag)
	animated_node_names = list()
	if node_names:
		animated_node_names.extend(filter_animated_nodes(node_names))
		if select:
			cmds.select(animated_node_names, replace=True)

	return animated_node_names
