#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Color Management (OCIO) utils functions for Maya
"""

import maya.cmds

from tp.core import log

LOGGER = log.tpLogger


def is_color_management_enabled():
    """
    Returns whether or not color management is enabled
    :return: bool
    """

    return maya.cmds.colorManagementPrefs(cmEnabled=True, query=True)


def enable_color_management():
    """
    Enables color management
    """

    return maya.cmds.colorManagementPrefs(cmEnabled=True, edit=True)


def disable_color_management():
    """
    Enables color management
    """

    return maya.cmds.colorManagementPrefs(cmEnabled=False, edit=True)


def toggle_color_management():
    """
    Toggles color management enable/disable status
    """

    return maya.cmds.colorManagementPrefs(
        cmEnabled=not maya.cmds.colorManagementPrefs(cmEnabled=True, query=True), edit=True)


def get_all_rendering_space_names():
    """
    Returns a list with all available render space names
    :return: list(str)
    """

    return maya.cmds.colorManagementPrefs(renderingSpaceNames=True, query=True)


def set_rendering_space(rendering_space):
    """
    Sets current rendering space used by OCIO
    :param rendering_space: int or string, element index in the rendering spaces list or rendering space name
    """

    all_rendering_space_names = get_all_rendering_space_names()
    if type(rendering_space) is int:
        rendering_space = all_rendering_space_names[rendering_space]
    else:
        if rendering_space not in all_rendering_space_names:
            LOGGER.warning('Color Management Rendering Space "{}" is not valid!'.format(rendering_space))
            return

    return maya.cmds.colorManagementPrefs(renderingSpaceName=rendering_space, edit=True)


def get_all_view_transform_names():
    """
    Returns a list with all available view transform names
    :return: list(str)
    """

    return maya.cmds.colorManagementPrefs(viewTransformNames=True, query=True)


def set_view_transform(view_transform):
    """
    Sets current view transform used by OCIO
    :param view_transform: int or string, element index in the view transforms list or view transform name
    """

    all_available_view_transforms = get_all_view_transform_names()
    if type(view_transform) is int:
        view_transform = get_all_view_transform_names[view_transform]
    else:
        if view_transform not in all_available_view_transforms:
            LOGGER.warning('Color Management View Transform "{}" is not valid!'.format(view_transform))
            return

    return maya.cmds.colorManagementPrefs(viewTransformName=view_transform, edit=True)
