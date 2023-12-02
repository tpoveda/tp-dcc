#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utilities functions and classes related with Maya API MDagPaths
"""

from __future__ import annotations

import re
from itertools import chain
from collections import deque
from six import integer_types
from typing import Iterator, Any

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya1
import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim

from tp.core import log
from tp.common.python import helpers
from tp.maya.om import undo

logger = log.tpLogger

__name_regex__ = re.compile(r'^(?:\:?([a-zA-Z0-9_]))+$')
__uuid_regex__ = re.compile(r'^[A-Z0-9]{8}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{12}$')
__path_regex__ = re.compile(r'^(.*\|)([^\|]*)$')


def iterate_active_selection(api_type: int = OpenMaya.MFn.kDependencyNode) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields the active selection.

    :param int api_type: API to filter selection by.
    :return: iterated active selected nodes.
    :rtype: Iterator[OpenMaya.MObject]
    """

    selection = OpenMaya.MGlobal.getActiveSelectionList()
    selection_count = selection.length()
    for i in range(selection_count):
        depend_node = selection.getDependNode(i)
        if depend_node.hasFn(api_type):
            yield depend_node


def active_selection(api_type: int = OpenMaya.MFn.kDependencyNode) -> list[OpenMaya.MObject]:
    """
    Returns active selection.

    :param int api_type: API to filter selection by.
    :return: list of selected nodes.
    :rtype: list[OpenMaya.MObject]
    """

    return list(iterate_active_selection(api_type=api_type))


def mobject_by_name(name: str) -> OpenMaya.MObject | None:
    """
    Returns an MObject from the given node name.

    :param str name: name of the node to get.
    :return: Maya object instance from given name.
    :rtype: OpenMaya.MObject or None
    """

    strings = name.split(':')
    has_namespace = len(strings) >= 2

    # Wildcards do not account for the root namespace!
    name = strings[-1]
    namespaces = (':'.join(strings[:-1]),) if has_namespace else ('', '*')

    selection = OpenMaya.MSelectionList()
    for namespace in namespaces:
        try:
            selection.add(f'{namespace}:{name}')
        except RuntimeError:
            continue

    # Evaluate selection list.
    selection_count = selection.length()
    if selection_count > 0:
        return selection.getDependNode(0)
    else:

        logger.debug(f'Cannot locate node from name: "{name}"')
        return OpenMaya.MObject.kNullObj


def mobject_by_path(path: str) -> OpenMaya.MObject | None:
    """
    Returns an MObject from the given node path.

    :param str path: node path.
    :return: Maya object instance from given path.
    :rtype: OpenMaya.MObject or None
    """

    # Check if a namespace was supplied
    # If not, then use a wildcard to search recursively!
    hierarchy = path.split('|')
    leaf_name = hierarchy[-1]
    strings = leaf_name.split(':')
    has_namespace = len(strings) >= 2
    name = strings[-1]
    namespaces = (':'.join(strings[:-1]),) if has_namespace else ('', '*')

    selection = OpenMaya.MSelectionList()
    for namespace in namespaces:
        try:
            selection.add(f'{namespace}:{name}')
        except RuntimeError:
            continue

    # Evaluate selection list
    selection_count = selection.length()
    if selection_count == 0:
        logger.debug(f'Cannot locate node from path: "{path}"')
        return OpenMaya.MObject.kNullObj
    elif selection_count == 1:
        return selection.getDependNode(0)
    else:
        parent_path = '|'.join(hierarchy[:-1])
        for i in range(selection_count):
            node = selection.getDependNode(i)
            node_path = node_name(node, include_path=True, include_namespace=has_namespace)
            if node_path.startswith(parent_path):
                return node
            else:
                continue
        logger.debug(f'Cannot locate node from path: "{path}"')
        return OpenMaya.MObject.kNullObj


def mobject_by_string(string: str) -> OpenMaya.MObject | None:
    """
    Returns an MObject from given string.

    :param str string: string to check.
    :return: Maya object instance from given string.
    :rtype: OpenMaya.MObject or None
    :raises TypeError: if given strig is not valid.
    """

    # Check if string contains an attribute.
    is_name = __name_regex__.match(string)
    is_path = __path_regex__.match(string)
    is_uuid = __uuid_regex__.match(string)

    if is_name:
        return mobject_by_name(string)
    elif is_path:
        return mobject_by_path(string)
    elif is_uuid:
        return mobject_by_uuid(string)
    else:
        raise TypeError(f'getMObjectByName() expects a valid string ("{string}" given)!')


def mobject_by_uuid(uuid: str | OpenMaya.MUuid) -> OpenMaya.MObject | list[OpenMaya.MObject] | None:
    """
    Returns an MObject from the given UUID.
    If multiples nodes are found with the same UUID, a list will be returned.

    :param OpenMaya.MUuid uuid: UUID to get object for.
    :return: Maya object instance from given uuid.
    :rtype: OpenMaya.MObject or list[OpenMaya.MObject] or None
    """

    nodes = list(iterate_nodes_by_uuid(uuid))
    if not nodes:
        return None

    if len(nodes) == 1:
        return nodes[0]

    return nodes


