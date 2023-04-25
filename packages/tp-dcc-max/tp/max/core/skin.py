#!#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with skinning
"""

from pymxs import runtime as rt

from tp.max.core import node as node_utils


def set_bone_weight(skin_node, bone_id, vertex_id, weight):
    """
    Sets bone weights for skin modifier
    :param skin_node: str
    :param bone_id: int
    :param vertex_id: int
    :param weight: float
    """

    rt.subobjectLevel = 1
    skin_node = node_utils.get_pymxs_node(skin_node)
    if not skin_node:
        return
    skin_modifier = skin_node.modifiers[rt.Name('Skin')]
    if not skin_modifier:
        return
    vertex_bitarray = rt.BitArray()
    vertex_indices = [vertex_id]
    vertex_bitarray.count = len(vertex_indices)
    for i, index in enumerate(vertex_indices):
        vertex_bitarray[i] = index

    skin_modifier.filter_vertices = True
    rt.skinOps.SelectBone(skin_modifier, bone_id)
    rt.skinOps.SelectVertices(skin_modifier, vertex_bitarray)
    rt.skinOps.setWeight(skin_modifier, weight)
