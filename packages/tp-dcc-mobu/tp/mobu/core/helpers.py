#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains MotionBuilder utility functions and classes
"""

import pyfbsdk


def get_mobu_version():
    """
    Returns version of the executed MotionBuilder
    :return: int, version of MotionBuilder
    """

    path = pyfbsdk.__file__

    supported_versions = [i for i in range(2000, 2100)]
    for v in supported_versions:
        if str(v) in path:
            return v

    return None


def get_node_item(item_list, item_index):
    """
    :param item_list: list
    :param item_index: int, index of the item we want to get from the list
    :return:
    """

    node_item = item_list.GetModel(item_index)

    return node_item
