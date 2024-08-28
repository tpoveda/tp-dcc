from __future__ import annotations

import os
import logging
import inspect
from types import ModuleType
from typing import Type, Iterable, Iterator, Any

from maya.api import OpenMaya

from ..om import attributetypes
from ..wrapper import DGNode, DagNode, Plug
from ...python import modules
from ...python.decorators import Singleton

logger = logging.getLogger(__name__)

META_CLASS_ATTR_NAME = "tpMetaClass"
META_VERSION_ATTR_NAME = "tpMetaVersion"
META_PARENT_ATTR_NAME = "tpMetaParent"
META_CHILDREN_ATTR_NAME = "tpMetaChildren"
META_TAG_ATTR_NAME = "tpMetaTag"


class MetaRegistry(metaclass=Singleton):
    """
    Singleton class that handles global registry of all available metaclasses.
    """

    META_ENV_VAR = "TP_DCC_META_PATHS"
    _CACHE: dict[str, Type[MetaBase]] = {}

    def __init__(self):
        super().__init__()

        try:
            self.reload()
        except ValueError:
            logger.error("Failed to registry meta classe", exc_info=True)

    @staticmethod
    def registry_name_for_class(class_type: Type[MetaBase]) -> str:
        """
        Returns the metaclass name used by the register.

        :param Type class_type: metaclass type to get name of.
        :return: name of the metaclass.
        :rtype: str
        """

        return class_type.ID or class_type.__name__

    @classmethod
    def is_in_registry(cls, type_name: str) -> bool:
        """
        Returns whether the given type is currently available within the registry.

        :param type_name: name of type to check.
        :return: True if the type is already registered; False otherwise.
        """

        return type_name in cls._CACHE

    @classmethod
    def get_type(cls, type_name: str) -> Type[MetaBase] | None:
        """
        Returns the class of the type.

        :param type_name: class name.
        :return: class object for the given type name.
        """

        return cls._CACHE.get(type_name)

    @classmethod
    def register_meta_class(cls, class_obj: Type[MetaBase]):
        """
        Registers a metaclass with the registry.
        :param class_obj: metaclass to register.
        """

        if issubclass(class_obj, MetaBase) or isinstance(class_obj, MetaBase):
            # noinspection PyTypeChecker
            registry_name = cls.registry_name_for_class(class_obj)
            if registry_name in cls._CACHE:
                return
            logger.debug(f"Registering MetaClass -> {registry_name} | {class_obj}")
            # noinspection PyTypeChecker
            cls._CACHE[registry_name] = class_obj

    @classmethod
    def register_by_package(cls, package_path: str):
        """
        Registers given package path into the meta registry.

        :param package_path: package path to register (e.g. tp.core)
        .warning:: this function is expensive as it requires a recursive search by importing all submodules.
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
        """
        Registers a module by searching all class members of the module and registers any class that is an instance
        of the MetaBase class.

        :param module: module to register.
        """

        if not inspect.ismodule(module):
            return

        for member in modules.iterate_module_members(module, predicate=inspect.isclass):
            cls.register_meta_class(member[1])

    @classmethod
    def register_meta_classes(cls, paths: Iterable[str]):
        """
        Registers given paths within the meta registry.

        :param paths: list of module or package paths.
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
        """
        Registers a set of metaclass based on the given environment variable.

        :param env_name: environment variable name.
        :raises ValueError: If environment variable with given name does not exist.
        """

        environment_paths = os.getenv(env_name)
        if environment_paths is None:
            raise ValueError(f'No environment variable with name "{env_name}" exists!')

        environment_paths = environment_paths.split(os.pathsep)

        cls.register_meta_classes(environment_paths)

    def reload(self):
        """
        Reloads meta register based on MetaRegistry environment variable.
        """

        self.register_by_env(MetaRegistry.META_ENV_VAR)


