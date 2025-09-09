from __future__ import annotations

from Qt.QtWidgets import QVBoxLayout

from tp.libs.qt.widgets import Window
from tp.core import Tool, UiData, current_host

from .view import ModuleCreatorView


class ModuleCreatorTool(Tool):
    """Tool to create rigging modules interactively."""

    id = "tp.modrig.module_creator"
    creator = "Tomi Poveda"
    ui_data = UiData(label="Module Creator")
    tags = ["modrig", "rigging", "modules"]

    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        host = current_host()
        host.show_dialog(
            window_class=ModuleCreatorWindow,
            name="ModuleBuilderUI",
            allows_multiple=False,
        )


class ModuleCreatorWindow(Window):
    """Main window for the Module Creator tool."""

    def __init__(self, **kwargs):
        super().__init__(title="Module Creator", **kwargs)

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        super().setup_widgets()

        self._view = ModuleCreatorView(parent=self)

    def setup_layouts(self, main_layout: QVBoxLayout):
        super().setup_layouts(main_layout)

        main_layout.addWidget(self._view)
