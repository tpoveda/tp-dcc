# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains MotionBuilder Python functions related with animation
"""

from tp.mobu.core import node as node_utils


def get_animation_node(node, transform='Translation'):
    """
    Returns animation node of the given model
    :param node: FBModel
    :param transform: str, transformation type to return animation node of
    :return:
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return None

    animation_node = None
    if transform == 'Translation':
        animation_node = node.Translation.GetAnimationNode()
    if transform == 'Rotation':
        animation_node = node.Rotation.GetAnimationNode()
    if transform == 'Scaling':
        animation_node = node.Scaling.GetAnimationNode()

    return animation_node
