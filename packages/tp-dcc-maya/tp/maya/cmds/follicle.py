# #! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya Follicles
"""

import maya.cmds

from tp.core import dcc
from tp.maya.cmds import shape, geometry, constraint as constraint_utils, transform as transform_utils
from tp.maya.cmds import mesh as mesh_utils, attribute as attr_utils


def create_empty_follicle(name=None, uv=None, hide_follicle=True):
    """
    Creates a new empty follicle
    :param name: str, name of the follicle
    :param uv: list(int, int), uv where follicle will be created
    :param hide_follicle: bool, Whether or not follicle should be hided by default
    :return: str, name of the created follicle
    """

    uv = uv if uv is not None else [0, 0]
    follicle_shape = maya.cmds.createNode('follicle')
    if hide_follicle:
        maya.cmds.hide(follicle_shape)
    follicle = maya.cmds.listRelatives(follicle_shape, p=True)[0]
    maya.cmds.setAttr('{}.inheritsTransform'.format(follicle), False)
    follicle = maya.cmds.rename(follicle, dcc.find_unique_name(name or 'follicle'))

    maya.cmds.setAttr('{}.parameterU'.format(follicle), uv[0])
    maya.cmds.setAttr('{}.parameterV'.format(follicle), uv[1])

    return follicle


def create_mesh_follicle(mesh, description=None, uv=None, hide_follicle=True):
    """
    Crates follicle on a mesh
    :param mesh: str, name of the mesh to attach follicle to
    :param description: str, description of the follicle
    :param uv: list(int, int,), corresponds to the UVs of the mesh in which the follicle will be attached
    :param hide_follicle: bool, Whether or not follicle should be hided by default
    :return: str, name of the created follicle
    """

    uv = uv if uv is not None else [0, 0]
    follicle = create_empty_follicle(description, uv, hide_follicle=hide_follicle)
    shape = maya.cmds.listRelatives(follicle, shapes=True)[0]
    maya.cmds.connectAttr('{}.outMesh'.format(mesh), '{}.inputMesh'.format(follicle))
    maya.cmds.connectAttr('{}.worldMatrix'.format(mesh), '{}.inputWorldMatrix'.format(follicle))
    maya.cmds.connectAttr('{}.outTranslate'.format(shape), '{}.translate'.format(follicle))
    maya.cmds.connectAttr('{}.outRotate'.format(shape), '{}.rotate'.format(follicle))

    return follicle


def create_surface_follicle(surface, name=None, uv=None, hide_follicle=True):
    """
    Crates follicle on a surface
    :param surface: str, name of the surface to attach follicle to
    :param name: str, description of the follicle
    :param uv: list(int, int,), corresponds to the UVs of the mesh in which the follicle will be attached
    :param hide_follicle: bool, Whether or not follicle should be hided by default
    :return: str, name of the created follicle
    """

    uv = uv if uv is not None else [0, 0]
    follicle = create_empty_follicle(name, uv, hide_follicle=hide_follicle)
    shape = maya.cmds.listRelatives(follicle, shapes=True)[0]
    maya.cmds.connectAttr('{}.local'.format(surface), '{}.inputSurface'.format(follicle))
    maya.cmds.connectAttr('{}.worldMatrix'.format(surface), '{}.inputWorldMatrix'.format(follicle))
    maya.cmds.connectAttr('{}.outTranslate'.format(shape), '{}.translate'.format(follicle))
    maya.cmds.connectAttr('{}.outRotate'.format(shape), '{}.rotate'.format(follicle))

    return follicle


def follicle_to_mesh(transform, mesh, u=None, v=None, constraint=True, constraint_type='parentConstraint', local=False):
    """
    Uses a follicle to attach the transform to the mesh.
    If no U an V values are given, the command will try to find the closest position on the mesh
    :param transform: str, name of a transform to follicle to the mesh
    :param mesh: str, name of a mesh to attach follicle to
    :param u: float, U value to attach to
    :param v: float, V, value to attach to
    :param constraint: bool
    :param constraint_type: str
    :param local: bool
    :return: str, name of the follicle created
    """

    if not shape.is_a_shape(mesh):
        mesh = geometry.get_mesh_shape(mesh)

    position = maya.cmds.xform(transform, q=True, ws=True, t=True)
    uv = u, v
    if not u or not v:
        uv = mesh_utils.get_closest_uv_on_mesh(mesh, position)

    follicle = create_mesh_follicle(mesh, transform, uv)

    if constraint:
        if local:
            constraint_utils.constraint_local(follicle, transform, constraint=constraint_type)
        else:
            loc = maya.cmds.spaceLocator(n='locator_{}'.format(follicle))[0]
            maya.cmds.parent(loc, follicle)
            transform_utils.MatchTransform(transform, loc).translation_rotation()
            # cmds.parentConstraint(loc, transform, mo=True)
            eval('cmds.{}("{}", "{}", mo=True)'.format(constraint_type, loc, transform))
    else:
        maya.cmds.parent(transform, follicle)

    return follicle


def follicle_to_surface(transform, surface, u=None, v=None, constraint=False):
    """
    Uses a follicle to attach the transform to the surface
    If no U an V values are given, the command will try to find the closest position on the surface
    :param transform: str, str, name of a transform to follicle to the surface
    :param surface: str, name of a surface to attach follicle to
    :param u: float, U value to attach to
    :param v: float, V value to attach to
    :param constraint: bool
    :return: str, name of the follicle created
    """

    position = maya.cmds.xform(transform, q=True, ws=True, rp=True)
    uv = u, v
    if not u or not v:
        uv = geometry.get_closest_parameter_on_surface(surface, position)

    follicle = create_surface_follicle(surface, transform, uv)

    if constraint:
        loc = maya.cmds.spaceLocator(n='locator_{}'.format(follicle))[0]
        maya.cmds.parent(loc, follicle)
        transform_utils.MatchTransform(transform, loc).translation_rotation()
        maya.cmds.parentConstraint(loc, transform, mo=True)
    else:
        maya.cmds.parent(transform, follicle)

    return follicle


def get_follicle_output_curve(follicle):
    """
    Returns the attached output curve of the given follicle node
    :param follicle: str
    :return: str or None
    """

    return attr_utils.outputs('{}.outCurve'.format(follicle), node_only=True)


def get_follicle_input_curve(follicle):
    """
    Returns the attached input curve of the given follicle node
    :param follicle: str
    :return: str or None
    """

    return attr_utils.inputs('{}.startPosition'.format(follicle), node_only=True)
