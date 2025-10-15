from __future__ import annotations

import sys
import typing
import weakref
import traceback
from typing import Iterable, Any
from abc import ABC, abstractmethod

from loguru import logger
from Qt.QtCore import Qt, QObject
from Qt.QtWidgets import QApplication, QMessageBox, QProgressDialog

from tp.libs.plugin import PluginsManager, PluginExecutionStats


if typing.TYPE_CHECKING:
    from ..widgets.editor import NodeGraphEditor


# === Command === #


class NodeGraphEditorCommand(ABC):
    """Base class to define commands for the node graph editor."""

    id = ""
    ui_data = {"icon": "about.png", "tooltip": "", "label": ""}

    def __init__(
        self,
        editor: NodeGraphEditor,
    ):
        self._editor = weakref.ref(editor)
        self._progress_dialog: QProgressDialog | None = None

    @property
    def editor(self) -> NodeGraphEditor | None:
        """The editor of the command."""

        return self._editor() if self._editor is not None else None

    # noinspection PyMethodMayBeStatic
    def is_visible(self) -> bool:
        """Check if the command is visible in the UI.

        Returns:
            `True` if the command is visible; `False` otherwise.
        """

        return True

    # noinspection PyMethodMayBeStatic
    def is_checked(self) -> bool:
        """Check if the command is checked in the UI.

        Returns:
            `True` if the command is checked; `False` otherwise.
        """

        return False

    # noinspection PyMethodMayBeStatic
    def variants(self) -> list[dict[str, Any]]:
        """Get the variants of the command

        Returns:
            A list of dictionaries containing the variants of the command.
        """

        return []

    def variant_by_id(self, variant_id: str) -> dict[str, Any]:
        """Get a variant of the command from the given variant ID.

        Args:
            variant_id: The ID of the variant to get.

        """

        if not variant_id:
            return {}
        try:
            result = [x for x in self.variants() if x["id"] == variant_id][0]
        except Exception:
            raise Exception(f"VariantID: '{variant_id}' not found for '{self.id}'")

        return result

    @abstractmethod
    def execute(self, *args, **kwargs):
        """Execute the command based on the current context."""

        raise NotImplementedError(
            "The `execute` method must be implemented in the derived class."
        )

    def process(self, variant_id: str | None = None, args: Any = None):
        """Process the command with the given variant ID and arguments.

        Args:
            variant_id: The ID of the variant to use.
            args: The arguments to pass to the command.
        """

        args = args or {}
        # noinspection PyTypeChecker
        stat = PluginExecutionStats(self)
        exc_type, exc_value, exc_tb = None, None, None
        try:
            stat.start()
            logger.debug("Executing plugin: {}".format(self.id))
            variant = self.variant_by_id(variant_id)
            if variant:
                exe_args = variant.get("args", {})
                exe_args.update(args)
                return self.execute(**exe_args)

            return self.execute(**args)

        except Exception:
            exc_type, exc_value, exc_tb = sys.exc_info()
            stat.finish(traceback.format_exception(exc_type, exc_value, exc_tb))
            self.show_error(
                f"Error executing command '{self.id}': {exc_value}",
                log_exception=True,
            )
            raise
        finally:
            self.close_progress_dialog()
            if not exc_type:
                stat.finish(None)
            logger.debug(
                f"Finished executing plugin: {self.id}, execution "
                f"time: {stat.info.execution_time}"
            )

    def show_progress_dialog(
        self,
        message: str,
        title: str,
        can_be_cancelled: bool = False,
        minimum: int = 0,
        maximum: int = 100,
    ):
        """Show a progress dialog with the given message and title.

        Args:
            message: The message to display in the progress dialog.
            title: The title of the progress dialog.
            can_be_cancelled: Whether the progress dialog can be cancelled by
                the user. Defaults to False.
            minimum: The minimum value of the progress dialog. Defaults to 0.
            maximum: The maximum value of the progress dialog. Defaults to 100.
        """

        self.close_progress_dialog()

        self._progress_dialog = QProgressDialog(
            message, "Cancel", minimum, maximum, parent=self.editor
        )

        if not can_be_cancelled:
            self._progress_dialog.setCancelButton(None)
        self._progress_dialog.setWindowTitle(title)
        self._progress_dialog.setWindowModality(Qt.WindowModal)
        self._progress_dialog.setMinimumDuration(minimum)
        self._progress_dialog.setAutoClose(False)
        self._progress_dialog.setAutoReset(False)
        self._progress_dialog.show()
        QApplication.processEvents()

    def close_progress_dialog(self):
        """Close the progress dialog if it is open."""

        if self._progress_dialog is not None:
            self._progress_dialog.close()
            self._progress_dialog = None
            QApplication.processEvents()

    def show_error(
        self,
        message: str,
        show_toast: bool = False,
        show_message_box: bool = True,
        log_exception: bool = False,
    ):
        """Show an error message in the progress dialog.

        Args:
            message: The error message to display.
            show_toast: Whether to show the message as a toast notification.
            show_message_box: Whether to show the message in a message box.
            log_exception: Whether to log the exception information.
        """

        logger.error(message, exc_info=log_exception)

        # self.editor.show_error(message, show_toast=show_toast, log_message=False)

        if show_message_box:
            QMessageBox.critical(self.editor, "Error", message)


# === Manager === #


class NodeGraphEditorCommandsManager(QObject):
    """Manager for the commands in the sequence wizard."""

    ENV_VAR = "TNM_NODE_GRAPH_EDITOR_COMMANDS"

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._commands = {}

        self._manager = PluginsManager(interfaces=[NodeGraphEditorCommand])

        self.reload()

    def reload(self):
        """Reload the available commands"""

        self._manager.register_by_environment_variable(self.ENV_VAR)

    def command(self, command_id: str) -> type[NodeGraphEditorCommand] | None:
        """Get a command by its ID.

        Args:
            command_id: The ID of the command.

        Returns:
            The command instance or `None` if not found.
        """

        return self._manager.get_plugin(command_id)

    def iterate_commands_from_layout(
        self, layout: list[str]
    ) -> Iterable[tuple[type[NodeGraphEditorCommand] | None, str, str | None]]:
        """Iterate over the commands in the layout.

        Args:
            layout: The layout of the commands.

        Returns:
            An iterable of tuples containing the command, its type, and
                variant ID.
        """

        for command_id in layout:
            variant_id = ""
            ids = command_id.split(":")
            if len(ids) > 1:
                variant_id = ids[1]
            _command_id = ids[0]
            # noinspection PyTypeChecker
            plugin: type[NodeGraphEditorCommand] = self._manager.get_plugin(_command_id)
            if plugin is None:
                if command_id == "---":
                    yield None, "SEPARATOR", None
                    continue
                logger.warning("Missing Requested Plugin: {}".format(command_id))
                continue
            yield plugin, "PLUGIN", variant_id
