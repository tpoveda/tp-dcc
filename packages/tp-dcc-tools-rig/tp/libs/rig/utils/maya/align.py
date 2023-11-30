from __future__ import annotations

from typing import List, Iterator

from tp.maya import api
from tp.maya.om import mathlib


def construct_plane_from_positions(
		position_vectors: List[api.OpenMaya.MVector, api.OpenMaya.MVector, api.OpenMaya.MVector],
		nodes: List[api.DagNode, ...], rotate_axis: api.OpenMaya.MVector = mathlib.Z_AXIS_VECTOR) -> api.OpenMaya.MPlane:
	"""
	Constructs a plane instance based on the averaged normal of the given node rotations.

	:param  List[api.OpenMaya.MVector, api.OpenMaya.MVector, api.OpenMaya.MVector] position_vectors: list with two or
		three vectors or more defining normals.
	:param List[api.DagNode, ...] nodes: list of nodes which will have their rotations taken into account when creating
		the plane to get the best normal direction.
	:param api.OpenMaya.MVector rotate_axis: rotation axis to use.
	:return: newly created plane.
	:rtype: api.OpenMaya.MPlane
	"""

	plane_a = api.OpenMaya.MPlane()
	normal = api.OpenMaya.MVector(api.OpenMaya.MVector.kXaxisVector)
	if len(position_vectors) == 3:
		normal = mathlib.three_point_normal(*position_vectors)
	elif len(position_vectors) > 3:
		average_position = api.average_position(nodes)
		normal = mathlib.three_point_normal(
			nodes[0].translation(space=api.kWorldSpace), average_position, nodes[-1].translation(space=api.kWorldSpace))
	else:
		for i in range(len(position_vectors)):
			current = api.Vector(position_vectors[i][0], position_vectors[i][1], position_vectors[i][2])
			prev = api.Vector(position_vectors[i - 1][0], position_vectors[i - 1][1], position_vectors[i - 1][2])
			normal += api.Vector(
				(prev.z + current.z) * (prev.y - current.y),
				(prev.x + current.x) * (prev.z - current.z),
				(prev.y + current.y) * (prev.x - current.x),
			)
		normal.normalize()

	average_normal = api.average_normal_vector(nodes, rotate_axis)
	if normal * average_normal < 0:
		normal *= -1

	plane_a.setPlane(normal, -normal * position_vectors[0])

	return plane_a


def align_nodes_iterator(
		nodes: List[api.DagNode], plane: api.OpenMaya.MPlane,
		skip_end: bool = True) -> Iterator[api.DagNode, api.DagNode]:
	"""
	Generator function that iterates over each node, protect its position in the world and returns eac node, and it's
	target.

	This function will handle setting translations while compensating for hierarchy state.

	:param List[api.DagNode] nodes: list of nodes to align.
	:param api.OpenMaya.MPlane plane: plane wher each node will be protected on.
	:param bool skip_end: whether to skip end node.
	:return: iterated nodes as a tuple with the node to set aligment as first element and the target node as the second
		element.
	:rtype: Iterator[api.DagNode, api.DagNode]
	"""

	node_array = nodes[:-1] if skip_end else nodes
	child_map = {}
	change_map = []
	last_index = len(node_array) - 1

	# un-parent all children so we can change the positions and orientations
	for current_node in reversed(node_array):
		children = current_node.children((api.kNodeTypes.kTransform, api.kNodeTypes.kJoint))
		child_map[current_node] = children
		for child in children:
			child.setParent(None)

	# update all positions and orientations
	for i, current_node in enumerate(node_array):
		translation = current_node.translation(space=api.kWorldSpace)
		if i == last_index:
			target_node = nodes[i + 1] if skip_end else None
			new_translation = translation if skip_end else mathlib.closest_point_on_plane(translation, plane)
		else:
			target_node = nodes[i + 1]
			new_translation = mathlib.closest_point_on_plane(translation, plane)
		current_node.setTranslation(new_translation, space=api.kWorldSpace)
		change_map.append((current_node, target_node, new_translation))

	# now yield, so client can run any code before re-parenting the nodes
	for current_node, target_node, new_translation in change_map:
		yield current_node, target_node
		for child in child_map[current_node]:
			child.setParent(current_node)
