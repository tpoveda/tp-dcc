#! /usr/bin/env python

"""
Utility methods related to Maya matrix operations
"""


import math

import maya.api.OpenMaya

from tp.maya.om import mathlib


def create_matrix_from_list(values_list):
    """
    Creates a new matrix from given list of values
    :param values_list: list(flaot)
    :return: OpenMaya.MMatrix
    """

    if len(values_list) != 16:
        raise Exception('Invalid list of values. Expecting 16 elements, found: {}'.format(len(values_list)))

    matrix = maya.api.OpenMaya.MMatrix()
    maya.api.OpenMaya.MScriptUtil.createMatrixFromList(values_list, matrix)

    return matrix


def get_matrix_as_list(matrix):
    """
    Retu9rns the given mamtrix as list of components
    :param matrix: OpenMaya.MMatrix
    :return: list(float)
    """

    return [
        matrix(0, 0), matrix(0, 1), matrix(0, 2), matrix(0, 3),
        matrix(1, 0), matrix(1, 1), matrix(1, 2), matrix(1, 3),
        matrix(2, 0), matrix(2, 1), matrix(2, 2), matrix(2, 3),
        matrix(3, 0), matrix(3, 1), matrix(3, 2), matrix(3, 3)
    ]


def set_matrix_cell(matrix, value, row, column):
    """
    Sets a MMatrix cell
    :param matrix:  MMatrix, matrix to set cell
    :param value: variant, value to set cell
    :param row: int, matrix row number
    :param column: int, matrix, column number
    """

    matrix[row][column] = value


def set_matrix_row(matrix, vector, row):
    """
    Sets a matrix row with an MVector or MPoint
    :param matrix: MMatrix, matrix to set row
    :param vector: MVector || MPoint, vector to set matrix row to
    :param row: int, matrix row number
    """

    set_matrix_cell(matrix, vector.x, row, 0)
    set_matrix_cell(matrix, vector.y, row, 1)
    set_matrix_cell(matrix, vector.z, row, 2)


def get_translation(matrix):
    """
    Returns the translation component of a transform matrix
    :param matrix: OpenMaya.MMatrix, matrix to extract translation info from
    :return:
    """

    x = maya.api.OpenMaya.MScriptUtil.getDoubleArrayItem(matrix[3], 0)
    y = maya.api.OpenMaya.MScriptUtil.getDoubleArrayItem(matrix[3], 1)
    z = maya.api.OpenMaya.MScriptUtil.getDoubleArrayItem(matrix[3], 2)


def get_rotation(matrix, rotation_order='xyz'):
    """
    Returns the rotation component of a transform matrix
    :param matrix: OpenMaya.MMatrix, matrix to extract translation info from
    :param rotation_order: str or int, rotation order of the matrix
    :return:
    """

    radian = 180.0 / math.pi

    if isinstance(rotation_order, str):
        rotation_order = rotation_order.lower()
        rotate_order = {'xyz': 0, 'yzx': 1, 'zxy': 2, 'xzy': 3, 'yxz': 4, 'zyx': 5}
        if rotation_order not in rotate_order:
            raise Exception('Invalid given rotation order!')
        rotation_order = rotate_order[rotation_order]
    else:
        rotation_order = int(rotation_order)

    transform_matrix = maya.api.OpenMaya.MTransformationMatrix(matrix)
    euler_rotation = transform_matrix.eulerRotation()
    euler_rotation.reorderIt(rotation_order)

    return euler_rotation.x * radian, euler_rotation.y * radian, euler_rotation.z * radian


def build_matrix(translate=(0, 0, 0), x_axis=(1, 0, 0), y_axis=(0, 1, 0), z_axis=(0, 0, 1)):
    """
    Builds a transformation matrix based on the input vectors
    :param translate: tuple/list, translate values for the matrix
    :param x_axis: tuple/list, X axis of the matrix
    :param y_axis: tuple/list, Y axis of the matrix
    :param z_axis: tuple/list, Z axis of the matrix
    :return: MMatrix
    """

    matrix = maya.api.OpenMaya.MMatrix()
    values = list()

    if not isinstance(translate, maya.api.OpenMaya.MVector):
        translate = maya.api.OpenMaya.MVector(translate[0], translate[1], translate[2])
    if not isinstance(x_axis, maya.api.OpenMaya.MVector):
        x_axis = maya.api.OpenMaya.MVector(x_axis[0], x_axis[1], x_axis[2])
    if not isinstance(y_axis, maya.api.OpenMaya.MVector):
        y_axis = maya.api.OpenMaya.MVector(y_axis[0], y_axis[1], y_axis[2])
    if not isinstance(z_axis, maya.api.OpenMaya.MVector):
        z_axis = maya.api.OpenMaya.MVector(z_axis[0], y_axis[1], y_axis[2])

    set_matrix_row(matrix, x_axis, 0)
    set_matrix_row(matrix, y_axis, 1)
    set_matrix_row(matrix, z_axis, 2)
    set_matrix_row(matrix, translate, 3)

    return matrix


