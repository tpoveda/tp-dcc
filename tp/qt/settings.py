from __future__ import annotations

from typing import Any

from Qt.QtCore import QSettings


class QtSettings(QSettings):
    """
    Custom QSettings class that allows to properly convert the value of a key to its
    proper type.
    """

    # noinspection PyMethodOverriding
    def value(self, key: str, default: Any | None = None) -> Any:
        """
        Overrides `value` method to allow to set a default value if the key is not
        found in the settings.

        :param key: settings key.
        :param default: default value to return if the key is not found in the settings.
        :return: The value of the key in the settings or the default value if the key
            is not found.
        """

        data_type = type(default) if default is not None else None
        settings_value = super().value(key, defaultValue=default)
        if settings_value is None:
            return default

        if data_type is list and not isinstance(settings_value, list):
            settings_value = [settings_value] if settings_value else []
        if data_type is dict and not isinstance(settings_value, dict):
            settings_value = dict(settings_value) if settings_value else {}
        if data_type is int and not isinstance(settings_value, int):
            settings_value = (
                int(settings_value) if settings_value is not None else default
            )
        if data_type is float and not isinstance(settings_value, float):
            settings_value = (
                float(settings_value) if settings_value is not None else default
            )
        if data_type is bool:
            settings_value = (
                True if settings_value in ("true", "True", "1", 1, True) else False
            )

        return settings_value
