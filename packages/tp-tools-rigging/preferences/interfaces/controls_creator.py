from __future__ import annotations

import typing

from tp import dcc
from tp.preferences.assets import BrowserPreference
from tp.preferences.interface import PreferenceInterface

if typing.TYPE_CHECKING:
    from tp.preferences.manager import PreferencesManager


class ControlsCreatorPreferenceInterface(PreferenceInterface):
    id = "controls_creator"
    _relative_path = f"prefs/{dcc.current_dcc()}/controls_creator.yaml"

    def __init__(self, preferences_manager: PreferencesManager):
        """Initialize the `PreferenceInterface`.

        Args:
            preferences_manager: The main preferences manager instance.
        """

        super().__init__(preferences_manager=preferences_manager)

        self._control_assets = BrowserPreference(
            asset_folder="control_curves",
            preference_interface=self,
            file_types=["curve"],
        )

    @property
    def control_assets(self) -> BrowserPreference:
        """The control assets browser preferences."""

        return self._control_assets