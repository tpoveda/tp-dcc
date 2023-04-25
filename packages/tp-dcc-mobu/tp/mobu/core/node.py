#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with MotionBuilder nodes
"""

import pyfbsdk

from tp.mobu.core import helpers


def get_node_name(node):
    """
    Returns name of the given node
    :param node:
    :return: str
    """

    return getattr(node, 'Name', node.Name)


def get_node_long_name(node):
    """
    Returns long name of the given node
    :param node:
    :return: str
    """

    return getattr(node, 'LongName', node.Name)


def get_node_by_name(name):
    """
    Returns node with the given name
    :param name: str
    :return: object
    """

    if isinstance(name, pyfbsdk.FBComponent):
        return name

    # TODO: Here we should support other node classes
    return get_model_node_by_name(name)


def get_model_node_by_name(name):
    """
    Returns model node with given name from current scene
    :param name: str, name of model node
    :return: FBModel or None
    """

    if isinstance(name, pyfbsdk.FBModel):
        return name

    find_function = pyfbsdk.FBFindModelByLabelName if helpers.get_mobu_version() >= 2014 else pyfbsdk.FBFindModelByName
    model = find_function(name)

    return model
