from __future__ import annotations

from typing import List, Dict

from overrides import override

import maya.cmds as cmds

from tp.core import log
from tp.tools.modelchecker import controller

logger = log.modelLogger


class MayaModelCheckerController(controller.ModelCheckerController):

	@override
	def top_node(self) -> str:

		selection = cmds.ls(selection=True)
		if not selection:
			logger.warning('Please select a node.')
			return ''

		return selection[0]

	@override
	def select_nodes(self, nodes: List[str]):
		"""
		Selects all given nodes.

		:param List[str] nodes: list of node names to select.
		"""

		cmds.select(nodes)

	@override(check_signature=False)
	def filter_nodes(self, top_node: str | None = None) -> List[str]:

		selection = cmds.ls(sl=True, type='transform')
		if selection:
			nodes = []
			for node in selection:
				relatives = cmds.listRelatives(node, allDescendents=True, type='transform')
				if relatives:
					nodes.extend(relatives)
				nodes.append(node)
		elif not top_node:
			nodes = self.filter_get_all_nodes()
		else:
			nodes = self.filter_get_top_node(top_node)

		self.filteredNodes.emit(nodes)

		return nodes

	@override
	def run_commands(self, command_names: List[str], nodes: List[str]) -> Dict:

		results = {}

		for command_name in command_names:
			command_function = self.command_function(command_name)
			if not command_function:
				logger.warning(f'Skipping command check execution: {command_name}!')
				results[command_name] = [None]
			else:
				errors = command_function(nodes)
				results[command_name] = errors
			self._results[command_name] = results[command_name]

		return results

	def filter_get_top_node(self, top_node: str) -> List[str]:
		"""
		Returns valid node names based in the hierarchy of the given top node name.

		:param str top_node: top node name.
		:return: list of valid node names.
		:rtype: List[str]
		"""

		nodes = []
		if top_node and cmds.objExists(top_node):
			nodes.append(top_node)
			children = cmds.listRelatives(top_node, allDescendents=True, type='transform')
			if children:
				nodes.extend(children)
		else:
			nodes = self.filter_get_all_nodes()

		self.filteredTopNode.emit(top_node)

		return nodes

	def filter_get_all_nodes(self) -> List[str]:
		"""
		Returns all valid node names within current scene.

		:return: list of valid node names.
		:rtype: List[str]
		"""

		all_nodes = cmds.ls(transforms=True)
		all_valid_nodes = []
		for node in all_nodes:
			if node not in ['front', 'persp', 'top', 'side']:
				all_valid_nodes.append(node)

		return all_valid_nodes

