"""Property system for the metadata network.

This module provides a property system that allows attaching specialized
metadata nodes (properties) to scene objects. Properties are leaf nodes
in the metadata graph that store data about specific scene objects.

Key concepts:
- Properties are meta nodes that attach to scene objects (joints, meshes, etc.)
- Properties can have actions (`act()`) that perform operations
- Properties support priority-based execution ordering
- Multiple properties of the same type can be restricted via `multi_allowed`

Example:
    >>> from tp.libs.maya.meta.properties import MetaProperty, add_property
    >>>
    >>> class RigProperty(MetaProperty):
    ...     ID = "rigProperty"
    ...     multi_allowed = False  # Only one per object
    ...
    ...     def on_add(self, obj, **kwargs):
    ...         print(f"Property added to {obj}")
    ...
    ...     def act(self, *args, **kwargs):
    ...         print("Executing rig property action")
    >>>
    >>> # Add property to a joint
    >>> prop = add_property(my_joint, RigProperty, rigType="FK")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from maya.api import OpenMaya
from tp.libs.python.decorators import Singleton

from .base import MetaBase, MetaFactory, MetaRegistry
from .constants import META_CLASS_ATTR_NAME

if TYPE_CHECKING:
    from ..wrapper import DagNode, DGNode


# =============================================================================
# Property Registry
# =============================================================================


class PropertyRegistry(metaclass=Singleton):
    """Manages registration of property-type meta nodes.

    This is a separate registry from MetaRegistry specifically for
    property nodes. This separation allows:
    - Different registration logic for properties
    - Separate namespace to avoid collisions
    - Property-specific queries and utilities

    Attributes:
        _CACHE: Internal storage for registered property classes.
        _HIDDEN: Storage for property classes with _do_register=False.
    """

    _CACHE: dict[str, type[MetaProperty]] = {}
    _HIDDEN: dict[str, type[MetaProperty]] = {}

    @staticmethod
    def registry_name_for_class(class_type: type[MetaProperty]) -> str:
        """Get the registry name for the given property class.

        Args:
            class_type: The property class type.

        Returns:
            The ID attribute if present, otherwise the class name.
        """

        if hasattr(class_type, "ID") and class_type.ID:
            return class_type.ID
        return class_type.__name__

    @classmethod
    def is_in_registry(cls, type_name: str) -> bool:
        """Check if a property type is registered.

        Args:
            type_name: The name of the property type to check.

        Returns:
            True if registered, False otherwise.
        """

        return type_name in cls._CACHE

    @classmethod
    def get_type(cls, type_name: str) -> type[MetaProperty] | None:
        """Get a registered property class by name.

        Args:
            type_name: The registered name of the property type.

        Returns:
            The property class, or None if not found.
        """

        return cls._CACHE.get(type_name)

    @classmethod
    def types(cls) -> dict[str, type[MetaProperty]]:
        """Return a copy of all registered property types.

        Returns:
            Dictionary mapping names to property classes.
        """

        return cls._CACHE.copy()

    @classmethod
    def hidden_types(cls) -> dict[str, type[MetaProperty]]:
        """Return a copy of all hidden (non-public) property types.

        Returns:
            Dictionary mapping names to hidden property classes.
        """

        return cls._HIDDEN.copy()

    @classmethod
    def get_hidden(cls, type_name: str) -> type[MetaProperty] | None:
        """Get a hidden property class by name.

        Args:
            type_name: The name of the hidden property type.

        Returns:
            The hidden property class, or None if not found.
        """

        return cls._HIDDEN.get(type_name)

    @classmethod
    def clear_cache(cls):
        """Clear all registered property classes."""

        cls._CACHE.clear()
        cls._HIDDEN.clear()

    @classmethod
    def unregister_property_class(cls, class_obj: type[MetaProperty]) -> bool:
        """Unregister a property class.

        Args:
            class_obj: The property class to unregister.

        Returns:
            True if successfully unregistered, False otherwise.
        """

        registry_name = cls.registry_name_for_class(class_obj)
        if registry_name in cls._CACHE:
            del cls._CACHE[registry_name]
            logger.debug(f"Unregistered PropertyClass -> {registry_name}")
            return True
        if registry_name in cls._HIDDEN:
            del cls._HIDDEN[registry_name]
            logger.debug(
                f"Unregistered hidden PropertyClass -> {registry_name}"
            )
            return True
        return False

    @classmethod
    def register_property_class(cls, class_obj: type[MetaProperty]):
        """Register a property class.

        Args:
            class_obj: The property class to register. Must be a
                subclass of MetaProperty.
        """

        if not (
            issubclass(class_obj, MetaProperty)
            or isinstance(class_obj, MetaProperty)
        ):
            return

        registry_name = cls.registry_name_for_class(class_obj)

        # Check _do_register flag
        do_register = getattr(class_obj, "_do_register", True)

        if do_register:
            if registry_name in cls._CACHE:
                return
            logger.debug(
                f"Registering PropertyClass -> {registry_name} | {class_obj}"
            )
            cls._CACHE[registry_name] = class_obj
        else:
            if registry_name in cls._HIDDEN:
                return
            logger.debug(
                f"Registering hidden PropertyClass -> {registry_name} | {class_obj}"
            )
            cls._HIDDEN[registry_name] = class_obj


# =============================================================================
# Property Factory Metaclass
# =============================================================================


class PropertyFactory(MetaFactory):
    """Metaclass for property nodes.

    Extends MetaFactory to provide property-specific instantiation logic,
    including registration with PropertyRegistry instead of MetaRegistry.
    """

    def __call__(cls: type[MetaProperty], *args, **kwargs):
        """Override instantiation to handle property registration.

        Args:
            cls: The property class being instantiated.
            *args: Positional arguments for instantiation.
            **kwargs: Keyword arguments for instantiation.

        Returns:
            An instance of the appropriate property class.
        """

        node = kwargs.get("node")
        if args:
            node = args[0]

        registry = PropertyRegistry

        # Register if not already registered
        registry_name = registry.registry_name_for_class(cls)
        if not registry.is_in_registry(registry_name):
            registry.register_property_class(cls)

        if not node:
            return type.__call__(cls, *args, **kwargs)

        # Try to resolve the actual class type from the node
        class_type = MetaBase.class_name_from_plug(node)
        if class_type == registry_name:
            return type.__call__(cls, *args, **kwargs)

        # Check property registry first, then meta registry
        registered_type = registry.get_type(class_type)
        if registered_type is None:
            registered_type = registry.get_hidden(class_type)
        if registered_type is None:
            registered_type = MetaRegistry.get_type(class_type)

        if registered_type is None:
            return type.__call__(cls, *args, **kwargs)

        return type.__call__(registered_type, *args, **kwargs)


# =============================================================================
# MetaProperty Base Class
# =============================================================================


class MetaProperty(MetaBase, metaclass=PropertyFactory):
    """Base class for property nodes that attach to scene objects.

    Properties are leaf nodes in the metadata graph that store data about
    specific scene objects. They provide a pattern for attaching metadata
    to joints, meshes, controls, and other scene elements.

    Class Attributes:
        ID: Unique identifier for this property type.
        VERSION: Version string for this property type.
        multi_allowed: If False, only one property of this type can be
            attached to an object. Default is False.
        auto_run: If True, the act() method is called automatically
            when the property is loaded. Default is False.
        priority: Execution priority for act(). Lower values run first.
            Default is 0.
        _do_register: Whether to register in public registry. Default False
            for base class (don't register base class).

    Example:
        >>> class JointProperty(MetaProperty):
        ...     ID = "jointProperty"
        ...     multi_allowed = False
        ...
        ...     def on_add(self, obj, **kwargs):
        ...         self.set("jointName", obj.name())
        ...
        ...     def act(self, *args, **kwargs):
        ...         return self.get("jointName")
    """

    ID: str | None = None
    VERSION: str = "1.0.0"
    DEFAULT_NAME: str | None = None
    _do_register: bool = False  # Base class should not be registered

    # Property-specific attributes
    multi_allowed: bool = False
    auto_run: bool = False
    priority: int = 0

    # Attribute name for the connection to the scene object
    CONNECTED_OBJECT_ATTR: str = "connectedObject"

    def __init__(
        self,
        node: DGNode | DagNode | OpenMaya.MObject | None = None,
        name: str | None = None,
        namespace: str | None = None,
        init_defaults: bool = True,
        lock: bool = False,
        mod: OpenMaya.MDGModifier | None = None,
        *args,
        **kwargs,
    ):
        """Initialize the property node.

        Args:
            node: Existing node to wrap, or None to create new.
            name: Name for new node.
            namespace: Namespace for new node.
            init_defaults: Whether to initialize default attributes.
            lock: Whether to lock the node after creation.
            mod: Optional modifier for batched operations.
            *args: Additional positional arguments passed to setup().
            **kwargs: Additional keyword arguments passed to setup().
        """

        super().__init__(
            node=node,
            name=name,
            namespace=namespace,
            init_defaults=init_defaults,
            lock=lock,
            mod=mod,
            *args,
            **kwargs,
        )

    def meta_attributes(self) -> list[dict]:
        """Generate metadata attributes including property-specific ones.

        Returns:
            List of attribute definitions including base attributes
            and property-specific attributes.
        """

        attrs = super().meta_attributes()

        # Add property-specific attributes
        from ..om import attributetypes

        attrs.extend(
            [
                {
                    "name": "propertyPriority",
                    "value": self.priority,
                    "type": attributetypes.kMFnNumericInt,
                    "locked": False,
                    "storable": True,
                    "writable": True,
                    "connectable": False,
                },
                {
                    "name": "propertyAutoRun",
                    "value": self.auto_run,
                    "type": attributetypes.kMFnNumericBoolean,
                    "locked": False,
                    "storable": True,
                    "writable": True,
                    "connectable": False,
                },
            ]
        )

        return attrs

    def connect_to_object(
        self,
        obj: DGNode | DagNode,
        mod: OpenMaya.MDGModifier | None = None,
    ):
        """Connect this property to a scene object.

        This establishes the property as being "owned by" the scene object.
        The connection is stored in the `connectedObject` attribute.

        Args:
            obj: The scene object to connect to.
            mod: Optional modifier for batched operations.
        """

        self.connect_to(self.CONNECTED_OBJECT_ATTR, obj)

    def connected_object(self) -> DGNode | DagNode | None:
        """Get the scene object this property is connected to.

        Returns:
            The connected scene object, or None if not connected.
        """

        if not self.hasAttribute(self.CONNECTED_OBJECT_ATTR):
            return None

        plug = self.attribute(self.CONNECTED_OBJECT_ATTR)
        source = plug.source()
        if source is None:
            return None

        return source.node()

    def act(self, *args: Any, **kwargs: Any) -> Any:
        """Perform the property's action.

        This method should be overridden in subclasses to implement
        the specific behavior of the property. It is called when
        the property needs to execute its action.

        Args:
            *args: Positional arguments for the action.
            **kwargs: Keyword arguments for the action.

        Returns:
            Result of the action (implementation-specific).
        """

        pass

    def on_add(self, obj: DGNode | DagNode, **kwargs: Any):
        """Called when this property is added to an object.

        Override this method to perform initialization when the
        property is first attached to a scene object.

        Args:
            obj: The scene object the property is being added to.
            **kwargs: Additional keyword arguments.
        """

        pass

    def compare(self, data: dict[str, Any]) -> bool:
        """Compare this property's data with a dictionary.

        Args:
            data: Dictionary of attribute names and values to compare.

        Returns:
            True if all provided values match, False otherwise.
        """

        for attr_name, expected_value in data.items():
            actual_value = self.get(attr_name)
            if actual_value != expected_value:
                return False
        return True

    def get_priority(self) -> int:
        """Get the execution priority of this property.

        Returns:
            Priority value (lower = higher priority).
        """

        return self.get("propertyPriority", default=self.priority)

    def set_priority(
        self, priority: int, mod: OpenMaya.MDGModifier | None = None
    ):
        """Set the execution priority of this property.

        Args:
            priority: New priority value.
            mod: Optional modifier for batched operations.
        """

        self.set("propertyPriority", priority)

    def is_auto_run(self) -> bool:
        """Check if this property should auto-run on load.

        Returns:
            True if auto-run is enabled.
        """

        return self.get("propertyAutoRun", default=self.auto_run)

    def set_auto_run(
        self, auto_run: bool, mod: OpenMaya.MDGModifier | None = None
    ):
        """Set whether this property should auto-run on load.

        Args:
            auto_run: Whether to enable auto-run.
            mod: Optional modifier for batched operations.
        """

        self.set("propertyAutoRun", auto_run)


# =============================================================================
# Property Utility Functions
# =============================================================================


def get_properties(node: DGNode | DagNode) -> list[MetaProperty]:
    """Get all properties attached to a scene node.

    Args:
        node: The scene node to query.

    Returns:
        List of MetaProperty instances attached to the node.
    """

    from .base import connected_meta_nodes

    properties: list[MetaProperty] = []
    for meta in connected_meta_nodes(node):
        if isinstance(meta, MetaProperty):
            properties.append(meta)
        elif meta.hasAttribute(META_CLASS_ATTR_NAME):
            # Check if it's a property type by looking at registry
            class_name = meta.attribute(META_CLASS_ATTR_NAME).value()
            if PropertyRegistry.is_in_registry(class_name):
                # Re-wrap as property
                prop_class = PropertyRegistry.get_type(class_name)
                if prop_class:
                    properties.append(
                        prop_class(node=meta.object(), init_defaults=False)
                    )

    # Sort by priority
    properties.sort(key=lambda p: p.get_priority())
    return properties


def get_property(
    node: DGNode | DagNode,
    property_type: type[MetaProperty],
) -> MetaProperty | None:
    """Get the first property of a specific type attached to a node.

    Args:
        node: The scene node to query.
        property_type: The property class to search for.

    Returns:
        The first matching property, or None if not found.
    """

    for prop in get_properties(node):
        if isinstance(prop, property_type):
            return prop
        # Also check by class name for dynamic resolution
        if prop.metaclass_type() == PropertyRegistry.registry_name_for_class(
            property_type
        ):
            return prop
    return None


def get_properties_by_type(
    node: DGNode | DagNode,
    property_type: type[MetaProperty],
) -> list[MetaProperty]:
    """Get all properties of a specific type attached to a node.

    Args:
        node: The scene node to query.
        property_type: The property class to search for.

    Returns:
        List of matching properties.
    """

    return [
        prop
        for prop in get_properties(node)
        if isinstance(prop, property_type)
        or prop.metaclass_type()
        == PropertyRegistry.registry_name_for_class(property_type)
    ]


def add_property(
    node: DGNode | DagNode,
    property_type: type[MetaProperty],
    name: str | None = None,
    **kwargs: Any,
) -> MetaProperty | None:
    """Add a property to a scene node.

    If the property type has `multi_allowed=False` and a property of
    that type already exists on the node, returns the existing property.

    Args:
        node: The scene node to add the property to.
        property_type: The property class to instantiate.
        name: Optional name for the property node.
        **kwargs: Additional attributes to set on the property.

    Returns:
        The created or existing property, or None on failure.
    """

    # Check if property already exists (for non-multi types)
    if not property_type.multi_allowed:
        existing = get_property(node, property_type)
        if existing is not None:
            logger.debug(
                f"Property {property_type.__name__} already exists on {node}"
            )
            return existing

    # Create the property
    try:
        prop = property_type(name=name, **kwargs)

        # Connect to the scene object
        prop.connect_to_object(node)

        # Call on_add hook
        prop.on_add(node, **kwargs)

        # Set any additional attributes
        for attr_name, value in kwargs.items():
            if not attr_name.startswith("_"):
                try:
                    prop.set(attr_name, value)
                except ValueError:
                    # Skip reserved attributes
                    pass

        return prop

    except Exception as e:
        logger.error(f"Failed to add property {property_type.__name__}: {e}")
        return None


def remove_property(
    node: DGNode | DagNode,
    property_type: type[MetaProperty] | None = None,
    mod: OpenMaya.MDGModifier | None = None,
) -> bool:
    """Remove properties from a scene node.

    Args:
        node: The scene node to remove properties from.
        property_type: If specified, only remove properties of this type.
            If None, removes all properties.
        mod: Optional modifier for batched operations.

    Returns:
        True if any properties were removed.
    """

    properties = get_properties(node)
    removed = False

    for prop in properties:
        if property_type is None or isinstance(prop, property_type):
            prop.delete(mod=mod)
            removed = True

    return removed


def get_properties_dict(
    node: DGNode | DagNode,
) -> dict[str, list[MetaProperty]]:
    """Get all properties grouped by type name.

    Args:
        node: The scene node to query.

    Returns:
        Dictionary mapping property type names to lists of properties.
    """

    result: dict[str, list[MetaProperty]] = {}
    for prop in get_properties(node):
        type_name = prop.metaclass_type()
        if type_name not in result:
            result[type_name] = []
        result[type_name].append(prop)
    return result


def run_properties(
    node: DGNode | DagNode,
    property_type: type[MetaProperty] | None = None,
    *args: Any,
    **kwargs: Any,
) -> list[Any]:
    """Run the act() method on properties attached to a node.

    Properties are executed in priority order (lower priority first).

    Args:
        node: The scene node whose properties to run.
        property_type: If specified, only run properties of this type.
        *args: Positional arguments passed to act().
        **kwargs: Keyword arguments passed to act().

    Returns:
        List of results from each property's act() method.
    """

    properties = get_properties(node)
    results: list[Any] = []

    for prop in properties:
        if property_type is None or isinstance(prop, property_type):
            try:
                result = prop.act(*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Error running property {prop.metaclass_type()}: {e}"
                )
                results.append(None)

    return results


def iterate_scene_properties(
    property_type: type[MetaProperty] | None = None,
) -> list[MetaProperty]:
    """Iterate all properties in the scene.

    Args:
        property_type: If specified, only return properties of this type.

    Returns:
        List of all properties in the scene.
    """

    from .base import iterate_scene_meta_nodes

    properties: list[MetaProperty] = []

    for meta in iterate_scene_meta_nodes():
        class_name = meta.metaclass_type()

        # Check if it's a registered property type
        prop_class = PropertyRegistry.get_type(class_name)
        if prop_class is None:
            prop_class = PropertyRegistry.get_hidden(class_name)

        if prop_class is not None:
            prop = prop_class(node=meta.object(), init_defaults=False)
            if property_type is None or isinstance(prop, property_type):
                properties.append(prop)

    return properties
