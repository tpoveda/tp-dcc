from __future__ import annotations

import os
from typing import List, Iterator

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.maya.cmds import node


def root_node() -> OpenMaya.MFnDependencyNode | None:
	"""
	Returns the root Maya object.

	:return: root Maya object.
	:rtype: OpenMaya.MObject or None
	"""

	for n in node.get_objects_of_mtype_iterator(object_type=OpenMaya.MFn.kWorld):
		return n

	return None


def all_scene_nodes() -> List[OpenMaya.MFnDependencyNode]:
	"""
	Returns all nodes in the scene.

	:return: list of scene nodes.
	:rtype: List[OpenMaya.MFnDependencyNode]
	"""

	obj_types = (
		OpenMaya.MFn.kDagNode, OpenMaya.MFn.kCharacter, OpenMaya.MFn.kDependencyNode)
	return node.get_objects_of_mtype_iterator(obj_types)


def iterate_references() -> Iterator[OpenMaya.MFnReference]:
	"""
	Generator function that returns a MObject for each valid reference node.

	:return: iterated references.
	:rtype: Iterator[OpenMaya.MFnReference]
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


def scene_references() -> List[str]:
	"""
	Returns a list of all scene references paths within current scene.

	:return: list of scene reference paths.
	:rtype: List[str]
	"""

	paths = set()

	for ref in iterate_references():
		ref_path = ref.fileName(True, False, False).replace('/', os.path.sep)
		if ref_path:
			paths.add(ref_path)

	return list(paths)


def scene_textures() -> List[str]:
	"""
	Find scene texture dependencies of the current scene that are not referenced.

	:return: list of texture paths.
	:rtype: List[str]
	"""

	paths = set()
	for f in cmds.ls(long=True, type='file'):
		if cmds.referenceQuery(f, isNodeReferenced=True):
			continue

		texture_path = cmds.getAttr(os.path.normpath('.'.join([f, 'fileTextureName'])))
		if texture_path:
			paths.add(texture_path)

	return list(paths)


def find_additional_scene_dependencies(references: bool = True, textures: bool = True) -> List[str]:
	"""
	Returns additional dependencies from the scene by looking at the file references and texture paths.

	:param bool references: whether to return scene references.
	:param bool textures: whether to return textures.
	:return: scene dependencies paths.
	:rtype: List[str]
	"""

	dependency_paths = set()
	if references:
		dependency_paths.union(scene_references())
	if textures:
		dependency_paths.union(scene_textures())

	return list(dependency_paths)


def iterate_selected_nodes(filtered_type: OpenMaya.MFn.kObjectTypeFilter | None = None) -> Iterator[OpenMaya.MObject]:
	"""
	Generator function that iterates over all current selected nodes within Maya scene.

	:param OpenMaya.MFn.kObjectTypeFilter filtered_type: selected nodes to filter.
	:return: iterated selected nodes.
	:rtype: Iterator[OpenMaya.MObject]
	"""

	current_selection = OpenMaya.MGlobal.getActiveSelectionList()
	for i in range(current_selection.length()):
		found_node = current_selection.getDependNode(i)
		if found_node.apiType() == filtered_type or not filtered_type:
			yield found_node


def selected_nodes(filtered_type: OpenMaya.MFn.kObjectTypeFilter | None = None) -> Iterator[OpenMaya.MObject]:
	"""
	Returns a list of all currently selected nodes.

	:param OpenMaya.MFn.kObjectTypeFilter filtered_type: selected nodes to filter.
	:return: list of selected nodes.
	:rtype: List[OpenMaya.MObject]
	"""

	return list(iterate_selected_nodes(filtered_type=filtered_type))


def is_centimeters() -> bool:
	"""
	Returns whether current scene is in centimeters.

	:return: True if current scene is in centimeters; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kCentimeters


def is_feet() -> bool:
	"""
	Returns whether current scene is in feet.

	:return: True if current scene is in feet; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kFeet


def is_inches() -> bool:
	"""
	Returns whether current scene is in inches.

	:return: True if current scene is in inches; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kInches


def is_kilometers() -> bool:
	"""
	Returns whether current scene is in kilometers.

	:return: True if current scene is in kilometers; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kKilometers


def is_last() -> bool:
	"""
	Returns whether current scene is in last.

	:return: True if current scene is in last; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kLast


def is_meters() -> bool:
	"""
	Returns whether current scene is in meters.

	:return: True if current scene is in meters; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kMeters


def is_miles() -> bool:
	"""
	Returns whether current scene is in miles.

	:return: True if current scene is in miles; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kMiles


def is_millimeters() -> bool:
	"""
	Returns whether current scene is in millimeters.

	:return: True if current scene is in millimeters; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kMillimeters


def is_yards() -> bool:
	"""
	Returns whether current scene is in yards.

	:return: True if current scene is in yards; False otherwise.
	:rtype: bool
	"""

	return OpenMaya.MDistance.uiUnit() == OpenMaya.MDistance.kYards
