#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utilities functions and classes related with Maya API MDagPaths
"""

import re
from typing import Iterator

import maya.api.OpenMaya as OpenMaya

from tp.core import log
from tp.common.python import helpers

logger = log.tpLogger

__name_regex__ = re.compile(r'^(?:\:?([a-zA-Z0-9_]))+$')
__uuid_regex__ = re.compile(r'^[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}$')
__path_regex__ = re.compile(r'^(.*\|)([^\|]*)$')


def mobject_by_name(name: str) -> OpenMaya.MObject | None:
	"""
	Returns an MObject from the given node name.

	:param str name: name of the node to get.
	:return: Maya object instance from given name.
	:rtype: OpenMaya.MObject or None
	"""

	strings = name.split(':')
	has_namespace = len(strings) >= 2

	# Wildcards do not account for the root namespace!
	name = strings[-1]
	namespaces = (':'.join(strings[:-1]),) if has_namespace else ('', '*')

	selection = OpenMaya.MSelectionList()
	for namespace in namespaces:
		try:
			selection.add(f'{namespace}:{name}')
		except RuntimeError:
			continue

	# Evaluate selection list.
	selection_count = selection.length()
	if selection_count > 0:
		return selection.getDependNode(0)
	else:

		logger.debug(f'Cannot locate node from name: "{name}"')
		return OpenMaya.MObject.kNullObj


def mobject_by_path(path: str) -> OpenMaya.MObject | None:
	"""
	Returns an MObject from the given node path.

	:param str path: node path.
	:return: Maya object instance from given path.
	:rtype: OpenMaya.MObject or None
	"""

	# Check if a namespace was supplied
	# If not, then use a wildcard to search recursively!
	hierarchy = path.split('|')
	leaf_name = hierarchy[-1]
	strings = leaf_name.split(':')
	has_namespace = len(strings) >= 2
	name = strings[-1]
	namespaces = (':'.join(strings[:-1]),) if has_namespace else ('', '*')

	selection = OpenMaya.MSelectionList()
	for namespace in namespaces:
		try:
			selection.add(f'{namespace}:{name}')
		except RuntimeError:
			continue

	# Evaluate selection list
	selection_count = selection.length()
	if selection_count == 0:
		logger.debug(f'Cannot locate node from path: "{path}"')
		return OpenMaya.MObject.kNullObj
	elif selection_count == 1:
		return selection.getDependNode(0)
	else:
		parent_path = '|'.join(hierarchy[:-1])
		for i in range(selection_count):
			node = selection.getDependNode(i)
			node_path = node_name(node, include_path=True, include_namespace=has_namespace)
			if node_path.startswith(parent_path):
				return node
			else:
				continue
		logger.debug(f'Cannot locate node from path: "{path}"')
		return OpenMaya.MObject.kNullObj


def mobject_by_string(string: str) -> OpenMaya.MObject | None:
	"""
	Returns an MObject from given string.

	:param str string: string to check.
	:return: Maya object instance from given string.
	:rtype: OpenMaya.MObject or None
	:raises TypeError: if given strig is not valid.
	"""

	# Check if string contains an attribute.
	is_name = __name_regex__.match(string)
	is_path = __path_regex__.match(string)
	is_uuid = __uuid_regex__.match(string)

	if is_name:
		return mobject_by_name(string)
	elif is_path:
		return mobject_by_path(string)
	elif is_uuid:
		return mobject_by_uuid(string)
	else:
		raise TypeError(f'getMObjectByName() expects a valid string ("{string}" given)!')


def mobject_by_uuid(uuid: str | OpenMaya.MUuid) -> OpenMaya.MObject | list[OpenMaya.MObject] | None:
	"""
	Returns an MObject from the given UUID.
	If multiples nodes are found with the same UUID, a list will be returned.

	:param OpenMaya.MUuid uuid: UUID to get object for.
	:return: Maya object instance from given uuid.
	:rtype: OpenMaya.MObject or list[OpenMaya.MObject] or None
	"""

	nodes = list(iterate_nodes_by_uuid(uuid))
	if not nodes:
		return None

	if len(nodes) == 1:
		return nodes[0]

	return nodes


def mobject_by_handle(handle: OpenMaya.MObjectHandle) -> OpenMaya.MObject:
	"""
	Returns an MObject from given MObjectHandle.

	:param OpenMaya.MObjectHandle handle: Maya object handle.
	:return: Maya object instance from given handle.
	:rtype: OpenMaya.MObject
	"""

	return handle.object()


def mobject_by_dag_path(dag_path: OpenMaya.MDagPath) -> OpenMaya.MObject:
	"""
	Returns an MObject from given MDagPath.

	:param OpenMaya.MDagPath dag_path: DAG path instance.
	:return: Maya object instance from given dag path.
	:rtype: OpenMaya.MObject
	"""

	return dag_path.node()


__get_mobject__ = {
	'str': mobject_by_string,
	'MUuid': mobject_by_uuid,
	'MObjectHandle': mobject_by_handle,
	'MDagPath': mobject_by_dag_path
}


def mobject(
		value: str | OpenMaya.MObject | OpenMaya.MObjectHandle | OpenMaya.MDagPath) -> OpenMaya.MObject | None:
	"""
	Returns an MObject for the input scene object.

	:param str or OpenMaya.MObject or OpenMaya.MObjectHandle or OpenMaya.MDagPath value: Maya node to get MObject for.
	:return: Maya object instance from given name.
	:rtype: OpenMaya.MObject or None
	:raises exceptions.MissingObjectByNameError: if no node with given name exists.
	:raises TypeError: if given node is not a valid Maya node.
	"""

	if isinstance(value, OpenMaya.MObject):
		return value

	type_name = type(value).__name__
	func = __get_mobject__.get(type_name, None)
	if func is not None:
		return func(value)
	else:
		raise TypeError(f'mobject() expects {tuple(__get_mobject__.keys())} ({type(value).__name__} given)')


def node_name(
		node: str | OpenMaya.MObject | OpenMaya.MDagPath, include_path: bool = False,
		include_namespace: bool = False) -> str:
	"""
	Returns the name of the given node.

	:param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get name from.
	:param bool include_path: whether to include node full path.
	:param bool include_namespace: whether to include node namespace.
	:return: node name.
	:rtype: str
	"""

	node = mobject(node)
	if not node.hasFn(OpenMaya.MFn.kDependencyNode):
		return ''

	if include_path:
		return '|'.join([node_name(ancestor, include_namespace=include_namespace) for ancestor in trace_hierarchy(node)])
	elif include_namespace:
		return f'{node_namespace(node)}:{node_name(node)}'
	else:
		return strip_all(OpenMaya.MFnDependencyNode(node).name())


def node_namespace(node: str | OpenMaya.MObject | OpenMaya.MDagPath) -> str:
	"""
	Returns the namespace of the given node.

	:param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get namespace from.
	:return: node namespace.
	:rtype: str
	"""

	return OpenMaya.MFnDependencyNode(mobject(node)).namespace


def iterate_nodes_by_uuid(*uuids: str | OpenMaya.MUuid | tuple[str | OpenMaya.MUuid]) -> Iterator[OpenMaya.MObject]:
	"""
	Generator function that yields dependency nodes with the given UUID.

	:param tuple[str or OpenMaya.MUuid] uuids: uuids.
	:return: iterated nodes.
	:rtype: Iterator[OpenMaya.MObject]
	"""

	for uuid in uuids:
		uuid = OpenMaya.MUuid(uuid) if isinstance(uuid, str) else uuid
		selection = OpenMaya.MSelectionList()
		selection.add(uuid)
		for i in range(selection.length()):
			yield selection.getDependNode(i)


def dag_path(value: str | OpenMaya.MObject | OpenMaya.MObjectHandle | OpenMaya.MDagPath) -> OpenMaya.MDagPath:
	"""
	Returns the MDagPath for the given value.

	:param str or OpenMaya.MObject or OpenMaya.MObjectHandle or OpenMaya.MDagPath value: node to get dag path of.
	:return: dag path instance.
	:rtype: OpenMaya.MDagPath
	..note:: This method expects the value to be derived from a dag node in order to work!
	"""

	return value if isinstance(value, OpenMaya.MDagPath) else OpenMaya.MDagPath.getAPathTo(mobject(value))


def parent(node: OpenMaya.MObject) -> OpenMaya.MObject | None:
	"""
	Returns the parent of the given node.

	:param OpenMaya.MObject node: node to get parent of.
	:return: parent node.
	:rtype: OpenMaya.MObject or None
	"""

	node_dag_path = dag_path(node)
	fn_dag_node = OpenMaya.MFnDagNode(node_dag_path)
	parent_count = fn_dag_node.parentCount()
	if parent_count == 0:
		return OpenMaya.MObject.kNullObj

	# Make sure parent is not world.
	found_parent = fn_dag_node.parent(0)
	if not found_parent.hasFn(OpenMaya.MFn.kWorld):
		return found_parent

	return OpenMaya.MObject.kNullObj


def iterate_ancestors(
		node: str | OpenMaya.MObject | OpenMaya.MDagPath,
		api_type: int = OpenMaya.MFn.kTransform) -> Iterator[OpenMaya.MObject]:
	"""
	Returns a generator that yields ancestors for the given transform node.

	:param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get namespace of.
	:param int api_type: optional API type to filter ancestors by.
	:return: iterated ancestors.
	:rtype: Iterator[OpenMaya.MObject]
	"""

	ancestor = parent(node)
	while not ancestor.isNull():
		if ancestor.hasFn(api_type):
			yield ancestor
			ancestor = parent(ancestor)
		else:
			break


def trace_hierarchy(node: OpenMaya.MObject) -> Iterator[OpenMaya.MObject]:
	"""
	Returns a generator that yields the nodes leading up to, and including, the given transform node.

	:param OpenMaya.MObject node: node to get hierarchy of.
	:return: Iterator[OpenMaya.MObject]
	"""

	yield from reversed(list(iterate_ancestors(node)))
	yield node


def strip_dag_path(name: str) -> str:
	"""
	Remove any separator from the given name.

	:param str name: dag path to strip.
	:return: stripped dag path.
	:rtype: str
	"""

	return name.split('|')[-1]


def strip_namespace(name: str) -> str:
	"""
	Removes any colon characters from the given name.

	:param str name: dag path to remove namespaces from.
	:return: path without namespaces.
	:rtype: str
	"""

	return name.split(':')[-1]


def strip_all(name: str) -> str:
	"""
	Removes any separator and colon characters from given name.
	
	:param str name: dag path to strip. 
	:return: stripped dag path.
	:rtype: str
	"""

	name = strip_dag_path(name)
	name = strip_namespace(name)

	return name


def child_paths(dag_path):
	"""
	Returns all MDagPaths that are child of the given MDagPath.

	:param MDagPath dag_path: DAG path we want to retrieve childs of.
	:return: list of children DAG paths.
	:rtype: list(MDagPath)
	"""

	out_paths = [child_path_at_index(dag_path, i) for i in range(dag_path.childCount())]

	return out_paths


def child_path_at_index(dag_path, index):
	"""
	Returns MDagPath of the child node at given index from given MDagPath.

	:param MDagPath dag_path: DAG path we want to retrieve child at index of.
	:param int index: index of the child we want to retrieve relative to the given DAG path hierarchy.
	:return: child DAG path at given index.
	:rtype: MDagPath
	"""

	existing_child_count = dag_path.childCount()
	if existing_child_count < 1:
		return None
	index = index if index >= 0 else dag_path.childCount() - abs(index)
	copy_path = OpenMaya.MDagPath(dag_path)
	copy_path.push(dag_path.child(index))

	return copy_path


def child_paths_by_fn(dag_path, child_fn):
	"""
	Returns all children paths of the given MDagPath that supports given MFn type.

	:param MDagPath dag_path: DAG path we want to retrieve of.
	:param MFn child_fn: Maya function type returned child need to have.
	:return: list of child DAG paths with the given Maya function type.
	:rtype: list(MDagPath).
	"""

	return [child_path for child_path in child_paths(dag_path) if child_path.hasFn(child_fn)]


def child_transforms(dag_path):
	"""
	Returns all the child transforms of the given MDagPath.

	:param OpenMaya.MDagPath dag_path: DAG path we want to retrieve child transforms of.
	:return: list of all transforms below given path.
	:rtype: list(MDagPath)
	"""

	return child_paths_by_fn(dag_path, OpenMaya.MFn.kTransform)


def iterate_shape_paths(dag_path, filter_types=None):
	"""
	Generator function that returns all the shape DAG paths directly below the given DAG path.

	:param MDagPath dag_path: DAG path to search shapes of.
	:param list(str) filter_types: list of tiler shapes for the shapes to return.
	:return: generator of shape DAG paths.
	:rtype: generator(MDagPath)
	"""

	filter_types = helpers.force_list(filter_types)
	for i in range(dag_path.numberOfShapesDirectlyBelow()):
		shape_dag_path = OpenMaya.MDagPath(dag_path)
		shape_dag_path.extendToShape(i)
		if not filter_types or shape_dag_path.apiType() in filter_types:
			yield shape_dag_path


def shapes_paths(dag_path, filter_types=None):
	"""
	Returns all the given shape DAG paths directly below the given DAG path as a list.

	:param MDagPath dag_path: DAG path to search shapes of.
	:param list(str) filter_types: list of tiler shapes for the shapes to return.
	:return: list of shape DAG paths.
	:rtype: list(MDagPath)
	"""

	return list(iterate_shape_paths(dag_path, filter_types=filter_types))
