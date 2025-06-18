from __future__ import annotations

import json
import typing
from typing import cast
from collections.abc import Iterator

from loguru import logger

from tp.libs.maya.wrapper import DagNode
from tp.libs.python import helpers, profiler
from tp.libs.maya.meta.base import find_meta_nodes_by_class_type

from . import constants, errors
from .configuration import RigConfiguration
from ..services import naming
from ..meta.rig import MetaRig
from ..meta.moduleslayer import MetaModulesLayer

if typing.TYPE_CHECKING:
    from .module import Module
    from ..meta.module import MetaModule
    from ..descriptors.module import ModuleDescriptor
    from tp.libs.naming.manager import NameManager


class Rig:
    """Class that represents a Rig, encapsulating functionality for managing
    the rig's components, configuration, and modules.

    This class provides methods for rig creation, modification, and management.
    It interacts with metadata and manages modules that make up the rig's
    hierarchy. The class ensures that the rig is defined persistently and
    efficiently, with methods for serialization, naming, and session
    management.

    Attributes:
        _meta: The metanode instance of the rig.
        _config: The configuration of the rig.
    """

    def __init__(
        self, rig_config: RigConfiguration | None = None, meta: MetaRig | None = None
    ):
        """Initialize a new instance of the class with optional rig
        configuration and metadata while setting up initial attributes
        for module cache and configuration.

        Args:
            rig_config: Optional configuration for the rig.
                If not provided, a default `RigConfiguration` will be used.
            meta: Optional metadata for the rig.
        """

        super().__init__()

        self._meta = meta
        self._modules_cache: set[Module] = set()
        self._config = rig_config or RigConfiguration()

    def __bool__(self) -> bool:
        """Determine the truth value of the object based on its existence.

        This method overrides the built-in `__bool__` method to provide
        an evaluation of the object's truthiness. The return value is
        dependent on the result of the `exists` method, which checks
        whether the object satisfies specific conditions for existence.

        Returns:
            True if the object exists and satisfies conditions defined in the
            `exists` method, otherwise False.
        """

        return self.exists()

    def __eq__(self, other: Rig | None) -> bool:
        """Compares this instance of the Rig class with another instance or
        None to determine equality.

        The equality is determined based on the 'meta' attribute of the
        `Rig` class. If the 'other' parameter is None, the method will
        return False.

        Args:
            other: An instance of the Rig class or None to be compared
                with this instance.

        Returns:
            True if the 'meta' attributes of both instances are
                equal; False otherwise.
        """

        if not other:
            return False

        return self.meta == other.meta

    def __ne__(self, other: Rig | None) -> bool:
        """Compare the meta-node information of the current instance with
        another instance of the `Rig` class or checks against `None`.

        This method determines inequality between two `Rig` instances by
        comparing their meta-node property or between the current instance
        and `None`.

        Args:
            other: A `Rig` instance or `None` to compare the current
                instance against.

        Returns:
            True if the meta-node property of the current instance is not
            equal to the meta-node property of the provided `Rig` instance,
            or if the other is `None` or does not have a meta-node attribute;
            False otherwise.
        """

        return self._meta != other.meta

    def __hash__(self) -> int:
        """Compute the hash value for the object.

        This method generates a hash value based on the `_meta` attribute of
        the object.

        If the meta-node is `None`, it falls back to using the unique
        identifier of the object.

        Returns:
            The hash value of the object.
        """

        return hash(self._meta) if self._meta is not None else hash(id(self))

    def __repr__(self) -> str:
        """Provide a string representation of an object, intended for debugging
        and logging purposes. Produces a concise and human-readable description
        in a standard format to identify the object and its relevant details.

        Returns:
            A string representation of the object, including the class name
            and the value returned by the 'name' method.
        """

        return f"<{self.__class__.__name__}>(name={self.name()})"

    @property
    def meta(self) -> MetaRig | None:
        """The meta-node instance of the rig."""

        return self._meta

    @property
    def configuration(self) -> RigConfiguration:
        """The configuration of the rig."""

        return self._config

    def version_info(self) -> dict[str, str]:
        """Retrieve version information for the rig.

        This method fetches version information stored in a specific
        metadata attribute associated with the rig.

        Returns:
            A dictionary containing version information extracted from the
            rig's metadata. If the metadata is missing or invalid, an empty
            dictionary is returned.
        """

        if self._meta is None:
            return {}

        try:
            return json.loads(
                self._meta.attribute(constants.RIG_VERSION_INFO_ATTR).value()
            )
        except json.JSONDecodeError:
            return {}

    def naming_manager(self) -> NameManager:
        """Find and return the name manager for a specific type.

        This function uses the configuration property to locate the
        appropriate name manager for the provided type "rig".

        It ensures that the correct name manager is retrieved and returned
        to the caller.

        Returns:
            The name manager instance corresponding to the type "rig".
        """

        return self.configuration.find_name_manager_for_type("rig")

    def exists(self) -> bool:
        """Determine if the underlying metadata exists.

        This method checks the presence of the metadata attribute and verifies
        if the `exists` property of the metadata is `True`.

        Returns:
            True if metadata exists and is defined, otherwise False.
        """

        return self._meta is not None and self._meta.exists()

    def name(self) -> str:
        """Return the name of the rig if it exists, otherwise returns an
        empty string.

        This method checks whether the rig exists. If it does, the method
        retrieves the name of the rig using its metadata.

        Returns:
            The name of the rig if it exists, or an empty string if it
                does not.
        """

        return self._meta.rig_name() if self.exists() else ""

    def root_transform(self) -> DagNode | None:
        """Retrieve the root transform of the current rig if it exists,
        otherwise returns `None`.

        This is used to access the top-level transform node associated with
        the rig.

        Returns:
            The root transform group of the object if it exists,
                otherwise `None`.
        """

        return self._meta.root_transform() if self._meta.exists() else None

    def modules_layer(self) -> MetaModulesLayer | None:
        """Retrieve the module layer instance from this rig by querying the
        attached metanode.

        Returns:
            The module layer instance if the metanode exists; None otherwise.
        """

        return self._meta.modules_layer() if self._meta else None

    def get_or_create_modules_layer(self) -> MetaModulesLayer:
        """Get or create the module layer for the current instance.

        If a module layer does not already exist, this method initializes a new
        module layer with the appropriate naming and hierarchy information.

        The method ensures that the module layer is properly linked to the
        root transform of the metanode.

        Returns:
            The existing or newly created components layer for the current
                instance.
        """

        modules_layer = self.modules_layer()
        if not modules_layer:
            name_manager = self.naming_manager()
            hierarchy_name, meta_name = naming.compose_rig_names_for_layer(
                name_manager, self.name(), constants.MODULES_LAYER_TYPE
            )
            modules_layer = self._meta.create_layer(
                constants.MODULES_LAYER_TYPE,
                hierarchy_name=hierarchy_name,
                meta_name=meta_name,
                parent=self._meta.root_transform(),
            )

        return modules_layer

    def cached_configuration(self) -> dict:
        """Retrieve and cache the configuration data from a specific attribute.

        Returns:
            The parsed configuration data if available and valid, otherwise
            an empty dictionary.
        """

        config_plug = self._meta.attribute(constants.RIG_CONFIG_ATTR)
        try:
            config_data = config_plug.value()
            if config_data:
                return json.loads(config_data)
        except ValueError:
            pass

        return {}

    @profiler.fn_timer
    def save_configuration(self) -> dict:
        """Save the current rig configuration by serializing it and storing it
        in a designated attribute.

        It retrieves configuration data by serializing the current rig's
        state. If serialization is successful, the data is stored in the
        rig-specific configuration attribute in JSON format.

        Returns:
            A dictionary containing the serialized configuration data for the
            rig. The dictionary structure depends on the implementation of the
            `serialize` method used.
        """

        logger.debug("Saving rig configuration...")
        config_data = self.configuration.serialize(rig=self)
        if config_data:
            config_plug = self._meta.attribute(constants.RIG_CONFIG_ATTR)
            config_plug.set(json.dumps(config_data))

        return config_data

    @profiler.fn_timer
    def start_session(
        self, name: str | None = None, namespace: str | None = None
    ) -> MetaRig:
        """Start a session by either finding an existing rig or creating a
        new one.

        The method first attempts to find a rig in the scene based on the
        provided name and namespace. If such a rig exists, it initializes the
        configuration from the found rig. If no existing rig is found, a new
        rig instance is created using the naming manager.

        Args:
            name: The name of the rig to find or create. If None, the search
                will not filter by name.
            namespace: The namespace of the rig to find or create. If None,
                the search will not filter by namespace.

        Returns:
            Either the found or newly created rig instance.
        """

        meta = self._meta
        if meta is None:
            meta = root_rig_by_name(name, namespace=namespace)
        if meta is not None:
            self._meta = meta
            logger.debug(f"Found rig in scene with name: {self.name()}")
            self.configuration.update_from_rig(self)
            return self._meta

        namer = self.naming_manager()
        meta = MetaRig(name=namer.resolve("rigMeta", {"rigName": name, "type": "meta"}))
        meta.attribute(constants.NAME_ATTR).set(name)
        meta.attribute(constants.ID_ATTR).set(name)
        meta.create_transform(namer.resolve("rigHrc", {"rigName": name, "type": "hrc"}))
        meta.create_selection_sets(namer)
        self._meta = meta

        return self._meta

    @profiler.fn_timer
    def create_module(
        self,
        module_type: str | None = None,
        name: str | None = None,
        side: str | None = None,
        descriptor: ModuleDescriptor | None = None,
    ) -> Module:
        """Add a new module instance to this rig and creates the structure for
        that module.

        Args:
            module_type: Type of the module to create.
            name: Name of the new module.
            side: Side of the new module. Defaults to "M" (middle).
            descriptor: Module descriptor to use for the new module.
                This is used to provide a pre-defined configuration for the
                module, including its type, name, and side.

        Returns:
            Newly created module instance.
        """

        if descriptor:
            module_type = module_type or descriptor.type
            name = name or descriptor.name
            side = side or descriptor.side
        else:
            descriptor = self.configuration.initialize_module_descriptor(module_type)

        component_class = (
            self.configuration.modules_manager().find_module_class_by_type(module_type)
        )
        if not component_class:
            raise errors.MissingModuleType(module_type)

        name = name or descriptor.name
        side = side or descriptor.side
        unique_name = naming.unique_name_for_module_by_rig(self, name, side)
        modules_layer = self.get_or_create_modules_layer()

        descriptor.side = side
        descriptor.name = unique_name
        new_module = component_class(rig=self, descriptor=descriptor)
        new_module.create(parent=modules_layer)
        self._modules_cache.add(new_module)

        return new_module

    def has_module(self, name: str, side: str = "M") -> bool:
        """Return whether a module with the provided name and side exists
        for this rig instance.

        Args:
            name: Name of the module to check.
            side: Side of the module to check. Defaults to "M" (middle).

        Returns:
            True if a module with the given name and side exists for this
            rig; False otherwise.
        """

        for module_found in self.iterate_modules():
            if module_found.name() == name and module_found.side() == side:
                return True

        return False

    def iterate_root_modules(self) -> Iterator[Module]:
        """Iterate through all root modules within a collection of modules.

        Notes:
            A root module is defined as a module that does not have a parent
            module.

        Returns:
            An iterator over root modules.
        """

        for found_module in self.iterate_modules():
            if not found_module.has_parent():
                yield found_module

    def iterate_modules(self) -> Iterator[Module]:
        """Iterate through and retrieves all the modules associated with the
        current instance.

        The method ensures valid modules are cached and fetches modules not
        yet visited.

        This includes both cached modules and dynamically fetched modules
        from the module layer.

        Any errors encountered during module initialization are logged, and
        a custom exception is raised for initialization failures.

        Yields:
            Module: The next valid module in the iteration process.

        Raises:
            InitializeModuleError: If a module fails to initialize from
                its meta-node.
        """

        found_modules: set[Module] = set()
        visited_meta: set[MetaModule] = set()

        for cached_module in self._modules_cache:
            if not cached_module.exists():
                continue
            found_modules.add(cached_module)
            visited_meta.add(cached_module.meta)
            yield cached_module

        self._modules_cache = found_modules

        modules_layer = self.modules_layer()
        if modules_layer is None:
            return

        modules_manager = self.configuration.modules_manager()
        for module_metanode in modules_layer.iterate_components():
            try:
                if module_metanode in visited_meta:
                    continue
                found_module = modules_manager.from_meta_node(
                    rig=self, meta=module_metanode
                )
                found_modules.add(found_module)
                visited_meta.add(found_module.meta)
                yield found_module
            except ValueError:
                logger.error(
                    f"Failed to initialize module: {module_metanode.name()}",
                    exc_info=True,
                )
                raise errors.InitializeModuleError(module_metanode.name())

    def modules(self) -> list[Module]:
        """Retrieve a list of all module components managed by the instance.

        This method aggregates all module components by iterating through them
        using the `iterate_components` method and consolidating them into a
        list.

        The resulting list provides an overview of all modules currently handled
        by the instance, enabling further operations or inspections.

        Returns:
            A list containing all module components present within the instance.
        """

        return list(self.iterate_modules())

    def iterate_components_by_type(self, component_type: str) -> Iterator[Component]:
        """Generator function that yields all components of the given type name.

        :param component_type: Noddle component type name.
        :return: iterated components of the given type.
        """

        for found_component in self.iterate_components():
            if found_component.component_type == component_type:
                yield found_component

    def component(self, name: str, side: str = "M") -> Component | None:
        """Tries to find the component by name and side by first check the component cache for this rig instance and
        after that checking the components via meta node network.

        :param name: component name to find.
        :param side: component side to find.
        :return: found component instance.
        """

        found_component: Component | None = None
        for cached_component in list(self._components_cache):
            if cached_component.name() == name and cached_component.side() == side:
                found_component = cached_component
                break
        if found_component is not None:
            return found_component

        components_layer = self.get_or_create_components_layer()
        if components_layer is None:
            return None

        components_manager = self.configuration.components_manager()
        for component_metanode in components_layer.iterate_components():
            component_name = component_metanode.attribute(consts.NAME_ATTR).asString()
            component_side = component_metanode.attribute(consts.SIDE_ATTR).asString()
            if component_name == name and component_side == side:
                component_instance = components_manager.from_meta_node(
                    rig=self, meta=component_metanode
                )
                self._components_cache.add(component_instance)
                return component_instance

        return None

    def component_from_node(self, node: DGNode | OpenMaya.MObject) -> Component | None:
        """Returns the component for the given node if it's part of this rig.

        :param node: node to get the component from.
        :return: component instance.
        :raises NoddleMissingMetaNode: If the given node does not have a meta node.
        """

        meta_node = component_meta_node_from_node(node)
        if not meta_node:
            raise errors.NoddleMissingMetaNode(node)

        return self.component(
            meta_node.attribute(consts.NAME_ATTR).value(),
            meta_node.attribute(consts.SIDE_ATTR).value(),
        )


