from __future__ import annotations

from ..core.tool import Tool
from ..core.consts import TOOLS_ENV_VAR
from ..libs.plugin import PluginsManager
from ..libs.python.decorators import Singleton


class ToolsManager(metaclass=Singleton):
    """Manager class that handles the registration of TP DCC tools."""

    def __init__(self):
        super().__init__()

        self._manager = PluginsManager(
            interfaces=[Tool], variable_name="id", name="tp.tools"
        )

        self.discover_tools()

    def discover_tools(self):
        """Searches all the tools defined in the environment variable."""

        self._manager.register_by_environment_variable(TOOLS_ENV_VAR)
