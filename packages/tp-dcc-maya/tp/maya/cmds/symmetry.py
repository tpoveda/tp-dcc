#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with symmetry
"""

import re
import copy

import maya.cmds

from tp.core import log
from tp.maya.cmds import decorators

logger = log.tpLogger


class SymmetryTable(object):
    def __init__(self):

        self.sym_table = list()
        self.asym_table = list()
        self.positive_vertex_list = list()
        self.positive_index_list = list()
        self.negative_vertex_list = list()
        self.negative_index_list = list()

    def build_symmetry_table(self, mesh, axis=0, tolerance=0.001, use_pivot=True):
        """
        Builds a symmetry table for the given mesh
        :param mesh: str, mesh to build symmetry table for
        :param axis: int, axis to check for symmetry across
        :param tolerance: float, distance tolerance for finding symmetry pairs
        :param use_pivot: bool, Whether to use object pivot or world pivot
        """

        negative_vertices = list()
        positive_vertices = list()
        non_symmetry_vertices = list()
        positive_vertices_int = list()
        positive_vertices_xform = list()
        negative_vertices_int = list()
        negative_vertices_xform = list()

        axis_ind = axis
        axis2_ind = (axis_ind + 1) % 3
        axis3_ind = (axis_ind + 2) % 3
        mid_offset_tolerance = -0.0000001

        vertices_counter = 0

        if use_pivot:
            vertex_xform = maya.cmds.xform(mesh, query=True, ws=True, rp=True)
            mid = vertex_xform[axis_ind]
        else:
            mesh_parent = mesh
            if maya.cmds.objectType(mesh_parent) != 'transform':
                mesh_parent = maya.cmds.listRelatives(mesh, p=True)[0]
            bounding_box = maya.cmds.xform(mesh_parent, q=True, ws=True, boundingBox=True)
            mid = bounding_box[axis_ind] + ((bounding_box[axis_ind + 3] - bounding_box[axis_ind]) / 2)

        total_vertices = maya.cmds.polyEvaluate(mesh, v=True)
        sym_table = range(int(total_vertices))

        # Retrieve positive and negative vertices
        for i in range(total_vertices):
            vtx = mesh + '.vtx[{}]'.format(i)
            vertex_xform = maya.cmds.xform(vtx, q=True, ws=True, translation=True)
            mid_offset = vertex_xform[axis_ind] - mid
            if mid_offset >= mid_offset_tolerance:
                positive_vertices.append(vtx)
                positive_vertices_int.append(i)
                positive_vertices_xform.append(vertex_xform[axis_ind])
            else:
                if mid_offset < mid_offset_tolerance:
                    negative_vertices.append(vtx)
                    negative_vertices_int.append(i)
                    negative_vertices_xform.append(vertex_xform[axis_ind])

        self.positive_vertex_list = copy.deepcopy(positive_vertices)
        self.positive_index_list = copy.deepcopy(positive_vertices_int)
        self.negative_vertex_list = copy.deepcopy(negative_vertices)
        self.negative_index_list = copy.deepcopy(negative_vertices_int)

        # Find non-symmetrical vertices
        for i in range(len(positive_vertices)):
            vtx = positive_vertices[i]
            positive_offset = positive_vertices_xform[i] - mid
            if positive_offset < tolerance:
                positive_vertices[i] = 'm'
                vertices_counter += 1
                continue

            for j in range(len(negative_vertices)):
                if negative_vertices[j] == 'm':
                    continue
                negative_offset = mid - negative_vertices_xform[j]
                if negative_offset < tolerance:
                    negative_vertices[j] = 'm'
                    vertices_counter += 1
                    continue

                if abs(positive_offset - negative_offset) <= tolerance:
                    vertex_xform = maya.cmds.xform(vtx, q=True, ws=True, t=True)
                    vertex2_xform = maya.cmds.xform(negative_vertices[j], q=True, ws=True, t=True)
                    test1 = vertex_xform[axis2_ind] - vertex2_xform[axis2_ind]
                    test2 = vertex_xform[axis3_ind] - vertex2_xform[axis3_ind]
                    if abs(test1) < tolerance and abs(test2) < tolerance:
                        sym_table[negative_vertices_int[j]] = positive_vertices_int[i]
                        sym_table[positive_vertices_int[i]] = negative_vertices_int[j]
                        vertices_counter += 2
                        positive_vertices[i] = negative_vertices[j] = 'm'
                        break

        # Determine asymmetrical vertices
        for i, j in zip(positive_vertices, negative_vertices):
            if i != 'm' and j != 'm':
                non_symmetry_vertices.append((i, j))

        # [non_symmetry_vertices.append(i) for i in positive_vertices if i != 'm']
        # [non_symmetry_vertices.append(i) for i in negative_vertices if i != 'm']

        if vertices_counter != total_vertices:
            logger.warning('Mesh object "{} is not symmetrical!'.format(mesh))

        self.sym_table = sym_table
        self.asym_table = non_symmetry_vertices

        return self.sym_table


def get_side_vertices(obj, axis=0, sel_negative=True, tolerance=0.001, use_pivot=False, base_obj=None):
    """
    Select a side of the object
    :param obj:
    :param axis:
    :param sel_negative: 0: select negative side; 1: 1: select positive side; None: select all vertices
    :param tolerance:
    :param use_pivot:
    :param base_obj:
    :return:
    """

    axis_ind = axis

    total_vertices = maya.cmds.polyEvaluate(obj, v=True)

    if sel_negative is None:
        all_vtx = list()
        for i in range(total_vertices):
            vtx = obj + '.vtx[{}]'.format(i)
            all_vtx.append(vtx)
        return all_vtx

    if not base_obj:
        base_obj = obj

    if use_pivot:
        vertex_xform = maya.cmds.xform(base_obj, query=True, ws=True, rp=True)
        mid = vertex_xform[axis_ind]
    else:
        mesh_parent = base_obj
        if maya.cmds.objectType(mesh_parent) != 'transform':
            mesh_parent = maya.cmds.listRelatives(base_obj, p=True)[0]
        bounding_box = maya.cmds.xform(mesh_parent, q=True, ws=True, boundingBox=True)
        mid = bounding_box[axis_ind] + ((bounding_box[axis_ind + 3] - bounding_box[axis_ind]) / 2)

    side_vertices = list()
    for i in range(total_vertices):
        vtx = base_obj + '.vtx[{}]'.format(i)
        vtx_xform = maya.cmds.xform(vtx, q=True, ws=True, t=True)
        mid_offset = vtx_xform[axis_ind] - mid
        if abs(mid_offset) < tolerance:
            side_vertices.append(vtx)
            continue
        elif mid_offset > 0 and not sel_negative:
            side_vertices.append(vtx)
            continue
        elif mid_offset < 0 and sel_negative:
            side_vertices.append(vtx)
            continue

    return side_vertices


def get_symmetric_vertex(vertex_index, sym_table_list):
    """
    Returns symmetric vertex or -1 if not symmetric vertex found
    :param vertex_index: int
    :param sym_table_list: int
    """

    for i in range(len(sym_table_list)):
        if int(vertex_index) == int(sym_table_list[i]):
            if i % 2 == 0:
                sym_vtx = sym_table_list[i + 1]
            else:
                sym_vtx = sym_table_list[i - 1]
            break

    return sym_vtx


@decorators.undo_chunk
def mirror_vertices(obj, selected_vertices=None, axis=0, neg_to_pos=False, tolerance=0.001, use_pivot=False,
                    flip=False, base_obj=None, sym_table_list=None):
    zero_vertices_int = list()
    pos_vertices_int = list()
    neg_vertices_int = list()

    axis_ind = axis

    if use_pivot:
        vertex_xform = maya.cmds.xform(base_obj, query=True, ws=True, rp=True)
        mid = vertex_xform[axis_ind]
    else:
        mesh_parent = base_obj
        if maya.cmds.objectType(mesh_parent) != 'transform':
            mesh_parent = maya.cmds.listRelatives(base_obj, p=True)[0]
        bounding_box = maya.cmds.xform(mesh_parent, q=True, ws=True, boundingBox=True)
        mid = bounding_box[axis_ind] + ((bounding_box[axis_ind + 3] - bounding_box[axis_ind]) / 2)

    if selected_vertices is None:
        selected_vertices = maya.cmds.ls(sl=True)

    for vtx in selected_vertices:
        vtx_index = re.search(r'\[(.*?)\]', vtx).group(1)
        vtx_xform = maya.cmds.xform(vtx, q=True, ws=True, t=True)
        mid_offset = vtx_xform[axis_ind] - mid
        if abs(mid_offset) < tolerance:
            zero_vertices_int.append(vtx_index)
            continue
        if mid_offset > 0:
            pos_vertices_int.append(vtx_index)
            continue
        if mid_offset < 0:
            neg_vertices_int.append(vtx_index)
            continue

    if neg_to_pos:
        pos_vertices_int = neg_vertices_int

    for i in range(len(pos_vertices_int)):
        vtx_num = get_symmetric_vertex(pos_vertices_int[i], sym_table_list)
        vtx = obj + '.vtx[{}]'.format(pos_vertices_int[i])
        vtx_sym = obj + '.vtx[{}]'.format(vtx_num)
        if vtx_num != -1:
            if not flip:
                vtx_xform = maya.cmds.xform(vtx, q=True, ws=True, t=True)
                vtx_xform[axis_ind] = 2 * mid - vtx_xform[axis_ind]
                maya.cmds.xform(vtx_sym, t=(vtx_xform[0], vtx_xform[1], vtx_xform[2]), ws=True)
            else:
                vtx_xform = maya.cmds.xform(vtx, q=True, ws=True, t=True)
                vtx_xform[axis_ind] = 2 * mid - vtx_xform[axis_ind]
                flip_vtx_xform = maya.cmds.xform(vtx_sym, q=True, ws=True, t=True)
                flip_vtx_xform[axis_ind] = 2 * mid - flip_vtx_xform[axis_ind]
                maya.cmds.xform(vtx_sym, t=(vtx_xform[0], vtx_xform[1], vtx_xform[2]), ws=True)
                maya.cmds.xform(vtx, t=(flip_vtx_xform[0], flip_vtx_xform[1], flip_vtx_xform[2]), ws=True)

    # Middle verts
    for i in range(len(zero_vertices_int)):
        vtx = obj + '.vtx[{}]'.format(zero_vertices_int[i])
        vtx_xform = maya.cmds.xform(vtx, q=True, ws=True, t=True)
        if flip:
            vtx_xform[axis_ind] = 2 * mid - vtx_xform[axis_ind]
        else:
            vtx_xform[axis_ind] = mid
        maya.cmds.xform(vtx, t=(vtx_xform[0], vtx_xform[1], vtx_xform[2]), ws=True)
