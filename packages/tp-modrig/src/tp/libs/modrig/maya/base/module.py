from __future__ import annotations

import typing
import logging
from typing import Iterator, Any

from maya.api import OpenMaya

from tp.libs.python import profiler
from tp.libs.maya.wrapper import DagNode, ContainerAsset
from tp.libs.maya.om import attributetypes

from . import constants, errors
from ..services import naming
from ..meta.module import MetaModule
from ..meta.layers import MetaGuidesLayer, MetaModulesLayer
from ..descriptors.module import (
    load_descriptor,
    migrate_to_latest_version,
    ModuleDescriptor,
)
from ..descriptors.utils import parse_raw_descriptor

if typing.TYPE_CHECKING:
    from tp.libs.naming.manager import NameManager
    from .rig import Rig
    from .configuration import RigConfiguration
    from .namingpresets import Preset
    from .subsystem import BaseSubsystem
    from ..meta.rig import MetaRig


class Module:
    """Base class that encapsulates a single rigging module."""

    id: str = ""
    documentation: str = ""
    icon_path: str = ""
    required_plugins: list[str] = []

    def __init__(
        self,
        rig: Rig,
        descriptor: ModuleDescriptor | None = None,
        meta: MetaModule | None = None,
    ):
        """Initialize a new `Module` instance.

        Args:
            rig: The parent rig instance this module belongs to.
            descriptor: The module descriptor. If `None`, it will be loaded
                from the given metanode instance and updated to the latest
                version if necessary.
            meta: The module's metanode instance. If `None`, a new module is
                created.
        """

        super().__init__()

        self._rig = rig
        self._meta = meta
        self._descriptor: ModuleDescriptor | None = None
        self._original_descriptor: ModuleDescriptor | None = None
        self._configuration = rig.configuration
        self._container: ContainerAsset | None = None
        self._is_building_guides = False
        self._is_building_skeleton = False
        self._is_building_rigs = False
        self._build_objects_cache: dict[str, Any] = {}

        self._initialize_descriptor(descriptor=descriptor, meta=meta)

        self.logger = logging.getLogger(
            ".".join([__name__, "_".join([self.name(), self.side()])])
        )

    def __bool__(self) -> bool:
        """Determine the boolean representation of the instance by checking
        its existence.

        This method enables the object to be used in a boolean context,
        returning the result of the `exists()` method call. It serves as a
        way to evaluate whether the instance is considered to exist or hold
        a valid state.

        Returns:
            `True` if the instance exists based on the implementation of
                `exists()`, otherwise `False`.
        """

        return self.exists()

    def __eq__(self, other: Module | None) -> bool:
        """Check equality between the current instance and another object.

        Args:
            other: The object to compare with the current instance.

        Returns:
            bool: True if the other object is an instance of Module and has
            the same metanode as the current instance, otherwise False.
        """

        if other is None:
            return False

        return isinstance(other, Module) and self._meta == other.meta

    def __ne__(self, other: Module | None) -> bool:
        """Compare the current instance with another object to determine if
        they are not equal.

        Equality is determined by the type of the other object and whether
        the metanode of the two modules are identical. If the other object is
        `None`, they are considered not equal.

        Args:
            other: An instance of the Module class or None.

        Returns:
            bool: True if the current instance and the other object are determined
            to be not equal, otherwise False.
        """

        if other is None:
            return False

        return isinstance(other, Module) and self._meta != other.meta

    def __hash__(self) -> int:
        """Compute the hash value for the object, based on its metanode.

        The `__hash__` method provides a mechanism for objects to be used as
        keys in dictionaries or stored in sets by returning a hash
        representation of the object.

        Returns:
            The hash value derived from the object's metanode.
        """

        return hash(self._meta)

    def __repr__(self):
        """Represents the string representation of the object instance.

        This method is used to provide a developer-friendly string
        representation of an instance that includes the class name,
        a name associated with the instance, and the side associated
        with the instance.

        Returns:
            A formatted string displaying the class name, name of the
                instance, and its side.
        """
        return f"<{self.__class__.__name__}>-{self.name()}:{self.side()}"

    # === Configuration === #

    @property
    def configuration(self) -> RigConfiguration:
        """The rig configuration instance."""

        return self._configuration

    def current_naming_preset(self) -> Preset:
        """Return the currently active naming preset based on the local
        override or the rig configuration.

        The method evaluates if there is a local naming preset override
        specified in the descriptor. If such an override exists, it attempts
        to locate and use the associated preset from the name presets manager.

        If no local override is present or the corresponding preset is not
        found, the method falls back to the default naming preset defined in
        the current rig configuration.

        Returns:
            The active naming preset, either determined by the local override
            or the rig configuration.
        """

        local_override = self.descriptor.naming_preset
        local_preset = (
            self.configuration.name_presets_manager().find_preset(local_override)
            if local_override
            else None
        )

        return (
            local_preset
            if local_preset is not None
            else self.configuration.current_naming_preset
        )

    def naming_manager(self) -> NameManager:
        """Retrieve or instantiates the `NameManager` instance for the
        current module type.

        This method checks if a `NameManager` instance is cached for the
        current module. If found, it retrieves it immediately; otherwise,
        it finds the appropriate `NameManager` based on the current
        configuration and naming preset.

        Returns:
            An instance of `NameManager` for managing naming conventions
                specific to the current module type.
        """

        naming_manager = self._build_objects_cache.get("naming")
        if naming_manager is not None:
            return naming_manager

        return self.configuration.find_name_manager_for_type(
            self.module_type, preset_name=self.current_naming_preset().name
        )

    # region === Rig === #

    @property
    def rig(self) -> Rig:
        """The rig instance this module belongs to."""

        return self._rig

    # endregion

    # region === Meta === #

    @property
    def meta(self) -> MetaModule:
        """The module metanode instance."""

        return self._meta

    @meta.setter
    def meta(self, value: MetaModule):
        """Set module metanode instance."""

        self._meta = value

    @property
    def module_type(self) -> str:
        """The module type for this instance."""

        return (
            self.__class__.__name__
            if not self.exists()
            else self.meta.attribute(constants.MODULE_TYPE_ATTR).asString()
        )

    def uuid(self) -> str:
        """Return the UUID (Universally Unique Identifier) for this module instance.

        The UUID is a unique identifier that remains constant for the lifetime
        of the module, event if the module is renamed. It is used to reliably
        reference the module across different sessions or when the module's
        name changes.

        Notes:
            - If the module's metanode exists, the UUID is retrieved from it.
            - Otherwise, the UUID is retrieved from the module's descriptor.

        Returns:
            The UUID of the module as a string.
        """

        if self._meta is None:
            return self.descriptor.uuid

        # All Maya nodes have a UUID attribute.
        return self._meta.uuid.asString()

    def exists(self) -> bool:
        """Determine if the module exists within the current scene.

        Checks for the existence of the module by verifying that its
        associated metanode exists in the scene.

        Notes:
            - This method is safe to call even if the module has not been
                fully initialized.

        Returns:
            `True` if the module exists; `False` otherwise.
        """

        try:
            return True if self._meta and self._meta.exists() else False
        except AttributeError:
            self.logger.warning(
                f"Module does not exist: {self.descriptor.name}",
                exc_info=True,
            )

        return False

    def root_transform(self) -> DagNode | None:
        """Return the root transform node for this module instance.

        This is retrieved from the module's metanode if it exists. The retrieved
        top-level transform serves as the parent for all the module's nodes
        within the scene hierarchy. It represents the module's position,
        rotation, and scale in 3D space.

        Returns:
            The root transform instance; `None` if the module does not exist
            in the scene.
        """

        return self._meta.root_transform() if self.exists() else None

    def find_layer(self, layer_type: str) -> MetaGuidesLayer | None:
        """Find a specific layer by its type within the module.

        Args:
            layer_type: The type of the layer to find.

        Returns:
            The found layer instance if it exists; `None` if the module
            does not exist in the scene or if no such layer is found.

        Raises:
            ValueError: If the provided layer type is not recognized.
        """

        if layer_type not in constants.LAYER_TYPES:
            raise ValueError(
                f'Invalid layer type: "{layer_type}", available types: {constants.LAYER_TYPES}'
            )

        if not self.exists():
            return None

        return self._meta.layer(layer_type)

    @profiler.fn_timer
    def create(
        self, parent: MetaModulesLayer | MetaRig | MetaModule | None = None
    ) -> MetaModule:
        """Create the module within the current scene.

        Handles the creation of the module's metanode, setting up its attributes,
        but does not handle the creation of guides or other module-specific
        elements.

        The following operations are performed:
            - Create the module's metanode with appropriate attributes.
            - Set up the naming based on the modules' descriptor.
            - Initialize the module's version and type attributes.
            - Set up the connections to the parent module or rig (if provided).


        Args:
            parent: Optional parent metanode, which can be a module layer,
                rig, or another module. If provided, the new module will be
                linked to this parent.

        Returns:
            The newly created module metanode instance.
        """

        descriptor = self.descriptor
        naming_manager = self.naming_manager()
        module_name, side = self.name(), self.side()
        hierarchy_name, meta_name = naming.compose_module_root_names(
            naming_manager, module_name, side
        )
        self.logger.debug("Creating module meta node instance...")
        meta_node = MetaModule(name=meta_name, parent=parent)
        meta_node.attribute(constants.ID_ATTR).set(module_name)
        meta_node.attribute(constants.NAME_ATTR).set(module_name)
        meta_node.attribute(constants.MODULE_SIDE_ATTR).set(side)
        meta_node.attribute(constants.MODULE_VERSION_ATTR).set(descriptor.version)
        meta_node.attribute(constants.MODULE_TYPE_ATTR).set(descriptor.type)
        notes = meta_node.attribute("notes")
        if notes is None:
            meta_node.addAttribute(
                "notes", type=attributetypes.kMFnDataString, value=self.documentation
            )
        else:
            notes.set(self.documentation)

        parent_transform = parent.root_transform() if parent else None
        meta_node.create_transform(hierarchy_name, parent=parent_transform)

        self._meta = meta_node

        if parent and isinstance(parent, MetaModulesLayer):
            meta_node.add_meta_parent(parent)

        return meta_node

    # endregion

    # region === Hierarchy === #

    def has_parent(self) -> bool:
        """Check if the module has a parent metanode.

        Returns:
            True if the module has a parent metanode, False otherwise.
        """

        if self._meta is None:
            return False

        for meta_parent in self._meta.iterate_meta_parents():
            if meta_parent.hasAttribute(constants.IS_MODULE_ATTR):
                return True

        return False

    def parent(self) -> MetaModule | None:
        """Return the parent module of this module instance.

        Notes:
            If the module is currently in the process of being built (guides,
            skeleton, or rigs), the parent is retrieved from a cached value to
            ensure consistency during the build process.

        Returns:
            The parent module instance if it exists; `None` if there is no
            parent or if the module does not exist in the scene.
        """

        if self._meta is None:
            return None

        if any(
            [
                self._is_building_guides,
                self._is_building_skeleton,
                self._is_building_rigs,
            ]
        ):
            return self._build_objects_cache.get("parent")

        for meta_parent in self._meta.iterate_meta_parents(recursive=False):
            if meta_parent.hasAttribute(constants.IS_MODULE_ATTR):
                return self._rig.module(
                    meta_parent.attribute(constants.NAME_ATTR).value(),
                    meta_parent.attribute(constants.MODULE_SIDE_ATTR).value(),
                )

        return None

    def iterate_children(self, depth_limit: int = 256) -> Iterator[Module]:
        """Iterate over the child modules of this module instance.

        Args:
            depth_limit: The maximum depth to traverse in the hierarchy.

        Yields:
            Each child module instance.
        """

        if not self.exists():
            return

        for meta_child in self._meta.iterate_meta_children(depth_limit=depth_limit):
            if not meta_child.hasAttribute(constants.IS_MODULE_ATTR):
                continue

            child_module = self._rig.module(
                meta_child.attribute(constants.NAME_ATTR).value(),
                meta_child.attribute(constants.MODULE_SIDE_ATTR).value(),
            )
            if child_module is None:
                continue

            yield child_module

    def children(self, depth_limit: int = 256) -> list[Module]:
        """Return a list of child modules parented under this module instance.

        Args:
            depth_limit: The maximum depth to traverse in the hierarchy.

        Returns:
            A list of child module instances.
        """

        return list(self.iterate_children(depth_limit=depth_limit))

    # endregion

    # region === Descriptor === #

    @property
    def descriptor(self) -> ModuleDescriptor:
        """The module descriptor instance."""

        return self._descriptor

    @descriptor.setter
    def descriptor(self, value: ModuleDescriptor):
        """Sets the module descriptor."""

        if isinstance(value, dict):
            value = load_descriptor(value, self._original_descriptor)

        self._descriptor = value

    def _initialize_descriptor(
        self, descriptor: ModuleDescriptor | None = None, meta: MetaModule | None = None
    ):
        """Initialize the descriptor for the module, determining its
        configuration and setup based on the provided descriptor or metanode
        information.

        - If both descriptor and metanode are provided, the descriptor is
        duplicated and updated if necessary.

        - If only metanode is provided, a new descriptor is initialized based
        on the module type metadata.

        The method also updates scene data and migrates descriptor data to
        the latest version if needed.

        Args:
            descriptor: The module descriptor to initialize. If not provided
                and metanode is defined, a new descriptor is initialized.
            meta: The metanode module used as a reference for initialization.
                Determines the module type if the descriptor is not explicitly
                supplied.
        """

        if descriptor is None and meta is not None:
            no_module_type = False
            module_type_name = meta.attribute(constants.MODULE_TYPE_ATTR).asString()
            if not module_type_name:
                no_module_type = True
                module_type_name = self.id
            raw_descriptor, original_descriptor = (
                self.configuration.initialize_module_descriptor(module_type_name)
            )
            if no_module_type:
                meta.attribute(constants.MODULE_TYPE_ATTR).set(module_type_name)
            self._original_descriptor = original_descriptor
            if self._meta is not None and self._meta.exists():
                data = self._meta.raw_descriptor_data()
                translated_data = parse_raw_descriptor(data)
                scene_data = migrate_to_latest_version(
                    translated_data, original_descriptor=raw_descriptor
                )
                raw_descriptor.update(scene_data)
            self._descriptor = raw_descriptor
        elif descriptor and meta:
            _, self._original_descriptor = (
                self._rig.configuration.initialize_module_descriptor(
                    module_type_name=descriptor.type
                )
            )
            self._descriptor = self._descriptor_from_scene()
        else:
            _, self._original_descriptor = (
                self._rig.configuration.initialize_module_descriptor(
                    module_type_name=descriptor.type
                )
            )
            self._descriptor = ModuleDescriptor(
                descriptor.serialize(self._original_descriptor), path=descriptor.path
            )

    def _descriptor_from_scene(self) -> ModuleDescriptor | None:
        """Retrieve the module descriptor from the scene data stored in
        the metanode.

        This method extracts the raw descriptor data from the metanode,
        parses it, and migrates it to the latest version if necessary.
        The resulting data is then used to create a new `ModuleDescriptor`
        instance.

        Returns:
            A `ModuleDescriptor` instance representing the module's
                configuration as defined in the scene. If the metanode does
                not exist, returns `None`.
        """

        if not self.exists():
            return None

        data = self._meta.raw_descriptor_data()
        translated_data = parse_raw_descriptor(data)
        return load_descriptor(translated_data, self._original_descriptor)

    def name(self) -> str:
        """Get the name of the module from the module descriptor data.

        The name of a module is a unique identifier that distinguishes it
        from other modules within the same rig. It is typically used to
        reference the module in scripts, user interfaces, and configuration
        files.

        Returns:
            The name of the module.
        """

        return self.descriptor.name

    def side(self) -> str:
        """Get the side of the module from the module descriptor data.

        The side represents the location of the module relative to the mesh
        (e.g., 'L' for the left, 'R' for right, 'C' for the center) and is
        used in naming conventions and module organization.

        Notes:
            - The side is set during module creation but can be modified later.
            - To change the side, use the ` setSide ()` method to ensure proper updates.

        Returns:
            The side of the module.
        """

        return self.descriptor.side

    def set_side(self, side: str):
        """Update the side of the module and updates all related data
        structures, including the metanode and naming configuration.

        Args:
            side: The new side value to set for the module.
        """

        if self._meta is None:
            return

        name = self.name()
        old_side = self.side()
        naming_manager = self.naming_manager()
        old_name = naming_manager.resolve(
            "moduleName", {"moduleName": name, "side": old_side}
        )
        new_name = naming_manager.resolve(
            "moduleName", {"moduleName": name, "side": side}
        )

        for module_node in self.nodes():
            module_node.rename(module_node.name().replace(old_name, new_name))

        self._meta.attribute(constants.MODULE_SIDE_ATTR).set(side)

        self.save_descriptor()
        self._update_space_switch_module_dependencies(
            name, old_side, self.name(), self.side()
        )

    # endregion

    # region === Namespace === #

    def namespace(self) -> str:
        """Return the full namespace path for this module.

        This method retrieves the complete namespace path under which this
        module's nodes are organized within the scene hierarchy.

        The namespace helps organize and prevent naming conflicts between
        modules and their elements.

        Notes:
            - If the modules has no metanode, it returns the current namespace
                plugs the module name.
            - The returned namespace path always includes the root namespace
                as the first element.
            - This is different from the module name which is just the last
                part of the namespace.

        Returns:
            The full namespace path as a string.
        """

        if self._meta is None:
            return ":".join([OpenMaya.MNamespace.currentNamespace(), self.name()])

        name = OpenMaya.MNamespace.getNamespaceFromName(self._meta.fullPathName())
        root = OpenMaya.MNamespace.rootNamespace()
        if not name.startswith(root):
            name = root + name

        return name

    def parent_namespace(self) -> str:
        """Retrieve the parent namespace of this module's namespace.

        This method navigates up on level in the namespace hierarchy from the
        module's current namespace.

        This is useful for operations that need to reference or modify the
        parent container of this module.

        Notes:
            - Return the root namespace if the module is in the root namespace
                or if an error occurs.
            - The current namespace is temporarily changed during execution.

        Returns:
            The parent namespace path (e.g. ":root:character" for a module in
                ":root:character:arm_L").
        """

        namespace = self.namespace()
        if not namespace:
            return OpenMaya.MNamespace.rootNamespace()

        current_namespace = OpenMaya.MNamespace.currentNamespace()
        OpenMaya.MNamespace.setCurrentNamespace(namespace)
        try:
            parent = OpenMaya.MNamespace.parentNamespace()
            OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
        except RuntimeError:
            parent = OpenMaya.MNamespace.rootNamespace()

        return parent

    def rename_namespace(self, namespace: str) -> bool:
        """Rename the module's namespace to a new name.

        This method changes the namespace of the module and all its nodes
        to the specified new namespace.

        Args:
            namespace: The new namespace to assign to the module.

        Returns:
            True if the operation was successful; False otherwise.
        """

        module_namespace = self.namespace()
        if OpenMaya.MNamespace.namespaceExists(namespace):
            self.logger.debug(f'Namespace "{namespace}" already exists.')
            return False

        parent_namespace = self.parent_namespace()
        if parent_namespace == OpenMaya.MNamespace.rootNamespace():
            self.logger.debug(
                f'Cannot rename namespace "{module_namespace}" '
                f'to "{namespace}" because it is in the root namespace.'
            )
            return False

        current_namespace = OpenMaya.MNamespace.currentNamespace()
        OpenMaya.MNamespace.setCurrentNamespace(parent_namespace)
        try:
            OpenMaya.MNamespace.renameNamespace(module_namespace, namespace)
            OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
        except RuntimeError:
            self.logger.error(
                f'Failed to rename namespace "{module_namespace}" -> "{namespace}".',
                exc_info=True,
            )
            return False

        return True

    def remove_namespace(self) -> bool:
        """Remove the module's namespace, moving all its nodes to the parent
        namespace.

        Returns:
            True if the operation was successful; False otherwise.
        """

        namespace = self.namespace()
        if not namespace:
            return False

        OpenMaya.MNamespace.moveNamespace(
            namespace, OpenMaya.MNamespace.rootNamespace(), True
        )
        OpenMaya.MNamespace.removeNamespace(namespace)

        return True

    # endregion

    # region === Cache === #

    def _generate_object_cache(self):
        """Generate a cache of commonly used objects for the module."""

        self._build_objects_cache: dict[str, Any] = self._meta.layer_id_mapping()
        self._build_objects_cache["container"] = self.container()
        self._build_objects_cache["parent"] = self.parent()
        self._build_objects_cache["naming"] = self.naming_manager()
        self._build_objects_cache["subsystems"] = self.subsystems()

    # endregion

    # region === Visibility === #

    def is_hidden(self) -> bool:
        """Determine whether the module is hidden in the scene.

        This method checks the visibility state of the module by examining its
        root transform node.

        A module is considered hidden if either:
            - The modules does not exist in the scene.
            - The root transform's visibility attribute is set to `False`.

        Returns:
            `True` if the module is hidden; `False` otherwise.
        """

        return self.exists() and self.root_transform().isHidden()

    def hide(self) -> bool:
        """Hide the module in the scene by setting its root transform's
        visibility attribute to `False`.

        This method affects the visual representation of the model within the
        viewport without deleting any of its nodes.

        Notes:
            The hidden state is persistent and will be saved with the scene.

        Notes:
            - This only affects the visibility in the viewport, not the
                module's functionality.

        Returns:
            `True` if the operation was successful; `False` otherwise.
        """

        if not self.exists():
            return False

        self.root_transform().hide()

        return True

    def show(self) -> bool:
        """Show the module in the scene by setting its root transform's
        visibility attribute to `True`.

        This method affects the visual representation of the model within the
        viewport without deleting any of its nodes.

        Notes:
            The visible state is persistent and will be saved with the scene.

        Notes:
            - This only affects the visibility in the viewport, not the
                module's functionality.

        Returns:
            `True` if the operation was successful; `False` otherwise.
        """

        if not self.exists():
            return False

        self.root_transform().show()

        return True

    # region === Asset Container === #

    def has_container(self) -> bool:
        """Check if the module has an associated asset container.

        Returns:
            `True` if the module has an associated asset container; `False`
            otherwise.
        """

        return self.container() is not None

    def container(self) -> ContainerAsset | None:
        """Return the asset container node associated with this module.

        The asset container serves as a container to encapsulate all the
        elements of this module within the scene hierarchy.
        It helps in organizing and managing the module's nodes.

        Returns:
            The asset container instance if it exists; `None` if the module
            does not exist in the scene or if no container is found.
        """

        if not self.exists():
            return None

        source = self._meta.container.source()
        return ContainerAsset(source.node().object()) if source is not None else None

    def create_container(self) -> ContainerAsset | None:
        """Create an asset container for this module.

        The asset container serves as a container to encapsulate all the
        elements of this module within the scene hierarchy.
        It helps in organizing and managing the module's nodes.

        Returns:
            The created asset container instance if successful; `None` if the module
            does not exist in the scene or if no container could be created.
        """

        container = self.container()
        if container is not None:
            return container

        if not self.configuration.use_containers:
            self.logger.debug(
                f"Skipping container creation for module: {self.name()}. "
                f"Containers are disabled in the configuration."
            )
            return None

        container_name = naming.compose_container_name(
            self.naming_manager(), self.name(), self.side()
        )
        container = ContainerAsset()
        container.create(container_name)
        container.message.connect(self._meta.attribute(constants.MODULE_CONTAINER_ATTR))
        self._container = container

        return container

    def delete_container(self) -> bool:
        """Delete the asset container associated with this module.

        This method removes the asset container from the scene, which
        encapsulates all the elements of this module. Deleting the container
        helps in cleaning up and managing the module's nodes.

        Returns:
            `True` if the container was successfully deleted; `False` if
            the module does not exist in the scene or if no container was found.
        """

        container = self.container()
        if container is None:
            return False

        container.delete()

        return True

    # endregion

    # region === Guides === #

    def has_guides(self) -> bool:
        """Check if the guides for this module have been built.

        Returns:
            `True` if the guides have been built; `False` otherwise.
        """

        return (
            self.exists()
            and self._meta.attribute(constants.MODULE_HAS_GUIDE_ATTR).value()
        )

    def has_guide_controls(self) -> bool:
        """Check if the guide controls for this module have been built.

        Returns:
            `True` if the guide controls have been built; `False` otherwise.
        """

        return (
            self.exists()
            and self._meta.attribute(constants.MODULE_HAS_GUIDE_CONTROLS_ATTR).value()
        )

    def guide_layer(self) -> MetaGuidesLayer | None:
        """Return the guide layer metanode for this module instance.

        The guide layer contains all the guide elements for this module,
        which are used during the rigging process to define the structure
        and placement of the rig.

        Returns:
            The guide layer metanode instance if it exists; `None` if the
            module does not exist in the scene or if no guide layer is found.
        """

        if not self.exists():
            return None

        cached = self._build_objects_cache.get(MetaGuidesLayer.ID)
        if cached is not None:
            return cached

        return self._meta.layer(constants.GUIDE_LAYER_TYPE)

    @profiler.fn_timer
    def build_guides(self):
        if not self.exists():
            raise errors.ModuleDoesNotExistError(self.descriptor.name)

        self._generate_object_cache()

        if self.has_guides():
            self.guide_layer().root_transform().show()

        if self.has_polished():
            self._set_has_polished(False)

        has_skeleton = self.has_skeleton()
        if has_skeleton:
            self._set_has_skeleton(False)

        self.logger.debug(f"Building guides for module: {self.name()}")

        self._is_building_guides = True

        container = self.container()
        if container is None:
            container = self.create_container()
            self._build_objects_cache["container"] = container
        if container is not None:
            container.makeCurrent(True)
            container.lock(False)

        self.logger.debug(f"Starting guide build with namespace: {self.namespace()}")

        try:
            hierarchy_name, meta_name = naming.compose_names_for_layer(
                self.naming_manager(),
                self.name(),
                self.side(),
                constants.GUIDE_LAYER_TYPE,
            )
            guide_layer = self._meta.create_layer(
                constants.GUIDE_LAYER_TYPE,
                hierarchy_name,
                meta_name,
                parent=self._meta.root_transform(),
            )
            guide_layer.update_metadata(
                self._descriptor.guide_layer.get(constants.METADATA_DESCRIPTOR_KEY)
            )
            self._build_objects_cache[MetaGuidesLayer.ID] = guide_layer

            self.logger.debug("Executing `pre_setup_guides` hook...")
            self.pre_setup_guides()

            self.logger.debug("Executing `setup_guides` hook...")
            self.setup_guides()

            self.logger.debug("Executing `post_setup_guides` hook...")
            self.post_setup_guides()

        except Exception:
            self.logger.error("Failed to setup guides", exc_info=True)
            self._set_has_guide(False)
            raise errors.BuildModuleGuideUnknownError(
                f"Failed {self.name()}_{self.side()}"
            )
        finally:
            if container is not None:
                container.makeCurrent(False)
            self._is_building_guides = False
            self._build_objects_cache.clear()

        return True

    def _set_has_guide(self, state: bool):
        """Set the state that defines whether the guides for this module
        have been built.

        Args:
            state: The state to set.
        """

        self.logger.debug(f"Setting has guide state to: {state}")
        has_guide_attr = self._meta.attribute(constants.MODULE_HAS_GUIDE_ATTR)
        has_guide_attr.lock(False)
        has_guide_attr.set(state)

    def pre_setup_guide(self):
        self.logger.debug("Running `pre_setup_guide`...")

        self._setup_guide_settings()

    def _setup_guide_settings(self):
        self.logger.debug("Creating guide settings from module descriptor ...")
        guide_layer = self.guide_layer()
        module_settings = self.descriptor.guide_layer.settings
        if not module_settings:
            return

    def pin(self):
        pass

    def unpin(self):
        pass

    # endregion

    # region === Skeleton === #

    def has_skeleton(self) -> bool:
        """Check if the skeleton for this module has been built.

        Returns:
            `True` if the skeleton has been built; `False` otherwise.
        """

        return (
            self.exists()
            and self._meta.attribute(constants.MODULE_HAS_SKELETON_ATTR).value()
        )

    def _set_has_skeleton(self, state: bool) -> None:
        """Set the state that defines whether the skeleton for this module
        have been built.

        Args:
            state: The state to set.
        """

        self.logger.debug(f"Setting has skeleton state to: {state}")
        has_skeleton_attr = self._meta.attribute(constants.MODULE_HAS_SKELETON_ATTR)
        has_skeleton_attr.lock(False)
        has_skeleton_attr.set(state)

    # endregion

    # region === Polish === #

    def has_polished(self) -> bool:
        """Check if the polish for this module has been built.

        Returns:
            `True` if the polish has been built; `False` otherwise.
        """

        return (
            self.exists()
            and self._meta.attribute(constants.MODULE_HAS_POLISHED_ATTR).value()
        )

    def _set_has_polished(self, state: bool) -> None:
        """Set the state that defines whether the polish for this module
        has been built.

        Args:
            state: The state to set.
        """

        self.logger.debug(f"Setting has polished state to: {state}")
        has_polished_attr = self._meta.attribute(constants.MODULE_HAS_POLISHED_ATTR)
        has_polished_attr.lock(False)
        has_polished_attr.set(state)

    # endregion

    # region === Subsystems === #

    def subsystems(self) -> dict[str, BaseSubsystem]:
        """Return a dictionary of subsystems associated with this module.

        The subsystems are components or functional units that make up the
        module, each responsible for specific tasks or features within the
        module's overall functionality.

        Returns:
            A dictionary where keys are subsystem names and values are
            subsystem instances.
        """

        return {}

    # endregion
