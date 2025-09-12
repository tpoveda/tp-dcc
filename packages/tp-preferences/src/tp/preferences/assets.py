from __future__ import annotations

import typing
from typing import Iterable, Any

from . import constants
from .directory import DirectoryPath

if typing.TYPE_CHECKING:
    from .interface import PreferenceInterface


class AssetPreference:
    def __init__(
        self,
        asset_folder: str,
        preference_interface: PreferenceInterface,
        build_assets: bool = True,
    ):
        super().__init__()

        self._asset_folder = asset_folder
        self._preference_interface = preference_interface

    @property
    def asset_folder(self) -> str:
        """The asset folder path."""

        return self._asset_folder

    @property
    def preference_interface(self) -> PreferenceInterface:
        """The preference interface."""

        return self._preference_interface


class BrowserPreference(AssetPreference):
    def __init__(
        self,
        asset_folder: str,
        preference_interface: PreferenceInterface,
        build_assets: bool = True,
        file_types: Iterable[str] | None = None,
        auto_fill_folders: bool = True,
    ):
        super().__init__(asset_folder, preference_interface, build_assets=build_assets)

        self._file_types = file_types or []
        self._auto_fill_folders = auto_fill_folders

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

        self.preference_interface.save(indent=indent, sort=sort)

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

    def browser_folder_paths(self) -> list[DirectoryPath]:
        """Retrieve the browser folder paths for the specified asset folder.

        Returns:
            A list of `DirectoryPath` objects representing the browser folders
            for the specified asset folder.
        """

        return [DirectoryPath(path) for path in self._get_browser_folders()]

    def refresh_asset_folders(self, set_active: bool = True, save: bool = True) -> None:

        print('Refreshing asset folders ...')

    def _get_browser_folder_roots(self) -> dict[str, str]:
        """Retrieve the browser folder roots from setting file.

        Returns:
            A dictionary mapping folder identifiers to their respective paths
            based on the configured browser folder settings.
        """

        return self.settings().get(constants.BROWSER_FOLDERS_KEY, {})

    def _get_browser_folders(self) -> list[str]:
        """Retrieve the list of browser folders for a specified asset folder.

        Returns:
            A list of folders corresponding to the specified asset folder.
        """

        return self._get_browser_folder_roots().get(self.asset_folder, [])
