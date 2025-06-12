from __future__ import annotations

from typing import Any

from maya import cmds

from tp.libs.commands.errors import UserCancelError
from tp.libs.commands.command import AbstractCommand


class MayaCommand(AbstractCommand):
    """Implementation of the AbstractCommand class for Maya commands."""

    # Whether to chunk all operations in `do`.
    use_undo_chunk = True

    # Whether to disable the undo queue in `do`.
    disable_queue = False

    @staticmethod
    def disable_undo_queue(flag: bool):
        """
        Enables/Disables the Maya undo queue.

        Args:
            flag: Whether to disable the undo queue or not.
        """

        cmds.undoInfo(stateWithoutFlush=not flag)

    @staticmethod
    def is_queue_disabled() -> bool:
        """
        Returns whether the Maya undo queue is disabled or not.

        Returns:
            Whether the Maya undo queue is disabled or not.
        """

        return not cmds.undoInfo(query=True, stateWithoutFlush=True)

    def run_arguments(self, **arguments) -> Any:
        """Overrides `run_arguments` method to add support for Maya specific
        arguments.

        Args:
            **arguments: Arguments to run the command with.

        Returns:
            Command run result.

        Raises:
            UserCancelError: If the command is canceled by the user.
            Exception: If the command fails to run.
        """

        original_state = self.is_queue_disabled()
        self.disable_undo_queue(self.disable_queue)
        try:
            self.parse_arguments(arguments)
            result = self.run()
        except UserCancelError:
            raise
        except Exception:
            raise
        finally:
            self.disable_undo_queue(original_state)

        return result
