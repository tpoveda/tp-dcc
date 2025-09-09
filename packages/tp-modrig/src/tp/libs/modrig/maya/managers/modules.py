from __future__ import annotations

import os
import copy
import typing
import inspect
import pathlib
from typing import cast
from typing import TypedDict

from loguru import logger

from tp.libs.plugin import PluginsManager
from tp.libs.python import decorators, yamlio

from ..base.module import Module
from ..base import constants, errors, settings
from ..descriptors.module import load_descriptor, ModuleDescriptor

if typing.TYPE_CHECKING:
    from ..base.rig import Rig
    from ..meta.module import MetaModule


class RegisteredModule(TypedDict):
    """Represents a typed dictionary for a registered module.

    This class is used to define the structure and expected keys when
    dealing with  registered modules.

    It specifies the attributes that must be present for a module to be
    considered registered, along with their respective types and descriptions.

    Attributes:
        module_class: The class reference of the registered module.
        path: The file system path where the module resides.
        descriptor_name: The name of the descriptor associated with the module.
    """

    module_class: type[Module]
    path: str
    descriptor_name: str


class RegisteredDescriptor(TypedDict):
    """Represents a registered descriptor with a specific path and associated data.

    This class is a specialized `TypedDict` designed to associate a file
    path with its corresponding data. It can be used to define mappings
    between resources and their metadata or properties.

    Attributes:
        path: The file path or identifier corresponding to the descriptor.
        data: The metadata or associated information linked to the specified
            path.
    """

    path: str
    data: dict


