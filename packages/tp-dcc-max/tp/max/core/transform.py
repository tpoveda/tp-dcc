#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with transforms
"""

from pymxs import runtime as rt

from tp.max.core import node as node_utils


def freeze_transform(node_name):
    """
    Freezes the transform for the given node
    :param node_name: str
    """

    node = node_utils.get_pymxs_node(node_name)

    rotation_controller = rt.getPropertyController(node.controller, 'Rotation')
    position_controller = rt.getPropertyController(node.controller, 'Position')

    if rt.classOf(rotation_controller) != rt.Rotation_Layer:
        rotation_list_controller = rt.Rotation_List()
        rt.setPropertyController(node.controller, 'Rotation', rotation_list_controller)
        rt.setPropertyController(rotation_list_controller, 'Available', rt.Euler_Xyz())
        rotation_list_controller.setName(1, 'Frozen Rotation')
        rotation_list_controller.setName(2, 'Zero Euler XYZ')
        rotation_list_controller.setActive(2)

    if rt.classOf(position_controller) != rt.Position_Layer:
        position_list_controller = rt.Position_List()
        rt.setPropertyController(node.controller, 'Position', position_list_controller)
        pos_xyz_controller = rt.Position_XYZ()
        rt.setPropertyController(position_list_controller, 'Available', pos_xyz_controller)
        position_list_controller.setName(1, 'Frozen Position')
        position_list_controller.setName(2, 'Zero Pos XYZ')
        position_list_controller.setActive(2)
        pos_xyz_controller.x_Position = 0
        pos_xyz_controller.y_Position = 0
        pos_xyz_controller.z_Position = 0


def reset_xform_and_collapse(node_name, freeze=False):
    """
    Resets the xform and collapse the stack of the given node
    :param node_name: str
    :param freeze: bool
    """

    node = node_utils.get_pymxs_node(node_name)
    rt.ResetXForm(node)
    rt.CollapseStack(node)
    if freeze:
        freeze_transform(node)


def reset_pivot_to_origin(node_name, align_to_world=False):
    """
    Resets the pivot of the given node to the origin of the world
    :param node_name:
    :param align_to_world:
    """

    node = node_utils.get_pymxs_node(node_name)
    node.pivot = rt.Point3(0, 0, 0)
    if align_to_world:
        rt.WorldAlignPivot(node)


def link_object(source_node, parent_node, freeze=True, hierarchy=False):
    """
    Links an object and freezes it transforms (optional)
    :param source_node: str
    :param parent_node: str
    :param freeze: bool
    :param hierarchy:  bool
    """

    source_node = node_utils.get_pymxs_node(source_node)
    parent_node = node_utils.get_pymxs_node(parent_node)

    source_node.parent = parent_node
    if freeze:
        freeze_transform(source_node)
    if hierarchy:
        # TODO: Freeze character
        pass


def quick_align(source_node, target_node, freeze=False):
    """
    Aligns to objects in position
    :param source_node: str
    :param target_node: str
    :param freeze: bool
    """

    source_node = node_utils.get_pymxs_node(source_node)
    target_node = node_utils.get_pymxs_node(target_node)

    source_node.position = target_node.position
    if freeze:
        freeze_transform(source_node)


def quick_pivot_align(source_node, target_node):
    """
    Aligns pivot in position and orientation
    :param source_node: str
    :param target_node: str
    """

    source_node = node_utils.get_pymxs_node(source_node)
    target_node = node_utils.get_pymxs_node(target_node)

    source_node.pivot = target_node.pivot


def match_position(source_node, target_node, freeze=False):
    """
    Matches the position of the source node to the position of the target node
    :param source_node: str
    :param target_node: str
    :param freeze: bool
    :return:
    """

    source_node = node_utils.get_pymxs_node(source_node)
    target_node = node_utils.get_pymxs_node(target_node)

    orig_xform = source_node.transform
    orig_xform.pos = target_node.transform.translationPart
    source_node.transform = orig_xform
    if freeze:
        freeze_transform(source_node)


def match_rotation(source_node, target_node, freeze=False):
    """
    Matches the rotation of the source node to the rotation of the target node
    :param source_node: str
    :param target_node: str
    :param freeze: bool
    """

    source_node = node_utils.get_pymxs_node(source_node)
    target_node = node_utils.get_pymxs_node(target_node)

    orig_xform = source_node.transform
    orig_translation = orig_xform.translationPart
    orig_xform.rotation = target_node.transform.rotationPart
    orig_xform.pos = orig_translation
    source_node.transform = orig_xform
    if freeze:
        freeze_transform(source_node)


def match_transforms(source_node, target_node, freeze=False):
    """
    Matches the transform of the source node to the transform of the target node
    :param source_node: str
    :param target_node: str
    :param freeze: bool
    """

    source_node = node_utils.get_pymxs_node(source_node)
    target_node = node_utils.get_pymxs_node(target_node)

    orig_xform = target_node.transform
    source_node.transform = orig_xform
    if freeze:
        freeze_transform(source_node)


def move_node(node_name, amount=None, move_vertices=False, use_local_axis=True):
    """
    Moves given node
    :param node_name:
    :param amount:
    :param move_vertices:
    :param use_local_axis:
    :return:
    """

    node_to_move = node_utils.get_pymxs_node(node_name)
    if not node_to_move:
        return

    amount = amount or [0, 0, 0]
    if rt.classOf(amount) != rt.Point3:
        amount = rt.Point3(*amount)

    if move_vertices:
        xform_mod = rt.xform()
        rt.addModifier(node_to_move, xform_mod)
        rt.setProperty(xform_mod.gizmo, 'position', amount)
        rt.CollapseStack(node_to_move)
    else:
        if use_local_axis:
            coordsys = getattr(rt, '%coordsys_context')
            local_coordsys = rt.Name('local')
            prev_coordsys = coordsys(local_coordsys, None)      # store current coordsys
            rt.move(node_to_move, amount)                       # this is done in local axis
            coordsys(prev_coordsys, None)                       # restore previous coordsys
        else:
            rt.move(node_to_move, amount)
