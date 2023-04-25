#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with meshes for Autodesk Maya OpenMaya API
"""

import maya.api.OpenMaya as OpenMaya


def mesh_path_and_components(mesh_name):
	"""
	Returns mesh path and components of the given mesh name.

	:param str mesh_name: name of the mesh whose components we want to retrieve.
	:return: tuple with the mesh DAG path and the Maya Object that represents the mesh components.
	:rtype: tuple(MDagPath, MObject)
	"""

	selection_list = OpenMaya.MGlobal.getSelectionListByName('{}.vtx[*]'.format(mesh_name))
	mesh_path, mesh_components = selection_list.getComponent(0)

	return mesh_path, mesh_components


def face_center(mesh, face_id):
	"""
	Returns the center position of a face.

	:param mesh: str, name of a mesh
	:param face_id: int, index of a face component
	:return: list(float, float, float), vector of the center of the face
	"""

	pass

	# mesh = get_mesh_shape(mesh)
	# face_iter = api.IteratePolygonFaces(mesh)
	#
	# return face_iter.get_center(face_id)


def face_centers(mesh):
	"""
	Returns all face centers of the given mesh
	:param mesh: str, name of a mesh
	:return: list(list(float, float, float)), list containing all vector centers of the mesh
	"""

	pass

	# mesh = get_mesh_shape(mesh)
	# face_iter = api.IteratePolygonFaces(mesh)
	#
	# return face_iter.get_face_center_vectors()