class MetaFactory(type):
    """
    A metaclass that manages the instantiation of classes, providing dynamic registration and retrieval based on
    a given node.

    This metaclass ensures that classes are registered in MetaRegistry before instantiation and can dynamically
    return instances of registered subclasses based on the node provided.
    """

    def __call__(cls: Type[MetaBase], *args, **kwargs):
        """
        Overrides the __call__ method to manage instantiation based on class registration
        and node type. Returns an instance of the appropriate class or subclass.

        :param cls: the class being instantiated.
        :param args: positional arguments passed to the class constructor.
        :param kwargs: keyword arguments passed to the class constructor.
        :return: An instance of `cls` or a registered subclass based on the provided node.
        """

        node: DGNode | DagNode | MetaBase | OpenMaya.MObject | None = kwargs.get("node")
        if args:
            node = args[0]

        register = MetaRegistry

        # if the given class is not registered, we register it
        registry_name = MetaRegistry.registry_name_for_class(cls)
        if not register.is_in_registry(registry_name):
            register.register_meta_class(cls)

        if not node:
            return type.__call__(cls, *args, **kwargs)

        class_type = MetaBase.class_name_from_plug(node)
        if class_type == registry_name:
            return type.__call__(cls, *args, **kwargs)

        registered_type = MetaRegistry().get_type(class_type)
        if registered_type is None:
            return type.__call__(cls, *args, **kwargs)

        return type.__call__(registered_type, *args, **kwargs)