def mobject_by_handle(handle: OpenMaya.MObjectHandle) -> OpenMaya.MObject:
    """
    Returns an MObject from given MObjectHandle.

    :param OpenMaya.MObjectHandle handle: Maya object handle.
    :return: Maya object instance from given handle.
    :rtype: OpenMaya.MObject
    """

    return handle.object()


def mobject_by_dag_path(dag_path: OpenMaya.MDagPath) -> OpenMaya.MObject:
    """
    Returns an MObject from given MDagPath.

    :param OpenMaya.MDagPath dag_path: DAG path instance.
    :return: Maya object instance from given dag path.
    :rtype: OpenMaya.MObject
    """

    return dag_path.node()


__get_mobject__ = {
    'str': mobject_by_string,
    'MUuid': mobject_by_uuid,
    'MObjectHandle': mobject_by_handle,
    'MDagPath': mobject_by_dag_path
}


def mobject(
        value: str | OpenMaya.MObject | OpenMaya.MObjectHandle | OpenMaya.MDagPath) -> OpenMaya.MObject | None:
    """
    Returns an MObject for the input scene object.

    :param str or OpenMaya.MObject or OpenMaya.MObjectHandle or OpenMaya.MDagPath value: Maya node to get MObject for.
    :return: Maya object instance from given name.
    :rtype: OpenMaya.MObject or None
    :raises exceptions.MissingObjectByNameError: if no node with given name exists.
    :raises TypeError: if given node is not a valid Maya node.
    """

    if isinstance(value, OpenMaya.MObject):
        return value

    type_name = type(value).__name__
    func = __get_mobject__.get(type_name, None)
    if func is not None:
        return func(value)
    else:
        raise TypeError(f'mobject() expects {tuple(__get_mobject__.keys())} ({type(value).__name__} given)')


def demote_mobject(node: OpenMaya.MObject) -> OpenMaya1.MObject:
    """
    Converts given MObject back into the legacy API type.

    :param OpenMaya.MObject node: Maya object from OpenMaya API 2.0
    :return: Maya object from OpenMaya API 1.0
    :rtype: OpenMaya1.MObject
    :raises TypeError: if given MObject is not from the expected type.
    ..warning:: This method only supports dependency/dag nodes!
    """

    if not isinstance(node, OpenMaya.MObject):
        raise TypeError('demote_mobject() expects the new MObject type!')

    # Get full path name from node.
    if node.hasFn(OpenMaya.MFn.kDagNode):
        found_dag_path = OpenMaya.MDagPath.getAPathTo(node)
        full_path_name = found_dag_path.fullPathName()
    elif node.hasFn(OpenMaya.MFn.kDependencyNode):
        full_path_name = OpenMaya.MFnDependencyNode(node).absoluteName()
    else:
        raise TypeError(f'demote_mobject() expects a dependency node ({node.apiTypeStr} given)!')

    # Add name to legacy selection list.
    selection_list = OpenMaya1.MSelectionList()
    selection_list.add(full_path_name)

    legacy_depend_node = OpenMaya1.MObject()
    selection_list.getDependNode(0, legacy_depend_node)

    return legacy_depend_node


def promote_mobject(node: OpenMaya1.MObject) -> OpenMaya.MObject:
    """
    Converts given MObject into the new API type.

    :param OpenMaya1.MObject node: Maya object from OpenMaya API 1.0
    :return: Maya object from OpenMaya API 2.0
    :rtype: OpenMaya.MObject
    :raises TypeError: if given MObject is not from the expected type.
    ..warning:: This method only supports dependency/dag nodes!
    """

    if not isinstance(node, OpenMaya1.MObject):
        raise TypeError('promote_mobject() expects the legacy MObject type!')

    # Get full path name from node.
    if node.hasFn(OpenMaya1.MFn.kDagNode):
        dag_path_found = OpenMaya1.MDagPath()
        OpenMaya1.MDagPath.getAPathTo(node, dag_path_found)
        full_path_name = dag_path_found.fullPathName()
    elif node.hasFn(OpenMaya1.MFn.kDependencyNode):
        full_path_name = OpenMaya.MFnDependencyNode(node).absoluteName()
    else:
        raise TypeError(f'promote_mobject() expects a dependency node ({node.apiTypeStr} given)!')

    # Add name to selection list.
    selection_list = OpenMaya.MSelectionList()
    selection_list.add(full_path_name)

    return selection_list.getDependNode(0)


def mobject_handle(node: str | OpenMaya.MObject | OpenMaya.MObjectHandle | OpenMaya.MDagPath) -> OpenMaya.MObjectHandle:
    """
    Returns object handle for the given node.

    :param str or OpenMaya.MObject or OpenMaya.MObjectHandle or OpenMaya.MDagPath node: node to get handle of.
    :return: node handle.
    :rtype: OpenMaya.MObjectHandle
    """

    if isinstance(node, OpenMaya.MObjectHandle):
        return node
    else:
        return OpenMaya.MObjectHandle(mobject(node))


def uniquify_objects(objects: list[OpenMaya.MObject]) -> OpenMaya.MObjectArray:
    """
    Returns a unique list of objects from the given list of objects.

    :param list[OpenMaya.MObject] objects: list of objects.
    :return: unique list of objects from the given list of objects.
    :rtype: OpenMaya.MObjectArray
    """

    handles = list(map(OpenMaya.MObjectHandle, objects))
    return OpenMaya.MObjectArray(list({handle.hashCode(): handle.object() for handle in handles}.values()))


