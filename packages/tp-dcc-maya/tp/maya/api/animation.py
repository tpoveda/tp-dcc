#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya API Anim Curves
"""

import maya.cmds as cmds

import maya.api.OpenMayaAnim as OpenMayaAnim

from tp.common.python import helpers
from tp.maya.api import consts
from tp.maya.om import contexts, animation


def keyframes_for_node(node, attributes, default_keyframes=None, bake_every_frame=False, frame_range=None):
	"""
	Returns the key frames, rotation order and name for the node based on given arguments.

	:param tp.maya.api.DagNode node: animated node to get keyframes of.
	:param list(str) attributes: list of attribute name sto take into account when reading keyframes.
	:param default_keyframes:
	:param bool bake_every_frame: whether all frames between the start and end frame will be baked.
	:param list(int, int) frame_range: start and end range to bake. If None, only existing keys will be updated.
	:return: dictionary containing a list of keys for the given attributes, the rotation order for the node and the
		node name.
	:rtype: dict
	..note:: if bake_every_frame is True and frame_range is not None then the provided default is returned. This is due
		to the need to cache the key list to optimise the function across multiple requests. When frame_range is None
		and bake_every_frame is True, then the function will query the min and max keyFrames for the attributes and
		return all keyFrames on whole numbers between them.
	"""

	default_keyframes = helpers.force_list(default_keyframes)
	node_name = node.fullPathName()
	if bake_every_frame:
		if frame_range:
			# get every frame between the given frame range
			rotation_keys = default_keyframes
		else:
			# grab every frame between the minimum and maximum keys
			rotation_keys = cmds.keyframe(node_name, attribute=attributes, query=True, timeChange=True)
			if rotation_keys:
				rotation_keys = list(range(int(min(rotation_keys)), int(max(rotation_keys)) + 1))
	elif frame_range:
		# not baking every frame, just the keys within the given range
		rotation_keys = cmds.keyframe(node_name, time=tuple(frame_range), attribute=attributes, query=True, timeChange=True)
	else:
		# grab all the current keys
		rotation_keys = cmds.keyframe(node, attribute=attributes, query=True, timeChange=True)

	return {
		'keys': set(rotation_keys or list()),
		'rotationOrder': node.rotationOrder(),
		'name': node_name
	}


def iterate_keyframes_for_nodes(nodes, attributes, bake_every_frame=False, frame_range=None):
	"""
	Generator function that iterates over all keyframe and rotations order sof given nodes.

	:param list(tp.maya.api.base.DagNode) nodes: list of nodes.
	:param list(str) attributes: list of attribute name sto take into account when reading keyframes.
	:param bool bake_every_frame: whether all frames between the start and end frame will be baked.
	:param list(int, int) frame_range: start and end range to bake. If None, only existing keys will be updated.
	:return: generator function where each element contains a dictionary with the keys and the rotation orders.
	:rtype: generator(dict)
	"""

	all_key_frames = helpers.force_list(frame_range)
	if all_key_frames:
		all_key_frames[-1] = all_key_frames[-1] + 1
		all_key_frames = list(range(*tuple(all_key_frames)))

	for node in nodes:
		yield node, keyframes_for_node(
			node, attributes=attributes, default_keyframes=all_key_frames, bake_every_frame=bake_every_frame,
			frame_range=frame_range)


def set_rotation_order_over_frames(nodes, rotation_order, bake_every_frame=False, frame_range=None):
	"""
	Changes the rotation order of the given nodes while preserving animation.

	:param list(tp.maya.api.base.DagNode) nodes: DAG nodes to set rotation orders of.
	:param int rotation_order: rotation order to set.
	:param bool bake_every_frame: whether to bake all frames between start and end.
	:param list(float) or None frame_range: optional start and end range to bake. If None, only existing keys will be
		updated.
	"""

	rotation_order_name = consts.kRotateOrderNames[rotation_order]
	all_key_times = set()
	unkeyed_objects = set()
	keyed_objects_mapping = dict()

	for node, node_key_info in iterate_keyframes_for_nodes(
			nodes, ['rotate', 'rotateOrder'], bake_every_frame=bake_every_frame, frame_range=frame_range):
		if node_key_info['keys']:
			all_key_times.update(node_key_info['keys'])
			keyed_objects_mapping[node] = node_key_info
		else:
			unkeyed_objects.add(node_key_info['name'])

	if keyed_objects_mapping:
		all_key_times = list(all_key_times)
		all_key_times.sort()

		with contexts.maintain_time():

			# force set key frames on all rotation attribute so that we respect the original state
			for context in animation.iterate_frames_dg_context(all_key_times):
				frame_time = context.getTime()
				frame = frame_time.value
				OpenMayaAnim.MAnimControl.setCurrentTime(frame_time)
				for node, info in keyed_objects_mapping.items():
					if frame not in info['keys']:
						continue
					node_name = info['name']
					cmds.setKeyframe(node_name, attribute='rotate', preserveCurveShape=True, respectKeyable=True)
					if node.rotateOrder.isAnimated():
						cmds.setKeyframe(node_name, attribute='rotateOrder', preserveCurveShape=True)

			# actual reordering and keyframing to new rotation values
			for context in animation.iterate_frames_dg_context(all_key_times):
				frame_time = context.getTime()
				frame = frame_time.value
				OpenMayaAnim.MAnimControl.setCurrentTime(frame_time)
				for node, info in keyed_objects_mapping.items():
					if frame not in info['keys']:
						continue
					node_name = info['name']
					node.setRotationOrder(rotation_order)
					cmds.setKeyframe(node_name, attribute='rotate', preserveCurveShape=True, respectKeyable=True)
					if node.rotateOrder.isAnimated():
						cmds.setKeyframe(node_name, attribute='rotateOrder', preserveCurveShape=True)
					node.setRotationOrder(rotate_order=info['rotationOrder'], preserve=True)

		# set using cmds to get undo
		for node_info in keyed_objects_mapping.values():
			cmds.xform(node_info['name'], preserve=False, rotateOrder=rotation_order_name)

	for node in unkeyed_objects:
		cmds.xform(node, preserve=True, rotateOrder=rotation_order_name)
