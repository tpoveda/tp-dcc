# ! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with animation layers in Maya
"""

import maya.mel as mel
import maya.cmds as cmds

from tp.core import log
from tp.common.python import helpers
from tp.common.qt import api as qt
from tp.maya.cmds import decorators, helpers as maya_helpers

logger = log.tpLogger


def create_and_select_anim_layer(rotation_mode=1):

	anim_layer = cmds.animLayer(addSelectedObjects=True)
	cmds.setAttr(f'{anim_layer}.rotationAccumulationMode')
	select_anim_layer(anim_layer)

	return anim_layer


def select_anim_layer(anim_layer_to_select):

	anim_layers = cmds.ls(type='animLayer')
	for anim_layer in anim_layers:
		cmds.animLayer(anim_layer, edit=True, selected=False)
	cmds.animLayer(anim_layer_to_select, edit=True, selected=True)
	mel.eval(f'animLayerEditorOnSelect "{anim_layer_to_select}" 1;')


def fix_solo_keyframe_animation_layers():
	"""
	Checks all animation layers with a single keyframe available within current scene and places a second keyframe
	after the first for all objects in the layer.

	..note:: animation layers with no animation are ignored.
	"""

	for animation_layer in cmds.ls(type='animLayer'):
		anim_curve_list = cmds.animLayer(animation_layer, query=True, animCurves=True)
		# Ignore anim layers with no animation
		single_keyframe = True if anim_curve_list else False
		keyed_frame = None
		for anim_curve in anim_curve_list:
			if anim_curve.numKeyframes() > 1:
				single_keyframe = False
				break
			else:
				keyed_frame = anim_curve.getTime(0)
		if single_keyframe:
			layer_obj_list = list(set(animation_layer.dagSetMembers.listConnections()))
			if layer_obj_list:
				cmds.copyKey(layer_obj_list, animLayer=animation_layer, t=keyed_frame)
				cmds.pasteKey(layer_obj_list, animLayer=animation_layer, t=keyed_frame + 1)


def anim_layers_from_nodes(nodes):
	"""
	Returns all animation layers associated with the given nodes.

	:param list(pm.PyNode) nodes: list of nodes that can be associated to an animation layer.
	:return: list of associated animation layers.
	:rtype: list(pm.AnimLayer)
	"""

	nodes = helpers.force_list(nodes)
	return cmds.animLayer(nodes, query=True, affectedLayers=True)


@decorators.viewport_off
def fast_merge_anim_layers(delete_baked=True):
	"""
	Fast merge animation layers function.
	From the given nodes this function finds, merges and remove any anim layers found.

	:param bool delete_baked: whether baked nodes should be deleted after the merge animation operation is completed.
	:return: True if merge animation layers operation was successful; False otherwise.
	:rtype: bool

	..info:: Based on: https://github.com/RedForty/FastMergeLayers/blob/main/fast_merge_layers.py
	"""

	root_layer = cmds.animLayer(query=True, root=True) or list()
	if not root_layer:
		logger.warning('BaseAnimation not found!')
		return False

	# check whether any layers are selected directly within UI
	anim_layers = cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True) or list()
	anim_layers = anim_layers or anim_layers_from_nodes(cmds.ls(sl=True))
	if len(anim_layers) == 1 and root_layer not in anim_layers:
		anim_layers.insert(0, root_layer)

	if not anim_layers:
		return False

	delete_merged = True
	try:
		# deal with Maya's optVars for animLayers as the call that sets the defaults for these, via the UI call,
		if cmds.optionVar(exists='animLayerMergeDeleteLayers'):
			delete_merged = cmds.optionVar(query='animLayerMergeDeleteLayers')
		cmds.optionVar(intValue=('animLayerMergeDeleteLayers', delete_baked))
		if not cmds.optionVar(exists='animLayerMergeByTime'):
			cmds.optionVar(floatValue=('animLayerMergeByTime', 1.0))
		mel.eval('animLayerMerge {"%s"}' % '","'.join(anim_layers))
	except Exception:
		logger.warning('AnimLayer merge operation failed!')
	finally:
		cmds.optionVar(intValue=('animLayerMergeDeleteLayers', delete_merged))

	return True


def selected_anim_layers():
	"""
	Returns a list with current selected animation layers.

	:return: list of selected animation layers.
	:rtype: list[str]
	"""

	return cmds.treeView('AnimLayerTabanimLayerEditor', query=True, selectItem=True) or list()


def max_anim_layers():
	"""
	Returns the maximum numer of animation layers.

	:return: maximum number of animation layers.
	:rtype: int
	"""

	return cmds.animLayer(query=True, maxLayers=True)


def best_anim_layers():
	"""
	Return the layers that will be keyed for specified attribute.

	:return: list of animation layers.
	:rtype: list[str]
	"""

	return cmds.animLayer(query=True, bestAnimLayer=True)


def affected_anim_layers():
	"""
	Return the layers that the currently selected object(s) are members of.

	:return: list of animation layers.
	:rtype: list[str]
	"""

	return cmds.animLayer(query=True, affectedLayers=True)


def all_anim_layers_ordered():
	"""
	Recursive function that returns all available animation layers within current scene.

	:return: list of animation layers.
	:rtype: list(str)
	"""

	def _add_node_recursive(layer_node):
		all_layers.append(layer_node)
		child_layers = cmds.animLayer(layer_node, query=True, children=True) or list()
		for child_layer in child_layers:
			_add_node_recursive(child_layer)

	all_layers = list()
	root_layer = cmds.animLayer(query=True, root=True)
	if not root_layer:
		return all_layers
	_add_node_recursive(root_layer)

	return all_layers


def anim_layers_available():
	"""
	Returns whether animation layers are available.

	:return: True if animation layers are available; False otherwise.
	:rtype: bool
	"""

	all_layers = all_anim_layers_ordered()
	return len(all_layers) < max_anim_layers()


def anim_layer_display_label(layer, show_namespace=True):
	"""
	Returns the display label for the given layer node.

	:param str layer: animation layer node.
	:param bool show_namespace: whether to display layer namespace.
	:return: layer display name.
	:rtype: str
	"""

	display_label = layer
	if not show_namespace:
		tokens = layer.split(':')
		if len(tokens) > 1:
			display_label = '...:' + tokens[-1]

	return display_label


def select_objects_from_anim_layers(anim_layers):
	"""
	Selects all the objects added to the given animationr layers.

	:param str or list[str] anim_layers: list of animation layers to select objects of.
	"""

	anim_layers = helpers.force_list(anim_layers)

	def _build_anim_layer_array_recursive(anim_layer_node):
		children = cmds.animLayer(anim_layer_node, query=True, children=True) or list()
		for child in children:
			all_anim_layers.append(child)
			_build_anim_layer_array_recursive(child)

	cmds.select(clear=True)

	all_anim_layers = list()

	for anim_layer in anim_layers:
		if cmds.objectType(anim_layer) != 'animLayer':
			continue
		if anim_layer == cmds.animLayer(query=True, root=True):
			_build_anim_layer_array_recursive(anim_layer)
			select_objects_from_anim_layers(all_anim_layers)
			break
		else:
			attrs = cmds.animLayer(anim_layer, query=True, attribute=True)
			for attr in attrs:
				cmds.select(attr.split('.')[0], add=True)


def remove_objects_from_anim_layers(nodes, anim_layers):

	for anim_layer in anim_layers:

		if cmds.objectType(anim_layer) != 'animLayer':
			continue
		attrs = cmds.animLayer(anim_layer, query=True, attribute=True) or list()
		for attr in attrs:
			attr_full_name = cmds.ls(attr, long=True)[0]
			node_full_name = attr_full_name.split('.')[0]
			for node in nodes:
				_node_full_name = cmds.ls(node, long=True)
				if _node_full_name == node_full_name:
					cmds.animLayer(anim_layer, edit=True, removeAttribute=attr)


def extract_animation_based_on_anim_layer_selected_objects():

	def _bake_simulation_playback_range():

		original_selection = cmds.ls(sl=True)
		maya_version = maya_helpers.maya_version()
		if maya_version >= 2016:
			eval_mode = cmds.evaluationManager(query=True, mode=True)
			if eval_mode[0] != 'off':
				cmds.evaluationManager(mode='off')
		min_time = cmds.playbackOptions(query=True, ast=True)
		max_time = cmds.playbackOptions(query=True, aet=True)
		its_baked = True
		try:
			its_baked = cmds.bakeResults(original_selection, simulation=True, shape=False, t=f'{min_time}:{max_time}')
		except Exception:
			pass
		if maya_version >= 2016:
			if eval_mode[0] != 'off':
				cmds.evaluationManager(mode=eval_mode[0])
		if its_baked:
			cmds.warning('Select something')

	def _euler_filter_on_selected_nodes():

		selected = cmds.ls(sl=True)
		if not selected:
			return
		anim_curves = cmds.keyframe(query=True, name=True)
		stat_time = cmds.keyframe(anim_curves, query=True, index=tuple([0]), timeChange=True)
		stat_time.sort()
		null_frame = stat_time[0] - 10
		for _node in selected:
			for attr in ['rotateX', 'rotateY', 'rotateZ']:
				try:
					cmds.setKeyframe(_node, v=0, t=null_frame, at=attr)
				except Exception:
					pass
			for attr in ['rotateX', 'rotateY', 'rotateZ']:
				try:
					cmds.filterCurve(f'{_node}.{attr}')
				except Exception:
					pass
			cmds.selectKey(clear=True)
			for attr in ['rotateX', 'rotateY', 'rotateZ']:
				try:
					cmds.cutKey(_node, t=null_frame, at=attr)
				except Exception:
					pass
			cmds.selectKey(clear=True)

	selection = cmds.ls(sl=True)
	objects_in_layers = list()

	for node in selection:
		cmds.select(node)
		affected = affected_anim_layers()
		if affected:
			objects_in_layers.append(node)

	locked_layers = list()
	unlocked_layers = list()
	locked_muted_layers = list()
	locked_unmuted_layers = list()

	if objects_in_layers:
		cmds.select(objects_in_layers)
		affected_layers = affected_anim_layers()
		for anim_layer in affected_layers:
			if cmds.animLayer(anim_layer, query=True, lock=True):
				locked_layers.append(anim_layer)
			else:
				unlocked_layers.append(anim_layer)
		for anim_layer in locked_layers:
			if cmds.animLayer(anim_layer, query=True, mute=True):
				locked_muted_layers.append(anim_layer)
			else:
				locked_unmuted_layers.append(anim_layer)

		for anim_layer in locked_layers:
			cmds.animLayer(anim_layer, edit=True, mute=True)

		_bake_simulation_playback_range()
		remove_objects_from_anim_layers(selection, unlocked_layers)
		delete_empty_anim_layers()
		for anim_layer in locked_unmuted_layers:
			cmds.animLayer(anim_layer, edit=True, mute=False)

	cmds.select(clear=True)
	have_locked = False if not locked_layers else True
	cmds.select(selection)
	if objects_in_layers:
		_euler_filter_on_selected_nodes()

	return have_locked


def delete_empty_anim_layers():

	def _empty_all_the_way(_anim_layer):

		attrs = cmds.animLayer(_anim_layer, query=True, attribute=True)
		if attrs:
			return False
		layer_children = cmds.animLayer(_anim_layer, query=True, children=True)
		for child_layer in layer_children:
			if not _empty_all_the_way(child_layer):
				return False

		return True

	root_layer = cmds.animLayer(query=True, root=True)
	layers_to_delete = list()

	anim_layers = all_anim_layers_ordered()
	for anim_layer in anim_layers:
		if anim_layer == root_layer:
			continue
		attributes = cmds.animLayer(anim_layer, query=True, attribute=True)
		if _empty_all_the_way(anim_layer):
			layers_to_delete.append(anim_layer)

	delete_anim_layers(layers_to_delete)


def delete_anim_layers(anim_layers):
	"""
	Deletes given animation layer nodes from current scene.

	:param str or list[str] anim_layers: animation layers to delete.
	..warning: care must be taken when deleting an animation layer because deleting a parent will also delete all the
		children layer.
	"""

	anim_layers = helpers.force_list(anim_layers)
	root_layer = cmds.animLayer(query=True, root=True)

	for anim_layer in anim_layers:
		if cmds.objectType(anim_layer) != 'animLayer':
			continue
		if not cmds.animLayer(anim_layer, query=True, exists=True):
			continue
		if anim_layer == root_layer:
			continue

		cmds.delete(anim_layer)


def anim_time_range_from_anim_layer(anim_layer):

	if anim_layer and anim_layer != 'BaseAnimation':
		current_layer_curves = cmds.animLayer(anim_layer, query=True, animCurves=True)
	else:
		current_layer_curves = cmds.keyframe(query=True, name=True)
	if not current_layer_curves:
		logger.warning('No layer and no object selected')
		return [0]

	anim_range = cmds.keyframe(current_layer_curves, query=True, timeChange=True)
	anim_range.sort()

	return [anim_range[0], anim_range[-1]]


def anim_time_range_from_multiply_anim_layers(anim_layers):

	if not anim_layers:
		return [0, 0]

	total_range = list()

	for anim_layer in anim_layers:
		anim_range = anim_time_range_from_anim_layer(anim_layer)
		total_range.append(anim_range[0])
		total_range.append(anim_range[1])
	total_range.sort()

	return [total_range[0], total_range[-1]]


def create_anim_layer_editor_window(window_name='MyCustomAnimDisplayLayerEditor', title='Anim Layer Editor'):

	if cmds.window(window_name, exists=True):
		cmds.deleteUI(window_name)
	window = cmds.window(window_name)
	cmds.window(window, edit=True, title=title)
	mel.eval('createAnimLayerEditor("{}", "MyCustomAnimDisplayLayerEditor");'.format(window))
	cmds.showWindow(window)
	window_qt = qt.to_qt_object(window)

	return window_qt
