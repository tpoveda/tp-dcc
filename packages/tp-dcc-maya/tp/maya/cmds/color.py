#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with colors
"""

from Qt.QtGui import QColor

import maya.cmds

# ==== Control Colors
CONTROL_COLORS = [(.467, .467, .467), [.000, .000, .000], (.247, .247, .247), (.498, .498, .498), (0.608, 0, 0.157),
                  (0, 0.016, 0.373), (0, 0, 1), (0, 0.275, 0.094), (0.145, 0, 0.263), (0.78, 0, 0.78),
                  (0.537, 0.278, 0.2), (0.243, 0.133, 0.122), (0.6, 0.145, 0), (1, 0, 0), (0, 1, 0), (0, 0.255, 0.6),
                  (1, 1, 1), (1, 1, 0), (0.388, 0.863, 1), (0.263, 1, 0.635), (1, 0.686, 0.686), (0.89, 0.675, 0.475),
                  (1, 1, 0.384), (0, 0.6, 0.325), (0.627, 0.412, 0.188), (0.62, 0.627, 0.188), (0.408, 0.627, 0.188),
                  (0.188, 0.627, 0.365), (0.188, 0.627, 0.627), (0.188, 0.404, 0.627), (0.435, 0.188, 0.627),
                  (0.627, 0.188, 0.404)]

MAYA_COLOR_NAMES = ['none', 'black', 'lightGrey', 'midGrey', 'tomato', 'darkBlue', 'blue', 'darkGreen', 'darkPurple',
                    'pink', 'brownOrange', 'brown', 'orange', 'red', 'green', 'royalBlue', 'white', 'yellow',
                    'babyBlue', 'aqua', 'palePink', 'skin', 'paleYellow', 'paleGreen', 'orangeBrownLight', 'olive',
                    'citrus', 'forestGreen', 'java', 'endeavourBlue', 'darkOrchid', 'mediumRedViolet']

# Maya color list integers (0 - 31). Not linear, so they will not match viewport color
MAYA_COLORS_SRGB = [(0.0, 0.0156, 0.3764), (0.0, 0.0, 0.0), (0.251, 0.251, 0.251), (0.6, 0.6, 0.6), (0.608, 0.0, 0.157),
                    (0.0, 0.0156, 0.3764), (0.0, 0.0, 1.0), (0.0, 0.275, 0.098), (0.149, 0.0, 0.263),
                    (0.784, 0.0, 0.784), (0.541, 0.282, 0.2), (0.247, 0.137, 0.121), (0.6, 0.149, 0.0), (1.0, 0.0, 0.0),
                    (0.0, 1.0, 0.0), (0.0, 0.255, 0.6), (1.0, 1.0, 1.0), (1.0, 1.0, 0.0), (0.3921, 0.8627, 1.0),
                    (0.263, 1.0, 0.639), (1.0, 0.650, 0.650), (0.894, 0.674, 0.474), (1.0, 1.0, 0.388),
                    (0.0, 0.6, 0.329), (0.631, 0.416, 0.188), (0.620, 0.631, 0.188), (0.407, 0.631, 0.188),
                    (0.188, 0.631, 0.365), (0.188, 0.631, 0.631), (0.188, 0.404, 0.631), (0.435, 0.188, 0.631),
                    (0.631, 0.188, 0.416)]

MAYA_COLORS_LINEAR_RGB = [(0.0000, 0.0012, 0.1169), (0.0000, 0.0000, 0.0000), (0.0513, 0.0513, 0.0513),
                          (0.3185, 0.3185, 0.3185), (0.3280, 0.0000, 0.0213), (0.0000, 0.0012, 0.1169),
                          (0.0000, 0.0000, 1.0000), (0.0000, 0.0615, 0.0097), (0.0194, 0.0000, 0.0562),
                          (0.5771, 0.0000, 0.5771), (0.2540, 0.0646, 0.0331), (0.0497, 0.0168, 0.0136),
                          (0.3185, 0.0194, 0.0000), (1.0000, 0.0000, 0.0000), (0.0000, 1.0000, 0.0000),
                          (0.0000, 0.0529, 0.3185), (1.0000, 1.0000, 1.0000), (1.0000, 1.0000, 0.0000),
                          (0.1274, 0.7156, 1.0000), (0.0562, 1.0000, 0.3660), (1.0000, 0.3801, 0.3801),
                          (0.7756, 0.4119, 0.1908), (1.0000, 1.0000, 0.1246), (0.0000, 0.3185, 0.0884),
                          (0.3559, 0.1444, 0.0295), (0.3424, 0.3559, 0.0295), (0.1378, 0.3559, 0.0295),
                          (0.0295, 0.3559, 0.1096), (0.0295, 0.3559, 0.3559), (0.0295, 0.1357, 0.3559),
                          (0.1587, 0.0295, 0.3559), (0.3559, 0.0295, 0.1444)]


TRACKER_COLOR_ATTR_NAME = 'colorTrack'
TRACKER_COLOR_DEFAULT_ATTR_NAME = 'colorTrackDefault'
ALL_COLOR_TRACKER_ATTRIBUTE_NAMES = [TRACKER_COLOR_ATTR_NAME, TRACKER_COLOR_DEFAULT_ATTR_NAME]


class MayaWireColors(object):
    """
    Class that defines predefined colors of Maya wireframe
    """

    Orange = 1
    DarkYellow = 2
    LightGreen = 3
    Green = 4
    LightBlue = 5
    Blue = 6
    Purple = 7
    Pink = 8


def get_color(color):
    """
    Returns a valid QColor from the given color
    :param color: variant, list || tuple || QColor
    :return: QColor
    """

    if type(color) == QColor:
        return color
    else:
        return QColor.fromRgba(*color)


def get_rig_color(rig_type='fk', side='center'):
    """
    Return a color given a rig type
    :param rig_type: str, Rig type ('fk' or 'ik')
    :param side: str, Rig side ('left', 'right', or 'center')
    """

    if rig_type == 'fk' or rig_type == 'FK':
        if side == 'left' or side == 'Left' or side == 'L' or side == 'l' or side == 'Lt':
            rig_color = QColor.fromRgbF(0.7, 0.4, 0.7)
            rig_color.ann = 'LtFK Color'
        elif side == 'right' or side == 'Right' or side == 'R' or side == 'r' or side == 'Rt':
            rig_color = QColor.fromRgbF(0.7, 0.4, 0.4)
            rig_color.ann = 'RtFK Color'
        else:
            rig_color = QColor.fromRgbF(0.7, 0.7, 0.4)
            rig_color.ann = 'CnFK Color'
    else:
        if side == 'left' or side == 'Left' or side == 'L' or side == 'l' or side == 'Lt':
            rig_color = QColor.fromRgbF(0.4, 0.5, 0.7)
            rig_color.ann = 'LtIK Color'
        elif side == 'right' or side == 'Right' or side == 'R' or side == 'r' or side == 'Rt':
            rig_color = QColor.fromRgbF(0.7, 0.4, 0.7)
            rig_color.ann = 'RtIK Color'
        else:
            rig_color = QColor.fromRgbF(0.4, 0.7, 0.4)
            rig_color.ann = 'CnIK Color'

    return rig_color


def get_mirror_rig_color_by_type(rig_type='fk', side='center'):
    """
    Returns a mirror color given a  type and a side
    :param rig_type: str, Rig type ('fk' or 'ik')
    :param side: str, Rig side ('left', 'right', or 'center')
    """

    rig_colors = dict()
    for rig_type_ in ['fk', 'ik']:
        rig_colors[rig_type_] = dict
        for side_ in ['left', 'right', 'center']:
            rig_colors[rig_type_][side_] = get_rig_color(rig_type=rig_type_, side=side_)

    if side == 'left':
        mirror_side = 'right'
    elif side == 'right':
        mirror_side = 'left'
    else:
        mirror_side = side

    try:
        return rig_colors[rig_type][mirror_side]
    except Exception:
        return rig_colors['fk']['center']


def get_mirror_rig_color_by_color(cl):
    """
    Returns a rig mirror color from a given color. If the color is not found in the mirror colors
    the function will return the complementary color of the given color
    :param cl: QColor
    """

    from tpDcc.libs.qt.core import color as color_utils

    rig_colors = dict()
    for rig_type in ['fk', 'ik']:
        rig_colors[rig_type] = dict
        for side in ['left', 'right', 'center']:
            rig_colors[rig_type][side] = get_rig_color(rig_type=rig_type, side=side)

    for rig_type, side_colors in rig_colors.items():
        for side, rig_color in side_colors.items():
            if side == 'left':
                mirror_side = 'right'
            elif side == 'right':
                mirror_side = 'left'
            else:
                mirror_side = side
            if cl == rig_color:
                return rig_colors[rig_type][mirror_side]
            elif cl == rig_color.lighter():
                return rig_colors[rig_type][mirror_side].lighter()
            elif cl == rig_color.darker():
                return rig_colors[rig_type][mirror_side].darker()
            else:
                return color_utils.Color.get_complementary_color(cl)


def convert_maya_color_string_to_index(color_nice_name):
    """
    Given a color nice name, returns the Maya index number (from 0 to 30)
    :param color_nice_name: str, name of the color
    :return: int, Maya's color as an index
    """

    if color_nice_name not in MAYA_COLOR_NAMES:
        return -1

    return MAYA_COLOR_NAMES.index(color_nice_name)


def convert_maya_color_index_to_rgb(color_index, linear=True):
    """
    Returns RGB color value of the given color index
    :param color_index: int, Maya's index color
    :param linear: bool, Whether or not the RGB should be in linear space (matches viewport color)
    :return: tuple(float, float, float), tuple of floats in 0-1 range
    """

    if color_index > len(MAYA_COLORS_LINEAR_RGB) - 1:
        return None

    return MAYA_COLORS_LINEAR_RGB[color_index] if linear else MAYA_COLORS_SRGB[color_index]


def convert_maya_color_string_to_rgb(color_nice_name, linear=True):
    """
    Returns RGB color value of the given color nice name
    :param color_nice_name: str, Maya's color nice name
    :param linear: bool, Whether or not the RGB should be in linear space (matches viewport color)
    :return: tuple(float, float, float), tuple of floats in 0-1 range
    """

    color_index = convert_maya_color_string_to_index(color_nice_name)

    return convert_maya_color_index_to_rgb(color_index, linear=linear) if color_index is not None else None


def add_color_tracker_attributes(node_name, rgb_color):
    """
    Adds color tracker attributes to the given node
    :param node_name: str, name of Maya node to track color of
    :param rgb_color: tuple(float, float, float), initial color as linear float
    """

    for i, attr_name in enumerate(ALL_COLOR_TRACKER_ATTRIBUTE_NAMES):
        if not maya.cmds.attributeQuery(attr_name, node=node_name, exists=True):
            maya.cmds.addAttr(node_name, longName=attr_name, attributeType='double3')
            for color_channel in 'RGB':
                axis_attr = '{}{}'.format(attr_name, color_channel)
                if not maya.cmds.attributeQuery(axis_attr, node=node_name, exists=True):
                    maya.cmds.addAttr(node_name, longName=axis_attr, attributeType='double', parent=attr_name)

    if rgb_color:
        maya.cmds.setAttr('.'.join([node_name, TRACKER_COLOR_ATTR_NAME]), rgb_color[0], rgb_color[1], rgb_color[2])
        maya.cmds.setAttr(
            '.'.join([node_name, TRACKER_COLOR_DEFAULT_ATTR_NAME]), rgb_color[0], rgb_color[1], rgb_color[2])
