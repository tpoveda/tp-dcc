#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with namespaces for MotionBuilder
"""

import re

import pyfbsdk

from tp.mobu.core import node as node_utils


def get_namespace(node):
    """
    Returns the namespace of the object
    :param node: FBModel
    :return: str or None
    """

    node = node_utils.get_node_by_name(node)
    if not node:
        return None

    namespace = re.match(".*:", getattr(node, 'LongName', node.Name))
    if namespace:
        return namespace.group()

    return None


def add_namespace(node, namespace, hierarchy=True, to_right=False):
    """
    Adds a namespace to the given object
    :param node: str or FBModel
    :param namespace: str
    :param hierarchy: bool, Whether to apply the namespace to the complete hierarchy of the object
    :param to_right: bool, Whether or not to add namespace to the right of other namespace.
    :return: str or None
    """

    node = node_utils.get_node_by_name(node)
    if not node:
        return None

    action = pyfbsdk.FBNamespaceAction.kFBConcatNamespace
    if hierarchy and not isinstance(node, pyfbsdk.FBConstraint):
        return node.ProcessNamespaceHierarchy(action, namespace, None, to_right)

    return node.ProcessObjectNamespace(action, namespace, None, to_right)


def swap_namespace(node, new_namespace, old_namespace, hierarchy=True):
    """
    Swaps a new namespace with an existing one
    :param node:
    :param new_namespace: str
    :param old_namespace: str
    :param hierarchy: bool, Whether to apply the namespace to the complete hierarchy of the object
    :return: str or None
    """

    action = pyfbsdk.FBNamespaceAction.kFBReplaceNamespace
    if hierarchy and not isinstance(node, pyfbsdk.FBConstraint):
        return node.ProcessNamespaceHierarchy(action, new_namespace, old_namespace)

    return node.ProcessObjectNamespace(action, new_namespace, old_namespace)


def remove_namespace(node, hierarchy=True):
    """
    Removes all teh namespaces
    :param node:
    :param hierarchy: bool, Whether to apply the namespace to the complete hierarchy of the object
    :return: bool
    """

    action = pyfbsdk.FBNamespaceAction.kFBRemoveAllNamespace
    if hierarchy and not isinstance(node, pyfbsdk.FBConstraint):
        return node.ProcessNamespaceHierarchy(action, '')

    return node.ProcessObjectNamespace(action, '')
