from __future__ import annotations

from typing import cast, Any
from dataclasses import dataclass, field

from loguru import logger

from ..core.tool import Tool, ToolUiData
from ..core.consts import TOOLS_ENV_VAR
from ..libs.plugin import PluginsManager
from ..libs.python.decorators import Singleton


def launch_tool(tool_id: str, *args: Any, **kwargs: Any) -> Tool:
    """Launch a tool by its ID.

    Args:
        tool_id: The ID of the tool to launch.
        *args: Positional arguments to pass to the tool.
        **kwargs: Keyword arguments to pass to the tool.

    Returns:
        The instance of the launched tool.
    """

    # noinspection PyUnresolvedReferences
    return ToolsManager().execute_tool(tool_id, *args, **kwargs)


@dataclass
class ToolCommand:
    """Represents a command to be executed by a specific tool that encapsulates
    the information necessary to execute a command on a specific tool.

    Attributes:
        tool_id: The unique identifier for the tool the command is associated
            with.
        string: The command string to be executed.
        arguments: A dictionary of arguments the  command requires.
    """

    tool_id: str
    string: str = ""
    arguments: dict[str, Any] | None = field(default_factory=dict)


class ToolsManager(metaclass=Singleton):
    """Manager class that handles the registration of TP DCC tools."""

    COMMAND_STRING = "from tp.core.managers import tools; tools.launch_tool(**{})"

    def __init__(self):
        super().__init__()

        self._manager = PluginsManager(
            interfaces=[Tool], variable_name="id", name="tp.tools"
        )

        self.discover_tools()

    def tool_ids(self) -> list[str]:
        """Returns a list of all registered tool IDs."""

        return self._manager.plugin_ids

    def discover_tools(self):
        """Searches all the tools defined in the environment variable."""

        self._manager.register_by_environment_variable(TOOLS_ENV_VAR)
        self._manager.load_all_plugins()

    def tool_class(self, tool_id: str) -> type[Tool] | None:
        """Returns the tool class for a given tool ID.

        Args:
            tool_id: The ID of the tool.

        Returns:
            The tool class if found, otherwise None.
        """

        try:
            return cast(type[Tool], self._manager.get_plugin(tool_id))
        except AttributeError:
            logger.error(f"Tool with ID '{tool_id}' is not registered.")
            return None

    def generate_command(
        self, tool_id: str, arguments: dict[str, Any] | None = None
    ) -> ToolCommand:
        """Generates a command string for a tool based on its ID and arguments.

        Args:
            tool_id: The ID of the tool.
            arguments: The arguments to pass to the tool.

        Returns:
            A command string that can be executed.
        """

        args = arguments or {}
        args["tool_id"] = tool_id
        command = self.COMMAND_STRING.format(args)

        return ToolCommand(tool_id, arguments=args, string=command)

    def tool_ui_data(
        self, tool_id: str, overrides: ToolUiData | None = None
    ) -> ToolUiData:
        """Get the UI data for a tool by its ID.

        Args:
            tool_id: The ID of the tool.
            overrides: Optional dictionary to override specific UI data.

        Returns:
            A dictionary containing the UI data for the tool.
        """

        ui_data = ToolUiData()
        overrides = overrides or ToolUiData()
        try:
            tool_class: type[Tool] = cast(type[Tool], self._manager.get_plugin(tool_id))
            ui_data.update(tool_class.ui_data)
            ui_data["tags"] = list(set(tool_class.tags))
            ui_data["class_name"] = tool_class.__name__
            ui_data.update(overrides)
        except AttributeError:
            logger.error(f"Tool with ID '{tool_id}' does not have UI data defined.")

        return ui_data

    def execute_tool(self, tool_id: str, *args: Any, **kwargs: Any) -> Tool:
        """Execute a tool by its ID.

        Args:
            tool_id: The ID of the tool to execute.
            *args: Positional arguments to pass to the tool.
            **kwargs: Keyword arguments to pass to the tool.

        Returns:
            The instance of the executed tool.

        Raises:
            ValueError: If the tool with the specified ID is not registered.
        """

        tool_instance = cast(Tool, self._manager.loaded_plugin(tool_id))
        if tool_instance is None:
            raise ValueError(f"Tool with ID '{tool_id}' is not registered.")

        # noinspection PyProtectedMember
        tool_instance._execute(*args, **kwargs)
        logger.debug(
            f"{tool_instance}, Execution time: {tool_instance.stats.execution_time}"
        )

        return tool_instance

    def shutdown(self):
        """Attempts to cleanly shut down all tools and unload plugins."""

        logger.debug("Attempting to teardown all tools...")
        for tool_instance in self._manager.loaded_plugins:
            logger.debug(f"Shutting down tool -> {tool_instance.id}")
            # noinspection PyProtectedMember
            cast(Tool, tool_instance)._run_teardown()

        self._manager.unload_all_plugins()

    def tool_color(self, tool_id: str) -> tuple[int, int, int] | None:
        """Return the default color for tools in the UI.

        Returns:
            A tuple representing the RGB color.
        """

        return None
