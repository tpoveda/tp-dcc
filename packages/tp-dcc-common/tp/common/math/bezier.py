#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains bezier related functions
"""

import math


def binomial(i, n):
    return math.factorial(n) / float(math.factorial(i) * math.factorial(n - i))


def bernstein(t, i, n):
    return binomial(i, n) * (t ** i) * ((1 - t) ** (n - i))


def bezier(t, points):
    n = len(points) - 1
    x = 0
    y = 0
    for i, pos in enumerate(points):
        bern = bernstein(t, i, n)
        x += pos[0] * bern
        y += pos[1] * bern

    return x, y


def bezier_curve_y_from_x(index_x, points):

    def take_closest(num, collection):
        return min(collection, key=lambda x_num: abs(x_num - num))

    full_list = dict()
    for i in range(101):
        x, y = bezier(i * 0.01, points)
        full_list[x] = y
    if index_x in full_list:
        return full_list[index_x]

    closest_number = take_closest(index_x, list(full_list.keys()))
    return full_list[closest_number]


def bezier_curve_range(n, points):
    for i in range(n):
        t = i / float(n - 1)
        yield bezier(t, points)


def get_data_on_percentage(percentage, points_list):
    base_size = points_list[-1][0]

    return bezier_curve_y_from_x(percentage * base_size, points_list) / base_size