def node_name(
        node: str | OpenMaya.MObject | OpenMaya.MDagPath, include_path: bool = False,
        include_namespace: bool = False) -> str:
    """
    Returns the name of the given node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get name from.
    :param bool include_path: whether to include node full path.
    :param bool include_namespace: whether to include node namespace.
    :return: node name.
    :rtype: str
    """

    node = mobject(node)
    if not node.hasFn(OpenMaya.MFn.kDependencyNode):
        return ''

    if include_path:
        return '|'.join(
            [node_name(ancestor, include_namespace=include_namespace) for ancestor in trace_hierarchy(node)])
    elif include_namespace:
        return f'{node_namespace(node)}:{node_name(node)}'
    else:
        return strip_all(OpenMaya.MFnDependencyNode(node).name())


def node_namespace(node: str | OpenMaya.MObject | OpenMaya.MDagPath) -> str:
    """
    Returns the namespace of the given node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get namespace from.
    :return: node namespace.
    :rtype: str
    """

    return OpenMaya.MFnDependencyNode(mobject(node)).namespace


def node_uuid(node: str | OpenMaya.MObject | OpenMaya.MDagPath, as_string: bool = False) -> str | OpenMaya.MUuid:
    """
    Returns the UUID from the given node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get UUID from.
    :param bool as_string: whether to return UUID as a string.
    :return: object UUID.
    :rtype: str or OpenMaya.MUuid
    """

    uuid = OpenMaya.MFnDependencyNode(mobject(node)).uuid()
    return uuid.asString() if as_string else uuid


def node_hash_code(node: str | OpenMaya.MObject | OpenMaya.MDagPath) -> int:
    """
    Returns a hash code from the given node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get hash code from.
    :return: node hash code.
    :rtype: int
    """

    return mobject_handle(node).hashCode()


def world_node() -> OpenMaya.MObject:
    """
    Return world node.

    :return: world node.
    :rtype: OpenMaya.MObject
    """

    return list(iterate_nodes(api_type=OpenMaya.MFn.kWorld))[0]


def iterate_nodes(
        api_type: int = OpenMaya.MFn.kDependencyNode, type_name: str | None = None) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields dependency nodes.
    Default arguments will yield all nodes derived from the given type.

    :param int api_type: dependency API type
    :param str or None type_name: optional type name to filter by.
    :return: iterated nodes.
    :rtype: Iterator[OpenMaya.MObject]
    """

    if not helpers.is_null_or_empty(type_name):
        # Yield nodes from `ls` command.
        node_names = cmds.ls(type=type_name, long=True)
        for node_name in node_names:
            yield mobject_by_name(node_name)
    else:
        # Initialize dependency node iterator.
        iter_depend_nodes = OpenMaya.MItDependencyNodes(api_type)
        while not iter_depend_nodes.isDone():
            current_node = iter_depend_nodes.thisNode()
            yield current_node
            iter_depend_nodes.next()


def iterate_nodes_by_namespace(*namespaces: str | list[str], recurse: bool = False) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields dependency nodes from the given namespace.

    :param str or list[str] namespaces: namespace(s) to find dependency nodes from.
    :param bool recurse: whether to recursively find nodes.
    :return: iterated dependency nodes from given namespace(s).
    :rtype: Iterator[OpenMaya.MObject]
    """

    for name in namespaces:
        if not OpenMaya.MNamespace.namespaceExists(name):
            logger.warning(f'Cannot locate "{name}" namespace!')
            continue

        # Iterate through namespace objects.
        namespace = OpenMaya.MNamespace.getNamespaceFromName(name)
        for depend_node in namespace.getNamespaceObjects(recurse=recurse):
            yield depend_node


def iterate_nodes_by_uuid(*uuids: str | OpenMaya.MUuid | tuple[str | OpenMaya.MUuid]) -> Iterator[OpenMaya.MObject]:
    """
    Generator function that yields dependency nodes with the given UUID.

    :param tuple[str or OpenMaya.MUuid] uuids: uuids.
    :return: iterated nodes.
    :rtype: Iterator[OpenMaya.MObject]
    """

    for uuid in uuids:
        uuid = OpenMaya.MUuid(uuid) if isinstance(uuid, str) else uuid
        selection = OpenMaya.MSelectionList()
        selection.add(uuid)
        for i in range(selection.length()):
            yield selection.getDependNode(i)


def iterate_nodes_by_pattern(
        *patterns: str | list[str], api_type: int = OpenMaya.MFn.kDependencyNode,
        exact_type: bool = False) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields any nodes whose name matches the given patterns.

    :param str or list[str] patterns: pattern(s) to filter by.
    :param int api_type: API type to filter nodes by.
    :param bool exact_type: whether to ignore subtypes.
    :return: iterated nodes whose name matches the given patterns.
    :rtype: Iterator[OpenMaya.MObject]
    """

    selection_list = OpenMaya.MSelectionList()
    for pattern in patterns:
        try:
            selection_list.add(pattern)
        except RuntimeError:
            continue

    selection_count = selection_list.length()
    for i in range(selection_count):
        node = selection_list.getDependNode(i)
        if exact_type and node.apiType() == api_type:
            yield node
        elif not exact_type and node.hasFn(api_type):
            yield node


def iterate_visible_nodes() -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields transform with visible shapes.

    :return: iterated transform with visible shapes.
    :rtype: Iterator[OpenMaya.MObject]
    """

    for node in iterate_nodes(api_type=OpenMaya.MFn.kTransform):
        is_visible = [dag_path(shape).isVisible() for shape in iterate_shapes(node)]
        if all(is_visible) and len(is_visible) > 0:
            yield node


