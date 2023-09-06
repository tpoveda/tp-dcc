from __future__ import annotations

import maya.cmds as cmds

from tp.common.python import helpers


def root_node(node: str, type_name: str) -> str:
	"""
	Recursive function that traverse up the hierarchy until finding the first object that does not have a parent.

	:param api.DagNode node: DAG node name that is part of a hierarchy.
	:param str type_name: type to filter node by.
	:return: top level node.
	:rtype: str
	"""

	parent = helpers.first_in_list(cmds.listRelatives(node, fullPath=True, parent=True, type=type_name) or [])
	return root_node(parent, type_name) if parent else node
