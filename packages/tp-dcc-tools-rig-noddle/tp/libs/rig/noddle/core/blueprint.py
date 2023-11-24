from __future__ import annotations

import os
from typing import Any

from tp.core import log
from tp.dcc import scene
from tp.preferences.interfaces import noddle
from tp.libs.rig.noddle.core import action, serializer

logger = log.rigLogger


class BlueprintSettings:
    """
    Class that holds constants that defines the keys for Blueprint settings.
    """

    RigName = 'rigName'
    RigNodeNameFormat = 'rigNodeNameFormat'
    DebugBuild = 'debugBuild'


class Blueprint:
    """
    Class that contains all the information needed to build a rig. Esentially is composed by:
        - configuration settings
        - ordered hierarchy of BuildActions.
    """

    def __init__(self):
        super().__init__()

        self._prefs = noddle.noddle_interface()
        self._settings: dict[str, Any] = {}
        self._add_missing_settings()
        self._version = '0.0.0'
        self._config: dict | None = None
        self._scene_path: str = ''

        self._root_step = action.BuildStep('Root')

        self.update_scene_path()

    @property
    def settings(self) -> dict[str, Any]:
        """
        Getter method that returns dictionary containing the settings for this blueprint.

        :return: blueprint settings.
        :rtype: dict[str, Any]
        """

        return self._settings

    @property
    def version(self) -> str:
        """
        Getter method that returns string version of the blueprint.

        :return: blueprint version.
        :rtype: str
        """

        return self._version

    @property
    def root_step(self) -> action.BuildStep:
        """
        Getter method that returns the root step of this blueprint.

        :return: root step.
        :rtype: action.BuildStep
        """

        return self._root_step

    @property
    def scene_path(self) -> str:
        """
        Getter method that returns the scene path associated with this blueprint.

        :return: scene path.
        :rtype: str
        """

        return self._scene_path

    def step_by_path(self, step_path: str) -> action.BuildStep | None:
        """
        Returns a build step from the blueprint at given path.

        :param str step_path: build step full path.
        :return: found build step.
        :rtype: action.BuildStep or None
        """

        if not step_path or step_path == '/':
            return self._root_step

        step = self.root_step.child_by_path(step_path)
        if not step:
            logger.warning(f'Could not find build step: {step_path}')
            return None

        return step

    def setting(self, key: str, default: Any = None):
        """
        Returns a blueprint setting by key.

        :param str key: key of the blueprint setting to get.
        :param Any default: value that is returned if setting with given key was not found.
        :return: setting value.
        :rtype: Any
        """

        return self._settings.get(key, default)

    def set_setting(self, key: str, value: Any):
        """
        Sets a blueprint setting by key.

        :param str key: key of the blueprint setting to set.
        :param Any value: setting value to set.
        """

        self._settings[key] = value

    def config(self) -> dict:
        """
        Returns the configuration for this blueprint.
        Loads the configuration from disk if it has not been loaded yet.

        :return: blueperint configuration.
        :rtype: dict
        """

        if not self._config:
            self._config = self._prefs.blueprint_config().copy()

        return self._config

    def reset_to_default(self):
        """
        Resets the blueprint to the default set of actions.
        """

        default_data = self.config().get('default', {})
        self.deserialize(default_data)

    def update_scene_path(self):
        """
        Updates associated scene path to the currently open DCC scene name.
        """

        self._scene_path = scene.Scene().current_name()

    def serialize(self) -> serializer.UnsortableOrderedDict:
        """
        Serializes this blueprint into a dictionary.

        :return: serialized blueprint dictionary.
        :rtype: serializer.UnsortableOrderedDict
        """

        self.update_scene_path()
        data = serializer.UnsortableOrderedDict()
        data['version'] = self.version
        data['settings'] = self.settings
        data['steps'] = self._root_step.serialize()
        data['scene_path'] = self._scene_path

        return data

    def deserialize(self, data: dict) -> bool:
        """
        Deserializes given blueprint serialized data and updates this blueprint based on that data.

        :param dict data: blueprint serialized data.
        :return: True if the data was deserialized successfully; False otherwise.
        :rtype: bool
        """

        self._version = data.get('version', None)
        self._settings = data.get('settings', {})
        self._root_step.deserialize(data.get('steps', {'name': 'Root'}))
        self._add_missing_settings()
        self._scene_path = data.get('scene_path', '')

        return True

    def _add_missing_settings(self):
        """
        Internal function that adds new or missing settings to the blueprint, without overwriting existing settings.
        """

        if BlueprintSettings.RigName not in self._settings:
            self.set_setting(BlueprintSettings.RigName, '')
        if BlueprintSettings.RigNodeNameFormat not in self._settings:
            self.set_setting(BlueprintSettings.RigNodeNameFormat, '{rigName}_rig')
        if BlueprintSettings.DebugBuild not in self._settings:
            self.set_setting(BlueprintSettings.DebugBuild, False)


