from __future__ import annotations

import copy
import typing
import logging
from typing import Any

from tp.libs.python import profiler
from tp.libs.maya.wrapper import DagNode
from tp.libs.maya.om import attributetypes

from . import constants
from ..services import naming
from ..meta.module import MetaModule
from ..meta.moduleslayer import MetaModulesLayer
from ..descriptors.module import (
    load_descriptor,
    parse_raw_descriptor,
    migrate_to_latest_version,
    ModuleDescriptor,
)

if typing.TYPE_CHECKING:
    from tp.libs.naming.manager import NameManager
    from .rig import Rig
    from .configuration import RigConfiguration
    from ..base.namingpresets import Preset


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
        super().__init__()

        self._rig = rig
        self._meta = meta
        self._descriptor: ModuleDescriptor | None = None
        self._original_descriptor: ModuleDescriptor | None = None
        self._configuration = rig.configuration
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
                instance and its side.
        """
        return f"<{self.__class__.__name__}>-{self.name()}:{self.side()}"

    @property
    def module_type(self) -> str:
        """The module type for this instance."""

        return (
            self.__class__.__name__
            if not self.exists()
            else self.meta.attribute(constants.MODULE_TYPE_ATTR).asString()
        )

    @property
    def rig(self) -> Rig:
        """The rig instance this module belongs to."""

        return self._rig

    @property
    def configuration(self) -> RigConfiguration:
        """The rig configuration instance."""

        return self._configuration

    @property
    def meta(self) -> MetaModule:
        """The module metanode instance."""

        return self._meta

    @meta.setter
    def meta(self, value: MetaModule):
        """Set module metanode instance."""

        self._meta = value

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

    def exists(self) -> bool:
        """Determine if the module exists within the current scene.

        Returns:
            True if the module exists, otherwise False.
        """

        try:
            return True if self._meta and self._meta.exists() else False
        except AttributeError:
            self.logger.warning(
                f"Module does not exist: {self.descriptor.name}",
                exc_info=True,
            )

        return False

    def name(self) -> str:
        """Get the name of the module from the module descriptor data.

        Returns:
            The name of the module.
        """

        return self.descriptor.name

    def side(self) -> str:
        """Get the side of the module from the module descriptor data.

        Returns:
            The side of the module.
        """

        return self.descriptor.side

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

    def root_transform(self) -> DagNode | None:
        """Return the root transform node for this module instance.

        This is retrieved from the module's metanode if it exists.

        Returns:
            The root transform instance.
        """

        return self._meta.root_transform() if self.exists() else None

    @profiler.fn_timer
    def create(self, parent: MetaModulesLayer | None = None) -> MetaModule:
        """Creates the component within current scene.

        :param layers.NoddleComponentsLayer or None parent: optional rig parent layer which component will connect to
            via its meta node instance.
        :return: newly created component meta node instance.
        :rtype: meta_component.NoddleComponent
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
            initialized_descriptor = self.configuration.initialize_module_descriptor(
                module_type_name
            )
            if no_module_type:
                meta.attribute(constants.MODULE_TYPE_ATTR).set(module_type_name)
            self._original_descriptor = (
                self.configuration.modules_manager().load_module_descriptor(
                    module_type_name
                )
            )
            if self._meta is not None and self._meta.exists():
                data = self._meta.raw_descriptor_data()
                translated_data = parse_raw_descriptor(data)
                scene_data = migrate_to_latest_version(
                    translated_data, original_descriptor=initialized_descriptor
                )
                initialized_descriptor.update(scene_data)
            self._descriptor = initialized_descriptor
        elif descriptor and meta:
            self._original_descriptor = copy.deepcopy(descriptor)
            self._descriptor = self._descriptor_from_scene()
        else:
            self._original_descriptor = descriptor
            self._descriptor = copy.deepcopy(descriptor)
