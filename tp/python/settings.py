from __future__ import annotations

import os
import json
import logging
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class JsonSettings:
    """
    Class that handles the loading and saving of settings in a JSON file.
    """

    def __init__(self, file_path: str):
        super().__init__()

        self._file_path = file_path
        self._settings = self._load()

    def get(self, key: str, default: Any = None) -> Any:
        """
        Returns the value of the given key in the settings.

        :param key: key to get value for.
        :param default: default value to return if key does not exist.
        :return: value of the key in the settings.
        """

        return self._settings.get(key, default)

    def set(self, key: str, value: Any, save: bool = True):
        """
        Sets the value of the given key in the settings.

        :param key: key to set value for.
        :param value: value to set for the key.
        :param save: whether to save the settings after setting the key.
        """

        self._settings[key] = value
        if save:
            self.save()

    def remove(self, key: str) -> bool:
        """
        Removes the given key from the settings.

        :param key: key to remove.
        :return: whether the key was removed successfully.
        """

        if key not in self._settings:
            return False

        del self._settings[key]
        self.save()

        return True

    def save(self):
        """
        Saves the current settings to the JSON file.
        """

        with open(self._file_path, "w") as f:
            json.dump(self._settings, f, indent=4)

    def refresh(self):
        """
        Refreshes the settings by loading them from the JSON file.
        """

        self._settings = self._load()

    def _load(self) -> dict[str, Any]:
        """
        Internal function that load settings from JSON file.
        """

        if not os.path.exists(self._file_path):
            logger.warning(f'Settings file path: "{self._file_path}" does not exist')
            return {}

        with open(self._file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f'Error decoding JSON file: "{self._file_path}"')
                return {}


class YAMLSettings(JsonSettings):
    """
    Class that handles the loading and saving of settings in a YAML file.
    """

    def save(self):
        """
        Saves the current settings to the JSON file.
        """

        with open(self._file_path, "w") as f:
            yaml.dump(self._settings, f, indent=4)

    def _load(self) -> dict[str, Any]:
        """
        Internal function that load settings from JSON file.
        """

        if not os.path.exists(self._file_path):
            logger.warning(f'Settings file path: "{self._file_path}" does not exist')
            return {}

        with open(self._file_path, "r") as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError:
                logger.warning(f'Error decoding YAML file: "{self._file_path}"')
                return {}
