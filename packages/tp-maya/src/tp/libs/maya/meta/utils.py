"""Utility functions for the meta system.

This module provides utility functions for working with metanodes in Maya,
including scene iteration, node searching, and network operations.
"""

from __future__ import annotations

import inspect
from collections.abc import Iterable, Iterator

from loguru import logger

from maya.api import OpenMaya

from ..wrapper import DGNode
from .constants import META_CLASS_ATTR_NAME
from .registry import MetaRegistry


def iterate_scene_meta_nodes():
    """Iterate through all scene metanodes and yields them as MetaBase objects.

    This function traverses all dependency nodes in the scene to identify those
    that have the specific meta-attribute defined by `META_CLASS_ATTR_NAME`.
    It yields a `MetaBase` object for each matching node, ensuring efficient
    and filtered access.

    Yields:
        An instance representing a metanode found in the dependency graph.
    """

    from .base import MetaBase

    it = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kAffect)
    while not it.isDone():
        mobj = it.thisNode()
        dep = OpenMaya.MFnDependencyNode(mobj)
        if dep.hasAttribute(META_CLASS_ATTR_NAME):
            yield MetaBase(node=mobj, init_defaults=False)
        it.next()


def find_meta_nodes_by_class_type(class_type: type | str) -> list:
    """Find metanodes in the scene that match the specified class type.

    This function iterates through all metanodes in the scene and collects
    those whose class type matches the provided class type.

    The match is determined by checking the value of the `META_CLASS_ATTR_NAME`
    attribute against the provided class type or its  corresponding `ID` if
    it is a class.

    Args:
        class_type: The class type to match. Can be a class (with an `ID`
            attribute) or a string representing a class type name.

    Returns:
        A list of metanodes matching the specified class type.
    """

    if inspect.isclass(class_type):
        class_type_name = MetaRegistry.registry_name_for_class(class_type)
    else:
        class_type_name = str(class_type)

    return [
        meta_node
        for meta_node in iterate_scene_meta_nodes()
        if meta_node.attribute(META_CLASS_ATTR_NAME).value() == class_type_name
    ]


def find_meta_nodes_by_tag(tag: str) -> list:
    """Find all metanodes in the scene that have the specified tag.

    Args:
        tag: The tag string to search for.

    Returns:
        A list of metanodes with the matching tag.
    """

    return [
        meta_node
        for meta_node in iterate_scene_meta_nodes()
        if meta_node.tag() == tag
    ]


def is_meta_node(node: DGNode) -> bool:
    """Determine whether a given `DGNode` is a meta node.

    This function checks if the provided `DGNode` instance is a metanode.

    Notes:
        A node is considered a metanode if it is an instance of `MetaBase` or
        a subclass thereof, or if it possesses an attribute referencing a
        metaclass registered in the `MetaRegistry`.

    Args:
        node: The node to check for being a meta node.

    Returns:
        True if the node is identified as a metanode, False otherwise.
    """

    from .base import MetaBase

    if isinstance(node, MetaBase) or issubclass(type(node), MetaBase):
        return True

    if not node.hasAttribute(META_CLASS_ATTR_NAME):
        return False

    # noinspection PyProtectedMember
    if not MetaRegistry._CACHE:
        MetaRegistry()

    class_name = node.attribute(META_CLASS_ATTR_NAME).asString()

    # Check both MetaRegistry and PropertyRegistry
    if MetaRegistry.is_in_registry(class_name):
        return True

    # Check PropertyRegistry (imported locally to avoid circular import)
    try:
        from .properties import PropertyRegistry

        if PropertyRegistry.is_in_registry(class_name):
            return True
        if PropertyRegistry.get_hidden(class_name) is not None:
            return True
    except ImportError:
        pass

    return False


def is_meta_node_of_types(node: DGNode, class_types: Iterable[str]) -> bool:
    """Determine if a given node is a metanode of specified types.

    This function checks whether the provided node is a metanode and verifies
    if its metaclass type belongs to the supplied list of class types. It also
    ensures that the metaclass type is registered in the `MetaRegistry`.

    Args:
        node: The specific DGNode instance to check.
        class_types: An iterable collection of string class type names to
            validate against the metaclass type of the node.

    Returns:
        True if the node is a meta node, belongs to one of the specified class
            types, and is in the `MetaRegistry`. `False` otherwise.
    """

    if not is_meta_node(node):
        return False

    type_str = node.attribute(META_CLASS_ATTR_NAME).asString()
    if type_str not in class_types:
        return False

    return MetaRegistry.is_in_registry(type_str)


