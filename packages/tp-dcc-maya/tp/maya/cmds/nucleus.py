#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya Nucleus solver
"""

import maya.cmds
import maya.mel


def set_active_nucleus(nucleus_node_name):
    """
    Sets global variable that Maya uses to know which nucleus node should use to perform command on
    :param nucleus_node_name: str, name of the nucleus node to activate
    """

    maya.mel.eval('global string $gActiveNucleusNode;$gActiveNucleusNode = "{}";'.format(nucleus_node_name))


def create_nucleus(name=''):
    """
    Creates an NCloth nucleus node
    :param name: str, name for the nucleus node
    :return: str, name of the nucleus node
    """

    name = 'nucleus_{}'.format(name) if name else 'nucleus'
    nucleus_node = maya.cmds.createNode('nucleus', name=name)
    set_active_nucleus(nucleus_node)
    maya.cmds.connectAttr('time1.outTime', '{}.currentTime'.format(nucleus_node))
    maya.cmds.setAttr('{}.spaceScale'.format(nucleus_node), 0.01)

    return nucleus_node
