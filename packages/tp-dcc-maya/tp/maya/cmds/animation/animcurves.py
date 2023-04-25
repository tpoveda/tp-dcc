# ! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with animation curves in Maya
"""

import maya.cmds as cmds

from tp.common.python import helpers


class AnimCurveInfinityType(object):
	"""
	Class that defines all the different animation curve types in Maya
	"""

	CONSTANT = 'constant'
	LINEAR = 'linear'
	CYCLE = 'cycle'
	CYCLE_RELATIVE = 'cycleRelative'
	OSCILLATE = 'oscillate'


def animation_curve_types():
	"""
	Returns a list with all animation curve types available in Maya.

	:return: list[str]
	"""

	anim_curve_types = ['TA', 'TL', 'TT', 'TU', 'UA', 'UL', 'UT', 'UU']
	return ['animCurve{}'.format(curve_type) for curve_type in anim_curve_types]


def node_has_animation_curves(node):
	"""
	Returns whether the given node has animation curves connected to it.

	:param str node: node name to check.
	:return: True if the given node has animation curves connected to it; False otherwise.
	:rtype: bool
	"""

	connection_type_list = list(set([type(x) for x in cmds.listConnections(node, s=True, d=False)]))

	# animation curves might be connected through animation layers or a PairBlend node
	anim_type_list = ['animBlendNodeBase', 'animCurve', 'pairBlend']
	has_animation = False
	for connection_type in connection_type_list:
		if connection_type in anim_type_list:
			has_animation = True
			break

	return has_animation


def node_animation_curves(node):
	"""
	Returns all animation curves of the given node.

	:param node: str
	:return: list[str]
	"""

	return cmds.listConnections(node, t='animCurve') or list()


def node_animation_curves_in_transform_attribute(node, attribute_name):
	"""
	Returns all animation nodes connected to the given node transform attribute.

	:param str node: node name we want to retrieve animation nodes for.
	:param str attribute_name: name of the attribute of the given node we want to get animation nodes connected
	to. Note that only transform attributes are supported: 'translate', 'rotate', 'scale'.
	:return: list of animation nodes found (animation curves, ...).
	:rtype: list[str]
	"""

	anim_curves = [x for x in cmds.listConnections(
		node, type='animCurve', s=True, d=False) if attribute_name in x.name().lower()]
	if not anim_curves:
		check_nodes = cmds.listConnections([
			getattr(node, attribute_name + 'X'),
			getattr(node, attribute_name + 'Y'),
			getattr(node, attribute_name + 'Z')],
			s=True, d=False)
		if check_nodes:
			for node in check_nodes:
				layer_curves = [x for x in cmds.listConnections(
					node, type='animCurve', s=True, d=False) if attribute_name in x.name().lower()]
				if layer_curves:
					anim_curves.extend(layer_curves)

	return anim_curves


def valid_anim_curve(anim_curve):
	"""
	Returns whether given animation curve is valid or not.

	:param str anim_curve: animation curve.
	:return: True if animation curve is valid; False otheriwse.
	:rtype: bool
	"""

	input_connections = cmds.listConnections('{}.input'.format(anim_curve))
	if not cmds.referenceQuery(anim_curve, isNodeReferenced=True) and not input_connections:
		return True
	else:
		return False


def all_anim_curves(check_validity=True):
	"""
	Returns all animation curves in current Maya scene
	:return: list(str)
	"""

	anim_curves = cmds.ls(type=animation_curve_types()) or list()

	if check_validity:
		return [anim_curve for anim_curve in anim_curves if valid_anim_curve(anim_curve)]
	else:
		return anim_curves


def all_keyframes_in_anim_curves(anim_curves=None):
	"""
	Returns al keyframes in given anim curves.

	:param list[str] anim_curves: list of animation curves.
	:return: list[str]
	"""

	if anim_curves is None:
		anim_curves = list()

	if not anim_curves:
		anim_curves = all_anim_curves()

	all_keyframes = sorted(cmds.keyframe(anim_curves, query=True)) or list()

	return all_keyframes


def minimize_rotation_curves(node):
	"""
	Updates animation curves attached to given node to make sure animation rotations are set to the value closest to
	zero. Minimization is done by applying an euler filter.

	:param str node: name of the node we want to minimize rotation curves of.
	"""

	rotate_curves = cmds.keyframe(node, attribute=('rotateX', 'rotateY', 'rotateZ'), query=True, name=True)
	if not rotate_curves or len(rotate_curves) < 3:
		return

	key_times = cmds.keyframe(rotate_curves, query=True, timeChange=True)

	# create a temporary key and apply and euler filter
	temp_frame = sorted(key_times)[0] - 1
	cmds.setKeyframe(rotate_curves, time=(temp_frame,), value=0)
	cmds.filterCurve(rotate_curves)
	cmds.cutKey(rotate_curves, time=(temp_frame,))


def copy_node_animation(source_node, target_node, paste_method='replace', offset=0, start_frame=None, end_frame=None,
						layer=None, rotate_order=True):
	"""
	Copies and paste animation from source node to target node.

	:param source_node:
	:param target_node:
	:param paste_method:
	:param offset:
	:param start_frame:
	:param end_frame:
	:param layer:
	:param rotate_order:
	:return:
	"""

	target_node_names = helpers.force_list(target_node)

	if layer:
		cmds.select(target_node_names)
		cmds.animLayer(layer, edit=True, addSelectedObjects=True)
		# we force rotation values to be withing 360 degrees, so we do not get flipping when blending layers
		minimize_rotation_curves(source_node)
		for target_node in target_node_names:
			minimize_rotation_curves(target_node)

	if rotate_order:
		for target_node in target_node_names:
			try:
				source_rotate_order = cmds.getAttr('{}.rotateOrder'.format(source_node))
				if cmds.getAttr('{}.rotateOrder'.format(target_node), keyable=True):
					cmds.setAttr('{}.rotateOrder'.format(target_node), source_rotate_order)
			except Exception:
				pass

		if paste_method == 'replaceCompletely' or not start_frame or not end_frame:
			cmds.copyKey(source_node)
			if layer:
				cmds.animLayer(layer, edit=True, selected=True)
			for target_node in target_node_names:
				cmds.pasteKey(target_node, option=paste_method, timeOffset=offset)
		else:

			# run for all animation curves to make sure we are not adding or removing too many keys
			anim_curves = cmds.keyframe(source_node, query=True, name=True)
			if not anim_curves:
				return

			# check whether curves have start and end frames
			cut_start = list()
			cut_end = list()

			# if no start or end frames found we create a temporary key
			for curve in anim_curves:
				start_key = cmds.keyframe(curve, time=(start_frame,), query=True, timeChange=True)
				end_key = cmds.keyframe(curve, time=(end_frame,), query=True, timeChange=True)
				if not start_key:
					cmds.setKeyframe(curve, time=(start_frame,), insert=True)
					cut_start.append(curve)
				if not end_key:
					cmds.setKeyframe(curve, time=(end_frame,), insert=True)
					cut_end.append(curve)

			cmds.copyKey(source_node, time=(start_frame, end_frame))
			if layer:
				for anim_layer in cmds.ls(type='animLayer'):
					cmds.animLayer(anim_layer, edit=True, selected=False, preferred=False)
				cmds.animLayer(layer, edit=True, selected=True, preferred=True)
			for target_node in target_node_names:
				cmds.pasteKey(
					target_node, option=paste_method, time=(start_frame, end_frame),
					copies=1, connect=0, timeOffset=offset)

			# clean temporary keys
			if cut_start:
				cmds.cutKey(cut_start, time=(start_frame,))
			if cut_end:
				cmds.cutKey(cut_end, time=(end_frame,))


def remove_node_animation(nodes_list, translate=True, rotate=True, scale=True):
	"""
	Remove animation curves from the list of given node names.

	:param list[str] nodes_list: list of Maya scene nodes to remove animation from.
	:param bool translate: whether to remove animation from translate attributes.
	:param bool rotate: whether to remove animation from rotate attributes.
	:param bool scale: whether to remove animation from scale attributes.
	"""

	for node in nodes_list:
		if translate:
			cmds.delete(node_animation_curves_in_transform_attribute(node, 'translate'))
		if rotate:
			cmds.delete(node_animation_curves_in_transform_attribute(node, 'rotate'))
		if scale:
			cmds.delete(node_animation_curves_in_transform_attribute(node, 'scale'))