def iterate_scene_rig_meta_nodes() -> Iterator[MetaRig]:
    """Iterate over all meta-nodes of the type `ModRig`.

    This function finds all meta-nodes that match the specific `RIG_TYPE`
    and yields them as `ModRig` objects.

    Yields:
        An iterator over meta-nodes of the type `ModRig`.
    """

    for found_meta_rig in find_meta_nodes_by_class_type(constants.RIG_TYPE):
        yield cast(MetaRig, found_meta_rig)


def iterate_scene_rigs() -> Iterator[Rig]:
    """Iterate over all rig meta-nodes in the scene and yields instantiated
    rig objects.

    This function scans through all meta-nodes representing rigs in the scene,
    instantiates them as `Rig` objects, starts a session for each rig, and
    yields the resulting rig object.

    Yields:
        Rig: An instance of `Rig` initialized with the corresponding meta-node,
        with an active session started.
    """

    for meta_rig in iterate_scene_rig_meta_nodes():
        rig_instance = Rig(meta=meta_rig)
        rig_instance.start_session()
        yield rig_instance


def root_rig_by_name(name: str, namespace: str | None = None) -> MetaRig | None:
    """Retrieve the root `ModRig` instance in the scene based on its name and
    optional namespace.

    This function iterates through rig meta-nodes in the scene and attempts to
    locate a single root `ModRig` instance that matches the given name. If a
    namespace is provided, it further refines the search to locate a match
    within the given  namespace.

    Args:
        name: The name of the `ModRig` to locate.
        namespace: The optional namespace to refine the search. If None,
            the search is conducted across the entire scene.

    Returns:
        Returns the `ModRig` instance if found; `None` otherwise.

    Raises:
        RigDuplicationError: If multiple rigs with the same name exist and
            no namespace is provided.
    """

    meta_rigs: list[MetaRig] = []
    meta_rig_names: list[str] = []

    found_meta_rig: MetaRig | None = None
    for meta_node in iterate_scene_rig_meta_nodes():
        meta_rigs.append(meta_node)
        meta_rig_names.append(meta_node.attribute(constants.NAME_ATTR).value())
    if not meta_rigs:
        return None

    if not namespace:
        dupes = helpers.duplicates_in_list(meta_rig_names)
        if dupes:
            raise errors.RigDuplicationError(dupes)
        for meta_rig in meta_rigs:
            if meta_rig.attribute(constants.NAME_ATTR).value() == name:
                found_meta_rig = meta_rig
                break

    if found_meta_rig is None and namespace:
        namespace = namespace if namespace.startswith(":") else f":{namespace}"
        for meta_rig in meta_rigs:
            rig_namespace = meta_rig.namespace()
            if (
                rig_namespace == namespace
                and meta_rig.attribute(constants.NAME_ATTR).value() == name
            ):
                found_meta_rig = meta_rig
                break

    return found_meta_rig
