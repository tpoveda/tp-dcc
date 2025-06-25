from __future__ import annotations

from tp.core import host
from tp.core.tool import Tool


class PreferencesTool(Tool):
    """Preferences Tool for managing preferences and settings."""

    id = "tp.preferences"
    creator = "Tomi Poveda"
    tags = ["preferences", "tool"]
    ui_data = {
        "label": "Tools Preferences",
        "tooltip": "Manage and visualize preferences.",
        "icon": "settings.png",
    }

    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        from tp.preferences.ui.view import PreferencesView

        current_host = host.current_host()
        current_host.show_dialog(
            window_class=PreferencesView, name="PreferencesUI", allows_multiple=False
        )
