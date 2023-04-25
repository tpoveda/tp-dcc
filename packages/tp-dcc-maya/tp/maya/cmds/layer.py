#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with scene layers
"""

import maya.cmds


def create_display_layer(name, nodes=None, display_type=2):
    """
    Creates a display layer containing given nodes
    :param name: str, name to give to the new display layer
    :param nodes: nodes that should be in the display layer
    :param display_type: int, type of display layer
    """

    if nodes is None:
        nodes = list()

    layer = maya.cmds.createDisplayLayer(name=name)
    maya.cmds.editDisplayLayerMembers(layer, nodes, noRecurse=True)
    maya.cmds.setAttr('{}.displayType'.format(layer), display_type)


def delete_display_layers():
    """
    Deletes all display layers
    """

    layers = maya.cmds.ls(type='displayLayer')
    for ly in layers:
        maya.cmds.delete(ly)


def get_current_render_layer():
    """
    Returns the current Maya render layer
    :return: str
    """

    return maya.cmds.editRenderLayerGlobals(query=True, currentRenderLayer=True)
