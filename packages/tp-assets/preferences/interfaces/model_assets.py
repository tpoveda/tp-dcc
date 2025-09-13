from __future__ import annotations

import typing

from tp import dcc
from tp.preferences.assets import BrowserPreference
from tp.preferences.interface import PreferenceInterface

if typing.TYPE_CHECKING:
    from tp.preferences.manager import PreferencesManager


class ModelAssetsPreferenceInterface(PreferenceInterface):
    id = "model_assets"
    _relative_path = f"prefs/{dcc.current_dcc()}/model_assets.yaml"

    def __init__(self, preferences_manager: PreferencesManager):
        """Initialize the `PreferenceInterface`.

        Args:
            preferences_manager: The main preferences manager instance.
        """

        super().__init__(preferences_manager=preferences_manager)

        self._model_assets_preference = BrowserPreference("model_assets", self)

    @property
    def model_assets_preference(self) -> BrowserPreference:
        """The model asset preference."""

        return self._model_assets_preference