def build_rotation(aim_vector, up_vector=(0, 1, 0), aim_axis='x', up_axis='y'):
    """
    Build rotation matrix from the given inputs
    :param aim_vector: tuple or list, aim vector used to construct rotation matrix (world space)
    :param up_vector: tuple or list, up vector used to construct rotation matrix (world space)
    :param aim_axis: str, aim vector used to construct rotation matrix
    :param up_axis: str, up vector used to construct rotation matrix
    :return: OpenMaya.MMatrix
    """

    axis_list = ['x', 'y', 'z']

    if not axis_list.count(aim_axis):
        raise Exception('Aim axis is not valid!')
    if not axis_list.count(up_axis):
        raise Exception('Up axis is not valid!')
    if aim_axis == up_axis:
        raise Exception('Aim and Up axis must be different!')

    negative_aim = False
    negative_up = False

    if aim_axis[0] == '-':
        aim_axis = aim_axis[1]
        negative_aim = True
    if up_axis[0] == '-':
        up_axis = up_axis[1]
        negative_up = True

    # Get cross axis
    axis_list.remove(aim_axis)
    axis_list.remove(up_axis)
    cross_axis = axis_list[0]

    # Normalize vectors
    aim_vector = mathlib.normalize_vector(aim_vector)
    if negative_aim:
        aim_vector = (-aim_vector[0], -aim_vector[1], -aim_vector[2])
    up_vector = mathlib.normalize_vector(up_vector)
    if negative_aim:
        aim_vector = (-aim_vector[0], -aim_vector[1], -aim_vector[2])

    # Get cross product vector
    cross_vector = (0, 0, 0)
    if (aim_axis == 'x' and up_axis == 'z') or (aim_axis == 'z' and up_axis == 'y'):
        cross_vector = mathlib.cross_product(up_vector, aim_vector)
    else:
        cross_vector = mathlib.cross_product(aim_vector, up_vector)

    # Ortogonalize up vector
    if (aim_axis == 'x' and up_axis == 'z') or (aim_axis == 'z' and up_axis == 'y'):
        up_vector = mathlib.cross_product(aim_vector, cross_vector)
    else:
        up_vector = mathlib.cross_product(cross_vector, aim_vector)

    # Build rotation matrix
    axis_dict = {aim_axis: aim_vector, up_axis: up_vector, cross_axis: cross_vector}
    rotation_matrix = build_matrix(x_axis=axis_dict['x'], y_axis=axis_dict['y'], z_axis=axis_dict['z'])

    return rotation_matrix


def vector_matrix_multiply(vector, matrix, transform_as_point=False, invert_matrix=False):
    """
    Transforms a vector (or point) by a given transformation matrix
    :param vector: tuple or list, vector or point to be transformed
    :param matrix: OpenMaya.MMatrix, transformation matrix
    :param transform_as_point: bool, Whether transform vector as point or not
    :param invert_matrix: bool, Whether use matrix invertse to transform the vector or not
    :return:
    """

    if not isinstance(matrix, maya.api.OpenMaya.MMatrix):
        raise Exception('Matrix input variable is not a valid MMatrix object ({})'.format(type(matrix)))

    if transform_as_point:
        vector = maya.api.OpenMaya.MPoint(vector[0], vector[1], vector[2], 1.0)
    else:
        vector = maya.api.OpenMaya.Point(vector[0], vector[1], vector[2])

    # Transform matrix
    if matrix != maya.api.OpenMaya.identity:
        if invert_matrix:
            matrix = matrix.inverse()
        vector *= matrix

    return [vector.x, vector.y, vector.z]


def print_matrix(matrix):
    """
    Prints the given matrix with proper format
    :param matrix: OpenMaya.MMatrix
    """

    print('%.3f' % matrix(0, 0)) + ', ' + ('%.3f' % matrix(0, 1)) + ', ' + ('%.3f' % matrix(0, 2)) + ', ' + (
        '%.3f' % matrix(0, 3))
    print('%.3f' % matrix(1, 0)) + ', ' + ('%.3f' % matrix(1, 1)) + ', ' + ('%.3f' % matrix(1, 2)) + ', ' + (
        '%.3f' % matrix(1, 3))
    print('%.3f' % matrix(2, 0)) + ', ' + ('%.3f' % matrix(2, 1)) + ', ' + ('%.3f' % matrix(2, 2)) + ', ' + (
        '%.3f' % matrix(2, 3))
    print('%.3f' % matrix(3, 0)) + ', ' + ('%.3f' % matrix(3, 1)) + ', ' + ('%.3f' % matrix(3, 2)) + ', ' + (
        '%.3f' % matrix(3, 3))
