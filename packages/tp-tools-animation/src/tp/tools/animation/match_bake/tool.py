from __future__ import annotations

from tp.core import Tool, UiData, current_host

from .controller import MatchBakeControllerFactory
from .view import MatchBakeWindow


class MatchBakeTool(Tool):
    """Tool used to match and bake animations."""

    id = "tp.animation.matchbake"
    creator = "Tomi Poveda"
    tags = ["tp", "animation", "match", "bake", "tool"]
    ui_data = UiData(label="Match & Bake Animations")

    def execute(self, *args, **kwargs):
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.
        """

        controller = MatchBakeControllerFactory.controller()

        host = current_host()
        host.show_dialog(
            window_class=MatchBakeWindow,
            name="MatchBakeUI",
            allows_multiple=False,
            controller=controller,
        )