def iterate_plugin_nodes(type_name: str) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields plugin derived nodes based on the given type name.

    :param str type_name:plugin type name to filter by.
    :return: iterated plugin derived nodes based on the given type name.
    :rtype: Iterator[OpenMaya.MObject]
    ..note:: The type name is defined through the "MFnPlugin::registerNode()" method as the first argument.
    ..warning:: This method will not respect subclasses on user plugins!
    """

    iter_depend_nodes = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kPluginDependNode)
    fn_depend_node = OpenMaya.MFnDependencyNode()
    while not iter_depend_nodes.isDone():
        current_node = iter_depend_nodes.thisNode()
        fn_depend_node.setObject(current_node)
        if fn_depend_node.typeName == type_name:
            yield current_node
        iter_depend_nodes.next()


def iterate_dependencies(
        node: OpenMaya.MObject, api_type: int, type_name: str = '',
        direction: int = OpenMaya.MItDependencyGraph.kDownstream,
        traversal: int = OpenMaya.MItDependencyGraph.kDepthFirst) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields dependencies based on the given criteria.

    :param OpenMaya.MObject node: node to find dependencies of.
    :param int api_type: API type to filter by.
    :param str type_name: optional type name to filter by.
    :param int direction: direction to traverse in the node graph.
    :param int traversal: order of traversal.
    :return: iterated dependencies based on the given criteria.
    :rtype: Iterator[OpenMaya.MObject]
    """

    iter_dep_graph = OpenMaya.MItDependencyGraph(
        node, filter=api_type, direction=direction, traversal=traversal, level=OpenMaya.MItDependencyGraph.kNodeLevel)

    fn_depend_node = OpenMaya.MFnDependencyNode()
    while not iter_dep_graph.isDone():
        current_node = iter_dep_graph.currentNode()
        fn_depend_node.setObject(current_node)
        if fn_depend_node.typeName == type_name or helpers.is_null_or_empty(type_name):
            yield current_node
        iter_dep_graph.next()


def depends_on(node: OpenMaya.MObject, api_type: int = OpenMaya.MFn.kDependencyNode) -> list[OpenMaya.MObject]:
    """
    Returns a list of nodes that this object is dependent on.

    :param OpenMaya.MObject node: node to get dependents nodes of.
    :param int api_type: API type to filter nodes by.
    :return: list of nodes that this object is dependent on.
    :rtype: list[OpenMaya.MObject]
    """

    return list(iterate_dependencies(node, api_type, direction=OpenMaya.MItDependencyGraph.kUpstream))


def dependents(node: OpenMaya.MObject, api_type: int = OpenMaya.MFn.kDependencyNode) -> list[OpenMaya.MObject]:
    """
    Returns a list of nodes that are dependent of this object.

    :param OpenMaya.MObject node: node to get dependents nodes of.
    :param int api_type: API type to filter nodes by.
    :return: list of nodes that are dependent of this object.
    :rtype: list[OpenMaya.MObject]
    """

    return list(iterate_dependencies(node, api_type, direction=OpenMaya.MItDependencyGraph.kDownstream))


def dag_path(value: str | OpenMaya.MObject | OpenMaya.MObjectHandle | OpenMaya.MDagPath) -> OpenMaya.MDagPath:
    """
    Returns the MDagPath for the given value.

    :param str or OpenMaya.MObject or OpenMaya.MObjectHandle or OpenMaya.MDagPath value: node to get dag path of.
    :return: dag path instance.
    :rtype: OpenMaya.MDagPath
    ..note:: This method expects the value to be derived from a dag node in order to work!
    """

    return value if isinstance(value, OpenMaya.MDagPath) else OpenMaya.MDagPath.getAPathTo(mobject(value))


def shape_directly_below(node: OpenMaya.MObject | OpenMaya.MDagPath) -> OpenMaya.MObject | None:
    """
    Returns the shape node directly below the given transform.

    :param OpenMaya.MObject or OpenMaya.MDagPath node: node to get shape of.
    :return: shape directly below given transform node.
    :rtype: OpenMaya.MObject or None
    :raises TypeError: if more than 1 shape is found.
    """

    shapes = list(iterate_shapes(node))
    num_shapes = len(shapes)
    if num_shapes == 0:
        return None
    elif num_shapes == 1:
        return shapes[0]
    else:
        raise TypeError(f'shape_directly_below() expects to find 1 shape ({num_shapes}s found)!')


