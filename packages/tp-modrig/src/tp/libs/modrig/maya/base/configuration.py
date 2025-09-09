from __future__ import annotations

import os
import typing
import traceback
from typing import Any
from typing import cast

from loguru import logger

from tp.libs.python import osplatform
from tp.libs.plugin import PluginsManager

from . import constants
from .settings import ModRigSettings
from .build_script import BaseBuildScript
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
    _BUILD_SCRIPTS_MANAGER: PluginsManager | None = None

    BUILD_SCRIPTS_ENV_VAR = "MODRIG_BUILD_SCRIPTS_PATHS"

    def __init__(self):
        super().__init__()

        self._config_cache: dict[str, Any] = {}
        self._current_naming_preset: Preset | None = None
        self._use_containers = False
        self._blackbox = True
        self._use_proxy_attributes = True
        self._build_scripts: list[BaseBuildScript] = []
        self._preferences_interface = cast(ModRigSettings, ModRigSettings())

        self._initialize_managers()
        self._initialize_environment()

    @property
    def preferences_interface(self) -> ModRigSettings:
        """The ModRig preferences interface instance."""

        return self._preferences_interface

    @property
    def use_containers(self) -> bool:
        """Whether to use Maya containers for grouping rig elements."""

        return self._use_containers

    @property
    def blackbox(self) -> bool:
        """Whether to set container as blackbox."""

        return self._blackbox

    @property
    def use_proxy_attributes(self) -> bool:
        """Whether to use proxy attributes for rig elements."""

        return self._use_proxy_attributes

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
        self.initialize_build_scripts_manager(force_reload=force_reload)

    def _initialize_environment(self):
        """Handle the loading and setup of Noddle preferences from settings."""

        self._config_cache = self._preferences_interface.settings

        self.set_naming_preset_by_name(
            self._config_cache.get("defaultNamingPreset", constants.DEFAULT_PRESET_NAME)
        )

    # === Naming Manager === #

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

    # === Modules Manager === #

    @classmethod
    def modules_manager(cls) -> ModulesManager:
        """Provide a class-level method to retrieve the singleton instance of
        the `ModulesManager`.

        Returns:
            The global instance of `ModulesManager` used within the rig.
        """

        return cls._MODULES_MANAGER

    def modules_paths(self) -> list[str]:
        """Retrieve the file paths of all available modules managed by the
        modules manager.

        Returns:
            A list containing the file paths of all modules as strings.
        """

        return self._MODULES_MANAGER.modules_paths()

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

    def initialize_module_descriptor(
        self, module_type_name: str
    ) -> tuple[ModuleDescriptor | None, ModuleDescriptor | None]:
        """Initialize a module descriptor for the specified module type name.

        The function interacts with the modules manager to create and
        retrieve a descriptor for the requested module type. This
        descriptor encapsulates details necessary for handling the module.

        Args:
            module_type_name: The name of the module type for which the
                descriptor is to be initialized.

        Returns:
            A tuple containing:
                - The loaded `ModuleDescriptor` if successful; `None` if
                    loading failed.
                - The original `ModuleDescriptor` if successful; `None` if
                    loading failed.
        """

        return self._MODULES_MANAGER.initialize_module_descriptor(module_type_name)

    # === Build Scripts Manager === #

    @staticmethod
    def build_script_paths() -> list[str]:
        """Retrieve the file paths of all available build scripts managed by
        the build scripts manager.

        Returns:
            A list containing the file paths of all build scripts as strings.
        """

        return [
            path
            for path in os.environ.get(
                RigConfiguration.BUILD_SCRIPTS_ENV_VAR, ""
            ).split(os.pathsep)
            if path
        ]

    @property
    def build_scripts(self) -> list[BaseBuildScript]:
        """The list of available build scripts."""

        return self._build_scripts

    def set_build_scripts(self, script_ids: list[str | list[str]]):
        """Set the list of active build scripts by their IDs.

        Args:
            script_ids: List of build script IDs to set as active.
        """

        self._build_scripts.clear()
        for build_script_id in script_ids:
            if isinstance(build_script_id, list):
                build_script_id = build_script_id[0]
            build_script = cast(
                BaseBuildScript, self._BUILD_SCRIPTS_MANAGER.get_plugin(build_script_id)
            )
            if build_script is not None:
                self._build_scripts.append(build_script)

    def add_build_script(self, script_id: str) -> bool:
        """Add a build script to the list of active build scripts by its ID.

        Args:
            script_id: The ID of the build script to add.

        Returns:
            True if the build script was successfully added; False otherwise.
        """

        if any(i.id == script_id for i in self._build_scripts):
            return True

        build_script = cast(
            BaseBuildScript, self._BUILD_SCRIPTS_MANAGER.get_plugin(script_id)
        )
        if build_script is not None:
            self._build_scripts.append(build_script)
            return True

        return False

    def remove_build_script(self, script_id: str) -> bool:
        """Remove a build script from the list of active build scripts by its ID.

        Args:
            script_id: The ID of the build script to remove.

        Returns:
            True if the build script was successfully removed; False otherwise.
        """

        default_user_scripts = self._preferences_interface.user_build_scripts()
        if script_id in default_user_scripts:
            logger.debug(f"Cannot remove default user build script: {script_id}")
            return False

        for build_script in self._build_scripts:
            if build_script.id != script_id:
                continue
            self._build_scripts.remove(build_script)
            build_script.delete()
            return True

        return False

    def initialize_build_scripts_manager(self, force_reload: bool = False):
        """Initialize the build scripts manager for the class, ensuring the
        availability of the necessary build scripts.

        If `force_reload` is set to True, or if the build scripts manager is not
        already initialized, it creates a new instance of the build scripts
        manager and refreshes it.

        Args:
            force_reload: If True, forces reloading and reinitialization of
                the build scripts manager.
        """

        def _handle_build_script_register_failure(path: str) -> bool:
            """Handle failures when registering a build script.

            Args:
                The path of the build script that failed to register.

            Returns:
                False always to indicate failure.
            """

            logger.error(
                f"{traceback.format_exc()}\nFailed to load build script: {path}"
            )
            return False

        if force_reload or RigConfiguration._BUILD_SCRIPTS_MANAGER is not None:
            script_paths = self.build_script_paths()
            script_paths.extend(self._preferences_interface.user_build_script_paths())

            osplatform.add_paths_to_env("TP_DCC_BASE_PATHS", script_paths)

            manager = PluginsManager(interfaces=[BaseBuildScript], variable_name="id")
            manager.register_by_environment_variable(
                RigConfiguration.BUILD_SCRIPTS_ENV_VAR
            )
            manager.register_paths(
                self._preferences_interface.user_build_script_paths(),
                error_callback=_handle_build_script_register_failure,
            )
            manager.load_all_plugins()

            self.__class__._BUILD_SCRIPTS_MANAGER = manager
