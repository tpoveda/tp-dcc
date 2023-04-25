#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with cameras
"""

import maya.cmds
import maya.api.OpenMaya
import maya.api.OpenMayaUI

from tp.maya.om import mathlib
from tp.maya.cmds import node, transform


class CameraTypes(object):
    ALL = 'all'
    PERSP = 'perspective'
    ORTHO = 'ortographic'


def check_camera(node):
    """
    Checks if given node is a camera. If not, exception is raised
    :param node: str
    """

    if not is_camera(node):
        raise Exception('Object "{}" is not a valid camera!'.format(node))

    return True


def is_camera(node):
    """
    Returns whether given node is a valid camera or not
    :param node: str
    :return: bool
    """

    if not maya.cmds.objExists(node):
        return False

    node_shapes = [node]
    if transform.is_transform(node):
        node_shapes = maya.cmds.listRelatives(node, s=True, pa=True)
        if not node_shapes:
            return False

    for shape in node_shapes:
        if maya.cmds.objectType(shape) == 'camera':
            return True

    return False


def filter_camera_type(cam_shapes_list=None, camera_type=CameraTypes.ALL):
    """
    Returns all camera shapes of the given type
    :param cam_shapes_list: list(str), list of camera shapes nodes. If not given, all scene cameras will be use
    :param camera_type: str, which camera type to filter ('all', 'perspective', 'orthographic')
    :return: list(str), list of filtered camera shape nodes
    """

    if cam_shapes_list is None:
        cam_shapes_list = get_all_camera_shapes(full_path=True)

    if camera_type == CameraTypes.ALL:
        return cam_shapes_list

    cam_filter_list = list()
    for cam_shape in cam_shapes_list:
        if maya.cmds.getAttr('{}.orthographic'.format(cam_shape)):
            if camera_type == CameraTypes.ORTHO:
                cam_filter_list.append(cam_shape)
        else:
            if camera_type == CameraTypes.PERSP:
                cam_filter_list.append(cam_shape)

    return cam_filter_list


def get_startup_camera_shapes(include_left_back_bottom=True):
    """
    Returns all the cameras shape nodes available when a new scene is created (long names)
    :param include_left_back_bottom: bool, Whether to include or not default bottom, left, and back camera shapes
    :return: list(str)
    """

    cam_shape_list = get_all_camera_shapes(full_path=True)
    startup_camera_shape_list = list()
    for cam_shape in cam_shape_list:
        if maya.cmds.camera(maya.cmds.listRelatives(cam_shape, parent=True)[0], startupCamera=True, query=True):
            startup_camera_shape_list.append(cam_shape)
    if not include_left_back_bottom:
        return startup_camera_shape_list

    for cam in ["bottom", "left", "back"]:
        cam_shape = '{}Shape'.format(cam)
        if maya.cmds.objExists(cam_shape):
            startup_camera_shape_list.append(cam_shape)

    return startup_camera_shape_list


def get_startup_camera_transforms(full_path=True):
    """
    Returns all the cameras transform nodes available when a new scene is created (long names)
    :param full_path: bool, Whether to return full path to camera nodes or short ones
    :return: list(str)
    """

    startup_camera_shapes = get_startup_camera_shapes()
    if not startup_camera_shapes:
        return list()

    return transform.get_transforms(startup_camera_shapes)


def get_all_camera_shapes(full_path=True):
    """
    Returns all cameras shapes available in the current scene
    :param full_path: bool, Whether tor return full path to camera nodes or short ones
    :return: list(str)
    """

    return maya.cmds.ls(type='camera', long=full_path) or list()


def get_all_camera_transforms(camera_type=CameraTypes.ALL, full_path=True):
    """
    Returns all camera transforms in the current scnee
    :param camera_type: str. type of camera to return transforms of
    :param full_path: bool, Whether tor return full path to camera nodes or short ones
    :return: list(str)
    """

    all_camera_shapes = get_all_camera_shapes(full_path=True)
    if not all_camera_shapes:
        return list()

    camera_shape_list = filter_camera_type(all_camera_shapes, camera_type=camera_type)

    return transform.get_transforms(camera_shape_list, full_path=full_path)


def get_user_camera_shapes():
    """
    Returns all the camera shape nodes in current scene except the default ones
    :return: list(str)
    """

    cam_shape_list = get_all_camera_shapes(full_path=True)
    startup_camera_shape_list = get_startup_camera_shapes()

    return list(set(cam_shape_list) - set(startup_camera_shape_list))


def get_user_camera_transforms(camera_type=CameraTypes.ALL):
    """
    Returns all the camera transforms node in the current scene except the default ones
    :param camera_type: str, camera type to filter by ('all', 'perspective', 'orthographic')
    :return: ist(str), filtered camera transforms
    """

    user_camera_shapes = get_user_camera_shapes()
    if not user_camera_shapes:
        return list()

    cam_shape_list = filter_camera_type(user_camera_shapes, camera_type=camera_type)

    return transform.get_transfroms(cam_shape_list)


def get_all_cameras(exclude_standard_cameras=True, return_transforms=True, full_path=True):
    """
    Returns all cameras in current scene
    :param exclude_standard_cameras: bool, Whether standard cameras (persp, top, front, and side) cameras
        should be excluded or not
    :param return_transforms: bool, Whether tor return camera shapes or transform nodes
    :param full_path: bool, Whether tor return full path to camera nodes or short ones
    :return: list(str)
    """

    if exclude_standard_cameras:
        cameras = [c for c in maya.cmds.ls(
            type='camera', long=full_path) if not maya.cmds.camera(c, query=True, sc=True)]
    else:
        cameras = get_all_camera_shapes(full_path=full_path)

    if return_transforms:
        return [maya.cmds.listRelatives(c, p=True, fullPath=full_path)[0] for c in cameras]

    return cameras


def get_current_camera(use_api=True, full_path=True):
    """
    Returns the currently active camera
    :param use_api: bool, Whether to use OpenMaya API to retrieve the camera path or not
    :param full_path: bool
    :return: str, name of the active camera transform
    """

    if use_api:
        camera_path = maya.api.OpenMayaUI.M3dView().active3dView().getCamera()
        if full_path:
            return camera_path.fullPathName()
        else:
            return camera_path.partialPathName()
    else:
        panel = maya.cmds.getPanel(withFocus=True)
        if maya.cmds.getPanel(typeOf=panel) == 'modelPanel':
            cam = maya.cmds.modelEditor(panel, query=True, camera=True)
            if cam:
                if maya.cmds.nodeType(cam) == 'transform':
                    return cam
                elif maya.cmds.objectType(cam, isAType='shape'):
                    parent = maya.cmds.listRelatives(cam, parent=True, fullPath=full_path)
                    if parent:
                        return parent[0]

        cam_shapes = maya.cmds.ls(sl=True, type='camera')
        if cam_shapes:
            return maya.cmds.listRelatives(cam_shapes, parent=True, fullPath=full_path)[0]

        transforms = maya.cmds.ls(sl=True, type='transform')
        if transforms:
            cam_shapes = maya.cmds.listRelatives(transforms, shapes=True, type='camera')
            if cam_shapes:
                return maya.cmds.listRelatives(cam_shapes, parent=True, fullPath=full_path)[0]


def set_current_camera(camera_name):
    """
    Sets the camera to be used in the active view
    :param camera_name: str, name of the camera to use
    """

    view = maya.api.OpenMayaUI.M3dView.active3dView()
    if maya.cmds.nodeType(camera_name) == 'transform':
        shapes = maya.cmds.listRelatives(camera_name, shapes=True)
        if shapes and maya.cmds.nodeType(shapes[0]) == 'camera':
            camera_name = shapes[0]

    mobj = node.get_mobject(camera_name)
    cam = maya.api.OpenMaya.MDagPath(mobj)
    view.setCamera(cam)

    maya.cmds.refresh()


def get_eye_point(camera_name):
    """
    Returns camera eye point
    :param camera_name: str
    :return: list(float, float, float)
    """

    check_camera(camera_name)

    camera_shape = maya.cmds.ls(maya.cmds.listRelatives(camera_name, s=True, pa=True), type='camera')[0]
    camera_dag_path = node.get_mdag_path(camera_shape)
    camera_fn = maya.api.OpenMaya.MFnCamera(camera_dag_path)
    camera_pt = camera_fn.eyePoint(maya.api.OpenMaya.MSpace.kWorld)

    return [camera_pt.x, camera_pt.y, camera_pt.z]


def get_distance_to_camera(transform_node, camera_node):
    """
    Returns the distance between the given node (transform) and a camera
    :param transform_node: str, transform node to calculate distance to camera from
    :param camera_node: str, camera to calculate distance from
    :return: float
    """

    node.check_node(transform_node)
    transform.check_transform(node)
    node.check_node(camera_node)
    check_camera(camera_node)

    cam_pt = get_eye_point(camera_node)
    node_pt = maya.cmds.xform(transform_node, query=True, ws=True, rp=True)
    distance = mathlib.distance_between(cam_pt, node_pt)

    return distance


def get_available_cameras_film_gates():
    """
    Returns a list with all available camera film gates
    NOTE: The order is VERY important, it must follows the order that appears in Maya
    :return: list(str)
    """

    return [
        'User', '16mm Theatrical', 'Super 16mm', '35mm Academy', '35mm TV Projection', '35mm Full Aperture',
        '35mm 1.85 Projection', '35mm Anamorphic', '70mm Projection', 'VistaVision'
    ]
