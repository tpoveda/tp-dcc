"""DAG-based metanode base class.

This module provides the MetaDagBase class which is a base class for
creating DAG-based metanodes (transforms, groups, etc.) that are visible
in the scene hierarchy.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import TYPE_CHECKING, Any

from loguru import logger

from maya.api import OpenMaya

from ..om import attributetypes
from ..wrapper import DagNode, DGNode, Plug
from .constants import (
    META_CHILDREN_ATTR_NAME,
    META_CLASS_ATTR_NAME,
    META_GUID_ATTR_NAME,
    META_PARENT_ATTR_NAME,
    META_TAG_ATTR_NAME,
    META_VERSION_ATTR_NAME,
)
from .factory import MetaFactory
from .registry import MetaRegistry

if TYPE_CHECKING:
    from .base import MetaBase


class MetaDagBase(DagNode, metaclass=MetaFactory):
    """Base class for creating DAG-based metanodes (transforms, groups, etc.).

    Unlike MetaBase which creates network nodes, MetaDagBase creates actual
    DAG nodes (transforms) that are visible in the scene hierarchy. This is
    useful for metanodes that need to:
    - Be parent of scene geometry
    - Have visual representation via shapes
    - Participate in the DAG hierarchy

    The node includes visual indicator shapes that can be customized by
    subclasses via the `shape_name` class attribute.

    Attributes:
        ID: Unique identifier for the metanode. `None` if not set.
        VERSION: Version string for the metanode class. Defaults to "1.0.0".
        DEFAULT_NAME: Default name used when creating a metanode instance.
        SHAPE_NAME: Name of the curve shape to load from the curves library.
            Set to None to skip shape creation.
        SHAPE_COLOR: Default RGB color for the visual indicator shape.
        _do_register: Whether this class should be registered in the registry.
    """

    ID: str | None = None
    VERSION: str = "1.0.0"
    DEFAULT_NAME: str | None = None
    SHAPE_NAME: str | None = None
    SHAPE_COLOR: tuple[float, float, float] = (0.5, 0.5, 0.5)
    _do_register: bool = True

    def __init__(
        self,
        node: DGNode | DagNode | OpenMaya.MObject | None = None,
        name: str | None = None,
        namespace: str | None = None,
        parent: DagNode | OpenMaya.MObject | None = None,
        init_defaults: bool = True,
        lock: bool = False,
        mod: OpenMaya.MDGModifier | None = None,
        *args,
        **kwargs,
    ):
        """Initialize a DAG-based metanode.

        Args:
            node: An existing node to wrap. If None, creates a new transform.
            name: Name for the new node.
            namespace: Optional namespace for the node.
            parent: Optional parent DAG node.
            init_defaults: Whether to initialize default meta attributes.
            lock: Whether to lock the node after creation.
            mod: Optional modifier for batched operations.
            *args: Additional positional arguments for setup().
            **kwargs: Additional keyword arguments for setup().
        """

        super().__init__(mobj=node)

        if node is None:
            self.create(
                name
                or self.DEFAULT_NAME
                or "_".join(
                    [
                        MetaRegistry.registry_name_for_class(self.__class__),
                        "meta",
                    ]
                ),
                node_type="transform",
                namespace=namespace,
                parent=parent.object()
                if isinstance(parent, DagNode)
                else parent,
                mod=mod,
            )

        if init_defaults and not self.isReferenced():
            if mod:
                mod.doIt()
            self._init_meta(mod=mod)

            if lock and not self.mfn().isLocked:
                self.lock(True, mod=mod)

        if node is None:
            self._create_visual_indicator()
            self.setup(*args, **kwargs)

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        return f"{self.as_str(name_only=True)} ({self.name()})"

    @classmethod
    def as_str(cls, name_only: bool = False) -> str:
        """Retrieve the class name or fully qualified class path as a string.

        Args:
            name_only: If True, returns only the class name.

        Returns:
            The class name or fully qualified class path.
        """

        meta_module = cls.__module__
        meta_name = cls.__name__
        if name_only:
            return meta_name
        return ".".join([meta_module, meta_name])

    @staticmethod
    def class_name_from_plug(
        node: DGNode | DagNode | MetaDagBase | OpenMaya.MObject,
    ) -> str:
        """Extract the class name from a node's meta class attribute.

        Args:
            node: The node to get the class name from.

        Returns:
            The class name string, or empty string if not found.
        """

        from .base import MetaBase

        if isinstance(node, (MetaBase, MetaDagBase)):
            return node.attribute(META_CLASS_ATTR_NAME).value()
        dep = OpenMaya.MFnDependencyNode(node)
        try:
            return dep.findPlug(META_CLASS_ATTR_NAME, False).asString()
        except RuntimeError:
            return ""

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete this metanode and disconnect all children.

        Args:
            mod: Optional modifier for batched operations.
            apply: Whether to apply immediately.

        Returns:
            True if deletion was successful.
        """

        child_plug = self.attribute(META_CHILDREN_ATTR_NAME)
        for element in child_plug:
            element.disconnectAll(mod=mod)

        return super().delete(mod=mod, apply=apply)

    def setup(self, *args: Any, **kwargs: Any):
        """Setup hook called after node creation.

        Override this method in subclasses to perform additional setup
        after the node and visual indicator are created.

        Args:
            *args: Positional arguments passed from __init__.
            **kwargs: Keyword arguments passed from __init__.
        """

        pass

    def meta_attributes(self) -> list[dict]:
        """Generate metadata attributes for this metanode.

        Returns:
            List of attribute definition dictionaries.
        """

        class_name = MetaRegistry.registry_name_for_class(self.__class__)

        return [
            {
                "name": META_CLASS_ATTR_NAME,
                "value": class_name,
                "type": attributetypes.kMFnDataString,
                "locked": True,
                "storable": True,
                "writable": True,
                "connectable": False,
            },
            {
                "name": META_VERSION_ATTR_NAME,
                "value": self.__class__.VERSION,
                "type": attributetypes.kMFnDataString,
                "locked": True,
                "storable": True,
                "writable": True,
                "connectable": False,
            },
            {
                "name": META_PARENT_ATTR_NAME,
                "value": None,
                "type": attributetypes.kMFnMessageAttribute,
                "isArray": True,
                "locked": False,
            },
            {
                "name": META_CHILDREN_ATTR_NAME,
                "value": None,
                "type": attributetypes.kMFnMessageAttribute,
                "locked": False,
                "isArray": True,
            },
            {
                "name": META_TAG_ATTR_NAME,
                "value": "",
                "type": attributetypes.kMFnDataString,
                "locked": False,
                "storable": True,
                "writable": True,
                "connectable": False,
            },
            {
                "name": META_GUID_ATTR_NAME,
                "value": str(uuid.uuid4()),
                "type": attributetypes.kMFnDataString,
                "locked": True,
                "storable": True,
                "writable": True,
                "connectable": False,
            },
        ]

    def metaclass_type(self) -> str:
        """Return the metaclass type identifier.

        Returns:
            The metaclass type string.
        """

        return self.attribute(META_CLASS_ATTR_NAME).value()

    def version(self) -> str:
        """Return the version string stored on this metanode.

        Returns:
            The version string.
        """

        return self.attribute(META_VERSION_ATTR_NAME).value()

    def tag(self) -> str:
        """Return the tag value stored on this metanode.

        Returns:
            The tag string.
        """

        return self.attribute(META_TAG_ATTR_NAME).value()

    def set_tag(self, tag: str, mod: OpenMaya.MDGModifier | None = None):
        """Set the tag value on this metanode.

        Args:
            tag: The tag string to set.
            mod: Optional modifier for batched operations.
        """

        tag_plug = self.attribute(META_TAG_ATTR_NAME)
        tag_plug.set(tag, mod=mod)

    def is_root(self) -> bool:
        """Determine if this metanode has no parent metanodes.

        Returns:
            True if this is a root metanode.
        """

        for _ in self.iterate_meta_parents():
            return False
        return True

    def connect_to(self, attribute_name: str, node: DGNode) -> Plug:
        """Connect a scene node to this metanode via a message attribute.

        Args:
            attribute_name: Name of the attribute to create/use.
            node: The node to connect.

        Returns:
            The destination plug on this metanode.
        """

        source_plug = node.attribute("message")

        if self.hasAttribute(attribute_name):
            destination_plug = self.attribute(attribute_name)
        else:
            new_attr = self.addAttribute(
                attribute_name,
                value=None,
                type=attributetypes.kMFnMessageAttribute,
            )
            destination_plug = (
                new_attr if new_attr else self.attribute(attribute_name)
            )

        source_plug.connect(destination_plug)
        return destination_plug

    def iterate_meta_parents(
        self, recursive: bool = False
    ) -> Iterator[MetaBase | MetaDagBase]:
        """Iterate over parent metanodes.

        Args:
            recursive: If True, recursively iterate all ancestors.

        Yields:
            Parent metanode instances.
        """

        from .base import MetaBase

        parent_plug = self.attribute(META_PARENT_ATTR_NAME)
        for child_element in parent_plug:
            for dest in child_element.destinations():
                parent_meta = MetaBase(
                    dest.node().object(), init_defaults=False
                )
                yield parent_meta
                if recursive:
                    for ancestor in parent_meta.iterate_meta_parents(
                        recursive=True
                    ):
                        yield ancestor

    def iterate_meta_children(
        self, depth_limit: int = 256, visited: set | None = None
    ) -> Iterator[MetaBase | MetaDagBase]:
        """Iterate over child metanodes.

        Args:
            depth_limit: Maximum recursion depth.
            visited: Set of already visited nodes to prevent cycles.

        Yields:
            Child metanode instances.
        """

        from .base import MetaBase

        child_plug = self.attribute(META_CHILDREN_ATTR_NAME)
        visited = visited or set()

        for element in child_plug:
            if depth_limit < 1:
                return
            child = element.source()
            if child is None:
                continue
            child_node = child.node()
            if (
                not child_node.hasAttribute(META_CHILDREN_ATTR_NAME)
                or child_node in visited
            ):
                continue
            visited.add(child_node)
            child_meta = MetaBase(child_node.object(), init_defaults=False)
            yield child_meta

            for sub_child in child_meta.iterate_meta_children(
                depth_limit=depth_limit - 1, visited=visited
            ):
                yield sub_child

    def add_meta_parent(
        self,
        parent: MetaBase | MetaDagBase,
        mod: OpenMaya.MDGModifier | None = None,
    ):
        """Add a parent metanode to this node.

        Args:
            parent: The parent metanode to add.
            mod: Optional modifier for batched operations.
        """

        parent_plug = self.attribute(META_PARENT_ATTR_NAME)
        next_element = parent_plug.nextAvailableElementPlug()
        next_element.connect(
            parent.attribute(
                META_CHILDREN_ATTR_NAME
            ).nextAvailableDestElementPlug(),
            mod=mod,
        )

    def add_meta_child(
        self,
        child: MetaBase | MetaDagBase,
        mod: OpenMaya.MDGModifier | None = None,
    ):
        """Add a child metanode to this node.

        Args:
            child: The child metanode to add.
            mod: Optional modifier for batched operations.
        """

        if hasattr(child, "remove_parent"):
            child.remove_parent(mod=mod)
        child.add_meta_parent(self, mod=mod)

    def remove_parent(
        self,
        parent: MetaBase | MetaDagBase | None = None,
        mod: OpenMaya.MDGModifier | None = None,
    ) -> bool:
        """Remove parent metanode connection(s).

        Args:
            parent: Specific parent to remove, or None to remove all.
            mod: Optional modifier for batched operations.

        Returns:
            True if any parents were removed.
        """

        from ..wrapper import dgModifier

        modifier = mod or dgModifier()
        parent_plug = self.attribute(META_PARENT_ATTR_NAME)

        for element in parent_plug:
            for dest in element.destinations():
                node = dest.node()
                if parent is None or node == parent:
                    element.disconnect(dest, modifier=modifier, apply=False)

        if mod is None:
            modifier.doIt()

        return True

    def _create_visual_indicator(self):
        """Create the visual indicator shape for this metanode.

        Override this method in subclasses to customize the visual appearance.
        The default implementation loads a shape from the curves library
        based on SHAPE_NAME class attribute.
        """

        if not self.SHAPE_NAME:
            return

        try:
            from ..curves import load_and_create_from_lib
            from ..om import nodes

            _, shapes = load_and_create_from_lib(
                self.SHAPE_NAME,
                parent=self.object(),
            )

            # Apply the default color to all shapes
            for shape in shapes:
                nodes.set_node_color(shape, self.SHAPE_COLOR)

        except Exception as err:
            logger.warning(f"Failed to create visual indicator: {err}")

    def set_shape_color(self, color: tuple[float, float, float]):
        """Set the color of all visual indicator shapes.

        Args:
            color: RGB color tuple (0.0-1.0 range).
        """

        from ..om import nodes as om_nodes

        for shape in self.shapes():
            om_nodes.set_node_color(shape.object(), color)

    def get_shape_color(self) -> tuple[float, float, float] | None:
        """Get the current color of the first visual indicator shape.

        Returns:
            RGB color tuple, or None if no shapes exist.
        """

        shapes = self.shapes()
        if not shapes:
            return None

        shape = shapes[0]
        try:
            r = shape.attribute("overrideColorR").value()
            g = shape.attribute("overrideColorG").value()
            b = shape.attribute("overrideColorB").value()
            return (r, g, b)
        except Exception:
            return None

    def _init_meta(
        self, mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None
    ) -> list[Plug]:
        """Initialize meta-attributes on this node.

        Args:
            mod: Optional modifier for batched operations.

        Returns:
            List of created Plug objects.
        """

        return self.createAttributesFromDict(
            {k["name"]: k for k in self.meta_attributes()}, mod=mod
        )
