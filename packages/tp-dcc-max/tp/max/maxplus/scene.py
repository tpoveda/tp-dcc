# !/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, division, absolute_import

"""
Module that contains Max Python functions related with 3ds Max scenes for MaxPlus
"""

import os

from Qt.QtWidgets import QMessageBox

import MaxPlus

from tp.common.python import helpers


def get_root():
    """
    Returns the root object of the scene
    :return: MaxPlus.INode
    """

    return MaxPlus.Core.GetRootNode()


def get_scene_name():
    """
    Returns the name of the current open 3ds Max scene
    :return: str
    """

    return MaxPlus.FileManager.GetFileName().rsplit('.')[0]


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

    return MaxPlus.FileManager.GetFileNameAndPath()


def check_node(node_name):
    """
    Returns whether the given node has valid type to work with MaxPlus. If not, raises an Exception
    :param node_name: variant, str || MaxPlus.INode, node we want to check
    """

    if not helpers.is_string(node_name) and type(node_name) is not MaxPlus.INode:
        raise Exception(
            'Given node "{}" has not a valid type: "{}" (str or MaxPlus.INode instead)!'.format(
                node_name, type(node_name)))


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
    Returns MaxPlus.INode object with the given name, if exists in the scene; otherwise returns None
    :param node_name: str, name of the node we want to retrieve
    :return: variant, MaxPlus.INode || None
    """

    return MaxPlus.INode.GetINodeByName(str(node_name))


def get_node_by_handle(node_id):
    """
    Returns MaxPlus.INode object with the given index, if exists in the scene; otherwise returns None
    :param node_id: int, unique node index
    :return: variant, MaxPlus.INode || None
    """

    return MaxPlus.INode.GetINodeByHandle(node_id)


def get_scene_nodes():
    """
    Returns al nodes in current scene as GamEX nodes
    :return: list<gx.dcc.DCCNode>
    """

    node_list = list()
    _append_children(MaxPlus.Core.GetRootNode(), node_list)

    return node_list, len(node_list)


def get_selected_nodes():
    """
    Implements abstract function from scene.VoyagerScene class
    Returns a list with the selected DCCNodes
    :return: (list<gx.dcc.DCCNode>, int)
    """

    selected_nodes = MaxPlus.SelectionManager.GetNodes()
    selected_nodes_count = selected_nodes.GetCount()

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

    parent = max_node.GetParent()
    if not parent or parent is get_root():
        return None

    return parent


def get_direct_children_nodes(max_node):
    """
    Returns direct children of the given Max node
    :param max_node: MaxPlus.INode
    :return: list<MaxPlus.INode>
    """

    return [child for child in max_node.Children]


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


def get_node_item(item_list, item_index):
    """
    :param item_list: list<MaxPlus.INode>, list
    :param item_index: int, index of the item we want to get from the list
    :return: MaxPlus.INode
    """

    node_item = item_list.GetItem(item_index)

    return node_item


def select_nodes(max_nodes, add=False):
    """
    Select given Max nodes
    :param max_nodes: list<MaxPlus.INode>
    :param add: bool, Whether to add given node names to an existing selection or not
    """

    # Check if we need to convert given list of MaxPlus.INodes into a MaxPlus.INodeTab
    if not isinstance(max_nodes, MaxPlus.INodeTab):
        sel = MaxPlus.INodeTab()
        for n in max_nodes:
            sel.Append(n)
    else:
        sel = max_nodes

    # Clear selection if need it
    if not add:
        MaxPlus.SelectionManager.ClearNodeSelection()

    MaxPlus.SelectionManager.SelectNodes(sel)


def select_nodes_by_name(names, add=False):
    """
    Selects nodes by name
    :param names: list<str>, names of nodes to select
    :param add: bool, Whether to add given node names to an existing selection or not
    """

    names = helpers.force_list(names)

    nodes = MaxPlus.INodeTab()
    for n in names:
        node = MaxPlus.INode.GetINodeByName(n)
        if node:
            nodes.Append(node)

    # Clear selection if need it
    if not add:
        MaxPlus.SelectionManager.ClearNodeSelection()

    MaxPlus.SelectionManager.SelectNodes(nodes)


def parent_node(max_child_node, max_parent_node):
    """
    Parents child node into parent node hierarchy
    :param max_child_node: MaxPlus.INode
    :param max_parent_node: MaxPlus.INode
    """

    max_child_node.SetParent(max_parent_node)

    return max_child_node


def unparent_node(max_node):
    """
    Unparents given Max node
    :param max_node: MaxPlus.INode
    """

    max_node.SetParent(get_root())

    return max_node


def remove_nodes(max_nodes):
    """
    Deletes given max nodes
    :param max_nodes: list<MaxPlus.INode>
    """

    if type(max_nodes) not in [list, tuple]:
        max_nodes = [max_nodes]

    for obj in max_nodes:
        obj.Delete()


def remove_nodes_by_ids(nodes_ids):
    """
    Removes objects with the given ids
    :param nodes_ids: list<int>
    """

    nodes_ids = helpers.force_list(nodes_ids)

    for obj_id in nodes_ids:
        args = '''
           for obj in objects do
           (
               if obj.handle == {} do
               (
                   undo "Deleted Node" on (delete obj)
               )
           )
           '''.format(obj_id)
        MaxPlus.Core.EvalMAXScript(args)


def convert_list_to_nodetab(max_nodes):
    """
    Given given list of MaxObjects into a INodeTab object
    :param max_nodes: list, list<MaxPlus.INode>
    :return: INodeTab
    """

    pass


def _append_children(max_node, node_list_):
    """
    Internal function to recursively append children to list
    :param max_node: MaxPlus.INode
    :param node_list_: list<MaxPlus.INode>
    """

    if len(list(max_node.Children)) > 0:
        for child in max_node.Children:
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


def save(force=False):
    """
    Saves current scene in current Max file
    :return: bool, Whether the scene was saved or not
    """

    file_check_state = MaxPlus.FileManager.IsSaveRequired()
    if file_check_state:
        if file_check_state:
            if force:
                MaxPlus.FileManager.Save()
                return True
            else:
                msg_box = QMessageBox()
                msg_box.setText('The 3ds Max scene has been modified')
                msg_box.setInformativeText('Do you want to save your changes?')
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.setDefaultButton(QMessageBox.Yes)
                res = msg_box.exec_()
                if res == QMessageBox.Yes:
                    MaxPlus.FileManager.Save()
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
        MaxPlus.Core.EvalMAXScript('actionMan.executeAction ' + str(ACTION_TABLE_ID) + ' "' + str(NEW_ACTION_ID) + '"')

    MaxPlus.FileManager.Reset(noPrompt=not do_save)