class BlueprintFile:
    """
    Class that represents a blueprint and its associated file path for saving and loading, as well as tracking
    modification status.

    A BlueprintFile can be initialized without a file path and still be considered valid. A file can be assigned after
    creating the BlueprintFile instance.

    On the other hand, a file path must be assigned before a blueprint can be saved.
    """

    # File extension used to save Blueprint files
    file_extension = 'yaml'

    def __init__(self, file_path: str | None = None, is_read_only: bool = False):
        super().__init__()

        self._blueprint = Blueprint()
        self._file_path = file_path
        self._is_read_only = is_read_only
        self._is_modified = False

    @property
    def blueprint(self) -> Blueprint:
        """
        Returns the blueprint to be opened/save.

        :return: blueprint instance.
        :rtype: Blueprint
        """

        return self._blueprint

    @property
    def file_path(self) -> str:
        """
        Returns the blueprint file path.

        :return: blueprint file path.
        :rtype: str
        """

        return self._file_path

    @file_path.setter
    def file_path(self, value: str):
        """
        Sets blueprint file path.

        :param str value: absolute path pointing to blueprint file in disk.
        """

        self._file_path = value

    @property
    def is_read_only(self) -> bool:
        """
        Getter method that returns whether blueprint only can be read.

        :return: True if blueprint is read only and cannot be modified; False otherwise.
        :rtype: bool
        """

        return self._is_read_only

    def has_file_path(self) -> bool:
        """
        Returns whether a file path is assigned to this instance.

        :return: True if file path is assigned; False otherwise.
        :rtype: bool
        """

        return bool(self._file_path)

    def default_file_path(self) -> str:
        """
        Returns the file path to use for a new Blueprint file.
        Uses current open DCC scene to retrieve it.

        :return: default blueprint file path.
        :rtype: str
        """

        scene_name = scene.Scene().current_name()
        return f'{scene_name}.{self.file_extension}'

    def resolve_file_path(self, allow_existing: bool = False):
        """
        Automatically resolves the current file path based on the open DCC scene.
        If path is already set this function does nothing.

        :param bool allow_existing: whether to allow resolving to a path that already exists on disk.
        """

        if self._file_path:
            return

        file_path = self.default_file_path()
        if not file_path:
            return

        if allow_existing or not os.path.isfile(file_path):
            self._file_path = file_path

    def file_name(self) -> str | None:
        """
        Returns the base name of the blueprint file path.

        :return: blueprint file path base name.
        :rtype: str or None
        """

        return os.path.basename(self._file_path) if self._file_path else None

    def can_load(self) -> bool:
        """
        Returns whether blueprint can be loaded.

        :return: True if blueprint can be loaded; False otherwise.
        :rtype: bool
        """

        return self.has_file_path()

    def can_save(self) -> bool:
        """
        Returns whether blueprint can be saved.

        :return: True if blueprint can be saved; False otherwise.
        :rtype: bool
        """

        return self.has_file_path() and not self._is_read_only

    def is_modified(self) -> bool:
        """
        Returns whether blueprint has not saved changes.

        :return: True if blueprint has been modified and not saved; False otherwise.
        :rtype: bool
        """

        return self._is_modified

    def modify(self):
        """
        Marks blueprint as been modified.
        """

        self._is_modified = True

    def clear_modified(self):
        """
        Marks blueprint as non-modified.
        """

        self._is_modified = False

    def save(self) -> bool:
        """
        Saves the blueprint to a file in disk.

        :return: True if the file was saved successfully; False otherwise.
        :rtype: bool
        """

        if not self._file_path:
            logger.warning('Cannot save Blueprint, file path is not set.')
            return False

        success = self.blueprint.save_to_file(self._file_path)
        if success:
            self.clear_modified()
        else:
            logger.error(f'Failed to save Blueprint to file: "{self._file_path}"')

        return success

    def save_as(self, file_path: str) -> bool:
        """
        Saves the blueprint with a new file path.

        :param str file_path: absolute path to save blueprint in.
        :return: True if the file was saved successfully; False otherwise.
        :rtype: bool
        """

        self._file_path = file_path
        return self.save()

    def load(self) -> bool:
        """
        Loads blueprint from file.

        :return: True if blueprinet was loaded successfully; False otherwise.
        :rtype: bool
        """

        if not self._file_path:
            logger.warning('Cannot load blueprint because file path is not set.')
            return False

        if not os.path.isfile(self._file_path):
            logger.warning(f'Cannot load blueprint because file does not exist: "{self._file_path}"')
            return False

        success = self.blueprint.load_from_file(self._file_path)

        if success:
            self.clear_modified()
        else:
            logger.error(f'Failed to load blueprint from file: "{self._file_path}"')

        return success
