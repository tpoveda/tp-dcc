"""Maya Node Wrapper Module.

This module provides high-level wrapper classes for Maya dependency graph (DG) and
directed acyclic graph (DAG) nodes. It offers an object-oriented interface for
working with Maya nodes using OpenMaya 2.0 API.

The main classes are:
    - DGNode: Base wrapper for dependency graph nodes.
    - DagNode: Wrapper for DAG nodes (transforms, shapes, etc.).
    - Plug: Wrapper for node attributes/plugs.
    - Joint: Specialized wrapper for joint nodes.
    - ContainerAsset: Wrapper for container nodes.
    - ObjectSet: Wrapper for object set nodes.
    - AnimCurve: Wrapper for animation curve nodes.

Example:
    >>> from tp.libs.maya.wrapper import node_by_name, DagNode
    >>> node = node_by_name("pCube1")
    >>> if node:
    ...     print(node.translation())
    ...     node.setTranslation((0, 10, 0))
"""

from __future__ import annotations

import contextlib
from functools import wraps
from typing import Any, Callable, Iterable, Iterator, Type

from loguru import logger

from maya import cmds
from maya.api import OpenMaya, OpenMayaAnim
from tp.libs.python import helpers

from .om import (
    attributetypes,
    constants,  # noqa: F401
    dagutils,
    factory,
    mathlib,
    nodes,
    plugs,
    scene,
)
from .om.apitypes import *  # noqa: F403
from .om.constants import *  # noqa: F403

LOCAL_TRANSLATE_ATTR = "translate"
LOCAL_ROTATE_ATTR = "rotate"
LOCAL_SCALE_ATTR = "scale"
LOCAL_TRANSLATE_ATTRS = ["translateX", "translateY", "translateZ"]
LOCAL_ROTATE_ATTRS = ["rotateX", "rotateY", "rotateZ"]
LOCAL_SCALE_ATTRS = ["scaleX", "scaleY", "scaleZ"]
LOCAL_TRANSFORM_ATTRS = (
    LOCAL_TRANSLATE_ATTRS + LOCAL_ROTATE_ATTRS + LOCAL_SCALE_ATTRS
)


def lock_node_context(fn: Callable) -> Callable:
    """Decorator that temporarily unlocks a node during function execution.

    If the node is locked and not referenced, it will be unlocked before the
    decorated function runs and re-locked afterwards.

    Args:
        fn: The function to decorate. First argument must be a DGNode instance.

    Returns:
        Wrapped function that handles node locking.
    """

    @wraps(fn)
    def locker(*args, **kwargs):
        node = args[0]
        set_locked = False
        if node.isLocked and not node.isReferenced():
            node.lock(False)
            set_locked = True
        try:
            return fn(*args, **kwargs)
        finally:
            if set_locked and node.exists():
                node.lock(True)

    return locker


def lock_node_plug_context(fn: Callable) -> Callable:
    """Decorator that temporarily unlocks a node and its plug during function execution.

    If the node or plug is locked and not referenced, they will be unlocked before
    the decorated function runs and re-locked afterwards.

    Args:
        fn: The function to decorate. First argument must be a Plug instance.

    Returns:
        Wrapped function that handles node and plug locking.
    """

    @wraps(fn)
    def locker(*args, **kwargs):
        plug = args[0]
        node = plug.node()
        set_locked = False
        set_plug_locked = False
        if node.isLocked and not node.isReferenced():
            node.lock(False)
            set_locked = True
        if plug.isLocked:
            plug.lock(False)
            set_plug_locked = True
        try:
            return fn(*args, **kwargs)
        finally:
            if node.exists():
                if set_plug_locked and plug.exists():
                    plug.lock(True)
                if set_locked:
                    node.lock(True)

    return locker


@contextlib.contextmanager
def lock_state_attr_context(
    node: DGNode, attr_names: Iterable[str], state: bool
) -> Iterator[None]:
    """Context manager that temporarily sets lock state for attributes.

    Args:
        node: Node containing the attributes.
        attr_names: Names of attributes to modify lock state.
        state: Lock state to set while in the context.

    Yields:
        None. Attributes are restored to their original lock state on exit.
    """

    attributes = []
    try:
        for attr_name in attr_names:
            attr = node.attribute(attr_name)
            if attr is None:
                continue
            if attr.isLocked != state:
                attributes.append(attr)
                attr.lock(state)
        yield
    finally:
        for attr in attributes:
            if not attr:
                continue
            attr.lock(not state)


