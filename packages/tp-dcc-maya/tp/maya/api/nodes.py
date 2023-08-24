from __future__ import annotations

from typing import List

import maya.api.OpenMaya as OpenMaya

from tp.maya.api import base
from tp.maya.om import nodes


def root_node(node: base.DagNode, node_type: OpenMaya.MTypeId):
	"""
	Recursively traverses up the hierarchy until finding the first object that does not have a parent.

	:param tp.maya.api.base.DagNode node: Dag node instance to get root of.
	:param OpenMaya.MTypeId node_type: node type for the root node.
	:return: found root node.
	:rtype: base.DagNode
	"""

	return base.node_by_object(nodes.root_node(node.object(), node_type=node_type))


def average_position(nodes_to_find: List[base.DagNode]) -> OpenMaya.MVector:
	"""
	Returns the average position on all given nodes.

	:param List[base.DagNode] nodes_to_find: nodes to get average position from.
	:return: average nodes position.
	:rtype: OpenMaya.MVector
	:raises ValueError: if no nodes are given.
	"""

	count = len(nodes_to_find)
	if count == 0:
		raise ValueError(f'Invalid number of nodes given: {count}')

	center = OpenMaya.MVector()
	for i in nodes_to_find:
		center += i.translation(space=OpenMaya.MSpace.kWorld)
	center /= count

	return center


def average_normal_vector(nodes_to_find: List[base.DagNode], axis: OpenMaya.MVector) -> OpenMaya.MVector:
	"""
	Returns the averaged normal based on the given node rotations.

	:param List[base.DagNode] nodes_to_find: nodes to get average normal vector from.
	:param OpenMaya.MVector axis: axis to rate around.
	:return: normalized averaged rotations as a vector.
	:rtype: OpenMaya.MVector
	"""

	up_axis = OpenMaya.MGlobal.upAxis()
	average = OpenMaya.MVector(up_axis.x, up_axis.y, up_axis.z)
	for node in nodes_to_find:
		world_orient = node.rotation(space=OpenMaya.MSpace.kWorld)
		rotation = axis.rotateBy(world_orient.asEulerRotation())
		average.x += rotation.x
		average.y += rotation.y
		average.z += rotation.z
	average.normalize()
	if average.x == 0 and average.y == 0 and average.z == 0:
		average.x = 1

	return average
