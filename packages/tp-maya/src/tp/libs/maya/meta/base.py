from __future__ import annotations

import os
import inspect
from typing import Any
from types import ModuleType
from collections.abc import Iterator, Iterable

from loguru import logger
from maya.api import OpenMaya

from tp.libs.python import modules
from tp.libs.python.decorators import Singleton

from ..om import attributetypes
from ..wrapper import DGNode, DagNode, Plug

META_CLASS_ATTR_NAME = "tpMetaClass"
META_VERSION_ATTR_NAME = "tpMetaVersion"
META_PARENT_ATTR_NAME = "tpMetaParent"
META_CHILDREN_ATTR_NAME = "tpMetaChildren"
META_TAG_ATTR_NAME = "tpMetaTag"


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
            logger.debug(f"Registering MetaClass -> {registry_name} | {class_obj}")
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

        for member in modules.iterate_module_members(module, predicate=inspect.isclass):
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
            raise ValueError(f'No environment variable with name "{env_name}" exists!')

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

        node: DGNode | DagNode | MetaBase | OpenMaya.MObject | None = kwargs.get("node")
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

        # noinspection PyUnresolvedReferences
        registered_type = MetaRegistry().get_type(class_type)
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
        DEFAULT_NAME: Default name used when creating a metanode instance.
            `None` indicates no default name is defined.
    """

    ID: str | None = None
    DEFAULT_NAME: str | None = None

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
                    [MetaRegistry.registry_name_for_class(self.__class__), "meta"]
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
            The class name derived from the node's attribute or plug.
        """

        if isinstance(node, MetaBase):
            return node.attribute(META_CLASS_ATTR_NAME).value()
        dep = OpenMaya.MFnDependencyNode(node)
        try:
            return dep.findPlug(META_CLASS_ATTR_NAME, False).asString()
        except RuntimeError as exc:
            return str(exc)

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
                "value": "1.0.0",
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
        ]

    def metaclass_type(self) -> str:
        """Return the metaclass type associated with the instance.

        This function retrieves the value of the metaclass attribute
        represented by the constant `META_CLASS_ATTR_NAME`.

        Returns:
            The value of the metaclass attribute.
        """

        return self.attribute(META_CLASS_ATTR_NAME).value()

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
            return True

        return False

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
                attribute_name, value=None, type=attributetypes.kMFnMessageAttribute
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
                parent_meta = MetaBase(dest.node().object(), init_defaults=False)
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
                    for i in parent_meta.iterate_meta_parents(recursive=recursive):
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
            self.iterate_meta_parents(recursive=recursive, check_type=check_type)
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
            if not child.hasAttribute(META_CHILDREN_ATTR_NAME) or child in _visited:
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
                    and check_type == child_meta.attribute(META_CLASS_ATTR_NAME).value()
                ):
                    yield child_meta
            for sub_child in child_meta.iterate_meta_children(
                depth_limit=depth_limit - 1, check_type=check_type, _visited=_visited
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
            self.iterate_meta_children(depth_limit=depth_limit, check_type=check_type)
        )

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
            if not filter_types or any(dest_node.hasFn(i) for i in filter_types):
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
            parent.attribute(META_CHILDREN_ATTR_NAME).nextAvailableDestElementPlug(),
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
        for element in parent_plug:
            for dest in element.destinations():
                n = dest.node()
                if parent is None or n == parent:
                    element.disconnect(dest, mod=modifier, apply=False)
        if mod is None:
            modifier.doIt()

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

    class_type_name = str(class_type)
    if inspect.isclass(class_type):
        # noinspection PyUnresolvedReferences
        class_type_name = class_type.ID

    return [
        meta_node
        for meta_node in iterate_scene_meta_nodes()
        if meta_node.attribute(META_CLASS_ATTR_NAME).value() == class_type_name
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

    return MetaRegistry.is_in_registry(node.attribute(META_CLASS_ATTR_NAME).asString())


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


def create_meta_node_by_type(type_name: str, *args: tuple, **kwargs) -> MetaBase | None:
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
            "Ensure the type is registered in the `MetaRegistry`."
            f"Available types: {MetaRegistry()._CACHE}"
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
