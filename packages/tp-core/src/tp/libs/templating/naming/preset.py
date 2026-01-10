"""Preset management for naming conventions."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from tp.libs.python import yamlio
from tp.libs.templating import consts
from tp.libs.templating.naming import config, convention

logger = logging.getLogger(__name__)


class PresetsManager:
    """Manager class that handles the loading and saving of naming presets."""

    def __init__(
        self, configuration: config.NamingConfiguration | None = None
    ):
        """Initializes the PresetsManager.

        Args:
            configuration: Optional naming configuration to use. If not provided, uses the global configuration.
        """

        super().__init__()

        self._presets: list[NamingPreset] = []
        self._root_preset: NamingPreset | None = None
        self._naming_conventions: dict[str, convention.NamingConvention] = {}
        self._naming_convention_types: set[str] = set()
        self._configuration = configuration or config.get_configuration()

    @classmethod
    def from_configuration(
        cls, configuration: config.NamingConfiguration | None = None
    ) -> PresetsManager:
        """Creates a PresetsManager from a configuration.

        Args:
            configuration: Optional naming configuration to use. If not provided, uses the global configuration.

        Returns:
            Initialized PresetsManager instance with presets loaded from configured paths.
        """

        cfg = configuration or config.get_configuration()
        preset_manager = cls(configuration=cfg)

        # Load default preset from configured paths.
        default_preset_file = cfg.find_preset_file(cfg.default_preset_name)
        if default_preset_file:
            preset_manager.load_preset_from_file(default_preset_file)

        return preset_manager

    @property
    def naming_conventions(self) -> dict[str, convention.NamingConvention]:
        """Getter method that returns a dictionary with all the available naming conventions.

        Returns:
            dict[str, convention.NamingConvention]: naming conventions.
        """

        return self._naming_conventions

    def load_presets_from_directory(
        self, directory: str, hierarchy: dict | None = None
    ):
        """Recursively loads all naming presets from the given folder.

        Args:
            directory (str): absolute file path pointing to a directory.
            hierarchy (str | None): dictionary containing the preset hierarchy to load.
        """

        for root, _, files in os.walk(directory):
            for file_name in files:
                full_path = os.path.join(root, file_name)
                self.load_preset_from_file(full_path)

        self._load_preset_hierarchy(data=hierarchy)

    def load_preset_from_file(
        self, file_path: str, hierarchy: dict | None = None
    ) -> bool:
        """Loads the given file path which either contains a naming preset or a naming convention.

        Args:
            file_path (str): absolute file path pointing to a naming preset or naming convention.
            hierarchy (str | None): dictionary containing the preset hierarchy to load.

        Returns:
            bool: True if the file was loaded successfully; False otherwise.
        """

        # Register naming preset
        if not file_path.endswith(f".{consts.NAMING_PRESET_EXTENSION}"):
            logger.warning(
                f'Was not possible to load naming preset from file: "{file_path}"'
            )
            return False

        preset = NamingPreset.load_from_path(
            os.path.normpath(file_path), manager=self
        )
        if preset is None:
            logger.warning(
                f'Was not possible to load naming preset from file: "{file_path}"'
            )
            return False
        self._presets.append(preset)
        for naming_convention in preset.naming_conventions:
            self._naming_convention_types.add(naming_convention.type)
            name_convention_file_path = os.path.join(
                os.path.dirname(file_path),
                f"{naming_convention.name}.{consts.NAMING_CONVENTION_EXTENSION}",
            )
            # If the convention file is not in the same directory as the preset,
            # search for it in all configured preset paths.
            if not os.path.isfile(name_convention_file_path):
                found_path = self._configuration.find_convention_file(
                    naming_convention.name
                )
                if found_path:
                    name_convention_file_path = found_path
                else:
                    logger.warning(
                        f'Naming convention file does not exist: "{naming_convention.name}"'
                    )
                    continue
            self._load_naming_convention_from_file(
                name_convention_file_path,
                naming_convention_type=naming_convention.type,
            )

        if hierarchy is not None:
            self._load_preset_hierarchy(hierarchy)

        return True

    def preset_hierarchy(self, preset: NamingPreset) -> dict:
        """Returns the current hierarchy dictionary of the given preset.

        Args:
            preset (NamingPreset): naming preset to get hierarchy of.

        Returns:
            dict: preset hierarchy.
        """

        def _serialize_hierarchy(_preset: NamingPreset) -> dict:
            """Internal function that handles the recursive hierarchy serialization.

            Args:
                _preset (NamingPreset): naming preset to serialize hierarchy of.

            Returns:
                dict: serialized preset hierarchy.
            """

            return {
                "name": _preset.name,
                "children": [
                    _serialize_hierarchy(_child_preset)
                    for _child_preset in _preset.children
                ],
            }

        if not self._root_preset:
            return {}

        return _serialize_hierarchy(self._root_preset)

    def _load_naming_convention_from_file(
        self, file_path: str, naming_convention_type: str | None
    ) -> bool:
        """Loads the given file path which either contains a naming preset or a naming convention.

        Args:
            file_path (str): absolute file path pointing to a naming preset or naming convention.
            naming_convention_type (str or None): optional naming convention type.

        Returns:
            bool: True if the file was loaded successfully; False otherwise.
        """

        # Register naming convention.
        if not file_path.endswith(f".{consts.NAMING_CONVENTION_EXTENSION}"):
            return False

        naming_convention = convention.NamingConvention.from_path(file_path)
        if naming_convention is None:
            logger.warning(
                f'Was not possible to load naming convention from file: "{file_path}"'
            )
            return False

        self._naming_conventions[naming_convention.name] = naming_convention

        if naming_convention_type:
            naming_convention.original_naming_data["type"] = (
                naming_convention_type
            )
        naming_convention_type = naming_convention.original_naming_data.get(
            "type"
        )
        if naming_convention_type:
            self._naming_convention_types.add(naming_convention_type)

        return True

    def _load_preset_hierarchy(self, data: dict | None = None):
        """Internal function that handles the loading of the presets making sure all presets and naming conventions have
        a root parent and also making sure that internal naming data for all presets is properly initialized.

        Args:
            data (dict or None): optional hierarchy data to load presets from. This allows us to define a hierarchy of
            presets that will be loaded using a parent-child hierarchy. If not given, default preset will be used
                as the root preset (which is the normal behaviour). The preset hierarchy data has the following format:
                {
                    "name": "AnyName",
                    "children":  [
                        {
                            "name": "myPreset",
                            "children": [
                                {
                                    "name": "myChildPreset"
                                }
                                ...
                            ]
                        },
                        ...
                    ]
                }
        """

        def _process_child(_child_data: dict, _parent: NamingPreset | None):
            """Internal recursive function that process child presets.

            Args:
                _child_data (dict): child data from hierarchy data.
                _parent (NamingPreset or None): parent naming preset.
            """

            _name = _child_data["name"]
            try:
                _child_preset: NamingPreset | None = current_presets[_name]
            except KeyError:
                logger.warning(f"Missing naming preset: {_name}")
                return
            _child_preset.parent = _parent

            for _naming_convention_data in _child_preset.naming_conventions:
                _naming_convention = self._naming_conventions.get(
                    _naming_convention_data.name
                )
                if _naming_convention is None:
                    _naming_convention_data.naming_convention = (
                        global_naming_convention
                    )
                    continue
                _naming_convention_data.naming_convention = _naming_convention
                _parent_naming_convention = (
                    global_naming_convention
                    if _naming_convention_data.type != "global"
                    else None
                )
                if _parent is not None:
                    _parent_naming_convention = (
                        _parent.find_naming_convention_by_type(
                            _naming_convention_data.type
                        )
                    )
                _naming_convention.parent = _parent_naming_convention

            for _child in _child_data.get("children", []):
                _process_child(_child, _parent=_child_preset)

        current_presets = {preset.name: preset for preset in self._presets}
        global_naming_convention = self._naming_conventions["global"]
        root = (
            _process_child(data, _parent=None)
            if data
            else self.find_preset(consts.DEFAULT_NAMING_PRESET_NAME)
        )

        # Make sure all presets have at least one parent.
        for preset in self._presets:
            if preset.parent is None and preset != root:
                preset.parent = root

        # Make sure all naming convention have at least one parent.
        for naming_convention in self._naming_conventions.values():
            if (
                naming_convention.parent is None
                and naming_convention != global_naming_convention
            ):
                naming_convention.parent = global_naming_convention

        self._root_preset = root

    def find_preset(self, name: str) -> NamingPreset | None:
        """Returns the naming preset that matches given name.

        Args:
            name (str): preset name to search for.

        Returns:
            NamingPreset or None: found naming preset.
        """

        found_naming_preset: NamingPreset | None = None
        for preset in self._presets:
            if preset.name == name:
                found_naming_preset = preset
                break

        return found_naming_preset

    def find_naming_conventions_by_type(
        self, type_: str
    ) -> list[convention.NamingConvention]:
        """Returns all naming conventions based on given type.

        Args:
            type_ (str): naming convention type.

        Returns:
            list[convention.NamingConvention]: list of naming conventions found.
        """

        return [
            i
            for i in self._naming_conventions.values()
            if i.original_naming_data.get("type", "") == type_
        ]


class NamingPreset:
    """Class that represents a collection of naming conventions configurations. It is represented in the following
    format:
        {
          "name":"Convergence",
          "namingConventions": [
            {
              "name": "cinematicsNaming",
              "type": "cinematics"
            },
            ...
          ]
        }

    Also, a naming preset can define a child-parent relationship that allow child naming presets to inherit the
    configurations of its parent naming preset.
    """

    def __init__(
        self,
        name: str,
        file_path: str,
        manager: PresetsManager,
        parent: NamingPreset,
    ):
        """Naming Preset Constructor.

        Args:
            name (str): preset name.
            file_path (str): absolute file path where the preset data is located. It does not need to exist.
            manager (PresetsManager): presets manager instance.
            parent (NamingPreset): parent preset.
        """

        super().__init__()

        self._name = name
        self._file_path = file_path
        self._manager = manager
        self._parent = parent
        self._children: list[NamingPreset] = []
        self._naming_conventions: list[NameConventionData] = []

    def __repr__(self) -> str:
        """Overrides __repr__ function to return a custom display name.

        Returns:
            str: naming preset display name.
        """

        return f"<{self.__class__.__name__}(name={self.name}) object at {hex(id(self))}>"

    @classmethod
    def load_from_path(
        cls, file_path: str, manager: PresetsManager
    ) -> NamingPreset | None:
        """Loads the naming preset from given path.

        Args:
            file_path (str): absolute file path pointing to a valid naming preset file.
            manager (PresetsManager): manager used to register the preset. Preset can be saved and accessed through
                this manager.

        Returns:
            NamingPreset or None: naming preset instance if preset file contents were valid; None otherwise.
        """

        try:
            logger.debug(f"Loading Naming Preset from path: {file_path}")
            data = yamlio.read_file(file_path)
        except json.decoder.JSONDecodeError:
            logger.error(
                f"Failed to load JSON file: {file_path}", exc_info=True
            )
            return None

        return cls.load_from_data(data, file_path, manager)

    @classmethod
    def load_from_data(
        cls,
        data: dict,
        file_path: str,
        manager: PresetsManager,
        parent: NamingPreset | None = None,
    ) -> NamingPreset:
        """Loads the naming preset from given preset data.

        Args:
            data (dict): dictionary containing the preset data to load.
            file_path (str): absolute file path pointing to a valid naming preset file.
            manager (PresetsManager): manager used to register the preset. Preset can be saved and accessed through
                this manager.
            parent (NamingPreset or None): optional parent preset.

        Returns:
            NamingPreset: new naming preset instance.
        """

        name = data.get("name")
        new_preset = cls(name, file_path, manager, parent=parent)
        for naming_convention in data.get("namingConventions", []):
            naming_convention_data = NameConventionData(
                naming_convention["name"], naming_convention["type"]
            )
            new_preset.naming_conventions.append(naming_convention_data)

        return new_preset

    @property
    def name(self) -> str:
        """Getter method that returns preset name.

        :return: preset name.
        :rtype: str
        """

        return self._name

    @property
    def naming_conventions(self) -> list[NameConventionData]:
        """Getter method that returns a list with all naming convention definitions found within preset file.

        Returns:
            list[NameConventionData]: list of naming convention data instances.
        """

        return self._naming_conventions

    @property
    def parent(self) -> NamingPreset | None:
        """Getter method that returns parent naming preset.

        Returns:
            NamingPreset or None: parent naming preset instance.
        """

        return self._parent

    @parent.setter
    def parent(self, value: NamingPreset | None):
        """Setter method that sets the parent of this naming preset.

        Args:
            value (NamingPreset): naming preset parent.
        """

        if value is None and self._parent is not None:
            self._parent.children.remove(self)

        self._parent = value

        if value is not None:
            value.children.append(self)

    @property
    def children(self) -> list[NamingPreset]:
        """Getter method that returns children naming presets.

        Returns:
            list[NamingPreset]: children naming presets.
        """

        return self._children

    def exists(self) -> bool:
        """Returns whether this naming preset exists within disk.

        Returns:
            bool: True if naming preset file exists in disk; False otherwise.
        """

        return os.path.exists(self._file_path)

    def find_naming_convention_data_by_type(
        self, type_: str, recursive: bool = True
    ) -> NameConventionData | None:
        """Returns the naming convention data by type.

        Args:
            type_ (str): type of the naming convention to find.
            recursive (bool): whether to find naming conventions recursively.

        Returns:
            NameConventionData or None: naming convention data instance; None if naming convention with given type does
            not exist.
        """

        # First we try to find naming conventions within the internal list of naming conventions.
        found_naming_convention_data: NameConventionData | None = None
        for naming_convention_data in self._naming_conventions:
            if naming_convention_data.type == type_:
                found_naming_convention_data = naming_convention_data
                break
        if found_naming_convention_data is not None:
            return found_naming_convention_data

        # If a parent preset is defined we recursively check parent naming conventions.
        if self._parent is not None and recursive:
            return self._parent.find_naming_convention_data_by_type(
                type_, recursive=recursive
            )
        elif self._parent is None:
            # We try to find a naming convention outside this naming preset.
            global_naming_conventions = (
                self._manager.find_naming_conventions_by_type(type_)
            )
            if not global_naming_conventions:
                return None
            naming_convention_data = NameConventionData(
                global_naming_conventions[0],
                type_,
                global_naming_conventions[0],
            )
            return naming_convention_data

    def find_naming_convention_by_name(
        self, name: str, recursive: bool = True
    ) -> convention.NamingConvention | None:
        """Returns the naming convention instance by name.

        Args:
            name (str): name of the naming convention to find.
            recursive (bool): whether to find naming conventions recursively.

        Returns:
            convention.NamingConvention or None: naming convention instance; None if naming convention with given name
            does not exist.
        """

        # First we try to find naming conventions within the internal list of naming conventions.
        found_naming_convention: convention.NamingConvention | None = None
        for naming_convention_data in self._naming_conventions:
            if naming_convention_data.name == name:
                found_naming_convention = (
                    naming_convention_data.naming_convention
                )
                break
        if found_naming_convention is not None:
            return found_naming_convention

        # If a parent preset is defined we recursively check parent naming conventions.
        if self._parent is not None and recursive:
            return self._parent.find_naming_convention_by_name(name)

    def find_naming_convention_by_type(
        self, type_: str, recursive: bool = True
    ) -> convention.NamingConvention | None:
        """Returns the naming convention instance by type.

        Args:
            type_ (str): type of the naming convention to find.
            recursive (bool): whether to find naming conventions recursively.

        Returns:
            convention.NamingConvention or None: naming convention instance; None if naming convention with given type
            does not exist.
        """

        naming_convention_data = self.find_naming_convention_data_by_type(
            type_, recursive=recursive
        )

        # If no naming convention data if found, fallback to the global naming convention.
        if naming_convention_data is None:
            return self.find_naming_convention_data_by_type(
                "global"
            ).naming_convention

        return naming_convention_data.naming_convention

    def to_dict(self) -> dict:
        """Returns the raw representing of this naming preset.

        Returns:
            dict: naming preset as a dictionary.
        """

        return {
            "name": self.name,
            "namingConventions": [
                i.to_dict() for i in self.naming_conventions
            ],
        }


class NameConventionData:
    """Data class that stores the naming convention name, its type and the naming convention instance for the preset to
    use.
    """

    def __init__(
        self,
        name: str,
        type_: str,
        name_convention: convention.NamingConvention | None = None,
    ):
        super().__init__()

        self._name = name
        self._type = type_
        self._name_convention = name_convention

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, NameConventionData):
            return False

        return self.name == other.name and self.type == other.type

    def __ne__(self, other: Any):
        if not isinstance(other, NameConventionData):
            return True

        return self.name != other.name or self.type != other.type

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, type={self.type}) object at {hex(id(self))}>"

    @property
    def name(self) -> str:
        """Getter method that returns the name of the naming convention to use by this preset. This name should match a
        naming convention file name.

        Returns:
            str: naming convention name.
        """

        return self._name

    @property
    def type(self) -> str:
        """Getter method that returns the type of the preset.

        Returns:
            str: preset type.
        """

        return self._type

    @property
    def naming_convention(self) -> convention.NamingConvention:
        """Getter method that returns naming convention instance wrapped by this instance.

        Returns:
            NamingConvention: naming convention instance.
        """

        return self._name_convention

    @naming_convention.setter
    def naming_convention(self, value: convention.NamingConvention):
        """Setter method that sets the naming convention instance wrapped by this intance.

        Args:
            value (convention.NamingConvention): naming convention instance.
        """

        self._name_convention = value

    def to_dict(self) -> dict:
        """Returns the raw representation of the name preset containing the name convention to use and its type.

        Returns:
            dict: name convention raw data.
        """

        return {"name": self.name, "type": self.type}
