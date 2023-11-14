#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and class related with maths
"""

from __future__ import annotations

import math
import struct

MAX_INT = 2 ** (struct.Struct('i').size * 8 - 1) - 1


def is_equal(x, y, tolerance=0.000001) -> bool:
    """
    Checks if 2 float values are equal withing a given tolerance.

    :param float x: first value to compare.
    :param float y: second value to compare.
    :param float tolerance: comparison tolerance.
    :return: True if both values are equal.
    :rtype: bool
    """

    return abs(x - y) < tolerance


def is_close(x: float, y: float, relative_tolerance: float = 1e-03, absolute_tolerance: float = 1e-03) -> bool:
    """
    Returns whether two given numbers are relatively close.

    :param float x: first value to compare.
    :param float y: second value to compare.
    :param float relative_tolerance: relative tolerance.
    :param float absolute_tolerance: absolute tolerance.
    :return: True if both numbers are relatively close; False otherwise.
    :rtype: bool
    """

    return abs(x - y) <= max(relative_tolerance * max(abs(x), abs(y)), absolute_tolerance)


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


def clamp(number, min_value=0.0, max_value=1.0):
    """
    Clamps a number between two values
    :param number: number, value to clamp
    :param min_value: number, maximum value of the number
    :param max_value: number, minimum value of the number
    :return: variant, int || float
    """

    return max(min(number, max_value), min_value)


def remap_value(value, old_min, old_max, new_min, new_max):
    """
    Remap value taking into consideration its old range and the new one
    :param value: float
    :param old_min: float
    :param old_max: float
    :param new_min: float
    :param new_max: float
    :return: float
    """

    return new_min + (value - old_min) * (new_max - new_min) / (old_max - old_min)


def roundup(number, to):
    """
    Round up a number
    :param number: number to roundup
    :param to: number, mas value to roundup
    :return: variant, int || float
    """

    return int(math.ceil(number / to)) * to


def sign(value):
    """
    Returns the sign of the given value
    :param value: float
    :return: -1 of the value is negative; 1 if the value is positive; 0 if the value is zero
    """

    return value and (1, -1)[value < 0]


def mean_value(numbers):
    """
    Returns the mean/average value of the given numbers.

    :param list[int or float] numbers: list of numbers.
    :return: mean/average value.
    :rtype: int or float
    """

    return float(sum(numbers)) / max(len(numbers), 1)


def range_percentage(min_value, max_value, value):
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


def map_range_clamped(value, in_range_a, in_range_b, out_range_a, out_range_b):
    """
    Returns value mapped from one range into another where the value is clamped to the input range
    For example, 0.5 normalized from the range 0:1 to 0:50 would result in 25
    :param value: float
    :param in_range_a: float
    :param in_range_b: float
    :param out_range_a: float
    :param out_range_b: float
    :return: float
    """

    clamped_percentage = clamp(range_percentage(in_range_a, in_range_b, value), 0.0, 1.0)
    return lerp(out_range_a, out_range_b, clamped_percentage)


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

    clamped_percentage = range_percentage(in_range_a, in_range_b, value)
    return lerp(out_range_a, out_range_b, clamped_percentage)


def snap_value(input, snap_value):
    """
    Returns snap value given an input and a base snap value
    :param input: float
    :param snap_value: float
    :return: float
    """

    return round((float(input) / snap_value)) * snap_value


def fade_sine(percent_value):
    input_value = math.pi * percent_value

    return math.sin(input_value)


def fade_cosine(percent_value):
    percent_value = math.pi * percent_value

    return (1 - math.cos(percent_value)) * 0.5


def fade_smoothstep(percent_value):
    return percent_value * percent_value * (3 - 2 * percent_value)


def fade_sigmoid(percent_value):
    if percent_value == 0:
        return 0

    if percent_value == 1:
        return 1

    input_value = percent_value * 10 + 1

    return (2 / (1 + (math.e**(-0.70258 * input_value)))) - 1


def ease_in_sine(percent_value):
    return math.sin(1.5707963 * percent_value)


def ease_in_expo(percent_value):
    return (pow(2, 8 * percent_value) - 1) / 255


def ease_out_expo(percent_value, power=2):
    return 1 - pow(power, -8 * percent_value)


def ease_out_circ(percent_value):
    return math.sqrt(percent_value)


def ease_out_back(percent_value):
    return 1 + (--percent_value) * percent_value * (2.70158 * percent_value + 1.70158)


def ease_in_out_sine(percent_value):
    return 0.5 * (1 + math.sin(math.pi * (percent_value - 0.5)))


def easi_in_out_quart(percent_value):
    if percent_value < 0.5:
        percent_value *= percent_value
        return 8 * percent_value * percent_value
    else:
        percent_value -= 1
        percent_value *= percent_value
        return 1 - 8 * percent_value * percent_value


def ease_in_out_expo(percent_value):
    if percent_value < 0.5:
        return (math.pow(2, 16 * percent_value) - 1) / 510
    else:
        return 1 - 0.5 * math.pow(2, -16 * (percent_value - 0.5))


def ease_in_out_circ(percent_value):
    if percent_value < 0.5:
        return (1 - math.sqrt(1 - 2 * percent_value)) * 0.5
    else:
        return (1 + math.sqrt(2 * percent_value - 1)) * 0.5


def ease_in_out_back(percent_value):
    if percent_value < 0.5:
        return percent_value * percent_value * (7 * percent_value - 2.5) * 2
    else:
        return 1 + (percent_value - 1) * percent_value * 2 * (7 * percent_value + 2.5)


def average_position(pos1=(0.0, 0.0, 0.0), pos2=(0.0, 0.0, 0.0), weight=0.5):
    """
    Returns the average of the two given positions. You can weight between 0 (first input) or 1 (second_input)
    :param pos1: tuple, first input position
    :param pos2: tuple, second input position
    :param weight: float, amount to weight between the two input positions
    :return: tuple
    """

    return (
        pos1[0] + ((pos2[0] - pos1[0]) * weight),
        pos1[1] + ((pos2[1] - pos1[1]) * weight),
        pos1[2] + ((pos2[2] - pos1[2]) * weight)
    )


def smooth_step(value, range_start=0.0, range_end=1.0, smooth=1.0):
    """
    Interpolates between 2 float values using hermite interpolation
    :param value: float, value to smooth
    :param range_start: float, minimum value of interpolation range
    :param range_end: float, maximum value of interpolation range
    :param smooth: float, strength of the smooth applied to the value
    :return: float
    """

    # Get normalized value
    range_val = range_end - range_start
    normalized_val = value / range_val

    # Get smooth value
    smooth_val = pow(normalized_val, 2) * (3 - (normalized_val * 2))
    smooth_val = normalized_val + ((smooth_val - normalized_val) * smooth)
    value = range_start + (range_val * smooth_val)

    return value


def distribute_value(samples, spacing=1.0, range_start=0.0, range_end=1.0):
    """
    Returns a list of values distributed between a start and end range
    :param samples: int, number of values to sample across the value range
    :param spacing: float, incremental scale for each sample distance
    :param range_start: float, minimum value in the sample range
    :param range_end: float, maximum value in the sample range
    :return: list<float>
    """

    # Get value range
    value_list = [range_start]
    value_dst = abs(range_end - range_start)
    unit = 1.0

    # Find unit distance
    factor = 1.0
    for i in range(samples - 2):
        unit += factor * spacing
        factor *= spacing
    unit = value_dst / unit
    total_unit = unit

    # Build Sample list
    for i in range(samples - 2):
        mult_factor = total_unit / value_dst
        value_list.append(range_start - ((range_start - range_end) * mult_factor))
        unit *= spacing
        total_unit += unit

    # Append final sample
    value_list.append(range_end)

    return value_list


def inverse_distance_weight_1d(value_array, sample_value, value_domain=(0, 1), cycle_value=False):
    """
    Returns the inverse distance weight for a given sample point given an array of scalar values
    :param value_array: list<float>, value array to calculate weights from
    :param sample_value: float, sample point to calculate weights for
    :param value_domain: variant, tuple || list, minimum and maximum range of the value array
    :param cycle_value: bool, Whether to calculate or not the distance based on a closed loop of values
    :return: float
    """

    dst_array = list()
    total_inv_dst = 0.0

    # Calculate inverse distance weight
    for v in range(len(value_array)):
        dst = abs(sample_value - value_array[v])
        if cycle_value:
            value_domain_len = value_domain[1] - value_domain[0]
            f_cyc_dst = abs(sample_value - (value_array[v] + value_domain_len))
            r_cyc_dst = abs(sample_value - (value_array[v] - value_domain_len))
            if f_cyc_dst < dst:
                dst = f_cyc_dst
            if r_cyc_dst < dst:
                dst = r_cyc_dst

        # Check zero distance
        if dst < 0.00001:
            dst = 0.00001

        dst_array.append(dst)
        total_inv_dst += 1.0 / dst

    # Normalize value weights
    weight_array = [(1.0 / d) / total_inv_dst for d in dst_array]

    return weight_array


def max_index(numbers):
    """
    Returns the largest number in the given list of numbers
    :param numbers: list(int) or list (float) or list(str)
    :return: int or float or str
    """

    max_value = 0
    result = 0
    for i in numbers:
        current_value = abs(float(i))
        if current_value > max_value:
            max_value = current_value
            result = numbers.index(i)

    return result
