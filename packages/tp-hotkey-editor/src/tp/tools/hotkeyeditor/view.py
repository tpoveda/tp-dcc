from __future__ import annotations

from Qt.QtWidgets import QWidget

from tp.libs.qt import factory as qt


class HotkeyEditorView(QWidget):
    """Main view for the Hotkey Editor tool."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up the widgets for the hotkey editor view."""

    def _setup_layouts(self):
        """Set up the layouts for the hotkey editor view."""

        main_layout = qt.vertical_main_layout()
        self.setLayout(main_layout)