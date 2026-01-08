from __future__ import annotations

from tp.core import Tool, ToolUiData, current_host

from .view import RigBuilderWindow


class RigBuilder(Tool):
    """Tool used to match and bake animations."""

    id = "tp.rigging.rigbuilder"
    creator = "Tomi Poveda"
    tags = ["tp", "rigging", "builder"]
    ui_data = ToolUiData(
        label="Rig Builder",
        icon="build.png",
        tooltip="Tool for building rigs.",
    )

    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        host = current_host()
        host.show_dialog(
            window_class=RigBuilderWindow,
            name="RigBiulderUI",
            allows_multiple=False,
        )
