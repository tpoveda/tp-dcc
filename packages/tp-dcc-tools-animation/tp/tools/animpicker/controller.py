from __future__ import annotations

from typing import Tuple, List, Any

from tp.core import log
from tp.common.python import path, decorators
from tp.common.qt.api import Signal, Controller
from tp.tools.animpicker import events

logger = log.modelLogger


class AnimPickerController(Controller):

	warning = Signal(str)
	preRefresh = Signal(events.PreRefreshEvent)
	doRefresh = Signal(events.RefreshEvent)
	loadPickerNodeToMap = Signal(events.LoadPickerNodeToMapEvent)
	preCreateMap = Signal(events.PreCreateMapEvent)
	createMap = Signal(events.CreateMapEvent)
	preAssignDataToNode = Signal(events.PreAssignDataToNodeEvent)
	assignDataToNode = Signal(events.AssignDataToNodeEvent)
	preMatchPrefixToMap = Signal(events.PreMatchPrefixToMapEvent)
	matchPrefixToMap = Signal(events.MatchPrefixToMapEvent)
	preLoadMap = Signal(events.PreLoadMapEvent)
	loadMap = Signal(events.LoadMapEvent)

	def __init__(self):
		super().__init__()

	@decorators.abstractmethod
	def filter_picker_nodes(self) -> List[str]:
		"""
		Returns a list with all picker nodes within current DCC scene.

		:return: list of picker node names.
		:rtype: List[str]
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def filter_map_nodes_character(self) -> List[str]:
		"""
		Returns filtered map nodes character.

		:return: map nodes character.
		:rtype: List[str]
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def selected_node_names(self) -> List[str]:
		"""
		Returns a list of selected node names.

		:return: node names.
		:rtype: List[str]
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def show_color_editor(self, color: Tuple[float, float, float]) -> Tuple[float, float, float]:
		"""
		Shows color editor.

		:param Tuple[float, float, float] color: 0.0 to 1.0 float RGB default color.
		:return: selected color.
		:rtype: Tuple[float, float, float]
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def check_proper_channels(self) -> bool:
		"""
		Returns whether necessary attribute channels for current command to create are selected.

		:return: True if necessary attribute channels are selected; False otherwise.
		:rtype: bool
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def undo_open_close(self, undo_open: bool):
		"""
		Enables or disables undo queue.

		:param str undo_open: whether to enable undo.
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def find_picker_node(self, subset: str, index: int) -> str:
		"""
		Finds picker witihn given subset.

		:param str subset: subset name.
		:param int index: picker index.
		:return: found picker node name.
		:rtype: str
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def create_picker_node(self, specific_map: str = '') -> str:
		"""
		Creates a picker node within current DCC scene.

		:param str specific_map: map we want to create picker node for.
		:return: newly created picker node name.
		:rtype: str
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def is_node_referenced(self, node_name: str) -> bool:
		"""
		Returns whether given node is referenced.

		:param str node_name: name of the node to check.
		:return: True if node is being referenced; False otherwise.
		:rtype: bool
		"""

		raise NotImplementedError

	@decorators.abstractmethod
	def picker_node_attribute(self, picker_node: str, attribute_name: str) -> Any:
		"""
		Returns the attribute value of within given picker node.

		:param str picker_node: picker node name.
		:param str attribute_name: picker attribute name whose value we want to retrieve.
		:return: attribute value.
		:rtype: Any
		"""

		raise NotImplementedError

	def refresh(self, *args):
		"""
		Refreshes UIs.
		"""

		nodes = self.filter_picker_nodes()
		pre_event = events.PreRefreshEvent(*args, nodes=nodes)
		self.preRefresh.emit(pre_event)
		if not pre_event.result:
			return
		self.load_bookmark()
		group_name = self.state.group_name
		character_names = [self.picker_node_attribute(picker_node, 'characterName') for picker_node in nodes]
		if not character_names:
			return
		character_names = list(set(character_names))
		character_names.sort()
		index = not character_names.count(group_name) and -1 or character_names.index(group_name)
		character_name = index >= 0 and character_names[index] or character_names[0]
		self.load_picker_node_to_map()
		event = events.RefreshEvent(
			group_names=character_names, current_group_name=character_name, current_index=pre_event.current_index)

		self.doRefresh.emit(event)

	def load_bookmark(self):
		pass

	def load_picker_node_to_map(self):
		nodes = self.filter_map_nodes_character()
		character_names = [self.picker_node_attribute(picker_node, 'characterName') for picker_node in nodes]
		subsets = [self.picker_node_attribute(picker_node, 'subSetName') for picker_node in nodes]
		sizes = [self.picker_node_attribute(picker_node, 'bgSize') for picker_node in nodes]
		use_prefixes = [self.picker_node_attribute(picker_node, 'usePrefix') for picker_node in nodes]
		prefixes = [self.picker_node_attribute(picker_node, 'prefix') for picker_node in nodes]
		referenced = [self.is_node_referenced(picker_node) for picker_node in nodes]

		event = events.LoadPickerNodeToMapEvent(
			nodes=nodes, character_names=character_names, subsets=subsets, sizes=sizes, use_prefixes=use_prefixes,
			prefixes=prefixes, referenced=referenced)
		self.loadPickerNodeToMap.emit(event)

	def create_new_map(self) -> bool:
		"""
		Creates a new animation picker map.

		:return: True if new map was created successfully; False otherwise.
		:rtype: bool
		"""

		if not self.state.group_name:
			self.warning.emit('Need character name!')
			return False
		if not self.state.map_name:
			self.warning.emit('Need map name!')
			return False

		pre_create_map_event = events.PreCreateMapEvent(
			group_name=self.state.group_name, map_name=self.state.map_name)
		self.preCreateMap.emit(pre_create_map_event)
		if not pre_create_map_event.result:
			self.warning.emit(f'Map name already exists: {pre_create_map_event.map_name}')
			return False

		create_map_event = events.CreateMapEvent(
			map_name=self.state.map_name, map_width=self.state.map_width, map_height=self.state.map_height)
		self.createMap.emit(create_map_event)
		if not create_map_event.result:
			return False

		if create_map_event.use_background_image:
			image_path = self.state.image_path
			if path.is_file(image_path):
				create_map_event.scene.set_background_pixmap(image_path)

		if create_map_event.result:
			self.assign_data_to_node()

		return True

	def assign_data_to_node(self, specific_map: str = '') -> List[str]:
		"""
		Assigns current map data to a node within current DCC scene.

		:param str specific_map: override map name to save data for.
		:return: list of saved node names.
		:rtype: List[str]
		"""

		result = []
		self.undo_open_close(True)
		try:
			pre_event = events.PreAssignDataToNodeEvent(group_name=self.state.group_name, specific_map=specific_map)
			self.preAssignDataToNode.emit(pre_event)
			if not pre_event.result:
				return []
			event = events.AssignDataToNodeEvent(group_name=self.state.group_name, specific_map=specific_map)
			if specific_map:
				picker_node = self.create_picker_node(specific_map=specific_map)
				is_referenced = self.is_node_referenced(picker_node)
				event.picker_node = picker_node
				event.is_referenced = is_referenced
				event.index = pre_event.index
				self.assignDataToNode.emit(event)
				result.append(picker_node)
			else:
				for i in range(pre_event.total_maps):
					map_name = pre_event.map_names[i]
					view = pre_event.views[i]
					picker_node = self.find_picker_node(map_name, i)
					if not view.loaded:
						continue
					event = events.AssignDataToNodeEvent(group_name=self.state.group_name, specific_map=map_name)
					if not picker_node:
						picker_node = self.create_picker_node(map_name)
					is_referenced = self.is_node_referenced(picker_node)
					event.picker_node = picker_node
					event.is_referenced = is_referenced
					event.index = i
					self.assignDataToNode.emit(event)
					result.append(picker_node)
		finally:
			self.undo_open_close(False)

		return result

	def match_prefix_to_map(self, index: int):
		"""
		Retrieves whether picker with given index should use prefix and the prefix to use.

		:param int index: picker index.
		"""

		pre_event = events.PreMatchPrefixToMapEvent(group_name=self.state.group_name, index=index)
		self.preMatchPrefixToMap.emit(pre_event)
		if not pre_event.result:
			return
		picker_node = self.find_picker_node(pre_event.map_name)
		if not picker_node:
			return
		use_prefix = self.picker_node_attribute(picker_node, 'usePrefix')
		prefix = self.picker_node_attribute(picker_node, 'prefix')
		event = events.MatchPrefixToMapEvent(
			group_name=self.state.group_name, picker_node=picker_node, use_prefix=use_prefix, prefix=prefix)
		self.matchPrefixToMap.emit(event)

	def load_map(self, index: int):
		"""
		Loads picker map with given index.

		:param int index: picker index.
		"""

		pre_event = events.PreLoadMapEvent(index=index)
		self.preLoadMap.emit(pre_event)
		if not pre_event.result:
			return





