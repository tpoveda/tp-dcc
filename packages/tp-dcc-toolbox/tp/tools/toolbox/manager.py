from __future__ import annotations

import os
import typing
from typing import Tuple, List, Dict, Type

from tp.core import log, dcc
from tp.common import plugin
from tp.common.python import yamlio, color
from tp.tools.toolbox.widgets import toolui

if dcc.is_maya():
	from tp.tools.toolbox.maya import toolui as maya_toolui

if typing.TYPE_CHECKING:
	from tp.tools.toolbox.view import ToolBoxWindow

logger = log.tpLogger


class ToolUisManager:
	"""
	Manager class that holds all registered Tool UIs classes.
	"""

	TOOL_UIS_ENV = 'TPDCC_TOOL_UI_PATHS'
	TOOL_UIS_TOOLBOX_ENV = 'TPDCC_TOOL_UI_TOOLBOX_PATHS'

	def __init__(self):
		super().__init__()

		self._tool_ui_classes = {}

		# List of available toolbox groups retrieved from .toolbox files with the following format:
		# {
		# 	"type": "assets",
		# 	"name": "Assets",
		# 	"color": [85, 127, 248],
		# 	"hueShift": 0,
		# 	"toolUis": ["tp.utility.scenebrowser"]
		# }
		# ,
		# ...
		self._toolbox_groups = []				# type: List[Dict]

		if dcc.is_maya():
			interfaces = [maya_toolui.MayaToolUiWidget, toolui.ToolUiWidget]
		else:
			interfaces = [toolui.ToolUiWidget]
		self._tool_uis_factory = plugin.PluginFactory(interface=interfaces, plugin_id='id', name='ToolUIs')

		self.discover_tool_uis()

	@classmethod
	def instance(cls) -> ToolUisManager:
		"""
		Returns ToolUisManager instance.

		:return: ToolUisManager instance.
		:rtype: ToolUisManager
		"""

		global _TOOLS_UI_MANAGER_INSTANCE
		if _TOOLS_UI_MANAGER_INSTANCE is None:
			_TOOLS_UI_MANAGER_INSTANCE = ToolUisManager()

		return _TOOLS_UI_MANAGER_INSTANCE

	@classmethod
	def open_tool_ui(cls, tool_ui_id: str, position: Tuple[int, int] | None = None) -> ToolBoxWindow | None:
		"""
		Opens tool Ui instance that matches given id.

		:param str tool_ui_id: tool Ui id of the tool ui we want to open.
		:param position:
		:return:
		"""

		# import here to avoid cyclic imports
		from tp.tools.toolbox import view

		tool_opened = view.run_tool_ui(tool_ui_id, log_warning=False)

		toolbox_window = None
		if not tool_opened:
			from tp.core.managers import tools
			tools_manager = tools.ToolsManager.load()
			tool_ui_ids = [tool_ui_id]
			toolbox_window = tools_manager.launch_tool_by_id(
				'tp.tools.toolbox', tool_ids_to_run=tool_ui_ids, position=position)

		return toolbox_window

	def discover_tool_uis(self) -> bool:
		"""
		Searches the Tool UI classes registered in manager environment variable "TPDCC_TOOL_UI_PATHS"

		:return: True if Tool UI paths where discovered; False otherwise.
		:rtype: bool
		"""

		self.register_toolbox_files()

		paths = os.environ.get(self.TOOL_UIS_ENV, '').split(os.pathsep)
		if not paths:
			logger.warning(f'No Tool UIs paths found for "{self.TOOL_UIS_ENV}"')
			return False

		self._tool_uis_factory.register_paths(paths)

		for too_ui_class in self._tool_uis_factory.plugins():
			self._tool_ui_classes[too_ui_class.id] = too_ui_class

		return True

	def register_toolbox_files(self):
		"""
		Finds all available Tool Ui configuration files and merges the data found into one data structure.
		"""

		config_paths = os.getenv(self.TOOL_UIS_TOOLBOX_ENV, '')
		config_paths = [config_path for config_path in config_paths.split(os.pathsep) if os.path.isfile(config_path)]
		for config_path in config_paths:
			config_data = yamlio.read_file(config_path)
			toolbox_groups = config_data.get('toolboxGroups', None)
			if toolbox_groups:
				self._toolbox_groups += toolbox_groups

		self._toolbox_groups.sort(key=lambda x: x['name'])

	def group_types(self) -> List[str]:
		"""
		Returns a list of all available toolbox group types.

		:return: list of toolbox group types.
		:rtype: List[str]
		"""

		return [group['type'] for group in self._toolbox_groups]

	def groups_data(self, show_hidden: bool = False) -> List[Dict]:
		"""
		Returns toolbox groups data within a list.

		:param bool show_hidden: whether to include hidden groups.
		:return: list of groups data.
		:rtype: List[Dict]
		"""

		return [group for group in self._toolbox_groups if show_hidden or group.get('hidden') is not True]

	def group_names(self) -> List[str]:
		"""
		Returns a list of all available toolbox group names.

		:return: list of toolbox group names.
		:rtype: List[str]
		"""

		return [group['name'] for group in self._toolbox_groups]

	def group_type(self, group_name: str) -> str | None:
		"""
		Returns the toolbox group type associated with given toolbox group name.

		:param str group_name: name of the toolbox group to get type of. e.g: "Assets" -> "assets"
		:return: group type of the given group name.
		:rtype: str or None
		"""

		found_type = None
		for group in self._toolbox_groups:
			if group['name'] == group_name:
				found_type = group['type']
				break

		return found_type

	def group_color(self, group_type: str) -> List[int, int, int] | None:
		"""
		Returns the toolbox group color associated with given toolbox group type.

		:param str group_type: group type to get color of ("Assets", "Rigging", "Animation", ...).
		:return: found toolbox group color.
		:rtype: List[int, int, int] or None
		"""

		found_color = None
		for group in self._toolbox_groups:
			if group['type'] == group_type:
				found_color = group['color']
				break

		return found_color

	def group_from_tool_ui(self, tool_ui_id: str, show_hidden: bool = False) -> str | None:
		"""
		Returns the toolbox group type based on the given tool Ui id.

		:param str tool_ui_id: id of the tool whose toolbox group type we want to retrieve.
		:param bool show_hidden: whether to show hidden tool Uis.
		:return: toolbox group type.
		:rtype: str or None
		"""

		found_group_type = None
		for group in self.groups_data(show_hidden=show_hidden):
			for _tool_ui_id in group['toolUis']:
				if _tool_ui_id == tool_ui_id:
					found_group_type = group['type']
					break

		return found_group_type

	def tool_ui_ids(self, group_type: str) -> List[str]:
		"""
		Returns a list of all available tool UI IDs under the given group type.

		:param str group_type: group type to get tool UI IDs of ("Assets", "Rigging", "Animation", ...).
		:return: found tool UIs IDs.
		:rtype: List[str]
		"""

		for toolbox_group in self._toolbox_groups:
			if toolbox_group['type'] == group_type:
				return toolbox_group['toolUis']

	def tool_uis(self, group_type: str) -> List[Type]:
		"""
		Returns list of tool UI classes under the given group type.

		:param str group_type: group type to get tool UI classes of ("Assets", "Rigging", "Animation", ...).
		:return: found tool UIs classes.
		:rtype: List[Type]
		:raises TypeError: if group_type argument is empty.
		"""

		if not group_type:
			raise TypeError('"group_type" argument must not be empty!')

		tool_ui_ids = self.tool_ui_ids(group_type)
		found_tool_ui_classes = []
		for tool_ui_id in tool_ui_ids:
			tool_ui_class = self.tool_ui(tool_ui_id)
			if tool_ui_class:
				found_tool_ui_classes.append(tool_ui_class)

		return found_tool_ui_classes

	def tool_ui(self, tool_ui_id: str) -> Type | None:
		"""
		Returns tool UI class based on given id.

		:param str tool_ui_id: ID of the tool UI class to find.
		:return: found tool ui class with given ID.
		:rtype: Type or None
		"""

		result = self._tool_ui_classes.get(tool_ui_id)
		if result is None:
			logger.warning('"{}" tool UI not found!')

		return result

	def tool_ui_color(self, tool_ui_id: str) -> Tuple[int, int, int] | None:
		"""
		Returns the color for the tool ui with the given id.

		:param str tool_ui_id: ID of the tool UI class to find color for.
		:return: tool Ui color.
		:rtype: Tuple[int, int, int] or None
		"""

		for group in self._toolbox_groups:
			if tool_ui_id in group['toolUis']:
				index = group['toolUis'].index(tool_ui_id)
				group_color = tuple(group['color'])
				hue_shift = group['hueShift'] * (index + 1)
				return tuple(color.hue_shift(group_color, hue_shift))

		return 255, 255, 255


_TOOLS_UI_MANAGER_INSTANCE = None			# type: ToolUisManager
