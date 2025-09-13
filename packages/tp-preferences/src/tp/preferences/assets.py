from __future__ import annotations

import os
import uuid
import typing
import inspect
from pathlib import Path
from typing import Iterable, Any

from loguru import logger

from tp.preferences import manager
from tp.libs.python import paths, folder
from tp.bootstrap.core.constants import PACKAGE_NAME
from tp.bootstrap.core.manager import PackagesManager

from . import constants
from .directory import DirectoryPath

if typing.TYPE_CHECKING:
    from .interface import PreferenceInterface


class AssetPreference:
    def __init__(
        self,
        asset_folder: str,
        preference_interface: PreferenceInterface,
    ):
        super().__init__()

        self._asset_folder = asset_folder
        self._preference_interface = preference_interface

    @property
    def preference_interface(self) -> PreferenceInterface:
        """The preference interface."""

        return self._preference_interface

    @property
    def asset_folder(self) -> str:
        """The asset folder path."""

        return self._asset_folder

    def user_asset_root(self) -> str:
        """Get the root path for user assets, creating the directory if it
        does not exist.

        Returns:
            The path to the user assets root directory.
        """

        user_prefs_path = self._preference_interface.manager.root("user")
        assets_path = str(Path(user_prefs_path, constants.ASSETS_FOLDER))
        if not os.path.isdir(assets_path):
            logger.debug(f"Creating user assets folder: {assets_path}")
            os.makedirs(assets_path)

        return assets_path

    def assets_directory(self) -> str:
        """Get the path to the assets folder handle by this preference.

        Returns:
            The path to the asset folder.
        """

        return str(Path(self.user_asset_root(), self._asset_folder))

    def assets_defaults_directory(self) -> str:
        """Get the path to the default assets folder for this preference.

        Returns:
            The path to the default asset folder.
        """

        return str(Path(self.assets_directory(), constants.ASSETS_DEFAULTS_FOLDER))

    def assets_directory_is_empty(self) -> bool:
        """Check if the assets directory is empty.

        Returns:
            `True` if the assets directory is empty; `False` otherwise.
        """

        assets_directory = self.assets_directory()
        if not os.path.isdir(assets_directory):
            return True

        return len(os.listdir(assets_directory)) == 0

    def current_package_path(self) -> str | None:
        """Get the root path of the package where the preference interface
        class is defined.

        Returns:
            The root path of the package, or `None` if not found.
        """

        found_package_path: str | None = None
        class_file = inspect.getfile(self._preference_interface.__class__)
        for directory in paths.iterate_parent_paths(class_file):
            package_file = str(Path(directory, PACKAGE_NAME))
            if not os.path.isfile(package_file):
                continue
            package = PackagesManager.current().resolver.package_from_path(package_file)
            if package is None:
                logger.warning(f"Could not find package for path: {package_file}")
                continue
            found_package_path = package.root
            break

        return found_package_path

    def assets_default_path(self) -> str | None:
        """Get the path to the default assets folder for this preference.

        Returns:
            The path to the default asset folder.
        """

        package_path = self.current_package_path()
        if package_path is None:
            logger.warning("Could not determine package path for asset defaults.")
            return None

        return str(
            Path(
                package_path,
                constants.PREFERENCES_FOLDER,
                constants.ASSETS_FOLDER,
                self._asset_folder,
            )
        )

    def copy_default_assets(self, path: str) -> bool:
        """Copy the default assets from the specified path to the user's asset
        directory if they do not already exist.

        Args:
            path: The path to the default assets.

        Returns:
            `True` if assets were copied; `False` otherwise.
        """

        default_assets_path = self.assets_default_path()
        if not default_assets_path or not os.path.exists(default_assets_path):
            logger.warning(
                f"Default assets path does not exist: {default_assets_path} "
                f"for {self._asset_folder}"
            )
            return False

        return folder.copy_folder_contents(default_assets_path, path)


