# ! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with keyframes in Maya
"""

import maya.cmds as cmds

from tp.core import log
from tp.maya.cmds import attribute
from tp.maya.cmds.animation import timerange

logger = log.tpLogger


def is_auto_keyframe_enabled():
	"""
	Returns whether auto keyframe mode is enabled.

	:return: True if the auto keyframe functionality is enabled; False otherwise.
	:rtype: bool
	"""

	return cmds.autoKeyframe(query=True, state=True)


def set_auto_keyframe_enabled(flag):
	"""
	Sets whether auto keyframe functionality is enabled.

	:param bool flag: whether auto keyframe functionality is enabled.
	"""

	return cmds.autoKeyframe(edit=True, state=flag)


def find_first_node_keyframe(node):
	"""
	Returns the first keyed frame on the given node.

	:param str node: node name we want to get first keyed frame of.
	:return: first keyed frame on given node.
	:rtype: int
	"""

	return min(cmds.keyframe(node, query=True))


def find_last_node_keyframe(node):
	"""
	Returns the last keyed frame on the given node.

	:param str node: node name we want to get first keyed frame of.
	:return: first keyed frame on given node.
	:rtype: int
	"""

	return max(cmds.keyframe(node, query=True))


def node_key_range(node, frame_range=None):
	"""
	Returns the first and last keyed frame from the given PyMEL node that lies outside the given frame range.

	:param str node: node name to get key range of.
	:param tuple[int, int] or None frame_range: optional lowest frame range to compare against.
	:return: lowest and highest frame range.
	:rtype: tuple[int, int]
	"""

	start_frame = None
	end_frame = None

	if frame_range is None:
		frame_range = (None, None)

	first_key, last_key = frame_range

	history_nodes = cmds.listHistory(node, pruneDagObjects=True, leaf=False)
	anim_curves = cmds.ls(history_nodes, type='animCurve')
	if anim_curves:
		# NOTE: cmds.findKeyframe returns currentTime if no animation curves are given.
		first_key = cmds.findKeyframe(anim_curves, which='first')
		last_key = cmds.findKeyframe(anim_curves, which='last')

	# we use frame -10000 and -10001 as a special holder frame for keys used by tools.
	if first_key:
		start_frame = first_key if first_key < frame_range[0] or frame_range[0] is None else frame_range[0]
		start_frame = None if start_frame == -10000 or start_frame == -10001 else start_frame
	if last_key:
		end_frame = last_key if last_key > frame_range[1] or frame_range[1] is None else frame_range[1]
		end_frame = None if end_frame == -10000 or end_frame == -10001 else end_frame

	return start_frame, end_frame


def node_constraints_key_range(node, frame_range, _nodes_to_check=None):
	"""
	Returns the first and last keyed frame from the given PyMEL node that by checking its constraints.

	:param str node: node str to check.
	:param tuple[int, int] frame_range: start and end frame range to check.
	:param None _nodes_to_check: used internally by the function to check constraint in a quicker way.
	:return: lowest and highest frame range.
	:rtype: tuple[int, int]
	"""

	if _nodes_to_check is None:
		_nodes_to_check = list()

	first_frame, last_frame = frame_range
	if node not in _nodes_to_check:
		_nodes_to_check.append(node)
		constraint_list = list(set(cmds.listConnections(node, type='constraint', s=True, d=False)))
		for constraint in constraint_list:
			for constraint_node in list(
					set(cmds.listConnections(constraint.target, type='joint', s=True, d=False))):
				first_frame, last_frame = node_key_range(constraint_node, (first_frame, last_frame))
				# if no keys found we check hierarchy
				if first_frame is None and last_frame is None:
					first_frame, last_frame = node_hierarchy_key_range(constraint_node, first_frame, last_frame)
				first_frame, last_frame = node_constraints_key_range(
					constraint_node, first_frame, last_frame, _nodes_to_check)

	pair_blend_list = list(set([x for x in cmds.listConnections(node, s=True, d=False) if cmds.nodeType(x) == 'pairBlend']))
	for pair_blend in pair_blend_list:
		first_frame, last_frame = node_constraints_key_range(pair_blend, first_frame, last_frame, _nodes_to_check)

	return first_frame, last_frame


def node_hierarchy_key_range(node, frame_range):
	"""
	Returns the first and last keyed frame from the given PyMEL node that by checking its hierarchy in a recursive way.

	:param pm.PyNode node: PyMEL node to check.
	:param tuple(int, int) frame_range: start and end frame range to check.
	:return: lowest and highest frame range.
	:rtype: tuple(int, int)
	"""

	first_frame, last_frame = frame_range
	if node:
		first_frame, last_frame = node_key_range(node, (frame_range[0], frame_range[1]))
		# we search hierarchy until we find a new key range
		if first_frame == frame_range[0] and last_frame == frame_range[1]:
			first_frame, last_frame = node_hierarchy_key_range(node.getParent(), (first_frame, last_frame))

	return first_frame, last_frame


def shift_keys(node_list, shift_length=None):
	"""
	Shifts all keyframes on a set of objects by a given value. If no shift length is given it will zero the animation.

	:param PyNode node_list: A list of objects to shift the keyframes on.
	:param int shift_length: How much the animation should be shifted by.
	"""

	if not node_list:
		logger.warning('A valid node list is required to shift keys from.')
		return

	if not shift_length:
		min_frame, max_frame = timerange.times(node_list)
		if min_frame != 0:
			shift_length = min_frame*-1

	if shift_length:
		cmds.keyframe(node_list, timeChange=shift_length, relative=True)
	else:
		logger.warning('No keyframes were shifted as none were found.')


def anim_hold():
	"""
	Creates a held pose with two identical keys and flat tangents from the current keyframes by:
	"""

	curve_attribute_nams = list()
	curve_attribute_values = list()
	current_attribute_values = list()

	curves_active = cmds.keyframe(query=True, name=True)
	if not curves_active:
		logger.warning('No curves active')
		return

	current_time = cmds.currentTime(query=True)
	selected_curves = cmds.keyframe(query=True, name=True, selected=True)
	selected_curves = selected_curves or curves_active
	last_key = cmds.findKeyframe(time=(current_time + 1, current_time + 1), which='previous')
	for curve in selected_curves:
		curve_connection = cmds.listConnections(curve, plugs=True, source=False)[0]
		curve_attribute_nams.append(curve_connection)
		current_attribute_values.append(cmds.getAttr(curve_connection))
		curve_attribute_values.append(cmds.keyframe(curve, query=True, eval=True)[0])

	for i, curve in enumerate(selected_curves):
		is_last_key = cmds.keyframe(curve, time=(last_key, last_key), query=True, keyframeCount=True)
		if is_last_key != 1:
			logger.info('No hold set on {}, no source key on frame'.format(curve))
			continue

		equivalent_test =abs(current_attribute_values[i] - current_attribute_values[i]) <= 0.001
		if not equivalent_test:
			cmds.setKeyframe(
				curve, value=curve_attribute_values[i], time=(last_key, last_key),
				inTangentType='linear', outTangentType='linear')
		last_key = cmds.findKeyframe(curve, time=(current_time + 1, current_time + 1), which='previous')
		next_key = cmds.findKeyframe(curve, time=(current_time, current_time), which='next')
		cmds.keyTangent(curve, time=(last_key, last_key), inTangentType='auto', outTangentType='auto')
		cmds.copyKey(curve, time=(last_key, last_key))
		cmds.pasteKey(curve, time=(next_key, next_key))
		cmds.keyTangent(curve, time=(next_key, next_key), inTangentType='auto', outTangentType='auto')
		logger.info('Created hold on {}'.format(curve))


def toggle_and_key_visibility(node_names=None):
	"""
	Inverts the visibility of current selected nodes.

	:param list(str) or None node_names: nodes to toggle visibility. If None, current selected nodes will be taken into
		account.
	"""

	nodes_to_toggle = node_names or cmds.ls(sl=True)
	for node_name in nodes_to_toggle:
		attr_name = '{}.visibility'.format(node_name)
		if not attribute.is_settable(attr_name):
			logger.warning(
				'The visibility of the object {} is locked or connected, keyframe toggle skipped'.format(node_name))
			continue
		if cmds.getAttr(attr_name):
			cmds.setAttr(attr_name, False)
		else:
			cmds.setAttr(attr_name, True)
		cmds.setKeyframe(node_name, breakdown=False, hierarchy=False, attribute='visibility')