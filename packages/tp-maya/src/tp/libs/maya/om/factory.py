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
) -> OpenMaya.MObject:
    """Create a dependency graph node and return the node Maya object.

    Args:
        name: New name of the node.
        node_type: Maya node type to create.
        mod: Optional Maya modifier to apply.
        apply: Whether to apply modifier immediately.

    Returns:
        Newly created Maya object instance.
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
    """Create a DAG node and return the node Maya object. If a parent is
    specified, then parent the new node.

    Args:
        name: new Name of the node.
        node_type: Maya node type to create.
        parent: Optional parent node to attach the new node to.
        mod: Optional Maya modifier to
        apply: Whether to apply modifier immediately.

    Returns:
        Newly created Maya object instance.

    Raises:
        NameError: if the node name is invalid
        TypeError: if the node type is invalid.
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
    """Create a motion path node that follows the given curve at the given
    param.

    Args:
        nurbs_curve: Curve to attach the node to.
        param: Param value to attach the node to.
        name: Name for the motion path node.
        fraction_mode: Whether the motion path should use fraction mode.

    Returns:
        The created motion path node.
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
