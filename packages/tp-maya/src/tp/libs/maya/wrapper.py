from __future__ import annotations

import logging
import contextlib

from functools import wraps
from typing import Type, Iterator, Iterable, Callable, Any

from tp.python import helpers
from maya import cmds
from maya.api import OpenMaya, OpenMayaAnim

from .om import constants  # noqa: F401
from .om import factory, nodes, plugs, attributetypes, mathlib, dagutils, scene
from .om.constants import *  # noqa: F403
from .om.apitypes import *  # noqa: F403

logger = logging.getLogger(__name__)

LOCAL_TRANSLATE_ATTR = "translate"
LOCAL_ROTATE_ATTR = "rotate"
LOCAL_SCALE_ATTR = "scale"
LOCAL_TRANSLATE_ATTRS = ["translateX", "translateY", "translateZ"]
LOCAL_ROTATE_ATTRS = ["rotateX", "rotateY", "rotateZ"]
LOCAL_SCALE_ATTRS = ["scaleX", "scaleY", "scaleZ"]
LOCAL_TRANSFORM_ATTRS = LOCAL_TRANSLATE_ATTRS + LOCAL_ROTATE_ATTRS + LOCAL_SCALE_ATTRS


def lock_node_context(fn: Callable):
    """
    Decorator function to lock and unlock the node.

    :param fn: decorated function.
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


def lock_node_plug_context(fn: Callable):
    """
    Decorator function to lock and unlock a node plug.

    :param fn: decorated function.
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
def lock_state_attr_context(node: DGNode, attr_names: Iterable[str], state: bool):
    """
    Context manager which handles the lock state for a list of attribute on the given node.

    :param node: node to lock/unlock attributes of.
    :param attr_names: list of attribute names.
    :param state: lock state to set while executing the context scope.
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
    """
    Wrapper class for the Maya dependency graph nodes.
    """

    MFN_TYPE: Type[OpenMaya.MFnBase] = OpenMaya.MFnDependencyNode

    def __init__(self, mobj: OpenMaya.MObject | None = None):
        super().__init__()

        self._mfn: Type[OpenMaya.MFnDependencyNode] | None = None
        self._handle: OpenMaya.MObjectHandle | None = None

        if mobj is not None:
            self.setObject(mobj)

    def __hash__(self) -> int:
        """
        Returns the hash value of the node.

        :return: hash value.
        """

        return (
            self._handle.hashCode() if self._handle is not None else super().__hash__()
        )

    def __repr__(self) -> str:
        """
        Returns the string representation of the node.

        :return: string representation.
        """

        return f"<{self.__class__.__name__}> {self.fullPathName()}"

    def __str__(self) -> str:
        """
        Returns the string representation of the node.

        :return: string representation.
        """

        return self.fullPathName()

    def __bool__(self) -> bool:
        """
        Returns whether the node is currently valid within the Maya scene.

        :return: True if the node is valid; False otherwise.
        """

        return self.exists()

    def __getitem__(self, item: str) -> Plug:
        """
        Overrides __getitem__ function to attempt to retrieve the MPlug for this node.

        :param item: attribute name.
        :return: Plug
        :raises KeyError: if attribute with given name does not exist in node.
        """

        fn = self._mfn
        try:
            return Plug(self, fn.findPlug(item, False))
        except RuntimeError:
            raise KeyError(f"{self.name()} has no attribute by the name {item}")

    def __setitem__(self, key: str, value: Any):
        """
        Overrides __setitem__ function to attempt to set node attribute.

        :param key: attribute name.
        :param value: attribute value.
        :raises KeyError: if attribute with given name does not exist in node.
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
            raise RuntimeError(f"Node {self.name()} has no attribute called: {key}")

    def __getattr__(self, name: str) -> Any:
        """
        Overrides __getattr__ function to try to access node attribute.

        :param name: name of the attribute to access.
        :return: attribute value.
        """

        attr = self.attribute(name)
        if attr is not None:
            return attr

        return super().__getattribute__(name)

    def __setattr__(self, key: str, value: Any):
        """
        Overrides __setattr__ function to try to call node before calling the function.

        :param key: name of the attribute to set.
        :param value: value of the attribute.
        """

        if key.startswith("_"):
            super().__setattr__(key, value)
            return
        if self.hasAttribute(key) is not None:
            if isinstance(value, Plug):
                self.connect(key, value)
                return
            self.setAttribute(key, value)
            return

        super().__setattr__(key, value)

    def __eq__(self, other: DGNode) -> bool:
        """
        Overrides __eq__ function to check whether other object is equal to this one.

        :param other: object instance to check.
        :return: True if given object and current rule are equal; False otherwise.
        """

        if not isinstance(other, DGNode) or (
            isinstance(other, DGNode) and other.handle() is None
        ):
            return False

        return self._handle == other.handle()

    def __ne__(self, other: DGNode) -> bool:
        """
        Overrides __ne__ function to check whether other object is not equal to this one.

        :param other: object instance to check.
        :return: True if given object and current rule are not equal; False otherwise.
        """

        if not isinstance(other, DGNode):
            return True

        return self._handle != other.handle()

    def __contains__(self, key: str) -> bool:
        """
        Overrides __contains__ function to check whether an attribute with given name exists in current DG node.

        :param key: attribute name.
        :return: True if attribute with given name exists; False otherwise.
        """

        return self.hasAttribute(key)

    def __delitem__(self, key: str):
        """
        Overrides __delitem__ to delete attribute with given name from node.

        :param key: name of the attribute to delete.
        """

        self.deleteAttribute(key)

    @property
    def typeName(self) -> str:
        """
        Returns Maya API type name.

        :return: API type name.
        """

        return self._mfn.typeName

    @property
    def isLocked(self) -> bool:
        """
        Returns whether the node is locked.

        :return: True if node is locked; False otherwise.
        """

        return self.mfn().isLocked

    def create(
        self,
        name: str,
        node_type: str,
        namespace: str | None = None,
        mod: OpenMaya.MDGModifier | None = None,
    ) -> DGNode:
        """
        Function that builds the node within the Maya scene.

        :param name: name of the new node.
        :param node_type: Maya node type to create.
        :param namespace: optional node namespace.
        :param mod: optional Maya modifier to add to.
        :return: newly created meta node instance.
        """

        name = namespace + name.split(":")[-1] if namespace else name
        self.setObject(factory.create_dg_node(name, node_type=node_type, mod=mod))
        return self

    def exists(self) -> bool:
        """
        Returns whether the node is currently valid within the Maya scene.

        :return: True if the node is valid; False otherwise.
        """

        handle = self._handle
        return False if handle is None else handle.isValid() and handle.isAlive()

    def handle(self) -> OpenMaya.MObjectHandle:
        """
        Returns the MObjectHandle of the node.

        :return: MObjectHandle of the node.
        .warning:: Developer is responsible for checking if the node exists before calling this method.
        """

        return self._handle

    def mfn(self) -> OpenMaya.MFnDagNode | OpenMaya.MFnDependencyNode:
        """
        Returns the function set for this node.

        :return: function set for this node.
        """

        if self._mfn is None and self._handle is not None:
            self._mfn = self.MFN_TYPE(self.object())

        return self._mfn

    def typeId(self) -> OpenMaya.MTypeId | None:
        """
        Returns the Maya type id of the node.

        :return: type id of the node.
        """

        return self._mfn.typeId if self.exists() else None

    def hasFn(self, fn_Type: OpenMaya.MFn) -> bool:
        """
        Returns whether the node has the given function set.

        :param fn_Type: function set to check.
        :return: True if the node has the given function set; False otherwise.
        """

        return self.object().hasFn(fn_Type)

    def apiType(self) -> OpenMaya.MFn:
        """
        Returns the API type of the node.

        :return: API type of the node.
        """

        mobj = self.object()
        return mobj.apiType() if mobj is not None else None

    def object(self) -> OpenMaya.MObject | None:
        """
        Returns the Maya object of the node.

        :return: Maya object.
        """

        return self._handle.object() if self.exists() else None

    def setObject(self, mobj: OpenMaya.MObject | OpenMaya.MDagPath):
        """
        Sets the Maya object of the node.

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
        """
        Returns the node name.

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
        """
        Returns the node scene name, this result is dependent on the arguments.

        :param partial_name: whether to return the partial name of the node.
        :param include_namespace: whether to include the namespace.
        :return: node full path name.
        :raises RuntimeError: if the node wrapped within this instance does not exist.
        """

        if not self.exists():
            raise RuntimeError("Current node does not exists!")

        return nodes.name(self.object(), partial_name, include_namespace)

    def isReferenced(self) -> bool:
        """
        Returns whether the node is referenced.

        :return: True if node is referenced; False otherwise.
        """

        return self.mfn().isFromReferencedFile

    def isDefaultNode(self) -> bool:
        """
        Returns whether this node is a default Maya node.

        :return: True if this node is a default Maya node; False otherwise.
        """

        return self.mfn().isDefaultNode

    @lock_node_context
    def rename(self, new_name, maintain_namespace=False, mod=None, apply=True) -> bool:
        """
        Renames this node.

        :param new_name: new node name.
        :param maintain_namespace: whether to maintain current namespace.
        :param mod: modifier to add rename operation to.
        :param apply: whether to rename node immediately using the modifier.
        :return: True if the rename operation was successful; False otherwise.
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

    def namespace(self):
        """
        Returns the current namespace for the node.

        :return: node namespace.
        :rtype: str
        """

        name = OpenMaya.MNamespace.getNamespaceFromName(self.fullPathName()).split("|")[
            -1
        ]
        root = OpenMaya.MNamespace.rootNamespace()
        if not name.startswith(root):
            name = root + name

        return name

    def parentNamespace(self):
        """
        Returns the parent namespace from the node.

        :return: parent namespace.
        :rtype: str
        """

        namespace = self.namespace()
        if namespace == ":":
            return namespace

        OpenMaya.MNamespace.setCurrentNamespace(namespace)
        parent = OpenMaya.MNamespace.parentNamespace()
        OpenMaya.MNamespace.setCurrentNamespace(namespace)

        return parent

    def renameNamespace(self, namespace: str):
        """
        Renames the current namespace with the given one.

        :param str namespace: new namespace.
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

    def removeNamespace(self, mod=None, apply=True):
        """
        Deletes the namespace from this node.

        :param DGModifier mod: optional Maya modifier to apply; if None, one will be created.
        :param bool apply: whether to apply modifier immediately.
        :return: True if the remove namespace operation was successful; False otherwise.
        :rtype: bool
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
        self, state: bool, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> OpenMaya.MDGModifier:
        """
        Sets the lock state for this node.

        :param bool state: lock state to change to.
        :param OpenMaya.MDGModifier mod: optional Maya modifier to apply; if None, one will be created.
        :param bool apply: whether to apply modifier immediately.
        :return: created Maya modifier.
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
        """
        Returns whether the attribute given name exist on this node.

        :param attribute_name: name of the attribute to check.
        :return: True if the given attribute exists on the node; False otherwise.
        """

        # arrays don't get picked up by hasAttribute.
        if "[" in attribute_name:
            sel = OpenMaya.MSelectionList()
            try:
                sel.add(attribute_name)
                return True
            except RuntimeError:
                return False
        return self.mfn().hasAttribute(attribute_name)

    def attribute(self, name: str) -> Plug | None:
        """
        Returns the attribute with the given name this node.

        :param name: name of the attribute to find.
        :return: found plug instance or None.
        """

        fn = self._mfn
        if any(i in name for i in ("[", ".")):
            sel = OpenMaya.MSelectionList()
            try:
                sel.add(".".join((self.fullPathName(), name)))
                mplug = sel.getPlug(0)
            except RuntimeError:
                # raised when the plug does not exist.
                return None
            return Plug(self, mplug)
        elif fn.hasAttribute(name):
            return Plug(self, fn.findPlug(name, False))

    def setAttribute(
        self,
        name: str,
        value: Any,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> bool:
        """
        Sets the value of the attribute if it exists.

        :param name: name of the attribute to set value of.
        :param value: value of the attribute to set.
        :param mod: modifier to add set attribute value operation into.
        :param apply: whether to apply the modifier immediately.
        :return: True if the attribute set value operation was successful; False otherwise.
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
        """
        Adds an attribute into this node.

        :param name: name of the attribute to add.
        :param type: type of the attribute to add.
        :param mod: optional modifier to add.
        :return: newly created plug.
        """

        if self.hasAttribute(name):
            return self.attribute(name)

        children = kwargs.get("children")
        if children:
            plug = self.addCompoundAttribute(name, attr_map=children, mod=mod, **kwargs)
        else:
            mobj = self.object()
            attr = nodes.add_attribute(mobj, name, name, type=type, mod=mod, **kwargs)
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
        """
        Creates a compound attribute with the given children attributes.

        :param name: name of the compound attribute to add.
        :param attr_map: [{"name":str, "type": attributetypes.kType, "isArray": bool}]
        :param isArray: whether to add the compound attribute as an array.
        :param mod: modifier to add.
        :return: newly created compound plug.
        """

        mobj = self.object()
        compound = nodes.add_compound_attribute(
            mobj, name, name, attr_map, isArray=isArray, mod=mod, **kwargs
        )
        return Plug(self, OpenMaya.MPlug(mobj, compound.object()))

    @lock_node_context
    def addProxyAttribute(self, source_plug: Plug, name: str) -> Plug | None:
        """
        Creates a proxy attribute where the created plug on this node will be connected to the source plug while still
        being modifiable.

        :param source_plug: plug to copy to the current node which whill become the primary attribute.
        :param name: name for the proxy attribute, if the attribute already exists then no proxy will happen.
        :return: proxy plug instance.
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
        """
        Creates an attribute on the node based on the attribute data in the following form:
        {
            "channelBox": true,
            "default": 3,
            "isDynamic": true,
            "keyable": false,
            "locked": false,
            "max": 9999,
            "min": 1,
            "name": "jointCount",
            "softMax": null,
            "softMin": null,
            "type": 2,
            "value": 3
        }

        :param data: serialized attribute data.
        :param mod: optional modifier to add.
        :return: list of created plugs.
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
                    mobj, name, name, attr_data.pop("type", None), mod=mod, **attr_data
                )
                created_plugs.append(Plug(self, OpenMaya.MPlug(mobj, attr.object())))

        return created_plugs

    def renameAttribute(self, name: str, new_name: str) -> bool:
        """
        Renames an attribute on the current node.

        :param name: name of the attribute to rename.
        :param new_name: new attribute name.
        :return: True if the rename attribute operation was successful; False otherwise.
        :raises AttributeError: if the attribute to rename does not exist.
        """

        try:
            plug = self.attribute(name)
        except RuntimeError:
            raise AttributeError(f"No attribute named: {name}")

        return plug.rename(new_name)

    def deleteAttribute(
        self, attribute_name: str, mod: OpenMaya.MDGModifier | None = None
    ) -> bool:
        """
        Removes the attribute with given name from this node.

        :param attribute_name: attribute name to delete.
        :param mod: optional Maya modifier to add to.
        :return: True if the attribute was deleted successfully; False otherwise.
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
        """
        Connects the attribute on this node with given name as the source to the destination plug.

        :param attribute_name: name of the attribute that will be used as the source.
        :param destination_plug: destination plug.
        :param mod: optional modifier to add.
        :param apply: whether to apply the operation immediately.
        :return: MDGModifier instance if the connection was successful; None otherwise.
        """

        source = self.attribute(attribute_name)
        if source is not None:
            return source.connect(destination_plug, mod=mod, apply=apply)

        return None

    def iterateConnections(
        self, source: bool = True, destination: bool = True
    ) -> Iterator[tuple[Plug, Plug], ...]:
        """
        Generator function that iterates over node connections.

        :param source: whether to iterate source connections.
        :param destination: whether to iterate destination connections.
        :return: generator with the first element is the plug instance and the second the connected plug.
        """

        for source_plug, destination_plug in nodes.iterate_connections(
            self.object(), source, destination
        ):
            yield (
                Plug(self, source_plug),
                Plug(node_by_object(destination_plug.node()), destination_plug),
            )

    def sources(self) -> Iterator[tuple[Plug, Plug], ...]:
        """
        Generator function that iterates over source plugs.

        :return: generator with the first element is the plug instance and the second the connected plug.
        """

        for source, destination in nodes.iterate_connections(
            self.object(), source=True, destination=False
        ):
            yield Plug(self, source), Plug(self, destination)

    def destinations(self) -> Iterator[tuple[Plug, Plug], ...]:
        """
        Generator function that iterates over destination plugs.

        :return: generator with the first element is the plug instance and the second the connected plug.
        """

        for source, destination in nodes.iterate_connections(
            self.object(), source=False, destination=True
        ):
            yield Plug(self, source), Plug(self, destination)

    @staticmethod
    def sourceNode(plug: Plug) -> DGNode | DagNode | None:
        """
        Helper function that returns the source node of the given plug.

        :param plug: plug to return source node of.
        :return: either the source node or None if the plug is not connected to any node.
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
        """
        Returns the source node connected to the given plug of this node instance.

        :param str plug_name: name of the plug to return source node of.
        :return: source node connected to the plug.
        :rtype: DGNode or DagNode or None
        """

        plug = self.attribute(plug_name)
        return self.sourceNode(plug) if plug is not None else None

    def setLockStateOnAttributes(
        self, attributes: Iterable[str], state: bool = True
    ) -> bool:
        """
        Locks/unlocks the given attributes.

        :param attributes: list of attributes to lock/unlock.
        :param state: whether to lock or unlock the attributes.
        :return: True if the lock/unlock operation was successful; False otherwise.
        """

        return nodes.set_lock_state_on_attributes(
            self.object(), attributes, state=state
        )

    def showHideAttributes(
        self, attributes: Iterable[str], state: bool = False
    ) -> bool:
        """
        Shows or hides given attributes in the channel box.

        :param attributes: list of attributes names to lock/unlock
        :param state: whether to hide or show the attributes.
        :return: True if the attributes show/hide operation was successful; False otherwise.
        """

        fn = self._mfn
        for attr in attributes:
            plug = fn.findPlug(attr, False)
            plug.isChannelBox = state
            plug.isKeyable = state

        return True

    def findAttributes(self, *names) -> list[Plug | None]:
        """
        Searches the node for each attribute name given and returns the plug instance.

        :param names: list of attribute names.
        :return: each element matching plug or None if not found.
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
        """
        Generator function that iterates over all the attributes on this node.

        :return: generator of iterated attributes.
        """

        for attr in nodes.iterate_attributes(self.object()):
            yield Plug(self, attr)

    def iterateExtraAttributes(
        self,
        skip: Iterable[str] | None = None,
        filtered_types: Iterable[str] | None = None,
        include_attributes: Iterable[str] | None = None,
    ) -> Iterator[Plug]:
        """
        Generator function that iterates over all the extra attributes on this node.

        :param skip: list of attributes to skip.
        :param filtered_types: optional list of types we want to filter.
        :param include_attributes: list of attributes to force iteration over.
        :return: generator of iterated extra attributes.
        """

        for attr in nodes.iterate_extra_attributes(
            self.object(),
            skip=skip,
            filtered_types=filtered_types,
            include_attributes=include_attributes,
        ):
            yield Plug(self, attr)

    def iterateProxyAttributes(self) -> Iterator[Plug]:
        """
        Generator function that iterates over all the proxy attributes on this node.

        :return: generator of iterated proxy attributes.
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
        """
        Serializes current node into a dictionary compatible with JSON.

        :param skip_attributes: list of attributes names to serialize.
        :param include_connections: whether to find and serialize all connections where the destination is this node.
        :param extra_attributes_only: whether to serialize only the extra attributes of this node.
        :param use_short_names: whether to use short names to serialize node data.
        :param include_namespace: whether to include the namespace as part of node.
        :return: JSON compatible dictionary.
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
        """
        Deletes the node from the scene.

        :param mod: modifier to add the delete operation into.
        :param apply: whether to apply the modifier immediately.
        :return: True if the node deletion was successful; False otherwise.
        :raises RuntimeError: if deletion operation fails.
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
            logger.error(f"Failed node deletion, {self.mfn().name()}", exc_info=True)
            raise


# noinspection PyPep8Naming
class DagNode(DGNode):
    """
    Wrapper class for the Maya DAG nodes.
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
        """
        Function that builds the node within the Maya scene.

        :param name: name of the new node.
        :param node_type: Maya node type to create.
        :param parent: optional parent node to attach to.
        :param namespace: optional node namespace.
        :param mod: optional Maya modifier to add to.
        :return: newly created meta node instance.
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
        """
        Serializes current node into a dictionary compatible with JSON.

        :param skip_attributes: list of attributes names to serialize.
        :param include_connections: whether to find and serialize all connections where the destination is this node.
        :param include_attributes: list of attributes to serialize.
        :param extra_attributes_only: whether to serialize only the extra attributes of this node.
        :param use_short_names: whether to use short names to serialize node data.
        :param include_namespace: whether to include the namespace as part of node.
        :return: JSON compatible dictionary.
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
                f"Something went wrong while deserializing node: {err}", exc_info=True
            )
            return {}

    def parent(self):
        """
        Returns the parent node as an MObject

        :return: parent Maya object.
        :rtype: DagNode or None
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
        """
        Sets the parent of this node.

        :param parent: new parent node.
        :param maintain_offset: whether to maintain it is current position in world space.
        :param mod: optional modifier to add.
        :param apply: whether to apply the modifier immediately.
        :return: Maya modifier used to set parent.
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
        """
        Returns the MDagPath of this node.

        :return: DAG path for this node.
        """

        return self.mfn().getPath()

    def depth(self) -> int:
        """
        Returns the depth level this node sits within the hierarchy.

        :return: hierarchy depth level.
        """

        return self.fullPathName().count("|") - 1

    def root(self) -> DagNode:
        """
        Returns the root dag node parent from this node instance.

        :return: root node.
        """

        return node_by_object(dagutils.root(self.object()))

    def boundingBox(self) -> OpenMaya.MBoundingBox:
        """
        Returns the bounding box information for this node.

        :return: bounding box information.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnDagNode = self._mfn
        return mfn.boundingBox

    def iterateShapes(self) -> Iterator[DagNode]:
        """
        Generator function that iterates over all shape nodes under this dag node instance.

        :return: iterated shape nodes.
        """

        path = self.dagPath()
        for i in range(path.numberOfShapesDirectlyBelow()):
            dag_path = OpenMaya.MDagPath(path)
            dag_path.extendToShape(i)
            yield node_by_object(dag_path.node())

    def shapes(self) -> list[DagNode]:
        """
        Returns a list of all shape nodes under this dag node instance.

        :return: list of shape nodes.
        """

        return list(self.iterateShapes())

    def setShapeColor(
        self, color: Iterable[float, float, float], shape_index: int | None = None
    ):
        """
        Sets the color of this node transform or the node shape.

        :param color: RGB color to set.
        :param shape_index: shape index to set. If None, then the transform color will be set. -1 will
            set the color of all shapes.
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
        """
        Deletes all shape nodes on this node.
        """

        for shape in self.shapes():
            shape.delete()

    def child(self, index: int, node_types: tuple[int] = ()) -> DagNode:
        """
        Returns the immediate child object based on given index.

        :param index: index of the child to find.
        :param node_types: node types to get child of.
        :return: found child.
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

    def addChild(self, node: DagNode):
        """
        Re-parent given node to this node.

        :param node: child node to re-parent to this node.
        """

        node.setParent(self)

    def iterateParents(self) -> Iterator[DagNode]:
        """
        Ggenerator function that iterates over each parent until root has been reached.

        :return: iterated parent nodes.
        """

        for parent in dagutils.iterate_parents(self.object()):
            yield node_by_object(parent)

    def iterateChildren(
        self,
        node: DagNode | None = None,
        recursive: bool = True,
        node_types: Iterable[int] | None = None,
    ) -> Iterator[DagNode]:
        """
        Generator function that iterates over each child of this node.

        :param node: optional node to iterate children of.
        :param recursive: whether to recursively loop all children of children.
        :param node_types: list of node types.
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
                    node_by_object(child), recursive=recursive, node_types=node_types
                ):
                    yield _child

    def children(self, node_types: tuple[int, ...] = ()) -> list[DagNode]:
        """
        Returns all immediate children objects.

        :param node_types: node types to get children of.
        :return: found children.
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
        """
        Generator function that iterates over all sibling nodes of this node.

        :param node_types: list of node types to filter.
        :return: iterated sibling nodes.
        """

        parent = self.parent()
        if parent is None:
            return
        for child in parent.iterateChildren(recursive=False, node_types=node_types):
            if child != self:
                yield child

    def translation(
        self, space: OpenMaya.MSpace | None = None, scene_units: bool = False
    ) -> OpenMaya.MVector:
        """
        Returns the translation for this node.

        :param space: coordinate system to use.
        :param scene_units: whether the translation vector needs to be converted to scene units.
        :return: object translation.
        """

        space = space or OpenMaya.MSpace.kWorld
        return nodes.translation(self.object(), space, scene_units=scene_units)

    def setTranslation(
        self,
        translation: OpenMaya.MVector | Iterable[float, float, float],
        space: OpenMaya.MSpace | None = None,
        scene_units: bool = False,
    ):
        """
        Sets the translation component of this node.

        :param translation: vector that represents a position in space.
        :param space: space to work.
        :param scene_units: whether the translation vector needs to be converted to scene units.
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
        """
        Returns the rotation for this node.

        :param space: coordinate system to use.
        :param as_quaternion: whether to return rotation as a quaternion.
        :return: Maya object rotation.
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
        | Iterable[float, float, float],
        space: OpenMaya.MSpace | None = None,
    ):
        """
        Sets the translation component of this node.

        :param tuple or list or OpenMaya.MEulerAngle or OpenMaya.MQuaternion rotation: rotation to set.
        :param int space: space to work.
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
        """
        Returns the scale for this node.

        :param space: coordinate system to use.
        :return: object scale.
        """

        space = space or OpenMaya.MSpace.kTransform
        transform = self.transformationMatrix(space)
        return OpenMaya.MVector(transform.scale(space))

    def setScale(self, scale: OpenMaya.MVector | Iterable[float, float, float]):
        """
        Sets the scale for this node.

        :param scale: scale to set.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnDagNode = self._mfn
        transform = OpenMaya.MFnTransform(mfn.getPath())
        transform.setScale(scale)

    def rotationOrder(self) -> int:
        """
        Returns the rotation order for this node.

        :return: rotation order index.
        """

        return self.rotateOrder.value()

    def setRotationOrder(
        self, rotate_order: int = constants.kRotateOrder_XYZ, preserve: bool = True
    ):
        """
        Sets rotation order for this node.

        :param rotate_order: rotate order index (defaults to XYZ).
        :param preserve: If True, X, Y, Z rotations will be modified so that the resulting rotation under the new
            order is the same as it was under the old. If False, then X, Y, Z rotations are unchanged.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnDagNode = self._mfn
        rotate_order = constants.kRotateOrders.get(rotate_order, -1)
        transform = OpenMaya.MFnTransform(mfn.getPath())
        transform.setRotationOrder(rotate_order, preserve)

    def worldMatrix(
        self, context: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
    ) -> OpenMaya.MMatrix:
        """
        Returns the world matrix of this node.

        :param context: optional context to use.
        :return: world matrix.
        """

        world_matrix = self._mfn.findPlug("worldMatrix", False).elementByLogicalIndex(0)
        return OpenMaya.MFnMatrixData(world_matrix.asMObject(context)).matrix()

    def setWorldMatrix(self, matrix: OpenMaya.MMatrix):
        """
        Sets the world matrix of this node.

        :param matrix: world matrix to set.
        """

        nodes.set_matrix(self.object(), matrix, space=OpenMaya.MSpace.kWorld)

    def matrix(self, context: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal):
        """
        Returns the local matrix of this node.

        :param context: optional context to use.
        :return: local matrix.
        """

        local_matrix = self._mfn.findPlug("matrix", False)
        return OpenMaya.MFnMatrixData(local_matrix.asMObject(context)).matrix()

    def setMatrix(self, matrix: OpenMaya.MMatrix):
        """
        Sets the local matrix of this node.

        :param matrix: local matrix to set.
        """

        nodes.set_matrix(self.object(), matrix, space=OpenMaya.MSpace.kTransform)

    def transformationMatrix(
        self,
        rotate_order: int | None = None,
        space: OpenMaya.MSpace | None = OpenMaya.MSpace.kWorld,
    ) -> OpenMaya.MTransformationMatrix:
        """
        Returns the current node matrix in the form of MTransformationMatrix.

        :param rotate_order: rotation order to use.
        :param space: coordinate space to use.
        :return: Maya transformation matrix instance.
        """

        transform = OpenMaya.MTransformationMatrix(
            self.worldMatrix() if space == OpenMaya.MSpace.kWorld else self.matrix()
        )
        rotate_order = self.rotationOrder() if rotate_order is None else rotate_order
        rotate_order = constants.kRotateOrders.get(rotate_order, -1)
        transform.reorderRotation(rotate_order)

        return transform

    def parentInverseMatrix(
        self, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
    ) -> OpenMaya.MMatrix:
        """
        Returns the current node parent inverse matrix.

        :param ctx: context to use.
        :return: parent inverse matrix.
        """

        return nodes.parent_inverse_matrix(self.object(), ctx=ctx)

    def worldMatrixPlug(self, index: int = 0) -> Plug:
        """
        Returns the world matrix plug for this node.

        :param index: index of the world matrix plug.
        :return: world matrix plug.
        """

        return Plug(
            self, self._mfn.findPlug("worldMatrix", False).elementByLogicalIndex(index)
        )

    def worldInverseMatrixPlug(self, index: int = 0) -> Plug:
        """
        Returns the world inverse matrix plug for this node.

        :param index: index of the world inverse matrix plug.
        :return: world inverse matrix plug.
        """

        return Plug(
            self,
            self._mfn.findPlug("worldInverseMatrix", False).elementByLogicalIndex(
                index
            ),
        )

    def offsetMatrix(
        self,
        target_node: DagNode,
        space: OpenMaya.MSpace = OpenMaya.MSpace.kWorld,
        ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal,
    ) -> OpenMaya.MMatrix:
        """
        Returns the offset matrix between this node and the given target node.

        :param target_node: target transform node.
        :param space: coordinate space.
        :param ctx: context to use.
        :return: parent inverse matrix.
        """

        return nodes.offset_matrix(
            self.object(), target_node.object(), space=space, ctx=ctx
        )

    def decompose(
        self, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal
    ) -> tuple[OpenMaya.MVector, OpenMaya.MVector, OpenMaya.MVector]:
        """
        Returns the world matrix decomposed for this node.

        :param ctx: context to use.
        :return: tuple with the world translation, rotation and scale of this node.
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
        """
        Resets the local translate, rotate and scale attributes to 0.0.

        :param translate: whether to reset translate attributes.
        :param rotate: whether to reset rotate attributes.
        :param scale: whether to reset scale attributes.
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
            self.setRotation(OpenMaya.MQuaternion(), space=OpenMaya.MSpace.kTransform)
        if (
            scale
            and not scale_attr.isDestination
            and scale_attr.numConnectedChildren() == 0
        ):
            self.setScale((1.0, 1.0, 1.0))

    def resetTransformToOffsetParent(self):
        """
        Resets the local translate, rotate and scale attributes to the offset parent matrix.
        """

        parent = self.parent()
        world_matrix = self.worldMatrix()
        parent_inverse_matrix = (
            parent.worldMatrix().inverse() if parent is not None else OpenMaya.MMatrix()
        )
        self.attribute("offsetParentMatrix").set(world_matrix * parent_inverse_matrix)
        self.resetTransform()

    def isHidden(self) -> bool:
        """
        Returns whether this node is visible.

        :return: True if this node is visible; False otherwise.
        """

        return not self._mfn.findPlug("visibility", False).asBool()

    def setVisible(
        self,
        flag: bool,
        mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
        apply: bool = True,
    ) -> bool:
        """
        Sets whether this node is visible.

        :param flag: True to make this node visible; False to hide it.
        :param mod: optional modifier to use to set the visibility this node.
        :param apply: whether to apply the operation immediately.
        :return: True if the set visibility operation was successful; False otherwise.
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

    def show(self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True) -> bool:
        """
        Sets the visibility for this node to 1.0.

        :param mod: optional modifier to use to show this node.
        :param apply: whether to apply the operation immediately.
        :return: True if node was showed successfully; False otherwise.
        """

        return self.setVisible(True, mod=mod, apply=apply)

    def hide(self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True):
        """
        Sets the visibility for this node to 0.0.

        :param mod: optional modifier to use to hide this node.
        :param apply: whether to apply the operation immediately.
        :return: True if node was hidden successfully; False otherwise.
        """

        return self.setVisible(False, mod=mod, apply=apply)


# noinspection PyPep8Naming
class Plug:
    """
    Wrapper class for OpenMaya.MPlug that provides an easier solution to access connections and values.
    """

    def __init__(self, node: DGNode | DagNode, mplug: OpenMaya.MPlug):
        """
        Plug constructor.

        :param node: node instance for this plug.
        :param mplug: Maya plug instance.
        """

        self._node = node
        self._mplug = mplug

    def __repr__(self) -> str:
        """
        Overrides __repr__ function to return the display string for this plug instance.

        :return: display string.
        """

        return (
            f"<{self.__class__.__name__}> {self._mplug.name()}" if self.exists() else ""
        )

    def __str__(self) -> str:
        """
        Overrides __str__ function to return the full path name for this instance.

        :return: full path name.
        """

        return "" if not self.exists() else self._mplug.name()

    def __eq__(self, other: Plug) -> bool:
        """
        Overrides __eq__ function to compare the internal plug with the given one.

        :param other: plug instance.
        :return: True if both plugs are the same; False otherwise.
        """

        return self._mplug == other.plug()

    def __ne__(self, other: Plug) -> bool:
        """
        Overrides __ne__ function to compare the internal plug with the given one.

        :param other: plug instance.
        :return: True if plugs are different; False otherwise.
        """

        return self._mplug != other.plug()

    def __abs__(self):
        """
        Overrides __abs__ function to return the absolute value of a plug.

        :return: absolute value of the plug.
        :rtype: any
        """

        return abs(self.value())

    def __int__(self) -> int:
        """
        Overrides __int__ function to return the value of the plug as an integer.

        :return: plug value as an integer.
        """

        return self._mplug.asInt()

    def __float__(self) -> float:
        """
        Overrides __float__ function to return the value of the plug as a float.

        :return: plug value as a float.
        """

        return self._mplug.asFloat()

    def __neg__(self) -> Any:
        """
        Overrides __neg__ function to return the negative value of the plug.

        :return: plug negative value.
        """

        return -self.value()

    def __bool__(self) -> bool:
        """
        Overrides __bool__ function to return True if the plug exists.

        :return: True if the plug exists; False otherwise.
        """

        return self.exists()

    def __getitem__(self, item: int) -> Plug | None:
        """
        Overrides __getitem__ function to return the child attribute if this plug is a compound one.
        Index starts from 0.

        :param item: element or child index to get.
        :return: child plug found.
        :raises TypeError: if attribute does not support indexing.
        """

        if self._mplug.isArray:
            return self.element(item)
        if self._mplug.isCompound:
            return self.child(item)

        raise TypeError(f"{self._mplug.name()} does not support indexing")

    def __getattr__(self, item: str) -> Any:
        """
        Overrides __getattr__ function to try to access OpenMaya.MPlug attribute before accessing this instance
        attribute.

        :param item: name of the attribute to access.
        :return: attribute value.
        """

        if hasattr(self._mplug, item):
            return getattr(self._mplug, item)

        return super().__getattribute__(item)

    def __setattr__(self, key: str, value: Any):
        """
        Overrides __setattr__ function to try to call OpenMaya.MPlug function before calling the function.
        If a Plug instance is passed, given plug will be connected into this plug instance.

        :param key: name of the attribute to set.
        :param value: value of the attribute.
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
        """
        Overrides __iter__ function that allow the iteration of all the compound plugs.

        :return: generator of iterated compound plugs.
        """

        mplug = self._mplug
        if mplug.isArray:
            indices = mplug.getExistingArrayAttributeIndices()
            # case in maya 2023 where num of indices is zero but 2022 is [0]
            # for consistency and because 0 is usually a valid logical index to bind to(connection,setattr)
            for i in indices or [0]:
                yield Plug(self._node, mplug.elementByLogicalIndex(i))
        elif mplug.isCompound:
            for i in range(mplug.numChildren()):
                yield Plug(self._node, mplug.child(i))

    def __len__(self) -> int:
        """
        Overrides __len__ function to return the total number of attributes in compound or array attributes or 0
        if the attribute is not iterable.

        :return: total number of array or compound attributes.
        """

        if self._mplug.isArray:
            return self._mplug.evaluateNumElements()
        elif self._mplug.isCompound:
            return self._mplug.numChildren()

        return 0

    def __rshift__(self, other: Plug):
        """
        Overrides __rshift__ function to allow to connect this plug instance into a downstream plug.

        :param other: downstream plug to connect.
        """

        self.connect(other)

    def __lshift__(self, other: Plug):
        """
        Overrides __lshift__ function to connect this plug instance into an upstream plug.

        :param other: upstream plug to connect.
        """

        other.connect(self)

    def __floordiv__(self, other: Plug):
        """
        Overrides __floordiv__ function to allow to disconnect this plug from the given one.

        :param other: plug to disconnect from.
        """

        self.disconnect(other)

    def apiType(self):
        """
        Returns the Maya API type integer

        :return: Maya API type.
        :rtype: int
        """

        return plugs.plug_type(self._mplug)

    def mfn(self):
        """
        Returns the Maya function set for this plug.

        :return: Maya function set.
        :rtype: OpenMaya.MFnBase
        """

        attr = self._mplug.attribute()
        return plugs.plug_fn(attr)(attr)

    def mfnType(self):
        """
        Returns the Maya function set attribute type.

        :return: attribute type index.
        :rtype: int
        """

        return plugs.plug_fn(self._mplug.attribute())

    def exists(self) -> bool:
        """
        Returns whether this plug is valid.

        :return: True if plag is valid; False otherwise.
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
        """
        Returns the partial name for the plug.

        :param include_node_name: whether to include the node name.
        :param  include_non_mandatory_indices: whether to include non-mandatory indices.
        :param include_instanced_indices: whether to include instanced indices.
        :param use_alias: whether to use alias.
        :param use_full_attribute_path: whether to use full attribute path.
        :param use_long_names: whether to use long names.
        :return: plug partial name.
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
        """
        Returns the Maya MPlug object.

        :return: Maya MPlug object.
        """

        return self._mplug

    def node(self) -> DGNode | DagNode:
        """
        Returns the attached node API instance for this plug.

        :return: DGNode or DagNode for this plug.
        """

        return self._node

    def default(self) -> Any:
        """
        Returns the default value of this plug instance.

        :return: default plug value.
        """

        if not self.exists():
            return

        return plugs.plug_default(self._mplug)

    def setDefault(self, value: Any) -> bool:
        """
        Sets the default for this plug default instance.

        :param value: default value to set.
        :return: True if set default operation was successful; False otherwise.
        """

        return plugs.set_plug_default(self._mplug, value) if self.exists() else False

    def isProxy(self) -> bool:
        """
        Returns whether this plug is a proxy one.

        :return: True if plug is a proxy one; False otherwise.
        """

        return OpenMaya.MFnAttribute(self._mplug.attribute()).isProxyAttribute

    def setAsProxy(self, source_plug: Plug):
        """
        Sets the current attribute as a proxy attribute and connects to the given source plug.

        :param source_plug: source plug to connect this plug.
        """

        if self._mplug.isCompound:
            plugs.set_compound_as_proxy(self.plug(), source_plug.plug())
            return

        OpenMaya.MFnAttribute(self._mplug.attribute()).isProxyAttribute = True
        source_plug.connect(self)

    def isAnimated(self):
        """
        Returns whether current plug is animated.

        :return: True if current plug is animated; False otherwise.
        :rtype: bool
        :raises exception
        """

        if not self.exists():
            raise ObjectDoesNotExistError("Current Plug does not exist")

        return OpenMayaAnim.MAnimUtil.isAnimated(self._mplug)

    def findAnimation(self):
        """
        Returns the anim curve/s that are animating this plug instance.

        :return: list of animation curves.
        :rtype:
        """

        if not self.exists():
            raise ObjectDoesNotExistError("Current Plug does not exist")

        return [
            node_by_object(i) for i in OpenMayaAnim.MAnimUtil.findAnimation(self._mplug)
        ]

    def isFreeToChanged(self) -> bool:
        """
        Returns whether the plug is free to be changed.

        :return: True if the plug is free to be changed; False otherwise.
        """

        return self._mplug.isFreeToChange() == self._mplug.kFreeToChange

    def value(self, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal) -> Any:
        """
        Returns the value of the plug.

        :param ctx: context to use.
        :return: plug value.
        """

        value = plugs.plug_value(self._mplug, ctx=ctx)
        value = Plug._convert_value_type(value)

        return value

    def enumFields(self) -> list[str]:
        """
        Returns the list of field names for this enum plug.

        :return: list of field names.
        :raises InvalidPlugPathError: if the plug is not an enum type.
        """

        plug_type = self.apiType()
        if plug_type != attributetypes.kMFnkEnumAttribute:
            raise InvalidPlugPathError(
                f"Required type 'Enum', current type: {attributetypes.internal_type_to_string(plug_type)} for {self}"
            )

        return plugs.enum_names(self.plug())

    @lock_node_plug_context
    def addEnumFields(self, fields: list[str]):
        """
        Adds a list of field names to the plug.
        If a name already exists it will be skipped. New fields will always be added to the end.

        :param fields: list of field names to add.
        :return:
        """

        if self.node().isReferenced() and self.isLocked:
            raise ReferenceObjectError(f"Plug {self.name()} is a reference and locked")

        existing_field_names = self.enumFields()
        attr = OpenMaya.MFnEnumAttribute(self.attribute())
        index: int = 0
        for field in fields:
            if field in existing_field_names:
                continue
            attr.addField(field, len(existing_field_names) + index)
            index += 1

    def setFields(self, fields: list[str]):
        """
        Sets the list of fields for this plug.

        :param fields: list of fields to set for this plug.
        """

        default_value = self.default()
        try:
            cmds.addAttr(self.name(), edit=True, enumName=":".join(fields))
        except RuntimeError:
            raise InvalidPlugPathError(
                f"Required type 'Enum', current type: "
                f"{attributetypes.internal_type_to_string(self.apiType())} for {self}"
            )
        if default_value is not None and default_value < len(self.enumFields()):
            self.setDefault(default_value)

    def array(self) -> Plug:
        """
        Returns the plug array for this array element.

        :return: plug array.
        """

        assert self._mplug.isElement, f"Plug: {self.name()} is not an array element"
        return Plug(self._node, self._mplug.array())

    def parent(self) -> Plug:
        """
        Returns the parent plug if this plug is a compound.

        :return: parent plug.
        :rtype: Plug
        """

        assert self._mplug.isChild, f"Plug {self.name()} is not a child attribute"
        return Plug(self._node, self._mplug.parent())

    def children(self) -> list[Plug]:
        """
        Returns all the child plugs of this compound plug.

        :return: children plugs.
        :rtype: list(Plug)
        """

        return [
            Plug(self._node, self._mplug.child(i))
            for i in range(self._mplug.numChildren())
        ]

    def child(self, index) -> Plug:
        """
        Returns the child plug by index.

        :param index: child index.
        :return: child plug at given index.
        """

        assert self._mplug.isCompound, f"Plug: {self._mplug.name()} is not a compound"
        if index < 0:
            new_index = max(0, len(self) + index)
            return Plug(self._node, self._mplug.child(new_index))

        return Plug(self._node, self._mplug.child(index))

    def element(self, index: int) -> Plug:
        """
        Returns the logical element plug if this plug is an array.

        :param index: element index.
        :return: element plug.
        """

        assert self._mplug.isArray, f"Plug: {self._mplug.name()} is not an array"
        if index < 0:
            new_index = max(0, len(self) + index)
            return Plug(self._node, self._mplug.elementByLogicalIndex(new_index))

        return Plug(self._node, self._mplug.elementByLogicalIndex(index))

    def elementByPhysicalIndex(self, index: int) -> Plug:
        """
        Returns the element plug by the physical index if this plug is an array.

        :param index: physical index.
        :return: element plug.
        """

        assert self._mplug.isArray, f"Plug {self.name()} is not an array"
        return Plug(self._node, self._mplug.elementByPhysicalIndex(index))

    def nextAvailableElementPlug(self):
        """
        Returns the next available output plug for this array.

        :return:  next available output plug.
        :rtype: Plug
        .info: availability is based on connections of elements plug and their children.
        """

        assert self._mplug.isArray, f"Plug {self.name()} is not an array"
        return Plug(self._node, plugs.next_available_element_plug(self._mplug))

    def nextAvailableDestElementPlug(self, force: bool = False):
        """
        Returns the next available input plug for this array.

        :param force: whether to force the next available plug.
        :return:  next available input plug.
        .info: availability is based on connections of elements plug and their children.
        """

        assert self._mplug.isArray, f"Plug {self.name()} is not an array"
        return Plug(
            self._node, plugs.next_available_dest_element_plug(self._mplug, force=force)
        )

    @lock_node_plug_context
    def set(
        self, value: Any, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> OpenMaya.MDGModifier:
        """
        Sets the value of this plug instance.

        :param value: OpenMaya value type.
        :param mod: optional Maya modifier to add to.
        :param apply: whether to apply modifier immediately.
        :return: created Maya modifier.
        :raises exceptions.ReferenceObjectError: if the node is locked or is a reference.
        """

        if self.node().isReferenced() and self.isLocked:
            raise ReferenceObjectError(
                f"Plug {self.name()} is a reference or is locked"
            )

        return plugs.set_plug_value(self._mplug, value, mod=mod, apply=apply)

    @lock_node_plug_context
    def setFromDict(self, **plug_info):
        """
        Sets the plug value from a dictionary.

        :param plug_info: plug value dictionary.
        """

        return plugs.set_plug_info_from_dict(self._mplug, **plug_info)

    @lock_node_plug_context
    def connect(
        self,
        plug: Plug | OpenMaya.MPlug,
        children: list[Plug] = None,
        force: bool = True,
        mod: OpenMaya.MDGModifier | None = None,
        apply: bool = True,
    ) -> OpenMaya.MDGModifier:
        """
        Connects given plug to this plug instance.

        :param Plug or OpenMaya.MPlug plug: plug to connect into this plug.
        :param children: children attributes to connect
        :param force: whether to force the connection.
        :param mod: optional Maya modifier to add to.
        :param apply: whether to apply modifier immediately.
        :return: created Maya modifier.
        """

        if self.isCompound and children:
            children = children or []
            self_len = len(self)
            child_len = len(children)
            if children == 0:
                plugs.connect_plugs(self._mplug, plug.plug(), force=force, mod=mod)
            # noinspection PyTypeChecker
            if child_len > self_len:
                children = children[:self_len]
            elif child_len < self_len:
                children += [False] * (self_len - child_len)
            return plugs.connect_vector_plugs(
                self._mplug, plug.plug(), children, force=force, mod=mod, apply=apply
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
        """
        Disconnects given destination plug.

        :param plug: destination plug.
        :param mod: optional Maya modifier to add to.
        :param apply: whether to apply modifier immediately.
        :return: created Maya modifier.
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
        """
        Disconnects all plugs from the current plug.

        :param bool source: whether to disconnect source connections.
        :param bool destination: whether to disconnect destination connections.
        :param DGModifier or None mod: optional Maya modifier to add to.
        :return: tuple with the result and modifier used to apply the operation.
        """

        return plugs.disconnect_plug(
            self._mplug, source=source, destination=destination, modifier=mod
        )

    def source(self) -> Plug | None:
        """
        Returns the source plug from this plug or None if it is not connected to any node.

        :return: connected source node plug.
        """

        source = self._mplug.source()
        return (
            Plug(node_by_object(source.node()), source) if not source.isNull else None
        )

    def sourceNode(self) -> DGNode | DagNode | None:
        """
        Returns the source node from this plug or None if it is not connected to any node.

        :return: source node.
        """

        source = self.source()
        return source.node() if source is not None else None

    def destinations(self) -> Iterator[Plug]:
        """
        Generator function that iterates over all destination plugs connected to this plug instance.

        :return: iterated destination plugs.
        """

        for destination_plug in self._mplug.destinations():
            yield Plug(node_by_object(destination_plug.node()), destination_plug)

    def destinationNodes(self) -> Iterator[DGNode]:
        """
        Generator function that iterates over all destination nodes.

        :return: iterated destination nodes.
        """

        for destination_plug in self.destinations():
            yield destination_plug.node()

    @lock_node_plug_context
    def rename(self, name: str, mod: OpenMaya.MDGModifier | None = None) -> bool:
        """
        Renames the current plug.

        :param name: new plug name.
        :param mod: optional modifier to add to.
        :return: True if the rename operation was valid; False otherwise.
        """

        with plugs.set_locked_context(self._mplug):
            mod = mod or OpenMaya.MDGModifier()
            mod.renameAttribute(self.node().object(), self.attribute(), name, name)
            mod.doIt()

        return True

    def show(self):
        """
        Shows the attribute in the channel box and makes the attribute keyable.
        """

        self._mplug.isChannelBox = True

    def hide(self):
        """
        Hides the attribute from the channel box and makes the attribute non-keyable.
        """

        self._mplug.isChannelBox = False
        self._mplug.isKeyable = False

    def lock(self, flag):
        """
        Sets the current plug lock state.

        :param bool flag: True to lock current plug; False to unlock it.
        """

        self._mplug.isLocked = flag

    def lockAndHide(self):
        """
        Locks and hides the attribute.
        """

        self._mplug.isLocked = True
        self._mplug.isChannelBox = False
        self._mplug.isKeyable = False

    def setKeyable(self, flag):
        """
        Sets the keyable state of the attribute.

        :param bool flag: True to make the attribute keyable; False otherwise.
        """

        self._mplug.isKeyable = flag

    @lock_node_plug_context
    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> OpenMaya.MDGModifier:
        """
        Deletes the plug from the attached node. If batching is needed then use the modifier parameter to pass a
        DGModifier, once all operations are done, call modifier.doIt() function.

        :param mod: modifier to dad to. If None, one will be created.
        :param apply: if True, then plugs value will be set immediately with the modifier, if False, then is
            user is responsible to call modifier.doIt() function.
        :return: Maya DGModifier used for the operation.
        :raises exceptions.ReferenceObjectError: in the case where the plug is not dynamic and is referenced.
        """

        if not self.isDynamic and self.node().isReferenced():
            raise ReferenceObjectError(f"Plug {self.name()} is reference and locked")

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
        """
        Deletes all array elements from this plug.

        :param OpenMaya.DGModifier mod: modifier to dad to. If None, one will be created.
        :param bool apply: if True, then plugs value will be set immediately with the modifier, if False, then is
            user is responsible to call modifier.doIt() function.
        :return: Maya DGModifier used for the operation.
        :rtype: OpenMaya.MDGModifier
        :raises exceptions.ReferenceObjectError: in the case where the plug is not dynamic and is referenced.
        :raises TypeError: if plug is not an array.
        """

        if not self.isDynamic and self.node().isReferenced():
            raise ReferenceObjectError(f"Plug {self.name()} is reference and locked")
        if not self._mplug.isArray:
            raise TypeError("Invalid plug type to delete, must be of type Array")

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
        """
        Serializes current PLUG instance and returns a JSON compatible dictionary with the container data.

        :return: serialized plug data.
        """

        return plugs.serialize_plug(self._mplug) if self.exists() else {}

    @staticmethod
    def _convert_value_type(value: Any) -> Any:
        """
        Internal static method that converts given value to a valid value type.

        :param any value: value to convert.
        :return: converted value.
        :rtype: any
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
    pass


class Mesh(DagNode):
    pass


class Camera(DagNode):
    pass


class IkHandle(DagNode):
    """
    Wrapper class for Maya ikHandle nodes.
    """

    # Twist controls scene worldUpType enum value.
    SCENE_UP = 0
    # Twist controls object up worldUpType enum value.
    OBJECT_UP = 1
    # Twist controls object up start/end worldUpType enum value.
    OBJECT_UP_START_END = 2
    # Twist controls object rotation up worldUpType enum value.
    OBJECT_ROTATION_UP = 3
    # TWist controls object rotation up start/end worldUpType enum value.
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
    UP_CLOSET_Y = 2
    UP_POSITIVE_Z = 3
    UP_NEGATIVE_Z = 4
    UP_CLOSET_Z = 5
    UP_POSITIVE_X = 6
    UP_NEGATIVE_X = 7
    UP_CLOSET_X = 8

    @staticmethod
    def vector_to_forward_axis_enum(vec: Iterable[float, float, float]) -> int:
        """
        Returns forward axis index from given vector.
        The forward axis direction is determined by finding the axis with the largets magnitude in the vector.

        If the sum of the values in the vector is negative, the method will return the corresponding negative up axis
        value.Available up axis enum values are:
            - IkHandle.FORWARD_NEGATIVE_X: The negative X axis
            - IkHandle.FORWARD_NEGATIVE_Y: The negative Y axis
            - IkHandle.FORWARD_NEGATIVE_Z: The negative Z axis

        If the sum of the values in the vector is not negative, the method will return the axis index corresponding to
        the forward axis direction.

        The possible axis indexes are:
            - X AXIS: The X axis
            - Y AXIS: The Y axis
            - Z AXIS: The Z axis

        :param vec: vector.
        :return: forward axis index.
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
        """
        Returns up axis index from given vector.
        The up axis direction is determined by finding the axis with the largest magnitude in the vector.

        If the sum of the values in the vector is negative, the method will return the corresponding negative up axis
        value.Available up axis enum values are:
            - IkHandle.UP_NEGATIVE_X: The negative X axis
            - IkHandle.UP_POSITIVE_Y: The negative Y axis
            - IkHandle.UP_NEGATIVE_Z: The negative Z axis

        If the sum of the values in the vector is not negative, the method will return the axis index corresponding to
        the up axis direction.

        The possible axis indexes are:
            - X AXIS: The X axis
            - Y AXIS: The Y axis
            - Z AXIS: The Z axis

        :param vec: vector.
        :return: up axis index.
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
    """
    Wrapper class for Maya joints.
    """

    def create(
        self,
        **kwargs,
    ) -> Joint:
        """
        Function that builds the node within the Maya scene.

        :return: newly created meta node instance.
        """

        kwargs["type"] = "joint"
        kwargs["name"] = kwargs.get("name", "joint")
        kwargs["parent"] = kwargs.get("parent", None)
        joint, _ = nodes.deserialize_node(kwargs, parent=None, include_attributes=True)
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
        """
        Sets the parent of this node.

        :param parent: new parent node.
        :param maintain_offset: whether to maintain it is current position in world space.
        :param mod: optional modifier to add.
        :param apply: whether to apply the modifier immediately.
        :return: Maya modifier used to set parent.
        """

        rotation = self.rotation(space=OpenMaya.MSpace.kWorld)

        result = super().setParent(parent, maintain_offset=True)
        if parent is None:
            return result

        parent_quat = parent.rotation(OpenMaya.MSpace.kWorld, as_quaternion=True)
        new_rotation = rotation * parent_quat.inverse()
        self.attribute("jointOrient").set(new_rotation.asEulerRotation())
        self.setRotation((0.0, 0.0, 0.0), OpenMaya.MSpace.kTransform)
        if parent.apiType() == OpenMaya.MFn.kJoint:
            parent.attribute("scale").connect(self.inverseScale)

        return result


# noinspection PyPep8Naming
class ContainerAsset(DGNode):
    """
    Wrapper class for MFnContainerNode nodes providing a set of common methods.
    """

    MFN_TYPE = OpenMaya.MFnContainerNode

    # noinspection PyMethodOverriding
    def create(self, name: str):
        """
        Creates the MFnSet and sets this instance MObject to the new node.

        :param name: name for the asset container node.
        """

        container = factory.create_dg_node(name, "container")
        self.setObject(container)

        return self

    def serializeFromScene(self, *args, **kwargs) -> dict:
        """
        Serializes current asset container instance and returns a JSON compatible
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
        """
        Deletes the node from the scene.

        :param remove_container: If True, then the container will be deleted, otherwise
            only members will be removed.
        """

        container_name = self.fullPathName()
        self.lock(False)
        cmds.container(container_name, edit=True, removeContainer=remove_container)

    @property
    def blackBox(self):
        """
        Getter method that returns the current black box attribute value.

        :return: True if the contents of the container are public; False otherwise.
        """

        return self.attribute("blackBox").asBool()

    @blackBox.setter
    def blackBox(self, flag):
        """
        Setter method that sets current black box attribute value.

        :param flag: True if the contents of the container are not public; False
            otherwise.
        """

        mfn = self.mfn()
        if not mfn:
            return
        self.attribute("blackBox").set(flag)

    def isCurrent(self) -> bool:
        """
        Returns whether this current container is the current active container.

        :return: True if this container is the active one; False otherwise.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnContainerNode = self._mfn
        return mfn.isCurrent()

    def makeCurrent(self, value):
        """
        Sets this container to be the currently active.

        :param bool value: whether to make container currently active.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnContainerNode = self._mfn
        mfn.makeCurrent(value)

    @contextlib.contextmanager
    def makeCurrentContext(self, value: bool):
        """
        Context manager that sets this container to be the currently active.

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
        """
        Returns current members of this container instance.

        :return: list of member nodes.
        :rtype: list(DagNode)
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnContainerNode = self.mfn()
        return map(node_by_object, mfn.getMembers())

    def addNode(self, node_to_add: DGNode, force: bool = False) -> bool:
        """
        Adds the given node to the container without publishing it.

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
        """
        Adds the given nodes to the container without published them.

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
        """
        Returns all published attributes in this container.

        :return: list of published attributes.
        """

        results = cmds.container(self.fullPathName(), query=True, bindAttr=True)
        if not results:
            return []

        # cmds returns a flat list of attribute name, published name, so we chunk as pai
        return [plug_by_name(attr) for attr, _ in helpers.iterate_chunks(results, 2)]

    def publishAttribute(self, attribute: Plug):
        """
        Publishes the given attribute to the container.

        :param attribute: attribute to publish.
        """

        self.publishAttributes([attribute])

    def publishAttributes(self, attributes: Iterable[Plug]):
        """
        Publishes the given attributes to the container.

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
        """
        Unpublishes attribute with given name from this container.

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
        """
        Unpublish all attributes published in this container.
        """

        for published_attribute in self.publishedAttributes():
            self.unpublish_attribute(
                published_attribute.partialName(use_long_names=False)
            )

    def publishedNodes(self):
        """
        Returns list of published node in this container.

        :return: list of published nodes.
        :rtype: list(DGNode)
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnContainerNode = self.mfn()
        return [
            node_by_object(node[1])
            for node in mfn.getPublishedNodes(OpenMaya.MFnContainerNode.kGeneric)
            if not node[0].isNull()
        ]

    def publishNode(self, node_to_publish: DGNode):
        """
        Publishes the given node to the container.

        :param node_to_publish: node to publish.
        """

        container_name = self.fullPathName()
        node_name = node_to_publish.fullPathName()
        short_name = node_name.split("|")[-1].split(":")[-1]
        try:
            cmds.containerPublish(
                container_name, publishNode=[short_name, node_to_publish.mfn().typeName]
            )
        except RuntimeError:
            pass
        try:
            cmds.containerPublish(container_name, bindNode=[short_name, node_name])
        except RuntimeError:
            pass

    def publishNodes(self, nodes_to_publish: Iterable[DGNode]):
        """
        Publishes the given nodes to the container.

        :param nodes_to_publish: list of nodes to publish.
        """

        for i in iter(nodes_to_publish):
            self.publishNode(i)

    def publishNodeAsChildParentAnchor(self, node: DGNode):
        """
        Publishes the given node as a child parent anchor.

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
        """
        Unpublishes given node from the container.

        :param node: node to unpublish.
        """

        message_plug = node.attribute("message")
        container_name = self.fullPathName()
        for dest_plug in message_plug.destinations():
            node = dest_plug.node().object()
            if node.hasFn(OpenMaya.MFn.kContainer):
                parent_name = dest_plug.parent().partialName(use_alias=True)
                cmds.containerPublish(container_name, unbindNode=parent_name)
                cmds.containerPublish(container_name, unpublishNode=parent_name)
                break

    def removeUnboundAttributes(self):
        """
        Removes any unbound attributes from the container.
        """

        container_name = self.fullPathName()
        for unbound in (
            cmds.container(
                container_name, query=True, publishName=True, unbindAttr=True
            )
            or []
        ):
            cmds.container(container_name, edit=True, removeUnbound=unbound)

    def setParentAnchor(self, node: DagNode):
        """
        Sets the given node as a parent anchor to the container.

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
        """
        Sets the given node as a child anchor to the container.

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
        """
        Returns the child anchor node of this container.

        :return: child anchor node.
        """

        child = cmds.container(self.fullPathName(), query=True, publishAsChild=True)
        return node_by_name(child[1]) if child else None

    def parentAnchor(self) -> DGNode:
        """
        Returns the parent anchor node of this container.

        :return: parent anchor node.
        """

        parent = cmds.container(self.fullPathName(), query=True, publishAsParent=True)
        return node_by_name(parent[1]) if parent else None

    def subContainers(self) -> Iterator[ContainerAsset]:
        """
        Generator function that iterates over all sub containers.

        :return: iterated sub containers.
        """

        mfn: OpenMaya.MFnContainerNode = self._mfn
        return map(node_by_object, mfn.getSubcontainers())


# noinspection PyPep8Naming
class AnimCurve(DGNode):
    """
    Wrapper class for Maya animCurve nodes.
    """

    MFN_TYPE = OpenMayaAnim.MFnAnimCurve

    def setPrePostInfinity(
        self, pre: int, post: int, change: OpenMayaAnim.MAnimCurveChange | None = None
    ):
        """
        Sets the behaviour of the curve for the range occurring before the first key and after the last key.

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
        """
        Adds a set of new keys with the given corresponding values and tangent types at the given times.

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
    """
    Wrapper class for Maya object sets
    """

    MFN_TYPE = OpenMaya.MFnSet

    # noinspection PyMethodOverriding
    def create(
        self,
        name: str,
        mod: OpenMaya.MDGModifier | None = None,
        members: list[DGNode] | None = None,
    ) -> ObjectSet:
        """
        Creates the MFnSet and sets this instance MObject to the new node.

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
        """
        Returns whether given node is a member of this set.

        :param node: node to check for membership.
        :return: True if given node is a member of this set; False otherwise.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnSet = self._mfn
        return mfn.isMember(self.object()) if node.exists() else False

    def addMember(self, node: DGNode) -> bool:
        """
        Adds given node to the set.

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
            node.message.connect(self.dnSetMembers.nextAvailableDestElementPlug())

        return True

    def addMembers(self, new_members: list[DGNode]):
        """
        Adds a list of new objects into the set.

        :param list[DGNode] new_members: list of nodes to add as new members to this set.
        """

        for member in new_members:
            self.addMember(member)

    def members(self, flatten: bool = False) -> list[DGNode]:
        """
        Returns the members of this set as a list.

        :param bool flatten: whether all sets that exist inside this set will be expanded into a list of their contents.
        :return: a list of all members in the set.
        :rtype: list[DGNode]
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnSet = self._mfn
        return list(map(node_by_name, mfn.getMembers(flatten).getSelectionStrings()))

    def removeMember(self, member: DGNode):
        """
        Removes given item from the set.

        :param DGNode member: item to remove.
        """

        if member.exists():
            self.removeMembers([member])

    def removeMembers(self, members: list[DGNode]):
        """
        Removes items of the list from the set.

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
        """
        Removes all members from this set.
        """

        # noinspection PyTypeChecker
        mfn: OpenMaya.MFnSet = self._mfn
        mfn.clear()


class BlendShape(DGNode):
    pass


# noinspection PyPep8Naming
class DisplayLayer(DGNode):
    """
    Wrapper class for Maya display layers.
    """

    def addNodes(self, display_nodes: list[DagNode]):
        """
        Adds the given nodes to the display layer.

        :param display_nodes: nodes to add to the display layer.
        """

        draw_info_plug = self.drawInfo
        for display_node in display_nodes:
            draw_info_plug.connect(display_node.drawOverride)

    def addNode(self, node: DagNode):
        """
        Adds the given node to the display layer.

        :param node: node to add to the display layer.
        """

        self.drawInfo.connect(node.drawOverride)


class AnimLayer(DGNode):
    pass


class ObjectDoesNotExistError(Exception):
    """
    Raised anytime the current object is operated on and does not exist.
    """

    pass


class ReferenceObjectError(Exception):
    """
    Raised when an object is a reference and the requested operation is not allowed on a reference.
    """

    pass


class InvalidPlugPathError(Exception):
    """
    Custom exception raised when a plug path is not valid.
    """

    pass


class InvalidTypeForPlugError(Exception):
    """
    Custom exception raised when the given type is not valid for a plug.
    """

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
    """
    Returns the correct API node for the given MObject by wrapping the MObject within an API node instance.

    :param OpenMaya.MObject mobj: Maya object.
    :return: API node instance.
    :rtype: DGNode
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
    """
    Returns a DAG node instance based on the given node name (expecting a full path).

    :param node_name: Maya node name or object instance.
    :return: API node instance.
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


def nodes_by_names(node_names: Iterable[str]) -> list[DGNode | DagNode]:
    """
    Returns DAG node instances based on the given node names (expecting a full path).

    :param node_names: Maya node name.
    :return: API node instances.
    """

    for node_name in node_names:
        yield node_by_name(node_name)


def nodes_by_type_names(node_type_names: str | Iterable[str]) -> list[DGNode | DagNode]:
    """
    Returns node instances based on the given node type name.

    :param node_type_names: node types to retrieve.
    :return: list of node instances.
    """

    found_node_names = cmds.ls(type=node_type_names, long=True)
    for found_node_name in found_node_names:
        yield node_by_name(found_node_name)


def selected(filter_types: Iterable[int] | None = None) -> Iterable[DGNode | DagNode]:
    """
    Returns selected nodes in the scene.

    :param filter_types: node types to filter by.
    :return: selected nodes.
    """

    return map(node_by_object, scene.iterate_selected_nodes(filter_types))


def select(
    nodes_to_select: Iterable[DGNode | DagNode],
    mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
    apply: bool = True,
) -> OpenMaya.MDGModifier | OpenMaya.MDagModifier:
    """
    Select given nodes within current scene.

    :param nodes_to_select: nodes to select.
    :param mod: optional modifier to run the command in.
    :param apply: whether to apply the modifier immediately.
    :return: Maya modifier used for the operation.
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
    """
    Select given node names within current scene.

    :param names: node names to select.
    :param mod: optional modifier to run the command in.
    :param apply: whether to apply the modifier immediately.
    :return: Maya modifier used for the operation.
    """

    mod = mod or OpenMaya.MDGModifier()
    mod.pythonCommandToExecute(f"from maya import cmds; cmds.select({names})")
    if apply:
        mod.doIt()

    return mod


def clear_selection(
    mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None, apply: bool = True
) -> OpenMaya.MDGModifier | OpenMaya.MDagModifier:
    """
    Clears current selection.

    :param mod: modifier to run the command in.
    :param apply: whether to apply the modifier immediately.
    """

    mod = mod or OpenMaya.MDGModifier()
    mod.pythonCommandToExecute("from maya import cmds; cmds.select(clear=True)")
    if apply:
        mod.doIt()

    return mod


def plug_by_name(plug_path: str) -> Plug:
    """
    Returns the Plug instance for the given plug path.

    :param plug_path: full path to the plug.
    :return: plug instance matching the given plug path.
    :raises InvalidPlugPathError: if given plug path is not valid.
    """

    if "." not in plug_path:
        raise InvalidPlugPathError(plug_path)

    plug = plugs.as_mplug(plug_path)
    return Plug(node_by_object(plug.node()), plug)