def create_meta_node_by_type(type_name: str, *args: tuple, **kwargs):
    """Create an instance of a metanode based on the provided type name by
    retrieving the class type from a registry.

    If the class type is found, initializes it with the optional positional
    and keyword arguments. Returns `None` if the type name does not exist in
    the registry.

    Args:
        type_name: The name of the type to retrieve from the meta-registry.
        *args: Positional arguments to pass to the initializer of the
            retrieved class.
        **kwargs: Keyword arguments to pass to the initializer of the
            retrieved class.

    Returns:
        An instance of the metanode corresponding to the provided type name,
            or `None` if no class type is found for the given type name.
    """

    # noinspection PyUnresolvedReferences
    class_type = MetaRegistry().get_type(type_name)
    result = class_type(*args, **kwargs) if class_type is not None else None
    if result is None:
        logger.warning(
            f'No metanode class found for type "{type_name}". '
            "Ensure the type is registered in the `MetaRegistry`. "
            f"Available types: {list(MetaRegistry.types().keys())}"
        )

    return result


def connected_meta_nodes(node: DGNode) -> list:
    """Retrieve a list of metanodes connected to a given input node.

    This function identifies whether the provided node is a metanode. If it is,
    it creates a `MetaBase` object from the node and initializes it with the
    specified parameters.

    For non-meta nodes, the function evaluates the destinations of the
    "message" attribute in the input node to determine if the connected nodes
    are metanodes. For every metanode detected, a corresponding `MetaBase`
    instance is added to the resulting list.

    Args:
        node: A `DGNode` instance representing the input node to check for
            connected metanodes.

    Returns:
        A list of `MetaBase` objects corresponding to the metanodes connected
    """

    from .base import MetaBase

    if is_meta_node(node):
        if isinstance(node, DGNode):
            return [MetaBase(node=node.object(), init_defaults=False)]
        return [node]

    meta_nodes = []
    for destination in node.attribute("message").destinations():
        obj = destination.node()
        if not is_meta_node(obj):
            continue
        meta_nodes.append(MetaBase(node=obj.object(), init_defaults=False))

    return meta_nodes


def is_in_network(node: DGNode) -> bool:
    """Check if a scene node is connected to any meta network.

    This function checks if the given node has its message attribute
    connected to any meta node.

    Args:
        node: The scene node to check.

    Returns:
        True if the node is connected to at least one meta node.

    Example:
        >>> if is_in_network(joint):
        ...     print("Joint is part of a meta network")
    """

    if is_meta_node(node):
        return True

    try:
        message_plug = node.attribute("message")
        for destination in message_plug.destinations():
            dest_node = destination.node()
            if is_meta_node(dest_node):
                return True
    except Exception:
        pass

    return False


def get_network_entries(
    node: DGNode, network_type: type | None = None
) -> list:
    """Get all meta nodes connected to a scene node.

    This function finds all meta nodes that the given scene node is
    connected to. Optionally filters by meta node type.

    Args:
        node: The scene node to query.
        network_type: If provided, only returns meta nodes of this type.
            If None, returns all connected meta nodes.

    Returns:
        List of MetaBase instances connected to the node.

    Example:
        >>> entries = get_network_entries(joint)
        >>> rig_entries = get_network_entries(joint, RigMeta)
    """

    from .base import MetaBase

    entries = []

    if is_meta_node(node):
        # Node itself is a meta node
        meta = MetaBase(node=node.object(), init_defaults=False)
        if network_type is None or isinstance(meta, network_type):
            entries.append(meta)
        return entries

    try:
        message_plug = node.attribute("message")
        for destination in message_plug.destinations():
            dest_node = destination.node()
            if is_meta_node(dest_node):
                meta = MetaBase(node=dest_node.object(), init_defaults=False)
                if network_type is None:
                    entries.append(meta)
                elif isinstance(meta, network_type):
                    entries.append(meta)
                elif (
                    meta.metaclass_type()
                    == MetaRegistry.registry_name_for_class(network_type)
                ):
                    # Re-wrap with correct type
                    entries.append(
                        network_type(
                            node=dest_node.object(), init_defaults=False
                        )
                    )
    except Exception:
        pass

    return entries


def delete_network(root, mod: OpenMaya.MDGModifier | None = None) -> bool:
    """Delete an entire meta network starting from the root node.

    This function recursively deletes all meta nodes in a network,
    starting from the given root and traversing all children.

    Args:
        root: The root meta node of the network to delete.
        mod: Optional modifier for batched operations.

    Returns:
        True if the network was successfully deleted.

    Example:
        >>> root = find_meta_nodes_by_class_type(RigCoreMeta)[0]
        >>> delete_network(root)
    """

    return root.delete_all(mod=mod)


def get_all_meta_nodes_of_type(meta_type: type) -> list:
    """Get all meta nodes of a specific type in the scene.

    This is a convenience wrapper around find_meta_nodes_by_class_type
    that accepts a class type instead of a string.

    Args:
        meta_type: The meta class type to search for.

    Returns:
        List of all meta nodes of the specified type.

    Example:
        >>> all_rigs = get_all_meta_nodes_of_type(RigMeta)
        >>> for rig in all_rigs:
        ...     print(rig.name())
    """

    return find_meta_nodes_by_class_type(meta_type)
