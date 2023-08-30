from __future__ import annotations

import typing
from typing import List

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.widgets.graphics import DropScene, EditableDropScene


class PreRefreshEvent:
	def __init__(self, *args, nodes: List[str]):
		self.args = args
		self.nodes = nodes
		self.current_index = -1
		self.result = False


class RefreshEvent:
	def __init__(self, group_names: List[str], current_group_name: str, current_index: int):
		self.group_names = group_names
		self.current_group_name = current_group_name
		self.current_index = current_index
		self.result = False


class LoadPickerNodeToMapEvent:
	def __init__(
			self, nodes: List[str], character_names: List[str], subsets: List[str], sizes: List[str],
			use_prefixes: List[bool], prefixes: List[str], referenced: List[bool]):
		self.nodes = nodes
		self.character_names = character_names
		self.subsets = subsets
		self.sizes = sizes
		self.use_prefixes = use_prefixes
		self.prefixes = prefixes
		self.referenced = referenced
		self.result = False


class PreCreateMapEvent:
	def __init__(self, group_name: str, map_name: str):
		self.group_name = group_name
		self.map_name = map_name
		self.result = False


class CreateMapEvent:
	def __init__(self, map_name: str, map_width: int, map_height: int):
		self.map_name = map_name
		self.map_width = map_width
		self.map_height = map_height
		self.use_background_image = False
		self.scene = None					# type: DropScene | EditableDropScene
		self.result = False


class PreAssignDataToNodeEvent:
	def __init__(self, group_name: str, specific_map: str):
		self.group_name = group_name
		self.specific_map = specific_map
		self.index = -1
		self.total_maps = 0
		self.views = []
		self.map_names = []
		self.result = False


class AssignDataToNodeEvent:
	def __init__(self, group_name: str, specific_map: str):
		self.group_name = group_name
		self.specific_map = specific_map
		self.picker_node = ''
		self.is_referenced = False
		self.index = -1
		self.result = False


class PreMatchPrefixToMapEvent:
	def __init__(self, group_name: str, index: int):
		self.group_name = group_name
		self.index = index
		self.map_name = ''
		self.result = False


class MatchPrefixToMapEvent:
	def __init__(self, group_name: str, picker_node: str, use_prefix: bool, prefix: str):
		self.group_name = group_name
		self.picker_node = picker_node
		self.use_prefix = use_prefix
		self.prefix = prefix
		self.result = False


class PreLoadMapEvent:
	def __init__(self, index: int):
		self.index = index
		self.picker_node = ''
		self.result = False


class LoadMapEvent:
	def __init__(self):
		self.result = False
