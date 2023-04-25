import maya.OpenMaya as OpenMaya

from tp.core import log, dcc
from tp.common.python import helpers

logger = log.tpLogger


def get_objects_to_rename(hierarchy_check, selection_type, uuid=False):
	"""
	Returns a list of objects to rename.

	:param bool hierarchy_check: whether hierarchy of selected nodes should be taken into account.
	:param int selection_type: type of selection to take into account.
	:param bool uuid: whether to use UUID of get the nodes that should be renamed.
	:return:
	"""

	search_hierarchy = hierarchy_check
	search_selection = True if selection_type == 0 else False

	if not search_selection:
		objs_to_rename = dcc.all_scene_nodes(full_path=True)
	else:
		objs_to_rename = dcc.selected_nodes(full_path=True)
	if not objs_to_rename:
		logger.warning('No objects to rename!')
		return

	if search_hierarchy:
		children_list = list()
		for obj in objs_to_rename:
			children = dcc.list_children(obj, all_hierarchy=True, full_path=True)
			if children:
				children_list.extend(children)
		children_list = list(set(children_list))
		objs_to_rename.extend(children_list)

	if uuid:
		handles_list = list()
		for obj in objs_to_rename:
			mobj = OpenMaya.MObject()
			sel = OpenMaya.MSelectionList()
			sel.add(obj)
			sel.getDependNode(0, mobj)
			handle = OpenMaya.MObjectHandle(mobj)
			handles_list.append(handle)
		return handles_list
	else:
		# we reverse the list, so we update first children and later parents, otherwise we will have problems during
		# renaming if we use full paths
		objs_to_rename.reverse()

	return objs_to_rename


def simple_rename(new_name, nodes=None, rename_shape=True):
	"""
	Renames the

	:param str or list(str) nodes: list of nodes to rename.
	:param rename_shape:
	:return:
	"""

	if not new_name:
		logger.warning('An empty new name is not valid')
		return False

	nodes = helpers.force_list(nodes or dcc.selected_nodes())
	if not nodes:
		logger.warning('No nodes to rename')
		return False

	for node in nodes:
		dcc.rename_node(node, new_name, rename_shape=rename_shape)

	return True


def add_prefix(new_prefix, nodes=None, rename_shape=True, hierarchy_check=False, only_selection=True, filter_type=None):
	"""

	:param new_prefix:
	:param nodes:
	:param rename_shape:
	:param hierarchy_check:
	:param only_selection:
	:param filter_type:
	:return:
	"""

	if not new_prefix:
		logger.warning('An empty prefix is not valid')
		return False
	if new_prefix[0].isdigit():
		logger.warning('Maya does not supports names with digits as first character')
		return False

	nodes = helpers.force_list(nodes or dcc.selected_nodes())
	if not nodes:
		logger.warning('No nodes to add prefix to')
		return False

	dcc.add_name_prefix(
		new_prefix, obj_names=nodes, filter_type=filter_type, search_hierarchy=hierarchy_check,
		selection_only=only_selection, rename_shape=rename_shape)

	return True


def remove_prefix(nodes=None, rename_shape=True, hierarchy_check=False, only_selection=True, filter_type=None):
	"""

	:param nodes:
	:param rename_shape:
	:param hierarchy_check:
	:param only_selection:
	:param filter_type:
	:return:
	"""

	if not hierarchy_check and not only_selection:
		logger.warning('Remove prefix must be used with "Selected" options not with "All"')
		return False

	nodes = helpers.force_list(nodes or dcc.selected_nodes())
	if not nodes:
		logger.warning('No nodes to remove prefix from')
		return False

	dcc.remove_name_prefix(
		obj_names=nodes, filter_type=filter_type, search_hierarchy=hierarchy_check, selection_only=only_selection,
		rename_shape=rename_shape)

	return True
