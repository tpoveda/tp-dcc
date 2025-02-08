from __future__ import annotations

import sys
import logging
import traceback
from typing import Any

from maya import cmds
from maya.api import OpenMaya

from ..python.decorators import Singleton
from ..core.command import (
    UserCancel,
    CommandExecutionError,
    CommandReturnStatus,
    AbstractCommand,
    CommandStats,
    BaseCommandRunner,
)
from .plugins import undocommand

logger = logging.getLogger(__name__)


class MayaCommand(AbstractCommand):
    is_enabled = True
    use_undo_chunk = True  # whether to chunk all operations in `do`
    disable_queue = False  # whether to disable the undo queue in `do`

    @staticmethod
    def disable_undo_queue(flag: bool):
        """
        Enables/Disables the Maya undo queue.

        :param flag: whether to disable the undo queue.
        """

        cmds.undoInfo(stateWithoutFlush=not flag)

    @staticmethod
    def is_queue_disabled():
        """
        Returns whether the Maya undo queue is disabled or not.

        :return: bool
        """

        return not cmds.undoInfo(query=True, stateWithoutFlush=True)

    def run_arguments(self, **arguments) -> Any:
        """
        Overrides `run_arguments` method to add support for Maya specific arguments.

        :param arguments: arguments to run the command with.
        :return: command run result.
        :raises UserCancel: If the command is cancelled by the user.
        :raises Exception: If the command fails to run.
        """

        original_state = self.is_queue_disabled()
        self.disable_undo_queue(self.disable_queue)
        try:
            self.parse_arguments(arguments)
            result = self.run()
        except UserCancel:
            raise
        except Exception:
            raise
        finally:
            self.disable_undo_queue(original_state)

        return result


class MayaCommandRunner(BaseCommandRunner, metaclass=Singleton):
    """
    Maya Command runner implementation that allows to inject DCC commands into the
    Maya undo stack.
    """

    def __init__(self):
        super().__init__(interface=MayaCommand)

        undocommand.install()

    def run(self, command_id: str, **kwargs: dict) -> Any:
        """
        Overrides `run` method to add support for Maya specific commands.

        :param command_id: ID of the command to run.
        :param kwargs: keyword arguments to run the command with.
        :return: command run result.
        :raises ValueError: If the command with the given ID is not found.
        :raises UserCancel: If the command is cancelled by the user.
        :raises Exception: If the command fails to run.
        :raises CommandExecutionError: If the command fails to run.
        """

        logger.debug(f'Executing command: "{command_id}"')

        command_to_run = self.find_command(command_id)
        if command_to_run is None:
            raise ValueError(f'No command found with given id "{command_id}"')

        # noinspection PyCallingNonCallable
        command_to_run: MayaCommand = command_to_run()
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
        command_to_run.stats = CommandStats(command_to_run)
        try:
            if command_to_run.is_undoable and command_to_run.use_undo_chunk:
                cmds.undoInfo(openChunk=True, chunkName=command_to_run.id)
                self._undo_stack.append(command_to_run)
            OpenMaya._TPDCC_COMMAND = command_to_run
            # noinspection PyUnresolvedReferences
            getattr(cmds, undocommand.UndoCommand.COMMAND_NAME)(id=command_to_run.id)
            if command_to_run.return_status == CommandReturnStatus.ERROR:
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

    def undo_last(self) -> bool:
        """
        Undoes the last command in the undo stack.
        """

        if not self._undo_stack:
            return False

        command_to_undo = self._undo_stack[-1]
        if command_to_undo is None or not command_to_undo.is_undoable:
            return False

        exc_tb, exc_type, exc_value = None, None, None
        try:
            command_to_undo.stats = CommandStats(command_to_undo)
            cmds.undo()
        except UserCancel:
            command_to_undo.stats.finish(None)
            return False
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            elif command_to_undo.is_undoable:
                self._undo_stack.remove(command_to_undo)
            self._redo_stack.append(command_to_undo)
            command_to_undo.stats.finish(tb)

        return True

    def redo_last(self) -> Any:
        """
        Redoes the last command in the redo stack.
        """

        if not self._redo_stack:
            return

        result = None
        command_to_redo = self._redo_stack[-1]
        if command_to_redo is None:
            return result

        exc_tb, exc_type, exc_value = None, None, None
        try:
            command_to_redo.stats = CommandStats(command_to_redo)
            cmds.redo()
        except UserCancel:
            command_to_redo.stats.finish(None)
            return
        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            raise
        finally:
            tb = None
            command_to_redo = self._redo_stack.pop()
            if exc_type and exc_value and exc_tb:
                tb = traceback.format_exception(exc_type, exc_value, exc_tb)
            elif command_to_redo.is_undoable:
                self._undo_stack.append(command_to_redo)
            command_to_redo.stats.finish(tb)

        return result

    def flush(self):
        super().flush()
        cmds.flushUndo()

    def _run(self, command_to_run: MayaCommand) -> Any:
        """
        Overrides `_run` method to add support for Maya specific commands.

        :param command_to_run: command to run.
        :return:
        """

        if OpenMaya.MGlobal.isRedoing():
            if self._redo_stack:
                self._redo_stack.pop()
            result = super()._run(command_to_run)
            self._undo_stack.append(command_to_run)
            return result
        try:
            return super(MayaCommandRunner, self)._run(command_to_run)
        except Exception:
            logger.error(
                f'Unhandled exception occurred in command "{command_to_run.id}"'
            )
            raise
