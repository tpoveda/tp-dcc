from __future__ import annotations

import typing
from typing import Any

from . import constants

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
    ):
        super().__init__(asset_folder, preference_interface, build_assets=build_assets)

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

        uniform_icons = (
            self.settings()
            .get(constants.BROWSER_UNIFORM_ICONS_KEY, {})
            .get(self.asset_folder, None)
        )
        if uniform_icons is None:
            self.settings().setdefault(constants.BROWSER_UNIFORM_ICONS_KEY, {})[
                self.asset_folder
            ] = True
            self.save_settings()
            return True

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
