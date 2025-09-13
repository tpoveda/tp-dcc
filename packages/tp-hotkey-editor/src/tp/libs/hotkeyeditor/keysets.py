from __future__ import annotations

import os
import glob
from pathlib import Path

from loguru import logger

from tp import dcc
from tp.core import host
from tp.libs.python import jsonio
from tp.preferences import manager
from tp.libs.python.decorators import Singleton

from . import constants, utils
from .keyset import KeySet


class KeySetsManager(metaclass=Singleton):
    """Manager for the hotkey sets."""

    DEFAULT_KEYSET_NAME = constants.DEFAULT_KEYSET
    HOST_CUSTOM_KEYSET_NAME = constants.HOST_CUSTOM_KEYSET
    HOST_DEFAULT_KEYSET_NAME = constants.HOST_KEYSET
    PREFIX = constants.KEY_SET_PREFIX
    VERSION = (1, 0)

    def __init__(self):
        super().__init__()

        current_host = host.current_host().host.name.lower()
        host_custom_keyset_name = self.HOST_CUSTOM_KEYSET_NAME.format(current_host)
        host_default_keyset_name = self.HOST_DEFAULT_KEYSET_NAME.format(current_host)

        relative_user_prefs_path = constants.RELATIVE_USER_PREFS_PATH.format(
            host.current_host().host.name.lower()
        )
        relative_internal_prefs_path = constants.RELATIVE_INTERNAL_PATH.format(
            host.current_host().host.name.lower()
        )

        self._hotkey_user_path = str(
            Path(
                manager.current_instance().root("user"),
                relative_user_prefs_path,
            )
        )
        self._hotkey_internal_path = str(
            Path(
                manager.current_instance().package_preference_location(
                    constants.PREF_FOLDER_NAME.replace("_", "-")
                ),
                relative_internal_prefs_path,
            )
        )
        self._default_key_set_path = str(
            Path(self._hotkey_internal_path) / self.DEFAULT_KEYSET_NAME
        )
        self._host_key_set_path = str(
            Path(self._hotkey_internal_path) / host_custom_keyset_name
        )
        self._new_key_set_template_path = str(
            Path(self._hotkey_internal_path) / constants.DEFAULT_TEMPLATE
        )
        self._default_key_set_path_user = str(
            Path(self._hotkey_user_path) / self.DEFAULT_KEYSET_NAME
        )
        self._host_key_set_path_user = str(
            Path(self._hotkey_user_path)
            / self.HOST_CUSTOM_KEYSET_NAME.format(host.current_host().host.name.lower())
        )
        self._new_key_set_template_path_user = str(
            Path(self._hotkey_user_path) / constants.DEFAULT_TEMPLATE
        )

        logger.info(f"User hotkey path: {self._hotkey_user_path}")
        logger.info(f"Internal hotkey path: {self._hotkey_internal_path}")
        logger.info(f"Default key set path: {self._default_key_set_path}")
        logger.info(f"Host key set path: {self._host_key_set_path}")
        logger.info(f"New key set template path: {self._new_key_set_template_path}")
        logger.info(f"User default key set path: {self._default_key_set_path_user}")
        logger.info(f"User host key set path: {self._host_key_set_path_user}")
        logger.info(
            f"User new key set template path: {self._new_key_set_template_path_user}"
        )

        self._default_key_set = self._create_keyset(
            json_path=f"{self._default_key_set_path_user}{constants.KEYSET_EXTENSION}"
        )
        self._host_key_set = self._create_keyset(
            json_path=f"{self._host_key_set_path_user}{constants.KEYSET_EXTENSION}"
        )
        self._new_key_set_template = self._create_keyset(
            json_path=f"{self._new_key_set_template_path_user}{constants.KEYSET_EXTENSION}"
        )
        self._key_sets: list[KeySet] = []
        self._reverts: list[KeySet] = []
        self._locked: list[str] = [
            self.DEFAULT_KEYSET_NAME,
            host_custom_keyset_name,
            host_default_keyset_name,
        ]
        self._current_key_set: KeySet | None = None

        self.revert_to_defaults()

    # === Properties === #

    @property
    def hotkey_user_path(self) -> str:
        """The user hotkey preferences path."""

        return self._hotkey_user_path

    @property
    def hotkey_internal_path(self) -> str:
        """The internal hotkey preferences path."""

        return self._hotkey_internal_path

    # === Creation === #

    def _create_keyset(
        self, key_set: KeySet | None = None, json_path: str = ""
    ) -> KeySet:
        """Get the keyset instance.

        Args:
            key_set: Optional existing key set instance to create new instance
                from.
            json_path: Optional path to the keyset JSON file.

        Returns:
            The keyset instance.

        Raises:
            NotImplementedError: If the current DCC is not supported.
        """

        if dcc.is_maya():
            from .maya.keyset import MayaKeySet as _KeySet
        else:
            raise NotImplementedError(
                f"Hotkey editor is only implemented for current DCC: {dcc.current_dcc()}."
            )

        if key_set is not None:
            return _KeySet.from_key_set(key_set)

        return _KeySet(manager=self, json_path=json_path)

    # === Installation === #

    def install_hotkeys(self):
        """Install all the available hotkey sets."""

        for key_set in self._key_sets:
            key_set.install()

    def save_hotkeys(self, save_over_defaults: bool = False):
        """Save all the available hotkey sets to disk."""

        for key_set in self._key_sets:
            if (
                not self.is_key_set_locked(key_set.name)
                or utils.is_admin_mode()
                or save_over_defaults
            ):
                logger.info(f"{key_set.name}: Saving to disk: {key_set.file_path}")
                utils.backup_file(key_set.file_path)
                key_set.save()
            else:
                logger.info(
                    f"{key_set.name}: Not saving to disk as it is locked (read-only). Ignoring..."
                )

        self.set_all_reverts()

    # === Active KeySet === #

    def current_key_set(self, force_host: bool = False) -> KeySet | None:
        """Get the current active key set.

        Args:
            force_host: Whether to force getting the current key set from the
                host application. This is useful when the current key set has
                been changed outside the hotkey editor.

        Returns:
            The current active `KeySet` instance.
        """

        if self._current_key_set and not force_host:
            return self._current_key_set

        current = host.current_host().host.current_hotkey_set_name()

        found_key_set: KeySet | None = None
        all_key_sets = self._key_sets + [self._host_key_set]
        for key_set in all_key_sets:
            if key_set.name == current:
                found_key_set = key_set
                self._current_key_set = found_key_set
                break

        return found_key_set

    def is_default_key_set(self) -> bool:
        """Check if the current active key set is the default key set.

        Returns:
            `True` if the current active key set is the default key set; `False` otherwise.
        """

        current_key_set = self.current_key_set()
        if not current_key_set:
            return False

        return current_key_set.name == self.DEFAULT_KEYSET_NAME

    def is_locked_key_set(self) -> bool:
        """Check if the current active key set is locked (read-only).

        Returns:
            `True` if the current active key set is locked; `False` otherwise.
        """

        current_key_set = self.current_key_set()
        if not current_key_set:
            return False

        return self.is_key_set_locked(self._current_key_set.name)

    # === Query === #

    def key_sets_by_name(self, names: list[str]) -> list[KeySet]:
        """Get key sets by their names.

        Args:
            names: List of key set names to retrieve.

        Returns:
            List of `KeySet` instances matching the provided names.
        """

        return [ks for ks in self._key_sets if ks.name in names]

    def is_key_set_locked(self, key_set_name: str) -> bool:
        """Check if a key set is locked (read-only).

        Args:
            key_set_name: The name of the key set to check.

        Returns:
            `True` if the key set is locked; `False` otherwise.
        """

        locked = [utils.remove_prefix(self.PREFIX, name) for name in self._locked]
        return key_set_name in locked

    # === Update === #

    # noinspection PyMethodMayBeStatic
    def hotkeys_installed(self) -> bool:
        """Whether tp-dcc framework hotkeys are installed.

        Returns:
            `True` if the default key sets are installed; `False` otherwise.
        """

        return host.current_host().host.hotkey_set_exists(constants.DEFAULT_KEYSET)

    def hotkeys_version(self) -> tuple[int, int]:
        """Get the version of the currently installed hotkeys.

        Returns:
            A tuple containing the major and minor version of the installed hotkeys.
            If no hotkeys are installed, returns (0, 0).
        """

        try:
            # noinspection PyTypeChecker
            return tuple(
                jsonio.read_file(os.path.join(self._hotkey_user_path, "version"))
            )
        except IOError:
            return -1, 0

    def hotkeys_version_str(self) -> str:
        """Get the version of the currently installed hotkeys as a string.

        Returns:
            The version of the installed hotkeys as a string in the format "major.minor".
            If no hotkeys are installed, returns "0.0".
        """

        version = self.hotkeys_version()
        if version == (-1, 0):
            return "0.0"

        return f"{version[0]}.{version[1]}"

    def save_version(self):
        """Save the current version of the hotkeys to a file in the user
        preferences directory.
        """

        # noinspection PyTypeChecker
        jsonio.write_to_file(
            list(self.VERSION),
            os.path.join(self._hotkey_user_path, "version"),
        )

    def copy_to_user_prefs(self):
        """Copy the default key sets to the user preferences directory.

        Notes:
            Files will not be overwritten if they already exist.
        """

        files_to_copy = (
            (self._default_key_set_path_user, self._default_key_set_path),
            (self._host_key_set_path_user, self._host_key_set_path),
            (self._new_key_set_template_path_user, self._new_key_set_template_path),
        )

        for user_path, original_path in files_to_copy:
            utils.copy_file(user_path, original_path, constants.KEYSET_EXTENSION)
        for user_path, original_path in files_to_copy[:-1]:
            utils.copy_file(user_path, original_path, constants.KEYSET_HOTKEY_EXTENSION)

    def update_defaults(self, force: bool = False):
        """Update the local hotkeys with the internal defaults if versions differ."""

        if not self.hotkeys_installed() and not force:
            logger.info("Hotkeys not installed, ignoring.")
            return

        if self.hotkeys_version() < self.VERSION or force:
            keyset = host.current_host().host.current_hotkey_set_name()
            self.delete_defaults()
            self.install_hotkeys()
            self.save_hotkeys(save_over_defaults=True)
            host.current_host().host.set_current_hotkey_set(keyset)
            logger.info(
                f"Hotkey sets are out of date. Updating to {self.hotkeys_version_str()}"
            )
            self.save_version()

    # === Defaults === #

    def default_key_sets(self) -> list[KeySet]:
        """Get the default key sets.

        Returns:
            List of default `KeySet` instances.
        """

        return self.key_sets_by_name(self._locked)

    def delete_defaults(self, delete_host: bool = True):
        """Delete the default key sets.

        Args:
            delete_host: Whether to delete the host key set. Usually this
                involves deleting the hotkey internally within the current DCC
                session (not from disk).
        """

        for key_set in self.default_key_sets():
            key_set.delete(delete_host=delete_host)

    def set_all_reverts(self):
        """Set all the key sets as reverts."""

        self._reverts.clear()

        for key_set in self._key_sets:
            key_set = self._create_keyset(key_set=key_set)
            self._reverts.append(key_set)

    def revert_to_defaults(self, force: bool = False):
        self.delete_defaults(delete_host=False)
        self.copy_to_user_prefs()

        self._default_key_set = self._create_keyset(
            json_path=f"{self._default_key_set_path_user}{constants.KEYSET_EXTENSION}"
        )
        self._host_key_set = self._create_keyset(
            json_path=f"{self._host_key_set_path_user}{constants.KEYSET_EXTENSION}"
        )
        self._new_key_set_template = self._create_keyset(
            json_path=f"{self._new_key_set_template_path_user}{constants.KEYSET_EXTENSION}"
        )
        self._key_sets.clear()
        self._reverts.clear()

        self._read_key_sets()
        self.update_defaults(force=force)

    def _read_key_sets(self):
        """Read the folder where the key sets are stored and loads them
        into memory.
        """

        user_key_set_paths: list[str] = []
        for file_path in glob.glob(
            f"{self._hotkey_user_path}/*{constants.KEYSET_EXTENSION}"
        ):
            if os.path.basename(file_path).startswith(self.PREFIX):
                user_key_set_paths.append(file_path)

        self._key_sets = [self._host_key_set, self._default_key_set]

        for user_key_set_path in user_key_set_paths:
            key_set = self._create_keyset(json_path=user_key_set_path)
            self._key_sets.append(key_set)

        self.set_all_reverts()
