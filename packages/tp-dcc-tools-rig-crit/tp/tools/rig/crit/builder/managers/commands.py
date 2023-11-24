from __future__ import annotations

from typing import Tuple, List, Type, Iterator

from tp.core import log
from tp.common import plugin

from tp.tools.rig.crit.builder.core import command

logger = log.rigLogger


class UiCommandsManager:
	"""
	Manager that registers all available CRIT UI Commands.
	"""

	COMMANDS_ENV = 'CRIT_UI_COMMANDS_PATHS'

	def __init__(self):
		super().__init__()

		self._crit_commands = {}
		self._manager = plugin.PluginFactory(interface=command.CritUiCommand, plugin_id='ID')
		self.reload()

	def reload(self):
		"""
		Reloads commands manager.
		"""

		self._manager.clear()
		self._manager.register_paths_from_env_var(self.COMMANDS_ENV)

	def plugin(self, command_id: str) -> Type | None:
		"""
		Retrieves a plugin based on the given command ID.

		:param str command_id: ID of the command to retrieve.
		:return: found command with given ID.
		:rtype: Type or None
		"""

		return self._manager.get_plugin_from_id(command_id)

	def iterate_ui_commands_from_ids(
			self, ui_commands_ids: List[str]) -> Iterator[Tuple[Type | None, str, str | None]]:
		"""
		Generator function that iterates over all ui commands that matches the given IDs.

		:param List[str] ui_commands_ids: list of UI commands IDs. '---' ID can be used to return a separator, which
		is useful when we want to generate contextual menus from the iterated UI commands.
		:return: iterated ui commands.
		:rtype: Iterator[Tuple[Type or None, str, str or None]]
		"""

		for ui_command_id in ui_commands_ids:
			variant_id = ''
			ids = ui_command_id.split(':')
			if len(ids) > 1:
				variant_id = ids[1]
			found_command_ui = self._manager.get_plugin_from_id(ids[0])
			if found_command_ui is None:
				if ui_command_id == '---':
					yield None, 'SEPARATOR', None
					continue
				logger.warning(f'Missing requested UI command: "{ui_command_id}"')
				continue
			yield found_command_ui, 'PLUGIN', variant_id