def parent(node: OpenMaya.MObject) -> OpenMaya.MObject | None:
    """
    Returns the parent of the given node.

    :param OpenMaya.MObject node: node to get parent of.
    :return: parent node.
    :rtype: OpenMaya.MObject or None
    """

    node_dag_path = dag_path(node)
    fn_dag_node = OpenMaya.MFnDagNode(node_dag_path)
    parent_count = fn_dag_node.parentCount()
    if parent_count == 0:
        return OpenMaya.MObject.kNullObj

    # Make sure parent is not world.
    found_parent = fn_dag_node.parent(0)
    if not found_parent.hasFn(OpenMaya.MFn.kWorld):
        return found_parent

    return OpenMaya.MObject.kNullObj


def trace_hierarchy(node: OpenMaya.MObject) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields the nodes leading up to, and including, the given transform node.

    :param OpenMaya.MObject node: node to get hierarchy of.
    :return: Iterator[OpenMaya.MObject]
    """

    yield from reversed(list(iterate_ancestors(node)))
    yield node


def iterate_ancestors(
        node: str | OpenMaya.MObject | OpenMaya.MDagPath,
        api_type: int = OpenMaya.MFn.kTransform) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields ancestors for the given transform node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get namespace of.
    :param int api_type: optional API type to filter ancestors by.
    :return: iterated ancestors.
    :rtype: Iterator[OpenMaya.MObject]
    """

    ancestor = parent(node)
    while not ancestor.isNull():
        if ancestor.hasFn(api_type):
            yield ancestor
            ancestor = parent(ancestor)
        else:
            break


def iterate_children(
        node: str | OpenMaya.MObject | OpenMaya.MDagPath,
        api_type: int = OpenMaya.MFn.kTransform) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields children from the given dag node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to iterate children of.
    :param int api_type: optional API type to filter children by.
    :return: iterated children.
    :rtype: Iterator[OpenMaya.MObject]
    """

    node = mobject(node)
    if not node.hasFn(OpenMaya.MFn.kDagNode):
        return iter([])

    # Iterate through children.
    found_dag_path = dag_path(node)
    fn_dag_node = OpenMaya.MFnDagNode(found_dag_path)

    child_count = fn_dag_node.childCount()
    for i in range(child_count):
        child = fn_dag_node.child(i)
        if child.hasFn(api_type):
            yield child


def iterate_descendants(
        node: str | OpenMaya.MObject | OpenMaya.MDagPath,
        api_type: int = OpenMaya.MFn.kTransform) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields descendants from the given dag node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to iterate descendants of.
    :param int api_type: optional API type to filter descendants by.
    :return: iterated descendants.
    :rtype: Iterator[OpenMaya.MObject]
    """

    queue = deque([node])
    while len(queue) > 0:
        # Pop descendant and yield children
        descendant = queue.popleft()
        children = list(iterate_children(descendant, api_type=api_type))
        queue.extend(children)
        yield from children


def iterate_shapes(
        node: OpenMaya.MObject | OpenMaya.MDagPath,
        api_type: int = OpenMaya.MFn.kShape) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields shapes from the given dag node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to iterate shapes of.
    :param int api_type: optional API type to filter shapes by.
    :return: iterated descendants.
    :rtype: Iterator[OpenMaya.MObject]
    """

    fn_dag_node = OpenMaya.MFnDagNode()
    for child in iterate_children(node, api_type=api_type):
        # Check if child is intermediate object.
        fn_dag_node.setObject(child)
        if not fn_dag_node.isIntermediateObject:
            yield child


def iterate_intermediate_objects(
        node: OpenMaya.MObject | OpenMaya.MDagPath,
        api_type: int = OpenMaya.MFn.kShape) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields intermediate objects from the given dag node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to iterate intermediate objects of.
    :param int api_type: optional API type to filter intermediate objects by.
    :return: iterated descendants.
    :rtype: Iterator[OpenMaya.MObject]
    """

    fn_dag_node = OpenMaya.MFnDagNode()
    for child in iterate_children(node, api_type=api_type):
        # Check if child is intermediate object.
        fn_dag_node.setObject(child)
        if fn_dag_node.isIntermediateObject:
            yield child