class BrowserPreference(AssetPreference):
    def __init__(
        self,
        asset_folder: str,
        preference_interface: PreferenceInterface,
        build_assets: bool = True,
        file_types: Iterable[str] | None = None,
        auto_fill_folders: bool = True,
        selected_indices: list[int] | None = None,
        copy_defaults: bool = True,
    ):
        super().__init__(asset_folder, preference_interface)

        self._file_types = file_types or []
        self._auto_fill_folders = auto_fill_folders
        self._selected_indices = selected_indices or []
        self._copy_defaults = (
            copy_defaults and manager.current_instance().should_copy_default_assets
        )

        if build_assets:
            self.build_asset_directories()

    # region === Settings === #

    def settings(self) -> dict[str, Any]:
        """Get the browser settings dictionary.

        Returns:
            A dictionary containing the browser settings.
        """

        return self.preference_interface.settings().get(constants.SETTINGS_KEY, {})

    def save_settings(self, indent: bool = True, sort: bool = False):
        """Save the current settings to disk.

        Args:
            indent: Whether to pretty-print the YAML file.
            sort: Whether to sort keys alphabetically.
        """

        self._cleanup_active_folders()

        self.preference_interface.save(indent=indent, sort=sort)

    def _cleanup_active_folders(self) -> None:
        """Clean up active folders by removing any that no longer exist in the
        browser folders.
        """

        actives_to_remove: list[str] = []
        ids = [f["id"] for f in self._get_browser_folders()]
        for active in self._get_active_folders():
            if active not in ids:
                actives_to_remove.append(active)
        for active in actives_to_remove:
            self._get_active_folders().remove(active)

    # endregion

    # region === Icons === #

    def browser_uniform_icons(self) -> bool:
        """Determine the uniformity of browser icons for a specific asset folder
        and updates the settings if required.

        Returns:
            True if uniform icons are enabled for the specified asset
                  folder, False otherwise.
        """

        return (
            self.settings()
            .get(constants.BROWSER_UNIFORM_ICONS_KEY, {})
            .get(self.asset_folder, True)
        )

    def set_browser_uniform_icons(self, value: bool, save: bool = True):
        """Set the uniformity of browser icons for a specific asset folder.

        Args:
            value: True to enable uniform icons, False to disable.
            save: Whether to save the settings immediately after updating.
        """

        self.settings().setdefault(constants.BROWSER_UNIFORM_ICONS_KEY, {})[
            self.asset_folder
        ] = value

        if save:
            self.save_settings()

    def set_browser_directories(
        self, directories: list[str | DirectoryPath], save: bool = True
    ):
        """Set the browser directories for the asset folder, replacing any
        existing directories.

        Args:
            directories: A list of directory paths or `DirectoryPath` objects
                         to set as browser directories.
            save: Whether to save the settings immediately after updating.
        """

        dir_paths: list[DirectoryPath] = []
        for directory in directories:
            if isinstance(directory, str):
                dir_path = self.directory_path(directory)
                if dir_path is None:
                    dir_path = DirectoryPath(path=directory)
                dir_paths.append(dir_path)
            elif isinstance(directory, DirectoryPath):
                dir_paths.append(directory)

        self._get_browser_folders()[:] = [d.to_dict() for d in dir_paths]

        if save:
            self.save_settings()

        self._cleanup_active_folders()

    # endregion

    # region === Directory Paths === #

    def directory_path(self, path: str) -> DirectoryPath | None:
        """Retrieve a `DirectoryPath` object for a given path if it exists in
        the browser folders.

        Args:
            path: The path to search for.

        Returns:
            The `DirectoryPath` object if found; `None` otherwise.
        """

        found_directory_path: DirectoryPath | None = None
        for browser_folder in self._get_browser_folders():
            if Path(browser_folder["path"]).as_posix() == Path(path).as_posix():
                found_directory_path = DirectoryPath(path=browser_folder["path"])
                break

        return found_directory_path

    def directory_path_by_id(self, directory_id: str) -> DirectoryPath | None:
        """Retrieve a `DirectoryPath` object for a given directory ID if it
        exists in the browser folders.

        Args:
            directory_id: The directory ID to search for.

        Returns:
            The `DirectoryPath` object if found; `None` otherwise.
        """

        found_directory_path: DirectoryPath | None = None
        for browser_folder in self._get_browser_folders():
            if browser_folder["id"] == directory_id:
                found_directory_path = DirectoryPath(path=browser_folder["path"])
                break

        return found_directory_path

    # endregion

    # region === Asset Directories === #

    def has_old_assets(self) -> bool:
        """Check if there are any old assets in the asset directory based on
        the specified file types.

        Returns:
            `True` if any files with the specified extensions are found; `False`
            otherwise.
        """

        assets_directory = self.assets_directory()
        asset_files = [
            f
            for f in os.listdir(assets_directory)
            if os.path.isfile(os.path.join(assets_directory, f))
        ]
        file_extensions = [os.path.splitext(f)[1][1:] for f in asset_files]
        for file_extension in file_extensions:
            if file_extension in self._file_types:
                return True

        return False

    def build_asset_directories(self) -> None:
        folder_paths = self.browser_folder_paths()
        assets_paths = self.user_asset_root()
        folder.ensure_folder_exists(assets_paths)

        assets_directory = self.assets_directory()

        if (
            os.path.isdir(assets_directory)
            and (
                self.has_old_assets()
                or not self._auto_fill_folders
                or self.assets_directory_is_empty()
            )
            and len(folder_paths) == 0
        ):
            folder.ensure_folder_exists(assets_directory)
            self._initialize_default_directory()
            return

        if not os.path.exists(assets_directory):
            folder.ensure_folder_exists(assets_directory)
            self._initialize_default_directory()

        self.refresh_asset_folders(set_active=False, save=True)

        if not self.has_old_assets() and len(self.browser_folder_paths()) > 1:
            logger.debug(f'Removing base assets folder: "{self.assets_directory()}"')
            self.remove_browser_folder(self.assets_directory())

        if self._selected_indices:
            browser_paths = self.active_browser_paths()
            browser_paths = (
                browser_paths if len(browser_paths) > 0 else self.browser_folder_paths()
            )
            self.set_active_directories(
                [browser_paths[i] for i in self._selected_indices]
            )
        else:
            new_paths = [
                d for d in self.browser_folder_paths() if d not in folder_paths
            ]
            self.set_active_directories(self.active_browser_paths() + new_paths)

    def refresh_asset_folders(self, set_active: bool = True, save: bool = True) -> None:
        logger.debug(f"Refreshing asset folders (set_active={set_active}) ...")

        folder_paths = self.browser_folder_paths()
        dirs = [_folder.path for _folder in folder_paths]

        if self._copy_defaults:
            default_assets_path = self.assets_defaults_directory()
            if self.copy_default_assets(default_assets_path):
                dirs.append(default_assets_path)

        assets_directory = self.assets_directory()
        if self._auto_fill_folders:
            new_folders: list[str] = []
            for d in os.listdir(assets_directory):
                dir_path = str(Path(assets_directory, d))
                if (
                    os.path.isdir(dir_path)
                    and "_fileDependencies" not in d
                    and not d.startswith(".")
                ):
                    new_folders.append(dir_path)
            dirs += new_folders
            logger.debug(f"Auto-filled asset folders: {new_folders}")
            dirs = sorted(list(set(dirs)))

        new_dirs = [
            DirectoryPath(path=d) for d in dirs if self.directory_path(d) is None
        ]
        self.add_browser_directories(new_dirs, save=save)

        if os.path.exists(assets_directory) and not len(dirs) > 0:
            self._initialize_default_directory(set_active=False)

        if set_active:
            new_paths = [d for d in new_dirs if d not in folder_paths]
            self.set_active_directories(
                self.active_browser_paths() + new_paths, save=save
            )

    # endregion

    # region === Browser Folders === #

    def browser_folder_paths(self) -> list[DirectoryPath]:
        """Retrieve the browser folder paths for the specified asset folder.

        Returns:
            A list of `DirectoryPath` objects representing the browser folders
            for the specified asset folder.
        """

        return [
            DirectoryPath(path=path["path"]) for path in self._get_browser_folders()
        ]

    def active_browser_paths(self) -> list[DirectoryPath]:
        """Retrieve the active browser folder paths for the specified asset
        folder.

        Returns:
            A list of `DirectoryPath` objects representing the active browser
            folders for the specified asset folder.
        """

        active_folders = self.settings()[constants.BROWSER_ACTIVE_FOLDERS_KEY][
            self._asset_folder
        ]
        return [f for f in self.browser_folder_paths() if f.id in active_folders]

    def set_active_directory(self, directory: DirectoryPath, clear: bool = True):
        """Set the active directory for the asset folder.

        Args:
            directory: The `DirectoryPath` object representing the directory to
                       set as active.
            clear: Whether to clear existing active directories before setting
                   the new one.
        """

        logger.debug(f'Set active directory: "{directory.path}"')

        active_folders = self._get_active_folders()
        if clear:
            active_folders[:] = []

        active_folders.append(directory.id)

        self.save_settings()

    def set_active_directories(
        self, directories: list[DirectoryPath], save: bool = True
    ):
        """Set multiple active directories for the asset folder.

        Args:
            directories: A list of `DirectoryPath` objects representing the
                         directories to set as active.
            save: Whether to save the settings immediately after updating.
        """

        logger.debug(
            f"Set active directories: {[directory.path for directory in directories]}"
        )

        self.settings()[constants.BROWSER_ACTIVE_FOLDERS_KEY][self._asset_folder] = [
            d.id for d in directories
        ]

        if save:
            self.save_settings()

        self.save_settings()

    def _get_browser_folder_roots(self) -> dict[str, list[dict[str, str]]]:
        """Retrieve the browser folder roots from setting file.

        Returns:
            A dictionary mapping folder identifiers to their respective paths
            based on the configured browser folder settings.
        """

        return self.settings().get(constants.BROWSER_FOLDERS_KEY, {})

    def _get_browser_folders(self) -> list[dict[str, str]]:
        """Retrieve the list of browser folders for a specified asset folder.

        Returns:
            A list of folders corresponding to the specified asset folder.
        """

        return self._get_browser_folder_roots().setdefault(self.asset_folder, [])

    def _get_active_folder_roots(self) -> dict[str, list[str]]:
        """Retrieve the active folder roots from setting the file.

        Returns:
            A dictionary mapping folder identifiers to their respective paths
            based on the configured active folder settings.
        """

        return self.settings().get(constants.BROWSER_ACTIVE_FOLDERS_KEY, {})

    def _get_active_folders(self) -> list[str]:
        """Retrieve the list of active folders for a specified asset folder.

        Returns:
            A list of active folders corresponding to the specified asset folder.
        """

        return self._get_active_folder_roots().setdefault(self.asset_folder, [])

    def _initialize_default_directory(self, set_active: bool = True) -> None:
        """Initialize the default directory for the asset folder if no
        directories are currently set.

        Args:
            set_active: Whether to set the newly created directory as active.
        """

        assets_directory = DirectoryPath(path=self.assets_directory())
        self._get_browser_folders()[:] = [assets_directory.to_dict()]

        if set_active:
            self.set_active_directory(assets_directory)

    def add_browser_directory(
        self, directory: DirectoryPath, save: bool = True
    ) -> bool:
        """Add a single browser directory to the list of folders for the
        specified asset folder, ensuring no duplicates are added.

        Args:
            directory: The `DirectoryPath` object representing the directory
                to add.
            save: Whether to save the settings immediately after adding the
                directory.

        Returns:
            `True` if the directory was added; `False` if it was a duplicate.
        """

        for d in self.browser_folder_paths():
            if d == directory:
                logger.debug(
                    "Duplicate folders found while adding browser directory, "
                    "ignoring. '{}'".format(d.alias)
                )
                return False

        asset_folder = self._get_browser_folder_roots()[self._asset_folder]
        asset_folder.append(directory.to_dict())

        logger.debug(f"Adding Browser Directory: '{self._asset_folder}': {directory}")

        if save:
            self.save_settings()

        return True

    def add_browser_directories(
        self, directories: list[DirectoryPath], save: bool = True
    ) -> int:
        """Add multiple browser directories to the list of folders for the
        specified asset folder, ensuring no duplicates are added.

        Args:
            directories: A list of `DirectoryPath` objects representing the
                directories to add.
            save: Whether to save the settings immediately after adding the
                directories.

        Returns:
            The number of directories that were successfully added.
        """

        added_count = 0
        for directory in directories:
            if self.add_browser_directory(directory, save=False):
                added_count += 1

        if added_count > 0 and save:
            self.save_settings()

        return added_count

    def add_active_directory(
        self, directory: str | DirectoryPath, save: bool = True
    ) -> bool:
        """Add a single active directory to the list of active folders for the
        specified asset folder, ensuring no duplicates are added.

        Args:
            directory: The `DirectoryPath` object representing the directory
                to add or a string representing the active path ID.
            save: Whether to save the settings immediately after adding the
                directory.

        Returns:
            `True` if the directory was added; `False` if it was a duplicate.
        """

        directory_id: str | None = None
        if isinstance(directory, DirectoryPath):
            directory_id = directory.id
        elif isinstance(directory, str):
            directory_id = self.directory_path(directory).id

        if directory_id is None:
            logger.warning(f"Could not find directory for path: {directory}")
            return False

        self.settings()[constants.BROWSER_ACTIVE_FOLDERS_KEY][
            self._asset_folder
        ].append(directory_id)

        if save:
            self.save_settings()

        return True

    def remove_browser_folder(self, path: str) -> bool:
        """Remove a browser folder from the list of folders for the specified

        Args:
            path: The path of the folder to remove.

        Returns:
            `True` if the folder was found and removed; `False` otherwise.
        """

        for p in self._get_browser_folders():
            if Path(path).as_posix() == Path(p["path"]).as_posix():
                self._get_browser_folders().remove(p)
                return True

        return False

    # endregion

    # region === Categories === #

    def categories(self) -> list[dict[str, Any]]:
        """Get the list of unique categories from the browser folders.

        Returns:
            A list of unique category names.
        """

        return (
            self.settings()
            .get(constants.BROWSER_CATEGORIES_KEY, {})
            .get(self._asset_folder, [])
        )

    def create_category(
        self, name: str, category_id: str | None, parent: str, children: list[str]
    ) -> dict[str, Any]:
        """Create a new category dictionary.

        Args:
            name: The name of the category.
            category_id: The ID of the category. If None, a new ID will be generated.
            parent: The parent category ID.
            children: A list of child category IDs.

        Returns:
            A dictionary representing the new category.
        """

        return {
            "id": category_id or str(uuid.uuid4())[:6],
            "alias": name,
            "parent": parent,
            "children": children,
        }

    def add_category(self, category: dict[str, Any], save: bool = True) -> None:
        """Add a new category to the list of categories for the specified asset
        folder.

        Args:
            category: The category name to add.
            save: Whether to save the settings immediately after adding.
        """

        self.settings()[constants.BROWSER_CATEGORIES_KEY].setdefault(
            self._asset_folder, []
        ).append(category)

        if save:
            self.save_settings()

    def add_categories(
        self, categories: list[dict[str, Any]], save: bool = True
    ) -> None:
        """Add multiple categories to the list of categories for the specified
        asset folder.

        Args:
            categories: A list of category names to add.
            save: Whether to save the settings immediately after adding.
        """

        existing = {i["id"]: i for i in self.categories()}
        for category in categories:
            existing_category = existing.get(category["id"])
            if existing_category is not None:
                existing_category["alias"] = category["alias"]
                existing_category["parent"] = category["parent"]
                existing_category["children"] = category["children"]
                continue
            existing[category["id"]] = category
            self.add_category(category, save=False)

        if save:
            self.save_settings()

    def update_category(
        self, category_id: str, data: dict[str, Any], save: bool = True
    ) -> bool:
        """Update a category's data based on its ID.

        Args:
            category_id: The ID of the category to update.
            data: A dictionary containing the data to update.
            save: Whether to save the settings immediately after updating.

        Returns:
            `True` if the category was found and updated; `False` otherwise.
        """

        updated = False
        for category in self.categories():
            if category["id"] == category_id:
                category.update(data)
                updated = True

        if save and updated:
            self.save_settings()

        return updated

    def active_categories(self) -> list[str]:
        """Get the list of active categories based on the active browser
        folders.

        Returns:
            A list of active category IDs.
        """

        return (
            self.settings()
            .get(constants.BROWSER_ACTIVE_CATEGORIES_KEY, {})
            .get(self._asset_folder, [])
        )

    def set_active_categories(self, category_ids: list[str], save: bool = True) -> None:
        """Set the active categories for the specified asset folder.

        Args:
            category_ids: A list of category IDs to set as active.
            save: Whether to save the settings immediately after updating.
        """

        self.settings().setdefault(constants.BROWSER_ACTIVE_CATEGORIES_KEY, {})[
            self._asset_folder
        ] = category_ids

        if save:
            self.save_settings()

    def remove_category(self, category_id: str, save: bool = True) -> bool:
        """Remove a category from the list of categories for the specified
        asset folder.

        Args:
            category_id: The ID of the category to remove.
            save: Whether to save the settings immediately after removing.

        Returns:
            `True` if the category was found and removed; `False` otherwise.
        """

        removed = False
        for category in self.categories():
            if category["id"] == category_id:
                self.categories().remove(category)
                removed = True

        if save and removed:
            self.save_settings()

        return removed

    def clear_categories(self, save: bool = True) -> None:
        """Clear all categories for the specified asset folder.

        Args:
            save: Whether to save the settings immediately after clearing.
        """

        self.settings()[constants.BROWSER_CATEGORIES_KEY][self._asset_folder] = []

        if save:
            self.save_settings()
