#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains bounding box implementation
"""

from tp.common.math import vec3


class BoundingBox(object):
    """
    Util class to work with bounding box
    """

    def __init__(self, bottom_corner_list=None, top_corner_list=None):
        """
        Constructor
        :param bottom_corner_list: list<float, float, float>, vector of bounding box bottom corner
        :param top_corner_list: list<float, float, float>, vector of bounding box top corner
        """

        self._create_bounding_box(bottom_corner_list, top_corner_list)

    def _create_bounding_box(self, bottom_corner_list, top_corner_list):
        """
        Initializes bounding box
        :param bottom_corner_list: list<float, float, float>, vector of bounding box bottom corner
        :param top_corner_list: list<float, float, float>, vector of bounding box top corner
        """

        self.min_vector = [bottom_corner_list[0], bottom_corner_list[1], bottom_corner_list[2]]
        self.max_vector = [top_corner_list[0], top_corner_list[1], top_corner_list[2]]
        self.opposite_min_vector = [top_corner_list[0], bottom_corner_list[1], top_corner_list[2]]
        self.opposite_max_vector = [bottom_corner_list[0], top_corner_list[1], bottom_corner_list[2]]

    def get_center(self):
        """
        Returns the center of the bounding box in a list
        :return: list<float, float, float>
        """

        return vec3.get_mid_point(self.min_vector, self.max_vector)

    def get_ymax_center(self):
        """
        Returns the top center of the bounding box in a list
        :return: list<float, float, float>
        """

        return vec3.get_mid_point(self.max_vector, self.opposite_max_vector)

    def get_ymin_center(self):
        """
        Returns the bottom center of the bounding box in a list
        :return: list<float, float, float>
        """

        return vec3.get_mid_point(self.min_vector, self.opposite_min_vector)

    def get_size(self):
        """
        Returns the size of the bounding box
        :return: float
        """

        return vec3.get_distance_between_vectors(self.min_vector, self.max_vector)


def bounding_box_half_values(bbox_min, bbox_max):
    """
    Returns the values half way between max and min XYZ given tuples
    :param bbox_min: tuple, contains the minimum X,Y,Z values of the mesh bounding box
    :param bbox_max: tuple, contains the maximum X,Y,Z values of the mesh bounding box
    :return: tuple(int, int, int)
    """

    min_x, min_y, min_z = bbox_min
    max_x, max_y, max_z = bbox_max
    half_x = (min_x + max_x) * 0.5
    half_y = (min_y + max_y) * 0.5
    half_z = (min_z + max_z) * 0.5

    return half_x, half_y, half_z
