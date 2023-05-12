from __future__ import annotations

import maya.cmds as cmds

from tp.core import log
from tp.maya import api

from tp.libs.rig.crit.maya.library.functions import names

logger = log.rigLogger


def joint_chain(start_joint: api.DagNode, end_joint: api.DagNode | None = None) -> list[api.DagNode]:
	"""
	Returns the joint chain from the given start joint.

	:param start_joint:
	:param end_joint:
	:return: list of joints from given start joint to end joint.
	:rtype: list[api.DagNode]
	"""

	chain = list(start_joint.iterateChildren(node_types=(api.OpenMaya.MFn.kJoint,)))
	chain.reverse()
	if not end_joint:
		return chain

	cut_chain = list()
	for joint in chain:
		if joint.name() in end_joint.fullPathName().split('|'):
			cut_chain.append(joint)

	return cut_chain


def validate_rotations(joint_chain: list[api.DagNode]) -> bool:
	"""
	Returns whether all joints of the given chain have no rotations.

	:param list[api.DagNode] joint_chain: list of joints to validate.
	:return: True if all joints are valid; False otherwise.
	:rtype: bool
	"""

	is_valid = True
	for joint in joint_chain:
		if joint.rotateX.asFloat() > 0.0:
			logger.warning(f'Non zero rotationX on joint {joint}')
			is_valid = False
		if joint.rotateY.asFloat() > 0.0:
			logger.warning(f'Non zero rotationY on joint {joint}')
			is_valid = False
		if joint.rotateZ.asFloat() > 0.0:
			logger.warning(f'Non zero rotationZ on joint {joint}')
			is_valid = False

	return is_valid


def duplicate_chain(
		new_joint_name: str | list[str], new_joint_side: str, new_joint_suffix: str = 'jnt',
		original_chain: list[api.DagNode] | None = None, start_joint: api.DagNode | None = None,
		end_joint: api.DagNode | None = None, new_parent: api.DagNode | None = None) -> list[api.DagNode]:
	"""

	:param new_joint_name:
	:param new_joint_side:
	:param new_joint_suffix:
	:param original_chain:
	:param start_joint:
	:param end_joint:
	:param new_parent:
	:return:
	"""

	original_chain = original_chain or joint_chain(start_joint, end_joint=end_joint)
	new_chain = cmds.duplicate([jnt.fullPathName() for jnt in original_chain], po=True, rc=True)
	new_chain = [api.node_by_name(name) for name in new_chain]

	# for new_joint in new_chain:
	# 	new_joint_name = names.generate_name(new_joint_name, new_joint_side, new_joint_suffix)
	# 	cmds.rename(new_joint, new_joint_name)
	# if new_parent:

