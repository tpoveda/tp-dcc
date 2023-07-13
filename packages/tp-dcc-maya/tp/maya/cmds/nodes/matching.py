#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related to matching node transformations.
"""

from __future__ import annotations

from typing import List, Iterable

import maya.cmds as cmds
import maya.mel as mel

from tp.maya.cmds.nodes import selection, attributes


def average_normals(normals: List[Iterable[float, float, float],...]) -> List[float, float, float]:
	"""
	Retursn the average values of the given normals.

	:param List[Iterable[float, float, float],...] normals: list of normals to average
		e.g: [[0.1, 0.9, 0.0], [0.0, 0.5, 0.5]]
	:return: averaged normals.
		[0.5, 0.75, 0.25]
	:rtype: List[float, float, float]
	"""

	_average_normals = [0, 0, 0]
	for x, y, z in normals:
		_average_normals[0] += x
		_average_normals[1] += y
		_average_normals[2] += z

	return [x / float(len(_average_normals)) for x in _average_normals]


def average_vertex_normals(vertices: List[str]):
	"""
	Returns the averaged normals of the given list of vertices.

	:param List[str] vertices: list of vertex components.
	:return: averaged normals.
	:rtype: List[float, float, float]
	"""

	normals = cmds.polyNormalPerVertex(vertices, query=True, xyz=True)
	normals = list(zip(*(iter(normals),) * 3))

	return average_normals(normals)


def average_face_normals(faces: List[str]):
	"""
	Returns the averaged normals of the given list of faces.

	:param List[str] faces: list of face components.
	:return: averaged normals.
	:rtype: List[float, float, float]
	"""

	normals = face_normals(faces)

	return average_normals(normals)


def face_normals(faces: List[str]) -> List[List[float, float, float], ...]:
	"""
	Returns a list of face normals from given list of faces.

	:param List[str] faces: list of faces.
	:return: list of face normals.
	:rtype: List[List[float, float, float], ...]
	"""

	_face_normals = []
	for face_normal in cmds.polyInfo(faces, faceNormals=True):
		_face_normal = face_normal.split()
		del _face_normal[0:2]
		_face_normals.append([float(x) for x in _face_normal])

	return _face_normals


def center_of_multiple_nodes(node_names: List[str]) -> List[float, float, float]:
	"""
	Returns the average center of all given node/component names based on bounding boxes.

	:param List[str] node_names: list of nodes or flattened components.
	:return: center of the pivot in XYZ world coordinates.
	:rtype: List[float, float, float]
	..warning:: face/edge selection is not accurate, use match_center_cluster instead.
	"""

	flatten_node_names = cmds.ls(node_names, flatten=True)
	count = len(flatten_node_names)
	sums = [0, 0, 0]
	for item in flatten_node_names:
		pos = cmds.xform(item, query=True, translation=True, worldSpace=True)
		sums[0] += pos[0]
		sums[1] += pos[1]
		sums[2] += pos[2]

	return [sums[0] / count, sums[1] / count, sums[2] / count]


def create_group_orient_from_components(
		components, aim_vector: Iterable[float, float, float] = (0.0, 1.0, 0.0),
		local_up: Iterable[float, float, float] = (0.0, 0.0, -1.0),
		world_up: Iterable[float, float, float] = (0.0, 1.0, 0.0)) -> str:
	"""
	Creates a group oriented to the average vector of the given vertex/edge/face components.

	:param List[str] components: list of component names to orient to (vertices, edges or faces).
	:param Iterable[float, float, float] aim_vector:
	:param Iterable[float, float, float] local_up:
	:param Iterable[float, float, float] world_up:
	:return: the group name oriented to given components.
	:rtype: str
	"""

	selection_type = selection.components_type(components)

	if selection_type == 'edges':
		cmds.select(components, replace=True)
		components = selection.convert_selection('vertices')
		selection_type = 'vertices'
	if selection_type == 'vertices':
		return create_group_orient_from_vertices(components, aim_vector=aim_vector, local_up=local_up, world_up=world_up)
	elif selection_type == 'faces':
		return create_group_orient_from_faces(components, aim_vector=aim_vector, local_up=local_up, world_up=world_up)


def create_group_orient_from_vertices(
		vertices, aim_vector: Iterable[float, float, float] = (0.0, 1.0, 0.0),
		local_up: Iterable[float, float, float] = (0.0, 0.0, -1.0),
		world_up: Iterable[float, float, float] = (0.0, 1.0, 0.0)) -> str:
	"""
	Creates a group oriented to the average vector of the given vertex/edge/face components.

	:param List[str] vertices: list of vertex names to orient to.
	:param Iterable[float, float, float] aim_vector:
	:param Iterable[float, float, float] local_up:
	:param Iterable[float, float, float] world_up:
	:return: the group name oriented to given components.
	:rtype: str
	"""

	_average_normals = average_vertex_normals(vertices)
	relative_node_name = vertices[0].split('.')[0]

	return create_group_from_vector(
		_average_normals, aim_vector=aim_vector, local_up=local_up, world_up=world_up,
		relative_node_name=relative_node_name)


def create_group_orient_from_faces(
		faces, aim_vector: Iterable[float, float, float] = (0.0, 1.0, 0.0),
		local_up: Iterable[float, float, float] = (0.0, 0.0, -1.0),
		world_up: Iterable[float, float, float] = (0.0, 1.0, 0.0)) -> str:
	"""
	Creates a group oriented to the average vector of the given vertex/edge/face components.

	:param List[str] faces: list of face names to orient to.
	:param Iterable[float, float, float] aim_vector:
	:param Iterable[float, float, float] local_up:
	:param Iterable[float, float, float] world_up:
	:return: the group name oriented to given components.
	:rtype: str
	"""

	_average_normals = average_face_normals(faces)
	relative_node_name = faces[0].split('.')[0]

	return create_group_from_vector(
		_average_normals, aim_vector=aim_vector, local_up=local_up, world_up=world_up,
		relative_node_name=relative_node_name)


def create_group_from_vector(
		vector: List[float, float, float], aim_vector: Iterable[float, float, float] = (0.0, 1.0, 0.0),
		local_up: Iterable[float, float, float] = (0.0, 0.0, -1.0),
		world_up: Iterable[float, float, float] = (0.0, 1.0, 0.0), relative_node_name: str = '') -> str:
	"""
	Creates a group oriented to the average vector of the given vertex/edge/face components.

	:param List[float, float, float] vector: vector direction composed by three floats.
	:param Iterable[float, float, float] aim_vector: direction to aim the group.
	:param Iterable[float, float, float] local_up: direction to aim the group up.
	:param Iterable[float, float, float] world_up: world up of the aim.
	:param str relative_node_name: optional node name to take into consideration the relative rotation of.
	:return: the group name oriented to given components.
	:rtype: str
	"""

	aim_obj = cmds.group(empty=True)
	aim_group = cmds.group(empty=True)

	if relative_node_name:
		cmds.parent(str(aim_obj), relative_node_name)
		cmds.parent(str(aim_group), relative_node_name)
		attributes.reset_transform_attributes(str(aim_obj))
		attributes.reset_transform_attributes(str(aim_group))

	cmds.setAttr(f'{aim_group}.translate', vector[0], vector[1], vector[2], type='float3')

	if relative_node_name:
		cmds.delete(cmds.aimConstraint(
			aim_group, aim_obj, aimVector=aim_vector, upVector=local_up, worldUpVector=world_up,
			worldUpObject=relative_node_name, worldUpType='objectrotation'))
	else:
		cmds.delete(cmds.aimConstraint(
			aim_group, aim_obj, aimVector=aim_vector, upVector=local_up, worldUpVector=world_up))
	cmds.delete(aim_group)

	return aim_obj


def match_center_cluster(node_to_center: str, match_to: List[str]):
	"""
	Matches the given object to the center of the given nodes by creating a cluster and then deleting if after moving
	the node to center to its center.

	:param str node_to_center: object to match.
	:param Lists[str] match_to: list of nodes or components to match to their center.
	"""

	cmds.select(match_to, replace=True)
	cluster = cmds.cluster(name='temp_pivot_XX_cluster')[1]
	cmds.matchTransform(node_to_center, cluster, position=True, rotation=True, scale=False)
	cmds.delete(cluster)


def match_to_center_nodes_components(
		node_to_center: str, match_to: List[str], set_object_mode: bool = True, orient_to_components: bool = True,
		aim_vector: Iterable[float, float, float] = (0.0, 1.0, 0.0),
		local_up: Iterable[float, float, float] = (0.0, 0.0, -1.0),
		world_up: Iterable[float, float, float] = (0.0, 1.0, 0.0)) -> bool:
	"""
	Takes given object and:
		1. If no valid matching objects then nothing happens.
		2. If one object to match is given, the rotation and translation will be matched.
		3. If multiple match objects are given, the object will be centered to all DAG objects.
		4. If match objects are components, object will be centered using clusters and using the average normal to
			orient it.

	:param str node_to_center: object to match.
	:param Lists[str] match_to: list of nodes or components to match to their center.
	:param bool set_object_mode:
	:param orient_to_components: whether to return to object mode if component mode is active.
	:param Iterable[float, float, float] aim_vector: optional aim vector.
	:param Iterable[float, float, float] local_up: optional up vector.
	:param Iterable[float, float, float] world_up: opptional world up vector.
	:return: True if match is performed; False otherwise.
	:rtype: bool
	"""

	if not match_to:
		return False

	selection_type = selection.selection_type(match_to)
	if not selection_type or selection_type == 'uv':
		return False

	dag_objs = cmds.ls(match_to, dag=True)
	if not dag_objs and selection_type == 'object':
		return False

	if selection_type == 'object':
		if len(match_to) == 1:
			cmds.matchTransform(([node_to_center, match_to[0]]), position=True, rotation=True, scale=True, piv=False)
			return True
		center_pos = center_of_multiple_nodes(match_to)
		cmds.move(center_pos[0], center_pos[1], center_pos[2], node_to_center, absolute=True)
		return True

	match_center_cluster(node_to_center, match_to)

	if orient_to_components:
		orient_group = create_group_orient_from_components(
			match_to, aim_vector=aim_vector, local_up=local_up, world_up=world_up)
		cmds.matchTransform(([node_to_center, orient_group]), position=False, rotation=True, scale=False, piv=False)
		cmds.delete(orient_group)

	if set_object_mode and cmds.selectMode(query=True, component=True):
		mel.eval('SelectTool')
		cmds.selectMode(object=True)
		cmds.select(node_to_center, replace=True)

	return True
