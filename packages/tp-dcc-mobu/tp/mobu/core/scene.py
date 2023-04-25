#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with MotionBuilder scene
"""

import os

import pyfbsdk


def get_scene_name():
    """
    Returns the name of the current open 3ds Max scene
    :return: str
    """

    path_drive, path_tail = os.path.split(pyfbsdk.FBApplication().FBXFileName())
    return path_tail.split('.')[0]


def get_scene_name_and_path():
    """
    Returns the name and path of the current open 3ds Max scene
    :return: str
    """

    return pyfbsdk.FBApplication().FBXFileName


def get_selected_nodes():
    """
    Implements abstract function from scene.VoyagerScene class
    Returns a list with the selected DCCNodes
    :return: (list<gx.dcc.DCCNode>, int)
    """

    selected_nodes = pyfbsdk.FBModelList()

    top_model = None  # Search all models, not just a particular branch
    selection_state = True  # Return models that are selected, not deselected
    sort_by_select_order = True  # The last model in the list was selected most recently
    pyfbsdk.FBGetSelectedModels(selected_nodes, top_model, selection_state, sort_by_select_order)
    selected_nodes_count = selected_nodes.GetCount()

    return selected_nodes, selected_nodes_count

