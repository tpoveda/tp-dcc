import os

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya


def root_node():
	"""
	Returns the root Maya object
	:return:
	"""

	from tp.maya.cmds import node

	for n in node.get_objects_of_mtype_iterator(object_type=OpenMaya.MFn.kWorld):
		return n

	return None


def all_scene_nodes():
	"""
	Returns all nodes in the scene
	:return:
	"""

	from tp.maya.cmds import node

	obj_types = (
		OpenMaya.MFn.kDagNode, OpenMaya.MFn.kCharacter, OpenMaya.MFn.kDependencyNode)
	return node.get_objects_of_mtype_iterator(obj_types)


def iterate_references():
	"""
	Generator function that returns a MObject for each valid reference node
	:return: Generator<OpenMaya.MObject>
	"""

	iterator = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kReference)
	while not iterator.isDone():
		try:
			fn = OpenMaya.MFnReference(iterator.thisNode())
			try:
				if not fn.isLoaded() or fn.isLocked():
					continue
			except RuntimeError:
				continue
			yield fn.object()
		finally:
			iterator.next()


def find_scene_references():
	"""
	Returns a list of all scene references within current scene.

	:return: list of scene references.
	:rtype: list(str)
	"""

	paths = set()

	for ref in iterate_references():
		ref_path = ref.fileName(True, False, False).replace('/', os.path.sep)
		if ref_path:
			paths.add(ref_path)

	return paths


def find_scene_textures():
	"""
	Find scene texture dependencies of the current scene that are not referenced
	:return: set<str>
	"""

	paths = set()
	for f in cmds.ls(long=True, type='file'):
		if cmds.referenceQuery(f, isNodeReferenced=True):
			continue

		texture_path = cmds.getAttr(os.path.normpath('.'.join([f, 'fileTextureName'])))
		if texture_path:
			paths.add(texture_path)

	return paths


def find_additional_scene_dependencies(references=True, textures=True):
	"""
	Returns additional dependencies from the scene by looking at the file references and texture paths.

	:param bool references: whether to return scene references.
	:param bool textures: whether to return textures.
	:return: scene dependnecies paths.
	:rtype: set(str)
	"""

	dependency_paths = set()
	if references:
		dependency_paths.union(find_scene_references())
	if textures:
		dependency_paths.union(find_scene_textures())

	return dependency_paths


def iterate_selected_nodes(filtered_type=None):
	"""
	Generator function that iterates over all current selected nodes within Maya scene.

	:param OpenMaya.MFn.kType filtered_type: selected nodes to filter.
	:return: generator of iterated selected nodes.
	:rtype: generator(OpenMaya.MObject)
	"""

	current_selection = OpenMaya.MGlobal.getActiveSelectionList()
	for i in range(current_selection.length()):
		found_node = current_selection.getDependNode(i)
		if found_node.apiType() == filtered_type or not filtered_type:
			yield found_node


def selected_nodes(filtered_type=None):
	"""
	Returns a list of all currently selected nodes.

	:param OpenMaya.MFn.kType filtered_type: selected nodes to filter.
	:return: list of selected nodes.
	:rtype: list(OpenMaya.MObject)
	"""

	return list(iterate_selected_nodes(filtered_type=filtered_type))
