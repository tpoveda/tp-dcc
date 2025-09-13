from __future__ import annotations

import typing

from Qt.QtWidgets import QWidget

from tp.core import host
from tp.libs.qt import contexts
from tp.libs.hotkeyeditor import KeySet, KeySetsManager
from tp.libs.qt.widgets.comboboxes import ComboBoxSearchableWidget


class SourceHotkeySetComboBox(ComboBoxSearchableWidget):
    """Combo box widget for selecting a source hotkey set."""

    SEPARATOR = "------"
    SUFFIX = "[TP]"

    def __init__(self, manager: KeySetsManager, parent: QWidget | None = None):
        super().__init__(label="Override Base Hotkey Set:", parent=parent)

        self._manager = manager

        self.refresh()

        self.itemChanged.connect(self._on_item_changed)

    def refresh(self):
        active_key_set = self._manager.current_key_set()

        self.clear()

        default_key_sets = [key_set_name for key_set_name in self._manager._locked]

        host_hotkey_sets = host.current_host().host.available_key_sets()
        try:
            [host_hotkey_sets.remove(key_set_name) for key_set_name in default_key_sets]
        except ValueError:
            # Hotkeys are not set up yet.
            return

        hotkey_set_names = [
            KeySet.to_nice_name(key_set_name, suffix=self.SUFFIX)
            for key_set_name in host_hotkey_sets
        ]
        hotkey_set_names = default_key_sets + [self.SEPARATOR, ""] + hotkey_set_names

        if active_key_set is not None:
            hotkey_set_names.remove(
                KeySet.to_nice_name(active_key_set.name, suffix=self.SUFFIX)
            )

        with contexts.block_signals(self):
            self.add_items(hotkey_set_names)

        if active_key_set:
            self.set_to_text(
                KeySet.to_nice_name(active_key_set.source, suffix=self.SUFFIX)
            )

    # noinspection PyMethodOverriding
    def _on_item_changed(
        self, event: SourceHotkeySetComboBox.ComboItemChangedEvent
    ) -> None:
        """Callback function for when the selected item in the combo box
        changes.

        Args:
            event: The combo item changed event.
        """

        text = event.text
        if text == self.SEPARATOR or text == "":
            return

        key_set_name = KeySet.to_key_set_name(text)
        current_key_set = self._manager.current_key_set()
        if current_key_set is not None:
            current_key_set.set_source(key_set_name)
            current_key_set.update_hotkeys()
