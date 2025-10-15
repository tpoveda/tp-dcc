from __future__ import annotations

from typing import Any

from loguru import logger
from Qt.QtCore import Qt, Signal, QTimer
from Qt.QtWidgets import QWidget, QMenuBar, QMessageBox

from tp.libs.qt import factory as qt

from .blueprint_canvas import BlueprintCanvasWidget
from ...core.graph_manager import GraphManager
from ...utils import menu
from ..core.editor_command import NodeGraphEditorCommand, NodeGraphEditorCommandsManager


class NodeGraphEditor(QWidget):
    TARGET_FPS: int = 30

    commandExecutionRequested = Signal(object)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._graph_manager = GraphManager()
        self._commands_manager = NodeGraphEditorCommandsManager(parent=self)

        self._modified = False
        self._tick_timer = QTimer(parent=self)
        self._last_clock = 0.0
        self._fps = self.TARGET_FPS

        self._setup_widgets()
        self._setup_layouts()

        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)

        self.start_main_loop()

    # === UI === #

    # noinspection PyAttributeOutsideInit
    def _setup_widgets(self) -> None:
        """Set up all widgets for the window."""

        self._menu_bar = self._setup_menubar()
        self._canvas_widget = BlueprintCanvasWidget(
            graph_manager=self._graph_manager, parent=self
        )

    def _setup_layouts(self) -> None:
        """Set up the layouts for the window."""

        main_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        main_layout.addWidget(self._menu_bar)
        main_layout.addWidget(self._canvas_widget)

    # === Loop === #

    def start_main_loop(self) -> None:
        """Start the main loop of the editor."""

        self._tick_timer.timeout.connect(self._on_tick_timer_timeout)
        self._tick_timer.start(int(1000 / self._fps))

    def stop_main_loop(self) -> None:
        """Stop the main loop of the editor."""

        self._tick_timer.stop()
        self._tick_timer.timeout.disconnect()

    def _on_tick_timer_timeout(self) -> None:
        """Callback for the tick timer timeout signal."""

    # === Editor Commands === #

    @property
    def commands_manager(self) -> NodeGraphEditorCommandsManager:
        """The commands manager instance for the editor."""

        return self._commands_manager

    def execute_command(
        self,
        command: NodeGraphEditorCommand,
        variant_id: str | None = None,
        args: Any = None,
    ) -> bool:
        """Execute a command in the current session.

        Args:
            command: The command to execute.
            variant_id: The ID of the variant to execute. If None, the default
            args: The arguments to pass to the command. This can be a dictionary
                or any other type of data. If `None`, an empty dictionary will
                be used.

        Returns:
            `True` if the command was executed successfully; `False` otherwise.
        """

        self.commandExecutionRequested.emit(command)

        logger.debug(f"Executing Sequence Wizard command: {command.id}")

        return command.process(variant_id=variant_id, args=args)

    # === MenuBar === #

    def _setup_menubar(self) -> QMenuBar:
        """Set up the menu bar for the sequence wizard."""

        menu_bar = QMenuBar(parent=self)
        menu_bar.setNativeMenuBar(False)
        menu_bar.setContentsMargins(0, 0, 0, 0)

        file_menu = menu_bar.addMenu("&File")
        file_commands = ["graph.new"]
        menu.fill_menu_from_commands_layout(self, file_commands, file_menu)

        return menu_bar

    # === Modify State === #

    @property
    def modified(self) -> bool:
        """Whether the editor has unsaved changes."""

        return self._modified

    @modified.setter
    def modified(self, flag: bool) -> None:
        """Set the modified state of the editor."""

        self._modified = flag
        self._update_label()

    def _update_label(self):
        pass

    def should_save(self) -> QMessageBox.StandardButton:
        """Check if there are unsaved changes and prompt the user to save.

        Returns:
            The button clicked by the user in the prompt.
        """

        if not self.modified:
            return False

        return QMessageBox.warning(
            self,
            "Confirm?",
            "Unsaved data will be lost. Do you want to save?",
            QMessageBox.Save | QMessageBox.Cancel | QMessageBox.Discard,
        )

    # === Graphs === #

    def new_graph(self, keep_root: bool = True) -> None:
        """Create a new graph.

        Args:
            keep_root: Whether to keep the root graph or create a new one.
        """

        self._tick_timer.stop()
        self._tick_timer.timeout.disconnect()

        self._graph_manager.clear(keep_root=keep_root)
