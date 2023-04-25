#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains vector3 implementation
"""

import math


class Vector3(object):
    def __init__(self, x=1.0, y=1.0, z=1.0):

        self.x = None
        self.y = None
        self.z = None

        x_test = x

        if type(x_test) == list or type(x_test) == tuple:
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]

        if type(x_test) == float or type(x_test) == int:
            self.x = x
            self.y = y
            self.z = z

        if isinstance(x_test, Vector3):
            self.x = x_test.x
            self.y = x_test.y
            self.z = x_test.z

    def _add(self, value):
        if type(value) == float or type(value) == int:
            return Vector3(self.x + value, self.y + value, self.z + value)

        if type(self) == type(value):
            return Vector3(value.x + self.x, value.y + self.y, value.z + self.z)

        if type(value) == list:
            return Vector3(self.x + value[0], self.y + value[1], self.z + value[2])

    def _sub(self, value):
        if type(value) == float or type(value) == int:
            return Vector3(self.x - value, self.y - value, self.z - value)

        if type(self) == type(value):
            return Vector3(self.x - value.x, self.y - value.y, self.z - value.z)

        if type(value) == list:
            return Vector3(self.x - value[0], self.y - value[1], self.z - value[2])

    def _rsub(self, value):
        if type(value) == float or type(value) == int:
            return Vector3(value - self.x, value - self.y - value, value - self.z)

        if type(self) == type(value):
            return Vector3(value.x - self.x, value.y - self.y, value.z - self.z)

        if type(value) == list:
            return Vector3(value[0] - self.x, value[1] - self.y, value[2] - self.z)

    def _mult(self, value):
        if type(value) == float or type(value) == int:
            return Vector3(self.x * value, self.y * value, self.z * value)

        if type(self) == type(value):
            return Vector3(value.x * self.x, value.y * self.y, value.z * self.z)

        if type(value) == list:
            return Vector3(self.x * value[0], self.y * value[1], self.z * value[2])

    def __add__(self, value):
        return self._add(value)

    def __radd__(self, value):
        return self._add(value)

    def __sub__(self, value):
        return self._sub(value)

    def __rsub__(self, value):
        return self._sub(value)

    def __mul__(self, value):
        return self._mult(value)

    def __rmul__(self, value):
        return self._mult(value)

    def __call__(self):
        return [self.x, self.y, self.z]

    def get_vector(self):
        return [self.x, self.y, self.z]

    def list(self):
        return self.get_vector()


def get_axis_vector(axis_name, offset=1):
    """
    Returns axis vector from its name
    :param axis_name: name of the axis ('X', 'Y' or 'Z')
    :param offset: float, offset to the axis, by default is 1
    :return: list (1, 0, 0) = X | (0, 1, 0) = Y | (0, 0, 1) = Z
    """

    if axis_name in ['X', 'x']:
        return offset, 0, 0
    elif axis_name in ['Y', 'y']:
        return 0, offset, 0
    elif axis_name in ['Z', 'z']:
        return 0, 0, 1


def check_vector(vector):
    """
    Returns new Vector object from the given vector
    :param vector: variant, list<float, float, float> || Vector
    :return: Vector
    """

    if isinstance(vector, Vector3):
        return vector

    return Vector3(vector[0], vector[1], vector[2])


def vector_add(vector1, vector2):
    """
    Adds one vector to another
    :param vector1: list(float, float, float)
    :param vector2: list(float, float, float)
    :return: list(float, float, float)
    """

    return [vector1[0] + vector2[0], vector1[1] + vector2[1], vector1[2] + vector2[2]]


def vector_sub(vector1, vector2):
    """
    Subtracts one vector to another
    :param vector1: list(float, float, float)
    :param vector2: list(float, float, float)
    :return: list(float, float, float)
    """

    return [vector1[0] - vector2[0], vector1[1] - vector2[1], vector1[2] - vector2[2]]


def vector_multiply(vector, value):
    """
    Multiples given vector by a value
    :param vector: list(float, float, float)
    :param value: float ,value to multiple vector by
    :return: list(float, float, float)
    """

    result = [vector[0] * value, vector[1] * value, vector[2] * value]

    return result


def vector_divide(vector, value):
    """
    Divides given vector by a value
    :param vector: list(float, float, float)
    :param value: float ,value to multiple vector by
    :return: list(float, float, float)
    """

    result = [vector[0] / value, vector[1] / value, vector[2] / value]

    return result


def vector_magnitude(vector):
    """
    Returns the magnitude of a vector
    :param vector: list(float, float, float)
    :return:  float
    """

    magnitude = math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)

    return magnitude


def vector_normalize(vector):
    """
    Normalizes given vector
    :param vector: list(float, float, float)
    :return: list(float, float, float)
    """

    return vector_divide(vector, vector_magnitude(vector))


def get_distance_between_vectors(vector1, vector2):
    """
    Returns the distance bewteen two vectors
    :param vector1: list(float, float, float)
    :param vector2: list(float, float, float)
    :return: float
    """

    vector1 = Vector3(vector1)
    vector2 = Vector3(vector2)
    vector = vector1 - vector2
    dst = vector()

    return math.sqrt((dst[0] * dst[0]) + (dst[1] * dst[1]) + (dst[2] * dst[2]))


def get_distance_between_vectors_before_sqrt(vector1, vector2):
    """
    Returns the distance bewteen two vectors before applying square root
    :param vector1: list(float, float, float)
    :param vector2: list(float, float, float)
    :return: float
    """

    vector1 = Vector3(vector1)
    vector2 = Vector3(vector2)
    vector = vector1 - vector2
    dst = vector()

    return (dst[0] * dst[0]) + (dst[1] * dst[1]) + (dst[2] * dst[2])


def get_dot_product(vector1, vector2):
    """
    Returns the dot product of the two vectors
    :param vector1: Vector
    :param vector2: Vector
    :return: float, dot product between the two vectors
    """

    v1 = check_vector(vector1)
    v2 = check_vector(vector2)
    return (v1.x * v2.x) + (v1.y * v2.y) + (v1.z * v2.z)


def get_dot_product_2d(vector1_2d, vector2_2d):
    """
    Returns the dot product of the two vectors
    :param vector1_2d: Vector2D
    :param vector2_2d: Vector2D
    :return: float, dot product between the two vectors
    """

    v1 = check_vector(vector1_2d)
    v2 = check_vector(vector2_2d)

    return (v1.x * v2.x) + (v1.y * v2.y)


def get_mid_point(vector1, vector2):
    """
    Get the mid vector between 2 vectors
    :param vector1: list<float, float, float>
    :param vector2: list<float, float, float>
    :return: list<float, float, float>, midpoint vector between vector1 and vector2
    """

    values = list()
    for i in range(0, 3):
        values.append(get_average([vector1[i], vector2[i]]))

    return values


def get_average(numbers):
    """
    Returns the average value of the given numbers list
    :param numbers: list<float>, list of the floats to get average from
    :return: float, average of the floats in numbers list
    """

    total = 0.0
    for num in numbers:
        total += num

    return total / len(numbers)


def get_inbetween_vector(vector1, vector2, percent=0.5):
    """
    Returns a vector inbetween vector1 and vector2 at the given percent
    :param vector1: list(float, float, float), vector
    :param vector2: list(float, float, float), vector
    :param percent: float, percent the vector should be between vector1 and vector2.
        - 0 percent will be exactly on vector1
        - 1 percent will be exactly on vector2
        - 0.5 percent will be exactly in the mid point between vector1 and vector2
    :return:  list(float, float, float), vector that represents the vector at the percentage between vector and vector2
    """

    vector1 = Vector3(vector1)
    vector2 = Vector3(vector2)
    percent = 1 - percent
    vector = ((vector1 - vector2) * percent) + vector2

    return vector()
