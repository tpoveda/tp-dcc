from __future__ import annotations

import os
import typing
from typing import cast
from pathlib import Path
from string import Template
from collections.abc import Iterator

import yaml
from loguru import logger

from tp.bootstrap.utils import fileio
from tp.libs.python import osplatform, folder
from tp.libs.plugin import PluginsManager

from . import constants, errors
from .setting import SettingObject
from .interface import PreferenceInterface

if typing.TYPE_CHECKING:
    from tp.bootstrap.core.manager import PackagesManager


_preferences_manager: PreferencesManager | None = None


def current_instance() -> PreferencesManager | None:
    """Get the current instance of the PreferencesManager.

    Returns:
        The current instance of the PreferencesManager.
    """

    global _preferences_manager

    return _preferences_manager


def set_instance(manager: PreferencesManager):
    """Set the current instance of the PreferencesManager.

    Args:
        manager: The PreferencesManager instance to set.

    Raises:
        RuntimeError: If the PreferencesManager has already been initialized.
    """

    global _preferences_manager

    _preferences_manager = manager


class PreferencesManager:
    """Manages all preference loading, override merging, and interface access
    for TP DCC package preferences.

    The PreferencesManager:
    - Handles multiple roots (project-specific overrides,
        package defaults, ...).
    - Searches for preferences across roots in priority order.
    - Loads YAML preferences into `SettingObject` instances.
    - Merges override preferences dynamically.
    - Acts as the main registry for preference interfaces if needed.

    Typical usage:
    - Add the project overrides root (highest priority).
    - Add package roots (lower priority).
    - Access preferences through interfaces that query this manager.
    """

    _EXTENSION = ".yaml"
    _DEFAULT_USER_PREFERENCE_NAME = "user"

    def __init__(self, packages_manager: PackagesManager):
        """Initialize the PreferencesManager."""

        super().__init__()

        self._packages_manager = packages_manager
        self._roots: dict[str, str] = {}
        self._interfaces_manager = PluginsManager(
            interfaces=[PreferenceInterface], variable_name="id", name="prefs"
        )

        self._resolve_interfaces()
        self._resolve_root_locations()

    def iterate_package_preference_roots(self) -> Iterator[str]:
        """Iterate over all package preference roots.

        Yields:
            The path of each package preference root.
        """

        for package in self._packages_manager.resolver.packages:
            preferences_path = Path(package.root).joinpath(constants.PREFERENCES_FOLDER)
            if not preferences_path.exists():
                continue
            yield str(preferences_path)

    def iterate_package_preference_paths(self):
        """Iterate over all package preference paths.

        Yields:
            An iterator over the string paths of valid "prefs" directories
            derived from package preference roots.
        """

        for preference_root in self.iterate_package_preference_roots():
            preferences_path = Path(preference_root).joinpath("prefs")
            if not preferences_path.exists():
                continue
            yield str(preferences_path)

    def root(self, name: str) -> str:
        """Get the path of a preference root.

        Args:
            name: Logical name of the root (e.g., 'project',
                'package: tp-xyz').

        Returns:
            The path of the preference root.

        Raises:
            errors.RootDoesNotExistError: If the root name does not exist.
        """

        if name not in self._roots:
            raise errors.RootDoesNotExistError(f"Root does not exist: {name}")

        return self._resolve_path(self._roots[name])

    def root_name_for_path(self, path: str) -> str:
        """Get the logical name of a preference root from its path.

        Args:
            path: Filesystem path to the root.

        Returns:
            The logical name of the preference root.

        Raises:
            errors.RootDoesNotExistError: If the root path does not exist.
        """

        path = self._resolve_path(path)
        for name, root in self._roots.items():
            if path == self._resolve_path(root):
                return name

        raise errors.RootDoesNotExistError(f"Root does not exist: {path}")

    def add_root(self, name: str, path: str):
        """Add a new preference root.

        Args:
            name: Logical name of the root (e.g., 'project',
                'package: tp-xyz').
            path: Filesystem path to the root.

        Raises:
            errors.RootAlreadyExistsError: If the root name already exists.
            errors.RootDoesNotExistError: If the root path does not exist.
            FileNotFoundError: If the root path does not exist.
        """

        if name in self._roots:
            raise errors.RootAlreadyExistsError(f"Root already exists: {name}")

        resolved_path = Path(self._resolve_path(path))
        if not resolved_path.exists():
            raise errors.RootDoesNotExistError(
                f'Root path does not exist: "{resolved_path}"'
            )

        self._roots[name] = str(path)

    def create_setting(
        self, relative_path: str, root: str, data: dict
    ) -> SettingObject:
        """Create a new setting (or update an existing one) and save it to
        disk.

        Args:
            relative_path: Relative path inside the root.
            root: Name of the root to save to.
            data: Data to write into the setting.

        Returns:
            SettingObject: The saved setting object.
        """

        relative_path = self._ensure_extension(
            relative_path,
            self._EXTENSION,
        )

        # Try to find existing setting, or create a new one
        setting = self.find_setting(relative_path, root=root)
        setting.data.update(data)

        return setting

    def find_setting(
        self,
        relative_path: str,
        root: str | None = None,
        name: str | None = None,
        extension: str | None = None,
    ) -> SettingObject:
        """Find a setting object by searching registered roots.

        Searches in reverse order of registration for overrides. If a specific
        root is given, only that root will be searched.

        Args:
            relative_path: Relative path to the setting file,
                e.g., "tools/mytool/settings"
            root: Specific root name to search. If None, all roots are
                searched.
            name: Specific setting key within the nested "settings" key to
                return.
            extension: File extension to use (default is '.yaml').

        Returns:
            A SettingObject instance, valid or empty if not found.
        """

        relative_path = self._ensure_extension(
            str(relative_path), extension or self._EXTENSION
        )

        merged_data = {}
        sources = {}
        first_writable_root = None

        search_roots = (
            [(root, self._roots[root])] if root else list(reversed(self._roots.items()))
        )

        for root_name, root_path in search_roots:
            resolved = self._resolve_path(root_path)
            full_path = Path(resolved).joinpath(relative_path)
            if not full_path.exists():
                continue

            with open(full_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            merged_data = self._deep_merge_dicts(merged_data, data)
            sources[root_name] = str(full_path)

            if (
                first_writable_root is None
                and root_name.startswith("user")
                or root_name.startswith("project")
            ):
                first_writable_root = root_name

        found_setting = SettingObject(
            relative_path=relative_path,
            sources=sources,
            active_root=first_writable_root,
            **merged_data,
        )

        if name is not None:
            settings = found_setting.get(constants.SETTINGS_DESCRIPTOR_KEY, {})
            if name not in settings:
                raise errors.SettingsNameDoesntExistError(
                    f"Failed to find setting '{name}' in file '{found_setting}'"
                )
            return settings[name]

        return found_setting

    def has_interface(self, interface_id: str) -> bool:
        """Returns whether a preference interface with the given name exists.

        Args:
            interface_id: ID of the interface to retrieve.

        Returns:
            True if the setting interface exists; False otherwise.
        """

        return self._interfaces_manager.get_plugin(interface_id) is not None

    def interface(self, interface_id: str) -> PreferenceInterface:
        """Returns the preference interface instance registered with the given
        ID.

        Args:
            interface_id: ID of the preference interface instance to retrieve.

        Returns:
            Preference interface instance.

        Raises:
            ValueError: if the interface with given ID is not registered.
        """

        interface_instance = self._interfaces_manager.loaded_plugin(interface_id)
        if interface_instance is None:
            interface_class = self._interfaces_manager.get_plugin(interface_id)
            if interface_class is None:
                raise ValueError(
                    f"Missing preference interface with  `id`: {interface_id}"
                )
            interface_instance = self._interfaces_manager.load_plugin(
                interface_id, preferences_manager=self
            )

        return cast(PreferenceInterface, interface_instance)

    def interface_ids(self) -> list[str]:
        """Returns the list of all registered preference interface IDs.

        Returns:
            List of registered preference interface IDs.
        """

        return self._interfaces_manager.plugin_ids

    # noinspection PyMethodMayBeStatic
    def _ensure_extension(self, path: str, ext: str = ".yaml") -> str:
        """Ensure the path ends with the given extension.

        Args:
            path: The path to check.
            ext: The extension to ensure (default is '.yaml').

        Returns:
            The path with the ensured extension.
        """

        if not path.endswith(ext):
            return f"{path}{ext}"
        return path

    # noinspection PyMethodMayBeStatic
    def _resolve_path(self, path_to_resolve: str) -> str:
        """Internal function that resolves a root path by patching Windows
        user folder issues, expanding variables, and normalizing slashes.

        Args:
            path_to_resolve: The path to resolve.

        Returns:
            str: The resolved root path.
        """

        resolved_path = osplatform.patch_windows_user_home(path_to_resolve)
        expanded = os.path.expandvars(resolved_path)
        path = Path(expanded).expanduser().resolve()

        return str(path).replace("\\", "/")

    def _resolve_path_template(self, template_str: str, root_name: str) -> str:
        """Internal function that resolves environment-variable template
        paths safely.

        Args:
            template_str: A string like "$TP_DCC_ROOT/Tools/configs"
            root_name: Name of the root (used for logging)

        Returns:
            Fully expanded path string.

        Raises:
            KeyError if substitution fails.
        """

        try:
            resolved = Template(template_str).substitute(os.environ)
            return self._resolve_path(resolved)
        except KeyError as e:
            logger.warning(
                f"Missing env variable '{e.args[0]}' while resolving "
                f"root '{root_name}': {template_str}"
            )
            raise

    def _resolve_interfaces(self):
        """Resolve all interfaces classes found within the different TP DCC
        Python packages preferences folders.
        """

        for preference_folder in self.iterate_package_preference_roots():
            interfaces_folder = Path(preference_folder).joinpath(
                constants.INTERFACES_FOLDER
            )
            if not interfaces_folder.exists():
                continue
            self._interfaces_manager.register_by_package(str(interfaces_folder))

    def _resolve_root_locations(self):
        """Populate `_roots` with default root paths.

        This should be called once at startup to register:
        - User preferences (from env or default).
        - Project preferences (from env or config).

        Raises:
            FileNotFoundError: If the preference root config file does not
                exist.
        """

        config_path = self._packages_manager.preference_roots_path()
        if not Path(config_path).exists():
            raise FileNotFoundError(
                f"Preferences root config file does not exist: {config_path}"
            )

        roots = fileio.load_yaml(config_path) or {}
        for root_name, root_path in roots.items():
            if not root_path:
                continue

            try:
                resolved_path = self._resolve_path(root_path)
                if root_name == self._DEFAULT_USER_PREFERENCE_NAME:
                    folder.ensure_folder_exists(resolved_path)
                self.add_root(root_name, resolved_path)
            except KeyError:
                logger.info(f"Skipping root '{root_name}' due to missing env variable.")
            except Exception as err:
                logger.warning(f"Failed to register root '{root_name}': {err}")

        for package in self._packages_manager.resolver.packages:
            pkg_root = Path(package.root) / constants.PREFERENCES_FOLDER
            if not pkg_root.exists():
                continue
            name = package.name
            self.add_root(name, str(pkg_root))

    def _deep_merge_dicts(self, base: dict, override: dict) -> dict:
        """Recursively merge override into base dict.

        Args:
            base: Base dictionary to merge into.
            override: Dictionary to merge into the base.

        Returns:
            Merged dictionary.
        """

        merged = dict(base)
        for key, value in override.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = self._deep_merge_dicts(merged[key], value)
            else:
                merged[key] = value

        return merged
