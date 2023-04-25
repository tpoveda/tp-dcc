#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related to nodes
"""

from pymxs import runtime as rt

from tp.common.python import helpers


def node_exists(node_name):
    """
    Returns whether or not given node exists in current scene
    :param node_name: str
    :return: bool
    """

    if not node_name:
        return False
    node = get_pymxs_node(node_name)

    return True if node else False


def get_node_by_name(node_name):
    """
    Returns pymxs object of the given 3ds max node name
    :param node_name: str
    :return: pymxs object
    """

    return rt.getNodeByName(node_name)


def get_node_by_handle(node_handle):
    """
    Returns pymxs object of the given 3ds max node handle
    :param node_handle: int
    :return: pymxs object
    """

    return rt.maxOps.getNodeByHandle(node_handle)


def get_pymxs_node(node_name):
    """
    Returns 3ds Max pymxs return based on its name or handle
    :return:
    """

    if helpers.is_string(node_name):
        return get_node_by_name(node_name)
    elif isinstance(node_name, int):
        return get_node_by_handle(node_name)

    return node_name


def create_point_helper(
        pos=None, size=1.0, is_center_marker=True, is_axis_tripod=False, is_cross=False, is_box=False, color=None):
    """
    Creates a new helper node in the scene
    :param pos:
    :param size:
    :param is_center_marker:
    :param is_axis_tripod:
    :param is_cross:
    :param is_box:
    :param color:
    :return:
    """

    pos = pos or [0, 0, 0]
    if rt.classOf(pos) != rt.Point3:
        pos = rt.Point3(*pos)
    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.green

    point_helper = rt.Point(
        pos=pos, size=size, centermarker=is_center_marker, axistripod=is_axis_tripod, cross=is_cross, box=is_box)
    point_helper.wirecolor = color

    return point_helper


def create_expose_transform(
        pos=None, size=1.0, is_center_marker=True, is_axis_tripod=False, is_cross=False, is_box=False, color=None):
    """
    Creates a new expose transform node in the scene
    :param pos:
    :param size:
    :param is_center_marker:
    :param is_axis_tripod:
    :param is_cross:
    :param is_box:
    :param color:
    :return:
    """

    pos = pos or [0, 0, 0]
    if rt.classOf(pos) != rt.Point3:
        pos = rt.Point3(*pos)
    if color and rt.classOf(color) != rt.color:
        color = rt.color(*color)
    if not color:
        color = rt.green

    expose_transform = rt.ExposeTM(
        pos=pos, size=size, centermarker=is_center_marker, axistripod=is_axis_tripod, cross=is_cross, box=is_box)
    expose_transform.wirecolor = color

    return expose_transform
