from __future__ import annotations

from typing import List

import maya.cmds as cmds


def filter_map_node(nodes: List[str], character: str, subset: str) -> str | None:

	found_node = None
	for node in nodes:
		if cmds.getAttr(f'{node}.characterName') == character and cmds.getAttr(f'{node}.subSetName') == subset:
			found_node = node
			break

	return found_node


def filter_map_nodes_character(nodes: List[str], character: str) -> List[str]:

	found_nodes = []
	for node in nodes:
		if cmds.getAttr(f'{node}.characterName') == character:
			found_nodes.append(node)

	return found_nodes


def default_string_attributes() -> List[str]:
	"""
	Returns a list of default string attribute names for map node.

	:return: list of attribute names.
	:rtype: List[str]
	"""

	return ['type', 'position', 'size', 'color', 'command', 'node', 'channel', 'value', 'label', 'icon', 'hashcode']


def create_map_node(character: str, subset: str):

	new_node = cmds.createNode('geometryVarGroup', n=f'animPicker_{character}_{subset}')
	cmds.addAttr(new_node, ln='characterName', dt='string')
	cmds.addAttr(new_node, ln='subSetName', dt='string')
	cmds.addAttr(new_node, ln='prefix', dt='string')
	cmds.addAttr(new_node, ln='bgSize', dt='string')
	cmds.addAttr(new_node, ln='tabOrder', at='long')
	cmds.addAttr(new_node, ln='usePrefix', at='bool')
	cmds.addAttr(new_node, ln='useBgColor', at='bool')
	cmds.addAttr(new_node, ln='animPickerMap', at='bool')
	cmds.addAttr(new_node, ln='bgImage', dt='string')
	cmds.addAttr(new_node, ln='bgColor', dt='string')
	cmds.setAttr(f'{new_node}.characterName', character, type='string')
	cmds.setAttr(f'{new_node}.subSetName', subset, type='string')
	for attr_name in default_string_attributes():
		cmds.addAttr(new_node, ln=attr_name, dt='string', multi=True)
