from __future__ import annotations

import maya.cmds as cmds


def reset_transform_attributes(
		node_name: str, translate: bool = True, rotate: bool = True, scale: bool = True, visibility: bool = False):
	"""
	Resets teh transforms of the given node name.

	:param str node_name: name of the node whose transform attributes we want to reset.
	:param bool translate: whether to reset translate transform attributes.
	:param bool rotate: whether to reset rotate transform attributes.
	:param bool scale: whether to reset scale transform attributes.
	:param bool visibility: whether to reset visibility attribute.
	"""

	if translate:
		cmds.setAttr(f'{node_name}.translate', 0.0, 0.0, 0.0)
	if rotate:
		cmds.setAttr(f'{node_name}.rotate', 0.0, 0.0, 0.0)
	if scale:
		cmds.setAttr(f'{node_name}.scale', 1.0, 1.0, 1.0)
	if visibility:
		cmds.setAttr(f'{node_name}.visibility', 1.0)
