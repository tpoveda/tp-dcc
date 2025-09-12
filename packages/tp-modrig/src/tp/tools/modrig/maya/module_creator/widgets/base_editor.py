from __future__ import annotations

from Qt.QtWidgets import QWidget


class BaseEditorWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up the widgets for the editor."""
        pass

    def _setup_layouts(self):
        """Set up the layouts for the editor."""

        pass
