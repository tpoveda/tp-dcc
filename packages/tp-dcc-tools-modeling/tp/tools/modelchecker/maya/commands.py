from typing import List

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya


def _get_meshes(nodes: List[str]) -> OpenMaya.MSelectionList:
	"""
	Function that returns a selection list with the given nodes that have a mesh.

	:param List[str] nodes: list of node names.
	:return: selection with meshes.
	:rtype: OpenMaya.MSelectionList
	"""

	selected_meshes = OpenMaya.MSelectionList()
	for node in nodes:
		shapes = cmds.listRelatives(node, shapes=True, type='mesh')
		if shapes:
			selected_meshes.add(node)

	return selected_meshes


def trailing_numbers(nodes: List[str]) -> List[str]:
	"""
	Returns list of node names that end with a number.

	:param List[str nodes: list of node names to check.
	:return: list of node names that end with a number.
	:rtype: List[str]
	"""

	found_trailing_numbers = []
	for node in nodes:
		if node[-1].isdigit():
			found_trailing_numbers.append(node)

	return found_trailing_numbers


def duplicated_names(nodes: List[str]) -> List[str]:
	"""
	Returns list of duplicated node names.

	:param List[str] nodes: list of node names to check.
	:return: list of duplicated node names.
	:rtype: List[str]
	"""

	found_duplicated_names = []
	for node in nodes:
		if '|' in node:
			found_duplicated_names.append(node)

	return found_duplicated_names


def shape_names(nodes: List[str]) -> List[str]:
	"""
	Returns list of node names which shapes have an invalid name.

	:param List[str] nodes: list of node names to check.
	:return: list of nodes with invalid shape names.
	:rtype: List[str]
	"""

	invalid_shape_names = []
	for node in nodes:
		new = node.split('|')
		shapes = cmds.listRelatives(node, shapes=True)
		if shapes:
			shape_name = f'{new[-1]}Shape'
			if shapes[0] != shape_name:
				invalid_shape_names.append(node)

	return invalid_shape_names


def namespaces(nodes: List[str]) -> List[str]:
	"""
	Returns a list of nodes that are contained within a namespace.

	:param List[str] nodes: list of node names to check.
	:return: list of nodes that have a namespace.
	:rtype: List[str]
	"""

	found_namespaces = []
	for node in nodes:
		if ':' in node:
			found_namespaces.append(node)

	return found_namespaces


def layers(nodes: List[str]) -> List[str]:
	"""
	Returns a list of nodes that are contained within display layers.

	:param List[str] nodes: list of node names to check.
	:return: list of nodes contained within display layers.
	:rtype: List[str]
	"""

	nodes_within_layers = []

	for node in nodes:
		found_layer = cmds.listConnections(node, type='displayLayer')
		if found_layer:
			nodes_within_layers.append(node)

	return nodes_within_layers


def history(nodes: List[str]) -> List[str]:
	"""
	Returns a list of nodes whose history is not cleanup.

	:param List[str] nodes: list of node names to check.
	:return: list of nodes with history.
	:rtype: List[str]
	"""

	nodes_with_history = []

	for node in nodes:
		shapes = cmds.listRelatives(node, shapes=True, fullPath=True)
		if shapes and cmds.nodeType(shapes[0]) == 'mesh':
			history_size = len(cmds.listHistory(shapes))
			if history_size > 1:
				nodes_with_history.append(node)

	return nodes_with_history


def shaders(nodes: List[str]) -> List[str]:
	"""
	Returns list of nodes with non-default shaders applied to them.

	:param List[str] nodes: list of node names to check.
	:return: list of nodes with non-default shaders applied to them.
	:rtype: List[str]
	"""

	nodes_with_shaders = []

	for node in nodes:
		shapes = cmds.listRelatives(node, shapes=True, fullPath=True)
		if shapes and cmds.nodeType(shapes[0]) == 'mesh':
			shading_groups = cmds.listConnections(shapes, type='shadingEngine')
			if shading_groups[0] != 'initialShadingGroup':
				nodes_with_shaders.append(node)

	return nodes_with_shaders


