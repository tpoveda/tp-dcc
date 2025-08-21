from __future__ import annotations

from tp.core import host
from tp.core.tool import Tool


class SceneInventoryTool(Tool):
    """Scene Inventory Tool."""

    id = "tp.core.sceneinventory"
    creator = "Tomi Poveda"
    tags = ["tp", "core", "sceneinventory"]
    ui_data = {
        "label": "Scene Inventory",
        "tooltip": "Manage scene inventory items",
        "icon": "sceneinventory.png",
    }

    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        from tp.tools.sceneinventory.ui.view import SceneInventoryWindow
        from tp.tools.sceneinventory.controller import SceneInventoryController

        controller = kwargs.get("controller", SceneInventoryController())

        current_host = host.current_host()
        current_host.show_dialog(
            window_class=SceneInventoryWindow,
            name="SceneInventoryUI",
            allows_multiple=False,
            controller=controller,
        )
