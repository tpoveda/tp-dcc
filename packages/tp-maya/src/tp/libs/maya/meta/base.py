from __future__ import annotations

import inspect
import os
import uuid
from collections.abc import Iterable, Iterator
from types import ModuleType
from typing import Any

from loguru import logger

from maya.api import OpenMaya
from tp.libs.python import modules
from tp.libs.python.decorators import Singleton

from ..om import attributetypes
from ..wrapper import DagNode, DGNode, Plug
from .constants import (
    META_CHILDREN_ATTR_NAME,
    META_CLASS_ATTR_NAME,
    META_GUID_ATTR_NAME,
    META_PARENT_ATTR_NAME,
    META_TAG_ATTR_NAME,
    META_VERSION_ATTR_NAME,
    RESERVED_ATTR_NAMES,
    TYPE_TO_MAYA_ATTR,
)


class MetaRegistry(metaclass=Singleton):
    """Manages the registration and storage of metaclasses for a specified type
    system.

    The `MetaRegistry` class is responsible for facilitating the registration
    and retrieval of metaclasses.

    It stores registered metaclasses in a centralized cache, provides methods
    to register metaclasses from various sources (e.g., individual classes,
    modules, packages, environment variables), and ensures unique
    registration of metaclasses.

    The class also includes functionality to verify and retrieve registered
    metaclasses by their name.

    Attributes:
        META_ENV_VAR: Name of the environment variable that holds paths for
            metaclasses registration.
        _CACHE: Internal storage cache mapping registry names to
            MetaBase-derived classes.
    """

    META_ENV_VAR = "TP_DCC_META_PATHS"
    _CACHE: dict[str, type[MetaBase]] = {}

    def __init__(self):
        super().__init__()

        try:
            self.reload()
        except ValueError:
            logger.error("Failed to registry meta classes", exc_info=True)

    @staticmethod
    def registry_name_for_class(class_type: type[MetaBase]) -> str:
        """Get the registry name for the given class.

        This static method retrieves the registry name associated with the
        given class type.

        If the class has an `ID` attribute, its value is returned; otherwise,
        the class's name is returned as the default identifier.

        Args:
            class_type: The class type for which the registry name is to be
            determined.

        Returns:
            The registry name for the provided class type.
        """

        if hasattr(class_type, "ID") and class_type.ID:
            return class_type.ID

        return class_type.__name__

    @classmethod
    def is_in_registry(cls, type_name: str) -> bool:
        """Determine whether a given type name is already registered in the class
        cache.

        This method checks if the specified type name exists in the `_CACHE`
        dictionary, indicating that the type has been registered.

        It provides a mechanism to verify the presence of a type in the
        registry maintained by the class.

        Args:
            type_name: The name of the type to check for in the class registry.

        Returns:
            True if the type name is in the registry, False otherwise.
        """

        return type_name in cls._CACHE

    @classmethod
    def get_type(cls, type_name: str) -> type[MetaBase] | None:
        """Retrieve the cached type associated with the given type name.

        This method searches the internal cache to find a type matching the
        provided type name.

        Args:
            type_name: The name of the type to retrieve from the cache.

        Returns:
            The cached type associated with the provided type name if it
                exists; `None` otherwise.
        """

        return cls._CACHE.get(type_name)

    @classmethod
    def types(cls) -> dict[str, type[MetaBase]]:
        """Return a copy of all registered types.

        Returns:
            A dictionary mapping registry names to their corresponding
                MetaBase subclasses.
        """

        return cls._CACHE.copy()

    @classmethod
    def clear_cache(cls):
        """Clear all registered metaclasses from the cache.

        This method removes all entries from the internal cache, effectively
        unregistering all previously registered metaclasses.
        """

        cls._CACHE.clear()

    @classmethod
    def unregister_meta_class(cls, class_obj: type[MetaBase]) -> bool:
        """Unregister a Meta class from the internal cache.

        Args:
            class_obj: The class object to be unregistered.

        Returns:
            True if the class was successfully unregistered; False if it
                was not found in the cache.
        """

        registry_name = cls.registry_name_for_class(class_obj)
        if registry_name in cls._CACHE:
            del cls._CACHE[registry_name]
            logger.debug(f"Unregistered MetaClass -> {registry_name}")
            return True
        return False

    @classmethod
    def register_meta_class(cls, class_obj: type[MetaBase]):
        """Register a Meta class to the internal cache of the system.

        This method verifies if the provided class object is a subclass or an
        instance of the base `MetaBase` class. If the verification passes and
        the class has not been previously registered, it is added to the cache.

        The registration process ensures that Meta classes remain organized and
        accessible throughout their use in the system.

        Args:
            class_obj: The class object to be registered. This object must
                either be a subclass or an instance of `MetaBase`.
        """

        if issubclass(class_obj, MetaBase) or isinstance(class_obj, MetaBase):
            registry_name = cls.registry_name_for_class(class_obj)
            if registry_name in cls._CACHE:
                return
            logger.debug(
                f"Registering MetaClass -> {registry_name} | {class_obj}"
            )
            cls._CACHE[registry_name] = class_obj

    @classmethod
    def register_by_package(cls, package_path: str):
        """Register metaclasses by iterating through a package's modules.

        The method dynamically loads and iterates through the modules within
        a given package path. It verifies each module for validity and skips
        special files or duplicates.

        Once the valid modules are identified, the method identifies the
        classes defined in those modules and registers them as meta classes.

        Args:
            package_path: The path of the package whose modules are to be
                processed and whose classes are to be registered.
        """

        visited_packages = set()
        for sub_module in modules.iterate_modules(package_path):
            file_name = os.path.splitext(os.path.basename(sub_module))[0]
            if file_name in visited_packages or not modules.valid_module_path(
                sub_module
            ):
                continue

            if file_name.startswith("__") or file_name in visited_packages:
                continue
            visited_packages.add(file_name)
            sub_module_obj = modules.import_module(
                modules.convert_to_dotted_path(os.path.normpath(sub_module))
            )
            for member in modules.iterate_module_members(
                sub_module_obj, predicate=inspect.isclass
            ):
                cls.register_meta_class(member[1])

    @classmethod
    def register_by_module(cls, module: ModuleType):
        """Register all classes from the given module within the metaclass
        registry if they meet the required predicate.

        This method examines the contents of the provided module, identifies
        class definitions, and registers them with the metaclass registry if
        the predicate condition is satisfied.

        Notes:
            It ignores any non-modules passed to it and ensures that only
            actual classes from the module are processed.

        Args:
            module: The module to iterate over for identifying classes and
                registering them.
        """

        if not inspect.ismodule(module):
            return

        for member in modules.iterate_module_members(
            module, predicate=inspect.isclass
        ):
            cls.register_meta_class(member[1])

    @classmethod
    def register_meta_classes(cls, paths: Iterable[str]):
        """Register metaclasses from the given paths. Each entry in the
        paths can either be a directory or a file.

        Directories are processed to register metaclasses by their package,
        and files are processed to register metaclasses by their module.

        Notes:
            Invalid paths, such as non-existent directories or files that do
            not represent valid modules, are ignored.

        Args:
            paths: A collection of directory or file paths. Directories are
                recursively processed to register metaclasses by packages,
                while files are processed to register meta-classes by modules.
        """

        for path in paths:
            if not path:
                continue
            if os.path.isdir(path):
                cls.register_by_package(path)
                continue
            elif os.path.isfile(path):
                if not modules.valid_module_path(path):
                    continue
                imported_module = modules.import_module(
                    modules.convert_to_dotted_path(os.path.normpath(path))
                )
                if imported_module:
                    cls.register_by_module(imported_module)
                    continue

    @classmethod
    def register_by_env(cls, env_name: str):
        """Register metaclasses by fetching environment variable values and
        splitting them into paths.

        Args:
            env_name: The name of the environment variable to fetch.

        Raises:
            ValueError: If the specified environment variable does not exist
                or has no value.
        """

        environment_paths = os.getenv(env_name)
        if environment_paths is None:
            raise ValueError(
                f'No environment variable with name "{env_name}" exists!'
            )

        environment_paths = environment_paths.split(os.pathsep)

        cls.register_meta_classes(environment_paths)

    def reload(self):
        """Reload the registry data by re-registering using an environment
        variable.

        This method ensures that the registry information is updated
        dynamically based on the specified environment variable.

        It relies on a meta-environment variable for the re-registration
        process.

        Raises:
            KeyError: If the environment variable specified by
                MetaRegistry.META_ENV_VAR is not set or cannot be accessed.
        """

        self.register_by_env(MetaRegistry.META_ENV_VAR)


