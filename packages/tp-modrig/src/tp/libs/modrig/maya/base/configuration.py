from __future__ import annotations

import typing
from typing import Any
from typing import cast

from . import constants
from .settings import ModRigSettings
from .namingpresets import PresetsManager, Preset

if typing.TYPE_CHECKING:
    from .rig import Rig
    from tp.libs.naming.manager import NameManager


class RigConfiguration:
    """Base class for rig configuration and rig managers access."""

    _NAMING_PRESET_MANAGER: PresetsManager | None = None

    def __init__(self):
        super().__init__()

        self._config_cache: dict[str, Any] = {}
        self._current_naming_preset: Preset | None = None
        self._preferences_interface = cast(ModRigSettings, ModRigSettings())

        self._initialize_managers()
        self._initialize_environment()

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

    def update_from_rig(self, rig: Rig) -> dict:
        """Updates this configuration from the given scene rig instance.

        :param rig: rig instance to pull configuration data from.
        :return: updated configuration dictionary.
        """

        cache = rig.cached_configuration()
        self.apply_settings(cache)
        return cache

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

    def _initialize_environment(self):
        """Handle the loading and setup of Noddle preferences from settings."""

        self.set_naming_preset_by_name(
            self._config_cache.get("defaultNamingPreset", constants.DEFAULT_PRESET_NAME)
        )
