from __future__ import annotations

import logging

import maya.api.OpenMaya as OpenMaya

from . import plugs
from ..cmds import helpers


logger = logging.getLogger(__name__)


def create_dg_node(
    name: str,
    node_type: str,
    mod: OpenMaya.MDGModifier | None = None,
    apply: bool = True,
):
    """
    Creates a dependency graph node and returns the node Maya object.

    :param name: new name of the node.
    :param node_type: Maya node type to create.
    :param mod: optional Maya modifier to apply.
    :param apply: whether to apply modifier immediately.
    :return: newly created Maya object instance.
    """

    modifier = mod or OpenMaya.MDGModifier()
    node = modifier.createNode(node_type)
    modifier.renameNode(node, name)
    if mod is None or apply:
        modifier.doIt()

    return node


def create_dag_node(
    name: str,
    node_type: str,
    parent: OpenMaya.MObject | OpenMaya.MObject.kNullObj | None = None,
    mod: OpenMaya.MDagModifier | None = None,
    apply: bool = True,
) -> OpenMaya.MObject:
    """
    Creates a new DAG node and if a parent is specified, then parent the new node.

    :param name: new name of the node.
    :param node_type: Maya node type to create.
    :param parent: optional parent node to attach the new node to.
    :param mod: optional Maya modifier to apply.
    :param apply: whether to apply modifier immediately.
    :return: newly created Maya object instance.
    :raises NameError: if the node name is invalid
    :raises TypeError: if the node type is invalid.
    """

    if not helpers.is_safe_name(name):
        raise NameError(f"Invalid node name: {name}")

    if (
        parent is None
        or parent.isNull()
        or parent.apiType() in (OpenMaya.MFn.kInvalid, OpenMaya.MFn.kWorld)
    ):
        parent = OpenMaya.MObject.kNullObj

    modifier = mod or OpenMaya.MDagModifier()
    try:
        node = modifier.createNode(node_type, parent)
    except TypeError:
        logger.exception(f"Failed to create DAG node of type: {node_type}")
        raise
    modifier.renameNode(node, name)
    if mod is None or apply:
        modifier.doIt()

    return node


def create_motion_path(
    nurbs_curve: OpenMaya.MObject, param: float, name: str, fraction_mode: bool = False
) -> OpenMaya.MObject:
    """
    Creates a motion path node that follows the given curve at the given param.

    :param nurbs_curve: curve to attach the node to.
    :param param: param value to attach the node to.
    :param name: name for the motion path node.
    :param fraction_mode: whether the motion path should use fraction mode.
    :return: the created motion path node.
    """

    curve_fn = OpenMaya.MFnDependencyNode(nurbs_curve)
    motion_path = create_dg_node(name, "motionPath")
    motion_path_fn = OpenMaya.MFnDependencyNode(motion_path)

    plugs.connect_plugs(
        curve_fn.findPlug("worldSpace", False).elementByLogicalIndex(0),
        motion_path_fn.findPlug("geometryPath", False),
    )
    motion_path_fn.findPlug("uValue", False).setFloat(param)
    motion_path_fn.findPlug("frontAxis", False).setInt(0)
    motion_path_fn.findPlug("upAxis", False).setInt(1)
    motion_path_fn.findPlug("fractionMode", False).setBool(fraction_mode)

    return motion_path
