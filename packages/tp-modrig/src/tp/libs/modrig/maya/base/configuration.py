from __future__ import annotations

import typing
from typing import Any
from typing import cast

from . import constants
from .settings import ModRigSettings
from .namingpresets import PresetsManager, Preset
from ..managers.modules import ModulesManager

if typing.TYPE_CHECKING:
    from tp.libs.naming.manager import NameManager
    from .rig import Rig
    from ..descriptors.module import ModuleDescriptor


class RigConfiguration:
    """Base class for rig configuration and rig managers access."""

    _NAMING_PRESET_MANAGER: PresetsManager | None = None
    _MODULES_MANAGER: ModulesManager | None = None

    def __init__(self):
        super().__init__()

        self._config_cache: dict[str, Any] = {}
        self._current_naming_preset: Preset | None = None
        self._preferences_interface = cast(ModRigSettings, ModRigSettings())

        self._initialize_managers()
        self._initialize_environment()

    @classmethod
    def name_presets_manager(cls) -> PresetsManager:
        """Return the naming presets manager for the class.

        Provide access to the private attribute `_NAMING_PRESET_MANAGER`
        responsible for managing naming presets within the class.

        Returns:
            An instance of PresetsManager responsible for handling naming
                presets.
        """

        return cls._NAMING_PRESET_MANAGER

    @classmethod
    def modules_manager(cls) -> ModulesManager:
        """Provide a class-level method to retrieve the singleton instance of
        the `ModulesManager`.

        Returns:
            The global instance of `ModulesManager` used within the rig.
        """

        return cls._MODULES_MANAGER

    @property
    def preferences_interface(self) -> ModRigSettings:
        """The ModRig preferences interface instance."""

        return self._preferences_interface

    @property
    def current_naming_preset(self) -> Preset | None:
        """The current naming preset."""

        return self._current_naming_preset

    def find_name_manager_for_type(
        self, mod_rig_type: str, preset_name: str | None = None
    ) -> NameManager | None:
        """Find and return the naming convention manager used to handle the
        nomenclature for the given type.

        Args:
            mod_rig_type: ModRig type to search name manager for.
            preset_name: The name of the preset to use for finding the name
                manager.

        Returns:
            The naming manager instance for the given type; None if not found.
        """

        preset = self._current_naming_preset
        if preset_name:
            preset = self._NAMING_PRESET_MANAGER.find_preset(preset_name)

        return preset.find_name_manager_for_type(mod_rig_type)

    def set_naming_preset_by_name(self, name: str):
        """Set the current naming convention preset by the given name.

        Args:
            name: Name of the preset to set as active.
        """

        preset = self._NAMING_PRESET_MANAGER.find_preset(name)
        if preset is None:
            preset = self._NAMING_PRESET_MANAGER.find_preset(
                constants.DEFAULT_PRESET_NAME
            )

        self._current_naming_preset = preset

    def modules_paths(self) -> list[str]:
        """Retrieve the file paths of all available modules managed by the
        modules manager.

        Returns:
            A list containing the file paths of all modules as strings.
        """

        return self._MODULES_MANAGER.modules_paths()

    def update_from_rig(self, rig: Rig) -> dict:
        """Updates this configuration from the given scene rig instance.

        :param rig: rig instance to pull configuration data from.
        :return: updated configuration dictionary.
        """

        cache = rig.cached_configuration()
        self.apply_settings(cache)
        return cache

    def apply_settings(self, state: dict[str, Any], rig: Rig | None = None):
        """Applies settings to the current object based on a given state
        configuration dictionary and an optional rig.

        Args:
            state: A dictionary containing state configuration.
            rig: Rig that will be used to apply settings to. If None,
                no rig-specific settings will be applied.
        """

        if rig is not None:
            pass

        try:
            naming_preset = state["namingPreset"]
            self.set_naming_preset_by_name(naming_preset)
        except KeyError:
            pass

    def initialize_naming_manager(self, force_reload: bool = False):
        """Initialize the naming manager.

        Args:
            force_reload: Whether to force the reloading of the naming manager.
        """

        if self.__class__._NAMING_PRESET_MANAGER and not force_reload:
            return

        presets_manager = PresetsManager()
        hierarchy = self._preferences_interface.naming_preset_hierarchy()
        presets_manager.load_from_hierarchy(hierarchy)
        self.__class__._NAMING_PRESET_MANAGER = presets_manager

    def initialize_modules_manager(self, force_reload: bool = False):
        """Initialize the modules manager for the class, ensuring the
        availability of the necessary modules.

        If `force_reload` is set to True, or if the modules manager is not
        already initialized, it creates a new instance of the modules
        manager and refreshes it.

        Args:
            force_reload: If True, forces reloading and reinitialization of
                the module manager.
        """

        if force_reload or self.__class__._MODULES_MANAGER is None:
            modules_manager = cast(ModulesManager, ModulesManager())
            modules_manager.refresh()
            RigConfiguration._MODULES_MANAGER = modules_manager

    def initialize_module_descriptor(self, module_type_name: str) -> ModuleDescriptor:
        """Initialize a module descriptor for the specified module type name.

        The function interacts with the modules manager to create and
        retrieve a descriptor for the requested module type. This
        descriptor encapsulates details necessary for handling the module.

        Args:
            module_type_name: The name of the module type for which the
                descriptor is to be initialized.

        Returns:
            An object containing metadata and details associated with the
                specified module type.
        """

        return self._MODULES_MANAGER.initialize_module_descriptor(module_type_name)

    def serialize(self, rig: Rig) -> dict:
        """Serialize current configuration data.

        Args:
            rig: The rig this configuration belongs to.

        Returns:
            Serialized data as a dictionary.
        """

        cache = self._config_cache
        overrides = {}

        return overrides

    def _initialize_managers(self, force_reload: bool = False):
        """Handle the initialization of all the configuration managers.

        Args:
            force_reload: Whether to force the reloading of the managers.
        """

        self.initialize_naming_manager(force_reload=force_reload)
        self.initialize_modules_manager(force_reload=force_reload)

    def _initialize_environment(self):
        """Handle the loading and setup of Noddle preferences from settings."""

        self._config_cache = self._preferences_interface.settings

        self.set_naming_preset_by_name(
            self._config_cache.get("defaultNamingPreset", constants.DEFAULT_PRESET_NAME)
        )