# noinspection PyPep8Naming
class DGNode:
    """Wrapper class for Maya dependency graph nodes.

    Provides a Pythonic interface for working with Maya DG nodes using the
    OpenMaya 2.0 API. Supports attribute access via dot notation, iteration,
    and common node operations.

    Attributes:
        MFN_TYPE: The Maya function set type for this node class.

    Example:
        >>> node = DGNode()
        >>> node.create("myNode", "network")
        >>> node.addAttribute("customAttr", type=attributetypes.kMFnNumericDouble)
        >>> node.customAttr = 5.0
    """

    MFN_TYPE: Type[OpenMaya.MFnBase] = OpenMaya.MFnDependencyNode

    def __init__(self, mobj: OpenMaya.MObject | None = None):
        """Initialize the DGNode wrapper.

        Args:
            mobj: Optional Maya object to wrap. If provided, the node will be
                initialized with this object.
        """

        super().__init__()

        self._mfn: Type[OpenMaya.MFnDependencyNode] | None = None
        self._handle: OpenMaya.MObjectHandle | None = None

        if mobj is not None:
            self.setObject(mobj)

    def __hash__(self) -> int:
        """Return the hash value of the node.

        Returns:
            Hash code from the internal MObjectHandle, or default hash if not set.
        """

        return (
            self._handle.hashCode()
            if self._handle is not None
            else super().__hash__()
        )

    def __repr__(self) -> str:
        """Return the string representation of the node.

        Returns:
            String in format "<ClassName> full_path_name".
        """

        return f"<{self.__class__.__name__}> {self.fullPathName()}"

    def __str__(self) -> str:
        """Return the full path name of the node.

        Returns:
            Full DAG path or node name.
        """

        return self.fullPathName()

    def __bool__(self) -> bool:
        """Check whether the node is valid in the Maya scene.

        Returns:
            True if the node exists and is valid; False otherwise.
        """

        return self.exists()

    def __getitem__(self, item: str) -> Plug:
        """Get a plug by attribute name using bracket notation.

        Args:
            item: Name of the attribute to retrieve.

        Returns:
            Plug instance for the requested attribute.

        Raises:
            KeyError: If no attribute with the given name exists.
        """

        fn = self._mfn
        try:
            return Plug(self, fn.findPlug(item, False))
        except RuntimeError:
            raise KeyError(
                f"{self.name()} has no attribute by the name {item}"
            )

    def __setitem__(self, key: str, value: Any):
        """Set an attribute value using bracket notation.

        Args:
            key: Name of the attribute to set.
            value: Value to set. If a Plug instance, creates a connection.

        Raises:
            RuntimeError: If no attribute with the given name exists.
        """

        if key.startswith("_"):
            setattr(self, key, value)
            return
        if self.hasAttribute(key) is not None:
            if isinstance(value, Plug):
                self.connect(key, value)
                return
            self.setAttribute(key, value)
            return
        else:
            raise RuntimeError(
                f"Node {self.name()} has no attribute called: {key}"
            )

    def __getattr__(self, name: str) -> Any:
        """Get an attribute value using dot notation.

        Attempts to retrieve a node attribute by name. If found, returns the
        Plug instance; otherwise, falls back to normal attribute lookup.

        Args:
            name: Name of the attribute to access.

        Returns:
            Plug instance if attribute exists on node, otherwise the Python attribute.
        """

        attr = self.attribute(name)
        if attr is not None:
            return attr

        return super().__getattribute__(name)

    def __setattr__(self, key: str, value: Any):
        """Set an attribute value using dot notation.

        If the key matches a node attribute, sets its value. If value is a Plug,
        creates a connection instead.

        Args:
            key: Name of the attribute to set.
            value: Value to set, or Plug to connect.
        """

        if key.startswith("_"):
            super().__setattr__(key, value)
            return
        if self.hasAttribute(key):
            if isinstance(value, Plug):
                self.connect(key, value)
                return
            self.setAttribute(key, value)
            return

        super().__setattr__(key, value)

    def __eq__(self, other: DGNode) -> bool:
        """Check equality with another node.

        Args:
            other: Node to compare against.

        Returns:
            True if both nodes reference the same Maya object; False otherwise.
        """

        if not isinstance(other, DGNode) or (
            isinstance(other, DGNode) and other.handle() is None
        ):
            return False

        return self._handle == other.handle()

    def __ne__(self, other: DGNode) -> bool:
        """Check inequality with another node.

        Args:
            other: Node to compare against.

        Returns:
            True if nodes reference different Maya objects; False otherwise.
        """

        if not isinstance(other, DGNode):
            return True

        return self._handle != other.handle()

    def __contains__(self, key: str) -> bool:
        """Check if an attribute exists on this node.

        Args:
            key: Name of the attribute to check.

        Returns:
            True if the attribute exists; False otherwise.
        """

        return self.hasAttribute(key)

    def __delitem__(self, key: str):
        """Delete an attribute from the node.

        Args:
            key: Name of the attribute to delete.
        """

        self.deleteAttribute(key)

    @property
    def typeName(self) -> str:
        """Get the Maya node type name.

        Returns:
            The Maya type name (e.g., "transform", "mesh").
        """

        return self._mfn.typeName

    @property
    def isLocked(self) -> bool:
        """Check if the node is locked.

        Returns:
            True if the node is locked; False otherwise.
        """

        return self.mfn().isLocked

    def create(
        self,
        name: str,
        node_type: str,
        namespace: str | None = None,
        mod: OpenMaya.MDGModifier | None = None,
    ) -> DGNode:
        """Function that builds the node within the Maya scene.

        :param name: name of the new node.
        :param node_type: Maya node type to create.
        :param namespace: optional node namespace.
        :param mod: optional Maya modifier to add to.
        :return: newly created meta node instance.
        """

        name = namespace + name.split(":")[-1] if namespace else name
        self.setObject(
            factory.create_dg_node(name, node_type=node_type, mod=mod)
        )
        return self

    def exists(self) -> bool:
        """Returns whether the node is currently valid within the Maya scene.

        :return: True if the node is valid; False otherwise.
        """

        handle = self._handle
        return (
            False if handle is None else handle.isValid() and handle.isAlive()
        )

    def handle(self) -> OpenMaya.MObjectHandle:
        """Returns the MObjectHandle of the node.

        :return: MObjectHandle of the node.
        .warning:: Developer is responsible for checking if the node exists before calling this method.
        """

        return self._handle

    def mfn(self) -> OpenMaya.MFnDagNode | OpenMaya.MFnDependencyNode:
        """Returns the function set for this node.

        :return: function set for this node.
        """

        if self._mfn is None and self._handle is not None:
            self._mfn = self.MFN_TYPE(self.object())

        return self._mfn

    def typeId(self) -> OpenMaya.MTypeId | None:
        """Returns the Maya type id of the node.

        :return: type id of the node.
        """

        return self._mfn.typeId if self.exists() else None

    def hasFn(self, fn_Type: OpenMaya.MFn) -> bool:
        """Returns whether the node has the given function set.

        :param fn_Type: function set to check.
        :return: True if the node has the given function set; False otherwise.
        """

        return self.object().hasFn(fn_Type)

    def apiType(self) -> OpenMaya.MFn:
        """Returns the API type of the node.

        :return: API type of the node.
        """

        mobj = self.object()
        return mobj.apiType() if mobj is not None else None

    def object(self) -> OpenMaya.MObject | None:
        """Returns the Maya object of the node.

        :return: Maya object.
        """

        return self._handle.object() if self.exists() else None

    def setObject(self, mobj: OpenMaya.MObject | OpenMaya.MDagPath):
        """Sets the Maya object of the node.

        :param mobj: Maya object to set.
        """

        object_path = mobj
        if isinstance(mobj, OpenMaya.MDagPath):
            mobj = mobj.node()
        if not mobj.hasFn(OpenMaya.MFn.kDependencyNode):
            raise ValueError(f"Invalid MObject type {mobj.apiTypeStr}")
        self._handle = OpenMaya.MObjectHandle(mobj)
        self._mfn = self.MFN_TYPE(object_path)

    def name(self, include_namespace: bool = True) -> str:
        """Returns the node name.

        :param include_namespace: whether to include the namespace.
        :return: node name.
        :raises RuntimeError: if the node wrapped within this instance does not exist.
        """

        if not self.exists():
            return ""

        node_name = self.mfn().name()
        return (
            node_name
            if include_namespace
            else OpenMaya.MNamespace.stripNamespaceFromName(node_name)
        )

    def fullPathName(
        self, partial_name: bool = False, include_namespace: bool = True
    ) -> str:
        """Returns the node scene name, this result is dependent on the arguments.

        :param partial_name: whether to return the partial name of the node.
        :param include_namespace: whether to include the namespace.
        :return: node full path name.
        :raises RuntimeError: if the node wrapped within this instance does not exist.
        """

        if not self.exists():
            raise RuntimeError("Current node does not exists!")

        return nodes.name(self.object(), partial_name, include_namespace)

    def isReferenced(self) -> bool:
        """Check if the node is from a referenced file.

        Returns:
            True if the node is referenced; False otherwise.
        """

        return self.mfn().isFromReferencedFile

    def isDefaultNode(self) -> bool:
        """Check if this is a Maya default node.

        Returns:
            True if this is a default Maya node; False otherwise.
        """

        return self.mfn().isDefaultNode

    @lock_node_context
    def rename(
        self,
        new_name: str,
        maintain_namespace: bool = False,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> bool:
        """Rename this node.

        Args:
            new_name: The new name for the node.
            maintain_namespace: Whether to preserve the current namespace.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the rename immediately.

        Returns:
            True if rename was successful; False otherwise.
        """

        if maintain_namespace:
            current_namespace = self.namespace()
            if current_namespace != OpenMaya.MNamespace.rootNamespace():
                new_name = ":".join([current_namespace, new_name])
        try:
            nodes.rename(self.object(), new_name, mod=mod, apply=apply)
        except RuntimeError:
            logger.error(
                f"Failed to rename node: {self.name()}-{new_name}",
                exc_info=True,
            )
            return False

        return True

    def namespace(self) -> str:
        """Get the current namespace for this node.

        Returns:
            The namespace path, including root prefix.
        """

        name = OpenMaya.MNamespace.getNamespaceFromName(
            self.fullPathName()
        ).split("|")[-1]
        root = OpenMaya.MNamespace.rootNamespace()
        if not name.startswith(root):
            name = root + name

        return name

    def parentNamespace(self) -> str:
        """Get the parent namespace of this node.

        Returns:
            The parent namespace path.
        """

        namespace = self.namespace()
        if namespace == ":":
            return namespace

        OpenMaya.MNamespace.setCurrentNamespace(namespace)
        parent = OpenMaya.MNamespace.parentNamespace()
        OpenMaya.MNamespace.setCurrentNamespace(namespace)

        return parent

    def renameNamespace(self, namespace: str):
        """Rename the node's namespace.

        Args:
            namespace: The new namespace name.
        """

        current_namespace = self.namespace()
        if not current_namespace:
            return

        if current_namespace == namespace:
            return

        parent_namespace = self.parentNamespace()
        if current_namespace == ":":
            OpenMaya.MNamespace.addNamespace(namespace)
            self.rename(":".join([namespace, self.name()]))
            return

        OpenMaya.MNamespace.setCurrentNamespace(parent_namespace)
        OpenMaya.MNamespace.renameNamespace(current_namespace, namespace)
        OpenMaya.MNamespace.setCurrentNamespace(namespace)

    def removeNamespace(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Remove the namespace from this node.

        Args:
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            True if namespace was removed; False otherwise.
        """

        namespace = self.namespace()
        if namespace:
            return self.rename(
                self.name(include_namespace=False),
                maintain_namespace=False,
                mod=mod,
                apply=apply,
            )

        return False

    def lock(
        self,
        state: bool,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> OpenMaya.MDGModifier:
        """Set the lock state for this node.

        Args:
            state: True to lock; False to unlock.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            The modifier used for the operation.
        """

        if self.isLocked != state and self.object():
            modifier = mod or OpenMaya.MDGModifier()
            try:
                modifier.setNodeLockState(self.object(), state)
            except TypeError:
                raise
            if apply:
                modifier.doIt()

        return mod

    def hasAttribute(self, attribute_name: str) -> bool:
        """Check if an attribute exists on this node.

        Args:
            attribute_name: Name of the attribute to check.

        Returns:
            True if the attribute exists; False otherwise.
        """

        # Arrays don't get picked up by hasAttribute.
        if "[" in attribute_name:
            sel = OpenMaya.MSelectionList()
            try:
                sel.add(attribute_name)
                return True
            except RuntimeError:
                return False
        return self.mfn().hasAttribute(attribute_name)

    def attribute(self, name: str) -> Plug | None:
        """Get an attribute plug by name.

        Args:
            name: Name of the attribute (supports compound paths and array indices).

        Returns:
            Plug instance if found; None otherwise.
        """

        fn = self._mfn
        if any(i in name for i in ("[", ".")):
            sel = OpenMaya.MSelectionList()
            try:
                sel.add(".".join((self.fullPathName(), name)))
                mplug = sel.getPlug(0)
            except RuntimeError:
                # Raised when the plug does not exist.
                return None
            return Plug(self, mplug)
        elif fn.hasAttribute(name):
            return Plug(self, fn.findPlug(name, False))

        return None

    def setAttribute(
        self,
        name: str,
        value: Any,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> bool:
        """Set the value of an attribute.

        Args:
            name: Name of the attribute to set.
            value: Value to set.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            True if successful; False if attribute doesn't exist.
        """

        attr = self.attribute(name)
        if attr is not None:
            attr.set(value, mod=mod, apply=apply)
            return True

        return False

    # noinspection PyShadowingBuiltins
    @lock_node_context
    def addAttribute(
        self,
        name: str,
        type: int = attributetypes.kMFnNumericDouble,
        mod: OpenMaya.MDGModifier | None = None,
        **kwargs,
    ) -> Plug:
        """Add a new attribute to this node.

        Args:
            name: Name of the attribute to add.
            type: Attribute type constant from attributetypes module.
            mod: Optional modifier for batching operations.
            **kwargs: Additional attribute properties (default, min, max, etc.).
                If "children" is provided, creates a compound attribute.

        Returns:
            The newly created Plug instance.
        """

        if self.hasAttribute(name):
            return self.attribute(name)

        children = kwargs.get("children")
        if children:
            plug = self.addCompoundAttribute(
                name, attr_map=children, mod=mod, **kwargs
            )
        else:
            mobj = self.object()
            attr = nodes.add_attribute(
                mobj, name, name, type=type, mod=mod, **kwargs
            )
            plug = Plug(self, OpenMaya.MPlug(mobj, attr.object()))

        return plug

    @lock_node_context
    def addCompoundAttribute(
        self,
        name: str,
        attr_map: list[dict],
        isArray: bool = False,
        mod: OpenMaya.MDGModifier | None = None,
        **kwargs,
    ) -> Plug:
        """Add a compound attribute with child attributes.

        Args:
            name: Name of the compound attribute.
            attr_map: List of child attribute definitions. Each dict should contain
                "name", "type", and optionally "isArray".
            isArray: Whether the compound attribute is an array.
            mod: Optional modifier for batching operations.
            **kwargs: Additional compound attribute properties.

        Returns:
            The newly created compound Plug instance.
        """

        mobj = self.object()
        compound = nodes.add_compound_attribute(
            mobj, name, name, attr_map, isArray=isArray, mod=mod, **kwargs
        )
        return Plug(self, OpenMaya.MPlug(mobj, compound.object()))

    @lock_node_context
    def addProxyAttribute(self, source_plug: Plug, name: str) -> Plug | None:
        """Create a proxy attribute connected to a source plug.

        The proxy attribute mirrors the source plug's value while remaining
        independently modifiable.

        Args:
            source_plug: The plug to proxy.
            name: Name for the new proxy attribute.

        Returns:
            The proxy Plug instance, or None if attribute already exists.
        """

        if self.hasAttribute(name):
            return None

        plug_data = plugs.serialize_plug(source_plug.plug())
        plug_data["long_name"] = name
        plug_data["short_name"] = name
        plug_data["type"] = plug_data["type"]
        current_obj = self.object()
        return Plug(
            self,
            OpenMaya.MPlug(
                current_obj,
                nodes.add_proxy_attribute(
                    current_obj, source_plug.plug(), **plug_data
                ).object(),
            ),
        )

    @lock_node_context
    def createAttributesFromDict(
        self, data: dict, mod: OpenMaya.MDGModifier | None = None
    ) -> list[Plug]:
        """Create attributes from a serialized dictionary.

        Args:
            data: Dictionary mapping attribute names to their properties.
                Each value should contain keys like "type", "default", "min", "max",
                "keyable", "locked", etc. Use "children" for compound attributes.
            mod: Optional modifier for batching operations.

        Returns:
            List of created Plug instances.

        Example:
            >>> data = {
            ...     "myFloat": {"type": 2, "default": 3.0, "keyable": True},
            ...     "myCompound": {"children": [{"name": "x", "type": 2}]}
            ... }
            >>> plugs = node.createAttributesFromDict(data)
        """

        created_plugs: list[Plug] = []
        mfn = self.mfn()
        mobj = self.object()
        for name, attr_data in iter(data.items()):
            children = attr_data.get("children")
            if children:
                compound = nodes.add_compound_attribute(
                    mobj, name, name, children, mod=mod, **attr_data
                )
                created_plugs.append(
                    Plug(self, OpenMaya.MPlug(mobj, compound.object()))
                )
            else:
                if self.hasAttribute(name):
                    created_plugs.append(Plug(self, mfn.findPlug(name, False)))
                    continue
                attr = nodes.add_attribute(
                    mobj,
                    name,
                    name,
                    attr_data.pop("type", None),
                    mod=mod,
                    **attr_data,
                )
                created_plugs.append(
                    Plug(self, OpenMaya.MPlug(mobj, attr.object()))
                )

        return created_plugs

    def renameAttribute(self, name: str, new_name: str) -> bool:
        """Rename an attribute on this node.

        Args:
            name: Current name of the attribute.
            new_name: New name for the attribute.

        Returns:
            True if rename was successful; False otherwise.

        Raises:
            AttributeError: If the attribute doesn't exist.
        """

        try:
            plug = self.attribute(name)
        except RuntimeError:
            raise AttributeError(f"No attribute named: {name}")

        return plug.rename(new_name)

    def deleteAttribute(
        self, attribute_name: str, mod: OpenMaya.MDGModifier | None = None
    ) -> bool:
        """Delete an attribute from this node.

        Args:
            attribute_name: Name of the attribute to delete.
            mod: Optional modifier for batching operations.

        Returns:
            True if attribute was deleted; False if it doesn't exist.
        """

        attr = self.attribute(attribute_name)
        if attr is None:
            return False

        attr.delete(mod=mod)

        return True

    def connect(
        self,
        attribute_name: str,
        destination_plug: Plug,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> OpenMaya.MDGModifier | None:
        """Connect an attribute to a destination plug.

        Args:
            attribute_name: Name of the source attribute on this node.
            destination_plug: The plug to connect to.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the connection immediately.

        Returns:
            The modifier used, or None if attribute doesn't exist.
        """

        source = self.attribute(attribute_name)
        if source is not None:
            return source.connect(destination_plug, mod=mod, apply=apply)

        return None

    def iterateConnections(
        self, source: bool = True, destination: bool = True
    ) -> Iterator[tuple[Plug, Plug]]:
        """Iterate over node connections.

        Args:
            source: Whether to include source (input) connections.
            destination: Whether to include destination (output) connections.

        Yields:
            Tuples of (local_plug, connected_plug).
        """

        for source_plug, destination_plug in nodes.iterate_connections(
            self.object(), source, destination
        ):
            yield (
                Plug(self, source_plug),
                Plug(
                    node_by_object(destination_plug.node()), destination_plug
                ),
            )

    def sources(self) -> Iterator[tuple[Plug, Plug]]:
        """Iterate over source (input) connections.

        Yields:
            Tuples of (local_plug, source_plug).
        """

        for source, destination in nodes.iterate_connections(
            self.object(), source=True, destination=False
        ):
            yield Plug(self, source), Plug(self, destination)

    def destinations(self) -> Iterator[tuple[Plug, Plug]]:
        """Iterate over destination (output) connections.

        Yields:
            Tuples of (local_plug, destination_plug).
        """

        for source, destination in nodes.iterate_connections(
            self.object(), source=False, destination=True
        ):
            yield Plug(self, source), Plug(self, destination)

    @staticmethod
    def sourceNode(plug: Plug) -> DGNode | DagNode | None:
        """Get the source node connected to a plug.

        Args:
            plug: The plug to check.

        Returns:
            The source node, or None if not connected.
        """

        source = plug.source()
        return source.node() if source is not None else None

    def sourceNodeByName(
        self, plug_name: str
    ) -> (
        DGNode
        | DagNode
        | NurbsCurve
        | Mesh
        | Camera
        | IkHandle
        | Joint
        | ContainerAsset
        | AnimCurve
        | SkinCluster
        | AnimLayer
        | ObjectSet
        | BlendShape
        | DisplayLayer
        | None
    ):
        """Get the source node connected to an attribute by name.

        Args:
            plug_name: Name of the attribute to check.

        Returns:
            The source node, or None if not connected.
        """

        plug = self.attribute(plug_name)
        return self.sourceNode(plug) if plug is not None else None

    def setLockStateOnAttributes(
        self, attributes: Iterable[str], state: bool = True
    ) -> bool:
        """Lock or unlock multiple attributes.

        Args:
            attributes: Names of attributes to modify.
            state: True to lock; False to unlock.

        Returns:
            True if successful.
        """

        return nodes.set_lock_state_on_attributes(
            self.object(), attributes, state=state
        )

    def showHideAttributes(
        self, attributes: Iterable[str], state: bool = False
    ) -> bool:
        """Show or hide attributes in the channel box.

        Args:
            attributes: Names of attributes to modify.
            state: True to show and make keyable; False to hide.

        Returns:
            True if successful.
        """

        fn = self._mfn
        for attr in attributes:
            plug = fn.findPlug(attr, False)
            plug.isChannelBox = state
            plug.isKeyable = state

        return True

    def findAttributes(self, *names: str) -> list[Plug | None]:
        """Find multiple attributes by name.

        Args:
            *names: Attribute names to search for.

        Returns:
            List of Plug instances or None for each name, in order.
        """

        results = [None] * len(names)
        for attr in nodes.iterate_attributes(self.object()):
            plug_found = Plug(self, attr)
            short_name = plug_found.name().partition(".")[-1]
            try:
                # noinspection PyTypeChecker
                results[names.index(short_name)] = plug_found
            except ValueError:
                continue

        return results

    def iterateAttributes(self) -> Iterator[Plug]:
        """Iterate over all attributes on this node.

        Yields:
            Plug instances for each attribute.
        """

        for attr in nodes.iterate_attributes(self.object()):
            yield Plug(self, attr)

    def iterateExtraAttributes(
        self,
        skip: Iterable[str] | None = None,
        filtered_types: Iterable[str] | None = None,
        include_attributes: Iterable[str] | None = None,
    ) -> Iterator[Plug]:
        """Iterate over dynamic (user-defined) attributes.

        Args:
            skip: Attribute names to exclude.
            filtered_types: Attribute types to include (e.g., "double", "string").
            include_attributes: Attribute names to always include.

        Yields:
            Plug instances for each extra attribute.
        """

        for attr in nodes.iterate_extra_attributes(
            self.object(),
            skip=skip,
            filtered_types=filtered_types,
            include_attributes=include_attributes,
        ):
            yield Plug(self, attr)

    def iterateProxyAttributes(self) -> Iterator[Plug]:
        """Iterate over proxy attributes on this node.

        Yields:
            Plug instances for each proxy attribute.
        """

        for attr in self.iterateAttributes():
            if not attr.isProxy():
                continue
            yield attr

    def serializeFromScene(
        self,
        skip_attributes: Iterable[str] | None = None,
        include_connections: bool = True,
        extra_attributes_only: bool = False,
        use_short_names: bool = False,
        include_namespace: bool = True,
    ) -> dict:
        """Serialize this node to a JSON-compatible dictionary.

        Args:
            skip_attributes: Attribute names to exclude from serialization.
            include_connections: Whether to include incoming connections.
            extra_attributes_only: Whether to serialize only dynamic attributes.
            use_short_names: Whether to use short attribute names.
            include_namespace: Whether to include namespace in node name.

        Returns:
            Dictionary containing the serialized node data.
        """

        try:
            return nodes.serialize_node(
                self.object(),
                skip_attributes=skip_attributes,
                include_connections=include_connections,
                extra_attributes_only=extra_attributes_only,
                use_short_names=use_short_names,
                include_namespace=include_namespace,
            )
        except RuntimeError:
            return {}

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete this node from the scene.

        Args:
            mod: Optional modifier for batching operations.
            apply: Whether to apply the deletion immediately.

        Returns:
            True if node was deleted; False if it doesn't exist.

        Raises:
            RuntimeError: If deletion fails.
        """

        if not self.exists():
            return False

        if self.isLocked:
            self.lock(False)
        try:
            if mod:
                mod.commandToExecute(f"delete {self.fullPathName()}")
                if apply:
                    mod.doIt()
            else:
                cmds.delete(self.fullPathName())
            self._mfn = None
            return True
        except RuntimeError:
            logger.error(
                f"Failed node deletion, {self.mfn().name()}", exc_info=True
            )
            raise


# noinspection PyPep8Naming
class DagNode(DGNode):
    """Wrapper class for Maya DAG nodes.

    Extends DGNode with DAG-specific functionality including transforms,
    hierarchy traversal, and visibility control.

    Attributes:
        MFN_TYPE: The Maya function set type (MFnDagNode).
    """

    MFN_TYPE: Type[OpenMaya.MFnBase] = OpenMaya.MFnDagNode

    def create(
        self,
        name: str,
        node_type: str,
        parent: OpenMaya.MObject | None = None,
        namespace: str | None = None,
        mod: OpenMaya.MDGModifier | None = None,
    ) -> DagNode:
        """Create a new DAG node and wrap it in this instance.

        Args:
            name: Name for the new node.
            node_type: Maya node type to create (e.g., "transform", "locator").
            parent: Optional parent node to attach to.
            namespace: Optional namespace to add to the node name.
            mod: Optional modifier for batching operations.

        Returns:
            This instance, now wrapping the newly created node.
        """

        if isinstance(parent, DagNode):
            parent = parent.object()
        new_node = factory.create_dag_node(
            name, node_type=node_type, parent=parent, mod=mod
        )
        self.setObject(new_node)

        return self

    def serializeFromScene(
        self,
        skip_attributes: Iterable[str] | None = None,
        include_connections: bool = True,
        include_attributes: Iterable[str] | None = None,
        extra_attributes_only: bool = True,
        use_short_names: bool = False,
        include_namespace: bool = True,
    ) -> dict:
        """Serialize this DAG node to a JSON-compatible dictionary.

        Includes transform data (translation, rotation, scale, matrices) in
        addition to base node serialization.

        Args:
            skip_attributes: Attribute names to exclude.
            include_connections: Whether to include incoming connections.
            include_attributes: Specific attributes to include.
            extra_attributes_only: Whether to serialize only dynamic attributes.
            use_short_names: Whether to use short attribute names.
            include_namespace: Whether to include namespace in node name.

        Returns:
            Dictionary containing serialized node data including transforms.
        """

        rotation_order = self.rotationOrder()
        world_matrix = self.worldMatrix()
        translation, rotation, scale = nodes.decompose_transform_matrix(
            world_matrix, constants.kRotateOrders.get(rotation_order, -1)
        )

        try:
            data = nodes.serialize_node(
                self.object(),
                skip_attributes=skip_attributes,
                include_connections=include_connections,
                include_attributes=include_attributes,
                extra_attributes_only=extra_attributes_only,
                use_short_names=use_short_names,
                include_namespace=include_namespace,
            )
            # noinspection PyTypeChecker
            data.update(
                {
                    "translate": tuple(translation),
                    "rotate": tuple(rotation),
                    "scale": tuple(scale),
                    "rotateOrder": rotation_order,
                    "matrix": list(self.matrix()),
                    "worldMatrix": list(world_matrix),
                }
            )
            return data
        except RuntimeError as err:
            logger.exception(
                f"Something went wrong while deserializing node: {err}",
                exc_info=True,
            )
            return {}

    def parent(self) -> DagNode | None:
        """Get the parent node.

        Returns:
            The parent DagNode, or None if at the world level.
        """

        mobj = self.object()
        if mobj is None:
            return None
        parent = dagutils.parent(mobj)
        if parent:
            return node_by_object(parent)

        return parent

    # noinspection PyPep8Naming
    @lock_node_context
    def setParent(
        self,
        parent: DagNode | None,
        maintain_offset: bool = True,
        mod: OpenMaya.MDagModifier | None = None,
        apply: bool = True,
    ) -> OpenMaya.MDagModifier:
        """Set the parent of this node.

        Args:
            parent: New parent node, or None for world parenting.
            maintain_offset: Whether to preserve world-space position.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            The modifier used for the operation.
        """

        parent_lock = False
        set_locked = False
        new_parent = None
        if parent is not None:
            new_parent = parent.object()
            parent_lock = parent.isLocked
            if parent_lock:
                set_locked = True
                parent.lock(False)
        try:
            result = dagutils.set_parent(
                self.object(),
                new_parent,
                maintain_offset=maintain_offset,
                mod=mod,
                apply=apply,
            )
        finally:
            if set_locked:
                parent.lock(parent_lock)

        return result

    def dagPath(self) -> OpenMaya.MDagPath:
        """Get the MDagPath for this node.

        Returns:
            The DAG path to this node.
        """

        return self.mfn().getPath()

    def depth(self) -> int:
        """Get the hierarchy depth of this node.

        Returns:
            The number of parents above this node (0 = world level).
        """

        return self.fullPathName().count("|") - 1

    def root(self) -> DagNode:
        """Get the root node of this hierarchy.

        Returns:
            The topmost parent DagNode.
        """

        return node_by_object(dagutils.root(self.object()))

    def boundingBox(self) -> OpenMaya.MBoundingBox:
        """Get the bounding box for this node.

        Returns:
            The node's bounding box in local space.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnDagNode = self._mfn
        return mfn.boundingBox

    def iterateShapes(self) -> Iterator[DagNode]:
        """Iterate over shape nodes under this transform.

        Yields:
            DagNode instances for each shape.
        """

        path = self.dagPath()
        for i in range(path.numberOfShapesDirectlyBelow()):
            dag_path = OpenMaya.MDagPath(path)
            dag_path.extendToShape(i)
            yield node_by_object(dag_path.node())

    def shapes(self) -> list[DagNode]:
        """Get all shape nodes under this transform.

        Returns:
            List of DagNode instances for shapes.
        """

        return list(self.iterateShapes())

    def setShapeColor(
        self,
        color: Iterable[float, float, float],
        shape_index: int | None = None,
    ):
        """Set the display color for this node or its shapes.

        Args:
            color: RGB color values (0.0-1.0).
            shape_index: Shape index to color. None for transform, -1 for all shapes.
        """

        if shape_index is not None:
            if shape_index == -1:
                for shape in iter(nodes.shapes(self.dagPath())):
                    nodes.set_node_color(shape.node(), color)
            else:
                shape = nodes.shape_at_index(self.dagPath(), shape_index)
                nodes.set_node_color(shape.node(), color)
            return

        # noinspection PyTypeChecker
        if len(color) == 3:
            nodes.set_node_color(self.object(), color)

    def deleteShapeNodes(self):
        """Delete all shape nodes under this transform."""

        for shape in self.shapes():
            shape.delete()

    def child(self, index: int, node_types: tuple[int, ...] = ()) -> DagNode:
        """Get a child node by index.

        Args:
            index: Index of the child (0-based).
            node_types: Optional MFn type constants to filter by.

        Returns:
            The child DagNode at the given index.
        """

        path = self.dagPath()
        current_index = 0
        for i in range(path.childCount()):
            child = path.child(i)
            if (
                not node_types or child.apiType() in node_types
            ) and current_index == index:
                return node_by_object(child)
            current_index += 1

        return None

    def addChild(self, node: DagNode):
        """Re-parent a node under this transform.

        Args:
            node: The node to make a child of this transform.
        """

        node.setParent(self)

    def iterateParents(self) -> Iterator[DagNode]:
        """Iterate up the hierarchy to the root.

        Yields:
            Each parent DagNode from immediate parent to root.
        """

        for parent in dagutils.iterate_parents(self.object()):
            yield node_by_object(parent)

    def iterateChildren(
        self,
        node: DagNode | None = None,
        recursive: bool = True,
        node_types: Iterable[int] | None = None,
    ) -> Iterator[DagNode]:
        """Iterate over child nodes.

        Args:
            node: Starting node (defaults to self).
            recursive: Whether to recursively iterate all descendants.
            node_types: Optional MFn type constants to filter by.

        Yields:
            Child DagNode instances.
        """

        node_types = node_types or ()
        self_object = node.object() if node is not None else self.object()
        path = OpenMaya.MDagPath.getAPathTo(self_object).getPath()
        for i in range(path.childCount()):
            child = path.child(i)
            if not node_types or child.apiType() in node_types:
                yield node_by_object(child)
            if recursive:
                for _child in self.iterateChildren(
                    node_by_object(child),
                    recursive=recursive,
                    node_types=node_types,
                ):
                    yield _child

    def children(self, node_types: tuple[int, ...] = ()) -> list[DagNode]:
        """Get all immediate children.

        Args:
            node_types: Optional MFn type constants to filter by.

        Returns:
            List of child DagNode instances.
        """

        path = self.dagPath()
        children = list()
        for i in range(path.childCount()):
            child = path.child(i)
            if not node_types or child.apiType() in node_types:
                children.append(node_by_object(child))

        return children

    def iterateSiblings(
        self, node_types: set[int] = (OpenMaya.MFn.kTransform,)
    ) -> Iterator[DagNode]:
        """Iterate over sibling nodes (same parent).

        Args:
            node_types: MFn type constants to filter by.

        Yields:
            Sibling DagNode instances (excludes self).
        """

        parent = self.parent()
        if parent is None:
            return
        for child in parent.iterateChildren(
            recursive=False, node_types=node_types
        ):
            if child != self:
                yield child

    def translation(
        self,
        space: OpenMaya.MSpace | int | None = None,
        scene_units: bool = False,
    ) -> OpenMaya.MVector:
        """Get the translation of this node.

        Args:
            space: Coordinate space (defaults to world space).
            scene_units: Whether to convert to scene units.

        Returns:
            Translation as MVector.
        """

        space = space or OpenMaya.MSpace.kWorld
        return nodes.translation(self.object(), space, scene_units=scene_units)

    def setTranslation(
        self,
        translation: OpenMaya.MVector
        | tuple[float, float, float]
        | list[float],
        space: OpenMaya.MSpace | int | None = None,
        scene_units: bool = False,
    ):
        """Set the translation of this node.

        Args:
            translation: New position as vector or tuple.
            space: Coordinate space (defaults to transform/local space).
            scene_units: Whether translation is in scene units.
        """

        space = space or OpenMaya.MSpace.kTransform
        nodes.set_translation(
            self.object(),
            OpenMaya.MVector(translation),
            space=space,
            scene_units=scene_units,
        )

    def rotation(
        self, space: OpenMaya.MSpace | None = None, as_quaternion: bool = True
    ) -> OpenMaya.MQuaternion | OpenMaya.MEulerRotation:
        """Get the rotation of this node.

        Args:
            space: Coordinate space (defaults to transform/local space).
            as_quaternion: Whether to return as quaternion (True) or euler (False).

        Returns:
            Rotation as MQuaternion or MEulerRotation.
        """

        return nodes.rotation(
            self.dagPath(),
            space or OpenMaya.MSpace.kTransform,
            as_quaternion=as_quaternion,
        )

    def setRotation(
        self,
        rotation: OpenMaya.MQuaternion
        | OpenMaya.MEulerRotation
        | tuple[float, float, float, float]
        | list[float],
        space: OpenMaya.MSpace | int | None = None,
    ):
        """Set the rotation of this node.

        Args:
            rotation: Rotation as quaternion (4 values), euler (3 values), or Maya types.
            space: Coordinate space (defaults to world space).
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnDagNode = self._mfn
        space = space or OpenMaya.MSpace.kWorld
        transform = OpenMaya.MFnTransform(mfn.getPath())
        if isinstance(rotation, OpenMaya.MQuaternion):
            transform.setRotation(rotation, space)
            return
        elif isinstance(rotation, (tuple, list)):
            if space == OpenMaya.MSpace.kWorld and len(rotation) > 3:
                rotation = OpenMaya.MQuaternion(rotation)
            else:
                rotation = OpenMaya.MEulerRotation(rotation)
        if space != OpenMaya.MSpace.kTransform and isinstance(
            rotation, OpenMaya.MEulerRotation
        ):
            space = OpenMaya.MSpace.kTransform

        transform.setRotation(rotation, space)

    def scale(self, space: OpenMaya.MSpace | None = None) -> OpenMaya.MVector:
        """Get the scale of this node.

        Args:
            space: Coordinate space (defaults to transform/local space).

        Returns:
            Scale as MVector.
        """

        space = space or OpenMaya.MSpace.kTransform
        transform = self.transformationMatrix(space)
        return OpenMaya.MVector(transform.scale(space))

    def setScale(
        self, scale: OpenMaya.MVector | Iterable[float, float, float]
    ):
        """Set the scale of this node.

        Args:
            scale: Scale values as MVector or tuple/list.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnDagNode = self._mfn
        transform = OpenMaya.MFnTransform(mfn.getPath())
        transform.setScale(scale)

    def rotationOrder(self) -> int:
        """Get the rotation order for this node.

        Returns:
            Rotation order index (0=XYZ, 1=YZX, etc.).
        """

        return self.rotateOrder.value()

    def setRotationOrder(
        self,
        rotate_order: int = constants.kRotateOrder_XYZ,
        preserve: bool = True,
    ):
        """Set the rotation order for this node.

        Args:
            rotate_order: Rotation order constant (defaults to XYZ).
            preserve: Whether to adjust rotation values to maintain orientation.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnDagNode = self._mfn
        rotate_order = constants.kRotateOrders.get(rotate_order, -1)
        transform = OpenMaya.MFnTransform(mfn.getPath())
        transform.setRotationOrder(rotate_order, preserve)

    def worldMatrix(
        self, context: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
    ) -> OpenMaya.MMatrix:
        """Get the world matrix of this node.

        Args:
            context: Evaluation context (defaults to normal/current time).

        Returns:
            The world transformation matrix.
        """

        world_matrix = self._mfn.findPlug(
            "worldMatrix", False
        ).elementByLogicalIndex(0)
        return OpenMaya.MFnMatrixData(world_matrix.asMObject(context)).matrix()

    def setWorldMatrix(self, matrix: OpenMaya.MMatrix):
        """Set the world matrix of this node.

        Args:
            matrix: The world transformation matrix to set.
        """

        nodes.set_matrix(self.object(), matrix, space=OpenMaya.MSpace.kWorld)

    def matrix(
        self, context: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
    ) -> OpenMaya.MMatrix:
        """Get the local matrix of this node.

        Args:
            context: Evaluation context (defaults to normal/current time).

        Returns:
            The local transformation matrix.
        """

        local_matrix = self._mfn.findPlug("matrix", False)
        return OpenMaya.MFnMatrixData(local_matrix.asMObject(context)).matrix()

    def setMatrix(self, matrix: OpenMaya.MMatrix):
        """Set the local matrix of this node.

        Args:
            matrix: The local transformation matrix to set.
        """

        nodes.set_matrix(
            self.object(), matrix, space=OpenMaya.MSpace.kTransform
        )

    def transformationMatrix(
        self,
        rotate_order: int | None = None,
        space: OpenMaya.MSpace | None = OpenMaya.MSpace.kWorld,
    ) -> OpenMaya.MTransformationMatrix:
        """Get the transformation matrix with rotation order applied.

        Args:
            rotate_order: Rotation order (defaults to node's rotation order).
            space: Coordinate space (defaults to world space).

        Returns:
            MTransformationMatrix with proper rotation order.
        """

        transform = OpenMaya.MTransformationMatrix(
            self.worldMatrix()
            if space == OpenMaya.MSpace.kWorld
            else self.matrix()
        )
        rotate_order = (
            self.rotationOrder() if rotate_order is None else rotate_order
        )
        rotate_order = constants.kRotateOrders.get(rotate_order, -1)
        transform.reorderRotation(rotate_order)

        return transform

    def parentInverseMatrix(
        self, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
    ) -> OpenMaya.MMatrix:
        """Get the parent inverse matrix of this node.

        Args:
            ctx: Evaluation context (defaults to normal/current time).

        Returns:
            The parent's inverse world matrix.
        """

        return nodes.parent_inverse_matrix(self.object(), ctx=ctx)

    def worldMatrixPlug(self, index: int = 0) -> Plug:
        """Get the world matrix plug.

        Args:
            index: Array index for instanced nodes (defaults to 0).

        Returns:
            Plug for the worldMatrix attribute.
        """

        return Plug(
            self,
            self._mfn.findPlug("worldMatrix", False).elementByLogicalIndex(
                index
            ),
        )

    def worldInverseMatrixPlug(self, index: int = 0) -> Plug:
        """Get the world inverse matrix plug.

        Args:
            index: Array index for instanced nodes (defaults to 0).

        Returns:
            Plug for the worldInverseMatrix attribute.
        """

        return Plug(
            self,
            self._mfn.findPlug(
                "worldInverseMatrix", False
            ).elementByLogicalIndex(index),
        )

    def offsetMatrix(
        self,
        target_node: DagNode,
        space: OpenMaya.MSpace = OpenMaya.MSpace.kWorld,
        ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal,
    ) -> OpenMaya.MMatrix:
        """Get the offset matrix between this node and a target.

        Args:
            target_node: The target transform node.
            space: Coordinate space for the calculation.
            ctx: Evaluation context.

        Returns:
            Matrix representing the offset from this node to target.
        """

        return nodes.offset_matrix(
            self.object(), target_node.object(), space=space, ctx=ctx
        )

    def decompose(
        self, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
    ) -> tuple[OpenMaya.MVector, OpenMaya.MVector, OpenMaya.MVector]:
        """Decompose the world matrix into translation, rotation, and scale.

        Args:
            ctx: Evaluation context.

        Returns:
            Tuple of (translation, rotation, scale) as MVector instances.
        """

        rotate_order = constants.kRotateOrders.get(self.rotationOrder(), -1)
        return nodes.decompose_transform_matrix(
            self.worldMatrix(ctx),
            rotate_order,
            space=OpenMaya.MSpace.kWorld,
        )

    def resetTransform(
        self, translate: bool = True, rotate: bool = True, scale: bool = True
    ):
        """Reset transform attributes to identity values.

        Args:
            translate: Whether to reset translation to (0, 0, 0).
            rotate: Whether to reset rotation to identity.
            scale: Whether to reset scale to (1, 1, 1).
        """

        translate_attr = self.attribute("translate")
        rotate_attr = self.attribute("rotate")
        scale_attr = self.attribute("scale")
        if (
            translate
            and not translate_attr.isDestination
            and translate_attr.numConnectedChildren() == 0
        ):
            self.setTranslation((0.0, 0.0, 0.0))
        if (
            rotate
            and not rotate_attr.isDestination
            and rotate_attr.numConnectedChildren() == 0
        ):
            self.setRotation(
                OpenMaya.MQuaternion(), space=OpenMaya.MSpace.kTransform
            )
        if (
            scale
            and not scale_attr.isDestination
            and scale_attr.numConnectedChildren() == 0
        ):
            self.setScale((1.0, 1.0, 1.0))

    def resetTransformToOffsetParent(self):
        """Reset transforms and move values to offset parent matrix.

        Transfers the current world transform to the offsetParentMatrix
        attribute and resets translate, rotate, and scale to identity.
        """

        parent = self.parent()
        world_matrix = self.worldMatrix()
        parent_inverse_matrix = (
            parent.worldMatrix().inverse()
            if parent is not None
            else OpenMaya.MMatrix()
        )
        self.attribute("offsetParentMatrix").set(
            world_matrix * parent_inverse_matrix
        )
        self.resetTransform()

    def isHidden(self) -> bool:
        """Check if this node is hidden.

        Returns:
            True if visibility is off; False if visible.
        """

        return not self._mfn.findPlug("visibility", False).asBool()

    def setVisible(
        self,
        flag: bool,
        mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
        apply: bool = True,
    ) -> bool:
        """Set the visibility of this node.

        Args:
            flag: True to show; False to hide.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            True if visibility was set; False if attribute is locked/connected.
        """

        visibility_plug = self.attribute("visibility")
        if (
            visibility_plug.isLocked
            or visibility_plug.isConnected
            and not visibility_plug.isProxy()
        ):
            return False

        visibility_plug.set(flag, mod, apply=apply)

        return True

    def show(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Show this node (set visibility to True).

        Args:
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            True if successful; False otherwise.
        """

        return self.setVisible(True, mod=mod, apply=apply)

    def hide(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Hide this node (set visibility to False).

        Args:
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            True if successful; False otherwise.
        """

        return self.setVisible(False, mod=mod, apply=apply)


# noinspection PyPep8Naming
class Plug:
    """Wrapper class for Maya MPlug objects.

    Provides a Pythonic interface for accessing and modifying node attributes,
    including connections, values, and metadata.

    Supports operator overloading for connections:
        - `plug1 >> plug2` connects plug1 to plug2
        - `plug1 << plug2` connects plug2 to plug1
        - `plug1 // plug2` disconnects plug1 from plug2

    Example:
        >>> node = node_by_name("pCube1")
        >>> tx = node.translateX
        >>> tx.set(10.0)
        >>> print(tx.value())
        10.0
    """

    def __init__(self, node: DGNode | DagNode, mplug: OpenMaya.MPlug):
        """Initialize the Plug wrapper.

        Args:
            node: The node this plug belongs to.
            mplug: The Maya MPlug object to wrap.
        """

        self._node = node
        self._mplug = mplug

    def __repr__(self) -> str:
        """Return the display string for this plug.

        Returns:
            String in format "<Plug> node.attribute" or empty if invalid.
        """

        return (
            f"<{self.__class__.__name__}> {self._mplug.name()}"
            if self.exists()
            else ""
        )

    def __str__(self) -> str:
        """Return the full path name of this plug.

        Returns:
            The plug path (e.g., "pCube1.translateX") or empty if invalid.
        """

        return "" if not self.exists() else self._mplug.name()

    def __eq__(self, other: Plug) -> bool:
        """Check equality with another plug.

        Args:
            other: Plug to compare against.

        Returns:
            True if both wrap the same MPlug; False otherwise.
        """

        return self._mplug == other.plug()

    def __ne__(self, other: Plug) -> bool:
        """Check inequality with another plug.

        Args:
            other: Plug to compare against.

        Returns:
            True if plugs are different; False otherwise.
        """

        return self._mplug != other.plug()

    def __abs__(self) -> Any:
        """Return the absolute value of the plug's value.

        Returns:
            Absolute value of the current plug value.
        """

        return abs(self.value())

    def __int__(self) -> int:
        """Return the plug value as an integer.

        Returns:
            Integer value of the plug.
        """

        return self._mplug.asInt()

    def __float__(self) -> float:
        """Return the plug value as a float.

        Returns:
            Float value of the plug.
        """

        return self._mplug.asFloat()

    def __neg__(self) -> Any:
        """Return the negated value of the plug.

        Returns:
            Negative of the current plug value.
        """

        return -self.value()

    def __bool__(self) -> bool:
        """Check if the plug is valid.

        Returns:
            True if the plug exists; False otherwise.
        """

        return self.exists()

    def __getitem__(self, item: int) -> Plug | None:
        """Get a child or element plug by index.

        Args:
            item: Index of the child (compound) or element (array).

        Returns:
            The child or element Plug.

        Raises:
            TypeError: If the plug doesn't support indexing.
        """

        if self._mplug.isArray:
            return self.element(item)
        if self._mplug.isCompound:
            return self.child(item)

        raise TypeError(f"{self._mplug.name()} does not support indexing")

    def __getattr__(self, item: str) -> Any:
        """Access MPlug attributes transparently.

        Args:
            item: Name of the attribute to access.

        Returns:
            The MPlug attribute value, or falls back to normal lookup.
        """

        if hasattr(self._mplug, item):
            return getattr(self._mplug, item)

        return super().__getattribute__(item)

    def __setattr__(self, key: str, value: Any):
        """Set attributes, with special handling for Plug connections.

        Args:
            key: Attribute name.
            value: Value to set. If a Plug, creates a connection.
        """

        if key.startswith("_"):
            super().__setattr__(key, value)
            return
        elif hasattr(self._mplug, key):
            return setattr(self._mplug, key, value)
        elif isinstance(value, Plug):
            value.connect(self)

        super().__setattr__(key, value)

    def __iter__(self) -> Iterator[Plug]:
        """Iterate over compound children or array elements.

        Yields:
            Plug instances for each child or element.
        """

        mplug = self._mplug
        if mplug.isArray:
            indices = mplug.getExistingArrayAttributeIndices()
            # Case in Maya 2023 where num of indices is zero but 2022 is [0].
            # For consistency, 0 is usually a valid logical index to bind to.
            for i in indices or [0]:
                yield Plug(self._node, mplug.elementByLogicalIndex(i))
        elif mplug.isCompound:
            for i in range(mplug.numChildren()):
                yield Plug(self._node, mplug.child(i))

    def __len__(self) -> int:
        """Return the number of elements or children.

        Returns:
            Element count for arrays, child count for compounds, 0 otherwise.
        """

        if self._mplug.isArray:
            return self._mplug.evaluateNumElements()
        elif self._mplug.isCompound:
            return self._mplug.numChildren()

        return 0

    def __rshift__(self, other: Plug):
        """Connect this plug to a downstream plug using >> operator.

        Args:
            other: The destination plug to connect to.
        """

        self.connect(other)

    def __lshift__(self, other: Plug):
        """Connect an upstream plug to this plug using << operator.

        Args:
            other: The source plug to connect from.
        """

        other.connect(self)

    def __floordiv__(self, other: Plug):
        """Disconnect this plug from another using // operator.

        Args:
            other: The plug to disconnect from.
        """

        self.disconnect(other)

    def apiType(self) -> int:
        """Get the Maya API attribute type.

        Returns:
            Attribute type constant from attributetypes module.
        """

        return plugs.plug_type(self._mplug)

    def mfn(self) -> OpenMaya.MFnAttribute:
        """Get the Maya function set for this attribute.

        Returns:
            The appropriate MFnAttribute subclass instance.
        """

        attr = self._mplug.attribute()
        return plugs.plug_fn(attr)(attr)

    def mfnType(self) -> type:
        """Get the Maya function set class for this attribute.

        Returns:
            The MFnAttribute subclass type.
        """

        return plugs.plug_fn(self._mplug.attribute())

    def exists(self) -> bool:
        """Check if this plug is valid.

        Returns:
            True if the plug exists and is not null; False otherwise.
        """

        return self._mplug and not self._mplug.isNull

    def partialName(
        self,
        include_node_name: bool = False,
        include_non_mandatory_indices: bool = True,
        include_instanced_indices: bool = True,
        use_alias: bool = False,
        use_full_attribute_path: bool = True,
        use_long_names: bool = True,
    ) -> str:
        """Get the partial name of this plug.

        Args:
            include_node_name: Include the node name prefix.
            include_non_mandatory_indices: Include optional array indices.
            include_instanced_indices: Include instance indices.
            use_alias: Use attribute alias if available.
            use_full_attribute_path: Include full compound path.
            use_long_names: Use long attribute names.

        Returns:
            The formatted partial name string.
        """

        return self._mplug.partialName(
            include_node_name,
            include_non_mandatory_indices,
            include_instanced_indices,
            use_alias,
            use_full_attribute_path,
            use_long_names,
        )

    def plug(self) -> OpenMaya.MPlug:
        """Get the underlying Maya MPlug object.

        Returns:
            The wrapped MPlug instance.
        """

        return self._mplug

    def node(self) -> DGNode | DagNode:
        """Get the node this plug belongs to.

        Returns:
            The parent node instance.
        """

        return self._node

    def default(self) -> Any:
        """Get the default value of this plug.

        Returns:
            The default value, or None if plug doesn't exist.
        """

        if not self.exists():
            return None

        return plugs.plug_default(self._mplug)

    def setDefault(self, value: Any) -> bool:
        """Set the default value of this plug.

        Args:
            value: The new default value.

        Returns:
            True if successful; False otherwise.
        """

        return (
            plugs.set_plug_default(self._mplug, value)
            if self.exists()
            else False
        )

    def isProxy(self) -> bool:
        """Check if this is a proxy attribute.

        Returns:
            True if this is a proxy attribute; False otherwise.
        """

        return OpenMaya.MFnAttribute(self._mplug.attribute()).isProxyAttribute

    def setAsProxy(self, source_plug: Plug):
        """Set this attribute as a proxy connected to a source plug.

        Args:
            source_plug: The plug to proxy.
        """

        if self._mplug.isCompound:
            plugs.set_compound_as_proxy(self.plug(), source_plug.plug())
            return

        OpenMaya.MFnAttribute(self._mplug.attribute()).isProxyAttribute = True
        source_plug.connect(self)

    def isAnimated(self) -> bool:
        """Check if this plug is animated.

        Returns:
            True if connected to animation curves; False otherwise.

        Raises:
            ObjectDoesNotExistError: If the plug doesn't exist.
        """

        if not self.exists():
            raise ObjectDoesNotExistError("Current Plug does not exist")

        return OpenMayaAnim.MAnimUtil.isAnimated(self._mplug)

    def findAnimation(self) -> list[AnimCurve]:
        """Find animation curves connected to this plug.

        Returns:
            List of AnimCurve instances animating this plug.

        Raises:
            ObjectDoesNotExistError: If the plug doesn't exist.
        """

        if not self.exists():
            raise ObjectDoesNotExistError("Current Plug does not exist")

        return [
            node_by_object(i)
            for i in OpenMayaAnim.MAnimUtil.findAnimation(self._mplug)
        ]

    def isFreeToChange(self) -> bool:
        """Check if the plug value can be modified.

        Returns:
            True if the plug is free to change; False if locked or connected.
        """

        return self._mplug.isFreeToChange() == self._mplug.kFreeToChange

    def value(
        self, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
    ) -> Any:
        """Get the current value of this plug.

        Args:
            ctx: Evaluation context (defaults to current time).

        Returns:
            The plug value, with MObjects converted to node wrappers.
        """

        value = plugs.plug_value(self._mplug, ctx=ctx)
        value = Plug._convert_value_type(value)

        return value

    def enumFields(self) -> list[str]:
        """Get the field names for an enum attribute.

        Returns:
            List of enum field names.

        Raises:
            InvalidPlugPathError: If this is not an enum attribute.
        """

        plug_type = self.apiType()
        if plug_type != attributetypes.kMFnkEnumAttribute:
            raise InvalidPlugPathError(
                f"Required type 'Enum', current type: {attributetypes.internal_type_to_string(plug_type)} for {self}"
            )

        return plugs.enum_names(self.plug())

    @lock_node_plug_context
    def addEnumFields(self, fields: list[str]):
        """Add new field names to an enum attribute.

        Existing field names are skipped. New fields are appended to the end.

        Args:
            fields: List of field names to add.

        Raises:
            ReferenceObjectError: If plug is referenced and locked.
        """

        if self.node().isReferenced() and self.isLocked:
            raise ReferenceObjectError(
                f"Plug {self.name()} is a reference and locked"
            )

        existing_field_names = self.enumFields()
        attr = OpenMaya.MFnEnumAttribute(self.attribute())
        index: int = 0
        for field in fields:
            if field in existing_field_names:
                continue
            attr.addField(field, len(existing_field_names) + index)
            index += 1

    def setFields(self, fields: list[str]):
        """Set the complete list of fields for an enum attribute.

        Args:
            fields: List of field names to set.

        Raises:
            InvalidPlugPathError: If this is not an enum attribute.
        """

        default_value = self.default()
        try:
            cmds.addAttr(self.name(), edit=True, enumName=":".join(fields))
        except RuntimeError:
            raise InvalidPlugPathError(
                f"Required type 'Enum', current type: "
                f"{attributetypes.internal_type_to_string(self.apiType())} for {self}"
            )
        if default_value is not None and default_value < len(
            self.enumFields()
        ):
            self.setDefault(default_value)

    def array(self) -> Plug:
        """Get the array plug for this array element.

        Returns:
            The parent array Plug.

        Raises:
            AssertionError: If this plug is not an array element.
        """

        assert self._mplug.isElement, (
            f"Plug: {self.name()} is not an array element"
        )
        return Plug(self._node, self._mplug.array())

    def parent(self) -> Plug:
        """Get the parent plug for this compound child.

        Returns:
            The parent compound Plug.

        Raises:
            AssertionError: If this plug is not a child attribute.
        """

        assert self._mplug.isChild, (
            f"Plug {self.name()} is not a child attribute"
        )
        return Plug(self._node, self._mplug.parent())

    def children(self) -> list[Plug]:
        """Get all children of this compound plug.

        Returns:
            List of child Plug instances.
        """

        return [
            Plug(self._node, self._mplug.child(i))
            for i in range(self._mplug.numChildren())
        ]

    def child(self, index: int) -> Plug:
        """Get a child plug by index.

        Args:
            index: Child index (supports negative indexing).

        Returns:
            The child Plug at the given index.

        Raises:
            AssertionError: If this plug is not a compound.
        """

        assert self._mplug.isCompound, (
            f"Plug: {self._mplug.name()} is not a compound"
        )
        if index < 0:
            new_index = max(0, len(self) + index)
            return Plug(self._node, self._mplug.child(new_index))

        return Plug(self._node, self._mplug.child(index))

    def element(self, index: int) -> Plug:
        """Get an array element by logical index.

        Args:
            index: Logical index (supports negative indexing).

        Returns:
            The element Plug at the given index.

        Raises:
            AssertionError: If this plug is not an array.
        """

        assert self._mplug.isArray, (
            f"Plug: {self._mplug.name()} is not an array"
        )
        if index < 0:
            new_index = max(0, len(self) + index)
            return Plug(
                self._node, self._mplug.elementByLogicalIndex(new_index)
            )

        return Plug(self._node, self._mplug.elementByLogicalIndex(index))

    def elementByPhysicalIndex(self, index: int) -> Plug:
        """Get an array element by physical (sparse) index.

        Args:
            index: Physical index in the array.

        Returns:
            The element Plug at the given physical index.

        Raises:
            AssertionError: If this plug is not an array.
        """

        assert self._mplug.isArray, f"Plug {self.name()} is not an array"
        return Plug(self._node, self._mplug.elementByPhysicalIndex(index))

    def nextAvailableElementPlug(self) -> Plug:
        """Get the next available output element for this array.

        Availability is based on output connections of elements and children.

        Returns:
            The next available element Plug.

        Raises:
            AssertionError: If this plug is not an array.
        """

        assert self._mplug.isArray, f"Plug {self.name()} is not an array"
        return Plug(self._node, plugs.next_available_element_plug(self._mplug))

    def nextAvailableDestElementPlug(self, force: bool = False) -> Plug:
        """Get the next available input element for this array.

        Availability is based on input connections of elements and children.

        Args:
            force: Whether to force creation of a new element.

        Returns:
            The next available destination element Plug.

        Raises:
            AssertionError: If this plug is not an array.
        """

        assert self._mplug.isArray, f"Plug {self.name()} is not an array"
        return Plug(
            self._node,
            plugs.next_available_dest_element_plug(self._mplug, force=force),
        )

    @lock_node_plug_context
    def set(
        self,
        value: Any,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> OpenMaya.MDGModifier:
        """Set the value of this plug.

        Args:
            value: The value to set (type depends on attribute type).
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            The modifier used for the operation.

        Raises:
            ReferenceObjectError: If plug is referenced and locked.
        """

        if self.node().isReferenced() and self.isLocked:
            raise ReferenceObjectError(
                f"Plug {self.name()} is a reference or is locked"
            )

        return plugs.set_plug_value(self._mplug, value, mod=mod, apply=apply)

    @lock_node_plug_context
    def setFromDict(self, **plug_info):
        """Set the plug value from a dictionary of properties.

        Args:
            **plug_info: Plug property dictionary (value, default, locked, etc.).
        """

        return plugs.set_plug_info_from_dict(self._mplug, **plug_info)

    @lock_node_plug_context
    def connect(
        self,
        plug: Plug | OpenMaya.MPlug,
        children: list[Plug] | None = None,
        force: bool = True,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> OpenMaya.MDGModifier:
        """Connect this plug to a destination plug.

        Args:
            plug: The destination plug to connect to.
            children: For compounds, list indicating which children to connect.
            force: Whether to break existing connections.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the connection immediately.

        Returns:
            The modifier used for the operation.
        """

        if self.isCompound and children:
            children = children or []
            self_len = len(self)
            child_len = len(children)
            if child_len == 0:
                plugs.connect_plugs(
                    self._mplug, plug.plug(), force=force, mod=mod
                )
            # noinspection PyTypeChecker
            if child_len > self_len:
                children = children[:self_len]
            elif child_len < self_len:
                children += [False] * (self_len - child_len)
            return plugs.connect_vector_plugs(
                self._mplug,
                plug.plug(),
                children,
                force=force,
                mod=mod,
                apply=apply,
            )

        return plugs.connect_plugs(
            self._mplug, plug.plug(), mod=mod, force=force, apply=apply
        )

    @lock_node_plug_context
    def disconnect(
        self,
        plug: Plug | OpenMaya.MPlug,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> OpenMaya.MDGModifier:
        """Disconnect this plug from a destination plug.

        Args:
            plug: The destination plug to disconnect from.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the disconnection immediately.

        Returns:
            The modifier used for the operation.
        """

        modifier = mod or OpenMaya.MDGModifier()
        modifier.disconnect(self._mplug, plug.plug())
        if mod is None or apply:
            modifier.doIt()

        return modifier

    @lock_node_plug_context
    def disconnectAll(
        self,
        source: bool = True,
        destination: bool = True,
        mod: OpenMaya.MDGModifier | None = None,
    ) -> tuple[bool, OpenMaya.MDGModifier]:
        """Disconnect all connections to/from this plug.

        Args:
            source: Whether to disconnect source (input) connections.
            destination: Whether to disconnect destination (output) connections.
            mod: Optional modifier for batching operations.

        Returns:
            Tuple of (success, modifier).
        """

        return plugs.disconnect_plug(
            self._mplug, source=source, destination=destination, modifier=mod
        )

    def source(self) -> Plug | None:
        """Get the source plug connected to this plug.

        Returns:
            The source Plug, or None if not connected.
        """

        source = self._mplug.source()
        return (
            Plug(node_by_object(source.node()), source)
            if not source.isNull
            else None
        )

    def sourceNode(self) -> DGNode | DagNode | None:
        """Get the source node connected to this plug.

        Returns:
            The source node, or None if not connected.
        """

        source = self.source()
        return source.node() if source is not None else None

    def destinations(self) -> Iterator[Plug]:
        """Iterate over all destination plugs.

        Yields:
            Destination Plug instances.
        """

        for destination_plug in self._mplug.destinations():
            yield Plug(
                node_by_object(destination_plug.node()), destination_plug
            )

    def destinationNodes(self) -> Iterator[DGNode]:
        """Iterate over all destination nodes.

        Yields:
            Destination node instances.
        """

        for destination_plug in self.destinations():
            yield destination_plug.node()

    @lock_node_plug_context
    def rename(
        self, name: str, mod: OpenMaya.MDGModifier | None = None
    ) -> bool:
        """Rename this attribute.

        Args:
            name: New attribute name (both long and short).
            mod: Optional modifier for batching operations.

        Returns:
            True if successful.
        """

        with plugs.set_locked_context(self._mplug):
            mod = mod or OpenMaya.MDGModifier()
            mod.renameAttribute(
                self.node().object(), self.attribute(), name, name
            )
            mod.doIt()

        return True

    def show(self):
        """Show this attribute in the channel box and make it keyable."""

        self._mplug.isChannelBox = True

    def hide(self):
        """Hide this attribute from the channel box and make it non-keyable."""

        self._mplug.isChannelBox = False
        self._mplug.isKeyable = False

    def lock(self, flag: bool):
        """Set the lock state of this plug.

        Args:
            flag: True to lock; False to unlock.
        """

        self._mplug.isLocked = flag

    def lockAndHide(self):
        """Lock this attribute and hide it from the channel box."""

        self._mplug.isLocked = True
        self._mplug.isChannelBox = False
        self._mplug.isKeyable = False

    def setKeyable(self, flag: bool):
        """Set whether this attribute is keyable.

        Args:
            flag: True to make keyable; False otherwise.
        """

        self._mplug.isKeyable = flag

    @lock_node_plug_context
    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> OpenMaya.MDGModifier:
        """Delete this attribute from its node.

        For array elements, removes the element. For regular attributes,
        removes the entire attribute.

        Args:
            mod: Optional modifier for batching operations.
            apply: Whether to apply the deletion immediately.

        Returns:
            The modifier used for the operation.

        Raises:
            ReferenceObjectError: If attribute is referenced and not dynamic.
        """

        if not self.isDynamic and self.node().isReferenced():
            raise ReferenceObjectError(
                f"Plug {self.name()} is reference and locked"
            )

        modifier = mod or OpenMaya.MDGModifier()

        if self._mplug.isElement:
            logical_index = self._mplug.logicalIndex()
            modifier = plugs.remove_element_plug(
                self._mplug.array(), logical_index, mod=modifier, apply=apply
            )
        else:
            modifier.removeAttribute(self.node().object(), self.attribute())

        if mod is None or apply:
            modifier.doIt()

        return modifier

    @lock_node_plug_context
    def deleteElements(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> OpenMaya.MDGModifier:
        """Delete all elements from this array plug.

        Args:
            mod: Optional modifier for batching operations.
            apply: Whether to apply the deletion immediately.

        Returns:
            The modifier used for the operation.

        Raises:
            ReferenceObjectError: If attribute is referenced and not dynamic.
            TypeError: If this plug is not an array.
        """

        if not self.isDynamic and self.node().isReferenced():
            raise ReferenceObjectError(
                f"Plug {self.name()} is reference and locked"
            )
        if not self._mplug.isArray:
            raise TypeError(
                "Invalid plug type to delete, must be of type Array"
            )

        modifier = mod or OpenMaya.MDGModifier()
        for element in self:
            logical_index = element.logicalIndex()
            modifier = plugs.remove_element_plug(
                self._mplug, logical_index, mod=modifier, apply=apply
            )

        if mod is None or apply:
            modifier.doIt()

        return modifier

    # noinspection PyUnusedLocal
    def serializeFromScene(self, *args, **kwargs) -> dict:
        """Serialize this plug to a JSON-compatible dictionary.

        Returns:
            Dictionary containing serialized plug data.
        """

        return plugs.serialize_plug(self._mplug) if self.exists() else {}

    @staticmethod
    def _convert_value_type(value: Any) -> Any:
        """Convert Maya types to wrapper types.

        Converts MObjects to node wrappers and recursively processes lists.

        Args:
            value: Value to convert.

        Returns:
            Converted value with MObjects wrapped as nodes.
        """

        is_mobj = isinstance(value, OpenMaya.MObject)
        is_valid_mobj = False if not is_mobj else nodes.is_valid_mobject(value)
        if is_mobj and is_valid_mobj:
            return node_by_object(value)
        elif is_mobj and not is_valid_mobj:
            return None
        elif isinstance(value, (list, tuple)):
            value = [Plug._convert_value_type(val) for val in value]

        return value


class NurbsCurve(DagNode):
    """Wrapper class for Maya NURBS curve nodes."""

    pass


class Mesh(DagNode):
    """Wrapper class for Maya polygon mesh nodes."""

    pass


class Camera(DagNode):
    """Wrapper class for Maya camera nodes."""

    pass


class IkHandle(DagNode):
    """Wrapper class for Maya IK handle nodes.

    Provides constants for twist control and axis settings used with
    spline IK and other IK systems.

    Attributes:
        SCENE_UP through RELATIVE: Twist control worldUpType enum values.
        FORWARD_*: Forward axis enum values.
        UP_*: Up axis enum values.
    """

    # Twist controls scene worldUpType enum value.
    SCENE_UP = 0
    # Twist controls object up worldUpType enum value.
    OBJECT_UP = 1
    # Twist controls object up start/end worldUpType enum value.
    OBJECT_UP_START_END = 2
    # Twist controls object rotation up worldUpType enum value.
    OBJECT_ROTATION_UP = 3
    # Twist controls object rotation up start/end worldUpType enum value.
    OBJECT_ROTATION_UP_START_END = 4
    # Twist controls Vector worldUpType enum value.
    VECTOR = 5
    # Twist controls Vector start/end worldUpType enum value.
    VECTOR_START_END = 6
    # Twist controls relative worldUpType enum value.
    RELATIVE = 7

    FORWARD_POSITIVE_X = 0
    FORWARD_POSITIVE_Y = 1
    FORWARD_POSITIVE_Z = 2
    FORWARD_NEGATIVE_X = 3
    FORWARD_NEGATIVE_Y = 4
    FORWARD_NEGATIVE_Z = 5

    UP_POSITIVE_Y = 0
    UP_NEGATIVE_Y = 1
    UP_CLOSEST_Y = 2
    UP_POSITIVE_Z = 3
    UP_NEGATIVE_Z = 4
    UP_CLOSEST_Z = 5
    UP_POSITIVE_X = 6
    UP_NEGATIVE_X = 7
    UP_CLOSEST_X = 8

    @staticmethod
    def vector_to_forward_axis_enum(vec: Iterable[float, float, float]) -> int:
        """Convert a vector to forward axis enum value.

        Determines the forward axis by finding the axis with largest magnitude.

        Args:
            vec: Direction vector (x, y, z).

        Returns:
            Forward axis enum value (FORWARD_POSITIVE_X, etc.).
        """

        axis_index = mathlib.X_AXIS_INDEX
        # noinspection PyTypeChecker
        is_negative = sum(vec) < 0.0

        # noinspection PyTypeChecker
        for axis_index, value in enumerate(vec):
            if int(value) != 0:
                break

        if is_negative:
            return {
                mathlib.X_AXIS_INDEX: IkHandle.FORWARD_NEGATIVE_X,
                mathlib.Y_AXIS_INDEX: IkHandle.FORWARD_NEGATIVE_Y,
                mathlib.Z_AXIS_INDEX: IkHandle.FORWARD_NEGATIVE_Z,
            }[axis_index]

        return axis_index

    @staticmethod
    def vector_to_up_axis_enum(vec: Iterable[float, float, float]) -> int:
        """Convert a vector to up axis enum value.

        Determines the up axis by finding the axis with largest magnitude.

        Args:
            vec: Up vector (x, y, z).

        Returns:
            Up axis enum value (UP_POSITIVE_Y, etc.).
        """

        axis_index = mathlib.X_AXIS_INDEX
        # noinspection PyTypeChecker
        is_negative = sum(vec) < 0.0

        # noinspection PyTypeChecker
        for axis_index, value in enumerate(vec):
            if int(value) != 0:
                break

        axis_mapping = {
            mathlib.X_AXIS_INDEX: IkHandle.UP_POSITIVE_X,
            mathlib.Y_AXIS_INDEX: IkHandle.UP_POSITIVE_Y,
            mathlib.Z_AXIS_INDEX: IkHandle.UP_POSITIVE_Z,
        }
        if is_negative:
            axis_mapping = {
                mathlib.X_AXIS_INDEX: IkHandle.UP_NEGATIVE_X,
                mathlib.Y_AXIS_INDEX: IkHandle.UP_NEGATIVE_Y,
                mathlib.Z_AXIS_INDEX: IkHandle.UP_NEGATIVE_Z,
            }

        return axis_mapping[axis_index]


class Joint(DagNode):
    """Wrapper class for Maya joint nodes.

    Provides specialized handling for joint orientation and parenting
    that maintains proper joint chains.
    """

    def create(
        self,
        **kwargs,
    ) -> Joint:
        """Create a new joint node.

        Args:
            **kwargs: Joint properties including:
                - name: Joint name (default: "joint").
                - parent: Parent node.
                - translate: World translation.
                - rotate: World rotation.
                - rotateOrder: Rotation order index.

        Returns:
            This instance, now wrapping the newly created joint.
        """

        kwargs["type"] = "joint"
        kwargs["name"] = kwargs.get("name", "joint")
        kwargs["parent"] = kwargs.get("parent", None)
        joint, _ = nodes.deserialize_node(
            kwargs, parent=None, include_attributes=True
        )
        self.setObject(joint)
        rotate_order = kwargs.get("rotateOrder", 0)
        self.setRotationOrder(rotate_order)
        world_matrix = OpenMaya.MTransformationMatrix()
        world_matrix.setTranslation(
            OpenMaya.MVector(kwargs.get("translate", OpenMaya.MVector())),
            OpenMaya.MSpace.kWorld,
        )
        world_matrix.setRotation(
            OpenMaya.MQuaternion(kwargs.get("rotate", OpenMaya.MQuaternion()))
        )
        world_matrix.reorderRotation(constants.kRotateOrders[rotate_order])
        self.setWorldMatrix(world_matrix.asMatrix())

        self.setParent(kwargs.get("parent", None), maintain_offset=True)
        self.segmentScaleCompensate.set(False)

        return self

    def setParent(
        self,
        parent: DagNode | None,
        maintain_offset: bool = True,
        mod: OpenMaya.MDagModifier | None = None,
        apply: bool = True,
    ) -> OpenMaya.MDagModifier:
        """Set the parent of this joint.

        Handles joint orientation properly by transferring rotation to
        jointOrient attribute and connecting scale compensation.

        Args:
            parent: New parent node, or None for world parenting.
            maintain_offset: Whether to preserve world-space position.
            mod: Optional modifier for batching operations.
            apply: Whether to apply the change immediately.

        Returns:
            The modifier used for the operation.
        """

        rotation = self.rotation(space=OpenMaya.MSpace.kWorld)

        result = super().setParent(parent, maintain_offset=True)
        if parent is None:
            return result

        parent_quat = parent.rotation(
            OpenMaya.MSpace.kWorld, as_quaternion=True
        )
        new_rotation = rotation * parent_quat.inverse()
        self.attribute("jointOrient").set(new_rotation.asEulerRotation())
        self.setRotation((0.0, 0.0, 0.0), OpenMaya.MSpace.kTransform)
        if parent.apiType() == OpenMaya.MFn.kJoint:
            parent.attribute("scale").connect(self.inverseScale)

        return result


# noinspection PyPep8Naming
class ContainerAsset(DGNode):
    """Wrapper class for MFnContainerNode nodes providing a set of common methods."""

    MFN_TYPE = OpenMaya.MFnContainerNode

    # noinspection PyMethodOverriding
    def create(self, name: str):
        """Creates the MFnSet and sets this instance MObject to the new node.

        :param name: name for the asset container node.
        """

        container = factory.create_dg_node(name, "container")
        self.setObject(container)

        return self

    def serializeFromScene(self, *args, **kwargs) -> dict:
        """Serializes current asset container instance and returns a JSON compatible
        dictionary with the container data.

        :return: serialized asset container data.
        """

        members = self.members()
        published_attributes = self.publishedAttributes()
        published_nodes = self.publishedNodes()

        return (
            {
                "graph": nodes.serialize_nodes(members),
                "attributes": published_attributes,
                "nodes": published_nodes,
            }
            if members
            else {}
        )

    # noinspection PyMethodOverriding
    def delete(self, remove_container: bool = True):
        """Deletes the node from the scene.

        :param remove_container: If True, then the container will be deleted, otherwise
            only members will be removed.
        """

        container_name = self.fullPathName()
        self.lock(False)
        cmds.container(
            container_name, edit=True, removeContainer=remove_container
        )

    @property
    def blackBox(self):
        """Getter method that returns the current black box attribute value.

        :return: True if the contents of the container are public; False otherwise.
        """

        return self.attribute("blackBox").asBool()

    @blackBox.setter
    def blackBox(self, flag):
        """Setter method that sets current black box attribute value.

        :param flag: True if the contents of the container are not public; False
            otherwise.
        """

        mfn = self.mfn()
        if not mfn:
            return
        self.attribute("blackBox").set(flag)

    def isCurrent(self) -> bool:
        """Returns whether this current container is the current active container.

        :return: True if this container is the active one; False otherwise.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnContainerNode = self._mfn
        return mfn.isCurrent()

    def makeCurrent(self, value):
        """Sets this container to be the currently active.

        :param bool value: whether to make container currently active.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnContainerNode = self._mfn
        mfn.makeCurrent(value)

    @contextlib.contextmanager
    def makeCurrentContext(self, value: bool):
        """Context manager that sets this container to be the currently active.

        :param value: whether to make container currently active.
        """

        current_state = self.isCurrent()
        if current_state == value:
            yield
        else:
            try:
                self.makeCurrent(value)
                yield
            finally:
                self.makeCurrent(current_state)

    def members(self):
        """Returns current members of this container instance.

        :return: list of member nodes.
        :rtype: list(DagNode)
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnContainerNode = self.mfn()
        return map(node_by_object, mfn.getMembers())

    def addNode(self, node_to_add: DGNode, force: bool = False) -> bool:
        """Adds the given node to the container without publishing it.

        :param DGNode node_to_add: node to add into this container.
        :param bool force: whether to force the operation.
        :return: True if the add node operation was successful; False otherwise.
        :raises RuntimeError: if something wrong happens when adding the node into
            the container.
        """

        mobj = node_to_add.object()
        if mobj != self._handle.object():
            try:
                cmds.container(
                    self.fullPathName(),
                    edit=True,
                    addNode=node_to_add.fullPathName(),
                    includeHierarchyBelow=True,
                    force=force,
                )
            except RuntimeError:
                raise
            return True

        return False

    def addNodes(self, nodes_to_add: list[DGNode], force: bool = False):
        """Adds the given nodes to the container without published them.

        :param nodes_to_add: nodes to add into this container.
        :param force: whether to force the operation.
        """

        container_path = self.fullPathName(False, True)
        for node_to_add in iter(nodes_to_add):
            if node_to_add == self:
                continue
            cmds.container(
                container_path,
                edit=True,
                addNode=node_to_add.fullPathName(),
                includeHierarchyBelow=True,
                force=force,
            )

    def publishedAttributes(self) -> list[Plug]:
        """Returns all published attributes in this container.

        :return: list of published attributes.
        """

        results = cmds.container(
            self.fullPathName(), query=True, bindAttr=True
        )
        if not results:
            return []

        # cmds returns a flat list of attribute name, published name, so we chunk as pai
        return [
            plug_by_name(attr)
            for attr, _ in helpers.iterate_chunks(results, 2)
        ]

    def publishAttribute(self, attribute: Plug):
        """Publishes the given attribute to the container.

        :param attribute: attribute to publish.
        """

        self.publishAttributes([attribute])

    def publishAttributes(self, attributes: Iterable[Plug]):
        """Publishes the given attributes to the container.

        :param attributes: list of attributes to publish.
        """

        container_name = self.fullPathName()
        current_publishes = self.publishedAttributes()
        for plug in attributes:
            if plug in current_publishes or plug.isChild or plug.isElement:
                continue
            name = plug.name()
            short_name = plug.partialName()
            try:
                cmds.container(
                    str(container_name),
                    edit=True,
                    publishAndBind=[str(name), str(short_name)],
                )
            except RuntimeError:
                pass

    def unPublishAttribute(self, attribute_name: str) -> bool:
        """Unpublishes attribute with given name from this container.

        :param attribute_name: name of the attribute to unpublish.
        :return: True if the attribute was unpublished successfully; False otherwise.
        """

        container_name = self.fullPathName()
        try:
            cmds.container(
                container_name,
                edit=True,
                unbindAndUnpublish=".".join([container_name, attribute_name]),
            )
        except RuntimeError:
            return False

        return True

    def unPublishAttributes(self):
        """Unpublish all attributes published in this container."""

        for published_attribute in self.publishedAttributes():
            self.unpublish_attribute(
                published_attribute.partialName(use_long_names=False)
            )

    def publishedNodes(self):
        """Returns list of published node in this container.

        :return: list of published nodes.
        :rtype: list(DGNode)
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnContainerNode = self.mfn()
        return [
            node_by_object(node[1])
            for node in mfn.getPublishedNodes(
                OpenMaya.MFnContainerNode.kGeneric
            )
            if not node[0].isNull()
        ]

    def publishNode(self, node_to_publish: DGNode):
        """Publishes the given node to the container.

        :param node_to_publish: node to publish.
        """

        container_name = self.fullPathName()
        node_name = node_to_publish.fullPathName()
        short_name = node_name.split("|")[-1].split(":")[-1]
        try:
            cmds.containerPublish(
                container_name,
                publishNode=[short_name, node_to_publish.mfn().typeName],
            )
        except RuntimeError:
            pass
        try:
            cmds.containerPublish(
                container_name, bindNode=[short_name, node_name]
            )
        except RuntimeError:
            pass

    def publishNodes(self, nodes_to_publish: Iterable[DGNode]):
        """Publishes the given nodes to the container.

        :param nodes_to_publish: list of nodes to publish.
        """

        for i in iter(nodes_to_publish):
            self.publishNode(i)

    def publishNodeAsChildParentAnchor(self, node: DGNode):
        """Publishes the given node as a child parent anchor.

        :param node: node to publish.
        """

        container_name = self.fullPathName()
        node_name = node.fullPathName()
        short_name = node_name.split("|")[-1].split(":")[-1]
        parent_name = "_".join((short_name, "parent"))
        child_name = "_".join((short_name, "child"))
        cmds.container(
            container_name, edit=True, publishAsParent=(node_name, parent_name)
        )
        cmds.container(
            container_name, edit=True, publishAsChild=(node_name, child_name)
        )

    def unPublishNode(self, node: DGNode):
        """Unpublishes given node from the container.

        :param node: node to unpublish.
        """

        message_plug = node.attribute("message")
        container_name = self.fullPathName()
        for dest_plug in message_plug.destinations():
            node = dest_plug.node().object()
            if node.hasFn(OpenMaya.MFn.kContainer):
                parent_name = dest_plug.parent().partialName(use_alias=True)
                cmds.containerPublish(container_name, unbindNode=parent_name)
                cmds.containerPublish(
                    container_name, unpublishNode=parent_name
                )
                break

    def removeUnboundAttributes(self):
        """Removes any unbound attributes from the container."""

        container_name = self.fullPathName()
        for unbound in (
            cmds.container(
                container_name, query=True, publishName=True, unbindAttr=True
            )
            or []
        ):
            cmds.container(container_name, edit=True, removeUnbound=unbound)

    def setParentAnchor(self, node: DagNode):
        """Sets the given node as a parent anchor to the container.

        :param node: node to set as parent anchor.
        """

        container_name = self.fullPathName()
        node_name = node.fullPathName()
        short_name = node_name.split("|")[-1].split(":")[-1]
        parent_name = "_".join((short_name, "parent"))
        cmds.container(
            container_name, edit=True, publishAsParent=(node_name, parent_name)
        )

    def setChildAnchor(self, node: DagNode):
        """Sets the given node as a child anchor to the container.

        :param node: node to set as child anchor.
        """

        container_name = self.fullPathName()
        node_name = node.fullPathName()
        short_name = node_name.split("|")[-1].split(":")[-1]
        child_name = "_".join((short_name, "child"))
        cmds.container(
            container_name, edit=True, publishAsChild=(node_name, child_name)
        )

    def childAnchor(self) -> DGNode:
        """Returns the child anchor node of this container.

        :return: child anchor node.
        """

        child = cmds.container(
            self.fullPathName(), query=True, publishAsChild=True
        )
        return node_by_name(child[1]) if child else None

    def parentAnchor(self) -> DGNode:
        """Returns the parent anchor node of this container.

        :return: parent anchor node.
        """

        parent = cmds.container(
            self.fullPathName(), query=True, publishAsParent=True
        )
        return node_by_name(parent[1]) if parent else None

    def subContainers(self) -> Iterator[ContainerAsset]:
        """Generator function that iterates over all sub containers.

        :return: iterated sub containers.
        """

        mfn: OpenMaya.MFnContainerNode = self._mfn
        return map(node_by_object, mfn.getSubcontainers())


# noinspection PyPep8Naming
class AnimCurve(DGNode):
    """Wrapper class for Maya animCurve nodes."""

    MFN_TYPE = OpenMayaAnim.MFnAnimCurve

    def setPrePostInfinity(
        self,
        pre: int,
        post: int,
        change: OpenMayaAnim.MAnimCurveChange | None = None,
    ):
        """Sets the behaviour of the curve for the range occurring before the first key and after the last key.

        :param pre: sets the behaviour of the curve for the range occurring before the first key.
        :param post: sets the behaviour of the curve for the range occurring after the last key.
        :param change: undo change object.

        Example:
            undo_change = OpenMayaAnim.MAnimCurveChange()
            curve = DGNode("myCurve", "animCurveTU")
            curve.setPrePostInfinity(
                OpenMayaAnim.MFnAnimCurve.kConstant,
                OpenMayaAnim.MFnAnimCurve.kConstant,
                undo_change
            )
        """

        # noinspection PyTypeChecker
        mfn: OpenMayaAnim.MFnAnimCurve = self.mfn()
        if change:
            mfn.setPreInfinityType(pre, change)
            mfn.setPostInfinityType(post, change)
        else:
            mfn.setPreInfinityType(pre)
            mfn.setPostInfinityType(post)

    def addKeysWithTangents(
        self,
        times: OpenMaya.MTimeArray | Iterable,
        values: Iterable[float],
        tangent_in_type: int = OpenMayaAnim.MFnAnimCurve.kTangentGlobal,
        tangent_out_type: int = OpenMayaAnim.MFnAnimCurve.kTangentGlobal,
        tangent_in_type_array: list[int] | None = None,
        tangent_out_type_array: list[int] | None = None,
        tangent_in_x_array: list[int] | None = None,
        tangent_in_y_array: list[int] | None = None,
        tangent_out_x_array: list[int] | None = None,
        tangent_out_y_array: list[int] | None = None,
        tangents_locked_aray: list[int] | None = None,
        weights_locked_array: list[int] | None = None,
        convert_units: bool = True,
        keep_existing_keys: bool = False,
        change: OpenMayaAnim.MAnimCurveChange | None = None,
    ):
        """Adds a set of new keys with the given corresponding values and tangent types at the given times.

        :param times: times at which keys are to be added.
        :param values: values to which the keys is to be set.
        :param tangent_in_type: in tangent type for al the added keys.
        :param tangent_out_type: out tangent type for all the added keys.
        :param tangent_in_type_array: in tangent types for individual added keys.
        :param tangent_out_type_array: out tangent types for individual added keys.
        :param tangent_in_x_array: Absolute x values of the slope for individual added in tangent keys.
        :param tangent_in_y_array: Absolute y values of the slope for individual added in tangent keys.
        :param tangent_out_x_array: Absolute x values of the slope for individual added out tangent keys.
        :param tangent_out_y_array: Absolute y values of the slope for individual added out tangent keys.
        :param tangents_locked_aray: lock status for individual added keys.
        :param weights_locked_array: weight lock status for individual added keys.
        :param convert_units: whether to convert the values to internal UI units.
        :param keep_existing_keys: whether new keys should be merged with existing keys or if they should be cut prior
            to adding the new keys.
        :param change cache to store undo/redo information.
        """

        arguments = [
            times,
            values,
            tangent_in_type,
            tangent_out_type,
            tangent_in_type_array or [],
            tangent_out_type_array or [],
            tangent_in_x_array or [],
            tangent_in_y_array or [],
            tangent_out_x_array or [],
            tangent_out_y_array or [],
            tangents_locked_aray or [],
            weights_locked_array or [],
            convert_units,
            keep_existing_keys,
        ]
        if change is not None:
            arguments.append(change)

        # noinspection PyTypeChecker
        mfn: OpenMayaAnim.MFnAnimCurve = self.mfn()
        mfn.addKeysWithTangents(*arguments)


class SkinCluster(DGNode):
    pass


# noinspection PyPep8Naming
class ObjectSet(DGNode):
    """Wrapper class for Maya object sets"""

    MFN_TYPE = OpenMaya.MFnSet

    # noinspection PyMethodOverriding
    def create(
        self,
        name: str,
        mod: OpenMaya.MDGModifier | None = None,
        members: list[DGNode] | None = None,
    ) -> ObjectSet:
        """Creates the MFnSet and sets this instance MObject to the new node.

        :param name: name for the object set node.
        :param mod: modifier to add to, if None it will create one.
        :param members: list of nodes to add as members of this object set.
        :return: instance of the new object set.
        """

        obj = factory.create_dg_node(name, "objectSet", mod=mod)
        self.setObject(obj)
        if members is not None:
            self.addMembers(members)

        return self

    def isMember(self, node: DGNode) -> bool:
        """Returns whether given node is a member of this set.

        :param node: node to check for membership.
        :return: True if given node is a member of this set; False otherwise.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnSet = self._mfn
        return mfn.isMember(self.object()) if node.exists() else False

    def addMember(self, node: DGNode) -> bool:
        """Adds given node to the set.

        :param DGNode node: node to add as a new member to this set.
        :return: True if the node was added successfully; False otherwise.
        :rtype: bool
        """

        if not node.exists():
            return False
        elif node.hasFn(OpenMaya.MFn.kDagNode):
            if self in node.instObjGroups[0].destinationNodes():
                return False
            node.instObjGroups[0].connect(
                self.dagSetMembers.nextAvailableDestElementPlug()
            )
        else:
            if self in node.attribute("message").destinationNodes():
                return False
            node.message.connect(
                self.dnSetMembers.nextAvailableDestElementPlug()
            )

        return True

    def addMembers(self, new_members: list[DGNode]):
        """Adds a list of new objects into the set.

        :param list[DGNode] new_members: list of nodes to add as new members to this set.
        """

        for member in new_members:
            self.addMember(member)

    def members(self, flatten: bool = False) -> list[DGNode]:
        """Returns the members of this set as a list.

        :param bool flatten: whether all sets that exist inside this set will be expanded into a list of their contents.
        :return: a list of all members in the set.
        :rtype: list[DGNode]
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnSet = self._mfn
        return list(
            map(node_by_name, mfn.getMembers(flatten).getSelectionStrings())
        )

    def removeMember(self, member: DGNode):
        """Removes given item from the set.

        :param DGNode member: item to remove.
        """

        if member.exists():
            self.removeMembers([member])

    def removeMembers(self, members: list[DGNode]):
        """Removes items of the list from the set.

        :param list[DGNode] members: member nodes to remove.
        """

        member_list = OpenMaya.MSelectionList()
        for member in members:
            if not member.exists():
                continue
            member_list.add(member.fullPathName())

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnSet = self._mfn
        mfn.removeMembers(member_list)

    def clear(self):
        """Removes all members from this set."""

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnSet = self._mfn
        mfn.clear()


class BlendShape(DGNode):
    pass


# noinspection PyPep8Naming
class DisplayLayer(DGNode):
    """Wrapper class for Maya display layers."""

    def addNodes(self, display_nodes: list[DagNode]):
        """Add multiple nodes to this display layer.

        Args:
            display_nodes: Nodes to add to the display layer.
        """

        draw_info_plug = self.drawInfo
        for display_node in display_nodes:
            draw_info_plug.connect(display_node.drawOverride)

    def addNode(self, node: DagNode):
        """Add a node to this display layer.

        Args:
            node: Node to add to the display layer.
        """

        self.drawInfo.connect(node.drawOverride)


class AnimLayer(DGNode):
    """Wrapper class for Maya animation layer nodes."""

    pass


class ObjectDoesNotExistError(Exception):
    """Raised when an operation is attempted on a non-existent node or plug."""

    pass


class ReferenceObjectError(Exception):
    """Raised when an operation is not allowed on a referenced object."""

    pass


class InvalidPlugPathError(Exception):
    """Raised when a plug path string is malformed or invalid."""

    pass


class InvalidTypeForPlugError(Exception):
    """Raised when an incompatible value type is used for a plug."""

    pass


def node_by_object(
    mobj: OpenMaya.MObject,
) -> (
    DGNode
    | DagNode
    | NurbsCurve
    | Mesh
    | Camera
    | IkHandle
    | Joint
    | ContainerAsset
    | AnimCurve
    | SkinCluster
    | AnimLayer
    | ObjectSet
    | BlendShape
    | DisplayLayer
    | AnimLayer
):
    """Create a wrapper instance for a Maya object.

    Automatically determines the appropriate wrapper class based on
    the object's Maya type.

    Args:
        mobj: The Maya object to wrap.

    Returns:
        An appropriate wrapper instance (DGNode, DagNode, Joint, etc.).
    """

    if mobj.hasFn(OpenMaya.MFn.kDagNode):
        dag_path = OpenMaya.MDagPath.getAPathTo(mobj)
        if mobj.hasFn(OpenMaya.MFn.kNurbsCurve):
            sup = NurbsCurve
        elif mobj.hasFn(OpenMaya.MFn.kMesh):
            sup = Mesh
        elif mobj.hasFn(OpenMaya.MFn.kCamera):
            sup = Camera
        elif mobj.hasFn(OpenMaya.MFn.kIkHandle):
            sup = IkHandle
        elif mobj.hasFn(OpenMaya.MFn.kJoint):
            sup = Joint
        else:
            sup = DagNode
        object_to_set = dag_path
    else:
        if mobj.hasFn(OpenMaya.MFn.kContainer):
            sup = ContainerAsset
        elif mobj.hasFn(OpenMaya.MFn.kAnimCurve):
            sup = AnimCurve
        elif mobj.hasFn(OpenMaya.MFn.kSkinClusterFilter):
            sup = SkinCluster
        elif mobj.hasFn(OpenMaya.MFn.kControllerTag):
            sup = DGNode
        elif mobj.hasFn(OpenMaya.MFn.kSet):
            sup = ObjectSet
        elif mobj.hasFn(OpenMaya.MFn.kBlendShape):
            sup = BlendShape
        elif mobj.hasFn(OpenMaya.MFn.kDisplayLayer):
            sup = DisplayLayer
        else:
            sup = DGNode
        object_to_set = mobj

    return sup(object_to_set)


def node_by_name(
    node_name: str | OpenMaya.MObject,
) -> (
    DGNode
    | DagNode
    | NurbsCurve
    | Mesh
    | Camera
    | IkHandle
    | Joint
    | ContainerAsset
    | AnimCurve
    | SkinCluster
    | AnimLayer
    | ObjectSet
    | BlendShape
    | DisplayLayer
    | AnimLayer
    | None
):
    """Create a wrapper instance for a node by name.

    Automatically determines the appropriate wrapper class based on
    the node's Maya type.

    Args:
        node_name: Node name (preferably full DAG path) or MObject.

    Returns:
        An appropriate wrapper instance, or None if node doesn't exist.
    """

    mobj = nodes.mobject(node_name)
    if mobj is None:
        return None
    if mobj.hasFn(OpenMaya.MFn.kDagNode):
        dag_path = OpenMaya.MDagPath.getAPathTo(mobj)
        if mobj.hasFn(OpenMaya.MFn.kNurbsCurve):
            sup = NurbsCurve
        elif mobj.hasFn(OpenMaya.MFn.kMesh):
            sup = Mesh
        elif mobj.hasFn(OpenMaya.MFn.kCamera):
            sup = Camera
        elif mobj.hasFn(OpenMaya.MFn.kIkHandle):
            sup = IkHandle
        elif mobj.hasFn(OpenMaya.MFn.kJoint):
            sup = Joint
        else:
            sup = DagNode
        object_to_set = dag_path
    else:
        if mobj.hasFn(OpenMaya.MFn.kContainer):
            sup = ContainerAsset

        elif mobj.hasFn(OpenMaya.MFn.kAnimCurve):
            sup = AnimCurve
        elif mobj.hasFn(OpenMaya.MFn.kSkinClusterFilter):
            sup = SkinCluster
        elif mobj.hasFn(OpenMaya.MFn.kControllerTag):
            sup = DGNode
        elif mobj.hasFn(OpenMaya.MFn.kAnimLayer):
            sup = AnimLayer
        elif mobj.hasFn(OpenMaya.MFn.kSet):
            sup = ObjectSet
        elif mobj.hasFn(OpenMaya.MFn.kBlendShape):
            sup = BlendShape
        elif mobj.hasFn(OpenMaya.MFn.kDisplayLayer):
            sup = DisplayLayer
        else:
            sup = DGNode
        object_to_set = mobj

    return sup(object_to_set)


def nodes_by_names(node_names: Iterable[str]) -> Iterator[DGNode | DagNode]:
    """Create wrapper instances for multiple nodes by name.

    Args:
        node_names: Node names to wrap.

    Yields:
        Wrapper instances for each node.
    """

    for node_name in node_names:
        yield node_by_name(node_name)


def nodes_by_type_names(
    node_type_names: str | Iterable[str],
) -> Iterator[DGNode | DagNode]:
    """Get wrapper instances for all nodes of given type(s).

    Args:
        node_type_names: Node type name(s) to search for.

    Yields:
        Wrapper instances for each matching node.
    """

    found_node_names = cmds.ls(type=node_type_names, long=True)
    for found_node_name in found_node_names:
        yield node_by_name(found_node_name)


def selected(
    filter_types: Iterable[int] | None = None,
) -> Iterable[DGNode | DagNode]:
    """Get the currently selected nodes.

    Args:
        filter_types: Optional MFn type constants to filter by.

    Returns:
        Iterable of wrapper instances for selected nodes.
    """

    return map(node_by_object, scene.iterate_selected_nodes(filter_types))


def select(
    nodes_to_select: Iterable[DGNode | DagNode],
    mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
    apply: bool = True,
) -> OpenMaya.MDGModifier | OpenMaya.MDagModifier:
    """Select nodes in the scene.

    Args:
        nodes_to_select: Node wrappers to select.
        mod: Optional modifier for batching operations.
        apply: Whether to apply the selection immediately.

    Returns:
        The modifier used for the operation.
    """

    mod = mod or OpenMaya.MDGModifier()
    mod.pythonCommandToExecute(
        f"from maya import cmds; cmds.select({[node.fullPathName() for node in nodes_to_select]})"
    )
    if apply:
        mod.doIt()

    return mod


def select_by_names(
    names: list[str],
    mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
    apply: bool = True,
) -> OpenMaya.MDGModifier | OpenMaya.MDagModifier:
    """Select nodes by name.

    Args:
        names: Node names to select.
        mod: Optional modifier for batching operations.
        apply: Whether to apply the selection immediately.

    Returns:
        The modifier used for the operation.
    """

    mod = mod or OpenMaya.MDGModifier()
    mod.pythonCommandToExecute(f"from maya import cmds; cmds.select({names})")
    if apply:
        mod.doIt()

    return mod


def clear_selection(
    mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
    apply: bool = True,
) -> OpenMaya.MDGModifier | OpenMaya.MDagModifier:
    """Clear the current selection.

    Args:
        mod: Optional modifier for batching operations.
        apply: Whether to apply immediately.

    Returns:
        The modifier used for the operation.
    """

    mod = mod or OpenMaya.MDGModifier()
    mod.pythonCommandToExecute(
        "from maya import cmds; cmds.select(clear=True)"
    )
    if apply:
        mod.doIt()

    return mod


def plug_by_name(plug_path: str) -> Plug:
    """Get a Plug instance by its full path.

    Args:
        plug_path: Full plug path (e.g., "pCube1.translateX").

    Returns:
        The Plug instance.

    Raises:
        InvalidPlugPathError: If the path is malformed or plug doesn't exist.
    """

    if "." not in plug_path:
        raise InvalidPlugPathError(plug_path)

    plug = plugs.as_mplug(plug_path)
    return Plug(node_by_object(plug.node()), plug)
