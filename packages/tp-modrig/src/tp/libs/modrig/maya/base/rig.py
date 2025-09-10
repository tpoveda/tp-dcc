from __future__ import annotations

import json
import typing
from typing import cast, Any
from collections.abc import Iterator
from contextlib import contextmanager

from loguru import logger
from maya.api import OpenMaya

from tp.libs.python import helpers, profiler
from tp.libs.maya.wrapper import DGNode, DagNode
from tp.libs.maya.meta.base import (
    MetaBase,
    find_meta_nodes_by_class_type,
    is_meta_node,
    connected_meta_nodes,
)

from . import constants, errors
from .configuration import RigConfiguration
from ..services import naming
from ..meta.rig import MetaRig
from ..meta.layers import MetaModulesLayer
from .utils.module_utils import disconnect_module_context

if typing.TYPE_CHECKING:
    from .module import Module
    from ..meta.module import MetaModule
    from ..descriptors.module import ModuleDescriptor
    from tp.libs.naming.manager import NameManager


class Rig:
    """Class that represents a Rig, encapsulating functionality for managing
    the rig's modules and configuration.

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
        self,
        rig_config: RigConfiguration | None = None,
        meta: MetaRig | None = None,
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

    def __contains__(self, item: Module) -> bool:
        """Check if the given module is contained within the object.

        This method determines whether a module with the specified name and
        side exists.

        Args:
            item: The module to check for its presence.

        Returns:
            True if the module is contained, False otherwise.
        """

        return bool(self.module(item.name(), item.side()))

    def __len__(self) -> int:
        """Calculate the total number of modules within the current rig.

        Returns:
            The number of modules in the current rig.
        """

        return len(self.modules())

    def __getattr__(self, item: str) -> typing.Any:
        """Handles dynamic attribute access allowing to retrieve modules
        dynamically based on structured attribute names following
        the `<module_name>_<side>` format.

        Notes:
            Lines with underscore-prefixed attributes, single-word attributes,
            or unrelated name formats will fall back to the default attribute
            retrieval mechanism.

        Args:
            item: The name of the attribute being accessed. The format can
                either represent structured module information or a
                simple attribute name.

        Returns:
            The dynamically resolved module matching the specified attribute
            name, or the result of the default `__getattribute__` if no valid
            module is found.
        """

        if item.startswith("_"):
            return super().__getattribute__(item)

        splitter = item.split("_")
        if len(splitter) < 2:
            return super().__getattribute__(item)

        module_name = "_".join(splitter[:-1])
        side = splitter[-1]
        found_module = self.module(module_name, side)
        if found_module is not None:
            return found_module

        return super().__getattribute__(item)

    # === Configuration === #

    @property
    def configuration(self) -> RigConfiguration:
        """The configuration of the rig."""

        return self._config

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

    # === Lifecycle === #

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
    def delete(self, delete_joints: bool = True) -> bool:
        """Delete the entire rig structure, including all associated modules
        and the root transform.

        Args:
            delete_joints: Whether to delete joints in the skeleton layer.

        Returns:
            `True` if the deletion was successful; `False` otherwise.
        """

        self.delete_modules()

        with self.build_script_context(constants.BuildScriptFunctionType.DeleteRig):
            root = self._meta.root_transform()
            self.delete_control_display_layer()
            for layer in self._meta.layers():
                if layer.id == constants.SKELETON_LAYER_TYPE:
                    layer.delete(delete_joints=delete_joints)
                    continue
                layer.delete()
            root.delete()
            self._meta.delete()

        return True

    def delete_control_display_layer(self) -> bool:
        """Delete the current control display layer for the rig.

        Returns:
            `True` if the control display layer was successfully deleted,
                `False` otherwise.
        """

        return self._meta.delete_control_display_layer() if self.exists() else False

    # region === Meta === #

    @property
    def meta(self) -> MetaRig | None:
        """The meta-node instance of the rig."""

        return self._meta

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

    # region === Modules === #

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
            The existing or newly created modules layer for the current
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
            descriptor, _ = self.configuration.initialize_module_descriptor(module_type)

        module_class = self.configuration.modules_manager().find_module_class_by_type(
            module_type
        )
        if not module_class:
            raise errors.MissingModuleType(module_type)

        name = name or descriptor.name
        side = side or descriptor.side
        unique_name = naming.unique_name_for_module_by_rig(self, name, side)
        modules_layer = self.get_or_create_modules_layer()

        descriptor.side = side
        descriptor.name = unique_name
        new_module = module_class(rig=self, descriptor=descriptor)
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

    def root_modules(self) -> list[Module]:
        """Retrieve a list of all root modules within the current instance.

        A root module is defined as a module that does not have a parent
        module.

        Returns:
            A list containing all root modules.
        """

        return list(self.iterate_root_modules())

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
        for module_metanode in modules_layer.iterate_modules():
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
        """Retrieve a list of all modules managed by the instance.

        This method aggregates all modules by iterating through them
        using the `iterate_modules` method and consolidating them into a
        list.

        The resulting list provides an overview of all modules currently handled
        by the instance, enabling further operations or inspections.

        Returns:
            A list containing all modules present within the instance.
        """

        return list(self.iterate_modules())

    def iterate_modules_by_type(self, module_type_name: str) -> Iterator[Module]:
        """Iterate over modules of a specific type and yields matching modules.

        Inspects all available modules and filters them by their module
        type. For every module whose module type matches the provided type,
        the function yields the module.

        Args:
            module_type_name: The type of the module to filter by.

        Yields:
            A module with the specified module type.
        """

        for found_module in self.iterate_modules():
            if found_module.module_type == module_type_name:
                yield found_module

    def modules_by_type(self, module_type_name: str) -> list[Module]:
        """Retrieve a list of modules with a specific type.

        This method collects all modules that match the specified type by
        iterating through the available modules and filtering them based on
        their module type.

        Args:
            module_type_name: The type of the module to filter by.

        Returns:
            A list of modules that match the specified module type.
        """

        return list(self.iterate_modules_by_type(module_type_name))

    def module(self, name: str, side: str = "M") -> Module | None:
        """Find and return a module instance with the specified name and side,
        checking the cache first and then querying the module layer.

        Args:
            name: The name of the module to find.
            side: The side of the module to find.

        Returns:
            The matching `Module` instance if found; `None` otherwise.
        """

        found_module: Module | None = None
        for cached_module in list(self._modules_cache):
            if cached_module.name() == name and cached_module.side() == side:
                found_module = cached_module
                break
        if found_module is not None:
            return found_module

        modules_layer = self.get_or_create_modules_layer()
        if modules_layer is None:
            return None

        modules_manager = self.configuration.modules_manager()
        for module_metanode in modules_layer.iterate_modules():
            module_name = module_metanode.attribute(constants.NAME_ATTR).asString()
            module_side = module_metanode.attribute(
                constants.MODULE_SIDE_ATTR
            ).asString()
            if module_name == name and module_side == side:
                module_instance = modules_manager.from_meta_node(
                    rig=self, meta=module_metanode
                )
                self._modules_cache.add(module_instance)
                return module_instance

        return None

    def module_from_node(self, node: DGNode | OpenMaya.MObject) -> Module | None:
        """Retrieve a module instance from a given node.

        This function attempts to determine the module corresponding to the
        provided node by first resolving its metanode.

        Once the metanode is retrieved, the function queries the relevant
        attributes from the metanode to identify and return the desired module.

        Args:
            node: The node from which to resolve the module.

        Raises:
            errors.MissingMetaNode: If the metanode cannot be resolved from
                the provided node.

        Returns:
            The resulting module instance if resolved successfully, or `None`
                if no suitable module is determined.
        """

        meta_node = module_meta_node_from_node(node)
        if not meta_node:
            raise errors.MissingMetaNode(
                f'No meta node attached to node: "{node.name()}"'
            )

        return self.module(
            meta_node.attribute(constants.NAME_ATTR).value(),
            meta_node.attribute(constants.MODULE_SIDE_ATTR).value(),
        )

    def _build_modules(
        self,
        modules: list[Module],
        child_parent_map: dict[Module, Module | None],
        build_func_name: str,
        **kwargs,
    ) -> bool:
        """Build modules in a specific order, ensuring that parent modules are
        built before their children.

        Args:
            modules: List of modules to build.
            child_parent_map: Mapping of modules to their parent modules.
            build_func_name: Name of the build function to call on each module.
            **kwargs: Additional keyword arguments to pass to the build function.

        Returns:
            `True` if all modules were built successfully; `False` otherwise.
        """

        def _construct_module_order(
            _modules: list[Module],
        ) -> dict[Module, Module | None]:
            """Construct an ordered mapping of modules to their parents,
            ensuring that parent modules are processed before their children.

            Args:
                _modules: List of modules to order.

            Returns:
                An ordered dictionary mapping each module to its parent module.
            """

            _ordered_modules: dict[Module, Module | None] = {}
            _unsorted_modules: dict[Module, Module | None] = {
                mod: mod.parent() for mod in _modules
            }
            while _unsorted_modules:
                for _child, _parent in list(_unsorted_modules.items()):
                    if _parent in _unsorted_modules:
                        continue
                    else:
                        del _unsorted_modules[_child]
                        _ordered_modules[_child] = _parent

            return _ordered_modules

        def _process_module(_module: Module, _parent_module: Module | None) -> bool:
            """Recursively process a module and its parent, ensuring that the
            parent is built before the child.

            Args:
                _module: The module to process.
                _parent_module: The parent module of the module to process.

            Returns:
                True if the module was processed successfully; False otherwise.
            """

            if _parent_module is not None and _parent_module not in visited_modules:
                _process_module(_parent_module, current_modules[_parent_module])

            if _module in visited_modules:
                return False

            visited_modules.add(_module)

            _parent_descriptor_id: str = _module.descriptor.parent
            if _parent_descriptor_id:
                logger.debug(
                    "Module descriptor has parents defined, adding parents ..."
                )
                _existing_module = self.module(*_parent_descriptor_id.split(":"))
                if _existing_module is not None:
                    _module.set_parent(_existing_module)

            try:
                logger.debug(
                    f"Building module: {_module} with method: {build_func_name} ..."
                )
                getattr(_module, build_func_name)(**kwargs)
                return True
            except errors.BuildModuleGuideUnknownError:
                logger.error(f"Failed to build for: {_module}", exc_info=True)
                return False

        ordered_modules = _construct_module_order(modules)
        current_modules = child_parent_map
        visited_modules: set[Module] = set()
        for child, parent_module in ordered_modules.items():
            success = _process_module(child, parent_module)
            if not success:
                return False

        return True

    @profiler.fn_timer
    def delete_modules(self) -> None:
        """Delete all modules associated with this rig instance."""

        with self.build_script_context(constants.BuildScriptFunctionType.DeleteModules):
            for module in self.iterate_modules():
                module_name = module.name()
                try:
                    module.delete()
                except Exception:
                    logger.error(
                        f"Failed to delete module: {module_name}", exc_info=True
                    )

        self._modules_cache.clear()

    def delete_module(self, name: str, side: str) -> bool:
        """Delete a specific module by name and side.

        Args:
            name: The name of the module to delete.
            side: The side of the module to delete.

        Returns:
            True if the module was found and deleted; False otherwise.
        """

        module = self.module(name, side)
        if not module:
            logger.warning(f'"Module {name}:{side} not found for deletion."')
            return False

        with self.build_script_context(constants.BuildScriptFunctionType.DeleteModule):
            self._cleanup_space_switches(module)
            module.delete()
            try:
                self._modules_cache.remove(module)
            except KeyError:
                return False

        return True

    def clear_modules_cache(self):
        """Clear the internal cache of modules."""

        self._modules_cache.clear()

    # endregion

    # region === Guides === #

    @profiler.fn_timer
    def build_guides(self, modules: list[Module] | None = None):
        self.configuration.update_from_rig(self)
        child_parent_map: dict[Module, Module | None] = {
            module: module.parent() for module in self.modules()
        }
        modules = modules or list(child_parent_map.keys())

        # Build an unordered list of modules respecting parent hierarchy.
        modules_with_parents: list[Module] = []
        _visited: set[Module] = set()

        def _add_with_parents(_module: Module):
            if _module in _visited:
                return
            _parent_module = child_parent_map[_module]
            if _parent_module is not None:
                _add_with_parents(_parent_module)
            modules_with_parents.append(_module)
            _visited.add(_module)

        for module in modules:
            _add_with_parents(module)

        with (
            disconnect_module_context(modules_with_parents),
            self.build_script_context(constants.BuildScriptFunctionType.Guide),
        ):
            self._build_modules(modules, child_parent_map, "build_guides")

    # === Build Scripts === #

    @contextmanager
    def build_script_context(
        self,
        build_script_type: constants.BuildScriptFunctionType,
        **kwargs: dict[str, Any],
    ):
        if not self._meta:
            return

        pre_func_name, post_func_name = constants.BUILD_SCRIPT_FUNCTION_MAPPING.get(
            build_script_type
        )
        script_configuration = self.meta.build_script_config()

        if pre_func_name:
            for script in self.configuration.build_scripts:
                if not hasattr(script, pre_func_name):
                    continue
                script_properties = script.properties_as_key_value()
                logger.debug(
                    f'Executing pre-build script: "{script.__class__.__name__}.{pre_func_name}"'
                )
                script_properties.update(script_configuration.get(script.id, {}))
                script.rig = self
                getattr(script, pre_func_name)(properties=script_properties, **kwargs)

        yield

        if post_func_name:
            for script in self.configuration.build_scripts:
                if not hasattr(script, post_func_name):
                    continue
                script_properties = script.properties_as_key_value()
                logger.debug(
                    f'Executing post-build script: "{script.__class__.__name__}.{post_func_name}"'
                )
                script_properties.update(script_configuration.get(script.id, {}))
                script.rig = self
                getattr(script, post_func_name)(properties=script_properties, **kwargs)


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


def rig_from_node(node: DGNode) -> Rig | None:
    """Retrieve the rig instance associated with a given node.

    Args:
        node: The node from which to retrieve the rig.

    Returns:
        The associated rig instance if found; `None` otherwise.

    Raises:
        errors.MissingMetaNode: If no metanode is attached to the provided node.
    """

    meta_nodes = connected_meta_nodes(node)
    if not meta_nodes:
        raise errors.MissingMetaNode(f'No meta node attached to node: "{node.name()}"')

    try:
        for meta_node in meta_nodes:
            found_rig = parent_rig(meta_node)
            if found_rig is not None:
                return found_rig
        else:
            raise AttributeError()
    except AttributeError:
        raise errors.MissingMetaNode("Attached meta node has no parent rig")


def parent_rig(meta_node: MetaBase) -> Rig | None:
    """Retrieve the parent rig instance associated with a given metanode.

    Args:
        meta_node: The metanode from which to retrieve the parent rig.

    Returns:
        The associated parents rig instance if found; `None` otherwise.
    """

    rig_meta: MetaRig | None = None
    for meta_parent in meta_node.iterate_meta_parents():
        root_attr = meta_parent.attribute(constants.IS_ROOT_ATTR)
        if root_attr and root_attr.value():
            rig_meta = cast(MetaRig, meta_parent)
            break
    if rig_meta is None:
        return None

    rig_instance = Rig(meta=rig_meta)
    rig_instance.start_session()

    return rig_instance


def module_meta_node_from_node(node: DGNode) -> MetaModule | None:
    """Retrieve the module metanode associated with a given node.

    This function attempts to find the metanode corresponding to the
    provided node. If the node is already a metanode of type `Module`,
    it is returned directly. Otherwise, the function searches for
    connected metanodes of type `Module` and returns the first one found.

    Args:
        node: The node from which to retrieve the module metanode.

    Returns:
        The associated module metanode if found; `None` otherwise.

    Raises:
        ValueError: If no metanode is attached to the provided node.
    """

    meta_nodes = (
        [MetaBase(node.object())] if is_meta_node(node) else connected_meta_nodes(node)
    )
    meta_node = meta_nodes[0] if meta_nodes else None
    if meta_node is None:
        raise errors.MissingMetaNode(f'No meta node attached to node: "{node.name()}"')

    if meta_node.hasAttribute(constants.MODULE_TYPE_ATTR):
        return cast(MetaModule, meta_node)

    found_meta_node: MetaModule | None = None
    for meta_parent in meta_node.iterate_meta_parents():
        if meta_parent.hasAttribute(constants.MODULE_TYPE_ATTR):
            found_meta_node = cast(MetaModule, meta_parent)
            break

    return found_meta_node


def module_from_node(node: DGNode, rig: Rig | None = None) -> Module | None:
    """Retrieve a module instance from a given node.

    This function attempts to determine the module corresponding to the
    provided node by first resolving its metanode.

    Once the metanode is retrieved, the function queries the relevant
    attributes from the metanode to identify and return the desired module.

    Args:
        node: The node from which to resolve the module.
        rig: Optional rig instance to use for module retrieval. If not
            provided, the function will attempt to find the rig based on
            the metanode's rig name and namespace.

    Raises:
        errors.MissingRigForNode: If the metanode is not attached to the
            provided node or if the rig cannot be determined.

    Returns:
        The resulting module instance if resolved successfully, or `None`
            if no suitable module is determined.
    """

    rig = rig if rig is not None else rig_from_node(node)
    if rig is None:
        raise errors.MissingRigForNode(node.fullPathName())

    return rig.module_from_node(node)


def modules_from_nodes(nodes: list[DGNode]) -> dict[Module, list[DGNode]]:
    """Retrieve a set of module instances associated with a list of nodes.

    This function iterates through the provided list of nodes, attempting
    to resolve the corresponding module metanode for each node. If a
    metanode is found, it initializes the appropriate module instance and
    adds it to a set to ensure uniqueness.

    Args:
        nodes: A list of nodes from which to retrieve module instances.

    Returns:
        A list of unique module instances associated with the provided nodes.
    """

    found_modules: dict[Module, list[DGNode]] = {}
    for node in nodes:
        try:
            found_module = module_from_node(node)
        except (errors.MissingMetaNode, errors.MissingRigForNode):
            continue
        found_modules.setdefault(found_module, []).append(node)

    return found_modules
