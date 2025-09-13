from __future__ import annotations

from Qt.QtWidgets import QWidget, QSplitter

from tp.libs.qt import icons
from tp.libs.qt import factory as qt
from tp.libs.hotkeyeditor import KeySetsManager, is_admin_mode

from .widgets.hotkeysetcombo import SourceHotkeySetComboBox
from .widgets.hotkeytablewidget import HotkeySearchWidget, HotkeyTableWidget


class HotkeyEditorView(QWidget):
    """Main view for the Hotkey Editor tool."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        # noinspection PyTypeChecker
        self._manager: KeySetsManager = KeySetsManager()

        self._setup_widgets()
        self._setup_layouts()

        self._install_hotkeys()

    def _setup_widgets(self):
        """Set up the widgets for the hotkey editor view."""

        self._splitter = QSplitter(parent=self)

        self._table_widget = HotkeyTableEditorWidget(manager=self._manager, parent=self)
        self._table_widget.setEnabled(False)

        self._splitter.addWidget(self._table_widget)

    def _setup_layouts(self):
        """Set up the layouts for the hotkey editor view."""

        main_layout = qt.vertical_main_layout()
        self.setLayout(main_layout)

        main_layout.addWidget(self._splitter)
        main_layout.setStretch(2, 1)

    def _install_hotkeys(self):
        self._manager.install_hotkeys()
        # self._manager.save_hotkeys()

        self._table_widget.setEnabled(True)


class HotkeyTableEditorWidget(QWidget):
    """Table widget for displaying and editing hotkeys."""

    def __init__(self, manager: KeySetsManager, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._manager = manager

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up the widgets for the hotkey table."""

        self._source_combo = SourceHotkeySetComboBox(manager=self._manager, parent=self)
        self._hotkey_table = HotkeyTableWidget(parent=self)
        self._hotkey_buttons_label = qt.label(text="Add/Remove Hotkeys", parent=self)
        self._new_hotkey_button = qt.styled_button(
            button_icon=icons.icon("plus_circle"),
            tooltip="Create a new hotkey",
            style=qt.ButtonStyles.TransparentBackground,
            parent=self,
        )
        self._delete_hotkey_button = qt.styled_button(
            button_icon=icons.icon("cancel_circle"),
            tooltip="Delete selected hotkey",
            style=qt.ButtonStyles.TransparentBackground,
            parent=self,
        )
        self._search_widget = HotkeySearchWidget(parent=self)
        self._revert_hotkeys_button = qt.styled_button(
            button_icon=icons.icon("left_arrow2"),
            style=qt.ButtonStyles.TransparentBackground,
            tooltip="Revert All Current Hotkey Settings",
            parent=self,
        )
        self._revert_hotkeys_button.setEnabled(False)

        self._save_close_button = qt.styled_button(
            text="Save",
            button_icon=icons.icon("save"),
            force_upper=True,
            tooltip="Save All Current Hotkey Settings",
            parent=self,
        )
        self._apply_button = qt.styled_button(
            text="Apply",
            button_icon=icons.icon("checkmark"),
            force_upper=True,
            tooltip="Apply All Current Hotkey Settings",
            parent=self,
        )
        self._cancel_button = qt.styled_button(
            text="Cancel",
            button_icon=icons.icon("close"),
            force_upper=True,
            tooltip="Cancel All Current Hotkey Settings",
            parent=self,
        )

        if self._manager.is_locked_key_set() and not is_admin_mode():
            self._new_hotkey_button.setEnabled(False)
            self._delete_hotkey_button.setEnabled(False)

    def _setup_layouts(self):
        """Set up the layouts for the hotkey table."""

        main_layout = qt.grid_layout(spacing=2, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        table_buttons_layout = qt.horizontal_layout(spacing=2, margins=(0, 0, 0, 0))
        table_buttons_layout.addWidget(self._hotkey_buttons_label)
        table_buttons_layout.addWidget(self._new_hotkey_button)
        table_buttons_layout.addWidget(self._delete_hotkey_button)
        table_buttons_layout.addStretch()
        table_buttons_layout.addWidget(self._search_widget)
        table_buttons_layout.addWidget(self._revert_hotkeys_button)

        buttons_layout = qt.horizontal_layout(spacing=2, margins=(0, 0, 0, 0))
        buttons_layout.addWidget(self._save_close_button)
        buttons_layout.addWidget(self._apply_button)
        buttons_layout.addWidget(self._cancel_button)

        main_layout.addWidget(self._source_combo, 1, 0)
        main_layout.addWidget(self._hotkey_table, 2, 0)
        main_layout.addLayout(table_buttons_layout, 3, 0)
        main_layout.addLayout(buttons_layout, 4, 0)
