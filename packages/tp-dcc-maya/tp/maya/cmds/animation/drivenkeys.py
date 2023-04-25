# ! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with driven keys in Maya
"""

import maya.cmds as cmds

from tp.maya.cmds import scene
from tp.maya.cmds.animation import animcurves


def quick_driven_key(source, target, source_values, target_values, infinite=False, tangent_type='linear'):
	"""
	Simple function that simplifies the process of creating driven keys.

	:param pm.Attribute source: attribute to drive target wit
	:param pm.Attribute target: attribute to be driven by source
	:param list source_values: list of values at the source
	:param list target_values: list of values at the target
	:param bool infinite: whether to infinite or not anim curves
	:param str tangent_type: type of tangent type to create for anim curves
	"""

	track_nodes = scene.TrackNodes()
	track_nodes.load('animCurve')

	if not type(tangent_type) == list:
		tangent_type = [tangent_type, tangent_type]

	for i in range(len(source_values)):
		cmds.setDrivenKeyframe(
			target, cd=source, driverValue=source_values[i],
			value=target_values[i], itt=tangent_type[0], ott=tangent_type[1])

	keys = track_nodes.get_delta()
	if not keys:
		return

	keyframe = keys[0]
	if infinite:
		keyframe.setPreInfinityType(animcurves.AnimCurveInfinityType.LINEAR)
		keyframe.setPostInfinityType(animcurves.AnimCurveInfinityType.LINEAR)
	if infinite == 'post_only':
		keyframe.setPreInfinityType(animcurves.AnimCurveInfinityType.CONSTANT)
		keyframe.setPostInfinityType(animcurves.AnimCurveInfinityType.LINEAR)
	if infinite == 'pre_only':
		keyframe.setPreInfinityType(animcurves.AnimCurveInfinityType.CONSTANT)
		keyframe.setPostInfinityType(animcurves.AnimCurveInfinityType.LINEAR)

	return keyframe
