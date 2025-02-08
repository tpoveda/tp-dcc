from __future__ import annotations

import sys
import time
import enum
import inspect
import logging
import traceback
from typing import Type, Any
from collections import deque
from abc import ABC, abstractmethod

from .. import dcc
from .. import plugin
from ..python import osplatform

logger = logging.getLogger(__name__)


class UserCancel(Exception):
    """
    Exception that is raised when user cancels a command.
    """

    def __init__(self, message: str, errors: list[str] | None = None):
        super(UserCancel, self).__init__(message)
        self.errors = errors


class CommandExecutionError(Exception):
    """
    Exception that is raised when a command execution fails.
    """

    def __init__(self, message: str, *args):
        super().__init__(message, *args)


class CommandReturnStatus(enum.Enum):
    """
    Enum that defines the different return statuses for a command.
    """

    SUCCESS = enum.auto()
    ERROR = enum.auto()


def execute(command_id: str, **kwargs) -> Any:
    """
    Executes given DCC command with given ID.

    :param str command_id: DCC command ID to execute.
    :return: DCC command result.
    :rtype: Any
    """

    # noinspection PyUnresolvedReferences
    return CommandRunner().run(command_id, **kwargs)


class ArgumentParser(dict):
    """
    Argument parser class that allows to parse command arguments.
    """

    def __getattr__(self, item: str) -> Any:
        """
        Returns the value of the given item.

        :param item: va
        :return:
        """

        result = self.get(item)
        if result:
            return result

        return super().__getattribute__(item)


