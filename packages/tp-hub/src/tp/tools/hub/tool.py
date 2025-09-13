from __future__ import annotations

from typing import cast, Any

from Qt.QtWidgets import QWidget

from tp.core import Tool, ToolUiData, current_host

from .view import HubWindow


class HubTool(Tool):
    """Tool to that acts as the hub to access all available tp-dcc functionality."""

    id = "tp.hub"
    creator = "Tomi Poveda"
    ui_data = ToolUiData(label="Hub")
    tags = ["hub"]

    # noinspection PyAttributeOutsideInit
    def execute(self, *args, **kwargs) -> HubWindow:
        """Execute the tool with the specified arguments.

        Args:
            args: Positional arguments to pass to the function.
            kwargs: Keyword arguments to pass to the function.

        Returns:
            The created `HubWindow` instance.
        """

        return launch(tool_args=kwargs or {})


def launch(
    tool_args: dict[str, Any] | None = None, parent: QWidget | None = None
) -> HubWindow:
    """Launches the hub window.

    Args:
        tool_args: Dictionary of tool arguments. Supported keys are:
            - tool_ids: List of tool ids to show in the hub. If not specified,
                all available tools will be shown.
            - init_pos: Initial position of the window as a tuple of (x, y)
                coordinates.
        parent: The parent widget of the window.

    Returns:
        The created `HubWindow` instance.
    """

    tool_args = tool_args or {}
    tool_ids: list[str] = tool_args.get("tool_ids", [])
    init_pos: tuple[int, int] | None = tool_args.get("init_pos", None)

    host = current_host()
    window = cast(
        HubWindow,
        host.show_dialog(
            window_class=HubWindow,
            name="HubUI",
            allows_multiple=True,
            init_pos=init_pos,
            icon_color=(231, 133, 255),
            hue_shift=10,
            tool_ids=tool_ids,
            parent=parent,
        ),
    )

    return window
