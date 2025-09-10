from __future__ import annotations

from typing import cast, Type
from collections.abc import Generator

from tp.libs.plugin import PluginsManager

from ..core import ModRigTool


class ModRigToolsManager:
    """Class that manages available ModRig tools."""

    ENV_VAR = "TP_MODRIG_TOOLS_PATHS"

    def __init__(self):
        super().__init__()

        self._manager = PluginsManager(interfaces=[ModRigTool], variable_name="id")
        self.reload()

    def reload(self) -> None:
        """Reloads tools from paths defined in environment variable."""

        self._manager.clear()
        self._manager.register_by_environment_variable(self.ENV_VAR)

    def tool_ids(self) -> list[str]:
        """Returns the list of available tool IDs.

        Returns:
            List of available tool IDs.
        """

        return self._manager.plugin_ids

    def iterate_tools(self) -> Generator[Type[ModRigTool]]:
        """Generator that yields all available tool instances.

        Yields:
            `ModRigTool` instance.
        """

        for tool_class in self._manager.plugin_classes:
            yield cast(Type[ModRigTool], tool_class)

    def tool_class(self, tool_id: str) -> Type[ModRigTool] | None:
        """Returns the tool class for the given tool ID.

        Args:
            tool_id: The ID of the tool to retrieve.

        Returns:
            The `ModRigTool` class if found, otherwise None.
        """

        return cast(Type[ModRigTool] | None, self._manager.get_plugin(tool_id))
