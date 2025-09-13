from __future__ import annotations

from enum import Enum
from dataclasses import dataclass

from loguru import logger

from tp.libs.python import strings

from . import utils


class HotKeyEvent(str, Enum):
    Press = "press"
    Release = "release"


class HotkeyCommandType(str, Enum):
    Hotkey = "hotkey"
    NameCommand = "nameCommand"
    RuntimeCommand = "runTimeCommand"
    HotkeyContext = "hotkeyCtx"
    HotkeySet = "hotkeySet"


@dataclass
class HotkeyCommandData:
    cmd_type: HotkeyCommandType | None = None
    name: str = ""
    release_name: str = ""
    key_shortcut: str = ""
    ctrl: bool = False
    shift: bool = False
    alt: bool = False
    cmd: bool = False


@dataclass
class HotkeyCommands:
    hotkey_command: HotkeyCommand | None = None
    name_command: HotkeyCommand | None = None
    runtime_command: HotkeyCommand | None = None
    hotkey_context_command: HotkeyCommand | None = None


class HotkeyCommand:
    def __init__(self, data: HotkeyCommandData | None = None):
        super().__init__()

        self._command_data = data

    @property
    def data(self) -> HotkeyCommandData | None:
        return self._command_data

    def get_key(self, key: str) -> bool:
        """Returns the value of the given key from the command data.

        Args:
            key: The key to get the value for.

        Returns:
            The value of the key, or `False` if the key does not exist or
            data is `None`.
        """

        if not self.data:
            return False

        return getattr(self.data, key, False)

    def run(self):
        if self.data.cmd_type == HotkeyCommandType.Hotkey:
            alt = self.get_key("alt")
            ctrl = self.get_key("ctrl")
            shift = self.get_key("shift")
            cmd = self.get_key("cmd")
            name: str | None = None
            release_name: str | None = None
            if self.data.name:
                name = self.data.name
            elif self.data.release_name:
                release_name = self.data.release_name

    def command_hotkey(
        self,
        key_shortcut: str,
        name: str | None = None,
        release_name: str | None = None,
        auto_save: int = 0,
        context_client: str = "",
    ):
        name = utils.remove_brackets(name)
        release_name = utils.remove_brackets(release_name)


class Hotkey:
    MODIFIERS = ["ctrl", "shift", "alt", "cmd"]

    def __init__(self, command: HotkeyCommand | None = None):
        super().__init__()

        self._name = ""
        self._release_name = ""
        self._pretty_name = ""
        self._name_command = ""
        self._runtime_command = ""
        self._category = ""
        self._language = ""
        self._key_shortcut = ""
        self._annotation = ""
        self._context_client = ""
        self._key_event: HotKeyEvent | None = None
        self._modified = False

        self._hotkey_commands = HotkeyCommands()
        self._modifiers = {modifier: False for modifier in Hotkey.MODIFIERS}

        if command:
            self.set_hotkey_command(command)

    @property
    def name(self) -> str:
        """The name of the hotkey."""

        return self._name

    @property
    def release_name(self) -> str:
        """The release name of the hotkey."""

        return self._release_name

    @property
    def name_command(self) -> str:
        """The name command of the hotkey."""

        return self._name_command

    def get_pretty_name(self) -> str:
        """Returns a pretty name for the hotkey.

        Returns:
            The pretty name of the hotkey.
        """

        return self._pretty_name

    def set_pretty_name(self, suffix: bool = True):
        """Sets a pretty name for the hotkey.

        Args:
            suffix: Whether to add a suffix to the name or not.
        """

        pretty_name = self._name_command

        name_command_str = "NameCommand"
        if pretty_name.endswith(name_command_str):
            pretty_name = pretty_name[0 : -len(name_command_str)]

        self._pretty_name = strings.camel_case_to_spaces(pretty_name)

        if suffix and self._pretty_name.strip() != "":
            name_suffix = ""
            if self._key_event == HotKeyEvent.Press:
                name_suffix = " [PRESS]"
            elif self._key_event == HotKeyEvent.Release:
                name_suffix = " [RELEASE]"
            self._pretty_name += " " + name_suffix

    def set_hotkey_command(self, hotkey_command: HotkeyCommand):
        """Set the hotkey command.

        Args:
            hotkey_command: The hotkey command to set.
        """

        self._hotkey_commands.hotkey_command = hotkey_command

        if hotkey_command.data.name:
            self._name = hotkey_command.data.name
            self._key_event = HotKeyEvent.Press
        elif hotkey_command.data.release_name:
            self._release_name = hotkey_command.data.release_name
            self._key_event = HotKeyEvent.Release

        if self._name:
            self._name_command = self._name
        elif self._release_name:
            self._name_command = self._release_name
        else:
            logger.warning(
                f"Hotkey name command not found! {hotkey_command} "
                f">>> {hotkey_command.data} "
            )

        self.set_pretty_name()

        self._key_shortcut = hotkey_command.data.key_shortcut
        self._runtime_command = ""

        self.set_modifiers(hotkey_command)

    def set_modifiers(self, hotkey_command: HotkeyCommand):
        """Sets the modifier keys for the hotkey.

        Args:
            hotkey_command: The hotkey command containing the modifier information.
        """

        for modifier in Hotkey.MODIFIERS:
            self._modifiers[modifier] = getattr(hotkey_command.data, modifier)
