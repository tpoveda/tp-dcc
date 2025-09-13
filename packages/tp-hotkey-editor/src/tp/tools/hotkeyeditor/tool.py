from __future__ import annotations

from Qt.QtWidgets import QVBoxLayout

from tp.core import host
from tp.core.tool import Tool, ToolUiData
from tp.libs.qt.widgets.window import Window

from .view import HotkeyEditorView


class HotkeyEditorTool(Tool):
    """Scene Inventory Tool."""

    id = "tp.hotkeyeditor"
    creator = "Tomi Poveda"
    tags = ["tp", "hotkey", "hotkeys", "editor"]
    ui_data = ToolUiData(
        label="Hotkey Editor",
        tooltip="Editor that allow to load, edit and create hotkey sets",
        icon="hotkey.png",
    )

    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        current_host = host.current_host()
        current_host.show_dialog(
            window_class=HotkeyEditorWindow,
            name="HotkeyEditorUI",
            allows_multiple=False,
        )


class HotkeyEditorWindow(Window):
    """Main window for the Hotkey Editor tool."""

    def __init__(self, **kwargs):
        super().__init__(
            title="Hotkey Editor",
            settings_path="tp/hotkeyeditorui",
            width=1000,
            height=600,
            **kwargs,
        )

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        super().setup_widgets()

        self._view = HotkeyEditorView(parent=self)

    def setup_layouts(self, main_layout: QVBoxLayout):
        super().setup_layouts(main_layout)

        main_layout.addWidget(self._view)
