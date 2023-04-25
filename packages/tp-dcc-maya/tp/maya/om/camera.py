#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with OpenMaya camera for Autodesk Maya
"""

import maya.api.OpenMayaUI as OpenMayaUI


def get_current_camera(full_path=True):
	"""
	Returns the current scene active camera.

	:param bool full_path: whether to return the long or short camera name
	:return: name of the active camera transform.
	:rtype: str
	"""

	active_3d_view = OpenMayaUI.M3dView().active3dView()
	if not active_3d_view:
		return ''

	camera_path = active_3d_view.getCamera()
	if not camera_path:
		return ''

	if full_path:
		return camera_path.fullPathName()
	else:
		return camera_path.partialPathName()