class MetaBase(DGNode, metaclass=MetaFactory):
    """
    Base class for meta nodes.
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
        """
        Initializes the MetaBase class.

        :param node: node instance this meta node will reference to.
        :param name: name of the meta node in the scene.
        :param namespace: optional namespace for the meta node.
        :param init_defaults: whether to initialize meta defaults.
        :param lock: whether to lock meta node instance after building it.
        :param mod: optional Maya modifier used to create and to lock the node if necessary.
        :param args: positional arguments passed to the setup function.
        :param kwargs: keyword arguments passed to the setup function.
        """

        # noinspection PyArgumentList
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
        """
        Returns the string representation of the node.

        :return: string representation.
        """

        return f"{self.as_str(name_only=True)} ({self.name()})"

    @classmethod
    def as_str(cls, name_only: bool = False) -> str:
        """
        Returns a string representation of this metaclass path.

        :param bool name_only: whether to only return the name of metaclass.
        :return: metaclass path representation
        :rtype: str
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
        """
        From the given Maya object or Meta clas instance, returns the associated class name which should exists on the
        Maya node as an attribute.

        :param OpenMaya.MObject or MetaBase node: node to find class name for.
        :return: metaclass name.
        :rtype: str
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
        """
        Overrides delete function.
        Deletes the node from the scene.

        :param mod: modifier to add the delete operation into.
        :param apply: whether to apply the modifier immediately.
        :return: True if the node deletion was successful; False otherwise.
        :raises RuntimeError: if deletion operation fails.
        """

        child_plug = self.attribute(META_CHILDREN_ATTR_NAME)
        for element in child_plug:
            element.disconnectAll(mod=mod)

        return super().delete(mod=mod, apply=apply)

    def setup(self, *args: Any, **kwargs: Any):
        """
        Function that is called after the create function is called.
        Can be used to customize the way a meta node is constructed.

        :param args: list of positional arguments.
        :param kwargs: dictionary of keyword arguments.
        """

        pass

    def meta_attributes(self) -> list[dict]:
        """
        Returns the list of default meta attributes that should be added into the meta node during creation.

        :return: list of attributes data within a dictionary.
        :rtype: List[Dict]
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
        """
        Returns metaclass for this meta node instance.

        :return: meta node instance type.
        """

        return self.attribute(META_CLASS_ATTR_NAME).value()

    def is_root(self) -> bool:
        """
        Returns whether this meta node instance is a root one.

        :return: True if this meta node instance is connected to a meta parent node; False otherwise.
        """

        for _ in self.iterate_meta_parents():
            return True

        return False

    def connect_to(self, attribute_name: str, node: DGNode) -> Plug:
        """
        Connects given node to the message attribute with given name.

        :param attribute_name: name of the attribute to connect from. If the attribute does not exist, it will
            be created automatically.
        :param node: destination node.
        :return: destination plug.
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
        """
        Connects given node to the message attribute of the given plug instance.

        :param destination_plug: target plug to connect.
        :param node: destination node.
        :return: destination plug.
        """

        source_plug = node.attribute("message")
        source_plug.connect(destination_plug)

        return destination_plug

    def meta_root(self) -> MetaBase | None:
        """
        Returns the first meta parent this meta node instance is connected to.

        :return: first meta node parent.
        :rtype: MetaBase or None
        """

        for current_parent in self.iterate_meta_parents(recursive=True):
            parents = list(current_parent.iterate_meta_parents(recursive=True))
            if not parents:
                return current_parent

        return None

    def meta_parent(self) -> MetaBase | None:
        """
        Returns direct meta parent for this meta node.

        :return: first direct meta parent.
        """

        meta_parents = list(self.iterate_meta_parents(recursive=False))
        return meta_parents[0] if meta_parents else None

    def iterate_meta_parents(
        self, recursive: bool = False, check_type: str | Type | None = None
    ) -> Iterator[MetaBase]:
        """
        Generator function that iterates over all meta parent nodes this node is linked to.

        :param recursive: whether to find meta parents in a recursive manner.
        :param check_type: meta node type to search for.
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
        self, recursive: bool = False, check_type: str | Type | None = None
    ) -> list[MetaBase]:
        """
        Returns all meta parent nodes this node is linked to.

        :param recursive: whether to find meta parents in a recursive manner.
        :param check_type: meta node type to search for.
        :return: list of meta parent nodes.
        """

        return list(
            self.iterate_meta_parents(recursive=recursive, check_type=check_type)
        )

    def iterate_meta_children(
        self,
        depth_limit: int = 256,
        check_type: str | Type | None = None,
        _visited: set[MetaBase] | None = None,
    ) -> Iterator[MetaBase]:
        """
        Generator function that yields all children meta node instances connected to the metaChildren plug of this meta
        node instance.

        :param depth_limit: recursive depth limit.
        :param check_type: meta node type to search for.
        :param _visited: internal list of visited nodes.
        :return: iterated meta children.
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
        self, depth_limit: int = 256, check_type: str | Type | None = None
    ) -> list[MetaBase]:
        """
        Returns all children meta node instances connected to the metaChildren plug of this meta node instance.

        :param depth_limit: recursive depth limit.
        :param check_type: meta node type to search for.
        :return: meta children.
        """

        return list(
            self.iterate_meta_children(depth_limit=depth_limit, check_type=check_type)
        )

    def iterate_children(
        self, filter_types: set | None = None, include_meta: bool = False
    ) -> Iterator[DGNode | DagNode]:
        """
        Generator function that iterates over all children nodes.

        :param filter_types: optional lister of node filter types.
        :param include_meta: whether to include children meta nodes.
        :return: iterated DG/Dag nodes.
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
        """
        Finds all meta node children of the given type.

        :param class_type: metaclass type name.
        :param depth_limit: recursive depth limit.
        :return: iterable of meta node children instances found of given type.
        """

        return [
            child
            for child in self.iterate_meta_children(depth_limit)
            if child.metaclass_type() == class_type
        ]

    def find_children_by_class_types(
        self, class_types: Iterable[str], depth_limit: int = 1
    ) -> list[MetaBase]:
        """
        Finds all meta node children of the given types.

        :param class_types: metaclass type names.
        :param depth_limit: recursive depth limit.
        :return: iterable of meta node children instances found of given type.
        """

        return [
            child
            for child in self.iterate_meta_children(depth_limit)
            if child.metaclass_type() in class_types
        ]

    def find_child_by_type(self, class_type: str):
        """
        Finds the first child of the given type.

        :param class_type: metaclass type name.
        :return: first child of the given type.
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
        """
        Adds a new meta child to this meta node instance.

        :param child: meta child.
        :param mod: optional Maya modifier to use.
        """

        child.remove_meta_parent(mod=mod)
        child.add_meta_parent(self, mod=mod)

    def add_meta_parent(
        self,
        parent: MetaBase,
        mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None,
    ):
        """
        Sets the parent meta node for this meta node instance and removes the previous meta parent if it is already
        defined.

        :param parent: parent meta node instance.
        :param mod: optional Maya modifier to use.
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
    ) -> bool:
        """
        Removes meta parent for this meta node instance.

        :param MetaBase or None parent: optional meta parent to remove; if None, all meta parents will be removed.
        :param OpenMaya.MDagModifier or OpenMaya.MDGModifier or None mod: optional Maya modifier to use.
        :return: True if the remove meta parent operation was successful; False otherwise.
        :rtype :bool
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

        return True

    def remove_all_meta_parents(self) -> bool:
        """
        Removes all meta parents for this meta node instance.
        :return: True if the remove meta parents operation was successful; False otherwise.
        :rtype :bool
        """

        parent_plug = self.attribute(META_PARENT_ATTR_NAME)
        for element in parent_plug:
            for dest in element.destinations():
                element.disconnect(dest)
                try:
                    element.delete()
                except RuntimeError:
                    pass

        return True

    def _init_meta(
        self, mod: OpenMaya.MDGModifier | OpenMaya.MDagModifier | None = None
    ) -> list[Plug]:
        """
        Internal function that initializes standard attributes for the meta node.

        :param mod: optional Maya modifier to add to.
        :return: list of created attributes.
        """

        return self.createAttributesFromDict(
            {k["name"]: k for k in self.meta_attributes()}, mod=mod
        )


def iterate_scene_meta_nodes() -> Iterator[MetaBase]:
    """
    Generator function that iterates over all meta nodes in the current Maya scene.

    :return: found meta node instances within current Maya scene.
    """

    it = OpenMaya.MItDependencyNodes(OpenMaya.MFn.kAffect)
    while not it.isDone():
        mobj = it.thisNode()
        dep = OpenMaya.MFnDependencyNode(mobj)
        if dep.hasAttribute(META_CLASS_ATTR_NAME):
            yield MetaBase(node=mobj)
        it.next()


def find_meta_nodes_by_class_type(class_type: Type | str) -> list[MetaBase]:
    """
    Generator function that returns all meta nodes within current scene with given meta type.

    :param class_type: metaclass type.
    :return: generator of found meta nodes with given metaclass type.
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
    """
    Returns whether given node is a meta node.

    :param base.DGNode node: node to check.
    :return: True if given node is a meta node ; False otherwise.
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
    """
    Returns whether given node is a meta node of given types.

    :param base.DGNode node: node to check.
    :param class_types: list of metaclass types.
    :return: True if given node is a meta node of given types; False otherwise.
    """

    if not is_meta_node(node):
        return False

    type_str = node.attribute(META_CLASS_ATTR_NAME).asString()
    if type_str not in class_types:
        return False

    return MetaRegistry.is_in_registry(type_str)


def create_meta_node_by_type(type_name: str, *args: tuple, **kwargs) -> MetaBase | None:
    """
    Creates a new meta node instance within current scene and returns the type class instance from the meta registry.

    :param str type_name: metaclass type to create.
    :param tuple args: args to pass to the class.__init__ function.
    :return: subclass instance of MetaBase for the type.
    :rtype: MetaBase or None
    """

    class_type = MetaRegistry().get_type(type_name)
    return class_type(*args, **kwargs) if class_type is not None else None
