#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility methods related to Maya deformer nodes
"""

import re

import maya.cmds
import maya.OpenMaya
import maya.api.OpenMaya
import maya.api.OpenMayaAnim

from tp.core import log
from tp.common.python import helpers
from tp.maya.cmds import node, attribute, exceptions, geometry as geo_utils

logger = log.tpLogger

ALL_DEFORMERS = (
    'blendShape',
    'skinCluster',
    'cluster',
    'softMod',
    'sculpt',
    'ffd',
    'wrap',
    'nonLinear',
    'wire',
    'sculpt',
    'jiggle'
)


def is_deformer(deformer):
    """
    Checks if a node is a valid deformer
    :param deformer: str, name of the node to be checked
    """

    if not maya.cmds.objExists(deformer):
        return False

    # NOTE: Geometry filter is the base type for all deformers
    node_type = maya.cmds.nodeType(deformer, i=True)
    if not node_type.count('geometryFilter'):
        return False

    return True


def check_deformer(deformer):
    """
    Checks if a node is a valid deformer and raises and exception if the node is not valid
    :param deformer: str
    :return: bool, True if the given deformer is valid
    """

    if not maya.cmds.objExists(deformer):
        exceptions.NodeExistsException(deformer)
    if not is_deformer(deformer):
        raise exceptions.DeformerException(deformer)


def get_deformer_list(node_type='geometryFilter', affected_geometry=[], regex_filter=''):
    """
    Returns a list of deformers that match the input criteria
    You can list deformers connected to a specific geometry, by type and filer the results using regular expressions
    :param node_type: str, Deformer type as string. Optional arg, only return deformers of specified type
    :param affected_geometry: list(str), Affected geometry list. Optional arg, will list deformers connected to the
        specific geometry
    :param regex_filter: str, Regular expression as string. Optional arg, will filter results
    """

    deformer_nodes = maya.cmds.ls(type=node_type)

    # Filter by affected geometry
    if affected_geometry:
        if type(affected_geometry) == str:
            affected_geometry = [affected_geometry]
        history_nodes = maya.cmds.listHistory(affected_geometry, groupLevels=True, pruneDagObjects=True)
        deformer_nodes = maya.cmds.ls(history_nodes, type=node_type)

    # Remove duplicated, tweak and transferAttributes nodes
    deformer_nodes = helpers.remove_dupes(deformer_nodes)
    tweak_nodes = maya.cmds.ls(deformer_nodes, type='tweak')
    if tweak_nodes:
        deformer_nodes = [x for x in deformer_nodes if x not in tweak_nodes]
    transfer_attr_nodes = maya.cmds.ls(deformer_nodes, type='transferAttributes')
    if transfer_attr_nodes:
        deformer_nodes = [x for x in deformer_nodes if x not in transfer_attr_nodes]

    # Filter results
    if regex_filter:
        reg_filter = re.compile(regex_filter)
        deformer_nodes = filter(reg_filter.search, deformer_nodes)

    return deformer_nodes


def get_deformer_fn(deformer):
    """
    Initializes and returns an MFnWeightGeometryFilter function set attached to the specific deformer
    :param deformer: str, name of the deformer to create function set for
    :return: str
    """

    # TODO: Make sure dependant functions return objects as OpenMaya1 objects
    # MFnWeightGeometryFilter does not exists in OpenMayaAnim 2.0 yet! Using OpenMaya 1.0 ...')

    if not maya.cmds.objExists(deformer):
        raise Exception('Deformer {} does not exists!'.format(deformer))

    deformer_obj = node.get_mobject(deformer)
    try:
        deformer_fn = maya.api.OpenMayaAnim.MFnWeightGeometryFilter(deformer_obj)
    except Exception as e:
        print(str(e))
        raise Exception('Could not get a geometry filter for deformer "{}"!'.format(deformer))

    return deformer_fn


def get_deformer_set(deformer):
    """
    Returns the deformer set name associated with the given deformer
    :param deformer: str, name of deformer to return the deform set for
    :return: str
    """

    check_deformer(deformer)

    deformer_obj = node.get_mobject(node_name=deformer)
    deformer_fn = maya.api.OpenMayaAnim.MFnGeometryFilter(deformer_obj)
    deformer_set_obj = deformer_fn.deformerSet()
    if deformer_set_obj.isNull():
        raise exceptions.DeformerSetExistsException(deformer)

    return maya.api.OpenMaya.MFnDependencyNode(deformer_set_obj).name()


def get_deformer_set_fn(deformer):
    """
    Initializes and return an MFnSet function set attached to the deformer set of the given deformer
    :param deformer: str, name of the deformer attached to the deformer set to create function set for
    :return: str
    """

    check_deformer(deformer)

    deformer_set = get_deformer_set(deformer=deformer)

    deformer_set_obj = node.get_mobject(node_name=deformer_set)
    deformer_set_fn = maya.api.OpenMaya.MFnSet(deformer_set_obj)

    return deformer_set_fn


def get_geo_index(geometry, deformer):
    """
    Returns the geometry index of a shape to a given deformer
    :param geometry: str, name of shape or parent transform to query
    :param deformer: str, name of deformery to query
    """

    check_deformer(deformer)

    geo = geometry
    if maya.cmds.objectType(geometry) == 'transform':
        try:
            geometry = maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True)[0]
        except Exception:
            raise exceptions.GeometryException(geo)
    geo_obj = node.get_mobject(node_name=geometry)

    deformer_obj = node.get_mobject(node_name=deformer)
    deformer_fn = maya.api.OpenMayaAnim.MFnGeometryFilter(deformer_obj)
    try:
        geo_index = deformer_fn.indexForOutputShape(geo_obj)
    except Exception:
        raise exceptions.NotAffectByDeformerException(geometry, deformer)

    return geo_index


def get_deformer_set_members(deformer, geometry=''):
    """
    Returns the deformer set members of the given deformer
    You can specify a shape name to query deformer membership for, otherwise, membership for the first affected
    geometry will be returned
    :param deformer: str, deformer to query set membership for
    :param geometry: str, geometry to query deformer set membership for (optional)
    :return: str
    """

    deformer_set_fn = get_deformer_set_fn(deformer=deformer)

    if geometry:
        geo_index = get_geo_index(geometry, deformer)
    else:
        geo_index = 0

    deformer_set_sel = deformer_set_fn.getMembers(True)
    deformer_set_len = len(deformer_set_sel)
    if geo_index >= deformer_set_len:
        raise exceptions.GeometryIndexOutOfRange(deformer, geometry, geo_index, deformer_set_len)
    geo_index, deformer_set_path, deformer_set_comp = deformer_set_sel.getDagPath()

    return [deformer_set_path, deformer_set_comp]


def get_deformer_set_member_str_list(deformer, geometry=''):
    """
    Returns the deformer set members of the given deformer as a list of strings
    You can specify a shape name to query deformer membership for, otherwise, membership for the first affected
    geometry will be returned
    :param deformer: str, deformer to query set membership for
    :param geometry: str, geometry to query deformer set membership for (optional)
    :return: list<str>
    """

    deformer_set_fn = get_deformer_set_fn(deformer)

    deformer_set_sel = deformer_set_fn.getMembers(True)
    set_member_str = str(deformer_set_sel)

    set_member_str = maya.cmds.ls(set_member_str, fl=True)

    return set_member_str


def get_deformer_set_member_indices(deformer, geometry=''):
    """
    Returns a list of deformer set member vertex indices
    :param deformer: str, deformer to set member indices for
    :param geometry: str, geometry to query deformer set membership for
    :return: str
    """

    geo = geometry
    if maya.cmds.objectType(geometry) == 'transform':
        try:
            geometry = maya.cmds.listRelatives(geometry, s=True, ni=True, pa=True)[0]
        except Exception:
            exceptions.GeometryException(geo)

    geometry_type = maya.cmds.objectType(geometry)
    deformer_set_mem = get_deformer_set_members(deformer=deformer, geometry=geometry)

    member_id_list = list()

    # Single Index
    if geometry_type == 'mesh' or geometry_type == 'nurbsCurve' or geometry_type == 'particle':
        single_index_comp_fn = maya.api.OpenMaya.MFnSingleIndexedComponent(deformer_set_mem[1])
        member_indices = single_index_comp_fn.getElements()
        member_id_list = list(member_indices)

    # Double Index
    if geometry_type == 'nurbsSurface':
        double_index_comp_fn = maya.api.OpenMaya.MFnDoubleIndexedComponent(deformer_set_mem[1])
        member_indices_U, member_indices_V = double_index_comp_fn.getElements()
        array_length = member_indices_U.length() if hasattr(member_indices_U, 'length') else len(member_indices_U)
        for i in range(array_length):
            member_id_list.append([member_indices_U[i], member_indices_V[i]])

    # Triple Index
    if geometry_type == 'lattice':
        triple_index_comp_fn = maya.api.OpenMaya.MFnTripleIndexedComponent(deformer_set_mem[1])
        member_indices_S, member_indices_T, member_indices_U = triple_index_comp_fn.getElements()
        array_length = member_indices_S.length() if hasattr(member_indices_S, 'length') else len(member_indices_S)
        for i in range(array_length):
            member_id_list.append([member_indices_S[i], member_indices_T[i], member_indices_U[i]])

    return member_id_list


def get_affected_geometry(deformer, return_shapes=False, full_path_names=False):
    """
    Returns a dictionary containing information about geometry affected by a given deformer
    Dict keys corresponds to affected geometry names and values indicate geometry index to deformer
    :param deformer: str, name of the deformer to query geometry from
    :param return_shapes: bool, Whether shape names should be returned instead of transform names
    :param full_path_names: bool, Whether full path names of affected objects should be returned
    :return: dict
    """

    check_deformer(deformer=deformer)

    affected_objects = dict()

    deformer_obj = node.get_mobject(node_name=deformer)
    geo_filter_fn = maya.api.OpenMayaAnim.MFnGeometryFilter(deformer_obj)

    output_object_array = geo_filter_fn.getOutputGeometry()

    array_length = output_object_array.length() if hasattr(output_object_array, 'length') else len(output_object_array)
    for i in range(array_length):
        output_index = geo_filter_fn.indexForOutputShape(output_object_array[i])
        output_node = maya.api.OpenMaya.MFnDagNode(output_object_array[i])

        if not return_shapes:
            output_node = maya.api.OpenMaya.MFnDagNode(output_node.parent(0))

        if full_path_names:
            affected_objects[output_node.fullPathName()] = output_index
        else:
            affected_objects[output_node.partialPathName()] = output_index

    return affected_objects


def find_input_shape(shape):
    """
    Returns the input shape ('...ShapeOrig') for the given shape node
    This function assumes that the specified shape is affected by at least one valid deformer
    :param shape: The shape node to find the corresponding input shape for
    :return: str
    """

    if not maya.cmds.objExists(shape):
        raise exceptions.ShapeException(shape)

    # Get inMesh connection
    in_mesh_cnt = maya.cmds.listConnections(shape + '.inMesh', source=True, destination=False, shapes=True)
    if not in_mesh_cnt:
        return shape

    # Check direct mesh (outMesh --> inMesh) connection
    if str(maya.cmds.objectType(in_mesh_cnt[0])) == 'mesh':
        return in_mesh_cnt[0]

    # Find connected deformer
    deformer_obj = node.get_mobject(in_mesh_cnt[0])
    if not deformer_obj.hasFn(maya.api.OpenMaya.MFn.kGeometryFilt):
        deformer_hist = maya.cmds.listHistory(shape, type='geometryFilter')
        if not deformer_hist:
            logger.warning(
                'Shape node "{0}" has incoming inMesh connections but is not affected by any valid deformers! '
                'Returning "{0}"!'.format(shape))
            return shape
        else:
            deformer_obj = node.get_mobject(deformer_obj[0])

    deformer_fn = maya.api.OpenMayaAnim.MFnGeometryFilter(deformer_obj)

    shape_obj = node.get_mobject(shape)
    geo_index = deformer_fn.indexForOutputShape(shape_obj)
    input_shape_obj = deformer_fn.inputShapeAtIndex(geo_index)

    return maya.api.OpenMaya.MFnDependencyNode(input_shape_obj).name()


def rename_deformer_set(deformer, deformer_set_name=''):
    """
    Rename the deformer set connected to the given deformer
    :param deformer: str, name of the deformer whose deformer set you want to rename
    :param deformer_set_name: str, new name for the deformer set. If left as default, new name will be (deformer+"Set")
    :return: str
    """

    check_deformer(deformer)

    if not deformer_set_name:
        deformer_set_name = deformer + 'Set'

    deformer_set = maya.cmds.listConnections(deformer + '.message', type='objectSet')[0]
    if deformer_set != deformer_set_name:
        deformer_set_name = maya.cmds.rename(deformer_set, deformer_set_name)

    return deformer_set_name


def get_weights(deformer, geometry=None):
    """
    Get the weights for the given deformer. Weights returned as a Python list object
    :param deformer: str, deformer to get weights for
    :param geometry: str, target geometry to get weights from
    :return: list<float>
    """

    # TODO: Make sure dependant functions return objects as OpenMaya1 objects
    # NOTE: 'get_weights function is dependant of MFnWeightGeometryFilter which is not available in OpenMaya 2.0 yet!

    check_deformer(deformer)

    if not geometry:
        geometry = get_affected_geometry(deformer=deformer).keys()[0]

    geo_shape = geometry
    if geometry and maya.cmds.objectType(geo_shape) == 'transform':
        geo_shape = maya.cmds.listRelatives(geometry, s=True, ni=True)[0]

    deformer_fn = get_deformer_fn(deformer)
    deformer_set_mem = get_deformer_set_members(deformer=deformer, geometry=geo_shape)

    weight_list = maya.api.OpenMaya.MFloatArray()
    deformer_fn.getWeights(deformer_set_mem[0], deformer_set_mem[1], weight_list)

    return list(weight_list)


def set_weights(deformer, weights, geometry=None):
    """
    Set the weights for the give ndeformer using the input value list
    :param deformer: str, deformer to set weights for
    :param weights: list<float>, input weight value list
    :param geometry: str, target geometry to apply weights to. If None, use first affected geometry
    """

    # TODO: Make sure dependant functions return objects as OpenMaya1 objects
    # set_weights function is dependant of MFnWeightGeometryFilter which is not available in OpenMaya 2.0 yet!

    check_deformer(deformer)

    if not geometry:
        geometry = get_affected_geometry(deformer).keys()[0]

    geo_shape = geometry
    geo_obj = node.get_mobject(geometry)
    if geometry and geo_obj.hasFn(maya.api.OpenMaya.MFn.kTransform):
        geo_shape = maya.cmds.listRelatives(geometry, s=True, ni=True)[0]

    deformer_fn = get_deformer_fn(deformer)
    deformer_set_mem = get_deformer_set_members(deformer=deformer, geometry=geo_shape)

    weights_list = maya.api.OpenMaya.MFloatArray()
    [weights_list.append(i) for i in weights]

    deformer_fn.setWeight(deformer_set_mem[0], deformer_set_mem[1], weights_list)


def bind_pre_matrix(deformer, bind_pre_matrix='', parent=True):
    """
    Creates a bindPreMatrix transform for the given deformer
    :param deformer: str, deformer to create bind pre matrix transform for
    :param bind_pre_matrix: str, specify existing transform for bind pre matrix connec tion.
        If empty, create a new transform
    :param parent: bool, parent the deformer handle to the bind pre matrix transform
    :return: str
    """

    check_deformer(deformer)

    deformer_handle = maya.cmds.listConnections(deformer + '.matrix', s=True, d=False)
    if deformer_handle:
        deformer_handle = deformer_handle[0]
    else:
        raise exceptions.DeformerHandleExistsException()

    if bind_pre_matrix:
        if not maya.cmds.objExists(bind_pre_matrix):
            bind_pre_matrix = maya.cmds.createNode('transform', n=bind_pre_matrix)
    else:
        prefix = deformer_handle.replace(deformer_handle.split('_')[-1], '')
        bind_pre_matrix = maya.cmds.createNode('transform', n=prefix + 'bindPreMatrix')

    # Match transform and pivot
    maya.cmds.xform(bind_pre_matrix, ws=True, matrix=maya.cmds.xform(deformer_handle, query=True, ws=True, matrix=True))
    maya.cmds.xform(bind_pre_matrix, ws=True, piv=maya.cmds.xform(deformer_handle, query=True, ws=True, rp=True))

    # Connect inverse matrix to deformer
    maya.cmds.connectAttr(bind_pre_matrix + '.worldInverseMatrix[0]', deformer + '.bindPreMatrix', f=True)

    if parent:
        maya.cmds.parent(deformer_handle, bind_pre_matrix)

    return bind_pre_matrix


def prune_weights(deformer, geo_list=None, threshold=0.001):
    """
    Set deformer component weights to 0.0 if the original weight value is below the given threshold
    :param deformer: str, name of the deformer to removed components from
    :param geo_list: list<str>, geometry objects whose components are checked for weight pruning
    :param threshold: float, weight threshold for removal
    """

    check_deformer(deformer)

    geo_list = [] if geo_list is None else helpers.force_list(geo_list)
    if not geo_list:
        geo_list = maya.cmds.deformer(deformer, q=True, g=True)
    if not geo_list:
        raise Exception('No geometry to prune weights for!')
    for geo in geo_list:
        if not maya.cmds.objExists(geo):
            raise exceptions.GeometryExistsException(geo)

    for geo in geo_list:
        weight_list = get_weights(deformer=deformer, geometry=geo)
        weight_list = [wt if wt > threshold else 0.0 for wt in weight_list]
        set_weights(deformer=deformer, weights=weight_list, geometry=geo)


def prune_membership_by_weights(deformer, geo_list=None, threshold=0.001):
    """
    Removes components from a given deformer set if there are weights values below the given threshold
    :param deformer: str, name of the deformer to removed components from
    :param geo_list: list<str>, geometry objects whose components are checked for weight pruning
    :param threshold: float, weight threshold for removal
    """

    # TODO: Make sure dependant functions return objects as OpenMaya1 objects
    # prune_membership_by_weights function is dependant of MFnWeightGeometryFilter which is not available in OpenMaya2

    check_deformer(deformer)

    geo_list = [] if geo_list is None else helpers.force_list(geo_list)
    if not geo_list:
        geo_list = maya.cmds.deformer(deformer, q=True, g=True)
    if not geo_list:
        raise Exception('No geometry to prune weights for!')
    for geo in geo_list:
        if not maya.cmds.objExists(geo):
            raise exceptions.GeometryExistsException(geo)

    deformer_set = get_deformer_set(deformer)
    all_prune_list = list()

    for geo in geo_list:
        geo_type = geo_utils.component_type(geo)
        member_index_list = get_deformer_set_member_indices(deformer=deformer, geometry=geo)
        weight_list = get_weights(deformer=deformer, geometry=geo)

        prune_list = [member_index_list[i] for i in range(len(member_index_list)) if weight_list[i] <= threshold]
        for i in range(len(prune_list)):
            if type(prune_list[i]) == str or type(prune_list[i]) == unicode or type(prune_list[i]) == int:
                prune_list[i] = '[{}]'.format(str(prune_list[i]))
            elif type(prune_list[i]) == list:
                prune_list[i] = [str(p) for p in prune_list[i]]
                prune_list[i] = '[' + ']['.join(prune_list[i]) + ']'
            prune_list[i] = geo + '.' + geo_type + str(prune_list[i])
        all_prune_list.extend(prune_list)

        if prune_list:
            maya.cmds.sets(prune_list, rm=deformer_set)

    return all_prune_list


def clean(deformer, threshold=0.001):
    """
    Clean given deformer by pruning weights and membership under the given tolerance
    :param deformer: str, deformer to clean
    :param threshold: float, weight value tolerance for prune operations
    """

    check_deformer(deformer)

    logger.debug('Cleaning deformer: {}!'.format(deformer))

    prune_weights(deformer=deformer, threshold=threshold)
    prune_membership_by_weights(deformer=deformer, threshold=threshold)


def check_multiple_outputs(deformer, print_result=True):
    """
    Check the  given deformer to check for multiple output connections from a single plug
    :param deformer: str, deformer to check for multiple output connections
    :param print_result: bool, Whether if the results should be printed or not
    :return: dict
    """

    check_deformer(deformer)

    out_geo_plug = attribute.attr_mplug(deformer + '.outputGeometry')
    if not out_geo_plug.isArray():
        raise Exception('Attribute ""{}".outputGeometry is not array" attribute!'.format(deformer))

    index_list = out_geo_plug.getExistingArrayAttributeIndices()
    num_index = len(index_list)

    return_dict = dict()
    for i in range(num_index):
        plug_cnt = maya.cmds.listConnections(
            deformer + '.outputGeometry[' + str(index_list[i]) + ']', s=False, d=True, p=True)
        if len(plug_cnt) > 1:
            return_dict[deformer + '.outputGeometry[' + str(index_list[i]) + ']'] = plug_cnt
            if print_result:
                logger.debug(
                    'Deformer output "' + deformer + '.outputGeometry[' + str(
                        index_list[i]) + ']" has ' + str(len(plug_cnt)) + ' outgoing connections:')
                for cnt in plug_cnt:
                    logger.debug('\t- ' + cnt)

    return return_dict


def get_deformer_history(geo_obj):
    """
    Returns the history of the geometry object
    :param geo_obj: str, name of the geometry
    :return: list<str>, list of deformers in the deformation history
    """

    scope = maya.cmds.listHistory(geo_obj, pruneDagObjects=True)
    if not scope:
        return

    found = list()
    for obj in scope:
        inherited = maya.cmds.nodeType(obj, inherited=True)
        if 'geometryFilter' in inherited:
            found.append(obj)
        if maya.cmds.objectType(obj, isAType='shape') and not maya.cmds.nodeType(obj) == 'lattice':
            return found

    if not found:
        return None

    return found


def find_all_deformers(geo_obj):
    """
    Returns a list of all deformers in the given geometry deformation history
    :param geo_obj: st,r name of the geometry
    :return: list<str>, list of deformers in the given geometry object deformation history
    """

    history = get_deformer_history(geo_obj)
    found = list()
    if not history:
        return found

    for obj in history:
        if maya.cmds.objectType(obj, isAType='geometryFilter'):
            found.append(obj)

    return found


def find_deformer_by_type(geo_obj, deformer_type, return_all=False):
    """
    Given a mesh object find a deformer with deformer_type in its history
    :param geo_obj: str, name of a mesh
    :param deformer_type: str, correspnds to the Maya deformer type (skinCluster, blendShape, etc)
    :param return_all: bool, Whether to return all the deformer found of the given type or just the first one
    :return: list<names of deformers of type found in the history>
    """

    found = list()
    history = get_deformer_history(geo_obj)
    if not history:
        return None

    for obj in history:
        if obj and maya.cmds.nodeType(obj) == deformer_type:
            if not return_all:
                return obj
            found.append(obj)

    if not found:
        return None

    return found
