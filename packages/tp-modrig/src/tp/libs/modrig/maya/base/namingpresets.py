from __future__ import annotations

import os
import json
import pathlib
import tempfile
from typing import cast

from loguru import logger

from tp.libs.naming import manager
from tp.libs.python import folder, jsonio

from . import settings
from . import constants

PRESET_EXT = "namingpreset"
CONFIG_EXT = "namingcfg"


def surround_text_as_token(text: str) -> str:
    """Return the given text with the token syntax added.

    Args:
        text: Text to convert to token syntax.

    Returns:
        Text surrounded by curly braces, which is the token syntax.
    """

    return "{" + text + "}"


class Preset:
    """Class that represents a naming preset for the naming managers."""

    def __init__(self, name: str, file_path: str, parent: Preset):
        """Initializes a new preset instance.

        Args:
            name: Name of the preset.
            file_path: Absolute file path where the preset is stored.
            parent: Optional parent preset instance. If None,
                this preset is a root preset.
        """

        super().__init__()

        self._name = name
        self._file_path = file_path
        self._parent = parent
        self._managers_data: list[NameManagerData] = []
        self._children: list[Preset] = []

    def __repr__(self) -> str:
        """Return a string representation of this preset.

        Returns:
            A string representation of this preset instance.
        """

        return (
            f"<{self.__class__.__name__}(name={self._name}) object at {hex(id(self))}>"
        )

    @classmethod
    def load_from_path(cls, file_path: str) -> Preset | None:
        """Load the preset from a valid absolute preset file path.

        Args:
            file_path: Absolute preset file path to load.

        Returns:
            New loaded preset instance if the file is valid; None otherwise.
        """

        try:
            logger.debug(f"Loading Preset from path: {file_path}")
            data = jsonio.read_file(file_path)
        except json.decoder.JSONDecodeError:
            logger.error(f"Failed to load preset file: {file_path}", exc_info=True)
            return None

        return cls.load_from_data(data, file_path)

    @classmethod
    def load_from_data(cls, data: dict, file_path: str, parent: Preset | None = None):
        """Loads the preset from the given valid preset data.

        Args:
            data: Raw preset data to load.
            file_path: File path where preset data was retrieved from.
            parent: Optional parent preset instance.
                If None, this preset is a root preset.

        Returns:
            New loaded preset instance.
        """

        name = data.get("name")
        new_preset = cls(name=name, file_path=file_path, parent=parent)
        for config in data.get("configs", list()):
            config_type = config["type"]
            name_manager_data = NameManagerData(config["name"], config_type)
            new_preset.managers_data.append(name_manager_data)

        return new_preset

    @property
    def name(self) -> str:
        """The preset name."""

        return self._name

    @property
    def file_path(self) -> str:
        """The preset file path."""

        return self._file_path

    @property
    def managers_data(self) -> list[NameManagerData]:
        """The list of name manager data for this preset."""

        return self._managers_data

    @property
    def children(self) -> list[Preset]:
        """The list of preset children for this preset instance."""

        return self._children

    @property
    def parent(self) -> Preset:
        """The preset parent for this preset instance."""

        return self._parent

    @parent.setter
    def parent(self, value: Preset):
        """Sets the preset parent for this instance."""

        self._parent = value

    def exists(self) -> bool:
        """Return whether this preset exists on disk.

        Returns:
            True if preset exists on disk; False otherwise.
        """

        return self.file_path and os.path.isfile(self.file_path)

    def create_name_manager_data(
        self,
        name: str | None,
        mod_rig_type: str,
        tokens: list[dict] | None,
        rules: list[dict] | None,
    ) -> NameManagerData:
        """Create in memory (not in disk) a new name manager and adds it to
        the preset.

        Args:
            name: Name for the manager. If None, a unique name will be
                generated.
            mod_rig_type: ModRig module name to use (e.g. 'rig', 'module').
            tokens: Tokens to set on the newly created name manager.
            rules: Newly created config rules.

        Returns:
            Newly created name manager data instance.
        """

        def _generate_unique_name_manager_name(
            _mod_rig_type: str, _directory: str
        ) -> str:
            """Generate a unique name for the name manager.

            Args:
                _mod_rig_type: ModRig module type to use (e.g. 'rig', 'module').
                _directory: Directory where the name manager will be created.

            Returns:
                Unique name for the name manager.
            """

            return os.path.basename(
                tempfile.mktemp(prefix=f"{mod_rig_type}_", dir=_directory)
            )

        name = name or _generate_unique_name_manager_name(
            mod_rig_type, _directory=os.path.dirname(self._file_path)
        )
        name_manager = manager.NameManager(
            {"name": name, "tokens": tokens or [], "rules": rules or []}
        )
        name_manager_data = NameManagerData(name, mod_rig_type)
        parent = self.find_name_manager_for_type(mod_rig_type)
        name_manager.parent_manager = parent
        name_manager_data.manager = name_manager
        self._managers_data.append(name_manager_data)

        return name_manager_data

    def find_name_manager_data_by_type(
        self, mod_rig_type: str, recursive: bool = True
    ) -> NameManagerData | None:
        """Return the configuration data instance stored on the preset with
        the provided type.

        Args:
            mod_rig_type: ModRig type to search for (e.g. 'rig', 'module').
            recursive: Whether to recursively check parent presets.

        Returns:
            The found config data instance with the given type; None if not found.
        """

        for name_manager_data in self._managers_data:
            if name_manager_data.modrig_type == mod_rig_type:
                return name_manager_data

        if self._parent is not None and recursive:
            return self._parent.find_name_manager_data_by_type(
                mod_rig_type, recursive=recursive
            )

        return None

    def find_name_manager_data_by_name(
        self, name: str, recursive: bool = True
    ) -> NameManagerData | None:
        """Return the configuration data instance stored on the preset with
        the provided name.

        Args:
            name: Name to search for.
            recursive: Whether to recursively check parent presets.

        Returns:
            Found config data instance with given name; None if not found.
        """

        for name_manager_data in self._managers_data:
            if name_manager_data.name == name:
                return name_manager_data

        if self._parent is not None and recursive:
            return self._parent.find_name_manager_data_by_name(
                name, recursive=recursive
            )

        return None

    def find_name_manager_for_type(
        self, mod_rig_type: str, recursive: bool = True
    ) -> manager.NameManager | None:
        """Find and returns the naming convention manager used to handle the
        nomenclature for the given type.

        Args:
            mod_rig_type: ModRig type to search for (e.g. 'rig', 'module').
            recursive: whether to recursively check parent presets.

        Returns:
            Found naming manager instance for the given type; None if not found.
        """

        preset_config_data = self.find_name_manager_data_by_type(
            mod_rig_type, recursive=recursive
        )
        if preset_config_data is None:
            return self.find_name_manager_data_by_type("global").manager

        return preset_config_data.manager

    def serialize(self) -> dict:
        """Return the raw dict representing this preset.

        Returns:
            Serialized preset data.
        """

        return {
            "name": self.name,
            "managers_data": [i.serialize() for i in self._managers_data],
        }


