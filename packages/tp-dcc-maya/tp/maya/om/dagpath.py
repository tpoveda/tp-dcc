#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utilities functions and classes related with Maya API MDagPaths
"""

import maya.api.OpenMaya as OpenMaya

from tp.common.python import helpers


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
