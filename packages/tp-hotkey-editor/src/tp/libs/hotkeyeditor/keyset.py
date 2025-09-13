from __future__ import annotations

import copy
import os
import time
import glob
import stat
import typing
import weakref
from typing import Any
from abc import ABC, abstractmethod

from loguru import logger

from tp.core import host
from tp.libs.python import yamlio

from . import constants, utils
from .hotkey import Hotkey, HotkeyCommandType, HotkeyCommandData, HotkeyCommand

if typing.TYPE_CHECKING:
    from .keysets import KeySetsManager


class KeySet(ABC):
    """Abstract base class for a key set."""

    def __init__(
        self,
        manager: KeySetsManager,
        json_path: str = "",
        name: str = "",
        source: str = "",
    ):
        super().__init__()

        self._manager = weakref.ref(manager)
        self._name = name
        self._source = source
        self._file_path = json_path
        self._hotkeys: list[Hotkey] = []
        self._read_only = False
        self._modified = False

        self._hotkey_commands: list[HotkeyCommand] = []
        self._runtime_commands: list[HotkeyCommand] = []
        self._name_commands: list[HotkeyCommand] = []
        self._hotkey_context_commands: list[HotkeyCommand] = []

        if json_path and os.path.isfile(json_path):
            self.update_from_file(json_path)
            self.sort()
            self._name = utils.get_file_name(self._file_path)

    @property
    def name(self) -> str:
        """The name of the key set."""

        return self._name

    @property
    def source(self) -> str:
        """The source of the key set."""

        return self._source

    @property
    def file_path(self) -> str:
        """The file path of the key set."""

        return self._file_path

    @property
    def manager(self) -> KeySetsManager:
        """The manager of the key set.

        Raises:
            RuntimeError: If the manager reference is no longer valid.
        """

        manager = self._manager()
        if not manager:
            raise RuntimeError("The KeySetsManager reference is no longer valid.")

        return manager

    @abstractmethod
    def delete_from_host(self) -> bool:
        """Remove keyset from host application.

        Returns:
            `True` if the keyset was successfully removed; `False` otherwise.
        """

        raise NotImplementedError

    @classmethod
    def from_key_set(cls, key_set: KeySet) -> KeySet:
        """Create a new instance of the keyset from another keyset.

        Args:
            key_set: The keyset to copy.

        Returns:
            A new instance of the keyset.
        """

        key_set = cls(manager=key_set.manager)
        key_set.__dict__ = copy.deepcopy(key_set.__dict__)

        return key_set

    @staticmethod
    def to_nice_name(key_set_name: str, suffix: str = "[TP]") -> str:
        """Convert a keyset name to a nice name.

        Args:
            key_set_name: The keyset name to convert.
            suffix: Suffix to append to the nice name.

        Returns:
            The nice name.
        """

        if not key_set_name:
            return ""

        if "tp_user_" in key_set_name.lower():
            return key_set_name.lower().replace("tp_user_", "") + " " + suffix

        return key_set_name

    @staticmethod
    def to_key_set_name(nice_name: str, suffix: str = "[TP]") -> str:
        """Convert a nice name to a keyset name.

        Args:
            nice_name: The nice name to convert.
            suffix: Suffix to remove from the nice name.

        Returns:
            The keyset name.
        """

        if suffix in nice_name:
            text = nice_name.replace(" " + suffix, "")
            text = "tp_user_" + text
            return text

        return nice_name

    def exists(self) -> bool:
        """Check if the keyset exists in the host application.

        Returns:
            `True` if the keyset exists; `False` otherwise.
        """

        return host.current_host().host.hotkey_set_exists(self._name)

    def update_from_file(self, yaml_file_path: str):
        """Update the keyset from a JSON file.

        Args:
            yaml_file_path: The path to the JSON file.
        """

        loaded_commands = yamlio.read_file(yaml_file_path)
        self._file_path = yaml_file_path
        self.setup_commands(loaded_commands)

    def setup_commands(self, commands: list[dict[str, Any]]):
        hotkey_set: dict[str, Any] | None = None

        for command in commands:
            data = HotkeyCommandData(**command)
            cmd = HotkeyCommand(data)
            if data.cmd_type == HotkeyCommandType.Hotkey:
                self._hotkey_commands.append(cmd)
            elif data.cmd_type == HotkeyCommandType.NameCommand:
                self._name_commands.append(cmd)
            elif data.cmd_type == HotkeyCommandType.RuntimeCommand:
                self._runtime_commands.append(cmd)
            elif data.cmd_type == HotkeyCommandType.HotkeyContext:
                self._hotkey_context_commands.append(cmd)
            elif data.cmd_type == HotkeyCommandType.HotkeySet:
                hotkey_set = command
            else:
                logger.warning(f"Unknown command type: {data.cmd_type}")

        try:
            self._source = hotkey_set["source"]
        except TypeError:
            logger.warning(
                "No hotkey set command found in the commands. YAML may be empty or corrupted!"
            )

        self.setup_hotkeys()

    def setup_hotkeys(
        self,
        hotkey_commands: list[HotkeyCommand] | None = None,
        name_commands: list[HotkeyCommand] | None = None,
        runtime_commands: list[HotkeyCommand] | None = None,
        hotkey_context_commands: list[HotkeyCommand] | None = None,
    ):
        """Set up the hotkeys from the hotkey commands.

        Args:
            hotkey_commands: The list of hotkey commands to set up. If `None`,
            use the existing hotkey commands.
        """

        hotkey_commands = hotkey_commands or self._hotkey_commands
        name_commands = name_commands or self._name_commands
        runtime_commands = runtime_commands or self._runtime_commands
        hotkey_context_commands = (
            hotkey_context_commands or self._hotkey_context_commands
        )

        for cmd in hotkey_commands:
            hotkey = Hotkey(command=cmd)
            self._hotkeys.append(hotkey)

    def sort(self):
        """Sort the hotkeys by their pretty name and then by their command
        name.
        """

        if not self._hotkeys:
            return

        self._hotkeys.sort(
            key=lambda hk: (
                hk.get_pretty_name() == "",
                hk.name_command.casefold(),
            )
        )

    def delete_yaml_files(self) -> bool:
        """Delete the JSON file associated with this keyset.

        Returns:
            `True` if the file was successfully deleted; `False` otherwise.
        """

        file_path = os.path.join(
            self.manager.hotkey_user_path,
            f"{self.name}{constants.KEYSET_EXTENSION}",
        )

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return False

        # Ensure the file is writable (Windows read-only files raise
        # `PermissionError` on `unlink`)
        # noinspection PyBroadException
        try:
            os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
        except Exception:
            pass

        # Retry a few times to handle transient locks
        for attempt in range(3):
            try:
                os.remove(file_path)
                return True
            except PermissionError:
                # Clear read-only again and wait a bit in case the file is
                # locked by another process.
                # noinspection PyBroadException
                try:
                    os.chmod(file_path, stat.S_IWRITE | stat.S_IREAD)
                except Exception:
                    pass
                time.sleep(0.2 * (attempt + 1))
            except FileNotFoundError:
                return False
            except IsADirectoryError:
                return False
            except OSError:
                # Could be locked; short backoff and retry.
                time.sleep(0.2 * (attempt + 1))

        return False

    def delete_hotkey_set_files(self) -> bool:
        """Delete all files associated with this keyset.

        Returns:
            `True` if all files were successfully deleted; `False` otherwise.
        """

        mhk_file_path = os.path.join(
            self.manager.hotkey_user_path,
            f"{self.name}{constants.KEYSET_HOTKEY_EXTENSION}",
        )
        if not os.path.isfile(mhk_file_path):
            return False

        files = glob.glob(mhk_file_path)
        for file in files:
            os.remove(file)

        return True

    def install(self, override: bool = True) -> bool:
        """Install the keyset into the host application.

        Returns:
            `True` if the keyset was successfully installed; `False` otherwise.
        """

        logger.info(f"Installing keyset: {self._name} (override={override})")

        if override and self.exists():
            host.current_host().host.delete_key_set(self._name)

        if self.exists():
            return False

        try:
            host.current_host().host.set_source_key_set(self._name, self._source)
        except RuntimeError:
            logger.warning(
                f"Hotkey Set missing source, defaulting to "
                f"{constants.DEFAULT_KEYSET}, Please Save!. "
                f"KeySet {self._name}, oldSource: {self._source}"
            )
            logger.debug(
                f"Creating hotkey set: {self._name} with default source "
                f"because current source({self._source}) no longer exists"
            )
            host.current_host().host.set_source_key_set(
                self._name, constants.DEFAULT_KEYSET
            )

        for command in self._runtime_commands:
            command.run()

        for command in self._name_commands:
            command.run()

        for command in self._hotkey_commands:
            command.run()

        for command in self._hotkey_context_commands:
            command.run()

        logger.info(f"Keyset '{self._name}' installed successfully.")

        return True

    def save(self):
        """Save the keyset to its JSON file."""

    def delete(self, delete_host: bool = True) -> bool:
        """Delete the keyset from the host and remove associated files.

        Returns:
            `True` if the keyset was successfully deleted; `False` otherwise.
        """

        if delete_host:
            if not self.delete_from_host():
                logger.error(f"Failed to delete keyset '{self.name}' from host.")
                return False

        if not self.delete_yaml_files():
            logger.error(f"Failed to delete JSON file for keyset '{self.name}'.")
            return False

        if not self.delete_hotkey_set_files():
            logger.error(f"Failed to delete hotkey set files for '{self.name}'.")
            return False

        return True
