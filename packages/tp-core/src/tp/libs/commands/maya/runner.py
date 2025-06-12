from __future__ import annotations

import sys
import traceback
from typing import cast, Any

from maya import cmds
from loguru import logger
from maya.api import OpenMaya

from tp.libs.python.decorators import Singleton
from tp.libs.commands.stats import CommandStats
from tp.libs.commands.runner import BaseCommandRunner
from tp.libs.commands.maya.command import MayaCommand
from tp.libs.commands.maya import plugin as undocommand
from tp.libs.commands.result import CommandReturnStatus
from tp.libs.commands.errors import UserCancelError, CommandExecutionError


class MayaCommandRunner(BaseCommandRunner, metaclass=Singleton):
    """Maya Command runner implementation that allows to inject DCC commands
    into the Maya undo stack.
    """

    def __init__(self):
        super().__init__(interface=MayaCommand)

        undocommand.install()

    def run(self, command_id: str, **kwargs: dict) -> Any:
        """Overrides `run` method to add support for Maya specific commands.

        Args:
            command_id: ID of the command to run.
            **kwargs: keyword arguments to run the command with.

        Returns:
            Command run result.

        Raises:
            ValueError: If the command with the given ID is not found.
            UserCancelError: If the command is canceled by the user.
            Exception: If the command fails to run.
            CommandExecutionError: If the command fails to run.
        """

        logger.debug(f'Executing command: "{command_id}"')

        command_to_run = cast(MayaCommand, self.find_command(command_id))
        if command_to_run is None:
            raise ValueError(
                f'No command found with given id "{command_id}".\n\n'
                f"Available commands: {self._manager.plugin_ids}"
            )

        # noinspection PyCallingNonCallable
        command_to_run: MayaCommand = command_to_run()
        if not command_to_run.is_enabled:
            return None

        try:
            command_to_run.parse_arguments(kwargs)
            if command_to_run.requires_warning():
                logger.warning(command_to_run.warning_message())
                return None
        except UserCancelError:
            return None
        except Exception:
            raise

        exc_tb, exc_type, exc_value = None, None, None
        command_to_run.stats = CommandStats(command_to_run)
        try:
            if command_to_run.is_undoable and command_to_run.use_undo_chunk:
                cmds.undoInfo(openChunk=True, chunkName=command_to_run.id)
            OpenMaya._TP_DCC_COMMAND = command_to_run
            # noinspection PyUnresolvedReferences
            getattr(cmds, undocommand.UndoCommand.COMMAND_NAME)(id=command_to_run.id)
            if command_to_run.return_status == CommandReturnStatus.Error:
                exc_type, exc_value, exc_tb = sys.exc_info()
                message = f'Command "{command_id}" failed to run.'
                raise CommandExecutionError(message)
            return command_to_run.return_result
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            if command_to_run.is_undoable and command_to_run.use_undo_chunk:
                cmds.undoInfo(closeChunk=True, chunkName=command_to_run.id)
            command_to_run.stats.finish(tb)
            logger.debug(f'Finished executing command: "{command_id}"')

    def flush(self):
        """Overrides `flush` method to flush the Maya undo stack."""

        super().flush()

        cmds.flushUndo()