def unfrozen_transforms(nodes: List[str]) -> List[str]:
	"""
	Returns list of nodes whose transforms are not frozen.

	:param List[str] nodes: list of node names to check.
	:return: list of unfrozen transform nodes.
	:rtype: List[str]
	"""

	unfrozen_nodes = []
	for node in nodes:
		translation = cmds.xform(node, query=True, worldSpace=True, translation=True)
		rotation = cmds.xform(node, query=True, worldSpace=True, rotation=True)
		scale = cmds.xform(node, query=True, worldSpace=True, scale=True)
		if translation != [0.0, 0.0, 0.0] or rotation != [0.0, 0.0, 0.0] or scale != [1.0, 1.0, 1.0]:
			unfrozen_nodes.append(node)

	return unfrozen_nodes


def uncentered_pivots(nodes: List[str]) -> List[str]:
	"""
	Returns list of nodes whose pivots are not centered.

	:param List[str] nodes: list of node names to check.
	:return: list of non-centered pivot transform nodes.
	:rtype: List[str]
	"""

	non_centered_pivots = []
	for node in nodes:
		if cmds.xform(node, query=True, worldSpace=True, rp=True) != [0.0 ,0.0, 0.0]:
			non_centered_pivots.append(node)

	return non_centered_pivots


def parent_geometry(nodes: List[str]) -> List[str]:
	"""
	Returns list of nodes whose parents contain mesh shapes.

	:param List[str] nodes: list of node names to check.
	:return: list of nodes whose parents contain mesh shapes.
	:rtype: List[str]
	"""

	parents_with_geometry = []

	for node in nodes:
		parents = cmds.listRelatives(node, parent=True, fullPath=True)
		if parents:
			for parent in parents:
				children = cmds.listRelatives(parent, fullPath=True)
				for child in children:
					if cmds.nodeType(child) == 'mesh':
						parents_with_geometry.append(node)

	return parents_with_geometry


def empty_groups(nodes: List[str]) -> List[str]:
	"""
	Returns list of transform nodes that have no children.

	:param List[str] nodes: list of node names to check.
	:return: empty group nodes.
	:rtype: List[str]
	"""

	found_empty_groups = []
	for node in nodes:
		children = cmds.listRelatives(node, allDescendents=True)
		if not children:
			found_empty_groups.append(node)

	return found_empty_groups


