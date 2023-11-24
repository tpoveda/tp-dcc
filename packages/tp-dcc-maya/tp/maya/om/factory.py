#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions to create different type of Maya nodes.
"""

import maya.api.OpenMaya as OpenMaya


def create_dag_node(name, node_type, parent=None, mod=None, apply=True):
    """
    Creates a new DAG node and if a parent is specified, then parent the new node.

    :param str name:
    :param str node_type:
    :param OpenMaya.MObject or OpenMaya.MObject.kNull or None parent:
    :param OpenMaya.MDagModifier or None mod: optional Maya modifier to apply.
    :param bool apply: whether to apply modifier immediately.
    :return: newly created Maya object instance.
    :rtype: OpenMaya.MObject
    """

    if parent is None or parent.isNull() or parent.apiType() in (OpenMaya.MFn.kInvalid, OpenMaya.MFn.kWorld):
        parent = OpenMaya.MObject.kNullObj

    modifier = mod or OpenMaya.MDagModifier()
    node = modifier.createNode(node_type, parent)
    modifier.renameNode(node, name)
    if mod is None or apply:
        modifier.doIt()

    return node


def create_dg_node(name, node_type, mod=None, apply=True):
    """
    Creates a dependency graph node and returns the node Maya object.

    :param str name: new name of the node.
    :param str node_type: Maya node type to create.
    :param OpenMaya.MDGModifier or None mod: optional Maya modifier to apply.
    :param bool apply: whether to apply modifier immediately.
    :return: newly created Maya object instance.
    :rtype: OpenMaya.MObject
    """

    modifier = mod or OpenMaya.MDGModifier()
    node = modifier.createNode(node_type)
    modifier.renameNode(node, name)
    if mod is None or apply:
        modifier.doIt()

    return node
