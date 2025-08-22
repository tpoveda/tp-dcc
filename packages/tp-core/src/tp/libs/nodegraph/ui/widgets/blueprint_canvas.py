from __future__ import annotations

from Qt.QtWidgets import QWidget
from Qt.QtGui import QKeyEvent, QMouseEvent

from tp.libs.qt import factory as qt

from tp.libs.nodegraph.core.input import InputAction, InputActionType
from ..canvas.canvas_base import CanvasBase


class BlueprintCanvas(CanvasBase):
    pass


class BlueprintCanvasWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._shortcuts_enabled = True
        self._current_pressed_key: int | None = None

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self) -> None:
        """Set up widgets for the blueprint canvas."""

        self._canvas = BlueprintCanvas(parent=self)

    def _setup_layouts(self) -> None:
        """Set up layouts for the blueprint canvas."""

        main_layout = qt.vertical_main_layout()
        self.setLayout(main_layout)

        main_layout.addWidget(self._canvas)

    # === Shortcuts ===

    def is_shortcuts_enabled(self) -> bool:
        """Check if shortcuts are enabled.

        Returns:
             `True` if shortcuts are enabled; `False` otherwise.
        """

        return self._shortcuts_enabled

    def enable_shortcuts(self) -> None:
        """Enable shortcuts for the canvas."""

        self._shortcuts_enabled = True

    def disable_shortcuts(self) -> None:
        """Disable shortcuts for the canvas."""

        self._shortcuts_enabled = False

    #  === Input Actions ===

    def keyPressEvent(self, event: QKeyEvent) -> None:
        modifiers = event.modifiers()
        current_input_action = InputAction(
            "temp",
            InputActionType.Keyboard,
            "temp",
            key=event.key(),
            modifiers=modifiers,
        )
        self._current_pressed_key = event.key()

        if self.is_shortcuts_enabled():
            pass

        super().keyPressEvent(event)

    # === Navigation ===

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events.

        Args:
            event (QMouseEvent): The mouse event.
        """

        super().mousePressEvent(event)
