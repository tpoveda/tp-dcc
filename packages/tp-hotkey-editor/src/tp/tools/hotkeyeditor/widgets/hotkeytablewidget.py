from __future__ import annotations

from Qt.QtWidgets import QWidget, QTableWidget

from tp.libs.qt.widgets.search import SearchLineEdit


class HotkeyTableWidget(QTableWidget):
    """Table widget for displaying and editing hotkeys."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)


class HotkeySearchWidget(QWidget):
    """Widget for searching hotkeys."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up the widgets for the search widget."""

        self._search_edit = HotkeySearchEdit(parent=self)

    def _setup_layouts(self):
        """Set up the layouts for the search widget."""

        from tp.libs.qt import factory as qt

        main_layout = qt.horizontal_layout(spacing=2)
        self.setLayout(main_layout)

        main_layout.addWidget(self._search_edit)


class HotkeySearchEdit(SearchLineEdit):
    """Search line edit for searching hotkeys."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)
