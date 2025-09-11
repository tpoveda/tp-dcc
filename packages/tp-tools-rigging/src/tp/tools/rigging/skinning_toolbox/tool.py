from __future__ import annotations

from tp.core import Tool, UiData, current_host

from .controller import SkinningToolboxControllerFactory
from .view import SkinningToolboxWindow


class SkinningToolbox(Tool):
    """Tool used to match and bake animations."""

    id = "tp.rigging.skinningtoolbox"
    creator = "Tomi Poveda"
    tags = ["tp", "rigging", "skin", "skinning", "toolbox", "tool"]
    ui_data = UiData(
        label="Skinning Toolbox",
        icon="skin.png",
        tooltip="Toolbox for skinning operations.",
    )

    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        controller = SkinningToolboxControllerFactory.controller()

        host = current_host()
        host.show_dialog(
            window_class=SkinningToolboxWindow,
            name="SkinningToolboxUI",
            allows_multiple=False,
            controller=controller,
        )
