from __future__ import annotations

from typing import Type

from tp.common import plugin

from tp.tools.rig.crit.builder.core import command


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
