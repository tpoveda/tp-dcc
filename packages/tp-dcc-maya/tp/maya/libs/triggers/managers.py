from __future__ import annotations

import os
from typing import List, Dict

from tp.common import plugin
from tp.common.python import decorators, yamlio
from tp.maya.libs.triggers import consts, errors, triggercommand, markingmenu


@decorators.add_metaclass(decorators.Singleton)
class TriggersManager:
	"""
	Class that holds all available trigger command classes
	"""

	TRIGGER_ENV_VAR = consts.TRIGGER_ENV

	def __init__(self):
		super(TriggersManager, self).__init__()

		self._factory = plugin.PluginFactory(interface=[triggercommand.TriggerCommand], plugin_id='ID')
		self._factory.register_paths_from_env_var(self.TRIGGER_ENV_VAR)

	@property
	def factory(self) -> plugin.PluginFactory:
		return self._factory

	def commands(self) -> List[triggercommand.TriggerCommand]:
		"""
		Returns list of all trigger command classes registered within this manager.

		:return: list of trigger command classes.
		:rtype: List[triggercommand.TriggerCommand]
		"""

		return self._factory.plugins()

	def command(self, command_name: str) -> triggercommand.TriggerCommand | None:
		"""
		Returns the trigger command class of given type.

		:param str command_name: name of the command to retrieve.
		:return: command class.
		:rtype: triggercommand.TriggerCommand or None
		"""

		return self._factory.get_plugin_from_id(command_name)


@decorators.add_metaclass(decorators.Singleton)
class MarkingMenusManager:
	"""
	Class that holds all currently available marking menu layouts.
	"""

	LAYOUT_ENV = 'TPDCC_MARKING_MENU_LAYOUT_PATHS'
	MENU_ENV = 'TPDCC_MARKING_MENU_PATHS'
	COMMAND_ENV = 'TPDCC_MARKING_MENU_COMMAND_PATHS'
	STATIC_MARKING_MENU_LAYOUT_TYPE = 0
	DYNAMIC_MARKING_MENU_LAYOUT_TYPE = 1

	def __init__(self):

		self._layouts = {}					# type: Dict[str, markingmenu.MarkingMenuLayout]
		self._active_menus = {}				# type: Dict[str, markingmenu.MarkingMenu]
		self.register_layout_by_env(MarkingMenusManager.LAYOUT_ENV)
		self._menu_factory = plugin.PluginFactory(interface=[markingmenu.MarkingMenuDynamic], plugin_id='ID')
		self._commands_factory = plugin.PluginFactory(interface=[markingmenu.MarkingMenuCommand], plugin_id='ID')
		self._menu_factory.register_paths_from_env_var(MarkingMenusManager.MENU_ENV)
		self._commands_factory.register_paths_from_env_var(MarkingMenusManager.COMMAND_ENV)

	@property
	def layouts(self) -> Dict[str, markingmenu.MarkingMenuLayout]:
		return self._layouts

	@property
	def active_menus(self) -> Dict:
		return self._active_menus

	@property
	def menu_factory(self) -> plugin.PluginFactory:
		return self._menu_factory

	@property
	def commands_factory(self) -> plugin.PluginFactory:
		return self._commands_factory

	def register_layout_by_env(self, env: str):
		"""
		Recursively registers all marking menu layout files with the extension .markingmenu and loads the data with
		a marking menu layout instance and adds it to the marking menu layouts cache.

		:param str env: environment variable name.
		:raises errors.InvalidMarkingMenuFileFormatError: if the marking menu layout file has an invalid format.
		"""

		paths = os.environ.get(env, '').split(os.pathsep)
		for path in paths:
			if os.path.isdir(path):
				for root, _, files in os.walk(path):
					for f in files:
						layout_file = os.path.join(root, f)
						try:
							if f.endswith(consts.MARKING_MENU_LAYOUT_EXTENSION):
								data = yamlio.read_file(layout_file)
								self._layouts[data['id']] = markingmenu.MarkingMenuLayout(**data)
						except ValueError:
							raise errors.InvalidMarkingMenuFileFormatError(
								f'Layout file "{layout_file}" is invalid possible due to the formatting')
			elif path.endswith(consts.MARKING_MENU_LAYOUT_EXTENSION):
				try:
					data = yamlio.read_file(path)
					self._layouts[data['id']] = markingmenu.MarkingMenuLayout(**data)
				except ValueError:
					raise errors.InvalidMarkingMenuFileFormatError(
						f'Layout file "{path}" is invalid possible due to the formatting')

	def has_menu(self, menu_id: str) -> bool:
		"""
		Returns whether menu with given ID is registered.

		:param str menu_id: menu ID.
		:return: True if menu with given ID is registered; False otherwise.
		:rtype: bool
		"""

		found_menu = self._menu_factory.get_plugin_from_id(menu_id)
		return not found_menu or menu_id not in self._layouts

	def menu_type(self, menu_id: str) -> int:
		"""
		Returns the marking menu type for the given menu id.

		:param str menu_id: marking menu id to get type of.
		:return: marking menu type.
		:rtype: int
		"""

		if self._menu_factory.get_plugin_from_id(menu_id):
			return MarkingMenusManager.DYNAMIC_MARKING_MENU_LAYOUT_TYPE

		return MarkingMenusManager.STATIC_MARKING_MENU_LAYOUT_TYPE