class MetaFactory(type):
    """Metaclass to manage dynamic instantiation and registration of classes.

    This metaclass overrides the default `__call__` method to allow dynamic
    instantiation  of classes or their appropriate subclasses.

    It evaluates whether a node or specific class type is provided and
    determines the correct class to instantiate based on a  registration
    mechanism.

    It enables seamless integration with a class registry for the dynamic
    management of instantiable classes.
    """

    def __call__(cls: type[MetaBase], *args, **kwargs):
        """Override the default `__call__` behavior of a class to introduce
        customized instantiation logic.

        It primarily checks whether the provided class is registered,
        registers it if needed, and determines the appropriate class type for
        the instantiation based on the provided `node`. If a specific type is
        resolved from the registry, it delegates the instantiation to that
        type.

        Args:
            cls: The class being called, of type `MetaBase` or its subclass.
            *args: Positional arguments for the class instantiation.
                The first argument can optionally be the `node`.
            **kwargs: Keyword arguments for the class instantiation.
                Contains `node`, which can be an instance of `DGNode`,
                `DagNode`, `MetaBase`, `OpenMaya.MObject`, or `None`.

        Returns:
            An instance of the determined class type. If no specific type is
            resolved, it defaults to instantiating the given `cls`.

        """

        node: DGNode | DagNode | MetaBase | OpenMaya.MObject | None = (
            kwargs.get("node")
        )
        if args:
            node = args[0]

        register = MetaRegistry

        # If the given class is not registered, we register it.
        registry_name = MetaRegistry.registry_name_for_class(cls)

        if not register.is_in_registry(registry_name):
            register.register_meta_class(cls)

        if not node:
            return type.__call__(cls, *args, **kwargs)

        class_type = MetaBase.class_name_from_plug(node)
        if class_type == registry_name:
            return type.__call__(cls, *args, **kwargs)

        # Check MetaRegistry first
        # noinspection PyUnresolvedReferences
        registered_type = MetaRegistry().get_type(class_type)

        # If not found, check PropertyRegistry
        if registered_type is None:
            try:
                from .properties import PropertyRegistry

                registered_type = PropertyRegistry.get_type(class_type)
                if registered_type is None:
                    registered_type = PropertyRegistry.get_hidden(class_type)
            except ImportError:
                pass

        if registered_type is None:
            return type.__call__(cls, *args, **kwargs)

        return type.__call__(registered_type, *args, **kwargs)


