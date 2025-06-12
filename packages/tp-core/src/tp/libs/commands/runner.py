from __future__ import annotations

import sys
import typing
import inspect
import traceback
from typing import cast, Type, Any

from loguru import logger

from .. import dcc
from ..plugin import PluginsManager

from .stats import CommandStats
from .errors import UserCancelError
from .result import CommandReturnStatus

if typing.TYPE_CHECKING:
    from .command import AbstractCommand


def execute(command_id: str, **kwargs) -> Any:
    """Executes given DCC command with given ID.

    Args:
        command_id: DCC command ID to execute.
        **kwargs: keyword arguments for the command execution.

    Returns:
        DCC command result.
    """

    # noinspection PyUnresolvedReferences
    return CommandRunner().run(command_id, **kwargs)


class MetaCommandRunner(type):
    """Command runner singleton class that returns runner class based on
    the current active DCC.
    """

    _instance = None

    def __call__(cls, *args, **kwargs):
        if cls._instance is None:
            if dcc.is_maya():
                from ..commands.maya.runner import MayaCommandRunner

                cls._instance = type.__call__(MayaCommandRunner, *args, **kwargs)
            elif dcc.is_unreal():
                from ..commands.unreal.runner import UnrealCommandRunner

                cls._instance = type.__call__(UnrealCommandRunner, *args, **kwargs)
            else:
                cls._instance = type.__call__(BaseCommandRunner, *args, **kwargs)

        return cls._instance


class CommandRunner(metaclass=MetaCommandRunner):
    """Command runner class"""

    pass


class BaseCommandRunner:
    def __init__(
        self,
        interface: Type[AbstractCommand],
        register_env: str = "TP_DCC_COMMAND_PATHS",
    ):
        interface = interface
        self._manager = PluginsManager(
            [interface], variable_name="id", name="tpCommandQueue"
        )
        self._manager.register_by_environment_variable(register_env)

    def commands(self) -> list[type[AbstractCommand]]:
        """Return all registered commands.

        Returns:
            List of registered commands.
        """

        return cast(list[type[AbstractCommand]], self._manager.plugin_classes)

    def manager(self) -> PluginsManager:
        """Return the command manager.

        Returns:
            Command manager instance.
        """

        return self._manager

    def run(self, command_id: str, **kwargs: dict) -> Any:
        """Run the command with the given ID.

        Args:
            command_id: ID of the command to run.
            ** kwargs: Keyword arguments for the command execution.

        Returns:
            Command Run result.

        Raises:
            ValueError: If the command with the given ID is not found.
            UserCancelError: If command execution is canceled by the user.
        """

        command_to_run = self.find_command(command_id)
        if not command_to_run:
            msg = f'No command found with given id "{command_id}"'
            msg += f"\nAvailable commands: {', '.join(self._manager.plugin_ids)}"
            raise ValueError(msg)

        command_to_run = command_to_run()
        if not command_to_run.is_enabled:
            return None
        try:
            command_to_run.parse_arguments(kwargs)
            if command_to_run.requires_warning():
                logger.warning(command_to_run.warning_message())
                return None
        except UserCancelError:
            raise
        except Exception:
            raise

        exc_tb, exc_type, exc_value = None, None, None
        command_to_run.stats = CommandStats(command_to_run)

        try:
            result = self._run(command_to_run)
            if command_to_run.return_status == CommandReturnStatus.Error:
                exc_type, exc_value, exc_tb = sys.exc_info()
                message = f'Command "{command_id}" failed to execute.'
                raise UserCancelError(message)
        except Exception:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            command_to_run.stats.finish(tb)
            logger.exception(f"Failed to execute command: {command_id}", exc_info=True)
            raise

        tb = None
        if exc_type and exc_value and exc_tb:
            tb = traceback.format_exception(exc_type, exc_value, exc_tb)
        command_to_run.stats.finish(tb)
        logger.debug(f"Finished executing command: {command_id}")

        return result

    def find_command(self, command_id: str) -> Type[AbstractCommand] | None:
        """Return the registered command by its ID.

        Args:
            command_id: ID of the command to find.

        Returns:
            Found command class.
        """

        return self._manager.get_plugin(command_id)

    def command_help(self, command_id: str) -> str:
        """Return the command help of the given command.

        Args:
            command_id: ID of the command to find.

        Returns:
            Command help string.
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
        """Clears the command.

        This function can be re-implemented in subclasses.
        """

        pass

    def cancel(self, msg: str):
        """Cancels command execution.

        Args:
            msg: Cancel message.
        """

        raise UserCancelError(msg)

    # noinspection PyMethodMayBeStatic
    def _run(self, command_to_run: AbstractCommand) -> Any:
        """Internal function that executes the given command.

        Args:
            command_to_run: command to run.

        Returns:
            Command run result.
        """

        result = command_to_run.do(**command_to_run.arguments)
        command_to_run._return_result = result

        return result