class AbstractCommand(ABC):
    """
    Abstract command metaclass interface.
    Each DCC command MUST implement this interface.
    """

    is_enabled = True

    def __init__(self, stats: CommandStats | None = None):
        self._stats = stats
        self._arguments = ArgumentParser()
        self._return_result: Any = None
        self._warning: str = ""
        self._errors: str = ""
        self._return_status: CommandReturnStatus = CommandReturnStatus.SUCCESS

        self.initialize()

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Getter that returns the command ID.

        :return: command ID.
        :rtype: str
        """

        pass

    @property
    @abstractmethod
    def is_undoable(self) -> bool:
        """
        Getter that returns whether the command is undoable or not.

        :return: True if command is undoable; False otherwise.
        :rtype: bool
        """

        return False

    @property
    def stats(self) -> CommandStats | None:
        """
        Getter that returns the command stats.

        :return: command stats.
        """

        return self._stats

    @stats.setter
    def stats(self, value: CommandStats):
        """
        Setter that sets the command stats.

        :param value: Command stats to set.
        """

        self._stats = value

    @property
    def arguments(self) -> ArgumentParser:
        """
        Getter that returns the command arguments.

        :return: command arguments.
        """

        return self._arguments

    @property
    def return_result(self) -> Any:
        """
        Getter that returns the command return result.

        :return: command return result.
        """

        return self._return_result

    @return_result.setter
    def return_result(self, value: Any):
        """
        Setter that sets the command return result.

        :param value: command return result.
        """

        self._return_result = value

    @property
    def return_status(self) -> CommandReturnStatus:
        """
        Getter that returns the command return status.

        :return: command return status.
        """

        return self._return_status

    @return_status.setter
    def return_status(self, value: CommandReturnStatus):
        """
        Setter that sets the command return status.

        :param value: command return status.
        """

        self._return_status = value

    @property
    def errors(self) -> str:
        """
        Getter that returns the command errors.

        :return: command errors.
        """

        return self._errors

    @errors.setter
    def errors(self, value: str):
        """
        Setter that sets the command errors.

        :param value: command errors.
        """

        self._errors = value

    def initialize(self):
        """
        Function that should be overridden by subclasses.
        Intended to be used as a replacement for the code that should be initialized
        within __init__ function.
        """

        self.prepare_command()

    @abstractmethod
    def do(self, **kwargs: dict) -> Any:
        """
        Executes the command functionality. This function only supports keyword
        arguments, so every argument MUST have a default value.

        :param dict kwargs: dictionary with key value pairs. Any kind of type is
            supported (even DCC specific types).
        :return: command run result.
        """

        pass

    def description(self) -> str:
        """
        Returns the description of the command. Class doc is used by default.

        :return: command description.
        :rtype: str
        """

        return self.__doc__

    def undo(self):
        """
        If the command is undoable this function is call to reverse the operation
        done by run function.
        """

        pass

    def run(self) -> Any:
        """
        Runs `do` function with the current arguments.

        :return: command run result.
        """

        return self.do(**self._arguments)

    def run_arguments(self, **arguments) -> Any:
        """
        Runs `do function with given arguments.

        :param arguments: key , value pairs corresponding to arguments for `do` function.
        :return: command run result.
        """

        self.parse_arguments(arguments)
        return self.run()

    def has_argument(self, name: str) -> bool:
        """
        Returns whether this command supports given argument.

        :param str name: argument name.
        :return: True if command supports given arguments; False otherwise.
        """

        return name in self._arguments

    def parse_arguments(self, arguments: dict) -> bool:
        """
        Parses given arguments, so they are ready to be passed to the command
         `do` function.

        :param dict arguments: arguments as dictionary.
        :return: True if the parse operation was successful; False otherwise.
        """

        kwargs = self._arguments
        kwargs.update(arguments)
        result = self.resolve_arguments(ArgumentParser(**kwargs)) or {}
        kwargs.update(result)

        return True

    # noinspection PyMethodMayBeStatic
    def resolve_arguments(self, arguments: dict) -> dict | None:
        """
        Function that is called before running the command. Useful to validate incoming
        command arguments before executing the command.

        :param dict arguments: key, value pairs of commands being passed to the run
            command function
        :return: dictionary with the same key value pairs as the arguments param.
        """

        return arguments

    def prepare_command(self):
        """
        Prepares command so it can be executed.
        """

        func_args = inspect.getfullargspec(self.run)
        args = func_args.args[1:]
        defaults = func_args.defaults or tuple()
        if len(args) != len(defaults):
            raise ValueError(
                f"Command run function({self.id}) must only use keyword arguments."
            )
        elif args and defaults:
            arguments = ArgumentParser(zip(args, defaults))
            self._arguments = arguments
            return arguments

        return ArgumentParser()

    def requires_warning(self) -> bool:
        """
        Returns whether this command requires warning.

        :return: True if command has warning; False otherwise.
        :rtype: bool
        """

        return True if self._warning else False

    def warning_message(self) -> str:
        """
        Returns command warning message.

        :return: warning message.
        :rtype: str
        """

        return self._warning

    def display_warning(self, message: str):
        """
        Sets display warning message to show.

        :param str message: warning message.
        """

        self._warning = message

    def cancel(self, msg: str | None = None):
        """
        Raises user cancel error.

        :param str or None msg: optional message to show.
        :raises exceptions.CommandCancel: when cancelling command execution.
        """

        raise UserCancel(msg)


class CommandStats:
    """
    Command stats class that stores information about the command execution.
    """

    def __init__(self, command: AbstractCommand):
        self._command = command
        self._start_time = 0.0
        self._end_time = 0.0
        self._execution_time = 0.0
        self._info = {}

        self._init()

    @property
    def start_time(self) -> float:
        """
        Getter that returns the command start time.

        :return: command start time.
        """

        return self._start_time

    @start_time.setter
    def start_time(self, value: float):
        """
        Setter that sets the command start time.

        :param value: command start time.
        """

        self._start_time = value

    @property
    def end_time(self) -> float:
        """
        Getter that returns the command end time.

        :return: command end time.
        """

        return self._end_time

    @end_time.setter
    def end_time(self, value: float):
        """
        Setter that sets the command end time.

        :param value: command end time.
        """

        self._end_time = value

    @property
    def execution_time(self) -> float:
        """
        Getter that returns the command execution time.

        :return: command execution time.
        """

        return self._execution_time

    def _init(self):
        """
        Internal function that initializes info for the command and its environment.
        """

        try:
            file_path = inspect.getfile(self._command.__class__)
        except Exception:
            file_path = ""

        self._info.update(
            {
                "name": self._command.__class__.__name__,
                "module": self._command.__class__.__module__,
                "filepath": file_path,
                "id": self._command.id,
                "application": dcc.current_dcc(),
            }
        )
        self._info.update(osplatform.machine_info())

    def finish(self, trace: str | None = None):
        """
        Function that is called when plugin finishes its execution.

        :param trace: optional trace stack.
        """

        self._end_time = time.time()
        self._execution_time = self._end_time - self._start_time
        self._info["executionTime"] = self._execution_time
        self._info["lastUsed"] = self._end_time
        if trace:
            self._info["traceback"] = trace


class BaseCommandRunner:
    def __init__(
        self,
        interface: Type[AbstractCommand],
        register_env: str = "TP_DCC_COMMAND_PATHS",
    ):
        interface = interface
        self._undo_stack: deque[AbstractCommand] = deque()
        self._redo_stack: deque[AbstractCommand] = deque()
        self._manager = plugin.PluginFactory(
            interface, plugin_id="id", name="commandQueue"
        )
        self._manager.register_paths_from_env_var(register_env, package_name="tp-dcc")

    @property
    def undo_stack(self) -> deque:
        """
        Getter that returns the undo stack.

        :return: undo stack.
        """

        return self._undo_stack

    @property
    def redo_stack(self) -> deque:
        """
        Getter that returns the redo stack.

        :return: redo stack.
        """

        return self._redo_stack

    def commands(self) -> list[AbstractCommand]:
        """
        Returns all registered commands.

        :return: list of registered commands.
        """

        return self._manager.plugins()

    def manager(self) -> plugin.PluginFactory:
        """
        Returns the command manager.

        :return: command manager instance.
        """

        return self._manager

    def run(self, command_id: str, **kwargs: dict) -> Any:
        """
        Run the command with given ID.

        :param str command_id: ID of the command to run.
        :param Dict kwargs: keyword arguments for the command execution.
        :return: command run result.
        :rtype: Any
        """

        command_to_run = self.find_command(command_id)
        if not command_to_run:
            raise ValueError(f'No command found with given id "{command_id}"')

        command_to_run = command_to_run(CommandStats(command_to_run))
        if not command_to_run.is_enabled:
            return
        try:
            command_to_run.parse_arguments(kwargs)
            if command_to_run.requires_warning():
                logger.warning(command_to_run.warning_message())
                return
        except UserCancel:
            return
        except Exception:
            raise

        exc_tb, exc_type, exc_value = None, None, None
        result = None
        try:
            result = self._run(command_to_run)
        except UserCancel:
            self._undo_stack.remove(command_to_run)
            command_to_run.stats.finish(None)
            return result
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            elif command_to_run.is_undoable:
                self._undo_stack.append(command_to_run)
            command_to_run.stats.finish(tb)

            return result

    def undo_last(self) -> bool:
        """
        Undoes last executed command.
        :return: True if the undo operation was successful; False otherwise.
        :rtype: bool
        """

        if not self._undo_stack:
            return False

        command_to_undo = self._undo_stack[-1]
        if command_to_undo is not None and command_to_undo.is_undoable:
            command_to_undo.undo()
            self._redo_stack.append(command_to_undo)
            self._undo_stack.remove(command_to_undo)
            return True

        return False

    def redo_last(self) -> Any:
        """
        Redoes last undo command.

        :return: redo command result.
        :rtype: Any
        """

        exc_tb, exc_type, exc_value = None, None, None
        result = None
        if self._redo_stack:
            command_to_redo = self._redo_stack.pop()
            if command_to_redo is not None:
                try:
                    command_to_redo.stats = CommandStats(command_to_redo)
                    result = self._run(command_to_redo)
                except UserCancel:
                    self._undo_stack.remove(command_to_redo)
                    command_to_redo.stats.finish(None)
                    raise
                except Exception:
                    exc_type, exc_value, exc_tb = sys.exc_info()
                    raise
                finally:
                    tb = None
                    if exc_type and exc_value and exc_tb:
                        tb = traceback.format_exception(exc_type, exc_value, exc_tb)
                    elif command_to_redo.is_undoable:
                        self._undo_stack.append(command_to_redo)
                    command_to_redo.stats.finish(tb)

        return result

    def find_command(self, command_id: str) -> Type[AbstractCommand] | None:
        """
        Returns registered command by its ID.

        :param command_id: ID of the command to find.
        :return: found command.
        """

        return self._manager.get_plugin_from_id(command_id)

    def command_help(self, command_id: str) -> str:
        """
        Returns the command help of the given command.

        :param command_id: ID of the command to get help of.
        :return: command help.
        """

        command = self.find_command(command_id)
        if not command:
            return ""

        doc_help = inspect.getdoc(command)
        run_help = inspect.getdoc(command.run)

        return f"""
        Class: {command.__name__}
        {doc_help}
        Run:
        {run_help}
        """

    def flush(self):
        """
        Clears the undo/redo history of the command.
        """

        self._undo_stack.clear()
        self._redo_stack.clear()

    def cancel(self, msg: str):
        """
        Cancels command execution.

        :param str msg: cancel message.
        """

        raise UserCancel(msg)

    def _run(self, command_to_run: AbstractCommand) -> Any:
        """
        Internal function that executes given command.

        :param DccCommand command_to_run: command to run.
        :return: command run result.
        :rtype: Any
        """

        result = command_to_run.do(**command_to_run.arguments)
        command_to_run._return_result = result

        return result


class MetaCommandRunner(type):
    """
    Command runner singleton class that returns runner class based on current DCC.
    """

    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            if dcc.is_maya():
                from tp.maya.command import MayaCommandRunner

                print("gogogogo maya")

                cls._instance = type.__call__(MayaCommandRunner, *args, **kwargs)
            else:
                cls._instance = type.__call__(BaseCommandRunner, *args, **kwargs)

        return cls._instance


class CommandRunner(metaclass=MetaCommandRunner):
    """
    Command runner class
    """

    pass
