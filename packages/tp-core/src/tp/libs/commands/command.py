from __future__ import annotations

import inspect
from typing import Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

from .stats import CommandStats
from .errors import UserCancelError
from .result import CommandReturnStatus


@dataclass
class CommandData:
    """Data class that holds command data."""

    # Command ID.
    id: str

    # Name of the command.
    name: str

    # Command tooltip.
    tooltip: str

    # Command documentation URL.
    documentation: str

    # File path where the command is defined.
    file_path: str

    # Icon path for the command.
    icon: str

    # Media file path for the tooltip to use.
    tooltip_media: str

    # Command settings command.
    settings_command: str

    # Command categories.
    categories: list[str]

    # Command sub commands.
    sub_commands: list[CommandData]

    @classmethod
    def from_dict(cls, data: dict) -> CommandData:
        """Creates a CommandData instance from the given dictionary.

        Args:
            data: dictionary to create the CommandData instance from.

        Returns:
            CommandData instance created from the given dictionary.
        """

        return cls(
            id=data.get("id"),
            name=data.get("name"),
            tooltip=data.get("tooltip"),
            documentation=data.get("documentation"),
            file_path=data.get("file_path"),
            icon=data.get("icon"),
            tooltip_media=data.get("tooltip_media"),
            settings_command=data.get("settings_command"),
            categories=data.get("categories", []),
            sub_commands=[cls.from_dict(sub) for sub in data.get("sub_commands", [])],
        )


class AbstractCommand(ABC):
    """Abstract command metaclass interface."""

    # Whether the command is enabled or not.
    is_enabled = True

    def __init__(self, stats: CommandStats | None = None):
        """Args:
        stats: command stats.
        """

        self._stats = stats
        self._arguments = CommandArgumentParser()
        self._return_result: Any = None
        self._warning: str = ""
        self._errors: str = ""
        self._return_status: CommandReturnStatus = CommandReturnStatus.Success

        self.initialize()

    @property
    @abstractmethod
    def id(self) -> str:
        """The command ID."""

    @property
    def is_undoable(self) -> bool:
        """Whether the command is undoable or not."""

        return False

    @property
    def stats(self) -> CommandStats | None:
        """The command stats."""

        return self._stats

    @stats.setter
    def stats(self, value: CommandStats):
        """Sets the command stats."""

        self._stats = value

    @property
    def arguments(self) -> CommandArgumentParser:
        """The command arguments."""

        return self._arguments

    @property
    def return_result(self) -> Any:
        """The command return result."""

        return self._return_result

    @return_result.setter
    def return_result(self, value: Any):
        """Sets the command return result."""

        self._return_result = value

    @property
    def return_status(self) -> CommandReturnStatus:
        """The command return status."""

        return self._return_status

    @return_status.setter
    def return_status(self, value: CommandReturnStatus):
        """Sets the command return status."""

        self._return_status = value

    @property
    def errors(self) -> str:
        """The command errors."""

        return self._errors

    @errors.setter
    def errors(self, value: str):
        """Sets the command errors."""

        self._errors = value

    def initialize(self):
        """Function intended to be used as a replacement for the code that
        should be initialized within __init__ function.

        This function can be overridden by subclasses.
        """

        self.prepare_command()

    @abstractmethod
    def do(self, **kwargs: dict) -> Any:
        """Executes the command functionality.

        Args:
            **kwargs: keyword arguments to pass to the command function.

        Notes:
            This function only supports keyword arguments, so every
            argument MUST have a default value.

        Returns:
            Command run result.
        """

        raise NotImplementedError("do function must be implemented in derived classes.")

    def description(self) -> str:
        """Returns the description of the command. Class doc is used by default.

        Returns:
            Command description.
        """

        return self.__doc__

    def undo(self):
        """If the command is undoable, this function is call to reverse the
        operation done by run function.
        """

        pass

    def run(self) -> Any:
        """Run the `do` function with the current arguments.

        Returns:
            Command run result.
        """

        return self.do(**self._arguments)

    def run_arguments(self, **arguments) -> Any:
        """Run `do function with given arguments.

        Args:
            **arguments: key, value pairs corresponding to arguments for the
                `do` function.

        Returns:
            Command run result.
        """

        self.parse_arguments(arguments)
        return self.run()

    def has_argument(self, name: str) -> bool:
        """Return whether this command supports the given argument.

        Args:
            name: Argument name to check.

        Returns:
            True if command supports given arguments; False otherwise.
        """

        return name in self._arguments

    def parse_arguments(self, arguments: dict) -> bool:
        """Parses given arguments, so they are ready to be passed to the command
         `do` function.

        Args:
            arguments: arguments as dictionary.

        Returns:
            True if the parse operation was successful; False otherwise.
        """

        kwargs = self._arguments
        kwargs.update(arguments)
        result = self.resolve_arguments(CommandArgumentParser(**kwargs)) or {}
        kwargs.update(result)

        return True

    # noinspection PyMethodMayBeStatic
    def resolve_arguments(self, arguments: dict) -> dict | None:
        """Function that is called before running the command.

        Notes:
            Useful to validate incoming command arguments before executing
            the command.

        Args:
            arguments: Dictionary with the same key value pairs as the
                arguments param.

        Returns:
            Dictionary with the same key value pairs as the arguments param.
        """

        return arguments

    def prepare_command(self) -> CommandArgumentParser:
        """Prepare the command so it can be executed.

        Returns:
            `CommandArgumentParser` instance with the command arguments.
        """

        func_args = inspect.getfullargspec(self.run)
        args = func_args.args[1:]
        defaults = func_args.defaults or tuple()
        if len(args) != len(defaults):
            raise ValueError(
                f"Command run function({self.id}) must only use keyword arguments."
            )
        elif args and defaults:
            arguments = CommandArgumentParser(zip(args, defaults))
            self._arguments = arguments
            return arguments

        return CommandArgumentParser()

    def requires_warning(self) -> bool:
        """Return whether this command requires warning.

        Returns:
            True if command requires warning; False otherwise.
        """

        return True if self._warning else False

    def warning_message(self) -> str:
        """Return command warning message.

        Returns:
            command warning message.
        """

        return self._warning

    def display_warning(self, message: str):
        """Set the display warning message to show.

        Args:
            message: The warning message to show.
        """

        self._warning = message

    def cancel(self, msg: str | None = None):
        """Raise user cancel error.

        Args:
            msg: Optional message to show.

        Raises:
            UserCancelError: When cancelling command execution.
        """

        raise UserCancelError(msg)


class CommandArgumentParser(dict):
    """Argument parser class that allows to parse command arguments."""

    def __getattr__(self, item: str) -> Any:
        """Return the value of the given item.

        Args:
            item: Item to get value from.

        Returns:
            Value of the given item.
        """

        result = self.get(item)
        if result:
            return result

        return super().__getattribute__(item)
