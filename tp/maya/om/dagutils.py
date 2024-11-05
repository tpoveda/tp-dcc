from __future__ import annotations

import logging
from typing import Iterator, Iterable

from maya import cmds
from maya.api import OpenMaya

from . import nodes
from ...python import helpers

logger = logging.getLogger(__name__)


def create_selection_list(
    items: list[str | OpenMaya.MObject | OpenMaya.MObjectHandle | OpenMaya.MDagPath],
) -> OpenMaya.MSelectionList:
    """
    Creates a new selection list from the given items.

    :param items: items to create the selection list from.
    :return: new selection list instance.
    """

    selection_list = OpenMaya.MSelectionList()

    for item in items:
        depend_node = nodes.mobject(item)
        if depend_node.isNull():
            logger.debug(f"Impossible to create selection list from item: {item}")
            continue
        if depend_node.hasFn(OpenMaya.MFn.kDagNode):
            selection_list.add(OpenMaya.MDagPath.getAPathTo(depend_node))
        else:
            selection_list.add(depend_node)

    return selection_list


def iterate_active_selection(
    api_type: OpenMaya.MFn.kDependencyNode,
) -> Iterator[OpenMaya.MObject]:
    """
    Iterates over the active selection and yields the MObjects that match the given API type.

    :param api_type: API type to filter the selection by.
    :return: Iterator with the MObjects that match the given API type.
    """

    selection = OpenMaya.MGlobal.getActiveSelectionList()
    selection_iter = OpenMaya.MItSelectionList(selection)

    while not selection_iter.isDone():
        depend_node: OpenMaya.MObject = selection_iter.getDependNode()
        if depend_node.hasFn(api_type):
            yield depend_node
        selection_iter.next()


def active_selection(
    api_type: int = OpenMaya.MFn.kDependencyNode,
) -> list[OpenMaya.MObject]:
    """
    Returns the active selection as a list of MObjects.

    :param api_type: API type to filter the selection by.
    :return: List of MObjects with the active selection.
    """

    return list(iterate_active_selection(api_type=api_type))


def root(mobj: OpenMaya.MObject) -> OpenMaya.MObject:
    """
    Traverses the given Maya object parents until the root node is found and returns that MObject.

    :param mobj: Maya object to get root of.
    :return: root Maya object.
    """

    current = mobj
    for node in iterate_parents(mobj):
        if node is None:
            return current
        current = node

    return current


def roots(mobjs: Iterable[OpenMaya.MObject]) -> list[OpenMaya.MObject]:
    """
    Returns all root nodes of the given ones

    :param mobjs: Maya objects to get roots from.
    :return: list of root Maya objects.
    """

    found_roots: list[OpenMaya.MObject] = []
    for mobj in mobjs:
        found_root = root(mobj)
        if found_root and found_root not in found_roots:
            found_roots.append(found_root)

    return found_roots


def root_node(mobj: OpenMaya.MObject, node_type: OpenMaya.MFn) -> OpenMaya.MObject:
    """
    Recursively traverses up the hierarchy until finding the first object that does not have a parent.

    :param mobj: Maya object to get root of.
    :param node_type: node type for the root node.
    :return: found root node.
    """

    parent_mobj = parent(mobj)
    if not parent_mobj:
        return mobj
    if parent_mobj.apiType() != node_type:
        return mobj

    return root_node(parent_mobj, node_type) if parent_mobj else mobj


def iterate_nodes(
    api_type: int = OpenMaya.MFn.kDependencyNode, type_name: str | None = None
):
    """
    Generator function that iterates over all nodes in the scene.

    :param api_type: Maya API type to filter the nodes by.
    :param type_name: name of the node type to filter the nodes by.
    :return: generator of iterated nodes.
    """

    if not helpers.is_null_or_empty(type_name):
        for node_name in cmds.ls(type=type_name, long=True) or []:
            yield nodes.mobject_by_name(node_name)
    else:
        iterator = OpenMaya.MItDependencyNodes(api_type)
        while not iterator.isDone():
            yield iterator.thisNode()
            iterator.next()


