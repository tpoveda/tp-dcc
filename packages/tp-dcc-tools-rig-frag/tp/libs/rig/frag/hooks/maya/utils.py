from __future__ import annotations

import re
from typing import Any

import maya.cmds as cmds

from tp.maya import api

VALID_UUID = re.compile('^[A-F0-9]{8}-([A-F0-9]{4}-){3}[A-F0-9]{12}$')


def is_uuid(obj: Any) -> bool:
    """
    Returns whether an object is a valid UUID.

    :param Any obj: node to check.
    :return: True if given object is a valid UUID; False otherwise.
    :rtype: bool
    """

    return isinstance(obj, str) and VALID_UUID.match(obj)


def uuid(node: api.DGNode | api.DagNode) -> str:
    """
    Returns the UUID of the given node.

    :param api.DGNode or api.DagNode node: object to get UUID of.
    :return: UUID of the given node as a string.
    :rtype: str
    """

    return node.uuid().asString()


def find_node_by_uuid(uuid: str, ref_node: str | None = None) -> api.DGNode | api.DagNode | None:
    """
    Finds and returns a node by its UUID.

    :param str uuid: A string UUID representing the node.
    :param str or None ref_node: name of the reference node that contains the node to find.
    :return: node instance with the UUID from the given reference, or None if not found.
    :rtype: api.DGNode or api.DagNode or None
    """

    nodes = cmds.ls(uuid, long=True)
    if not nodes:
        return None

    found_node: str | None = None
    if ref_node:
        for node in nodes:
            if not cmds.referenceQuery(node, isNodeReferenced=True):
                continue
            if not cmds.referenceQuery(node, referenceNode=True) == ref_node:
                continue
            found_node = node
            break
    found_node = found_node or nodes[0]

    return api.node_by_name(found_node)
