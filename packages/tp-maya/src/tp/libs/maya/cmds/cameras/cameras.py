from __future__ import annotations

import enum

from maya import cmds

from ..nodeutils import objhandling


class CameraTypes(enum.Enum):
    """Enum that defines the types of cameras available in Maya."""

    ALL = "all"
    PERSP = "perspective"
    ORTHO = "orthographic"


def get_all_camera_shapes(full_path=True):
    """
    Returns all cameras shape names available in the current scene.

    :param full_path: Whether tor return full path to camera nodes or short ones
    :return: list of all camera shape names in the scene.
    """

    return cmds.ls(type="camera", long=full_path) or []


def filter_camera_type(cam_shapes_list: list[str] | None = None, camera_type: str = CameraTypes.ALL.value):
    """
    Returns all camera shape names of the given type.

    :param cam_shapes_list: list of camera shapes nodes. If not given, all scene cameras will be used.
    :param camera_type: which camera type to filter ('all', 'perspective', 'orthographic').
    :return: list of filtered camera shape node names.
    """

    cam_shapes_list = get_all_camera_shapes(full_path=True) if cam_shapes_list is None else cam_shapes_list

    if camera_type == CameraTypes.ALL:
        return cam_shapes_list

    cam_filter_list: list[str] = []
    for cam_shape in cam_shapes_list:
        if cmds.getAttr("{}.orthographic".format(cam_shape)):
            if camera_type == CameraTypes.ORTHO:
                cam_filter_list.append(cam_shape)
        else:
            if camera_type == CameraTypes.PERSP:
                cam_filter_list.append(cam_shape)

    return cam_filter_list


def get_all_camera_transforms(
    camera_type: str = CameraTypes.ALL.value, full_path: bool = True
) -> list[str]:
    """
    Returns all camera transform names in the current scene.

    :param camera_type: type of camera to return transforms of.
    :param full_path: Whether tor return full path to camera nodes or short ones
    :return: list of all camera transform names in the scene.
    """

    all_camera_shapes = get_all_camera_shapes(full_path=True)
    if not all_camera_shapes:
        return []

    camera_shape_list = filter_camera_type(all_camera_shapes, camera_type=camera_type)

    return objhandling.get_transforms(camera_shape_list, full_path=full_path)


def get_startup_camera_shapes(include_left_back_bottom=True):
    """
    Returns all the cameras shape nodes available when a new scene is created (long names)
    :param include_left_back_bottom: bool, Whether to include or not default bottom, left, and back camera shapes
    :return: list(str)
    """

    cam_shape_list = get_all_camera_shapes(full_path=True)
    startup_camera_shape_list: list[str] = []
    for cam_shape in cam_shape_list:
        if cmds.camera(
            cmds.listRelatives(cam_shape, parent=True)[0],
            startupCamera=True,
            query=True,
        ):
            startup_camera_shape_list.append(cam_shape)
    if not include_left_back_bottom:
        return startup_camera_shape_list

    for cam in ["bottom", "left", "back"]:
        cam_shape = "{}Shape".format(cam)
        if cmds.objExists(cam_shape):
            startup_camera_shape_list.append(cam_shape)

    return startup_camera_shape_list


def get_startup_camera_transforms() -> list[str]:
    """
    Returns all the cameras transform nodes available when a new scene is created (long names).

    :return: list of startup camera transform names.
    """

    startup_camera_shapes = get_startup_camera_shapes()
    if not startup_camera_shapes:
        return []

    return objhandling.get_transforms(startup_camera_shapes)