class MetaBase(DGNode, metaclass=MetaFactory):
    """Base class for creating and managing metanodes in a Maya scene.

    This class serves as a foundational structure for defining and working
    with metanode instances within the Maya scene.

    Metanodes are network nodes that store metadata about a scene object.

    This base class provides methods for creating, initializing, connecting,
    and managing such metanodes, as well as querying their attributes and
    relationships.

    Attributes:
        ID: Unique identifier for the metanode. `None` if not set.
        VERSION: Version string for the metanode class. Defaults to "1.0.0".
        DEFAULT_NAME: Default name used when creating a metanode instance.
            `None` indicates no default name is defined.
        _do_register: Whether this class should be registered in the public
            registry. Set to False for internal/private classes.
    """

    ID: str | None = None
    VERSION: str = "1.0.0"
    DEFAULT_NAME: str | None = None
    _do_register: bool = True

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
        """Initializes the object with the provided parameters and sets up a
        network node if the node is not provided. It also allows locking the
        node and initializing default settings.

        Args:
            node: An instance of `DGNode`, `DagNode`, `OpenMaya.MObject`,
                or `None`. If `None`, a new node will be created.
            name: A string representing the name of the node. Defaults to `None`.
            namespace: A string specifying the namespace for the node.
            init_defaults: A boolean indicating whether default settings
                should be initialized.
            lock: A boolean indicating whether the node should be locked
                after creation.
            mod: An instance of OpenMaya.MDGModifier used to apply
                modifications to the node.
            *args: Additional positional arguments for further setup or
                extension.
            **kwargs: Additional keyword arguments for further setup or
                extension.
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
                node_type="network",
                namespace=namespace,
                mod=mod,
            )

        if init_defaults and not self.isReferenced():
            if mod:
                mod.doIt()
            self._init_meta(mod=mod)

            if lock and not self.mfn().isLocked:
                self.lock(True, mod=mod)

        if node is None:
            self.setup(*args, **kwargs)

    def __repr__(self) -> str:
        """Return a string representation of the object for debugging purposes.

        This method provides a concise and human-readable string format of the
        object, combining its string representation and name. It is primarily
        useful for debugging or logging to identify the object and its state
        easily.

        Returns:
            A formatted string combining the object's string representation
                and name.
        """

        return f"{self.as_str(name_only=True)} ({self.name()})"

    @classmethod
    def as_str(cls, name_only: bool = False) -> str:
        """Retrieve the class name or the fully qualified class path as a string,
        depending on the input parameters.

        This method allows retrieving either the name of the class alone or
        the fully qualified class path, including the module it is defined in.

        It can be useful in debugging, logging, or dynamically identifying
        class information.

        Args:
            name_only: Determines whether to return only the class
                name (True) or the fully qualified  class path with the
                module (False)

        Returns:
            The class name or the fully qualified class path, depending on
                the value of `name_only`.
        """

        meta_module = cls.__module__
        meta_name = cls.__name__
        if name_only:
            return meta_name

        return ".".join([meta_module, meta_name])

    @staticmethod
    def class_name_from_plug(
        node: DGNode | DagNode | MetaBase | OpenMaya.MObject,
    ) -> str:
        """Extract the class name from a specific type of plug object.

        This method determines and returns the class name associated with
        the given node by either accessing an attribute directly or by
        querying the plug  associated with the node.

        The input node can be of several specific types.

        Args:
            node: Input node object from which to derive the class name.

        Returns:
            The class name derived from the node's attribute or plug. Returns
                an empty string if the attribute cannot be found.
        """

        if isinstance(node, MetaBase):
            return node.attribute(META_CLASS_ATTR_NAME).value()
        dep = OpenMaya.MFnDependencyNode(node)
        try:
            return dep.findPlug(META_CLASS_ATTR_NAME, False).asString()
        except RuntimeError:
            return ""

    def delete(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete the current object and disconnects all child attributes
        associated with it.

        If a modifier is provided, the operation will use it to handle
        disconnection and deletion tasks. Once all the child attributes are
        successfully disconnected, the base deletion implementation is called.

        Args:
            mod: An optional modifier to manage the disconnection and
            deletion operations. If None, the default behavior is used.
            apply: Determines whether the modification should be applied or not.

        Returns:
            True if the object was successfully deleted; False otherwise.
        """

        child_plug = self.attribute(META_CHILDREN_ATTR_NAME)
        for element in child_plug:
            element.disconnectAll(mod=mod)

        return super().delete(mod=mod, apply=apply)

    def delete_all(
        self, mod: OpenMaya.MDGModifier | None = None, apply: bool = True
    ) -> bool:
        """Delete this node and all downstream meta nodes.

        This method recursively deletes all child meta nodes before
        deleting this node. Useful for cleaning up an entire meta
        network branch.

        Args:
            mod: An optional modifier for batched operations.
            apply: Whether to apply the modifier immediately.

        Returns:
            True if all nodes were successfully deleted; False otherwise.
        """

        # Collect all children first (to avoid modifying during iteration).
        children = list(self.iterate_meta_children(depth_limit=1))

        # Recursively delete children first.
        for child in children:
            if hasattr(child, "delete_all"):
                child.delete_all()
            else:
                child.delete()

        # Delete this node.
        return self.delete(mod=mod, apply=apply)

    def select(self, add: bool = False, replace: bool = True):
        """Select this node in Maya.

        Args:
            add: If True, add to the current selection.
            replace: If True (default), replace the current selection.

        Example:
            >>> meta.select()  # Select only this node
            >>> meta.select(add=True)  # Add to selection
        """

        import maya.cmds as cmds

        if not self.exists():
            return

        node_name = self.name()
        if replace and not add:
            cmds.select(node_name, replace=True)
        elif add:
            cmds.select(node_name, add=True)
        else:
            cmds.select(node_name)

    def setup(self, *args: Any, **kwargs: Any):
        """Represent a configuration setup for the metanode initialization.

        This serves as an entry point to initialize all the necessary
        parameters or options for a new metanode instance.

        This method acts as a flexible setup that accepts any arguments or
        keyword arguments without enforcing strict validation.

        Warnings:
            Users need to ensure the correctness of the provided input as this
            method doesn't directly validate or constrain the data.

        Args:
            *args: Positional arguments that can be used for configuration.
            **kwargs: Keyword arguments intended to provide additional
                configuration options.
        """

    def meta_attributes(self) -> list[dict]:
        """Generate metadata attributes for the current class instance.

        This method constructs and returns a list of dictionaries where each
        dictionary represents a metadata attribute associated with the current
        class instance.

        These attributes include details such as the attribute name, value,
        type, and flags (e.g., locked, storable, writable).

        The metadata is generated dynamically and tailored to the specific
        class using its registry name.

        Returns:
            A list containing dictionaries with metadata attributes.
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
        """Return the metaclass type associated with the instance.

        This function retrieves the value of the metaclass attribute
        represented by the constant `META_CLASS_ATTR_NAME`.

        Returns:
            The value of the metaclass attribute.
        """

        return self.attribute(META_CLASS_ATTR_NAME).value()

    def version(self) -> str:
        """Return the version string stored on the metanode.

        Returns:
            The version string stored in the metanode's version attribute.
        """

        return self.attribute(META_VERSION_ATTR_NAME).value()

    def tag(self) -> str:
        """Return the tag value stored on the metanode.

        Returns:
            The tag string stored in the metanode's tag attribute.
        """

        return self.attribute(META_TAG_ATTR_NAME).value()

    def set_tag(self, tag: str, mod: OpenMaya.MDGModifier | None = None):
        """Set the tag value on the metanode.

        Args:
            tag: The tag string to set.
            mod: An optional modifier to apply the change.
        """

        tag_plug = self.attribute(META_TAG_ATTR_NAME)
        tag_plug.set(tag, mod=mod)

    def __eq__(self, other: object) -> bool:
        """Check equality between two MetaBase instances based on their MObject.

        Args:
            other: The other object to compare with.

        Returns:
            True if both objects reference the same Maya node; False otherwise.
        """

        if not isinstance(other, MetaBase):
            return False
        return self.object() == other.object()

    def __hash__(self) -> int:
        """Return a hash based on the MObject handle for use in sets and dicts.

        Returns:
            Hash value for the meta node.
        """

        return OpenMaya.MObjectHandle(self.object()).hashCode()

    def is_root(self) -> bool:
        """Determine if the current object is the root by iterating over its
        metanode parents.

        The method checks if there are any metanode parents for the current
        object. If no metanode parents are found, the object is considered a
        root. Otherwise, it is not a root.

        Returns:
            True if the object is a root (has no metanode parents);
            False otherwise.
        """

        for _ in self.iterate_meta_parents():
            return False

        return True

    def connect_to(self, attribute_name: str, node: DGNode) -> Plug:
        """Connect an attribute on the current object to the "message" plug
        of the specified `DGNode` instance.

        The method ensures a connection between the source plug of the `DGNode`
        and the destination plug on the current object. If the named attribute
        already exists, it directly uses it for connection; otherwise, a new
        attribute is created.

        Args:
            attribute_name: Name of the attribute to connect to the current
                object.
            node: The `DGNode` object whose "message" plug is to be connected.

        Returns:
            A reference to the destination plug that is connected.
        """

        node_attr_name = "message"
        source_plug = node.attribute(node_attr_name)

        if self.hasAttribute(attribute_name):
            destination_plug = self.attribute(attribute_name)
        else:
            new_attr = self.addAttribute(
                attribute_name,
                value=None,
                type=attributetypes.kMFnMessageAttribute,
            )
            if new_attr is not None:
                destination_plug = new_attr
            else:
                destination_plug = self.attribute(attribute_name)
        source_plug.connect(destination_plug)

        return destination_plug

    @staticmethod
    def connect_to_by_plug(destination_plug: Plug, node: DGNode) -> Plug:
        """Connect the given `destination_plug` to the `message` attribute
        of the specified `node`.

        This method establishes a connection from a plug of a node to the
        input plug passed in as the destination. It operates in a static
        context and is used to link data flows within a dependency graph.

        Args:
            destination_plug: The plug to which the `message` attribute of
                the node will be connected.
            node: The node whose `message` attribute is being connected
                to the `destination_plug`.

        Returns:
            The destination plug after the connection is made.
        """

        source_plug = node.attribute("message")
        source_plug.connect(destination_plug)

        return destination_plug

    def connect_node(
        self,
        node: DGNode,
        attribute_name: str,
        mod: OpenMaya.MDGModifier | None = None,
    ) -> Plug:
        """Connect a scene node to this meta node via a named attribute.

        This is a convenience alias for connect_to() with clearer semantics.
        The connection is made from the scene node's message attribute to
        a message attribute on this meta node.

        Args:
            node: The scene node to connect.
            attribute_name: Name of the attribute to create/use on this meta node.
            mod: Optional modifier for batched operations.

        Returns:
            The destination plug on this meta node.

        Example:
            >>> meta.connect_node(joint, "rootJoint")
            >>> meta.connect_node(mesh, "bodyMesh")
        """

        return self.connect_to(attribute_name, node)

    def disconnect_node(
        self,
        node: DGNode,
        attribute_name: str | None = None,
        mod: OpenMaya.MDGModifier | None = None,
    ):
        """Disconnect a scene node from this meta node.

        If attribute_name is provided, only disconnects from that specific
        attribute. If None, disconnects from all attributes where this node
        is connected.

        Args:
            node: The scene node to disconnect.
            attribute_name: Specific attribute to disconnect from.
                If None, disconnects from all attributes.
            mod: Optional modifier for batched operations.
        """

        modifier = mod or OpenMaya.MDGModifier()
        node_mobj = node.object()

        if attribute_name is not None:
            # Disconnect from specific attribute
            if self.hasAttribute(attribute_name):
                plug = self.attribute(attribute_name)
                source = plug.source()
                if source is not None and source.node().object() == node_mobj:
                    # Disconnect: source -> destination
                    modifier.disconnect(source.plug(), plug.plug())
                    modifier.doIt()
        else:
            # Disconnect from all attributes
            for plug in self.iterateExtraAttributes(
                skip=tuple(RESERVED_ATTR_NAMES)
            ):
                if (
                    plug.plug()
                    .attribute()
                    .hasFn(OpenMaya.MFn.kMessageAttribute)
                ):
                    source = plug.source()
                    if (
                        source is not None
                        and source.node().object() == node_mobj
                    ):
                        modifier.disconnect(source.plug(), plug.plug())
                        modifier.doIt()

    def get_connected_nodes(
        self,
        attribute_name: str | None = None,
        include_meta: bool = False,
    ) -> list[DGNode]:
        """Get scene nodes connected to this meta node.

        Args:
            attribute_name: If provided, returns only nodes connected to
                that specific attribute. If None, returns all connected nodes.
            include_meta: If True, includes other meta nodes in the result.
                If False (default), only returns non-meta scene nodes.

        Returns:
            List of connected DGNode instances.

        Example:
            >>> joints = meta.get_connected_nodes("joints")
            >>> all_connected = meta.get_connected_nodes()
        """

        connected: list[DGNode] = []

        if attribute_name is not None:
            # Get nodes from specific attribute
            if self.hasAttribute(attribute_name):
                plug = self.attribute(attribute_name)
                if plug.plug().isArray:
                    for element in plug:
                        source = element.source()
                        if source is not None:
                            node = source.node()
                            if include_meta or not is_meta_node(node):
                                connected.append(node)
                else:
                    source = plug.source()
                    if source is not None:
                        node = source.node()
                        if include_meta or not is_meta_node(node):
                            connected.append(node)
        else:
            # Get nodes from all message attributes (excluding reserved)
            for plug in self.iterateExtraAttributes(
                skip=tuple(RESERVED_ATTR_NAMES)
            ):
                if (
                    plug.plug()
                    .attribute()
                    .hasFn(OpenMaya.MFn.kMessageAttribute)
                ):
                    if plug.plug().isArray:
                        for element in plug:
                            source = element.source()
                            if source is not None:
                                node = source.node()
                                if include_meta or not is_meta_node(node):
                                    connected.append(node)
                    else:
                        source = plug.source()
                        if source is not None:
                            node = source.node()
                            if include_meta or not is_meta_node(node):
                                connected.append(node)

        return connected

    @property
    def data(self) -> dict[str, Any]:
        """Return all user-defined attributes as a dictionary.

        This property collects all attributes on the node that are not part
        of the reserved metadata attributes and returns them as a dictionary.

        Returns:
            A dictionary mapping attribute names to their values.
        """

        data_dict: dict[str, Any] = {}
        # Convert frozenset to tuple for startswith compatibility
        skip_attrs = tuple(RESERVED_ATTR_NAMES)
        for plug in self.iterateExtraAttributes(skip=skip_attrs):
            try:
                attr_name = plug.name().split(".")[-1]
                data_dict[attr_name] = plug.value()
            except (RuntimeError, AttributeError):
                continue
        return data_dict

    @data.setter
    def data(self, values: dict[str, Any]):
        """Set multiple attributes from a dictionary.

        This setter allows bulk-setting of attributes by passing a dictionary.
        Attributes that don't exist will be created with an appropriate type.

        Args:
            values: A dictionary mapping attribute names to values.
        """

        for attr_name, value in values.items():
            self.set(attr_name, value)

    def get(
        self,
        attr_name: str,
        default: Any = None,
        auto_create: bool = False,
        attr_type: int | None = None,
    ) -> Any:
        """Get an attribute value by name.

        This method retrieves the value of an attribute. If the attribute
        doesn't exist and `auto_create` is True, it will be created with
        the given default value.

        Args:
            attr_name: The name of the attribute to get.
            default: The default value to return if the attribute doesn't
                exist and auto_create is False.
            auto_create: If True and the attribute doesn't exist, create it
                with the default value.
            attr_type: The Maya attribute type to use when auto-creating.
                If None, the type is inferred from the default value.

        Returns:
            The attribute value, or the default if the attribute doesn't exist.
        """

        if not self.hasAttribute(attr_name):
            if auto_create and default is not None:
                self.set(attr_name, default, attr_type=attr_type)
                return default
            return default

        try:
            plug = self.attribute(attr_name)
            value = plug.value()
            return value if value is not None else default
        except (RuntimeError, AttributeError):
            return default

    def set(
        self,
        attr_name: str,
        value: Any,
        attr_type: int | None = None,
        mod: OpenMaya.MDGModifier | None = None,
    ):
        """Set an attribute value by name, creating it if necessary.

        This method sets the value of an attribute. If the attribute doesn't
        exist, it will be created with the appropriate type.

        Args:
            attr_name: The name of the attribute to set.
            value: The value to set.
            attr_type: The Maya attribute type to use when creating.
                If None, the type is inferred from the value type.
            mod: An optional modifier to apply the change.

        Raises:
            ValueError: If the attribute cannot be created or set.
        """

        if attr_name in RESERVED_ATTR_NAMES:
            raise ValueError(
                f"Cannot set reserved attribute '{attr_name}'. "
                f"Use the dedicated method instead."
            )

        if not self.hasAttribute(attr_name):
            # Determine attribute type from value if not specified
            if attr_type is None:
                attr_type = TYPE_TO_MAYA_ATTR.get(
                    type(value), attributetypes.kMFnDataString
                )

            # Create the attribute
            self.addAttribute(
                attr_name,
                value=value,
                type=attr_type,
            )
        else:
            # Set existing attribute
            plug = self.attribute(attr_name)
            plug.set(value, mod=mod)

    def data_equals(self, other_data: dict[str, Any]) -> bool:
        """Compare this node's data with a dictionary.

        Checks if all key-value pairs in `other_data` match the corresponding
        attributes on this node. Keys in `other_data` that don't exist on
        the node are considered non-matching.

        Args:
            other_data: Dictionary of attribute names and expected values.

        Returns:
            True if all provided values match, False otherwise.

        Example:
            >>> if meta.data_equals({"rigType": "FK", "side": "L"}):
            ...     print("Data matches!")
        """

        for attr_name, expected_value in other_data.items():
            if not self.hasAttribute(attr_name):
                return False
            actual_value = self.get(attr_name)
            if actual_value != expected_value:
                return False
        return True

    def bake_to_object(
        self,
        obj: DGNode,
        prefix: str = "meta_",
        include_class_info: bool = True,
    ):
        """Serialize meta node data as attributes on a scene object.

        Creates attributes on the target object containing this meta node's
        data. This allows storing metadata directly on scene objects for
        export or transfer.

        Args:
            obj: The scene object to bake data to.
            prefix: Prefix for attribute names to avoid collisions.
            include_class_info: If True, includes the meta class type and
                version as attributes.

        Example:
            >>> meta.bake_to_object(joint, prefix="rigMeta_")
        """

        from ..om import nodes as om_nodes

        # Bake class info if requested
        if include_class_info:
            class_attr_name = f"{prefix}class"
            version_attr_name = f"{prefix}version"

            if not obj.hasAttribute(class_attr_name):
                obj.addAttribute(
                    class_attr_name,
                    value=self.metaclass_type(),
                    type=attributetypes.kMFnDataString,
                )
            else:
                obj.attribute(class_attr_name).set(self.metaclass_type())

            if not obj.hasAttribute(version_attr_name):
                obj.addAttribute(
                    version_attr_name,
                    value=self.version(),
                    type=attributetypes.kMFnDataString,
                )
            else:
                obj.attribute(version_attr_name).set(self.version())

        # Bake user data
        for attr_name, value in self.data.items():
            baked_attr_name = f"{prefix}{attr_name}"

            # Determine attribute type
            attr_type = TYPE_TO_MAYA_ATTR.get(
                type(value), attributetypes.kMFnDataString
            )

            # Convert non-string values to string for safe storage
            if attr_type == attributetypes.kMFnDataString and not isinstance(
                value, str
            ):
                value = str(value)

            if not obj.hasAttribute(baked_attr_name):
                try:
                    obj.addAttribute(
                        baked_attr_name,
                        value=value,
                        type=attr_type,
                    )
                except Exception:
                    # Fall back to string
                    obj.addAttribute(
                        baked_attr_name,
                        value=str(value),
                        type=attributetypes.kMFnDataString,
                    )
            else:
                obj.attribute(baked_attr_name).set(value)

    def bake_to_connected(self, prefix: str = "meta_"):
        """Bake data to all connected scene objects.

        Calls bake_to_object for each scene node connected to this meta node.

        Args:
            prefix: Prefix for attribute names to avoid collisions.

        Example:
            >>> meta.bake_to_connected()
        """

        for node in self.get_connected_nodes():
            self.bake_to_object(node, prefix=prefix)

    @classmethod
    def load_from_object(
        cls,
        obj: DGNode,
        prefix: str = "meta_",
        create_if_missing: bool = True,
    ) -> MetaBase | None:
        """Reconstruct a meta node from baked attributes on a scene object.

        Reads baked attributes from the object and creates a new meta node
        with the same data. If class info was baked, uses the correct class.

        Args:
            obj: The scene object to load data from.
            prefix: Prefix that was used when baking.
            create_if_missing: If True, creates a new meta node. If False,
                returns None if no baked data is found.

        Returns:
            A new MetaBase instance (or subclass) with the loaded data,
            or None if no baked data was found and create_if_missing is False.

        Example:
            >>> meta = MetaBase.load_from_object(joint, prefix="rigMeta_")
        """

        class_attr_name = f"{prefix}class"
        version_attr_name = f"{prefix}version"

        # Check if baked data exists
        if not obj.hasAttribute(class_attr_name):
            if not create_if_missing:
                return None
            # Create with base class if no class info
            meta_class = cls
        else:
            # Get the class type
            class_type = obj.attribute(class_attr_name).value()
            meta_class = MetaRegistry.get_type(class_type)
            if meta_class is None:
                meta_class = cls

        # Create the meta node
        meta = meta_class()

        # Load user data - iterate object attributes looking for prefix
        skip_attrs = {class_attr_name, version_attr_name}
        for plug in obj.iterateExtraAttributes():
            attr_name = plug.name().split(".")[-1]
            if attr_name.startswith(prefix) and attr_name not in skip_attrs:
                # Remove prefix to get original attribute name
                original_name = attr_name[len(prefix) :]
                try:
                    value = plug.value()
                    meta.set(original_name, value)
                except Exception:
                    continue

        return meta

    def meta_root(self) -> MetaBase | None:
        """Determine the root metadata object in a hierarchical structure.

        This function traverses through the hierarchy of metadata objects
        using `iterate_meta_parents`, which returns the parent nodes of the
        current metadata object.

        The function recursively checks each parent node and its parents
        until it identifies the top-most parent (the root element) in the
        hierarchy.

        Returns:
            The root metadata object if it exists, or `None` if the hierarchy
            is empty or there is no root element.
        """

        for current_parent in self.iterate_meta_parents(recursive=True):
            parents = list(current_parent.iterate_meta_parents(recursive=True))
            if not parents:
                return current_parent

        return None

    def meta_parent(self) -> MetaBase | None:
        """Return the first metanode parent from the iterable of metanode
        parents or None if no metanode parents are present.

        This method retrieves metanode parent objects by iterating through
        metanode parents non-recursively.

        Returns:
            The first metanode parent object if present; None if no metanode
            parents exist.
        """

        meta_parents = list(self.iterate_meta_parents(recursive=False))
        return meta_parents[0] if meta_parents else None

    def iterate_meta_parents(
        self, recursive: bool = False, check_type: str | type | None = None
    ) -> Iterator[MetaBase]:
        """Iterate over the meta-parents of the current object.

        This method traverses the metanode hierarchy and yields parent metanode
        objects based on the provided criteria.

        It supports filtering by type or class name and can recursively
        iterate through the entire hierarchy of metanode parents if desired.

        Args:
            recursive: Determines whether to recursively iterate through all
                ancestor metanode parents in the hierarchy. If set to False,
                only immediate metanode parents are considered.
            check_type: A filter criterion to yield only metanode parents
                matching the specified type or class name.
                    - If None, yields all metanode parents.
                    - If a type is passed, only metanode parents whose class
                        is in the type's MRO (Method Resolution Order) are
                        yielded.
                    - If a string is passed, only metanode parents with a
                        matching class name attribute are yielded.

        Yields:
            Iterates through and yields instances of `MetaBase` that satisfy
                the filtering and traversal criteria specified by the
                arguments.
        """

        is_type = inspect.isclass(check_type)
        parent_plug = self.attribute(META_PARENT_ATTR_NAME)
        if not parent_plug:
            return
        for child_element in parent_plug:
            for dest in child_element.destinations():
                parent_meta = MetaBase(
                    dest.node().object(), init_defaults=False
                )
                if not check_type:
                    yield parent_meta
                else:
                    if is_type and check_type in parent_meta.__class__.mro():
                        yield parent_meta
                    elif (
                        isinstance(check_type, str)
                        and check_type
                        == parent_meta.attribute(META_CLASS_ATTR_NAME).value()
                    ):
                        yield parent_meta
                if recursive:
                    for i in parent_meta.iterate_meta_parents(
                        recursive=recursive, check_type=check_type
                    ):
                        yield i

    def meta_parents(
        self, recursive: bool = False, check_type: str | type | None = None
    ) -> list[MetaBase]:
        """Returns a list of meta-parents for the current instance.

        The method collects and returns meta-parent objects associated with
        the current instance, considering optional filters such as recursion
        and type check.

        Notes:
            Metanode parents refer to the hierarchical parent(s) of the
            current object based on its metadata structure.

        Args:
            recursive: Specifies whether the method should recursively fetch
                metanode parents of the current object. If True, all parents
                in the hierarchy are returned.
            check_type: Specifies a type or a list of types to filter the
                metanode parents by. Only the metanode parents matching the
                provided type(s) will be included. If `None`, no type
                filtering is applied.

        Returns:
            A list of meta-parent objects that match the specified criteria.
        """

        return list(
            self.iterate_meta_parents(
                recursive=recursive, check_type=check_type
            )
        )

    def iterate_meta_children(
        self,
        depth_limit: int = 256,
        check_type: str | type | None = None,
        _visited: set[MetaBase] | None = None,
    ) -> Iterator[MetaBase]:
        """Iterate through the metanode children of the current object,
        yielding all valid children based on specified depth limit and type
        checks.

        This function traverses recursively through the hierarchical
        structure of metanode children while ensuring no duplicate nodes are
        visited in the iteration process.

        Args:
            depth_limit: The maximum depth to traverse through the metanode
                children. The default is 256. If set to 0 or a negative value,
                 further traversal stops.
            check_type: A type or class name to filter the meta-children.
                - If a type is provided, it checks against the class hierarchy
                    of the child.
                - If a string is provided, it matches against the name of the
                    class attribute.
                - If None, no filtering occurs.
            _visited: A set of already visited nodes to prevent infinite
                loops or redundant traversals.

        Yields:
            The metanode child object that satisfies the depth and type
                constraints.
        """

        is_type = inspect.isclass(check_type)
        child_plug = self.attribute(META_CHILDREN_ATTR_NAME)
        _visited = _visited or set()
        for element in child_plug:
            if depth_limit < 1:
                return
            # noinspection PyTypeChecker
            child: MetaBase = element.source()
            if child is None:
                continue
            child = child.node()
            if (
                not child.hasAttribute(META_CHILDREN_ATTR_NAME)
                or child in _visited
            ):
                continue
            _visited.add(child)
            child_meta = MetaBase(child.object(), init_defaults=False)
            if not check_type:
                yield child_meta
            else:
                if is_type and check_type in child_meta.__class__.mro():
                    yield child_meta
                elif (
                    isinstance(check_type, str)
                    and check_type
                    == child_meta.attribute(META_CLASS_ATTR_NAME).value()
                ):
                    yield child_meta
            for sub_child in child_meta.iterate_meta_children(
                depth_limit=depth_limit - 1,
                check_type=check_type,
                _visited=_visited,
            ):
                yield sub_child

    def meta_children(
        self, depth_limit: int = 256, check_type: str | type | None = None
    ) -> list[MetaBase]:
        """Iterate over metanode children and returns them as a list.

        The function explores metanode children up to a specified depth and
        optionally filters the results by a specific type.

        Args:
            depth_limit: The maximum depth to traverse while iterating over
                the metanode children.
            check_type: A specific type or class to filter the metanode
                children, or `None` to include all types.

        Returns:
            A list of metanode children matching the defined constraints by
            `depth_limit` and `check_type`.
        """

        return list(
            self.iterate_meta_children(
                depth_limit=depth_limit, check_type=check_type
            )
        )

    def get_upstream(
        self, check_type: type[MetaBase] | str
    ) -> MetaBase | None:
        """Find the first meta node of the given type upstream (toward parents).

        This method traverses up the meta node hierarchy (toward the root)
        looking for a node that matches the specified type.

        Args:
            check_type: The type to search for. Can be a MetaBase subclass
                or a string matching the metaclass type attribute.

        Returns:
            The first matching meta node found upstream, or None if not found.
        """

        for parent in self.iterate_meta_parents(
            recursive=True, check_type=check_type
        ):
            return parent
        return None

    def get_downstream(
        self, check_type: type[MetaBase] | str
    ) -> MetaBase | None:
        """Find the first meta node of the given type downstream (toward children).

        This method traverses down the meta node hierarchy (toward the leaves)
        looking for a node that matches the specified type.

        Args:
            check_type: The type to search for. Can be a MetaBase subclass
                or a string matching the metaclass type attribute.

        Returns:
            The first matching meta node found downstream, or None if not found.
        """

        for child in self.iterate_meta_children(check_type=check_type):
            return child
        return None

    def get_all_upstream(
        self, check_type: type[MetaBase] | str | None = None
    ) -> list[MetaBase]:
        """Find all meta nodes of the given type upstream (toward parents).

        This method traverses up the meta node hierarchy (toward the root)
        and returns all nodes that match the specified type.

        Args:
            check_type: The type to search for. Can be a MetaBase subclass,
                a string matching the metaclass type attribute, or None to
                return all upstream nodes.

        Returns:
            A list of all matching meta nodes found upstream.
        """

        return self.meta_parents(recursive=True, check_type=check_type)

    def get_all_downstream(
        self, check_type: type[MetaBase] | str | None = None
    ) -> list[MetaBase]:
        """Find all meta nodes of the given type downstream (toward children).

        This method traverses down the meta node hierarchy (toward the leaves)
        and returns all nodes that match the specified type.

        Args:
            check_type: The type to search for. Can be a MetaBase subclass,
                a string matching the metaclass type attribute, or None to
                return all downstream nodes.

        Returns:
            A list of all matching meta nodes found downstream.
        """

        return self.meta_children(check_type=check_type)

    def iterate_children(
        self, filter_types: set | None = None, include_meta: bool = False
    ) -> Iterator[DGNode | DagNode]:
        """Iterate over child nodes connected to the current node, applying
        optional filters to include only nodes of certain types or exclude
        metanodes.

        This method traverses the graph connections of the current node to
        yield child nodes based on the specified filtering criteria.

        The filtering can be based on specific node types and an option to
        exclude metanodes from the iteration.

        Args:
            filter_types: A set of node types to filter child nodes. Only nodes
                matching any of the provided types will be included.
                Defaults to `None`, which includes all node types.
            include_meta: A flag indicating whether metanodes should be
                included in the iteration. If False, metanodes are excluded.

        Yields:
            Child nodes connected to the current node that satisfy the
                specified filtering criteria.
        """

        filter_types = filter_types or ()
        for _, destination in self.iterateConnections(False, True):
            dest_node = destination.node()
            if not filter_types or any(
                dest_node.hasFn(i) for i in filter_types
            ):
                if not include_meta and is_meta_node(dest_node):
                    continue
                yield dest_node

    def find_children_by_class_type(
        self, class_type: str, depth_limit: int = 1
    ) -> list[MetaBase]:
        """Find and returns all children of the object that match the
        specified class type.

        This method iterates through the children of the current object up to
        a specified depth limit and filters them based on their metaclass
        type, returning those that match the provided `class_type`.

        Args:
            class_type: The name of the class type to match against the
                children's metaclass type.
            depth_limit: The maximum depth to search for matching children.

        Returns:
            A list of child objects that match the specified class type.
        """

        return [
            child
            for child in self.iterate_meta_children(depth_limit)
            if child.metaclass_type() == class_type
        ]

    def find_children_by_class_types(
        self, class_types: Iterable[str], depth_limit: int = 1
    ) -> list[MetaBase]:
        """Find and retrieves all child metadata objects whose metaclass types
        match the specified class types up to a given depth limit in the
        hierarchical structure.

        This method searches through all child metadata objects and filters
        them based on the provided class types. The depth of the search
        can be restricted using the `depth_limit` parameter, allowing
        for optimized and controlled hierarchy traversals.

        Args:
            class_types: An iterable collection of strings representing the
                metaclass types to match during the search.
            depth_limit: The maximum depth in the hierarchy to search
                for child metadata objects. Defaults to 1.

        Returns:
            A list containing all child metadata objects whose metaclass
                types match the specified class types within the given
                depth limit.

        """

        return [
            child
            for child in self.iterate_meta_children(depth_limit)
            if child.metaclass_type() in class_types
        ]

    def find_child_by_type(self, class_type: str) -> list[MetaBase]:
        """Find and return a list of child elements of a specific type.

        This method retrieves all child elements, considering only the
        immediate children (depth limit of 1), and filters them by their
        API type to match the specified type.

        Args:
            class_type: The type of the child elements to find, specified
            as a string.

        Returns:
            A list of child elements matching the specified class type.
        """

        return [
            child
            for child in self.iterate_meta_children(depth_limit=1)
            if child.apiType() == class_type
        ]

    def add_meta_child(
        self,
        child: MetaBase,
        mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
    ):
        """Adds a `MetaBase` instance as a child of the current `MetaBase`
        instance.

        Ensures that the given `child` MetaBase instance has the current
        instance as its parent in registry, updating its existing
        relationships if necessary.

        This function modifies the parent-child relationship structure within
        the Meta system.

        Args:
            child: The MetaBase instance to be set as a child of the
                current MetaBase instance.
            mod: An optional modifier to manage Maya dependency graph
                operations for this action.
        """

        child.remove_meta_parent(mod=mod)
        child.add_meta_parent(self, mod=mod)

    def add_meta_parent(
        self,
        parent: MetaBase,
        mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
    ):
        """Connect the current metanode to a parent metanode. This
        establishes a hierarchical relationship, allowing the current metanode
        to reference its parent.

        The method uses the given modifier to establish connections
        between the current node's parent attribute and the parent's
        children attribute, ensuring that it updates the parent and child
        relationships correctly.

        Args:
            parent: The parent meta node to which this node should be connected.
            mod: An optional Maya modifier used to manage dependency graph
                connections. If None, default connection behavior will be used.
        """

        parent_plug = self.attribute(META_PARENT_ATTR_NAME)
        next_element = parent_plug.nextAvailableElementPlug()
        next_element.connect(
            parent.attribute(
                META_CHILDREN_ATTR_NAME
            ).nextAvailableDestElementPlug(),
            mod=mod,
        )

    def remove_meta_parent(
        self,
        parent: MetaBase | None = None,
        mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
    ):
        """Remove the connection between the current instance's metaparent
        attribute and the specified parent or all connected metaparents if no
        specific parent is provided.

        The modification can be handled with a provided modifier or a
        default modifier that gets created internally.

        Args:
            parent: The specific meta parent to disconnect from.
                If None, all connected meta parents will be removed.
            mod: An optional modifier instance to handle the  disconnection.
                If None, a new MDGModifier instance will be created and used.
        """

        modifier = mod or OpenMaya.MDGModifier()
        parent_plug = self.attribute(META_PARENT_ATTR_NAME)
        parent_mobj = parent.object() if parent is not None else None
        for element in parent_plug:
            for dest in element.destinations():
                dest_node = dest.node()
                dest_mobj = dest_node.object()
                if parent is None or dest_mobj == parent_mobj:
                    element.disconnect(dest, mod=modifier, apply=True)

    def remove_all_meta_parents(self):
        """Remove all meta parent connections and deletes related connections.

        This method iterates over the meta parent attribute elements and
        disconnects all its destinations.

        Additionally, it attempts to delete each element after disconnection.
        If an element cannot be deleted, it suppresses the runtime error.
        """

        parent_plug = self.attribute(META_PARENT_ATTR_NAME)
        for element in parent_plug:
            for dest in element.destinations():
                element.disconnect(dest)
                try:
                    element.delete()
                except RuntimeError:
                    pass

    def find_children_by_tag(
        self, tag: str, depth_limit: int = 256
    ) -> list[MetaBase]:
        """Find and return all children with the specified tag.

        Args:
            tag: The tag string to search for.
            depth_limit: The maximum depth to search for matching children.

        Returns:
            A list of child objects that have the specified tag.
        """

        return [
            child
            for child in self.iterate_meta_children(depth_limit=depth_limit)
            if child.tag() == tag
        ]

    def to_dict(self, include_children: bool = False) -> dict[str, Any]:
        """Serialize the metanode data to a dictionary.

        This method exports the metanode's key attributes to a dictionary
        format, useful for debugging, logging, or data export.

        Args:
            include_children: If True, recursively includes child metanodes
                in the output.

        Returns:
            A dictionary representation of the metanode's data.
        """

        data: dict[str, Any] = {
            "name": self.name(),
            "class": self.metaclass_type(),
            "version": self.version(),
            "tag": self.tag(),
            "is_root": self.is_root(),
        }

        if include_children:
            data["children"] = [
                child.to_dict(include_children=True)
                for child in self.iterate_meta_children(depth_limit=1)
            ]

        return data

    def _init_meta(
        self, mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None
    ) -> list[Plug]:
        """Initialize meta-attributes by creating them from a dictionary and
        return the corresponding list of Plug objects.

        This function generates the required attributes for a specific
        operation or entity using a dictionary representation and ensures
        the attributes are instantiated with the appropriate modifiers if
        provided.

        Args:
            mod: An `instance of OpenMaya.MDGModifier`,
                `OpenMaya.MDagModifier`, `or` None. If provided, it is used
                to apply the modifications when creating attributes.

        Returns:
            A list of created Plug objects based on the meta-attributes
                defined in the dictionary.
        """

        return self.createAttributesFromDict(
            {k["name"]: k for k in self.meta_attributes()}, mod=mod
        )


def iterate_scene_meta_nodes() -> Iterator[MetaBase]:
    """Iterate through all scene metanodes and yields them as MetaBase objects.

    This function traverses all dependency nodes in the scene to identify those
    that have the specific meta-attribute defined by `META_CLASS_ATTR_NAME`.
    It yields a `MetaBase` object for each matching node, ensuring efficient
    and filtered access.

    Yields:
        An instance representing a metanode found in the dependency graph.
    """

    it = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kAffect)
    while not it.isDone():
        mobj = it.thisNode()
        dep = OpenMaya.MFnDependencyNode(mobj)
        if dep.hasAttribute(META_CLASS_ATTR_NAME):
            yield MetaBase(node=mobj, init_defaults=False)
        it.next()


def find_meta_nodes_by_class_type(class_type: type | str) -> list[MetaBase]:
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


def find_meta_nodes_by_tag(tag: str) -> list[MetaBase]:
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


def create_meta_node_by_type(
    type_name: str, *args: tuple, **kwargs
) -> MetaBase | None:
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


def connected_meta_nodes(node: DGNode) -> list[MetaBase]:
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

    if is_meta_node(node):
        if isinstance(node, DGNode):
            return [MetaBase(node=node.object(), init_defaults=False)]
        return [node]

    meta_nodes: list[MetaBase] = []
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
    node: DGNode,
    network_type: type[MetaBase] | None = None,
) -> list[MetaBase]:
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

    entries: list[MetaBase] = []

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


def delete_network(
    root: MetaBase, mod: OpenMaya.MDGModifier | None = None
) -> bool:
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


def get_all_meta_nodes_of_type(
    meta_type: type[MetaBase],
) -> list[MetaBase]:
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
