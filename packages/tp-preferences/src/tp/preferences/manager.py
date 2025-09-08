from __future__ import annotations

import os
import stat
import timeit
import shutil
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

    @property
    def roots(self) -> dict[str, str]:
        """The registered preference roots."""

        return self._roots

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
            raise errors.RootDoesNotExistError(
                f"Root does not exist: {name}. Available roots: {list(self._roots.keys())}"
            )

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
        setting.update(data)

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
        root_paths = {}
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
            root_paths[root_name] = str(root_path)

            if (
                first_writable_root is None
                and root_name.startswith("user")
                or root_name.startswith("project")
            ):
                first_writable_root = root_name

        found_setting = SettingObject(
            relative_path=relative_path,
            root_paths=root_paths,
            active_root=first_writable_root,
            **merged_data,
        )

        if name is not None:
            settings = found_setting.get(constants.SETTINGS_KEY, {})
            if name not in settings:
                raise errors.SettingsNameDoesntExistError(
                    f"Failed to find setting '{name}' in file '{found_setting}'"
                )
            return settings[name]

        return found_setting

    def setting_from_root_path(
        self, relative_path: str, root_path: str, extension: str | None = None
    ) -> SettingObject:
        """Create a SettingObject from a specific root path.

        Args:
            relative_path: Relative path to the setting file, e.g.,
                "tools/mytool/settings".
            root_path: The absolute path to the root directory.
            extension: Optional file extension to use (default is '.yaml').

        Returns:
            A SettingObject instance for the specified path.
        """

        extension = extension or self._EXTENSION
        base, ext = os.path.splitext(relative_path)
        compare_extension = extension
        if not compare_extension.startswith("."):
            compare_extension = "." + extension
        if compare_extension != ext:
            relative_path = (
                base + extension if extension.startswith(".") else f"{base}.{extension}"
            )

        root_name = self.root_name_for_path(root_path)

        full_path = Path(root_path).joinpath(relative_path)
        if full_path.exists():
            with open(full_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                return self.create_setting(relative_path, root_name, data)

        return SettingObject(relative_path=relative_path)

    def package_preference_root_location(self, package_name: str) -> str:
        """Determine the root location of the preference folder for a given
        package.

        Args:
            package_name: The name of the package for which the preferences
                folder root location is requested.

        Returns:
            str: The absolute path to the preferences folder of the
            requested package.

        Raises:
            ValueError: If the package does not exist in the environment or if the
                preferences folder is not present.
        """

        package = self._packages_manager.resolver.package_by_name(package_name)
        if not package:
            error_msg = (
                f'Requested package "{package_name}" does not exist '
                f"within the current environment."
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        preference_path = Path(package.root).joinpath(constants.PREFERENCES_FOLDER)
        if not preference_path.exists():
            error_msg = (
                f"Default preferences folder does not exist for "
                f"package: {package_name} -> {preference_path}"
            )
            logger.error(error_msg)
            raise ValueError(error_msg)

        return str(preference_path)

    def package_preference_location(self, package_name: str) -> str:
        """Generate and return the preference file location for a given
        package name.

        Notes:
            Given the root location for package preferences, this method
            appends "prefs"  to generate the complete preference file path for
            the specified package.

        Args:
            package_name: The name of the package for which the preference
                file location is to be generated.

        Returns:
            The complete path to the preference file for the given
            package name.
        """

        return str(
            Path(self.package_preference_root_location(package_name)).joinpath("prefs")
        )

    def default_preference_settings(
        self, package_name: str, relative_path: str
    ) -> SettingObject | None:
        """Generates default preference settings for a package by locating its
        preference file and getting the associated settings object.
        Validates the created settings object before returning it.

        Args:
            package_name: The name of the package for which the default
                preference settings are being configured.
            relative_path: The relative path to the location where the package
                settings should be fetched.

        Returns:
            A valid settings object representing the package's default
            preferences, or `None` if the object is invalid.
        """

        package_prefs_root = self.package_preference_root_location(package_name)
        obj = self.setting_from_root_path(relative_path, package_prefs_root)
        return obj if obj.is_valid() else None

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

    def copy_preferences_to_root(self, root_name: str, force: bool = False):
        """Copy all preference files from the package preference roots to the
        specified root directory, creating destination directories as needed.

        Notes:
            Only files ending with the specific file extension for preferences
            are transferred.

        Args:
            root_name: The name of the root directory where preferences should
                be copied.
            force: If True, overwrites existing files in the destination.
        """

        root_path = self.root(root_name)
        for preferences_path in self.iterate_package_preference_roots():
            preferences_root = Path(preferences_path).joinpath("prefs")
            start_time = timeit.default_timer()

            for pref_file_path in preferences_root.rglob("*"):
                if not pref_file_path.is_file():
                    continue
                if not pref_file_path.name.endswith(PreferencesManager._EXTENSION):
                    continue

                relative_path = pref_file_path.relative_to(Path(preferences_path))
                destination_path = root_path / relative_path

                if force or not destination_path.exists():
                    destination_path.parent.mkdir(parents=True, exist_ok=True)
                    logger.debug(
                        f"Transferring preference {pref_file_path} to "
                        f"destination: {destination_path}"
                    )

                    shutil.copy2(str(pref_file_path), str(destination_path))
                    # Set read permissions for user, group, and others.
                    pref_file_path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            logger.debug(
                f"Finished package preferences to: {preferences_root}, "
                f"total Time: {timeit.default_timer() - start_time}"
            )

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