def iterate_parents(node: OpenMaya.MObject) -> Iterator[OpenMaya.MObject]:
    """
    Generator function that iterate over all given Maya object parents.

    :param node: Maya object whose parents we want to iterate over.
    :return: iterated parents.
    """

    parent_mobj = parent(node)
    while parent_mobj is not None:
        yield parent_mobj
        parent_mobj = parent(parent_mobj)


def has_parent(node: OpenMaya.MObject) -> bool:
    """
    Returns whether given Maya object is parented.

    :param node: Maya object.
    :return: True if the Maya object is parented under other Maya object; False otherwise.
    """

    parent_mobj = parent(node)
    return False if parent_mobj is None or parent_mobj.isNull() else True


def parent(mobj: OpenMaya.MObject) -> OpenMaya.MObject | None:
    """
    Returns the parent MObject of the given Maya object.

    :param mobj: Maya object we want to retrieve parent of.
    :return: parent Maya object.
    """

    if not mobj.hasFn(OpenMaya.MFn.kDagNode):
        return None

    dag_path = OpenMaya.MDagPath.getAPathTo(mobj)
    if dag_path.node().apiType() == OpenMaya.MFn.kWorld:
        return None

    dag_node = OpenMaya.MFnDagNode(dag_path).parent(0)
    if dag_node.apiType() == OpenMaya.MFn.kWorld:
        return None

    return dag_node


def set_parent(
    child: OpenMaya.MObject,
    new_parent: OpenMaya.MObject | None = None,
    maintain_offset: bool = False,
    mod: OpenMaya.MDagModifier | None = None,
    apply: bool = True,
) -> OpenMaya.MDagModifier:
    """
    Sets the parent of the given child.

    :param child: child node which will have its parent changed
    :param new_parent: new parent for the child.
    :param maintain_offset: bool, whether current transformation is maintained relative to the new parent
    :param mod: modifier to add to; if None, a new will be created.
    :param apply: whether to apply modifier immediately
    :return: modifier used to set the parent.
    """

    mod = mod or OpenMaya.MDagModifier()

    new_parent = new_parent or OpenMaya.MObject.kNullObj
    if child == new_parent:
        return mod

    current_parent = parent(child) or OpenMaya.MObject.kNullObj
    if current_parent and current_parent == new_parent:
        return mod

    if not maintain_offset:
        mod.reparentNode(child, new_parent)
        if apply:
            mod.doIt()
        return mod

    flags: str = ""
    _parent_path: str = ""
    if new_parent == OpenMaya.MObject.kNullObj:
        flags += " -world"
    else:
        _parent_path = nodes.name(new_parent)

    mod.commandToExecute(f"parent -a {flags} {nodes.name(child)} {_parent_path}")
    if apply:
        mod.doIt()

    return mod


def children(
    node: OpenMaya.MObject,
    recursive: bool = False,
    filter_types: Iterable[OpenMaya.MFn] | None = None,
) -> tuple[OpenMaya.MObject, ...]:
    """
     Function that returns all children of the give Maya object.

    :param node: Maya object whose children we want to retrieve.
    :param recursive: True to recursively find children; False otherwise.
    :param filter_types: filter children types. If not given all type will be returned.
    :return: tuple of found children.
    """

    filter_types = filter_types or (OpenMaya.MFn.kTransform,)
    return tuple(iterate_children(node, recursive=recursive, filter_types=filter_types))


def iterate_children(
    node: OpenMaya.MObject,
    recursive: bool = False,
    filter_types: Iterable[OpenMaya.MFn] | None = None,
) -> Iterator[OpenMaya.MObject]:
    """
    Generator function that iterates over all children of the give Maya object.

    :param node: Maya object whose children we want to retrieve.
    :param recursive: True to recursively find children; False otherwise.
    :param filter_types: filter children types. If not given all type will be returned.
    :return: generator of iterated children.
    """

    dag_node = OpenMaya.MDagPath.getAPathTo(node)
    child_count = dag_node.childCount()
    if not child_count:
        return
    filter_types = filter_types or ()
    for i in range(child_count):
        child_obj = dag_node.child(i)
        if not filter_types or child_obj.apiType() in filter_types:
            yield child_obj
            if recursive:
                for child in iterate_children(
                    child_obj, recursive=recursive, filter_types=filter_types
                ):
                    yield child