def triangles(nodes: List[str]) -> List[str]:
	"""
	Returns a list of face component names that are part of triangles.

	:param List[str] nodes: list of node names to check.
	:return: face component names.
	:rtype: List[str]
	"""

	face_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return face_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		face_iterator = OpenMaya.MItMeshPolygon(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not face_iterator.isDone():
			num_of_edges = face_iterator.getEdges()
			if len(num_of_edges) == 3:
				component_name = f'{object_name}.f[{face_iterator.index()}]'
				face_components.append(component_name)
			face_iterator.next()
		list_iterator.next()

	return face_components


def ngons(nodes: List[str]) -> List[str]:
	"""
	Returns a list of face component names that are part of ngons.

	:param List[str] nodes: list of node names to check.
	:return: face component names.
	:rtype: List[str]
	"""

	face_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return face_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		face_iterator = OpenMaya.MItMeshPolygon(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not face_iterator.isDone():
			num_of_edges = face_iterator.getEdges()
			if len(num_of_edges) > 4:
				component_name = f'{object_name}.f[{face_iterator.index()}]'
				face_components.append(component_name)
			face_iterator.next()
		list_iterator.next()

	return face_components


def open_edges(nodes: List[str]) -> List[str]:
	"""
	Returns a list of edge component names that are part of open edges.

	:param List[str] nodes: list of node names to check.
	:return: edge component names.
	:rtype: List[str]
	"""

	edge_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return edge_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		edge_iterator = OpenMaya.MItMeshEdge(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not edge_iterator.isDone():
			if edge_iterator.numConnectedFaces() > 2:
				component_name = f'{object_name}.e[{edge_iterator.index()}]'
				edge_components.append(component_name)
			edge_iterator.next()
		list_iterator.next()

	return edge_components


def poles(nodes: List[str]) -> List[str]:
	"""
	Returns a list of vertex component names that are part of a pole.

	:param List[str] nodes: list of node names to check.
	:return: vertex component names.
	:rtype: List[str]
	"""

	vertex_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return vertex_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		vertex_iterator = OpenMaya.MItMeshVertex(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not vertex_iterator.isDone():
			if vertex_iterator.numConnectedEdges() > 5:
				component_name = f'{object_name}.vtx[{vertex_iterator.index()}]'
				vertex_components.append(component_name)
			vertex_iterator.next()
		list_iterator.next()

	return vertex_components


def hard_edges(nodes: List[str]) -> List[str]:
	"""
	Returns a list of edge component names that are hard edges.

	:param List[str] nodes: list of node names to check.
	:return: edge component names.
	:rtype: List[str]
	"""

	edge_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return edge_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		edge_iterator = OpenMaya.MItMeshEdge(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not edge_iterator.isDone():
			if not edge_iterator.isSmooth and not edge_iterator.onBoundary():
				component_name = f'{object_name}.e[{edge_iterator.index()}]'
				edge_components.append(component_name)
			edge_iterator.next()
		list_iterator.next()

	return edge_components


def lamina(nodes: List[str]) -> List[str]:
	"""
	Returns a list of lamina face component names.

	:param List[str] nodes: list of node names to check.
	:return: face component names.
	:rtype: List[str]
	"""

	face_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return face_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		face_iterator = OpenMaya.MItMeshPolygon(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not face_iterator.isDone():
			lamina_faces = face_iterator.isLamina()
			if lamina_faces:
				component_name = f'{object_name}.f[{face_iterator.index()}]'
				face_components.append(component_name)
			face_iterator.next()
		list_iterator.next()

	return face_components


def zero_area_faces(nodes: List[str]) -> List[str]:
	"""
	Returns a list of zero area face component names.

	:param List[str] nodes: list of node names to check.
	:return: face component names.
	:rtype: List[str]
	"""

	face_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return face_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		face_iterator = OpenMaya.MItMeshPolygon(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not face_iterator.isDone():
			if face_iterator.getArea() <= 0.00000001:
				component_name = f'{object_name}.f[{face_iterator.index()}]'
				face_components.append(component_name)
			face_iterator.next()
		list_iterator.next()

	return face_components


def zero_length_edges(nodes: List[str]) -> List[str]:
	"""
	Returns a list of edge component names whose length is 0.

	:param List[str] nodes: list of node names to check.
	:return: edge component names.
	:rtype: List[str]
	"""

	edge_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return edge_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		edge_iterator = OpenMaya.MItMeshEdge(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not edge_iterator.isDone():
			if edge_iterator.length() <= 0.00000001:
				component_name = f'{object_name}.e[{edge_iterator.index()}]'
				edge_components.append(component_name)
			edge_iterator.next()
		list_iterator.next()

	return edge_components


def non_manifold_edges(nodes: List[str]) -> List[str]:
	"""
	Returns a list of manifold edge component names.

	:param List[str] nodes: list of node names to check.
	:return: edge component names.
	:rtype: List[str]
	"""

	edge_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return edge_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		edge_iterator = OpenMaya.MItMeshEdge(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not edge_iterator.isDone():
			if edge_iterator.numConnectedFaces() < 2:
				component_name = f'{object_name}.e[{edge_iterator.index()}]'
				edge_components.append(component_name)
			edge_iterator.next()
		list_iterator.next()

	return edge_components


def star_like(nodes: List[str]) -> List[str]:
	"""
	Returns a list of star-like face component names.

	:param List[str] nodes: list of node names to check.
	:return: face component names.
	:rtype: List[str]
	"""

	face_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return face_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		face_iterator = OpenMaya.MItMeshPolygon(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not face_iterator.isDone():
			if not face_iterator.isStarlike():
				component_name = f'{object_name}.f[{face_iterator.index()}]'
				face_components.append(component_name)
			face_iterator.next()
		list_iterator.next()

	return face_components


def self_penetrating_uvs(nodes: List[str]) -> List[str]:
	"""
	Returns a list nodes whose UVs are penetrating.

	:param List[str] nodes: list of node names to check.
	:return: self penetrating UVs nodes.
	:rtype: List[str]
	"""

	self_penetrating_nodes = []
	for node in nodes:
		shapes = cmds.listRelatives(node, shapes=True, fullPath=True)
		convert_to_faces = cmds.ls(cmds.polyListComponentConversion(shapes, tf=True), flatten=True)
		overlapping = cmds.polyUVOverlap(convert_to_faces, oc=True)
		if overlapping:
			for _node in overlapping:
				self_penetrating_nodes.append(_node)

	return self_penetrating_nodes


def missing_uvs(nodes: List[str]) -> List[str]:
	"""
	Returns a list of missing UVs face component names.

	:param List[str] nodes: list of node names to check.
	:return: face component names.
	:rtype: List[str]
	"""

	face_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return face_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		face_iterator = OpenMaya.MItMeshPolygon(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not face_iterator.isDone():
			if not face_iterator.hasUVs():
				component_name = f'{object_name}.f[{face_iterator.index()}]'
				face_components.append(component_name)
			face_iterator.next()
		list_iterator.next()

	return face_components


def uv_range(nodes: List[str]) -> List[str]:
	"""
	Returns a list of map components names whose UV range is not valid.

	:param List[str] nodes: list of node names to check.
	:return: map component names.
	:rtype: List[str]
	"""

	map_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return map_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	mesh = OpenMaya.MFnMesh(list_iterator.getDagPath())
	object_name = list_iterator.getDagPath().getPath()
	us, vs = mesh.getUVs()
	for i in range(len(us)):
		if us[i] < 0 or us[i] > 10 or vs[i] < 0:
			component_name = f'{object_name}.map[{i}]'
			map_components.append(component_name)

	return map_components


def cross_border(nodes: List[str]) -> List[str]:
	"""
	Returns a list of cros border face component names.

	:param List[str] nodes: list of node names to check.
	:return: face component names.
	:rtype: List[str]
	"""

	face_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return face_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	while not list_iterator.isDone():
		face_iterator = OpenMaya.MItMeshPolygon(list_iterator.getDagPath())
		object_name = list_iterator.getDagPath().getPath()
		while not face_iterator.isDone():
			u, v = set(), set()
			try:
				uvs = face_iterator.getUVs()
				us, vs = uvs[0], uvs[1]
				for i in range(len(us)):
					u.add(int(us[i]) if us[i] > 0 else int(us[i]) - 1)
					v.add(int(vs[i]) if vs[i] > 0 else int(vs[i]) - 1)
				if len(u) > 1 or len(v) > 1:
					component_name = f'{object_name}.f[{face_iterator.index()}]'
					face_components.append(component_name)
				face_iterator.next()
			except:
				cmds.warning(f'Face {face_iterator.index()} has no UVs!')
				face_iterator.next()
		list_iterator.next()

	return face_components


def on_border(nodes: List[str]) -> List[str]:
	"""
	Returns a list of map components names whose UVs are near the border.

	:param List[str] nodes: list of node names to check.
	:return: map component names.
	:rtype: List[str]
	"""

	map_components = []
	selection_list = _get_meshes(nodes)
	if selection_list.isEmpty():
		return map_components
	list_iterator = OpenMaya.MItSelectionList(selection_list)
	mesh = OpenMaya.MFnMesh(list_iterator.getDagPath())
	object_name = list_iterator.getDagPath().getPath()
	us, vs = mesh.getUVs()
	for i in range(len(us)):
		if abs(int(us[i]) - us[i]) < 0.00001 or abs(int(vs[i]) - vs[i]) < 0.00001:
			component_name = f'{object_name}.map[{i}]'
			map_components.append(component_name)

	return map_components
