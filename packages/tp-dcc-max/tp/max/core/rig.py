#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with rigs
"""

from __future__ import print_function, division, absolute_import

from pymxs import runtime as rt

from tp.core import log
from tp.max.core import node as node_utils, transform as xform_utils

logger = log.tpLogger


def create_bone(root_node, name='new_bone', target_node=None, parent=None, **kwargs):

    length = kwargs.pop('length', 10)
    width = kwargs.pop('width', 10)
    height = kwargs.pop('height', 10)
    color = kwargs.pop('color', [7, 7, 11])
    main_axis = kwargs.pop('main_axis', 'z')
    flip_main_axis = kwargs.pop('flip_main_axis', False)
    main_rot_axis = kwargs.pop('main_rot_axis', 'y')
    flip_main_rot_axis = kwargs.pop('flip_main_rot_axis', False)
    freeze = kwargs.pop('freeze', False)

    root_node = node_utils.get_pymxs_node(root_node)
    target_node = node_utils.get_pymxs_node(target_node)
    parent = node_utils.get_pymxs_node(parent)

    if not root_node or not node_utils.node_exists(root_node.name):
        logger.error('Bone could not be created!')
        return False

    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.color(7, 7, 11)

    bone_name = rt.uniquename(name)
    bone_box = rt.box(
        name=bone_name, lengthsegs=1, widthsegs=1, heightsegs=1, length=length, width=width, height=height,
        mapcoords=True, isSelected=True)
    bone_box.wirecolor = color
    bone_box.boneEnable = True
    bone_box.boneAxis = rt.Name(main_axis.lower())

    main_axis_index = 0
    main_rot_index = 0
    if main_axis.lower() == 'y':
        main_axis_index = 1
    elif main_axis.lower() == 'z':
        main_axis_index = 2
    if main_rot_axis.lower() == 'y':
        main_rot_index = 1
    elif main_rot_axis.lower() == 'z':
        main_rot_index = 2

    xform_utils.match_transforms(bone_box, root_node)
    if target_node and node_utils.node_exists(target_node.name):
        temp_helper = rt.Point(pos=rt.Point3(0, 0, 0))
        xform_utils.match_position(temp_helper, bone_box)
        look_at_controller = rt.LookAt_Constraint()
        rt.setPropertyController(temp_helper.controller, 'Rotation', look_at_controller)
        look_at_controller.appendTarget(target_node, 1)
        look_at_controller.target_axis = main_axis_index
        look_at_controller.upnode_axis = 1
        look_at_controller.StoUP_axis = main_rot_index
        look_at_controller.target_axisFlip = flip_main_axis
        look_at_controller.StoUP_axisFlip = flip_main_rot_axis
        xform_utils.match_transforms(bone_box, temp_helper)
        rt.delete(temp_helper)
        bone_box.height = rt.distance(root_node, target_node)

    if parent:
        bone_box.parent = parent

    if freeze:
        xform_utils.freeze_transform(bone_box)

    return bone_box


def create_end_bone(parent_bone, name='newBone', snap_to=None, match_to=None, parent=None, **kwargs):
    """
    Creates and end bone
    :param parent_bone:
    :param snap_to:
    :param match_to:
    :param name:
    :param parent:
    :return:
    """

    length = kwargs.pop('length', 10)
    width = kwargs.pop('width', 10)
    height = kwargs.pop('height', 5)
    color = kwargs.pop('color', [7, 7, 11])
    main_axis = kwargs.pop('main_axis', 'z')
    extrude = kwargs.pop('extrude', True)
    freeze = kwargs.pop('freeze', False)

    parent_bone = node_utils.get_pymxs_node(parent_bone)
    snap_to = node_utils.get_pymxs_node(snap_to)
    match_to = node_utils.get_pymxs_node(match_to)
    parent = node_utils.get_pymxs_node(parent)

    if not parent_bone or not node_utils.node_exists(parent_bone.name):
        logger.error('Bone could not be created!')
        return False

    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.color(7, 7, 11)

    bone_name = rt.uniquename(name)
    bone_box = rt.box(
        name=bone_name, lengthsegs=1, widthsegs=1, heightsegs=1, length=length, width=width, height=height,
        mapcoords=True, isSelected=True)
    bone_box.wirecolor = color
    bone_box.boneEnable = True
    bone_box.boneAxis = rt.Name(main_axis.lower())
    xform_utils.match_transforms(bone_box, parent_bone)

    rt.SetCommandPanelTaskMode(rt.Name('modify'))
    rt.convertTo(bone_box, rt.PolyMeshObject)
    rt.subobjectLevel = 1
    vertex_bitarray = rt.BitArray()
    vertex_indices = [1, 2, 3, 4]
    vertex_bitarray.count = len(vertex_indices)
    for i, index in enumerate(vertex_indices):
        vertex_bitarray[i] = index
    bone_box.EditablePoly.SetSelection(rt.Name('Vertex'), vertex_bitarray)
    bone_box.EditablePoly.collapse(rt.Name('Vertex'))
    bone_box.EditablePoly.SetSelection(rt.Name('Vertex'), rt.BitArray())
    if extrude:
        rt.subobjectLevel = 4
        vertex_bitarray = rt.BitArray()
        vertex_indices = [1]
        vertex_bitarray.count = len(vertex_indices)
        for i, index in enumerate(vertex_indices):
            vertex_bitarray[i] = index
        bone_box.EditablePoly.SetSelection(rt.Name('Face'), vertex_bitarray)
        bone_box.EditablePoly.extrudeFaces(height)
        bone_box.EditablePoly.SetSelection(rt.Name('Vertex'), rt.BitArray())
    rt.subobjectLevel = 0

    if snap_to:
        xform_utils.match_position(bone_box, snap_to)
    if match_to:
        xform_utils.match_transforms(bone_box, match_to)

    if parent:
        bone_box.parent = parent

    if freeze:
        xform_utils.freeze_transform(bone_box)

    return bone_box


def get_pole_vector_position(bone_a, bone_b, bone_c, pole_vector_distance=1.0, create_locator=False):
    """
    Calculates the correct pole vector position
    NOTE: Given nodes must be coplanar (must be on the same plane)
    :param bone_a:
    :param bone_b:
    :param bone_c:
    :param pole_vector_distance:
    :param create_locator:
    :return:
    """

    bone_a_pos = rt.Point3(*bone_a.position)
    bone_b_pos = rt.Point3(*bone_b.position)
    bone_c_pos = rt.Point3(*bone_c.position)

    # get initial vectors
    ab_vec = bone_b_pos - bone_a_pos
    ac_vec = bone_c_pos - bone_a_pos

    # calculate projection length
    ab_ac_dot = rt.dot(ab_vec, ac_vec)
    proj = float(ab_ac_dot) / float(rt.length(ac_vec))

    # calculate project vector by normalizing ac_vec and multiplying
    # that normalized vector by the projection length
    ac_vec_normalized = rt.normalize(ac_vec)
    proj_vec = ac_vec_normalized * proj

    # get the vector from the projected vector to the bone_b position
    b_proj_vec = bone_b_pos - (bone_a_pos + proj_vec)

    # calculate final pole vector position
    b_proj_vec *= pole_vector_distance
    final_pos = b_proj_vec + bone_b_pos

    if create_locator:
        test_point_helper = node_utils.create_point_helper(size=15.0, is_center_marker=False, is_box=True)
        rt.setProperty(test_point_helper, 'position', final_pos)
        return test_point_helper

    return final_pos
