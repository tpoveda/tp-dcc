from __future__ import annotations

import maya.api.OpenMaya as OpenMaya


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
    """

    if (
        parent is None
        or parent.isNull()
        or parent.apiType() in (OpenMaya.MFn.kInvalid, OpenMaya.MFn.kWorld)
    ):
        parent = OpenMaya.MObject.kNullObj

    modifier = mod or OpenMaya.MDagModifier()
    node = modifier.createNode(node_type, parent)
    modifier.renameNode(node, name)
    if mod is None or apply:
        modifier.doIt()

    return node