def iterate_function_sets() -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields function sets compatible with dependency nodes.

    :return: iterated function sets.
    :rtype: Iterator[OpenMaya.MObject]
    """

    for (key, value) in chain(OpenMaya.__dict__.items(), OpenMayaAnim.__dict__.items()):
        # Check if pair matches criteria
        if key.startswith('MFn') and issubclass(value, OpenMaya.MFnDependencyNode):
            yield value


def iterate_active_component_selection() -> Iterator[tuple[OpenMaya.MDagPath, OpenMaya.MObject]]:
    """
    Returns a generator that yields the active component selection.

    :return: tuple containing a dag path and a component object.
    :rtype: Iterator[tuple[OpenMaya.MDagPath, OpenMaya.MObject]]
    """

    # Get active selection
    # Unfortunately the rich selection method will raise a runtime error if the selection is empty
    # So we have to wrap this in a try/catch in order to preserve weighted component data

    try:
        selection = OpenMaya.MGlobal.getRichSelection().getSelection()
    except RuntimeError as exception:
        logger.debug(exception)
        selection = OpenMaya.MGlobal.getActiveSelectionList()

    # Iterate through selection.
    iter_selection = OpenMaya.MItSelectionList(selection, OpenMaya.MFn.kMeshComponent)
    while not iter_selection.isDone():
        # Check if item has a valid component.
        found_dag_path, component = iter_selection.getComponent()
        if found_dag_path.isValid() and not component.isNull():
            yield found_dag_path, component
        else:

            logger.debug(f'Skipping invalid component selection on {found_dag_path.partialPathName()}.')
        iter_selection.next()


def iterate_associated_deformers(
        node: OpenMaya.MObject | OpenMaya.MDagPath,
        api_type: int = OpenMaya.MFn.kGeometryFilt) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields deformers associated with the given object.

    :param OpenMaya.MObject or OpenMaya.MDagPath node: node to iterate deformers of.
    :param int api_type: API type to filter deformers by.
    :return: iterated deformers associated with the given object.
    :rtype: Iterator[OpenMaya.MObject]
    ..note:: It is safe to supply either the transform, shape or deformer component.
    """

    node = mobject(node)
    if node.hasFn(OpenMaya.MFn.kTransform):
        return iterate_associated_deformers(shape_directly_below(node), api_type=api_type)
    elif node.hasFn(OpenMaya.MFn.kGeometryFilt):
        return iterate_associated_deformers(dependents(node, api_type=OpenMaya.MFn.kShape)[0], api_type=api_type)
    elif node.hasFn(OpenMaya.MFn.kShape):
        return iterate_dependencies(node, api_type, direction=OpenMaya.MItDependencyGraph.kUpstream)
    else:
        logger.warning(f'iterate_associated_deformers() expects a shape node ({node.apiTypeStr} given)!')


def associated_deformers(
        node: str | OpenMaya.MObject | OpenMaya.MDagPath,
        api_type: int = OpenMaya.MFn.kGeometryFilt) -> list[OpenMaya.MObject]:
    """
    Returns a list of deformers associated to given shape node.

    :param str or OpenMaya.MObject or OpenMaya.MDagPath node: node to get associated deformers of.
    :param int api_type: API type to filter deformers by.
    :return: list of associated deformers.
    :rtype: list[OpenMaya.MObject]
    """

    return list(iterate_associated_deformers(node, api_type=api_type))


