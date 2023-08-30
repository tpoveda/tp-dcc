from __future__ import annotations

import ast
import traceback
from typing import Tuple, List

from overrides import override
import maya.cmds as cmds

from tp.core import log
from tp.tools.animpicker import controller
from tp.tools.animpicker.maya import utils


logger = log.modelLogger


class MayaAnimPickerController(controller.AnimPickerController):

	@override
	def filter_picker_nodes(self) -> List[str]:
		return [n for n in cmds.ls(type='geometryVarGroup') if cmds.objExists(f'{n}.animPickerMap')]

	@override
	def filter_map_nodes_character(self) -> List[str]:
		nodes = utils.filter_map_nodes_character(self.filter_picker_nodes(), self.state.group_name)
		nodes.sort(key=lambda x: cmds.getAttr(f'{x}.tabOrder'))

	@override
	def selected_node_names(self) -> List[str]:
		return cmds.ls(sl=True) or []

	@override
	def show_color_editor(self, color: Tuple[float, float, float]) -> Tuple[float, float, float]:
		return_str = cmds.colorEditor(rgb=color)
		color_values = [ast.literal_eval(c) for c in return_str.split()]
		return color_values[:3] if color_values[-1] == 1 else color

	@override
	def check_proper_channels(self) -> bool:
		try:
			command = self.state.command
			if command in ('Select', 'Key', 'Reset', 'Pose'):
				return True
			if command in ('Toggle', 'Range'):
				channels = cmds.channelBox('mainChannelBox', q=1, sma=1)
				if channels:
					node = cmds.ls(sl=True)[0]
					for ch in channels:
						if not cmds.attributeQuery(ch, n=node, re=True):
							self.warning.emit(f'Attribute does not have a range: {ch}')
							return False
					return True
				else:
					self.warning.emit('Please select attribute in Channel Box first, then try again.')
					return False
		except:
			logger.error(traceback.format_exc())

		return False

	@override
	def undo_open_close(self, undo_open: bool):
		if undo_open:
			cmds.undoInfo(ock=True)
		else:
			cmds.undoInfo(cck=True)

	@override
	def find_picker_node(self, subset: str, index: int | None = None) -> str:
		picker_node = utils.filter_map_node(
			nodes=self.filter_picker_nodes(), character=self.state.group_name, subset=subset)
		if picker_node:
			cmds.setAttr(f'{picker_node}.tabOrder', index)

		return picker_node

	@override
	def create_picker_node(self, specific_map: str = '') -> str:
		picker_node = utils.filter_map_node(
			nodes=self.filter_picker_nodes(), character=self.state.group_name, subset=specific_map)
		if not picker_node:
			picker_node = utils.create_map_node(character=self.state.group_name, subset=specific_map)

		return picker_node

	@override
	def is_node_referenced(self, node_name: str) -> bool:
		return cmds.referenceQuery(node_name, isNodeReferenced=True)

	@override
	def picker_node_attribute(self, picker_node: str, attribute_name: str) -> Any:
		return cmds.getAttr(f'{picker_node}.{attribute_name}')
