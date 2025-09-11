from __future__ import annotations

from tp.core import consts
from tp.libs.plugin import PluginsManager
from tp.libs.python.decorators import Singleton

from ..widgets.toolpanel import ToolPanelWidget


class ToolPanelsManager(metaclass=Singleton):
    PANELS_ENV_VAR = consts.TOOLS_ENV_VAR
    PANELS_PALETTE_ENV_VAR = "TP_TOOL_PANELS_PALETTE_PATHS"

    def __init__(self):
        super().__init__()

        self._tool_panel_groups: list = []

        self._manager = PluginsManager(
            interfaces=[ToolPanelWidget], variable_name="id", name="ToolPanels"
        )

        self.discover_tool_panels()

    def discover_tool_panels(self):
        """Discovers available tool panels and palettes."""

        self._manager.register_by_environment_variable(self.PANELS_ENV_VAR)

    def tool_panel_class(self, tool_id: str) -> type[ToolPanelWidget] | None:
        """Return the tool panel class for the given tool ID."""

        return self._manager.get_plugin(tool_id)

    def tool_panel_color(self, tool_id: str) -> tuple[int, int, int] | None:
        for toolset_group in self._tool_panel_groups:
            pass

        return None
