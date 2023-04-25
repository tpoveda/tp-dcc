#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya Skin Cluster node
"""

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim

from tp.core import command
from tp.common.python import helpers
from tp.maya.om import mesh


def skin_cluster(dag_path=None):
	"""
	Loops through the DAG hierarchy of the given DAG path finding a skin cluster
	:param dag_path: OpenMaya.MDagPath
	:return: (OpenMayaAnim.MFnSkinCluster, str), Skin cluster object and skin cluster node name
	"""

	if not dag_path:
		return None, None

	if not helpers.is_string(dag_path):
		dag_path = dag_path.fullPathName()

	skin_cluster = cmds.ls(cmds.listHistory(dag_path), type='skinCluster')
	if not skin_cluster:
		return None, None

	skin_name = skin_cluster[0]
	selection_list = OpenMaya.MSelectionList(skin_name)

	skin_node = selection_list.getDependNode(0)
	skin_node = OpenMayaAnim.MFnSkinCluster(skin_node)

	return skin_node, skin_name


def skin_weights(skin_cluster, mesh_shape_name):
	"""
	Returns the skin weights of the given skin cluster in the given mesh
	:param skin_cluster:
	:param mesh_shape_name:
	:return:
	"""

	if helpers.is_string(skin_cluster):
		skin_cluster, _ = skin_cluster(skin_cluster)
	if not skin_cluster:
		return None

	mesh_path, mesh_components = mesh.mesh_path_and_components(mesh_shape_name)
	if not mesh_path or not mesh_components:
		return None

	influences_array = OpenMaya.MIntArray()
	path_array = skin_cluster.influenceObjects()
	influences_count = len(path_array)
	for i in range(influences_count):
		influences_array.append(skin_cluster.indexForInfluenceObject(path_array[i]))

	weights = skin_cluster.getWeights(mesh_path, mesh_components, influences_array)

	return weights


def set_skin_weights(skin_cluster, mesh_shape_name, skin_data):
	_skin_cluster = None
	if helpers.is_string(skin_cluster):
		_skin_cluster, _ = skin_cluster(skin_cluster)
	if not _skin_cluster:
		return None

	skin_data = str(list(skin_data))

	mesh_path, mesh_components = mesh.mesh_path_and_components(mesh_shape_name)
	if not mesh_path or not mesh_components:
		return None

	influences_array = OpenMaya.MIntArray()
	path_array = _skin_cluster.influenceObjects()
	influences_count = len(path_array)
	for i in range(influences_count):
		influences_array.append(_skin_cluster.indexForInfluenceObject(path_array[i]))

	weights_array = OpenMaya.MDoubleArray()
	for i in skin_data[1:-1].split(','):
		weights_array.append(float(i))

	runner = command.CommandRunner()

	runner.run(
		'tp-maya-commands-setSkinWeights',
		skin_cluster=_skin_cluster, mesh_path=mesh_path, mesh_components=mesh_components,
		influences_array=influences_array, weights_array=weights_array)

	# skin_cluster.setWeights(mesh_path, mesh_components, influences_array, weights_array, False)
