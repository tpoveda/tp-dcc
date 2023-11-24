#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with joints
"""

import math
import random

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.core import log, dcc
from tp.common.python import helpers, strings, name as python_name
from tp.common.math import vec3
from tp.maya.om import mathlib
from tp.maya.cmds import exceptions, decorators, scene, attribute, transform, node, constraint as cns_utils
from tp.maya.cmds import matrix as matrix_utils, name as name_utils, shape as shape_utils, ik as ik_utils

logger = log.tpLogger


def check_joint(joint):
    """
    Checks if a node is a valid joint and raise and exception if the joint is not valid
    :param joint: str, name of the node to be checked
    :return: bool, True if the give node is a joint node or False otherwise
    """

    if not is_joint(joint):
        raise exceptions.JointException(joint)


def is_joint(joint):
    """
    Checks if the given object is a joint
    :param joint: str, object to query
    :return: bool, True if the given object is a valid joint or False otherwise
    """

    if not cmds.objExists(joint):
        return False

    if not cmds.nodeType(joint) == 'joint':
        return False

    return True


def is_end_joint(joint):
    """
    Returns True if the given joint is an end joint (last child of hierarchy) or False otherwise
    :param joint: str, name of the joint to check
    :return: bool
    """

    check_joint(joint)

    joint_descendants = cmds.ls(cmds.listRelatives(joint, ad=True) or [], type='joint')
    if not joint_descendants:
        return True

    return False


def end_joint(start_joint, include_transforms=False):
    """
    Find the end joint of a chain from the given start joint
    :param start_joint: str, joint to find end joint from
    :param include_transforms: bool, Include non-joint transforms in the chain
    :return: str
    """

    check_joint(start_joint)

    end_joint = None
    next_joint = start_joint
    while next_joint:
        child_list = cmds.listRelatives(next_joint, fullPath=True, c=True) or list()
        child_joints = cmds.ls(child_list, long=True, type='joint') or list()
        if include_transforms:
            child_joints = list(set(child_joints + cmds.ls(child_list, long=True, transforms=True) or list()))
        if child_joints:
            next_joint = child_joints[0]
        else:
            end_joint = next_joint
            next_joint = None

    return end_joint


def joint_list(start_joint, end_joint):
    """
    Get list of joints between and including given start and end joint
    :param start_joint: str, start joint of joint list
    :param end_joint: str, end joint of joint list
    :return: list<str>
    """

    check_joint(start_joint)
    check_joint(end_joint)

    if start_joint == end_joint:
        return [start_joint]

    # Check hierarchy
    descendant_list = cmds.ls(cmds.listRelatives(start_joint, ad=True, fullPath=True), long=True, type='joint')
    if not descendant_list.count(end_joint):
        raise Exception('End joint "{}" is not a descendant of start joint "{}"'.format(end_joint, start_joint))

    joint_list = [end_joint]
    while joint_list[-1] != start_joint:
        parent_jnt = cmds.listRelatives(joint_list[-1], p=True, pa=True, fullPath=True)
        if not parent_jnt:
            raise Exception('Found root joint while searching for start joint "{}"'.format(start_joint))
        joint_list.append(parent_jnt[0])

    joint_list.reverse()

    return joint_list


def is_joint_below_hierarchy(joint: str, find_joint: str) -> bool:
    """
    Recursive function that checks whether a joint is in the parent hierarchy of another.

    :param str joint: joint name that is part of a skeleton.
    :param str find_joint: joint name to check for.
    :return: True if the given joint is in the parent hierarchy; False otherwise.
    :rtype: bool
    """

    parent = helpers.first_in_list(cmds.listRelatives(joint, parent=True, fullPath=True, type='joint'))
    if joint == find_joint or parent == find_joint:
        return True
    elif parent and parent != find_joint:
        return is_joint_below_hierarchy(parent, find_joint)
    else:
        return False


def get_length(joint):
    """
    Returns the length of a given joint
    :param joint: str, joint to query length from
    :return: str
    """

    check_joint(joint)

    child_joints = cmds.ls(cmds.listRelatives(joint, c=True, pa=True) or [], type='joint')
    if not child_joints:
        return 0.0

    max_length = 0.0
    for child_jnt in child_joints:
        pt1 = transform.get_position(joint)
        pt2 = transform.get_position(child_jnt)
        offset = mathlib.offset_vector(pt1, pt2)
        length = mathlib.magnitude(offset)
        if length > max_length:
            max_length = length

    return max_length


def duplicate_joint(joint, name=None):
    """
    Duplicates a given joint
    :param joint: str, joint to duplicate
    :param name: variant, str || None, new name for duplicated joint. If None, leave as default
    :return: str
    """

    check_joint(joint)
    if not name:
        name = joint + '_dup'
    if cmds.objExists(str(name)):
        raise Exception('Joint "{}" already exists!'.format(name))

    dup_joint = cmds.duplicate(joint, po=True)[0]
    if name:
        dup_joint = cmds.rename(dup_joint, name)

    # Unlock transforms
    for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v', 'radius']:
        cmds.setAttr(dup_joint + '.' + attr, long=False, cb=True)

    return dup_joint


def duplicate_chain(start_jnt, end_jnt=None, parent=None, skip_jnt=None, prefix=None):
    """
    Duplicats a joint chain based on start and en joint
    :param start_jnt: str, start joint of chain
    :param end_jnt: str, end joint of chain. If None, use end of current chain
    :param parent: str, parent transform for new chain
    :param skip_jnt: variant, str ||None, skip joints in chain that match name pattern
    :param prefix: variant, str ||None, new name prefix
    :return: list<str>, list of duplicate joints
    """

    if not cmds.objExists(start_jnt):
        raise Exception('Start joint "{}" does not exists!'.format(start_jnt))
    if end_jnt and not cmds.objExists(str(end_jnt)):
        raise Exception('End joint "{}" does not exists!'.format(end_jnt))

    if parent:
        if not cmds.objExists(parent):
            raise Exception('Given parent transform "{}" does not eixsts!'.format(parent))
        if not transform.is_transform(parent):
            raise Exception('Parent object "{}" is not a valid transform!'.format(parent))

    if not end_jnt:
        end_jnt = end_joint(start_jnt=start_jnt)
    joints = joint_list(start_joint=start_jnt, end_joint=end_jnt)

    skip_joints = cmds.ls(skip_jnt) if skip_jnt else list()

    dup_chain = list()
    for i in range(len(joints)):
        if joints[i] in skip_joints:
            continue

        name = None
        if prefix:
            jnt_index = strings.get_alpha(i, capitalong=True)
            if i == (len(joints) - 1):
                jnt_index = 'End'
            name = prefix + jnt_index + '_jnt'

        jnt = duplicate_joint(joint=joints[i], name=name)

        if not i:
            if not parent:
                if cmds.listRelatives(jnt, p=True):
                    try:
                        cmds.parent(jnt, w=True)
                    except Exception:
                        pass
            else:
                try:
                    cmds.parent(jnt, parent)
                except Exception:
                    pass
        else:
            try:
                cmds.parent(jnt, dup_chain[-1])
                if not cmds.isConnected(dup_chain[-1] + '.scale', jnt + '.inverseScale'):
                    cmds.connectAttr(dup_chain[-1] + '.scale', jnt + '.inverseScale', f=True)
            except Exception as e:
                raise Exception('Error while duplicating joint chain! - {}'.format(str(e)))

        dup_chain.append(jnt)

    return dup_chain


def joint_buffer(joint, index_str=0):
    """
    Creates a joint buffer group in the given joint
    :param joint: str, name of the joint we want to create buffer for
    :param index_str: int, string index
    :return: str, name of the joint buffer group created
    """

    if not cmds.objExists(joint):
        raise Exception('Joint "{}" does not exists!'.format(joint))

    if not index_str:
        result = cmds.promptDialog(
            title='Index String',
            message='Joint Group Index',
            text='0',
            button=['Create', 'Cancel'],
            defaultButton='Create',
            cancelButton='Cancel',
            dismissString='Cancel'
        )

        if result == 'Create':
            index_str = cmds.promptDialog(q=True, text=True)
        else:
            logger.warning('User canceled joint group creation ...')
            return

        # Get joint prefix and create joint buffer group
        prefix = strings.strip_suffix(joint)
        grp = cmds.duplicate(joint, po=True, n=prefix + 'Buffer' + index_str + '_jnt')[0]
        cmds.parent(joint, grp)

        if cmds.getAttr(grp + '.radius', se=True):
            try:
                cmds.setAttr(grp + '.radius', 0)
            except Exception:
                pass

        # Connect inverse scale
        inverse_scale_cnt = cmds.listConnections(joint + '.inverseScale', s=True, d=False)
        if not inverse_scale_cnt:
            inverse_scale_cnt = list()
        if not inverse_scale_cnt.count(grp):
            try:
                cmds.connectAttr(grp + '.scale', joint + '.inverseScale', f=True)
            except Exception:
                pass

        # Delete user attributes
        user_attrs = cmds.listAttr(grp, ud=True)
        if user_attrs:
            for attr in user_attrs:
                if cmds.objExists(grp + '.' + attr):
                    cmds.setAttr(grp + '.' + attr, long=False)
                    cmds.deleteAttr(grp + '.' + attr)

        node.display_override(obj=joint, override_enabled=True, override_lod=0)
        node.display_override(obj=grp, override_enabled=True, override_display=2, override_lod=1)


def set_draw_style(joints, draw_style='bone'):
    """
    Set joint draw style for the given joints
    :param joints: list<str>, list of joints to set draw style for
    :param draw_style: str, draw style to apply to the given joints ("bone", "box", "none")
    :return: list<str>, list of joints which draw styles have been changed
    """

    if not joints:
        raise Exception('No joints given!')

    draw_style = draw_style.lower()
    if draw_style not in ['bone', 'box', 'none']:
        raise Exception('Invalid draw style ("{}")! Accepted values are "bone", "box", "none"'.format(draw_style))

    if type(joints) not in [list, tuple]:
        joints = [joints]

    for jnt in joints:
        if not is_joint(jnt):
            continue
        if draw_style == 'bone':
            cmds.setAttr('{}.drawStyle'.format(jnt), 0)
        elif draw_style == 'box':
            cmds.setAttr('{}.drawStyle'.format(jnt), 1)
        elif draw_style == 'none':
            cmds.setAttr('{}.drawStyle'.format(jnt), 2)

    return joints


def create_from_point_list(point_list, orient=False, side='c', part='chain', suffix='jnt'):
    """
    Create joint chain from a list of point positions
    :param point_list: list<tuple>, list of points to create joint chain from
    :param orient: bool, Whether to orient or not the joints
    :param side: str, joint side name prefix
    :param part: str, joint part name
    :param suffix: str, joint suffix name
    :return: list<str>, list of new created joints
    """

    cmds.select(clong=True)

    joint_list = list()
    for i in range(len(point_list)):
        jnt = cmds.joint(p=point_list[i], n='{}_{}{}_{}'.format(side, part, str(i + 1), suffix))
        if i and orient:
            cmds.joint(joint_list[-1], e=True, zso=True, oj='xyz', sao='yup')
        joint_list.append(jnt)

    return joint_list


def orient(joint, aim_axis='x', up_axis='y', up_vector=(0, 1, 0)):
    """
    Orient joints based on user defined vectors
    :param joint: str, joints to orient
    :param aim_axis: str, axis to be aligned down the length of the joint
    :param up_axis: str, axis to be aligned with the world vector given by up vector
    :param up_vector: tuple<int>, world vector to align up axis to
    """

    check_joint(joint)

    child_list = cmds.listRelatives(joint, c=True)
    child_joint_list = cmds.listRelatives(joint, c=True, type='joint', pa=True)

    if child_list:
        child_list = cmds.parent(child_list, world=True)

    if not child_joint_list:
        cmds.setAttr('{}.jo'.format(joint), 0, 0, 0)
    else:
        parent_matrix = OpenMaya.MMatrix()
        parent_joint = cmds.listRelatives(joint, p=True, pa=True)
        if parent_joint:
            parent_matrix = transform.get_matrix(parent_joint[0])

        # Aim Vector
        aim_point_1 = transform.get_position(joint)
        aim_point_2 = transform.get_position(child_joint_list[0])
        aim_vector = mathlib.offset_vector(aim_point_1, aim_point_2)

        target_matrix = matrix_utils.build_rotation(aim_vector, up_vector, aim_axis, up_axis)
        orient_matrix = target_matrix * parent_matrix.inverse()

        # Extract joint orient values
        rotation_order = cmds.getAttr('{}.ro'.format(joint))
        orient_rotation = matrix_utils.get_rotation(orient_matrix, rotation_order=rotation_order)

        # Reset joint rotation and orientation
        cmds.setAttr('{}.r'.format(joint), 0, 0, 0)
        cmds.setAttr('{}.jo'.format(orient_rotation[0], orient_rotation[1], orient_rotation[2]))

    # Reparent children
    if child_list:
        cmds.aprent(child_list, joint)


def orient_to(joint, target):
    """
    Matches given joint orientation to given transform
    :param joint: str, joint to set orientation for
    :param target: str, transform to match joint orientation to
    """

    if not cmds.objExists(joint):
        raise Exception('Joint "{}" does not exist!'.format(joint))
    if not cmds.objExists(target):
        raise Exception('Target "{}" does not exist!'.format(target))
    if not transform.is_transform(target):
        raise Exception('Target "{}" is not a valid transform!'.format(target))

    # Unparent children
    child_list = cmds.listRelatives(joint, c=True, type=['joint', 'transform'])
    if child_list:
        child_list = cmds.parent(child_list, world=True)

    # Get parent joint matrix
    parent_matrix = OpenMaya.MMatrix()
    parent_joint = cmds.listRelatives(joint, p=True, pa=True)
    if parent_joint:
        parent_matrix = transform.get_matrix(parent_joint[0])

    target_matrix = transform.get_matrix(target)
    orient_matrix = target_matrix * parent_matrix.inverse()

    # Extract joint orient values
    rotation_order = cmds.getAttr('{}.ro'.format(joint))
    orient_rotation = matrix_utils.get_rotation(orient_matrix, rotation_order=rotation_order)

    # Reset joint rotation and orientation
    cmds.setAttr('{}.r'.format(joint), 0, 0, 0)
    cmds.setAttr('{}.jo'.format(orient_rotation[0], orient_rotation[1], orient_rotation[2]))

    # Reparent children
    if child_list:
        cmds.aprent(child_list, joint)


def orient_x_to_child(joint, invert=False):
    """
    Function that orients given joint to its child (points X axis of joint to its child)
    :param joint: str
    :param invert: bool
    """

    aim_axis = [1, 0, 0] if not invert else [-1, 0, 0]
    up_axis = [0, 1, 0] if not invert else [0, -1, 0]
    children = cmds.listRelatives(joint, type='transform')
    if children:
        orient = OrientJoint(joint, children)
        orient.set_aim_at(3)
        orient.set_aim_up_at(0)
        orient.set_aim_vector(aim_axis)
        orient.set_up_vector(up_axis)
        orient.run()

    if not children:
        cmds.makeIdentity(joint, jo=True, apply=True)


def orient_y_to_child(joint, invert=False):
    """
    Function that orients given joint to its child (points Y axis of joint to its child)
    :param joint: str
    :param invert: bool
    """

    aim_axis = [0, 1, 0] if not invert else [0, -1, 0]
    up_axis = [0, 0, 1] if not invert else [0, 0, -1]
    children = cmds.listRelatives(joint, type='transform')
    if children:
        orient = OrientJoint(joint, children)
        orient.set_aim_at(3)
        orient.set_aim_up_at(0)
        orient.set_aim_vector(aim_axis)
        orient.set_up_vector(up_axis)
        orient.run()

    if not children:
        cmds.makeIdentity(joint, jo=True, apply=True)


def orient_x_to_child_up_to_surface(joint, invert=False, surface=None):
    """
    Function that orients given joint to its child (points X axis of joint to its child) and tryis to orient the
    up axis to the normal of the given surface
    :param joint: str
    :param invert: bool
    :param surface: str
    """

    aim_axis = [1, 0, 0] if not invert else [-1, 0, 0]
    up_axis = [0, 1, 0] if not invert else [0, -1, 0]
    children = cmds.listRelatives(joint, type='transform')
    if children:
        orient = OrientJoint(joint, children)
        orient.set_surface(surface)
        orient.set_aim_at(3)
        orient.set_aim_up_at(6)
        orient.set_aim_vector(aim_axis)
        orient.set_up_vector(up_axis)
        orient.run()

    if not children:
        cmds.makeIdentity(joint, jo=True, apply=True)


def flip_orient(joint, target=None, axis='x'):
    """
    Flips the given joint orient across the given axis
    Flipped orientation will be applied to target joint or to original one if target is not specified
    :param joint: str, joint to flip orientation of
    :param target: str or None, joint to apply flipped orientation to
    :param axis: str, axis to flip orientation across
    """

    check_joint(joint)

    rad_to_deg = 100.0 / math.pi

    if not target:
        target = joint

    joint_matrix = transform.get_matrix(joint)

    # Build flip matrix
    flip_matrix = None
    if axis == 'x':
        flip_matrix = matrix_utils.build_matrix(x_axis=(-1, 0, 0))
    if axis == 'y':
        flip_matrix = matrix_utils.build_matrix(x_axis=('', -1, 0))
    if axis == 'z':
        flip_matrix = matrix_utils.build_matrix(x_axis=(0, 0, -1))

    target_matrix = OpenMaya.MTransformationMatrix(joint_matrix * flip_matrix.inverse())
    flip_rotation = target_matrix.eulerRotation()
    flip_rotation_list = (flip_rotation.x * rad_to_deg, flip_rotation.y * rad_to_deg, flip_rotation.z * rad_to_deg)
    cmds.setAttr('{}.jo'.format(target), *flip_rotation_list)

    return flip_rotation_list


def mirror_orient(joint, roll_axis):
    """
    Reorients joint to replicate mirrored behaviour
    :param joint: str, joint to mirror orientation for
    :param roll_axis: str, axis to maintain orientation for
    """

    check_joint(joint)

    if not ['x', 'y', 'z'].count(roll_axis):
        raise Exception('Invalid roll axis "{}"!'.format(roll_axis))

    # Unparent children
    child_list = cmds.listRelatives(joint, c=True)
    if child_list:
        cmds.parent(child_list, world=True)

    # Reorient joint
    rotation_list = [0, 0, 0]
    axis_dict = {'x': 0, 'y': 1, 'z': 2}
    rotation_list[axis_dict[roll_axis]] = 180
    cmds.setAttr('{}.r'.format(joint), *rotation_list)
    cmds.makeIdentity(joint, apply=True, t=True, r=True, s=True)

    # Reparent children
    if child_list:
        cmds.parent(child_list, joint)


def start_joint_tool():
    """
    Initializes Maya joint creation tool
    """

    cmds.JointTool()


def set_joint_local_rotation_axis_visibility(joints=None, bool_value=None):
    """
    Sets the joint visibility of the given node or given nodes
    :param joints: list<str>, list of joints to set axis visibility of. If None, given, all joints of the scene
        will be used
    :param bool_value: bool, value of the local rotation axis visibility. If None given, current joint visibility
        will be toggled
    :return:
    """

    if joints is None:
        joints = cmds.ls(type='joint')
    else:
        joints = helpers.force_list(joints)

    for jnt in joints:
        if bool_value is None:
            new_value = not cmds.getAttr('{}.displayLocalAxis'.format(jnt))
        else:
            new_value = bool_value
        cmds.setAttr('{}.displayLocalAxis'.format(jnt), new_value)

    return True


def connect_inverse_scale(joint, inverse_scale_object=None, force=False):
    """
    Connects joints inverseScale attribute
    :param joint: str, joint to connect inverseScale for
    :param inverse_scale_object: str, object to connect to joint inverseScale attribute. If None, joint parent is use.
    :param force: bool, Whether to force the connection or not
    """

    check_joint(joint)

    # Get inverse scale object if not given
    if not inverse_scale_object or not cmds.objExists(inverse_scale_object):
        parent = cmds.listRelatives(joint, p=True) or list()
        if parent and force:
            parent = cmds.ls(parent, type='joint') or list()
        if not parent:
            logger.warning(
                'No source object specified and no parent joint found for joint "{}". Skipping connection ...'.format(
                    joint))
            return None
        inverse_scale_object = parent[0]

    # Connect inverse scale
    inverse_scale_connections = cmds.listConnections('{}.inverseScale'.format(joint), s=True, d=False) or list()
    if inverse_scale_object not in inverse_scale_connections:
        try:
            cmds.connectAttr('{}.scale'.format(inverse_scale_object), '{}.inverseScale'.format(joint), f=True)
        except Exception as exc:
            logger.error(
                'Error connection "{}.scale" to "{}.inverseScale! {}'.format(inverse_scale_object, joint, exc))
            return None

    return '{}.scale'.format(inverse_scale_object)


@decorators.undo
def create_joint_at_points(points, name, joint_radius=1.0):
    """
    Creates a new joint in the middle center of the given points. If only 1 point is given, the joint
    will be created in the same exact position of the point
    :param points: list(float, float, float), list of points
    :param name: str, name for the new joint
    :return: str, newly created joint
    """

    pos = transform.get_center(points)
    cmds.select(clear=True)
    joint = cmds.joint(n=name_utils.find_unique_name('joint_{}'.format(name)), p=pos, radius=joint_radius)

    return joint


@decorators.undo
def create_joints_on_cvs(curve, parented=True):
    """
    Creates a joint in each CV of the given curve.
    :param curve: str, name of the curve
    :param parented: bool, Whether or not, joints should be parented under the last joint created at the previous CV
    :return: list(str), list of created joints
    """

    joints = list()
    last_joint = None

    cvs = cmds.ls('{}.cv[*]'.format(curve), flatten=True)
    cmds.select(clear=True)

    for i, cv in enumerate(cvs):
        position = cmds.pointPosition(cv)
        if not parented:
            cmds.select(clear=True)
        joint = cmds.joint(n=name_utils.find_unique_name('joint_{}'.format(curve)), p=position)
        joints.append(joint)
        if last_joint and parented:
            cmds.joint(last_joint, e=True, zso=True, oj='xyz', sao='yup')
        last_joint = joint

    return joints


@decorators.undo
def create_joints_on_faces(mesh, faces=None, follow=True, name=None):
    """
    Creates joints on the faces of the given mesh
    :param mesh: str, name of a mesh
    :param faces: list(str), list of faces ids to create joints on. If not given, new joints will be created in all
        geometry faces
    :param follow: bool, Whether or not joints should follow faces
    :param name: str, name to apply to created joints
    :return: list(str) or list(str, str): List of created joints if follow is False or list of created joints and list
        of created follicles if follow is True
    """

    from tp.maya.cmds import rivet as rivet_utils, geometry as geo_utils

    centers = list()
    face_ids = list()
    joints = list()
    follicles = list()

    mesh = geo_utils.get_mesh_shape(mesh)

    if faces:
        for face in faces:
            if helpers.is_string(face):
                sub_faces = cmds.ls(face, flatten=True)
                for sub_face in sub_faces:
                    id_value = python_name.get_last_number(sub_face)
                    face_ids.append(id_value)
            elif type(face) == int:
                face_ids.append(face)

    if face_ids:
        for face_id in face_ids:
            center = geo_utils.get_face_center(mesh, face_id)
            centers.append(center)
    else:
        centers = geo_utils.get_face_centers(mesh)

    for center in centers:
        cmds.select(clear=True)
        name = name if name else 'joint_mesh_1'
        joint = cmds.joint(p=center, n=name_utils.find_unique_name(name))
        joints.append(joint)
        if follow:
            follicle = rivet_utils.attach_to_mesh(joint, mesh, hide_shape=True, constraint=False, rotate_pivot=True)
            follicles.append(follicle)

    if follicles:
        return joints, follicles

    return joints


@decorators.undo
def create_joint_on_center():
    """
    Creates a new joint on center of the selected objects or components
    """

    selection = cmds.ls(sl=True)
    if not selection:
        return cmds.joint(n='joint#')

    # if cmds.objectType(selection[0]) != 'mesh':
    #     raise NotImplementedError('Center to selected objects not implemented yet')

    bounding = transform.BoundingBox(selection)
    center_point = bounding.get_center()

    cmds.select(clear=True)

    new_joint = cmds.joint(n='joint#', p=center_point)

    return new_joint


@decorators.undo
def create_joints_on_selected_components_center():
    """
    Creates joints on current selected components (vertices, faces or edges) center
    :return:
    """

    created_joints = list()

    selected_components = cmds.ls(sl=True)
    if not selected_components:
        return created_joints

    if dcc.node_is_curve(selected_components[0]):
        return create_joints_on_cvs(curve=selected_components[0], parented=False)

    if cmds.objectType(selected_components[0]) != 'mesh':
        return created_joints

    sel_list = list()
    obj_name = selected_components[0][0:selected_components[0].index('.')]
    for comp in selected_components:
        comp_split = comp.split(':')
        c = ':'.join(comp_split[1:])

        if ':' not in c:
            sel_list.append(comp)
        else:
            start_component = int(c[c.index('[') + 1:c.index(':')])
            end_component = int(c[c.index(':') + 1:c.index(']')])
            component_type = c[c.index('.') + 1:c.index('[')]
            while start_component <= end_component:
                sel_list.append('{}.{}[{}]'.format(obj_name, component_type, start_component))
                start_component += 1
    if not sel_list:
        return False

    component_centers = list()
    component_type = sel_list[0][sel_list[0].index('.') + 1:sel_list[0].index('[')]

    if component_type == 'f' or component_type == 'e':
        for comp in sel_list:
            pos = cmds.xform(comp, query=True, t=True, ws=True)
            component_centers.append([
                sum(pos[0::3]) / len(pos[0::3]),
                sum(pos[1::3]) / len(pos[1::3]),
                sum(pos[2::3]) / len(pos[2::3])]
            )
            for loc in component_centers:
                cmds.select(clear=True)
                created_joints.append(cmds.joint(n='joint#', p=loc, rad=0.25))
    else:
        for comp in sel_list:
            cmds.select(clear=True)
            created_joints.append(cmds.joint(n='joint#', p=cmds.pointPosition(comp), rad=0.25))

    cmds.select(clear=True)

    return created_joints


@decorators.undo
def create_oriented_joints_along_curve(curve, count=20, description='curve', attach=False):
    """
    Create joints on curve that are oriented to aim at child
    :param curve: str, name of a curve
    :param count: int, number of joints to create
    :param description: str, description for the new created joints
    :param attach: bool, Whether to attach the joints to the curve or not
    :return: list(str), list of created joints
    """

    if count < 2:
        return

    new_joints = list()

    cmds.select(clear=True)

    total_length = cmds.arclen(curve)
    start_joint = cmds.joint(n='joint_{}Start'.format(description))
    end_joint = cmds.joint(p=[total_length, 0, 0], n='joint_{}End'.format(description))
    if count > 3:
        count = count - 2

    joints = subdivide_joint(start_joint, end_joint, count, prefix='joint', name=description)
    joints.insert(0, start_joint)
    joints.append(end_joint)
    for joint in joints:
        new_joints.append(joint)
    #     new_joints.append(cmds.rename(joint, name_utils.find_unique_name('joint_{}_1'.format(curve))))

    ik = ik_utils.IkHandle(curve)
    ik.set_start_joint(new_joints[0])
    ik.set_end_joint(new_joints[-1])
    ik.set_solver(ik.SOLVER_SPLINE)
    ik.set_curve(curve)
    ik_handle = ik.create()
    cmds.setAttr('{}.dTwistControlEnable'.format(ik_handle), 1)
    cmds.refresh()
    if not attach:
        cmds.delete(ik_handle)
        cmds.makeIdentity(new_joints[0], apply=True, r=True)

    return new_joints


def create_joint_along_curve_in_intersection_curves(
        curve, intersect_curves_list, joint_at_base=True, joint_at_tip=True, use_direction=False,
        intersect_direction=(0, 0, 0), prefix=''):
    """
    Creates joints along a curves at the point of intersection with a list of secondary curves
    :param curve: str, curve to create joint along
    :param intersect_curves_list: list, list of intersection curves
    :param joint_at_base: bool, creates a joint at the base of the curve
    :param joint_at_tip: bool, creates a joint at the tip of the curve
    :param use_direction: bool, project the curves in a given direction before intersecting
    :param intersect_direction: tuple or list, the direction to project the curves before intersecting
    :param prefix: str, name prefix for newly created joints
    :return: list(str), list of new created joints
    """

    if not cmds.objExists(curve):
        raise Exception('Curve object "{}" does not exist!'.format(curve))
    for i in range(len(intersect_curves_list)):
        if not cmds.objExists(intersect_curves_list[i]):
            raise Exception('Object "{}" does not exist!'.format(intersect_curves_list[i]))

    if not prefix:
        prefix = strings.strip_suffix(curve)

    # Get curve range
    min_u = cmds.getAttr('{}.minValue'.format(curve))
    max_u = cmds.getAttr('{}.maxValue'.format(curve))

    cmds.select(clear=True)
    joint_list = list()

    # TODO: We should use nameit library to rename new joints
    joint_name_format = '{}_new{}_jnt'

    # Create base joint if necessary
    if joint_at_base:
        pos = cmds.pointOnCurve(curve, pr=min_u, p=True)
        joint_index = '01'
        new_joint_name = joint_name_format.format(prefix, joint_index)
        new_joint = cmds.joint(p=pos, n=new_joint_name)
        joint_list.append(new_joint)

    # Create joints at curve intersections
    for n in range(len(intersect_curves_list)):
        joint_index = str(n + 1 + int(joint_at_base))
        if i < (9 - int(joint_at_base)):
            joint_index = '0{}'.format(joint_index)
        u_list = cmds.curveIntersect(curve, intersect_curves_list[n], ud=use_direction, d=intersect_direction)
        if not u_list:
            continue
        u_list = u_list.split(' ')
        for u in range(int(len(u_list) / 2)):
            pos = cmds.pointOnCurve(curve, pr=float(u_list[u * 2]), p=True)
            new_joint_name = joint_name_format.format(prefix, joint_index)
            new_joint = cmds.joint(p=pos, n=new_joint_name)
            joint_list.append(new_joint)

    # Create tip joint
    if joint_at_tip:
        joint_index = str(len(intersect_curves_list) + int(joint_at_base) + 1)
        if len(intersect_curves_list) < (9 - int(joint_at_base)):
            joint_index = '0{}'.format(joint_index)

        pos = cmds.pointOnCurve(curve, pr=max_u, p=True)
        new_joint_name = joint_name_format.format(prefix, joint_index)
        new_joint = cmds.joint(p=pos, n=new_joint_name)
        joint_list.append(new_joint)

    return joint_list


def create_joint_buffer(joint, connect_inverse=True):
    """
    Creates a joint buffer on top of the given joint
    :param joint: str
    :param connect_inverse: bool, Whether to connect new buffer joint inverseScale to source joint parent node
    """

    cmds.select(clear=True)

    # Create buffer joint and make sure that it has same translation and rotation than the source joint
    buffer_joint = cmds.joint(n='{}_bufferJoint'.format(joint))
    cmds.setAttr('{}.drawStyle'.format(buffer_joint), 2)
    transform.MatchTransform(joint, buffer_joint).translation_rotation()

    # Parent buffer joint to source joint parent node (if exists)
    parent = cmds.listRelatives(joint, p=True, f=True)
    if parent:
        parent = parent[0]
        cmds.parent(buffer_joint, parent)
        if connect_inverse:
            if not cmds.isConnected('{}.scale'.format(parent), '{}.inverseScale'.format(buffer_joint)):
                cmds.connectAttr('{}.scale'.format(parent), '{}.inverseScale'.format(buffer_joint))

    # Parent source joint to new created buffer joint
    cmds.parent(joint, buffer_joint)

    return buffer_joint


@decorators.undo
def insert_joints(joints=None, joint_count=1):
    """
    Inserts joints evenly spaced along a bone
    :param list(str) joints: list of joints to insert child joints to
    :param int joint_count: Number of joints to insert
    :return: List of created joints
    :rtype: list(str)
    """

    if joints is None:
        joints = cmds.ls(sl=True, type='joint')
        if not joints:
            logger.warning('No joint selected')
            return
    if joint_count < 1:
        logger.warning('Must insert at least 1 joint')
        return

    result = list()

    for joint in joints:
        children = cmds.listRelatives(joint, children=True, type='joint', fullPath=True)
        if not children:
            logger.warning('Joint "{}" needs at least a child in order to insert joints. Skipping!'.format(joint))
            continue

        name = joint
        end_joint = children[0]
        dst = mathlib.distance_between_nodes(joint, end_joint)
        increment = dst / (joint_count + 1)
        direction = mathlib.direction_vector_between_nodes(joint, end_joint)
        direction.normalize()
        direction *= increment

        for i in range(joint_count):
            position = OpenMaya.MPoint(*cmds.xform(joint, query=True, worldSpace=True, translation=True))
            position += direction
            joint = cmds.insertJoint(joint)
            joint = cmds.rename(joint, '{}#'.format(name))
            cmds.joint(joint, edit=True, component=True, position=(position.x, position.y, position.z))
            result.append(joint)

    return result


@decorators.undo
def subdivide_joint(joint1=None, joint2=None, count=1, prefix='joint', name='sub_1', duplicate=False):
    """
    Adds evenly spaced joints between joint1 and joint2
    :param joint1: str, first joint. If None, first selected joint will be used
    :param joint2: str, second joint. If None, second selected joint will be used
    :param count: int, number of joints to add inbetween joint1 and joint2
    :param prefix: str, prefix to add in front of the new joints
    :param name: str name to give t othe new joints after the prefix.
    :param duplicate: bool, Whether or not to create a duplicate chain and keep the original chain intact
    :return: list(str), list of newly created joints
    """

    if not joint1 and not joint2:
        selection = cmds.ls(sl=True)
        if cmds.nodeType(selection[0]) == 'joint':
            joint1 = selection[0]
        if len(selection) > 1:
            if cmds.nodeType(selection[1]) == 'joint':
                joint2 = selection[1]
    if joint1 and not joint2:
        joint_relatives = cmds.listRelatives(joint1, type='joint')
        if joint_relatives:
            joint2 = joint_relatives[0]
    if not joint1 and not joint2:
        return

    joints = list()
    top_joint = joint1
    last_joint = None
    bottom_joint = joint2
    radius = cmds.getAttr('{}.radius'.format(joint1))
    vector1 = cmds.xform(joint1, query=True, worldSpace=True, translation=True)
    vector2 = cmds.xform(joint2, query=True, worldSpace=True, translation=True)
    name = '{}_{}'.format(prefix, name)
    offset = 1.00 / (count + 1)
    value = offset

    if duplicate:
        cmds.select(clear=True)
        top_joint = cmds.joint(p=vector1, n=name_utils.find_unique_name(name), r=radius + 1)
        joints.append(top_joint)
        match = transform.MatchTransform(joint1, top_joint)
        match.rotation()
        cmds.makeIdentity(top_joint, apply=True, r=True)

    for i in range(count):
        position = vec3.get_inbetween_vector(vector1, vector2, value)
        cmds.select(clear=True)
        joint = cmds.joint(p=position, n=name_utils.find_unique_name(name), r=radius)
        cmds.setAttr('{}.radius'.format(joint), radius)
        joints.append(joint)
        value += offset
        if i == 0:
            cmds.parent(joint, top_joint)
            cmds.makeIdentity(joint, apply=True, jointOrient=True)
        if last_joint:
            cmds.parent(joint, last_joint)
            cmds.makeIdentity(joint, apply=True, jointOrient=True)
            if not cmds.isConnected('{}.scale'.format(last_joint), '{}.inverseScale'.format(joint)):
                cmds.connectAttr('{}.scale'.format(last_joint), '{}.inverseScale'.format(joint))
        last_joint = joint

    if duplicate:
        cmds.select(clear=True)
        bottom_joint = cmds.joint(p=vector2, n=name_utils.find_unique_name(name), r=radius + 1)
        joints.append(bottom_joint)
        match = transform.MatchTransform(joint1, bottom_joint)
        match.rotation()
        cmds.makeIdentity(bottom_joint, apply=True, r=True)

    cmds.parent(bottom_joint, joint)

    if not cmds.isConnected('{}.scale'.format(joint), '{}.inverseScale'.format(bottom_joint)):
        cmds.connectAttr('{}.scale'.format(joint), '{}.inverseScale'.format(bottom_joint))

    return joints


def get_joints_chain_length(list_of_joints_in_chain):
    """
    Return the total distance of a of joints chain
    :param list_of_joints_in_chain: list(str)
    :return: float
    """

    length = 0
    joint_count = len(list_of_joints_in_chain)
    for i in range(joint_count):
        if i + 1 == joint_count:
            break
        current_joint = list_of_joints_in_chain[i]
        next_joint = list_of_joints_in_chain[i + 1]
        distance = transform.get_distance(current_joint, next_joint)
        length += distance

    return length


@decorators.undo
def create_oriented_joints_on_curve(curve, count=20, description=None, attach=False):
    """
    Create joints on curve that are oriented to aim at child
    :param curve: str, name of the curve
    :param count: int, number of joints
    :param description: str, description to given to the newly created joints
    :param attach: bool, Whether to attach or not the joints to the curve
    :return: list(str), list of names of the created joints
    """

    created_joints = list()

    description = description or 'curve'
    if count < 2:
        logger.info('A joint chain need to have at least 2 joints')
        return created_joints
    if count < 3:
        count = count - 2

    length = cmds.arclen(curve, ch=False)
    cmds.select(clear=True)
    start_joint = cmds.joint(n='joint_{}Start'.format(description))
    end_joint = cmds.joint(p=[length, 0, 0], n='joint_{}End'.format(description))
    joints = subdivide_joint(start_joint, end_joint, count=count, prefix='joint', name=description)
    joints.insert(0, start_joint)
    joints.append(end_joint)

    for joint in joints:
        created_joints.append(cmds.rename(joint, name_utils.find_unique_name('joint_{}_1'.format(curve))))

    ik = ik_utils.IkHandle(curve)
    ik.set_start_joint(created_joints[0])
    ik.set_end_joint(created_joints[-1])
    ik.set_solver(ik_utils.IkHandle.SOLVER_SPLINE)
    ik.set_curve(curve)
    ik_handle = ik.create()
    cmds.setAttr('{}.dTwistControlEnable'.format(ik_handle), True)
    cmds.refresh()
    if not attach:
        cmds.delete(ik_handle)
        cmds.makeIdentity(created_joints[0], apply=True, r=True)

    return created_joints


def check_joint_labels(joints=None):
    """
    Checks whether all given joints have labels applied
    :param joints: list(str)
    :return: bool
    """

    from tp.maya.cmds import skin

    joints = joints or cmds.ls(sl=True, type='joint')
    joints = helpers.force_list(joints)
    if not joints:
        meshes = list()
        transforms = dcc.selected_nodes_of_type('transform')
        if transforms:
            for xform in transforms:
                shapes = dcc.list_shapes_of_type(xform, 'mesh')
                if not shapes:
                    continue
                meshes.extend(shapes)
        if meshes:
            for mesh in meshes:
                influences = skin.get_influencing_joints(mesh) or list()
                joints.extend(influences)
    if not joints:
        return False
    joints = list(set(joints))

    if cmds.getAttr('{}.type'.format(joints[random.randint(0, len(joints) - 1)])) == 0:
        return False

    return True


@decorators.undo
def auto_label_joints(joints=None, input_left='*_l_*', input_right='*_r_*'):
    """
    Automatically adds labels to given joints
    :param joints: list(str) or None, list of joints to set labels of. If not given, selected joints will be used.
    :param input_left: str, string to identify all joints that are on the left side
    :param input_right: str, string to identify all joints that are on the right side
    """

    def _set_attrs(side, joint_type, name):
        try:
            cmds.setAttr('{}.side'.format(joint), lock=0)
            cmds.setAttr('{}.type'.format(joint), lock=0)
            cmds.setAttr('{}.otherType'.format(joint), lock=0)
            cmds.setAttr('{}.drawLabel'.format(joint), lock=0)
        except Exception:
            pass

        cmds.setAttr('{}.side'.format(joint), side)
        cmds.setAttr('{}.type'.format(joint), joint_type)
        cmds.setAttr('{}.otherType'.format(joint), name, type='string')
        cmds.setAttr('{}.drawLabel'.format(joint), 1)

    all_joints = joints or cmds.ls(sl=True, type='joint') or cmds.ls(type='joint')
    all_found_joints = all_joints[:]
    if not all_joints:
        return False

    percentage = 99.0 / len(all_joints)
    progress_value = 0.0

    if '*' not in input_left:
        input_left = '*{}*'.format(input_left)
    if '*' not in input_right:
        input_right = '*{}*'.format(input_right)

    left_joints = cmds.ls(str(input_left), type='joint')
    right_joints = cmds.ls(str(input_right), type='joint')

    for i, joint in enumerate(left_joints):
        _set_attrs(1, 18, str(joint).replace(str(input_left).strip('*'), ''))
        if joint not in all_joints:
            continue
        all_joints.remove(joint)
        progress_value += ((i + 1) * percentage)

    for j, joint in enumerate(right_joints):
        _set_attrs(2, 18, str(joint).replace(str(input_right).strip('*'), ''))
        if joint not in all_joints:
            continue
        all_joints.remove(joint)
        progress_value += (j * percentage)

    for k, joint in enumerate(all_joints):
        _set_attrs(0, 18, str(joint))
        progress_value += (k * percentage)

    for joint in all_found_joints:
        cmds.setAttr('{}.drawLabel'.format(joint), 0)

    progress_value = 100

    return True


@decorators.undo
def auto_assign_labels_to_mesh_influences(skinned_mesh, input_left=None, input_right=None, check_labels=True):
    """
    Auto assigns labels to all joint influences of the given skinned mesh
    :param skinned_mesh: str or list(str)
    :param check_labels: bool
    """

    from tp.maya.cmds import skin

    skinned_mesh = skinned_mesh or dcc.selected_nodes_of_type('transform')
    skinned_mesh = helpers.force_list(skinned_mesh)
    if not skinned_mesh:
        return False

    input_left = input_left or '*_l_*'
    input_right = input_right or '*_r_*'

    all_joints = list()
    all_shapes = list()
    for mesh in skinned_mesh:
        if dcc.node_type(mesh) == 'mesh':
            all_shapes.append(mesh)
        else:
            target_shapes = dcc.list_shapes_of_type(mesh, 'mesh')
            if target_shapes:
                all_shapes.append(target_shapes[0])
    if not all_shapes:
        return False

    for shape in all_shapes:
        influences = skin.get_influencing_joints(shape) or list()
        all_joints.extend(influences)

    if not all_joints:
        return False

    if check_labels:
        if check_joint_labels(all_joints):
            return True

    success = auto_label_joints(all_joints, input_left=input_left, input_right=input_right)

    return success


class BuildJointHierarchy(object):
    def __init__(self):
        self._transforms = list()
        self._replace_old = None
        self._replace_new = None

    def create(self):
        """
        Creates the new joint hierarchy
        :return: list<str>
        """

        new_joints = self._build_hierarchy()

        return new_joints

    def set_transforms(self, transform_list):
        """
        Set the list of transform that we need to create joint hierarchy for
        :param transform_list: list<str>
        """

        self._transforms = transform_list

    def set_replace(self, old, new):
        """
        Replace the naming in the new joints
        :param old: str, string in the duplicate name to replace
        :param new: str, string in the duplicate to replace with
        """

        self._replace_old = old
        self._replace_new = new

    def _build_hierarchy(self):
        new_joints = list()
        last_transform = None
        for xform in self._transforms:
            cmds.select(clear=True)
            joint = cmds.joint()
            name = xform
            if self._replace_old and self._replace_new:
                for old_name, replace_name in zip(self._replace_old, self._replace_new):
                    if old_name in name:
                        name = name.replace(old_name, replace_name)
                        break
                    else:
                        name = '{}_{}'.format(name, replace_name)
                joint = cmds.rename(joint, name_utils.find_unique_name(name))
            transform.MatchTransform(xform, joint).translation_rotation()
            transform.MatchTransform(xform, joint).world_pivots()
            cmds.makeIdentity(joint, r=True, apply=True)
            new_joints.append(joint)
            if last_transform:
                cmds.parent(joint, last_transform)
            last_transform = joint

        return new_joints


class AttachJoints(object):
    """
    Attaches a chain of joints to a matching chain using parent and scale constraints
    """

    class AttachType(object):
        CONSTRAINT = 0
        MATRIX = 1

        @staticmethod
        def get_string_list():
            """
            Returns a list with the attach types as strings
            :return: list<str>
            """

            return ['Constraint', 'Matrix']

    def __init__(
            self, source_joints, target_joints, create_switch=True, switch_node=None, switch_attribute_name='switch'):
        self._source_joints = source_joints
        self._target_joints = target_joints
        self._create_switch = create_switch
        self._switch_node = switch_node
        self._switch_attribute_name = switch_attribute_name
        self._attach_type = AttachJoints.AttachType.CONSTRAINT
        self._remap_nodes = list()

    @property
    def remap_nodes(self):
        return self._remap_nodes

    def create(self):
        """
        Creates the attachments
        """

        self._attach_joints(self._source_joints, self._target_joints)

    def set_source_and_target_joints(self, source_joints, target_joints):
        """
        :param source_joints: list<str>, list of joint names that should move the target
        :param target_joints: list<str>, list of joint names that should be moved by the source
        """

        self._source_joints = source_joints
        self._target_joints = target_joints

    def set_attach_type(self, attach_type):
        self._attach_type = attach_type

    def set_create_switch(self, flag):
        self._create_switch = flag

    def set_switch_attribute_name(self, attribute_name):
        self._switch_attribute_name = attribute_name

    def _hook_scale_constraint(self, node):
        cns = cns_utils.Constraint()
        scale_cns = cns.get_constraint(node, cns_utils.Constraints.SCALE)
        if not scale_cns:
            return
        cns_utils.scale_constraint_to_world(scale_cns)

    def _unhook_scale_constraint(self, scale_constraint):
        cns_utils.scale_constraint_to_local(scale_constraint)

    def _attach_joint(self, source_joint, target_joint):
        if self._attach_type == AttachJoints.AttachType.CONSTRAINT:
            self._hook_scale_constraint(target_joint)
            parent_cns = cmds.parentConstraint(source_joint, target_joint, mo=True)[0]
            cmds.setAttr('{}.interpType'.format(parent_cns), 2)
            scale_cns = cmds.scaleConstraint(source_joint, target_joint)[0]
            if self._create_switch:
                cns = cns_utils.Constraint()
                cns.create_switch(self._target_joints[0], self._switch_attribute_name, parent_cns)
                cns.create_switch(self._target_joints[0], self._switch_attribute_name, scale_cns)
                self._remap_nodes.extend(cns.remaps)
            self._unhook_scale_constraint(scale_cns)
        elif self._attach_type == AttachJoints.AttachType.MATRIX:
            switches = cns_utils.SpaceSwitch().get_space_switches(target_joint)
            if switches:
                cns_utils.SpaceSwitch().add_source(source_joint, target_joint, switches[0])
                if self._create_switch:
                    cns_utils.SpaceSwitch().create_switch(
                        self._target_joints[0], self._switch_attribute_name, switches[0])
            else:
                switch = cns_utils.SpaceSwitch(source_joint, target_joint)
                switch.set_use_weight(True)
                switch_node = switch.create()
                if self._create_switch:
                    switch.create_switch(self._target_joints[0], self._switch_attribute_name, switch_node)

    def _attach_joints(self, source_chain, target_chain):
        for i in range(len(source_chain)):
            self._attach_joint(source_chain[i], target_chain[i])


class OrientJointAttributes(object):
    """
    Creates attributes on a node that can be used with OrientAttributes
    """

    def __init__(self, joint):
        """
        Constructor
        :param joint: str, name of the joint we want to create orient attributes to
        """

        self.joint = None
        self.attributes = list()
        self.title = None

        if is_joint(joint) or transform.is_transform(joint):
            self.joint = joint
            self._create_attributes()

    @staticmethod
    @decorators.undo
    def add_orient_attributes(obj):
        """
        Adds orient attributes to the given joint node
        :param obj: str, name of a valid joint node
        """

        if type(obj) is not list:
            obj = [obj]

        for o in obj:
            if not is_joint(o) and not transform.is_transform(o):
                continue
            ori = OrientJointAttributes(joint=o)
            ori.set_default_values()

    @staticmethod
    @decorators.undo
    def zero_orient_joint(joint):
        """
        Move orientation to orient joint attributes and zero out orient attributes from the given joint node
        :param joint: str, name of valid joint node
        """

        joint = helpers.force_list(joint)

        for jnt in joint:
            if not is_joint(jnt):
                continue
            for axis in 'XYZ':
                rotate_value = cmds.getAttr('{}.rotate{}'.format(jnt, axis))
                cmds.setAttr('{}.rotate{}'.format(jnt, axis), 0)
                cmds.setAttr('{}.jointOrient{}'.format(jnt, axis), rotate_value)

        return True

    @staticmethod
    @decorators.undo
    def remove_orient_attributes(joint):
        """
        Removes orient attributes from the given joint node
        :param joint: str, name of valid joint node
        """

        joint = helpers.force_list(joint)
        for jnt in joint:
            if not is_joint(jnt):
                continue
            ori = OrientJointAttributes(joint=jnt)
            ori.delete()

    @classmethod
    @decorators.undo
    def orient_with_attributes(cls, objects_to_orient=None, force_orient_attributes=False):
        """
        Orients all joints and transforms with OrientJointAttribute added on them
        :param objects_to_orient: list<str>, if given, only given objects will be oriented
        :param force_orient_attributes: bool, Whether or not to force the creation of the orient attributes
        """

        if not objects_to_orient:
            objects_to_orient = scene.get_top_dag_nodes()

        logger.debug('Orienting {}'.format(objects_to_orient))

        oriented = False
        for obj in objects_to_orient:
            relatives = cmds.listRelatives(obj, f=True)
            if not cmds.objExists('{}.ORIENT_INFO'.format(obj)):
                if force_orient_attributes:
                    cls.add_orient_attributes(obj)
                else:
                    if relatives:
                        cls.orient_with_attributes(
                            objects_to_orient=relatives, force_orient_attributes=force_orient_attributes)
                        oriented = True
                    continue

            if cmds.nodeType(obj) in ['joint', 'transform']:
                orient = OrientJoint(joint_name=obj)
                orient.run()
                if relatives:
                    cls.orient_with_attributes(
                        objects_to_orient=relatives, force_orient_attributes=force_orient_attributes)
                    oriented = True

        return oriented

    def set_joint(self, joint):
        """
        Set a joint to create attributes on
        :param joint: str, name of the joint
        """

        if not is_joint(joint):
            return

        self.joint = joint

        self._create_attributes()

    def get_values(self):
        """
        Returns all orient settings attributes as a dictionary
        :return: dict
        """

        values_dict = dict()
        for attr in self.attributes:
            values_dict[attr.name()] = attr.get_value()

        return values_dict

    def set_values(self, value_dict):
        """
        Set joint orient attributes by the values stored in the given dictionary (get_values()
        function generates that dict)
        :param value_dict: dict
        """

        for attr in self.attributes:
            attr.set_value(value_dict[attr.name()])

    def set_default_values(self):
        """
        Set all joint orient axis to their default values
        """

        for attr in self.attributes:
            attr.set_default_value()

    def delete(self):
        """
        Removes all joint orient attributes (created on _create_attribute() function)
        """

        if self.title:
            self.title.delete()

        for attr in self.attributes:
            attr.delete()

    def _create_attributes(self):
        """
        Internal function that creates joint orient attributes
        """

        self.title = attribute.EnumAttribute('Orient_Info'.upper())
        if not cmds.objExists('{}.ORIENT_INFO'.format(self.joint)):
            self.title.create(self.joint)
            self.title.set_locked(True)
        else:
            self.title.set_node(self.joint)

        self.attributes.append(attribute.create_axis_attribute(name='aimAxis', node=self.joint, value=0))
        self.attributes.append(attribute.create_axis_attribute(name='upAxis', node=self.joint, value=1))
        self.attributes.append(attribute.create_axis_attribute(name='worldUpAxis', node=self.joint, value=1))

        aim_at_attr = attribute.EnumAttribute('aimAt', value=3)
        aim_at_attr.set_enum_names(['worldX', 'worldY', 'worldZ', 'child', 'parent', 'localParent'])
        aim_at_attr.create(self.joint)
        self.attributes.append(aim_at_attr)

        aim_up_attr = attribute.EnumAttribute('aimUpAt', value=0)
        aim_up_attr.set_node(self.joint)
        aim_up_attr.set_enum_names(['world', 'parentRotate', 'childPosition', 'trianglePlane', '2ndChildPosition'])
        aim_at_attr.create(self.joint)
        self.attributes.append(aim_up_attr)

        self.attributes.append(attribute.create_triangle_attribute(name='triangleTop', node=self.joint, value=1))
        self.attributes.append(attribute.create_triangle_attribute(name='triangleMid', node=self.joint, value=2))
        self.attributes.append(attribute.create_triangle_attribute(name='triangleBottom', node=self.joint, value=3))

        invert_scale_attr = attribute.EnumAttribute('invertScale')
        invert_scale_attr.set_enum_names(['none', 'X', 'Y', 'Z', 'XY', 'XZ', 'YZ'])
        invert_scale_attr.set_locked(False)
        invert_scale_attr.create(self.joint)
        self.attributes.append(invert_scale_attr)

        active_attr = attribute.NumericAttribute('active', value=1)
        active_attr.set_variable_type(attribute.AttributeTypes.Bool)
        active_attr.set_keyable(True)
        active_attr.create(self.joint)
        self.attributes.append(active_attr)


class OrientJoint(object):
    """
    Orient the joint using attributes created with OrientJointAttributes
    """

    def __init__(self, joint_name, children=None):
        """
        Constructor
        :param joint_name: str, name of the joint we want to orient
        """

        self._joint = joint_name
        self._orient_values = None
        self._aim_vector = [1, 0, 0]
        self._up_vector = [0, 1, 0]
        self._world_up_vector = [0, 1, 0]

        self._aim_at = 3
        self._aim_up_at = 0

        self._children = children or list()
        self._child = None
        self._child2 = None
        self._grand_child = None
        self._parent = None
        self._grand_parent = None
        self._surface = None
        self._delete_later = list()
        self._world_up_vector = self.get_vector_from_axis(1)
        self._up_space_type = 'vector'

        self._get_relatives()

    @staticmethod
    def get_vector_from_axis(axis_index):
        """
        Returns vector from the given axis type
        :param axis_index: int
        :return: list<int, int, int>
        """

        vectors = [[1, 0, 0],
                   [0, 1, 0],
                   [0, 0, 1],
                   [-1, 0, 0],
                   [0, -1, 0],
                   [0, 0, -1],
                   [0, 0, 0]]

        return vectors[axis_index]

    def set_aim_vector(self, vector_list):
        """
        Set the aim vector for the orient process
        :param vector_list: list<float, float, float>, vector that defines what axis should aim
        """

        self._aim_vector = vector_list

    def set_up_vector(self, vector_list):
        """
        Set the up vector for the orient process
        :param vector_list: list<float, float, float>, vector that defines what axis should aim up
        """

        self._up_vector = vector_list

    def set_world_up_vector(self, vector_list):
        """
        Set the world up axis for the orient process
        :param vector_list: list<float, float, float>, vector that defines what world up axis be
        """

        self._world_up_vector = vector_list

    def set_aim_at(self, index):
        """
        Defines how the joint will aim
        :param index: int, aim at index value
                                0: aim at world X
                                1: aim at world Y
                                2: aim at world Z
                                3: aim at inmediate child
                                4: aim at inmediate parent
                                5: aim at local parent (aiming at the parent and then reversing the direction)
        """

        self._aim_at = self._get_aim_at(index=index)

    def set_aim_up_at(self, index):
        """
        Defines how the will aim up
        :param index: int, aim up at index value
                                0: parent rotate
                                1: child position
                                2: parent position
                                3: triangle plane (need to be configured before)
        """

        self._aim_up_at = self._get_aim_up_at(index=index)

    def set_aim_up_at_object(self, transform_name):
        """
        Defines the object used for aim up
        :param transform_name: str, name of the object
        """

        self._aim_up_at = self._get_local_up_group(transform_name=transform_name)
        self._up_space_type = 'objectrotation'
        self._world_up_vector = [0, 1, 0]

    def set_surface(self, surface_name):
        """
        Defines the surface used to orient
        :param surface_name: str
        """

        self._surface = surface_name
        self.set_aim_up_at(6)
        if cmds.objExists('{}.surface'.format(self._joint)):
            try:
                cmds.setAttr('{}.surface'.format(self._joint), surface_name, type='string')
            except Exception:
                pass

    def run(self):
        """
        Orients joints
        """

        if cmds.objExists('{}.active'.format(self._joint)):
            if not cmds.getAttr('{}.active'.format(self._joint)):
                logger.warning('{} has orientation attributes but is not active. Skipping ...'.format(self._joint))
                return

        self._get_relatives()
        self._unparent()
        self._get_children_special_cases()
        self._freeze(scale=True)

        logger.info('Orienting {}'.format(name_utils.get_basename(self._joint)))

        try:
            for axis in 'XYZ':
                cmds.setAttr('{}.rotateAxis{}'.format(self._joint, axis), 0)
        except Exception:
            logger.warning('Could not zero our rotateAxis on {}. This can cause rig errors!'.format(self._joint))

        self._orient_values = self._get_values()

        if self._orient_values:
            self._aim_vector = self.get_vector_from_axis(self._orient_values['aimAxis'])
            self._up_vector = self.get_vector_from_axis(self._orient_values['upAxis'])
            self._world_up_vector = self.get_vector_from_axis(self._orient_values['worldUpAxis'])
            self._aim_at = self._get_aim_at(self._orient_values['aimAt'])
            self._aim_up_at = self._get_aim_up_at(self._orient_values['aimUpAt'])
        else:
            if type(self._aim_at) == int:
                self._aim_at = self._get_aim_at(self._aim_at)
            if type(self._aim_up_at) == int:
                self._aim_up_at = self._get_aim_up_at(self._aim_up_at)

        self._create_aim()
        if self._orient_values:
            self._invert_scale()
        self._cleanup()
        self._freeze(scale=False)
        self._create_parent()

    def _get_values(self):
        """
        Returns orient joint attributes stored in the wrapped joint node
        :return: dict<str, Attribute>
        """

        if not cmds.objExists('{}.ORIENT_INFO'.format(self._joint)):
            logger.warning(
                'Impossible to get orient attributes from {} because they do not exists!'.format(self._joint))
            return

        ori_attrs = OrientJointAttributes(joint=self._joint)
        return ori_attrs.get_values()

    def _get_relatives(self):
        """
        Internal function that returns all relatives joints of the given joint
        """

        # Get parent and grand parent nodes
        parent = cmds.listRelatives(self._joint, p=True, f=True)
        if parent:
            self._parent = parent[0]
            grand_parent = cmds.listRelatives(self._parent, p=True, f=True)
            if grand_parent:
                self._grand_parent = grand_parent[0]

        if not self._children:
            self._children = cmds.listRelatives(self._joint, f=True, type='transform')
        if self._children:
            self._child = self._children[0]

    def _get_children_special_cases(self):
        if not self._children:
            return

        self._child = self._children[0]
        if len(self._children) > 1:
            self._child2 = self._children[1]
        grand_children = cmds.listRelatives(self._child, f=True, type='transform')
        if grand_children:
            self._grand_child = grand_children[0]

    def _update_locator_scale(self, locator):
        """
        Internal function that updates locator scale to fit the radius of the joint
        :param locator: str
        """

        if cmds.objExists('{}.localScale'.format(locator)):
            radius = cmds.getAttr('{}.radius'.format(self._joint))
            for axis in 'XYZ':
                cmds.setAttr('{}.localScale{}'.format(locator, axis), radius)

    def _invert_scale(self):
        invert_scale = self._orient_values['invertScale']
        if invert_scale == 0:
            return

        if self._child:
            logger.warning(
                'Orient Joints inverted scale only permitted on joints with no children. '
                'Skipping scale invert change on {}'.format(name_utils.get_basename(self.joint)))
            return

        if invert_scale == 1:
            cmds.setAttr('{}.scaleX'.format(self._joint), -1)
        elif invert_scale == 2:
            cmds.setAttr('{}.scaleY'.format(self._joint), -1)
        elif invert_scale == 3:
            cmds.setAttr('{}.scaleZ'.format(self._joint), -1)
        elif invert_scale == 4:
            cmds.setAttr('{}.scaleX'.format(self._joint), -1)
            cmds.setAttr('{}.scaleY'.format(self._joint), -1)
        elif invert_scale == 5:
            cmds.setAttr('{}.scaleX'.format(self._joint), -1)
            cmds.setAttr('{}.scaleZ'.format(self._joint), -1)
        elif invert_scale == 6:
            cmds.setAttr('{}.scaleY'.format(self._joint), -1)
            cmds.setAttr('{}.scaleZ'.format(self._joint), -1)

    def _get_aim_at(self, index):
        """
        Creates and returns the group we want to aim depending of the given index option
        :param index: int, index that defines how we want to create the aim group
        :return: str, created group positioned where lookAt constraint should aim
        """

        # World Axis (0=X, 1=Y, 2=Z)
        if index < 3:
            world_aim = cmds.group(empty=True, n='world_aim')
            transform.MatchTransform(source_transform=self._joint, target_transform=world_aim).translation()

            if index == 0:
                cmds.move(1, 0, 0, world_aim, r=True)
            elif index == 1:
                cmds.move(0, 1, 0, world_aim, r=True)
            elif index == 2:
                cmds.move(0, 0, 1, world_aim, r=True)

            self._delete_later.append(world_aim)
            return world_aim

        # Child
        elif index == 3:
            child_aim = None
            if self._child and cmds.objExists(self._child):
                self._update_locator_scale(self._child)
                child_aim = self._get_position_group(self._child)
            return child_aim

        # Parent
        elif index == 4:
            parent_aim = self._get_position_group(self._parent)
            return parent_aim

        # Front (in X axis) of wrapped joint
        elif index == 5:
            aim = self._get_local_up_group(self._parent)
            return aim

    def _get_aim_up_at(self, index):
        """
        Creates and returns the group we want to set as up group depending of the given index option
        :param index: int, index that defines how we want to create the aim up group
        :return: str, created group positioned where lookAt up axis should look
        """

        if index == 1:
            self._up_space_type = 'objectrotation'
            return self._get_local_up_group(self._parent)

        elif index == 2:
            if self._child and cmds.objExists(self._child):
                self._update_locator_scale(self._child)
                child_group = self._get_position_group(self._child)
                self._up_space_type = 'object'
            elif not self._child or not cmds.objExists(self._child):
                logger.warning('Child specified as up in orient attribute but {} has no child'.format(self._joint))
            return child_group

        elif index == 3:
            parent_group = self._get_position_group(self._parent)
            self._up_space_type = 'object'
            return parent_group

        elif index == 4:
            top = self._get_triangle_group(self._orient_values['triangleTop'])
            mid = self._get_triangle_group(self._orient_values['triangleMid'])
            btm = self._get_triangle_group(self._orient_values['triangleBottom'])
            if not top or not mid or not btm:
                logger.warning(
                    'Could not orient {} fully with current triangle plane settings'.format(self._joint))
                return

            plane_grp = transform.create_group_in_plane(top, mid, btm)
            cmds.move(0, 10, 0, plane_grp, r=True, os=True)
            self._delete_later.append(plane_grp)
            self._up_space_type = 'object'
            return plane_grp

        elif index == 5:
            child_group = None
            if self._child2 and cmds.objExists(self._child2):
                self._update_locator_scale(self._child2)
                child_group = self._get_position_group(self._child2)
                self._up_space_type = 'object'
            elif not self._child2 or not cmds.objExists(self._child2):
                logger.warning(
                    'Child 2 specified as up in orient attributes but {} has no 2nd child'.format(self._joint))
            return child_group

        elif index == 6:
            self._get_surface()
            space_group = None
            if not self._surface:
                return space_group
            self._up_space_type = 'object'
            space_group = self._get_position_group(self._joint)
            space_group_xform = cmds.xform(space_group, query=True, t=True, ws=True)
            if shape_utils.has_shape_of_type(self._surface, 'mesh'):
                mesh_fn = OpenMaya.MFnMesh(self._surface)
                normal = mesh_fn.getClosestNormal(space_group_xform, atSourcePosition=True)
                cmds.xform(space_group, ws=True, t=normal)
            elif shape_utils.has_shape_of_type(self._surface, 'nurbsSurface'):
                surface_fn = OpenMaya.MFnNurbsSurface(self._surface)
                normal = surface_fn.getClosestNormal(space_group_xform, atSourcePosition=True)
                cmds.xform(space_group, ws=True, t=normal)
            return space_group

    def _freeze(self, scale=True):
        """
        Internal function that freezes wrapped joint without touching its hierarchy
        """

        if scale:
            if transform.is_rotate_scale_default(self._joint):
                return
        else:
            if transform.is_rotate_default(self._joint):
                return

        try:
            cmds.makeIdentity(self._joint, apply=True, r=True, s=scale)
        except Exception as exc:
            logger.warning('Could not freeze {} when trying to orient: {}'.format(self._joint, exc))

    def _get_local_up_group(self, transform_name):
        """
        Creates an empty group matching give transform rotation but positioned in front of the
        current wrapped joint (moved in X axis)
        :param transform_name: str, transform we want to match position to
        :return: str, new created local up group
        """

        local_up_group = cmds.group(empty=True, n='local_up_{}'.format(transform))
        transform.MatchTransform(source_transform=transform_name, target_transform=local_up_group).rotation()
        transform.MatchTransform(source_transform=self._joint, target_transform=local_up_group).translation()
        cmds.move(1, 0, 0, local_up_group, relative=True, objectSpace=True)
        self._delete_later.append(local_up_group)

        return local_up_group

    def _get_position_group(self, transfrom_name):
        """
        Creates an empty group with its transformations matching the given transform node
        :param transfrom_name: str, transform we want to match new group to
        :return: str, new created position group
        """

        position_group = cmds.group(empty=True, name='position_group')
        transform.MatchTransform(source_transform=transfrom_name,
                                 target_transform=position_group).translation_rotation()
        self._delete_later.append(position_group)

        return position_group

    def _get_triangle_group(self, index):
        """
        Creates an empty group positioned based on the childs/parents based on given index
        :param index: int, index that defines position of the group
        (0=grand_parent, 1=parent, 2=joint, 3=child, 4=grand_child)
        :return: str, new created triangle position group
        """

        target_transform = None
        if index == 0:
            target_transform = self._grand_parent
        elif index == 1:
            target_transform = self._parent
        elif index == 2:
            target_transform = self._joint
        elif index == 3:
            target_transform = self._child
        elif index == 4:
            target_transform = self._grand_child
        if not target_transform:
            return

        return self._get_position_group(target_transform)

    def _create_aim(self):
        """
        Create aim constraints used to orient the joint
        """

        if not self._aim_at:
            return

        if self._aim_up_at:
            aim = cmds.aimConstraint(
                self._aim_at,
                self._joint,
                aimVector=self._aim_vector,
                upVector=self._up_vector,
                worldUpObject=self._aim_up_at,
                worldUpVector=self._world_up_vector,
                worldUpType=self._up_space_type)[0]
        else:
            aim = cmds.aimConstraint(
                self._aim_at,
                self._joint,
                aimVector=self._aim_vector,
                upVector=self._up_vector,
                worldUpVector=self._world_up_vector,
                worldUpType=self._up_space_type)[0]

        self._delete_later.append(aim)

    def _create_parent(self):
        if self._children:
            cmds.parent(self._children, self._joint)

    def _unparent(self):
        if self._children:
            self._children = cmds.parent(self._children, w=True)
        else:
            self._children = cmds.listRelatives(self._joint, f=True, type='transform')

    def _get_surface(self):
        try:
            self._surface = cmds.getAttr('{}.surface'.format(self.joint))
        except Exception:
            pass

    def _cleanup(self):
        """
        Removes all extra nodes created during orient process
        """

        if self._delete_later:
            cmds.delete(self._delete_later)
