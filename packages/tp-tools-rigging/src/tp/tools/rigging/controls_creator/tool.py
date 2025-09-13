from __future__ import annotations

from tp.core import Tool, ToolUiData
from tp.tools.hub import ToolPanelWidget

from .view import ControlsCreatorView
from .model import ControlsCreatorModel
from .controller import ControlsCreatorController


class ModuleCreatorTool(Tool):
    """Tool to create and edit controls."""

    id = "tp.rigging.controls.creator"
    creator = "Tomi Poveda"
    ui_data = ToolUiData(
        label="Control Creator",
        icon="star_control",
        tooltip="Tool for creating control curves",
    )
    tags = ["modrig", "rigging", "modules"]
    tool_model = ControlsCreatorModel
    tool_controller = ControlsCreatorController
    tool_view = ControlsCreatorView

    @classmethod
    def setup_model_controller(
        cls, model: ControlsCreatorModel, controller: ControlsCreatorController
    ) -> None:
        """Sets up the model and controller instances.

        Args:
            model: The model instance.
            controller: The controller instance.
        """

        pass

    @classmethod
    def setup_tool_panel(
        cls, tool_panel: ToolPanelWidget, view: ControlsCreatorView
    ) -> None:
        """Sets up the tool panel widget.

        Args:
            tool_panel: The tool panel widget.
            view: The controls creator view instance.
        """

        tool_panel.toolPanelDragged.connect(view.thumb_browser.close_directory_popup)
        tool_panel.toolPanelDeactivated.connect(
            view.thumb_browser.close_directory_popup
        )
        tool_panel.toolPanelDropped.connect(view.thumb_browser.close_directory_popup)

        hub_window = tool_panel.hub_window
        if hub_window is not None:
            hub_window.minimized.connect(view.thumb_browser.close_directory_popup)
            hub_window.beginClosing.connect(view.thumb_browser.close_directory_popup)
            hub_window.closed.connect(view.thumb_browser.close_directory_popup)
