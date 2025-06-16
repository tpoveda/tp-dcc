from __future__ import annotations


class RigConfiguration:
    """Base class for rig configuration and rig managers access."""

    _NAMING_PRESET_MANAGER: namingpresets.PresetsManager | None = None

    def __init__(self):
        super().__init__()

    def find_name_manager_for_type(
        self, noddle_type: str, preset_name: str | None = None
    ) -> NameManager | None:
        """Finds and returns the naming convention manager used to handle the nomenclature for the given type.

        :param noddle_type: Noddle type to search for ('rig', 'module', ...).
        :param preset_name: optional preset to use find the Noddle type.
        :return: naming manager instance.
        """

        preset = self._current_naming_preset
        if preset_name:
            preset = self._NAMING_PRESET_MANAGER.find_preset(preset_name)

        return preset.find_name_manager_for_type(noddle_type)