class NameManagerData:
    """Data class which stores the config name, modrig type, and linked
    name manager on a preset.
    """

    def __init__(self, name: str, mod_rig_type: str):
        """Initialize a new name manager data instance.

        Args:
            name: The name of the naming manager.
            mod_rig_type: The type of the modrig module this naming manager
        """

        super().__init__()

        self._name = name
        self._mod_rig_type = mod_rig_type
        self._manager: manager.NameManager | None = None

    def __eq__(self, other: NameManagerData) -> bool:
        """Override the equality operator to compare two `NameManagerData`
        instances.

        Args:
            other: The other `NameManagerData` instance to compare with.

        Returns:
            True if both instances have the same name and modrig type;
                False otherwise.
        """

        if not isinstance(other, NameManagerData):
            return False

        return self.name == other.name and self.modrig_type == other.modrig_type

    def __ne__(self, other: NameManagerData) -> bool:
        """Override the inequality operator to compare two `NameManagerData`
        instances.

        Args:
            other: The other `NameManagerData` instance to compare with.

        Returns:
            True if the instances have different names or modrig types;
        """

        if not isinstance(other, NameManagerData):
            return True

        return self.name != other.name or self.modrig_type != other.modrig_type

    def __repr__(self) -> str:
        """Return a string representation of the `NameManagerData` instance.

        Returns:
            A string representation of the instance, including its name and
                modrig type.
        """

        return f"{self.__class__.__name__}(name={self.name}, type={self.modrig_type}"

    @property
    def name(self) -> str:
        """The name of the naming manager."""

        return self._name

    @property
    def modrig_type(self) -> str:
        """The type of the modrig module this naming manager is used for."""

        return self._mod_rig_type

    @property
    def manager(self) -> manager.NameManager:
        """The name manager instance linked to this data."""

        return self._manager

    @manager.setter
    def manager(self, value):
        """Set the name manager instance linked to this data."""

        self._manager = value

    def serialize(self) -> dict:
        """Return the raw representation of this naming manager data.

        Returns:
            A dictionary containing the name and modrig type of this
        """

        return {"name": self.name, "type": self.modrig_type}


