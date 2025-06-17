from __future__ import annotations

import json
import typing
from typing import cast
from collections.abc import Iterator

from loguru import logger

from tp.libs.python import helpers, profiler
from tp.libs.maya.meta.base import find_meta_nodes_by_class_type

from .module import Module
from . import constants, errors
from .configuration import RigConfiguration
from ..meta.rig import ModRig

if typing.TYPE_CHECKING:
    from tp.libs.naming.manager import NameManager


class Rig:
    """Base class for all rigs in the ModRig library.

    This class allows the construction and destruction of modules.
    """

    def __init__(
        self, rig_config: RigConfiguration | None = None, meta: ModRig | None = None
    ):
        super().__init__()

        self._meta = meta
        self._modules_cache: set[Module] = set()
        self._config = rig_config or RigConfiguration()

    def __bool__(self) -> bool:
        """Return whether this rig exists by checking the existing of its
        metanode instance.

        Returns:
            True if the rig exists; False otherwise.
        """

        return self.exists()

    def __eq__(self, other: Rig | None) -> bool:
        """Return whether this rig is equal to the given rig instance.

        Args:
            other: rig instance to compare with.

        Returns:
            True if both rig instances are equal; False otherwise.
        """

        if not other:
            return False

        return self.meta == other.meta

    def __ne__(self, other: Rig | None) -> bool:
        """Return whether this rig is not equal to the given rig instance.

        Args:
            other: Rig instance to compare with.

        Returns:
            True if both rig instances are not equal; False otherwise.
        """

        return self._meta != other.meta

    def __hash__(self) -> int:
        """Return the hash value for this rig instance.

        Returns:
            The hash value of the rig instance.
        """

        return hash(self._meta) if self._meta is not None else hash(id(self))

    def __repr__(self) -> str:
        """Return the string representation of this rig instance.

        Returns:
            string representation of the rig instance.
        """

        return f"<{self.__class__.__name__}>(name={self.name()})"

    @property
    def meta(self) -> ModRig | None:
        """The metanode instance of the rig."""

        return self._meta

    @property
    def configuration(self) -> RigConfiguration:
        """The configuration of the rig."""

        return self._config

    def version_info(self) -> dict[str, str]:
        """Return the build version for the rig composed by the
        application version, tp-dcc version and ModRig version.

        Returns:
            Version info as a dictionary.
        """

        if self._meta is None:
            return {}

        try:
            return json.loads(
                self._meta.attribute(constants.RIG_VERSION_INFO_ATTR).value()
            )
        except json.JSONDecodeError:
            return {}

    def naming_manager(self) -> NameManager:
        """Return the naming manager for the current rig instance.

        Returns:
            The naming manager instance used for the rig.
        """

        return self.configuration.find_name_manager_for_type("rig")

    def exists(self) -> bool:
        """Return whether this rig exists by checking the existing of the
        metanode instance.

        Returns:
            True if the rig exists; False otherwise.
        """

        return self._meta is not None and self._meta.exists()

    def name(self) -> str:
        """Return the name of the rig by accessing metanode instance data.

        Returns:
            The name of the rig if it exists; otherwise, an empty string.
        """

        return self._meta.rig_name() if self.exists() else ""

    def cached_configuration(self) -> dict:
        """Return the configuration cached on the rig metanode instance as a
        dictionary.

        Returns:
            The configuration dictionary if it exists; otherwise, an empty
            dictionary.
        """

        config_plug = self._meta.attribute(constants.RIG_CONFIG_ATTR)
        try:
            config_data = config_plug.value()
            if config_data:
                return json.loads(config_data)
        except ValueError:
            pass

        return {}

    @profiler.fn_timer
    def save_configuration(self) -> dict:
        """Serialize and save the configuration for this rig on the metanode
        instance.

        Returns:
            The saved serialized configuration as a dictionary.
        """

        logger.debug("Saving rig configuration...")
        config_data = self.configuration.serialize(rig=self)
        if config_data:
            config_plug = self._meta.attribute(constants.RIG_CONFIG_ATTR)
            config_plug.set(json.dumps(config_data))

        return config_data

    @profiler.fn_timer
    def start_session(
        self, name: str | None = None, namespace: str | None = None
    ) -> ModRig:
        """Start a new session for the rig with the provided name and
        namespace.

        If the rig already exists, then the existing rig will be returned.

        Args:
            name: Name of the rig to initialize.
            namespace: The rig namespace to use for the rig.

        Returns:
            The initialized rig metanode instance.
        """

        meta = self._meta
        if meta is None:
            meta = root_rig_by_name(name, namespace=namespace)
        if meta is not None:
            self._meta = meta
            logger.debug(f"Found rig in scene with name: {self.name()}")
            self.configuration.update_from_rig(self)
            return self._meta

        namer = self.naming_manager()
        meta = ModRig(name=namer.resolve("rigMeta", {"rigName": name, "type": "meta"}))
        meta.attribute(constants.NAME_ATTR).set(name)
        meta.attribute(constants.ID_ATTR).set(name)
        meta.create_transform(namer.resolve("rigHrc", {"rigName": name, "type": "hrc"}))
        meta.create_selection_sets(namer)
        self._meta = meta

        return self._meta


def iterate_scene_rig_meta_nodes() -> Iterator[ModRig]:
    """Generator function that iterates over all rig meta node instances
    within the current scene.

    Yields:
        `ModRig` instances representing the rig metanodes found in the scene.
    """

    for found_meta_rig in find_meta_nodes_by_class_type(constants.RIG_TYPE):
        yield cast(ModRig, found_meta_rig)


def iterate_scene_rigs() -> Iterator[Rig]:
    """Generator function that iterates over all rig instances within the
    current scene.

    Yields:
        `Rig` instances representing the rig metanodes found in the scene.
    """

    for meta_rig in iterate_scene_rig_meta_nodes():
        rig_instance = Rig(meta=meta_rig)
        rig_instance.start_session()
        yield rig_instance


def root_rig_by_name(name: str, namespace: str | None = None) -> ModRig | None:
    """Find the root meta with the provided name and namespace.

    Args:
        name: The name of the rig to find.
        namespace: Optional namespace to search for the rig metanode instance.

    Returns:
        Found root metanode instance with the given name and namespace.

    Raises:
        errors.RigDuplicationError: If there are duplicated rig names in
            the scene.
    """

    meta_rigs: list[ModRig] = []
    meta_rig_names: list[str] = []

    found_meta_rig: ModRig | None = None
    for meta_node in iterate_scene_rig_meta_nodes():
        meta_rigs.append(meta_node)
        meta_rig_names.append(meta_node.attribute(constants.NAME_ATTR).value())
    if not meta_rigs:
        return None

    if not namespace:
        dupes = helpers.duplicates_in_list(meta_rig_names)
        if dupes:
            raise errors.RigDuplicationError(dupes)
        for meta_rig in meta_rigs:
            if meta_rig.attribute(constants.NAME_ATTR).value() == name:
                found_meta_rig = meta_rig
                break

    if found_meta_rig is None and namespace:
        namespace = namespace if namespace.startswith(":") else f":{namespace}"
        for meta_rig in meta_rigs:
            rig_namespace = meta_rig.namespace()
            if (
                rig_namespace == namespace
                and meta_rig.attribute(constants.NAME_ATTR).value() == name
            ):
                found_meta_rig = meta_rig
                break

    return found_meta_rig