def iterate_deformers_from_selection(api_type: int = OpenMaya.MFn.kGeometryFilt) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields deformers from the active selection.

    :param int api_type: API type to filter deformers by.
    :return: iterated deformers from current selection.
    :rtype: Iterator[OpenMaya.MObject]
    """

    for depend_node in iterate_active_selection(api_type=OpenMaya.MFn.kDagNode):
        for deformer in iterate_associated_deformers(depend_node, api_type=api_type):
            yield deformer


def find_deformer_by_type(node: OpenMaya.MObject | OpenMaya.MDagPath, api_type: int) -> OpenMaya.MObject | None:
    """
    Returns the deformer with given from the given node.

    :param OpenMaya.MObject or OpenMaya.MDagPath node: node to get deformer from.
    :param int api_type: API type of the deformer to retrieve.
    :return: found deformer of given type.
    :rtype: OpenMaya.MObject or None
    :raises TypeError: ig more than one deformer found.
    """

    deformers = associated_deformers(node, api_type=api_type)
    num_deformers = len(deformers)
    if num_deformers == 0:
        return None
    elif num_deformers == 1:
        return deformers[0]
    else:
        raise TypeError(f'find_deformer_by_type() expects 1 deformer ({num_deformers} given)!')


def decompose_deformer(deformer: OpenMaya.MObject) -> tuple[OpenMaya.MObject, OpenMaya.MObject, OpenMaya.MObject]:
    """
    Breaks down a deformer into 3 components: transform, shape and intermediate object.

    :param OpenMaya.MObject deformer: deformer to decompose.
    :return: decomposed deformer.
    :rtype: tuple[OpenMaya.MObject, OpenMaya.MObject, OpenMaya.MObject]
    :raises TypeError:  if the deformer was not setup correctly.
    """

    shapes = dependents(deformer, api_type=OpenMaya.MFn.kShape)
    num_shapes = len(shapes)
    if num_shapes == 1:
        shape = shapes[0]
    else:
        raise TypeError(f'decompose_deformer() expects 1 shape node ({num_shapes} found)!')

    # Locate transform from shape node.
    transform = OpenMaya.MFnDagNode(shape).parent(0)

    # Locate intermediate objects upstream.
    intermediate_objects = depends_on(deformer, api_type=OpenMaya.MFn.kShape)
    num_intermediate_objects = len(intermediate_objects)
    if num_intermediate_objects == 1:
        intermediate_object = intermediate_objects[0]
    else:
        raise TypeError(f'decompose_deformer() expects 1 intermediate object ({num_intermediate_objects} found)!')

    return transform, shape, intermediate_object


def strip_dag_path(name: str) -> str:
    """
    Remove any separator from the given name.

    :param str name: dag path to strip.
    :return: stripped dag path.
    :rtype: str
    """

    return name.split('|')[-1]


def strip_namespace(name: str) -> str:
    """
    Removes any colon characters from the given name.

    :param str name: dag path to remove namespaces from.
    :return: path without namespaces.
    :rtype: str
    """

    return name.split(':')[-1]


def strip_all(name: str) -> str:
    """
    Removes any separator and colon characters from given name.

    :param str name: dag path to strip.
    :return: stripped dag path.
    :rtype: str
    """

    name = strip_dag_path(name)
    name = strip_namespace(name)

    return name


def absolutify(name: str, namespace: str = '') -> str:
    """
    Ensures the given name starts with the root namespace.

    :param str name: name.
    :param str namespace: namespace.
    :return: name with namespace.
    :rtype: str
    """

    if not name.startswith(':'):
        return f'{namespace}:{name}'
    else:
        return name


def is_dg_type(type_name: str | int) -> bool:
    """
    Returns whether given type name is derived from a DG node.

    :param str or int type_name: type name to check.
    :return: True if given type name is derived from a DG node; False otherwise.
    :rtype: bool
    :raises TypeError: if type_name argument is not a valid type.
    """

    if isinstance(type_name, str):
        return OpenMaya.MNodeClass(type_name).hasAttribute('message')
    elif isinstance(type_name, integer_types):
        return OpenMaya.MFnDependencyNode().hasObj(type_name)
    else:
        raise TypeError(f'is_dg_type() expects either a str or int ({type(type_name).__name__} given)!')


def is_dag_type(type_name: str | int) -> bool:
    """
    Returns whether given type name is derived from a DAG node.

    :param str or int type_name: type name to check.
    :return: True if given type name is derived from a DAG node; False otherwise.
    :rtype: bool
    :raises TypeError: if type_name argument is not a valid type.
    """

    if isinstance(type_name, str):
        return OpenMaya.MNodeClass(type_name).hasAttribute('visibility')
    elif isinstance(type_name, integer_types):
        return OpenMaya.MFnDagNode().hasObj(type_name)
    else:
        raise TypeError(f'is_dag_type() expects either a str or int ({type(type_name).__name__} given)!')


def create_selection_list(items: list[Any]) -> OpenMaya.MSelectionList:
    """
    Retursn a selection list from the given objects.

    :param list[Any] items: lits of objects.
    :return: selection list instance.
    :rtype: OpenMaya.MSelectionList
    """

    selection = OpenMaya.MSelectionList()
    for item in items:
        depend_node = mobject(item)
        if depend_node.isNull():
            continue
        if depend_node.hasFn(OpenMaya.MFn.kDagNode):
            found_dag_path = OpenMaya.MDagPath.getAPathTo(depend_node)
            selection.add(found_dag_path)
        else:
            selection.add(depend_node)

    return selection


def create_node(
        type_name: str, name: str = '', parent: str | OpenMaya.MObject | OpenMaya.MDagPath | None = None,
        skip_select: bool = True) -> OpenMaya.MObject:
    """
    Creates a new dependency node from the given type name.

    :param str type_name: type name of the node to create.
    :param str name: optional node name.
    :param str or OpenMaya.MObject or OpenMaya.MDagPath or None parent: optional parent node.
    :param bool skip_select: whehter to add newly created node to the active selection.
    :return: newly created node.
    :rtype: OpenMaya.MObject
    """

    node = OpenMaya.MObject.kNullObj
    parent = OpenMaya.MObject.kNullObj if parent is None else mobject(parent)

    if is_dag_type(type_name):
        modifier = OpenMaya.MDagModifier()
        node = modifier.createNode(type_name, parent=parent)
    else:
        modifier = OpenMaya.MDGModifier()
        node = modifier.createNode(type_name)

    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()

    # Check if a name was supplied.
    if not helpers.is_null_or_empty(name):
        rename_node(node, name)

    # Check if node should be selected.
    if not skip_select:
        selection_list = create_selection_list([node])
        OpenMaya.MGlobal.setActiveSelectionList(selection_list)

    return node


def create_component(
        indices: OpenMaya.MIntArray, api_type: int = OpenMaya.MFn.kSingleIndexedComponent) -> OpenMaya.MObject:
    """
    Creates a component object based on a list of elements and an API enumerator constant.

    :param OpenMaya.MIntArray indices: list of elements.
    :param int api_type: API type to create component for.
    :return: newly created component.
    :rtype: OpenMaya.MObject
    :raises TypeError: if given argument types are not valid.
    """

    if isinstance(indices, OpenMaya.MIntArray):
        # Create component from function set and add elements to component.
        fn_single_index_component = OpenMaya.MFnSingleIndexedComponent()
        component = fn_single_index_component.create(api_type)
        fn_single_index_component.addElements(indices)
        return component
    elif isinstance(indices, (list, set, tuple, deque)):
        return create_component(OpenMaya.MIntArray(indices), api_type=api_type)
    elif isinstance(indices, int):
        return create_component(OpenMaya.MIntArray([indices]), api_type=api_type)
    elif indices is None:
        return create_component(OpenMaya.MIntArray(), api_type=api_type)
    else:
        raise TypeError(f'create_component() expects a list ({type(indices).__name__} given)!')


def rename_node(node: OpenMaya.MObject, new_name: str, modifier: OpenMaya.MDGModifier | None = None) -> str:
    """
    Renames the given node to the new name.

    :param OpenMaya.MObject node: node to rename.
    :param str new_name: new node name.
    :param OpenMaya.MDGModifier or None modifier: optional modifier to use to rename the node.
    :return: new node name.
    :rtype: str
    """

    modifier = modifier or OpenMaya.MDGModifier()

    modifier.renameNode(node, new_name)
    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()

    return new_name


def reparent_node(
        node: OpenMaya.MObject, other_node: OpenMaya.MObject,
        modifier: OpenMaya.MDagModifier | None = None) -> OpenMaya.MObject:
    """
    Renames the given node to the new name.

    :param OpenMaya.MObject node: node to re-parent.
    :param OpenMaya.MObject other_node: parent node.
    :param OpenMaya.MDagModifier or None modifier: optional modifier to use to re-parent the node.
    :return: parent node.
    :rtype: OpenMaya.MObject
    """

    modifier = modifier or OpenMaya.MDagModifier()

    modifier.reparentNode(node, other_node)
    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()

    return other_node


def delete_node(node: OpenMaya.MObject, include_children: bool = False):
    """
    Deletes the given dependency node from the scene.
    TODO: Add undo support!

    :param OpenMaya.MObject node: object to delete.
    :param bool include_children: whether to delete children.
    ..info:: In order to prevent any other nodes from being deleted this method breaks all connections before deleting
        the node.
    """

    # Break all connections to node.
    fn_depend_node = OpenMaya.MFnDependencyNode(node)
    plugs = fn_depend_node.getConnections()

    modifier = OpenMaya.MDagModifier()
    for plug in plugs:
        # Check if plug has any source or destination connections.
        source = plug.source()
        if not source.isNull:
            logger.debug(f'Breaking connection: {source.info} and {plug.info}')
            modifier.disconnect(source, plug)
        destinations = plug.destinations()
        for destination in destinations:
            logger.debug(f'Breaking connection: {plug.info} and {destination.info}')
            modifier.disconnect(plug, destination)

    # Check if children should be deleted.
    if include_children:
        # Delete all children in reverse order.
        for child in reversed(list(iterate_descendants(node, api_type=OpenMaya.MFn.kDagNode))):
            modifier.deleteNode(child, includeParents=False)
    else:
        # Un-parent immediate children and delete any shapes.
        world = world_node()
        for child in iterate_children(node):
            modifier.reparentNode(child, world)
        for shape in iterate_shapes(node):
            modifier.deleteNode(shape, includeParents=False)

    # Delete node and execute modifier stack
    modifier.deleteNode(node, includeParents=False)
    modifier.doIt()


def child_paths(dag_path):
    """
    Returns all MDagPaths that are child of the given MDagPath.

    :param MDagPath dag_path: DAG path we want to retrieve childs of.
    :return: list of children DAG paths.
    :rtype: list(MDagPath)
    """

    out_paths = [child_path_at_index(dag_path, i) for i in range(dag_path.childCount())]

    return out_paths


def child_path_at_index(dag_path, index):
    """
    Returns MDagPath of the child node at given index from given MDagPath.

    :param MDagPath dag_path: DAG path we want to retrieve child at index of.
    :param int index: index of the child we want to retrieve relative to the given DAG path hierarchy.
    :return: child DAG path at given index.
    :rtype: MDagPath
    """

    existing_child_count = dag_path.childCount()
    if existing_child_count < 1:
        return None
    index = index if index >= 0 else dag_path.childCount() - abs(index)
    copy_path = OpenMaya.MDagPath(dag_path)
    copy_path.push(dag_path.child(index))

    return copy_path


def child_paths_by_fn(dag_path, child_fn):
    """
    Returns all children paths of the given MDagPath that supports given MFn type.

    :param MDagPath dag_path: DAG path we want to retrieve of.
    :param MFn child_fn: Maya function type returned child need to have.
    :return: list of child DAG paths with the given Maya function type.
    :rtype: list(MDagPath).
    """

    return [child_path for child_path in child_paths(dag_path) if child_path.hasFn(child_fn)]


def child_transforms(dag_path):
    """
    Returns all the child transforms of the given MDagPath.

    :param OpenMaya.MDagPath dag_path: DAG path we want to retrieve child transforms of.
    :return: list of all transforms below given path.
    :rtype: list(MDagPath)
    """

    return child_paths_by_fn(dag_path, OpenMaya.MFn.kTransform)


def iterate_shape_paths(dag_path, filter_types=None):
    """
    Generator function that returns all the shape DAG paths directly below the given DAG path.

    :param MDagPath dag_path: DAG path to search shapes of.
    :param list(str) filter_types: list of tiler shapes for the shapes to return.
    :return: generator of shape DAG paths.
    :rtype: generator(MDagPath)
    """

    filter_types = helpers.force_list(filter_types)
    for i in range(dag_path.numberOfShapesDirectlyBelow()):
        shape_dag_path = OpenMaya.MDagPath(dag_path)
        shape_dag_path.extendToShape(i)
        if not filter_types or shape_dag_path.apiType() in filter_types:
            yield shape_dag_path


def shapes_paths(dag_path, filter_types=None):
    """
    Returns all the given shape DAG paths directly below the given DAG path as a list.

    :param MDagPath dag_path: DAG path to search shapes of.
    :param list(str) filter_types: list of tiler shapes for the shapes to return.
    :return: list of shape DAG paths.
    :rtype: list(MDagPath)
    """

    return list(iterate_shape_paths(dag_path, filter_types=filter_types))
