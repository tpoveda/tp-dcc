from __future__ import annotations

import copy
import typing
from typing import Any

from loguru import logger

from . import constants, errors

if typing.TYPE_CHECKING:
    from .setting import SettingObject
    from .manager import PreferencesManager


class PreferenceInterface:
    """Base class for interfacing with YAML-based preference settings.

    This class provides an abstraction layer between client code and direct
    access to raw preference files (settings YAML files).

    It allows tools, packages, or systems to easily manage their own
    preferences without worrying about file paths, formats, or overrides.

    **Key Responsibilities:**
    - Loading a `SettingObject` from a registered preferences root.
    - Providing cached access to settings (with refresh support).
    - Saving modified settings.
    - Supporting revert functionality to restore settings if needed.
    - Allowing structured access to individual preference keys.

    **Usage Notes:**
    - Each subclass should define its own `id` and `_relative_path` uniquely.
    - Interfaces should only manage settings inside their own package domain.
    - Interfaces should NOT directly modify other package preferences.
      Use `self.preference.interface('other_package')` to access others safely
      if needed.

    This class should NOT be instantiated manually.
    Always use `PreferencesManager.interface()` to retrieve instances.

    Example:
    ```python
    interface = preference_manager.interface('mytool')
    setting_obj = interface.settings()
    setting_obj.set('optionA', True)
    interface.save_settings()
    ```

    See also: `tp.preferences.manager.PreferencesManager`,
        `tp.preferences.setting.SettingObject`.
    """

    # Required to uniquely identify this interface
    # (used for lookup/registration)
    id: str = ""

    # Default relative path to the YAML settings file this interface manages
    # (should be overridden in subclasses).
    _relative_path: str = ""

    # Cached SettingObject instance.
    _settings: SettingObject | None = None

    def __init__(self, preferences_manager: PreferencesManager):
        """Initialize the `PreferenceInterface`.

        Args:
            preferences_manager: The main preferences manager instance.
        """

        self._preferences_manager = preferences_manager
        self._revert_settings: SettingObject | None = None

    def settings(
        self,
        name: str | None = None,
        fallback: Any | None = None,
        relative_path: str | None = None,
        root: str | None = None,
        refresh: bool = False,
    ) -> Any:
        """Load or return the cached `SettingObject`.

        Args:
            name: Specific setting key within the nested "settings" key to
                return.
            fallback: Fallback value to return if the setting is not found.
            relative_path: Relative path to the setting. For example,
                'interface/sid'. Defaults to self._relative_path).
            root: Root name to restrict search to a specific root. If None,
                all roots are searched.
            refresh: Force reload from disk.

        Returns:
            The loaded or cached settings object, or specific key value
            if `name` is provided.
        """

        relative_path = relative_path or self._relative_path

        if self._settings is None or refresh:
            self._settings = self._preferences_manager.find_setting(
                relative_path, root=root
            )

        if name is not None:
            settings_data = self._settings.get(constants.SETTINGS_DESCRIPTOR_KEY, {})
            if name not in settings_data:
                if fallback is not None:
                    return fallback
                raise errors.SettingsNameDoesntExistError(
                    f"Failed to find setting '{name}' in file '{relative_path}'"
                )
            return settings_data[name]

        self._setup_revert()

        return self._settings

    def save(self, indent: bool = True, sort: bool = False) -> str:
        """Save the current settings to disk.

        Args:
            indent (bool): Whether to pretty-print the YAML file.
            sort (bool): Whether to sort keys alphabetically.

        Returns:
            str: Full path to the saved settings file.
        """
        logger.debug(f"Saving settings for `PreferenceInterface`: '{self}'")
        path = self.settings().save(indent=indent, sort=sort)

        self._revert_settings = None

        return path

    def refresh(self) -> None:
        """Force reloading settings from disk."""

        self.settings(refresh=True)

    def revert(self) -> bool:
        """Revert settings to the previously cached state.

        Returns:
            True if settings were reverted, False if no revert state was found.
        """

        if not self._revert_settings:
            return False

        self._settings.clear()
        self._settings.update(self._revert_settings)

        self.save()

        return True

    def is_valid(self) -> bool:
        """Check if the current settings are valid (file exists).

        Returns:
            True if settings are valid;False otherwise.
        """

        return self.settings().is_valid()

    def _setup_revert(self) -> None:
        """Internal method to set up a revert snapshot.

        Revert settings are only created after loading and are cleared when
        saving.
        """

        if not self._revert_settings:
            self._revert_settings = copy.deepcopy(self._settings)
