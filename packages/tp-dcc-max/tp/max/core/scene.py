# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Max Python functions related with 3ds Max scenes
"""

import os

from Qt.QtWidgets import QMessageBox

import pymxs
from pymxs import runtime as rt

from tp.common.python import helpers, path as path_utils
from tp.max.core import node, directory


def get_root():
    """
    Returns the root object of the scene
    :return: MaxPlus.INode
    """

    return rt.rootNode


def get_scene_name():
    """
    Returns the name of the current open 3ds Max scene
    :return: str
    """

    return rt.maxFileName.rsplit('.')[0]


def get_scene_path():
    """
    Returns the path of the current open 3ds Max scene
    :return: str
    """

    scene_path = get_scene_name_and_path()
    if scene_path and os.path.isfile(scene_path):
        return os.path.dirname(scene_path)

    return None


def get_scene_name_and_path():
    """
    Returns the name and path of the current open 3ds Max scene including the extension (.max)
    :return: str
    """

    return path_utils.join_path(rt.maxFilePath, rt.maxFileName)


def node_handle_exists(node_id):
    """
    Checks if exists a node with the given ID
    :param node_id: int
    :return: bool
    """

    native_node = int(node_id)
    return native_node is not None


def get_node_by_name(node_name):
    """
    Returns pymxs node object with the given name, if exists in the scene; otherwise returns None
    :param node_name: str, name of the node we want to retrieve
    :return: variant, pymxs object or None
    """

    return rt.getNodeByName(str(node_name))


def get_node_by_handle(node_id):
    """
    Returns MaxPlus.INode object with the given index, if exists in the scene; otherwise returns None
    :param node_id: int, unique node index
    :return: variant, pymxs object or None
    """

    return rt.maxOps.getNodeByHandle(node_id)


def is_empty_scene():
    """
    Returns whether or not current scene is empty
    :return: bool
    """

    return len(rt.rootNode.children) == 0


def get_scene_nodes():
    """
    Returns al nodes in current scene as GamEX nodes
    :return: list<gx.dcc.DCCNode>
    """

    node_list = list()
    _append_children(get_root(), node_list)

    return node_list, len(node_list)


def get_selected_nodes():
    """
    Implements abstract function from scene.VoyagerScene class
    Returns a list with the selected DCCNodes
    :return: (list<gx.dcc.DCCNode>, int)
    """

    selected_nodes = list(rt.selection)
    selected_nodes_count = rt.selection.count

    return selected_nodes, selected_nodes_count


def get_all_scene_nodes():
    """
    Returns a list with all objects in the current scene
    :return: list<MaxPlus.INode>
    """

    node_list = list()
    _append_children(get_root(), node_list)

    return node_list


def get_direct_parent_node(max_node):
    """
    Returns direct parent of the given Max node
    :param max_node: MaxPlus.INode
    :return: variant, MaxPlus.INode || None
    """

    parent = max_node.parent
    if not parent or parent is get_root():
        return None

    return parent


def get_direct_children_nodes(max_node):
    """
    Returns direct children of the given Max node
    :param max_node: MaxPlus.INode
    :return: list<MaxPlus.INode>
    """

    return [child for child in max_node.children]


def get_all_parent_nodes(max_node):
    """
    Return all parent nodes of the given Max node
    :param max_node: MaxPlus.INode
    :return: list<MaxPlus.INode>
    """

    node_list = list()
    _append_parents(max_node, node_list)

    return node_list


def get_all_children_nodes(max_node):
    """
    Return all children nodes of the given Max node
    :param max_node: MaxPlus.INode
    :return: list<MaxPlus.INode>
    """

    node_list = list()
    _append_children(max_node, node_list)

    return node_list


def select_nodes(max_nodes, add=False):
    """
    Select given Max nodes
    :param max_nodes: list<MaxPlus.INode>
    :param add: bool, Whether to add given node names to an existing selection or not
    """

    max_nodes = helpers.force_list(max_nodes)

    sel = list() if not add else list(rt.selection)
    for max_node in max_nodes:
        max_node = node.get_pymxs_node(max_node)
        sel.append(max_node)
    if not sel:
        return

    rt.select(sel)


def select_nodes_by_name(names, add=False):
    """
    Selects nodes by name
    :param names: list<str>, names of nodes to select
    :param add: bool, Whether to add given node names to an existing selection or not
    """

    names = helpers.force_list(names)

    nodes = list() if not add else list(rt.selection)
    for n in names:
        node = get_node_by_name(n)
        if node:
            nodes.append(node)

    # Clear selection if need it
    if not add:
        rt.clearSelection()

    rt.select(nodes)


def parent_node(max_child_node, max_parent_node):
    """
    Parents child node into parent node hierarchy
    :param max_child_node: MaxPlus.INode
    :param max_parent_node: MaxPlus.INode
    """

    max_child_node = node.get_pymxs_node(max_child_node)
    max_parent_node = node.get_pymxs_node(max_parent_node)

    max_child_node.parent = max_parent_node

    return max_child_node


def unparent_node(max_node):
    """
    Unparents given Max node
    :param max_node: MaxPlus.INode
    """

    max_node = node.get_pymxs_node(max_node)

    max_node.parent = None

    return max_node


def remove_nodes(max_nodes):
    """
    Deletes given max nodes
    :param max_nodes: list<MaxPlus.INode>
    """

    max_nodes = helpers.force_list(max_nodes)
    for obj in max_nodes:
        rt.delete(obj)


def remove_nodes_by_ids(nodes_ids):
    """
    Removes objects with the given ids
    :param nodes_ids: list<int>
    """

    nodes_ids = helpers.force_list(nodes_ids)

    loop_ids = nodes_ids[:]

    scene_objects = list(rt.objects)[:]
    with pymxs.undo(True):
        for obj in scene_objects:
            if not loop_ids:
                return
            if obj.handle in loop_ids:
                loop_ids.remove(obj.handle)
                rt.delete(obj)


def _append_children(max_node, node_list_):
    """
    Internal function to recursively append children to list
    :param max_node: MaxPlus.INode
    :param node_list_: list<MaxPlus.INode>
    """

    if len(list(max_node.children)) > 0:
        for child in max_node.children:
            node_list_.append(child)
            _append_children(child, node_list_)


def _append_parents(max_node, node_list_):
    """
    Internal function to recursively append parents to list
    :param max_node: MaxPlus.INode
    :param node_list_: list<MaxPlus.INode>
    """

    parent = max_node.GetParent()
    if parent and not parent.IsRoot:
        node_list_.append(parent)
        _append_parents(parent, node_list_)


def save(file_path=None):
    """
    Saves current scene in current Max file
    :return: bool, Whether the scene was saved or not
    """

    file_path = file_path or ''
    file_check_state = rt.getSaveRequired()
    if file_check_state:
        msg_box = QMessageBox()
        msg_box.setText('The 3ds Max scene has been modified')
        msg_box.setInformativeText('Do you want to save your changes?')
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        res = msg_box.exec_()
        if res == QMessageBox.Yes:
            file_path = file_path or directory.save_file_dialog('Save File', filters='*.max')
            if not file_path:
                return
            rt.saveMaxFile(file_path)
            return True

    return False


def new_scene(force=True, do_save=True):
    """
    Creates a new Max scene
    :param force: bool, True if we want to save the scene without any prompt dialog
    :param do_save: bool, True if you want to save the current scene before creating new scene
    """

    if do_save and not force:
        save()
        ACTION_TABLE_ID = 0
        NEW_ACTION_ID = "16"
        rt.EvalMAXScript('actionMan.executeAction ' + str(ACTION_TABLE_ID) + ' "' + str(NEW_ACTION_ID) + '"')
        return

    mxs_function = """fn mf = (
        local windowHandle = DialogMonitorOPS.GetWindowHandle()
        if (windowHandle != 0) then (
            UIAccessor.PressButtonByName windowHandle "Do&n't Save"
        )
        return true
    )
    """
    rt.execute('mf={}'.format(mxs_function))

    rt.DialogMonitorOPS.unRegisterNotification(id=rt.Name('forceNewFile'))
    rt.DialogMonitorOPS.registerNotification(rt.mf, id=rt.Name('forceNewFile'))
    rt.DialogMonitorOPS.enabled = True
    rt.actionMan.executeAction(0, '16')     # new file macro action
    rt.DialogMonitorOPS.unRegisterNotification(id=rt.Name('forceNewFile'))
    rt.DialogMonitorOPS.enabled = False

    return True