class ModulesManager(metaclass=decorators.Singleton):
    """Manages the discovery, registration, and interaction of modules and their
    descriptors within the system.

    This class is responsible for managing modules and their associated
    descriptors, performing tasks such as registration, discovery,
    retrieval, and initialization. It integrates with the `PluginsManager`
    for plugin and module management. Modules and descriptors are discovered
    through environmental variables, configured paths, and metadata.

    Attributes:
        _modules: A dictionary mapping module type names to their
            corresponding registered module definitions.
        _descriptors: A dictionary mapping descriptor type names to their
            corresponding descriptor definitions.
        _manager: The plugin manager responsible for handling modules and
            their integrations.
        _preferences_interface: The settings interface used to manage
            module-related preferences and configurations.
    """

    def __init__(self):
        super().__init__()

        self._modules: dict[str, RegisteredModule] = {}
        self._descriptors: dict[str, RegisteredDescriptor] = {}
        self._manager: PluginsManager | None = None
        self._preferences_interface = cast(
            settings.ModRigSettings, settings.ModRigSettings()
        )

    @property
    def modules(self) -> dict[str, RegisteredModule]:
        """The registered modules."""

        return self._modules

    @property
    def descriptors(self) -> dict[str, RegisteredDescriptor]:
        """The registered descriptors."""

        return self._descriptors

    def refresh(self, force: bool = False) -> bool:
        """Refresh the state of the module manager by clearing its current
        modules, descriptors and reinitializing the manager with the
        appropriate plugin and modules.

        This method discovers all the modules again and reloads the
        state if necessary based on the specified parameters.

        Args:
            force: If True, forces the refresh operation even if the modules
                are already populated.

        Returns:
            True if the refresh operation was performed, False otherwise.
        """

        if self._modules and not force:
            return False

        self._modules.clear()
        self._descriptors.clear()
        self._manager = PluginsManager(
            interfaces=[Module], variable_name="id", name="ModRigModules"
        )

        self.discover_modules()

        return True

    def discover_modules(self):
        """Discover and registers modules and their associated descriptors.

        This method performs the discovery process for modules and their
        associated descriptors. It registers module paths from environment
        variables, checks provided paths for descriptor files, loads
        descriptors into memory, and stores them alongside the related
        modules.

        It also integrates plugin modules, assigning unique identifiers
        and determining icons for the loaded modules.
        """

        self._manager.register_by_environment_variable(constants.MODULES_ENV_VAR_KEY)
        module_paths = self._preferences_interface.module_paths()
        self._manager.register_paths(module_paths)
        descriptor_paths = os.environ.get(constants.DESCRIPTORS_ENV_VAR_KEY, "").split(
            os.pathsep
        )
        for descriptor_path in descriptor_paths + module_paths:
            for root, dirs, files in os.walk(descriptor_path):
                for file_name in files:
                    if not file_name.endswith(constants.DESCRIPTOR_EXTENSION):
                        continue
                    descriptor_base_name = file_name.split(os.extsep)[0]
                    if descriptor_base_name in self._descriptors:
                        continue
                    descriptor_path = pathlib.Path(root, file_name).as_posix()
                    cache = self._load_descriptor_from_path(descriptor_path)
                    self._descriptors[cache["type"]] = RegisteredDescriptor(
                        path=descriptor_path, data=cache
                    )

        for class_obj in self._manager.plugin_classes:
            class_id = class_obj.id if hasattr(class_obj, "id") else None
            if not class_id:
                class_obj.id = class_obj.__name__
                class_id = class_obj.id
            class_path = inspect.getfile(class_obj)
            if class_id in self._modules:
                continue

            if hasattr(class_obj, "ICON_PATH"):
                icon_path = class_obj.ICON_PATH
                if not icon_path:
                    icon_name = os.path.splitext(os.path.basename(class_path))[0]
                    icon_path = os.path.join(
                        os.path.dirname(class_path), f"{icon_name}.png"
                    )
                    icon_path = icon_path if os.path.exists(icon_path) else ""
                class_obj.ICON_PATH = icon_path

            # noinspection PyTypeChecker
            self._modules[class_id] = RegisteredModule(
                module_class=class_obj,
                path=class_path,
                descriptor_name=class_id,
            )

    def modules_paths(self) -> list[str]:
        """Retrieve a list of paths related to the 'noddle' module managed by
        the internal manager.

        Returns:
            A list of paths associated with the 'noddle' module.
        """

        return self._manager.paths

    def module_data(self, module_type_name: str) -> dict | None:
        """Retrieve module data for a given module type name.

        This method looks up and returns the module data associated with the
        provided module type name.

        Args:
            module_type_name: The name of the module type for which the
                associated data is being requested.

        Returns:
            A dictionary containing module data if the specified module type
            name exists; None otherwise.
        """

        return self._modules.get(module_type_name)

    def load_module_descriptor(self, module_type_name: str) -> dict:
        """Load the descriptor data for a given module type name.

        The function retrieves the descriptor associated with the specified
        module type name and returns it as a deep copy.

        Args:
            module_type_name: The name of the module type whose descriptor
                is to be loaded.

        Returns:
            dict: A deep copy of the descriptor data of the specified module
                type.

        Raises:
            ValueError: If the specified module type name is not available
                in `_descriptors` or if there are other issues while
                retrieving the descriptor data.
        """

        if module_type_name not in self._descriptors:
            raise ValueError(
                "Requested module is not available. Requested: {}; "
                "Available: {}".format(module_type_name, list(self._descriptors.keys()))
            )

        try:
            descriptor_data = self._descriptors[
                self._modules[module_type_name]["descriptor_name"]
            ]
            return copy.deepcopy(descriptor_data["data"])
        except ValueError:
            logger.error(
                f"Failed to load module descriptor: {module_type_name}",
                exc_info=True,
            )
            raise ValueError(f"Failed to load module descriptor: {module_type_name}")

    def initialize_module_descriptor(
        self, module_type_name: str
    ) -> tuple[ModuleDescriptor | None, ModuleDescriptor | None]:
        """Initialize the module descriptor for a given module type.

        This involves loading the descriptor data and module data,
        verifying their existence, and returning a properly loaded descriptor.

        Args:
            module_type_name: A string representing the type of the module
                for which the module descriptor is to be initialized.

        Returns:
            A tuple containing:
                - The loaded `ModuleDescriptor` if successful; `None` if
                    loading failed.
                - The original `ModuleDescriptor` if successful; `None` if
                    loading failed.
        """

        descriptor_data = self.load_module_descriptor(module_type_name)
        module_data = self.module_data(module_type_name)
        if not descriptor_data:
            logger.error(
                f"Was not possible to initialize module descriptor "
                f'for "{module_type_name}". No descriptor data found.'
            )
            return None, None
        if not module_data:
            logger.error(
                f"Was not possible to initialize module descriptor "
                f'for "{module_type_name}". No module data found.'
            )
            return None, None

        original_descriptor_data = ModuleDescriptor(
            descriptor_data, path=module_data["path"]
        )

        return load_descriptor(
            descriptor_data, original_descriptor_data, path=module_data["path"]
        ), original_descriptor_data

    def find_module_class_by_type(self, module_type_name: str) -> type[Module] | None:
        """Find and returns the module class corresponding to the given
        module type name.

        This method retrieves the module class for a given `module_type_name`
        from the stored mapping of available modules.

        Args:
            module_type_name: The name of the module type to find.

        Returns:
            The module class associated with the given `module_type_name`;
                `None` if not found.

        Raises:
            ValueError: If the specified `module_type_name` does not exist in
                the available modules.
        """

        try:
            return self._modules[module_type_name]["module_class"]
        except KeyError:
            raise ValueError(
                f"Module requested is not available. "
                f"Requested: {module_type_name}; "
                f"Available: {list(self._modules.keys())}"
            )

    def from_meta_node(self, rig: Rig, meta: MetaModule) -> Module:
        """Converts a meta-node into a module class representation for the
        specified rig.

        This function processes the provided meta-node, retrieves its
        associated root transform, and determines the module type by reading
        the relevant metadata attribute.

        Using this information, it initializes and returns an instance of
        the appropriate module class.

        Args:
            rig: The rig structure associated with the meta-node instance.
            meta: The meta-node object that contains the metadata and
                attributes required for module initialization.

        Returns:
            Module: An instance of the newly created module class
                corresponding to the meta-node type.

        Raises:
            MissingMetaNodeRootTransform: If the meta-node instance does not
                have a valid root transform or if the transform could not be
                retrieved.
        """

        root = meta.root_transform()
        if not root:
            raise errors.MissingMetaNodeRootTransform(meta.fullPathName())

        module_type_name = meta.attribute(constants.MODULE_TYPE_ATTR).asString()
        new_module_class = self.find_module_class_by_type(module_type_name)
        new_module = new_module_class(rig, meta=meta)

        return new_module

    @staticmethod
    def _load_descriptor_from_path(descriptor_path: str) -> dict | None:
        """Load a YAML descriptor file from the given path and returns its
        parsed content as a dictionary.

        This method is intended for internal usage as a utility to read
        configuration or module descriptor files in YAML format.

        Args:
            descriptor_path: The file path to the descriptor YAML file.

        Returns:
            The parsed content of the YAML file as a dictionary; `None`
            if the file could not be loaded or parsed.

        Raises:
            ValueError: If the file cannot be read or parsed successfully.
        """

        try:
            return yamlio.read_file(descriptor_path)
        except ValueError:
            logger.error(
                f"Failed to load module descriptor: {descriptor_path}", exc_info=True
            )
            raise ValueError(f"Failed to load module descriptor: {descriptor_path}")
