#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utils functions used by tpDcc-libs-qt
"""


def clamp(number, min_value=0.0, max_value=1.0):
    """
    Clamps a number between two values
    :param number: number, value to clamp
    :param min_value: number, maximum value of the number
    :param max_value: number, minimum value of the number
    :return: variant, int || float
    """

    return max(min(number, max_value), min_value)


def get_range_percentage(min_value, max_value, value):
    """
    Returns the percentage value along a line from min_vlaue to max_value that value is
    :param min_value: float, minimum value
    :param max_value: float, maximum value
    :param value: float, input value
    :return: Percentage (from 0.0 to 1.0) between the two values where input value is
    """

    try:
        return (value - min_value) / (max_value - min_value)
    except ZeroDivisionError:
        return 0.0


def lerp(start, end, alpha):
    """
    Computes a linear interpolation between two values
    :param start: start value to interpolate from
    :param end:  end value to interpolate to
    :param alpha: how far we want to interpolate (0=start, 1=end)
    :return: float, result of the linear interpolation
    """

    # return (1 - alpha) * start + alpha * end
    return start + alpha * (end - start)


def map_range_unclamped(value, in_range_a, in_range_b, out_range_a, out_range_b):
    """
    Returns value mapped from one range into another where the value
    For example, 0.5 normalized from the range 0:1 to 0:50 would result in 25
    :param value: float
    :param in_range_a: float
    :param in_range_b: float
    :param out_range_a: float
    :param out_range_b: float
    :return: float
    """

    clamped_percentage = get_range_percentage(in_range_a, in_range_b, value)
    return lerp(out_range_a, out_range_b, clamped_percentage)
