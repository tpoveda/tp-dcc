from __future__ import annotations

from tp.core import host
from tp.core.tool import Tool


class AssetsTool(Tool):
    """Asset Tool for managing and visualizing assets."""

    id = "tp.assets"
    creator = "Tomi Poveda"
    tags = ["assets", "tool"]
    ui_data = {
        "label": "Assets",
        "tooltip": "Manage and visualize assets.",
        "icon": "assets.png",
    }

    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        from tp.assets.ui.view import AssetsView

        current_host = host.current_host()
        current_host.show_dialog(
            window_class=AssetsView, name="AssetsUI", allows_multiple=True
        )