class PresetsManager:
    """Manager to handle the different naming presets used by ModRig."""

    ENV_VAR = "TP_MODRIG_NAME_PRESET_PATHS"

    def __init__(self):
        super().__init__()

        self._preferences_interface = cast(
            settings.ModRigSettings, settings.ModRigSettings()
        )

        # Full list of preset instances.
        self._presets: list[Preset] = []

        # Root preset loaded from naming preset hierarchy
        self._root_preset: Preset | None = None

        # Dictionary containing all naming managers
        self._naming_managers: dict[str, manager.NameManager] = {}

        # Dictionary containing all available naming manager types
        self._available_manager_types = set()

    @property
    def preferences_interface(self) -> settings.ModRigSettings:
        """The ModRig preference interface that allows to access
        ModRig related preferences.
        """

        return self._preferences_interface

    @property
    def root_preset(self) -> Preset | None:
        """The root preset loaded from naming preset hierarchy."""

        return self._root_preset

    def available_naming_manager_types(self) -> set[str]:
        """Return all currently available naming manager types.

        Returns:
            The set of available naming manager types.
        """

        return self._available_manager_types

    def update_available_naming_managers(self, types: list[str] or set[str]):
        """Update the currently available naming manger types.

        Args:
            Types to update. This can be a list or set of strings
                representing the naming manager types.
        """

        self._available_manager_types.update(set(types))

    def contains_path(self, file_path: str) -> bool:
        """Return whether the provided file path is already registered within
        this manager.

        Args:
            file_path: Absolute file path to check if it is already registered.

        Returns:
            True if the given file path is already registered; False otherwise.
        """

        file_path = pathlib.Path(file_path).resolve()
        for preset in self._presets:
            if pathlib.Path(preset.file_path).resolve() == file_path:
                return True

        return False

    def load_from_file(self, file_path: str) -> manager.NameManager | Preset | None:
        """Load the naming preset or naming manager data from the provided
        absolute preset file path.

        Args:
           file_path: Absolute file path to load.

        Returns:
           The loaded preset from the given file if it is a valid preset file;
           None if the file is not a valid preset or naming manager file.
        """

        if not file_path or not os.path.isfile(file_path):
            return None

        if file_path.endswith("." + PRESET_EXT):
            loaded_preset = Preset.load_from_path(
                pathlib.Path(file_path).resolve().as_posix()
            )
            if loaded_preset is not None:
                self._presets.append(loaded_preset)
                for manager_data in loaded_preset.managers_data:
                    self._available_manager_types.add(manager_data.modrig_type)
                return loaded_preset
        elif file_path.endswith("." + CONFIG_EXT):
            loaded_manager = manager.NameManager.from_path(file_path)
            self._naming_managers[loaded_manager.name] = loaded_manager

        return None

    def load_from_directory_path(self, directory: str):
        """Load all naming preset from the given folder recursively.

        Args:
            Absolute directory path to a folder containing naming presets.
        """

        if not directory or not os.path.isdir(directory):
            return

        for root, dirs, files in os.walk(directory):
            for preset_file in files:
                file_path = pathlib.Path(root, preset_file).as_posix()
                self.load_from_file(file_path)

    def load_from_hierarchy(self, hierarchy: dict):
        """Load all presets and constructs the preset hierarchy based on
        the given preset hierarchy data.

        Args:
            hierarchy: hierarchy data in the following format:
            {'name': 'modRig', 'children': [
                {'name': 'defaultPreset', 'children': []},
                {'name': 'UE5Preset', 'children': [
                    {'name': 'UE5ClaviclePreset', 'children': []}, {'name': 'UE5ThumbPreset', 'children': []}]}]}
        .note:: this function will clear the current presets cache and
            the current preset hierarchy before loading the new hierarchy data.
        """

        self._presets.clear()
        self._root_preset = None
        self._naming_managers.clear()
        self._available_manager_types.clear()

        paths = os.environ.get(self.ENV_VAR, default="").split(os.pathsep)
        pref_paths = self._preferences_interface.naming_preset_paths()

        visited = set()
        for _path in paths + pref_paths:
            if not _path:
                continue
            _path = pathlib.Path(_path).resolve().as_posix()
            if _path in visited:
                continue
            visited.add(_path)
            if self.contains_path(_path):
                continue
            if os.path.isdir(_path):
                self.load_from_directory_path(_path)
            elif os.path.isfile(_path):
                self.load_from_file(_path)
            elif not os.path.exists(_path):
                logger.warning(f"Invalid missing preset path will be ignored: {_path}")
                continue

        self._load_preset_hierarchy(hierarchy)

    def hierarchy_data(self) -> dict:
        """Return the current hierarchy raw data from the current preset
        hierarchy.

        Returns:
            The serialized preset hierarchy data.
        """

        def _serialize_hierarchy(preset: Preset) -> dict:
            """Recursively serializes the given preset.

            Args:
                preset: The preset to serialize.

            Returns:
                The serialized preset data.
            """

            return {
                "name": preset.name,
                "children": [
                    _serialize_hierarchy(child_preset)
                    for child_preset in preset.children
                ],
            }

        return (
            dict() if not self._root_preset else _serialize_hierarchy(self._root_preset)
        )

    def create_preset(
        self, name: str, directory: str, parent: Preset | None = None
    ) -> Preset:
        """Create a new preset instance.

        Args:
            name: Name for the new preset.
            directory: Directory where the preset should be created.
            parent: Optional parent preset for the new preset.

        Notes:
            The newly created preset will not be saved to disk.

        Returns:
            Newly created preset instance.
        """

        file_path = pathlib.Path(
            directory, os.path.extsep.join((name, PRESET_EXT))
        ).as_posix()
        new_preset = Preset(name=name, file_path=file_path, parent=parent)
        if parent is not None:
            parent.children.append(new_preset)
        self._presets.append(new_preset)

        return new_preset

    def find_preset(self, name: str) -> Preset | None:
        """Return the present instance with the provided name.

        Args:
            name: Name of the preset to find.

        Returns:
            Found preset instance if it exists; None otherwise.
        """

        for found_preset in self._presets:
            if found_preset.name == name:
                return found_preset

        return None

    def remove_preset(self, name: str) -> bool:
        """Remove the preset by name and returns whether the deletion
        operation was successful. Presets only will be removed from memory,
        not from the disk.

        Args:
            name: Name of the preset to remove.

        Notes:
            This function will also modify the parent preset by removing
            the preset from its children list if it has a parent preset.

        Returns:
            True if the preset remove operation was successful; False otherwise.
        """

        found_preset = self.find_preset(name)
        if found_preset is None:
            return False

        parent_preset = found_preset.parent
        if parent_preset is not None:
            parent_preset.children.remove(found_preset)

        self._presets.remove(found_preset)

        return True

    def delete_preset(self, preset: Preset) -> bool:
        """Delete the given preset instance from the manager and deletes the
        preset file.

        Args:
            preset: Preset instance to delete.

        Returns:
            True if the preset delete operation was successful; False otherwise.
        """

        if preset.exists():
            logger.debug(f"Deleting Preset file: {preset.file_path}")
            os.remove(preset.file_path)

        for manager_data in preset.managers_data:
            found_manager = manager_data.manager
            file_path = found_manager.config_path
            if file_path and os.path.isfile(file_path):
                logger.debug(f'Deleting configuration file: "{file_path}"')
                os.remove(file_path)

        return self.remove_preset(preset.name)

    def config_save_folder(self) -> str:
        """Return the current folder which all new presets will be saved into.

        Returns:
            Absolute path to the folder where presets will be saved.
        """

        return self._preferences_interface.naming_preset_save_path()

    def save_manager(self, naming_manager: manager.NameManager) -> bool:
        """Save the given naming manage instance to disk.

        Args:
            naming_manager: Instance of the naming manager to save.

        Returns:
            True if the naming manager was saved successfully; False otherwise.
        """

        if not naming_manager.config_path:
            config_folder = self.config_save_folder()
            file_path = pathlib.Path(
                config_folder, os.path.extsep.join([naming_manager.name, CONFIG_EXT])
            ).as_posix()
            naming_manager.config_path = file_path
        else:
            config_folder = os.path.dirname(naming_manager.config_path)
        logger.info(f'Saving Naming data: "{naming_manager.config_path}"')
        folder.ensure_folder_exists(config_folder)
        jsonio.write_to_file(naming_manager.serialize(), naming_manager.config_path)

        return True

    def _load_preset_hierarchy(self, hierarchy):
        """Handle the loading of the given naming hierarchy data.

        :param dict hierarchy: hierarchy data:
            {'name': 'modRig', 'children': [
                {'name': 'defaultPreset', 'children': []},
                {'name': 'UE5Preset', 'children': [
                    {'name': 'UE5ClaviclePreset', 'children': []},
                    {'name': 'UE5ThumbPreset', 'children': []}]}]}
        """

        def _process_child(child_hierarchy: dict, parent: Preset | None):
            """Recursively process the given hierarchy.

            Args:
                child_hierarchy: Child hierarchy data to process.
                parent: The parent preset to attach the child preset to.

            Returns:
                Newly processed Preset instance; None if the preset
                with the given name does not exist.
            """

            name = child_hierarchy["name"]
            try:
                child_preset = current_presets[name]
            except KeyError:
                logger.error("Missing naming manager preset: {}".format(name))
                return None

            if parent:
                parent.children.append(child_preset)
            child_preset.parent = parent

            for name_manager_data in child_preset.managers_data:
                name_manager = self._naming_managers.get(name_manager_data.name)
                if name_manager is None:
                    name_manager_data.manager = global_config
                    continue
                name_manager_data.manager = name_manager
                parent_manager = (
                    global_config if name_manager_data.modrig_type != "global" else None
                )
                if parent is not None:
                    parent_manager = parent.find_name_manager_for_type(
                        name_manager_data.modrig_type
                    )
                name_manager.parent_manager = parent_manager

            for _child_hierarchy in child_hierarchy.get("children", list()):
                _process_child(_child_hierarchy, parent=child_preset)

            return child_preset

        current_presets = {i.name: i for i in self._presets}
        global_config = self._naming_managers["modRigGlobalConfig"]

        if hierarchy:
            root = _process_child(hierarchy, parent=None)
        else:
            root = self.find_preset(constants.DEFAULT_PRESET_NAME)

        for preset in self._presets:
            if preset.parent is None and preset != root:
                preset.parent = root
                root.children.append(preset)

        self._root_preset = root
