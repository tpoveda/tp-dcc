#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with transforms for MotionBuilder
"""

import pyfbsdk

from tp.core import log
from tp.mobu.core import node as node_utils

logger = log.tpLogger


INVERSE_MATRIX_TYPE_DICT = dict(
    Transformation=pyfbsdk.FBModelTransformationType.kModelInverse_Transformation,
    Translation=pyfbsdk.FBModelTransformationType.kModelInverse_Translation,
    Rotation=pyfbsdk.FBModelTransformationType.kModelInverse_Rotation,
    Scaling=pyfbsdk.FBModelTransformationType.kModelInverse_Scaling)
#   Center=FBModelTransformationType.kModelCenter,
#   All=FBModelTransformationType.kModelAll)


MATRIX_TYPE_DICT = dict(
    Transformation=pyfbsdk.FBModelTransformationType.kModelTransformation,
    Translation=pyfbsdk.FBModelTransformationType.kModelTranslation,
    Rotation=pyfbsdk.FBModelTransformationType.kModelRotation,
    Scaling=pyfbsdk.FBModelTransformationType.kModelScaling)
#   ParentOffset=FBModelTransformationType.kModelParentOffset)
#   Center=FBModelTransformationType.kModelCenter,
#   All=FBModelTransformationType.kModelAll)


def get_children(node):
    """
    Returns children of the given node
    :param node: FBModel
    :return: list(FBModel)
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return list()

    return node.Children


def get_parent(node):
    """
    Returns parent of the given node
    :param node: FBModel
    :return: FBModel or None
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return None

    return node.Parent


def get_matrix(node, world_space=False, matrix_type='Transformation'):
    """
    Returns node matrix
    :param node: FBModel
    :param world_space: bool, Whether to return the matrix in world or local space
    :param matrix_type: str, matrix type to return ('Transformation', 'Translation', 'Rotation', 'Scaling', ...)
    :return: FBMatrix or None
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return None

    matrix = pyfbsdk.FBMatrix()
    try:
        node.GetMatrix(matrix, MATRIX_TYPE_DICT[matrix_type], world_space)
    except IndexError:
        logger.warning('Invalid matrix type "{}". Valid types are: "{}"'.format(
            matrix_type, ', '.join(list(MATRIX_TYPE_DICT.keys()))))
        return None

    return matrix


def set_matrix(node, matrix, world_space=False, matrix_type='Transformation'):
    """
    Sets node matrix
    :param node: FBModel
    :param matrix: FBMatrix
    :param world_space: bool, Whether to set the matrix in world or local space
    :param matrix_type: str, matrix type to set ('Transformation', 'Translation', 'Rotation', 'Scaling', ...)
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return

    try:
        node.SetMatrix(matrix, MATRIX_TYPE_DICT[matrix_type], world_space)
    except IndexError:
        logger.warning('Invalid matrix type "{}". Valid types are: "{}"'.format(
            matrix_type, ', '.join(list(MATRIX_TYPE_DICT.keys()))))


def get_inverse_matrix(node, world_space=False, matrix_type='Transformation'):
    """
    Returns inverse matrix
    :param node: FBModel
    :param world_space: bool, Whether to return the matrix in world or local space
    :param matrix_type: str, matrix type to return ('Transformation', 'Translation', 'Rotation', 'Scaling', ...)
    :return: FBMatrix or None
    :return: FBMatrix or None
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return None

    matrix = pyfbsdk.FBMatrix()
    try:
        node.GetMatrix(matrix, INVERSE_MATRIX_TYPE_DICT[matrix_type], world_space)
    except IndexError:
        logger.warning('Invalid inverse matrix type "{}". Valid types are: "{}"'.format(
            matrix_type, ', '.join(list(INVERSE_MATRIX_TYPE_DICT.keys()))))
        return None

    return matrix


def set_inverse_matrix(node, matrix, world_space=False, matrix_type='Transformation'):
    """
    Sets node inverse matrix
    :param node: FBModel
    :param matrix: FBMatrix
    :param world_space: bool, Whether to set the matrix in world or local space
    :param matrix_type: str, matrix type to set ('Transformation', 'Translation', 'Rotation', 'Scaling', ...)
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return

    try:
        node.SetMatrix(matrix, INVERSE_MATRIX_TYPE_DICT[matrix_type], world_space)
    except IndexError:
        logger.warning('Invalid inverse matrix type "{}". Valid types are: "{}"'.format(
            matrix_type, ', '.join(list(INVERSE_MATRIX_TYPE_DICT.keys()))))


def get_translation(node, world_space=False):
    """
    Returns node translation vector
    :param node: FBModel
    :param world_space: bool, Whether to return the vector in world or local space.
    :return: FBVector3d or None
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return None

    vector = pyfbsdk.FBVector3d()
    node.GetVector(vector, MATRIX_TYPE_DICT['Translation', world_space])

    return vector


def set_translation(node, vector, world_space=False):
    """
    Sets node translation vector
    :param node: FBModel
    :param vector: FBVector3d
    :param world_space: bool, Whether to set the vector in world or local space.
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return

    node.SetVector(vector, MATRIX_TYPE_DICT['Translation'], world_space)


def get_rotation(node, world_space=False):
    """
    Returns node rotation vector
    :param node: FBModel
    :param world_space: bool, Whether to return the vector in world or local space.
    :return: FBVector3d or None
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return None

    vector = pyfbsdk.FBVector3d()
    node.GetVector(vector, MATRIX_TYPE_DICT['Rotation', world_space])

    return vector


def set_rotation(node, vector, world_space=False):
    """
    Sets node rotation vector
    :param node: FBModel
    :param vector: FBVector3d
    :param world_space: bool, Whether to set the vector in world or local space.
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return

    node.SetVector(vector, MATRIX_TYPE_DICT['Rotation'], world_space)


def get_scale(node, world_space=False):
    """
    Returns node scale vector
    :param node: FBModel
    :param world_space: bool, Whether to return the vector in world or local space.
    :return: FBVector3d or None
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return None

    vector = pyfbsdk.FBVector3d()
    node.GetVector(vector, MATRIX_TYPE_DICT['Scaling', world_space])

    return vector


def set_scale(node, vector, world_space=False):
    """
    Sets node scale vector
    :param node: FBModel
    :param vector: FBVector3d
    :param world_space: bool, Whether to set the vector in world or local space.
    """

    node = node_utils.get_model_node_by_name(node)
    if not node:
        return

    node.SetVector(vector, MATRIX_TYPE_DICT['Scaling'], world_space)

