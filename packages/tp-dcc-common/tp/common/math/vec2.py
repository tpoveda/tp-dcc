#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains vector3 implementation
"""

import math


class Vector2(object):
    def __init__(self, x=1.0, y=1.0):
        self.x = None
        self.y = None

        if type(x) == list or type(x) == tuple:
            self.x = x[0]
            self.y = x[1]

        if type(x) == float or type(x) == int:
            self.x = x
            self.y = y

        self.magnitude = None

    def _add(self, value):
        if type(value) == float or type(value) == int:
            return Vector2(self.x + value, self.y + value)

        if type(self) == type(value):
            return Vector2(value.x + self.x, value.y + self.y)

        if type(value) == list:
            return Vector2(self.x + value[0], self.y + value[1])

    def _sub(self, value):
        if type(value) == float or type(value) == int:
            return Vector2(self.x - value, self.y - value)

        if type(self) == type(value):
            return Vector2(self.x - value.x, self.y - value.y)

        if type(value) == list:
            return Vector2(self.x - value[0], self.y - value[1])

    def _rsub(self, value):
        if type(value) == float or type(value) == int:
            return Vector2(value - self.x, value - self.y - value)

        if type(self) == type(value):
            return Vector2(value.x - self.x, value.y - self.y)

        if type(value) == list:
            return Vector2(value[0] - self.x, value[1] - self.y)

    def _mult(self, value):
        if type(value) == float or type(value) == int:
            return Vector2(self.x * value, self.y * value)

        if type(self) == type(value):
            return Vector2(value.x * self.x, value.y * self.y)

        if type(value) == list:
            return Vector2(self.x * value[0], self.y * value[1])

    def _divide(self, value):
        if type(value) == float or type(value) == int:
            return Vector2(self.x / value, self.y / value)

        if type(self) == type(value):
            return Vector2(value.x / self.x, value.y / self.y)

        if type(value) == list:
            return Vector2(self.x / value[0], self.y / value[1])

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
        return [self.x, self.y]

    def __div__(self, value):
        return self._divide(value)

    def _reset_data(self):
        self.magnitude = None

    def normalize(self, in_place=False):
        if not self.magnitude:
            self.magnitude()

        vector = self._divide(self.magnitude)

        if in_place:
            self.x = vector.x
            self.y = vector.y
            self._reset_data()

        if not in_place:
            return vector

    def get_vector(self):
        return [self.x, self.y]

    def get_magnitude(self):
        self.magnitude = math.sqrt((self.x * self.x) + (self.y * self.y))
        return self.magnitude

    def get_distance(self, x=0.0, y=0.0):
        other = Vector2(x, y)

        offset = self - other

        return offset.get_magnitude()


def check_vector_2d(vector):
    """
    Returns new Vector2D object from the given vector
    :param vector: variant, list<float, float> || Vector
    :return: Vector
    """

    if isinstance(vector, Vector2):
        return vector

    return Vector2(vector[0], vector[1])


def get_distance_2d(vector1_2d, vector2_2d):
    """
    Returns the distance between two 2D vectors
    :param vector1_2d: Vector2D
    :param vector2_2d: Vector2D
    :return: float, distance between the two 2D vectors
    """

    v1 = check_vector_2d(vector1_2d)
    v2 = check_vector_2d(vector2_2d)

    v = v1 - v2
    dst = v()

    return math.sqrt(dst[0] * dst[0]) + (dst[1] * dst[1])
