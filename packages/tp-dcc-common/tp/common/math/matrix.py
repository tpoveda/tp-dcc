#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains matrix related functions
"""

from __future__ import print_function, division, absolute_import

import math


def rotation_matrix_xyz(rotation_angles):
    """
    Converts given rotation angles to a rotation represented by the sequences of rotations  around XYZ with given angles
    """

    rad_angles = [math.radians(x) for x in rotation_angles]
    x_angle = rad_angles[0]
    y_angle = rad_angles[1]
    z_angle = rad_angles[2]
    s1, c1 = math.sin(z_angle), math.cos(z_angle)
    s2, c2 = math.sin(y_angle), math.cos(y_angle)
    s3, c3 = math.sin(x_angle), math.cos(x_angle)

    m = ((c1 * c2, c1 * s2 * s3 - c3 * s1, s1 * s3 + c1 * c3 * s2),
         (c2 * s1, c1 * c3 + s1 * s2 * s3, c3 * s1 * s2 - c1 * s3),
         (- s2, c2 * s3, c2 * c3))

    return m


def rotation_matrix_xzy(rotation_angles):
    """
    Converts given rotation angles to a rotation represented by the sequences of rotations  around XZY with given angles
    """

    rad_angles = [math.radians(x) for x in rotation_angles]
    x_angle = rad_angles[0]
    y_angle = rad_angles[1]
    z_angle = rad_angles[2]
    s1, c1 = math.sin(z_angle), math.cos(z_angle)
    s2, c2 = math.sin(y_angle), math.cos(y_angle)
    s3, c3 = math.sin(x_angle), math.cos(x_angle)

    m = ((c1 * c2, s1 * s3 - c1 * c3 * s2, c3 * s1 + c1 * s2 * s3),
         (s2, c2 * c3, -c2 * s3),
         (-c2 * s1, c1 * s3 + c3 * s1 * s2, c1 * c3 - s1 * s2 * s3))

    return m


def rotation_matrix_to_xyz_euler(rotation_matrix):
    """
    Extracts XYZ euler angles from given rotation matrix
    """

    sy = math.sqrt(rotation_matrix[0][0] * rotation_matrix[0][0] + rotation_matrix[1][0] * rotation_matrix[1][0])
    singular = sy < 1e-7
    if not singular:
        x = math.degrees(math.atan2(rotation_matrix[2][1], rotation_matrix[2][2]))
        y = math.degrees(math.atan2(-rotation_matrix[2][0], sy))
        z = math.degrees(math.atan2(rotation_matrix[1][0], rotation_matrix[0][0]))
    else:
        x = math.degrees(math.atan2(-rotation_matrix[1][2], rotation_matrix[1][1]))
        y = math.degrees(math.atan2(-rotation_matrix[2][0], sy))
        z = 0

    return [x, y, z]


def rotation_matrix_to_xzy_euler(rotation_matrix):
    """
    Extracts XZY euler angles from given rotation matrix
    """

    sy = math.sqrt(rotation_matrix[0][0] * rotation_matrix[0][0] + rotation_matrix[2][0] * rotation_matrix[2][0])
    singular = sy < 1e-7
    if not singular:
        x = math.degrees(math.atan2(-rotation_matrix[1][2], rotation_matrix[1][1]))
        y = math.degrees(math.atan2(rotation_matrix[1][0], sy))
        z = math.degrees(math.atan2(-rotation_matrix[2][0], rotation_matrix[0][0]))
    else:
        x = math.degrees(math.atan2(-rotation_matrix[1][2], rotation_matrix[1][1]))
        y = math.degrees(math.atan2(rotation_matrix[1][0], sy))
        z = 0

    return [x, y, z]
