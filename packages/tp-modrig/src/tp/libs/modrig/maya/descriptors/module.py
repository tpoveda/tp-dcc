from __future__ import annotations

import copy
import json

from ..base import constants


class ModuleDescriptor:
    VERSION: str = "1.0"

    def __init__(
        self,
        data: dict | None = None,
        original_descriptor: ModuleDescriptor | dict | None = None,
        path: str | None = None,
    ):
        data = data or {}
        self._data = data
        self._uuid = data.get("uuid", "")
        self._path: str = path or ""
        self._name: str = data.get("name", "")
        self._side: str = data.get("side", "")
        self._type: str = data.get("type", "")
        self._parent: str | None = data.get(
            constants.MODULE_PARENT_DESCRIPTOR_KEY, None
        )
        self._connections = data.get(constants.MODULE_CONNECTIONS_DESCRIPTOR_KEY, {})
        self._naming_preset: str = data.get(
            constants.MODULE_NAMING_PRESET_DESCRIPTOR_KEY, ""
        )

        self._version: str = ""

        self._original_descriptor = (
            ModuleDescriptor(original_descriptor)
            if original_descriptor is not None
            else {}
        )

    def __repr__(self) -> str:
        """Provide a string representation of the object's information for
        developers.

        Returns:
            A string containing the class name and the name attribute.
        """

        return f"<{self.__class__.__name__}> {self.name}"

    @property
    def data(self) -> dict:
        """The raw descriptor data."""

        return self._data

    @property
    def uuid(self) -> str:
        """The unique identifier of the descriptor."""

        return self._uuid

    @uuid.setter
    def uuid(self, value: str):
        """Set the unique identifier of the descriptor."""

        self._uuid = value

    @property
    def path(self) -> str:
        """The absolute path to this descriptor."""

        return self._path

    @path.setter
    def path(self, value: str):
        """Set the absolute path to this descriptor."""

        self._path = value

    @property
    def name(self) -> str:
        """The name of the descriptor."""

        return self._name

    @name.setter
    def name(self, name: str):
        """Set the name of the descriptor."""

        self._name = name

    @property
    def side(self) -> str:
        """The side name of the descriptor."""

        return self._side

    @side.setter
    def side(self, side: str):
        """Set the side name of the descriptor."""

        self._side = side

    @property
    def type(self) -> str:
        """The module type this descriptor is attached to."""

        return self._type

    @type.setter
    def type(self, value: str):
        """Set the module type this descriptor is attached to."""

        self._type = value

    @property
    def parent(self) -> str | None:
        """The parent descriptor in the form {moduleName:side}."""

        return self._parent

    @parent.setter
    def parent(self, value: str | None):
        """Set the parent descriptor in the form {moduleName:side}."""

        self._parent = value

    @property
    def connections(self) -> dict:
        """The connection types to the parent component."""

        return self._connections

    @connections.setter
    def connections(self, connections: dict):
        """Set the connection types to the parent component."""

        self._connections = connections

    @property
    def naming_preset(self) -> str:
        """The naming preset of the descriptor."""

        return self._naming_preset

    @naming_preset.setter
    def naming_preset(self, naming_preset: str):
        """Set the naming preset of the descriptor."""

        self._naming_preset = naming_preset

    @property
    def version(self) -> str:
        """The version of the descriptor."""

        return self._version


def migrate_to_latest_version(
    descriptor_data: dict | ModuleDescriptor,
    original_descriptor: ModuleDescriptor | None = None,
) -> dict | ModuleDescriptor:
    """Migrate a module descriptor to its latest version while preserving
    critical rig layer data from the original descriptor, if provided.

    This function is designed to ensure consistency between module descriptors
    during updates or modifications, especially by retaining the rig layer
    details. Depending on the data type of `descriptor_data`, the function
    modifies and returns an updated version of the descriptor.

    Args:
        descriptor_data: The descriptor data to migrate. It could either be
            in dictionary format or an instance of a `ModuleDescriptor` class.
        original_descriptor: The original module descriptor containing the
            base rig layer data to preserve. If not provided, no data
            will be preserved from an original descriptor.

    Returns:
        The updated descriptor, potentially containing the preserved rig layer.
    """

    # Expect rig layer to come from the base descriptor not the scene, so
    # we make sure to keep the original rig data.
    if original_descriptor:
        if isinstance(descriptor_data, dict):
            descriptor_data[constants.MODULE_RIG_LAYER_DESCRIPTOR_KEY] = copy.deepcopy(
                original_descriptor.rig_layer
            )
        else:
            descriptor_data.rig_layer = copy.deepcopy(original_descriptor.rig_layer)

    return descriptor_data


def load_descriptor(
    descriptor_data: dict | ModuleDescriptor,
    original_descriptor: dict | ModuleDescriptor,
    path: str | None = None,
) -> ModuleDescriptor:
    """Load and process a module descriptor, ensuring it's migrated to the
    latest version and structured properly for further use.

    Args:
        descriptor_data: The input descriptor, either in dictionary form or
            as a `ModuleDescriptor` instance, which will be migrated to the
            latest version.
        original_descriptor: The original descriptor, either in dictionary
            format or as a `ModuleDescriptor` instance, which serves as the
            base for deep copying.
        path: Optional path where the module descriptor is located or stored,
            used for referencing within the resulting `ModuleDescriptor`.

    Returns:
        A new instance of `ModuleDescriptor` containing the migrated
            descriptor data, a deep copy of the original descriptor, and
            the optional path.

    """

    if isinstance(descriptor_data, dict):
        latest_data = migrate_to_latest_version(descriptor_data)
        return ModuleDescriptor(
            data=latest_data,
            original_descriptor=copy.deepcopy(original_descriptor),
            path=path,
        )

    latest_data = migrate_to_latest_version(descriptor_data)
    return ModuleDescriptor(
        data=latest_data.serialize(),
        original_descriptor=copy.deepcopy(original_descriptor),
        path=path,
    )


def parse_raw_descriptor(descriptor_data: dict) -> dict:
    """Parse a raw descriptor data dictionary, transforming it into a
    structured and interpreted format.

    The function processes various keys in the input data, handling them based
    on specific rules and conditions, such as JSON decoding and splitting data
    into components like DAG, settings, and metadata.

    The parsed data is returned as a new structured dictionary.

    Args:
        descriptor_data: A dictionary containing raw descriptor data.
            The values can potentially be JSON strings or other structured
            data formats that need parsing.

    Returns:
        A dictionary containing the structured and interpreted descriptor data.
    """

    translated_data = {}

    for k, v in descriptor_data.items():
        if not v:
            continue
        if k == "info":
            translated_data.update(json.loads(v))
            continue
        elif k == constants.MODULE_SPACE_SWITCH_DESCRIPTOR_KEY:
            translated_data[constants.MODULE_SPACE_SWITCH_DESCRIPTOR_KEY] = json.loads(
                v
            )
            continue
        dag, settings, metadata = (
            v[constants.MODULE_DAG_DESCRIPTOR_KEY] or "[]",
            v[constants.MODULE_SETTINGS_DESCRIPTOR_KEY]
            or ("{}" if k == constants.MODULE_RIG_LAYER_DESCRIPTOR_KEY else "[]"),
            v[constants.MODULE_METADATA_DESCRIPTOR_KEY] or "[]",
        )
        translated_data[k] = {
            constants.MODULE_DAG_DESCRIPTOR_KEY: json.loads(dag),
            constants.MODULE_SETTINGS_DESCRIPTOR_KEY: json.loads(settings),
            constants.MODULE_METADATA_DESCRIPTOR_KEY: json.loads(metadata),
        }

    return translated_data
