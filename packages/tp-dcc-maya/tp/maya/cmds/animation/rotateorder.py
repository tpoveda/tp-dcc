# ! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with rotate orders in Maya
"""

import math

import maya.cmds as cmds
import maya.api.OpenMayaAnim as OpenMayaAnim

from tp.core import log
from tp.common.python import helpers
from tp.common.math import scalar
from tp.maya.cmds import contexts
from tp.maya.cmds.animation import timerange
from tp.maya.om.animation import timerange as om_timerange

logger = log.tpLogger


class RotateOrder(object):
	"""
	Class that defines all available rotation orders in Maya as strings
	"""

	XYZ = 'XYZ'
	YZX = 'YZX'
	ZXY = 'ZXY'
	XZY = 'XZY'
	YXZ = 'YXZ'
	ZYX = 'ZYX'

	@staticmethod
	def get_all():
		return [RotateOrder.XYZ, RotateOrder.YZX, RotateOrder.ZXY, RotateOrder.XZY, RotateOrder.YXZ, RotateOrder.ZYX]

	@staticmethod
	def from_index(index):
		if not helpers.is_int(index):
			if index is not None and hasattr(index, 'index') and not callable(index.index):     # support for PyMEL enum
				index = index.index - 1
			else:
				return index

		return RotateOrder.get_all()[index]

	@staticmethod
	def to_index(rotate_order):
		return RotateOrder.get_all().index(str(rotate_order).upper())


def iterate_keyframe_rotation_orders_for_nodes(nodes, attributes, bake_every_frame=False, frame_range=None):
	"""
	Generator function that yields every keyframe and rotation orders for given nodes.

	:param list[str] nodes: list of node names.
	:param list[str] attributes: list of attribute names to take into account when reading key frames.
	:param bool bake_every_frame: whether all frames either on the timeline or between the start and end frame keys
		for the node should be baked.
	:param tuple[int, int] or None frame_range: the start and range to bake. If None, only existing keys will be
		updated.
	:return: generator function of iterated rotation orders.  {'keys': [], 'rotationOrder': int, 'node': None}
	:rtype: collections.Iterator[tuple[str, dict[]]]
	"""

	all_key_frames = frame_range or list()
	if all_key_frames:
		all_key_frames = list(all_key_frames)
		all_key_frames[-1] = all_key_frames[-1] + 1
		all_key_frames = list(range(*tuple(all_key_frames)))

	# first cache existing keyframes and rotation orders which will be used to loop over.
	for node in nodes:
		yield node, keyframe_rotation_orders_for_node(
			node,
			attributes=attributes,
			default_key_frames=all_key_frames,
			bake_every_frame=bake_every_frame,
			frame_range=frame_range
		)


def keyframe_rotation_orders_for_node(
		node, attributes, default_key_frames=None, bake_every_frame=False, frame_range=None):
	"""
	Returns the key frames, rotation order and name for the node based on given arguments.

	:param str node: animated node to read.
	:param list[str] attributes: list of attribute names to take into account when reading key frames.
	:param list[int] or None default_key_frames: default key frames to use when bake_every_frame is True and a frame
		range is provided.
	:param bool bake_every_frame: whether all frames either on the timeline or between the start and end frame keys
		for the node should be baked.
	:param tuple[int, int] or None frame_range: the start and range to bake. If None, only existing keys will be
		updated.
	:return: dict containing a unique flat list of keys for the given attributes.
	:rtype: dict
	"""

	default_key_frames = default_key_frames or list()
	if bake_every_frame:
		# grab every frame between the specified frame range
		if frame_range:
			key_frames = default_key_frames
		else:
			# grab every frame between the min and max keys
			key_frames = cmds.keyframe(node, attribute=attributes, query=True, timeChange=True)
			if key_frames:
				key_frames = list(range(int(min(key_frames)), int(max(key_frames))))
	# not baking every frame just the keys within the specified range
	elif frame_range:
		key_frames = cmds.keyframe(node, time=tuple(frame_range), attribute=attributes, query=True, timeChange=True)
	# otherwise, grab the all current keys
	else:
		key_frames = cmds.keyframe(node, attribute=attributes, query=True, timeChange=True)

	return {
		'keys': set(key_frames or list()),
		'rotationOrder': cmds.getAttr('{}.rotateOrder'.format(node)),
		'node': node
	}


def set_rotation_order_over_frames(nodes, rotation_order, bake_every_frame=False, frame_range=None):
	"""
	Changes the rotation order of the given nodes while preserving animation.

	:param list nodes: list of node names to set rotation order of.
	:param str or int rotation_order: rotation order as a string or index (between 0 and 5).
	:param bool bake_every_frame: whether all frames either on the timeline or between the start and end frame keys
		for the node should be baked.
	:param tuple[int, int] or None frame_range: the start and range to bake. If None, only existing keys will be
		updated.
	"""

	rotation_order_name = RotateOrder.from_index(rotation_order) if helpers.is_int(rotation_order) else rotation_order
	all_key_times = set()
	un_keyed_nodes = set()
	keyed_object_mapping = dict()

	# first cache existing keyframes and rotation orders which will be used to loop over
	for node, node_key_info in iterate_keyframe_rotation_orders_for_nodes(
			nodes, ['rotate'], bake_every_frame=bake_every_frame, frame_range=frame_range):
		if node_key_info['keys']:
			all_key_times.update(node_key_info['keys'])
			keyed_object_mapping[node] = node_key_info
		else:
			un_keyed_nodes.add(node_key_info['node'])

	# change rotation order for keyed objects
	if keyed_object_mapping:
		all_key_times = list(all_key_times)
		all_key_times.sort()
		with contexts.maintain_time_context():

			# force set key frames on all rotation attributes so that we are true to the original state.
			for ctx in om_timerange.iterate_frames_dg_context(all_key_times):
				frame_time = ctx.getTime()
				frame = frame_time.value
				OpenMayaAnim.MAnimControl.setCurrentTime(frame_time)
				for info in keyed_object_mapping.values():
					if frame not in info['keys']:
						continue
					cmds.setKeyframe(info['node'], attribute='rotate', preserveCurveShape=True, respectKeyable=True)

			# actual reordering and key framing to new rotation values
			for ctx in om_timerange.iterate_frames_dg_context(all_key_times):
				frame_time = ctx.getTime()
				frame = frame_time.value
				OpenMayaAnim.MAnimControl.setCurrentTime(frame_time)
				for node, info in keyed_object_mapping.items():
					if frame not in info['keys']:
						continue
					node = info['node']
					cmds.setKeyframe(info['node'], attribute='rotate', preserveCurveShape=True, respectKeyable=True)
					node.setRotationOrder(rotation_order, True)
					cmds.setKeyframe(node, attribute='rotate', preserveCurveShape=True, respectKeyable=True)
					# reset to original rotationOrder so on next frame we have the original anim.
					node.setRotationOrder(info['rotationOrder'], False)

		for each in keyed_object_mapping.values():
			cmds.xform(each['node'], preserve=False, rotateOrder=rotation_order_name)
		cmds.filterCurve([o['node'] for o in list(keyed_object_mapping.values())])

	for obj in un_keyed_nodes:
		cmds.xform(obj, preserve=True, rotateOrder=rotation_order_name)


def change_node_rotate_order(nodes, new_rotate_order=RotateOrder.XYZ, bake_every_frame=False, timeline=True):
	"""
	Sets the rotation order of the given nodes.

	:param list nodes: list of node names to set rotation order of.
	:param str or int new_rotate_order: rotation order as a string or index (between 0 and 5).
	:param bool bake_every_frame: whether all frames either on the timeline or between the start and end frame keys
		for the node should be baked.
	:param bool timeline: whether the current active timeline should be used as a key filter.
	"""

	nodes = helpers.force_list(nodes)
	if not nodes:
		logger.warning('No objects to set rotate order for given!')
		return

	frame_range = list(map(int, timerange.selected_or_current_frame_range())) if timeline else None

	set_rotation_order_over_frames(
		nodes, rotation_order=new_rotate_order, bake_every_frame=bake_every_frame, frame_range=frame_range)


def change_selected_nodes_rotate_order(new_rotate_order=RotateOrder.XYZ, bake_every_frame=False, timeline=True):
	"""
	Sets the rotation order of the current selected nodes.

	:param str or int new_rotate_order: rotation order as a string or index (between 0 and 5)
	:param bool bake_every_frame: whether all frames either on the timeline or between the start and end frame keys
		for the node should be baked.
	:param bool timeline: whether the current active timeline should be used as a key filter.
	"""

	return change_node_rotate_order(cmds.ls(sl=True, type='transform'))


def node_gimbal_tolerance(node, frame=None):
	"""
	Returns the gimbal tolerance value between 0 and 1 for the current rotation order.

	:param str node: node to get gimbal tolerance of.
	:param int or None frame: frame to get gimbal tolerance value of.
	"""

	rotation_order = cmds.getAttr('{}.rotateOrder'.format(node))
	rotation_order = RotateOrder.from_index(rotation_order)
	rotate_attr = 'rotate{}'.format(rotation_order[1].upper())
	value = cmds.getAttr('{}.{}'.format(node, rotate_attr), time=frame) if frame is not None else cmds.getAttr(
		'{}.{}'.format(node, rotate_attr))

	half_pi = math.pi * 0.5
	return abs(((value + half_pi) % math.pi) - half_pi) / half_pi


def node_all_gimbal_tolerances(node, frames=None, step=1):
	"""
	Returns the gimbal tolerance value between 0 and 1 for all rotation orders.

	:param :class:str node: node to query gimbal tolerance of.
	:param list[int or float] or None frames: individual frames to query for example: [0,1,2,3], if None then only the
		current state is queried.
	:param int step: amount of keys to skip between samples..
	:return: list of gimbal tolerances for given node.
	:rtype: list[float]
	"""

	original_rotation_order = node.rotateOrder.get()
	try:
		if frames:
			total_tolerances = list()
			for frame_index, ctx in enumerate(om_timerange.iterate_frames_dg_context(frames, step)):
				frame_time = ctx.getTime()
				frame = frame_time.value
				frame_tolerances = [0.0] * len(RotateOrder.get_all())
				for index, order in enumerate(RotateOrder.get_all()):
					node.setRotationOrder(order, True)
					frame_tolerances[index] = node_gimbal_tolerance(node, frame=frame)
				total_tolerances.append(frame_tolerances)
			# average each rotation order across all frames.
			tolerances = [scalar.mean_value(
				[frame[i] for frame in total_tolerances]) for i, _ in enumerate(RotateOrder.get_all())]
		else:
			# no frames specified so just do the current state
			tolerances = [0.0] * len(RotateOrder.get_all())
			for index, order in enumerate(RotateOrder.get_all()):
				node.setRotationOrder(order, True)
				tolerances[index] = node_gimbal_tolerance(node)
	finally:
		node.setRotationOrder(RotateOrder.from_index(original_rotation_order), True)

	return tolerances


def all_gimbal_tolerances_for_node_keys(node, current_frame_range=False):
	"""
	Returns the tolerances for each rotation order for the given nodes key frames.

	:param str node: list of  nodes to get gimbal tolerances of.
	:param bool current_frame_range: whether current active frame range will be used.
	:return: list of tolerances.
	:rtype: list[float]
	"""

	if current_frame_range:
		frame_range = timerange.selected_or_current_frame_range()
		keys = cmds.keyframe(node, time=tuple(frame_range), attribute='rotate', timeChange=True, query=True)
	else:
		keys = cmds.keyframe(node, attribute="rotate", timeChange=True, query=True)
	step_count = 1
	if keys:
		keys = sorted(set(keys))
		keys_count = len(keys)
		if keys_count >= 100:
			step_count = int(math.floor(keys_count / 100.0) * 100 / 50.0)
		elif keys_count >= 50:
			step_count = 2

	return node_all_gimbal_tolerances(node, keys, step=step_count)


def gimbal_tolerances_to_labels(tolerances):
	"""
	From a list of given tolerances, this function returns appropriate labels.

	:param list[float] tolerances: list of gimbal tolerances.
	:return: list of gimbal tolerance labels.
	:rtype: list[str]
	"""

	percentages = [(int(percent * 100)) for index, percent in enumerate(tolerances)]
	min_percent = min(percentages)
	labels = [''] * len(RotateOrder.get_all())
	for i, rotate_order in enumerate(RotateOrder.get_all()):
		name = '{} {}% Gimballed'.format(rotate_order.upper(), percentages[i])
		if percentages[i] == min_percent:
			name = "{} (recommended)".format(name)
		labels[i] = name

	return labels
