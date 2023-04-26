#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains generic color functionality
"""

import math
import colorsys


def clamp(number, min_value=0.0, max_value=1.0):
    """
    Clamps a number between two values
    :param number: number, value to clamp
    :param min_value: number, maximum value of the number
    :param max_value: number, minimum value of the number
    :return: variant, int || float
    """

    return max(min(number, max_value), min_value)


def convert_hsv_to_rgb(hsv):
    """
    Converts HSV (0-360, 0-1 ranges) values to RGB (0-1 range in SRGBFloats)
    :param hsv: list, hue, saturation, value in 0-360 range, saturation, value in 0-1 range
    :return: list, red, green, blue RGB values in 0-1 srgbFloat
    """

    return list(colorsys.hsv_to_rgb((hsv[0] / 360.0), hsv[1], hsv[2]))


def convert_rgb_to_hsv(rgb):
    """
    Converts RGB (0-1 range in SRGBFloats) to HSV (0-360, 0-1 ranges) values
    :param rgb: list, red, green, blue RGB values in 0-1 srgbFloat
    :return: list, hue, saturation, value in 0-360 range, saturation, value in 0-1 range
    """

    hsv = list(colorsys.rgb_to_hsv((rgb[0]), rgb[1], rgb[2]))
    hsv[0] *= 360.0

    return hsv


def convert_single_srgb_to_linear(color_value):
    """
    Changes a single RGB color to linear space
    :param color_value: float, a single value in 0-1 range (for example red channel)
    :return: float, new color converted to linear
    """

    a = 0.055
    if color_value <= 0.04045:
        return color_value * (1.0 / 12.92)

    return pow((color_value + a) * (1.0 / (1 + a)), 2.4)


def convert_single_linear_to_srgb(color_value):
    """
    Changes as single RGB color in linear to SRGB color space
    :param color_value:float, single color value in 0-1 range (for example red channel)
    :return:float, new color converted to SRGB
    """

    a = 0.055
    if color_value <= 0.0031308:
        return color_value * 12.92

    return (1 + a) * pow(color_value, 1 / 2.4) - a


def convert_color_srgb_to_linear(srgb_color):
    """
    Changes a SRGB color to linear color
    :param srgb_color: list(float, float, float), SRGB float color in list/tuple in 0-1 range
    :return: tuple(float, float, float), new color gamma converted to linear
    """

    return (
        convert_single_srgb_to_linear(srgb_color[0]),
        convert_single_srgb_to_linear(srgb_color[1]),
        convert_single_srgb_to_linear(srgb_color[2])
    )


def convert_color_linear_to_srgb(linear_rgb):
    """
    Changes a linear color to SRGB color
    :param linear_rgb: list(float, float, float), RGB color list/tuple in 0-1 range
    :return: tuple(float, float, flaot), new color gamma converted to SRGB
    """

    return (
        convert_single_linear_to_srgb(linear_rgb[0]),
        convert_single_linear_to_srgb(linear_rgb[1]),
        convert_single_linear_to_srgb(linear_rgb[2])
    )


def hex_to_rgba(hex_str):
    """
    Converts hexadecimal number to RGBA tuple in following formats:
        - "RRGGBB" (2F2F2F)
        - "AARRGGBB" (882F2F2F)
        - "RGB" (CCC)
    :param hex_str: str, hexadecimal string
    :return: tuple(float, float, float, float), color tuple (R, G, B, A)
    """

    if hex_str.startswith('#'):
        hex_str = hex_str[1:]

    if len(hex_str) == 8:
        return int(hex_str[2:4], 16), int(hex_str[4:6], 16), int(hex_str[6:8], 16), int(hex_str[0:2], 16)
    elif len(hex_str) == 6:
        return int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16), 255
    elif len(hex_str) == 3:
        return int(hex_str[0:1] * 2, 16), int(hex_str[1:2] * 2, 16), int(hex_str[2:3] * 2, 16), 255
    else:
        raise Exception('Invalid hex length: {} ({})'.format(hex_str, len(hex_str)))


def hex_to_rgb(hex_str):
    """
    Converts hexadecimal number to RGBA tuple
    :param hex_str: str, hexadecimal string
    :return: tuple(float, float, float), color tuple (R, G, B)
    """

    return hex_to_rgba(hex_str)[0:3]


def rgb_to_hex(rgb):
    """
    Converts RGB tuple to hexadecimal string
    :param rgb: tuple(float, float, float): color tuple (R, G, B)
    :return: str, hexadecimal string (eg. 2F2F2F)
    """

    ret = ''.join([hex(h)[2:].upper().zfill(2) for h in rgb])
    if len(ret) == 8:
        # Move last two characters to the beginning
        return ret[-2] + ret[:2]

    return ret


def rgb_int_to_float(color):
    """
    Turns an integer color in 0-255 range into a 0-1 float range
    :param color: tuple(int, int, int, int), color in 0-255 range
    :return: tuple(float, float, float, float) color in 0-1 range
    """

    return tuple([color_channel / 255.0 for color_channel in color])


def rgb_float_to_int(color):
    """
    Turns a float color in 0-1 range into a 0-255 integer range
    :param color: tuple(float, float, float, float), color in 0-1 range
    :return: tuple(int, int, int, int), color in 0-255 range
    """

    return tuple([int(round(255 * float(color_channel))) for color_channel in color])


def rgb_int_round(color):
    """
    Rounds all values of 255 color (eg. (243.1, 100, 10.3) is returned as (243, 100, 10)
    :param color: tuple(int, int, int, int), int color tuple
    :return: tuple(int, int, int, int), color converted
    """

    return tuple([int(round(color_channel)) for color_channel in color])


def convert_srgb_list_to_linear(srgb_list, round_number=True):
    """
    Converts a list of SRGB colors to linear. Can optionally round the result color to 4 decimals
    :param srgb_list: list, list(list(int, int, int), list of SRGB colors in 0-1 range
    :param round_number: bool, Whether to round result color values to 4 decimals or not
    :return: list(list(int, int, int), list of converted colors
    """

    linear_srgb_list = list()
    for srgb_color in srgb_list:
        linear_color_long = convert_color_srgb_to_linear(srgb_color)
        if round_number:
            linear_color = list()
            for long_number in linear_color_long:
                rounded_number = round(long_number, 4)
                linear_color.append(rounded_number)
        else:
            linear_srgb_list.append(linear_color_long)

    return linear_srgb_list


def hsl_color_offset_float(rgb_color, hue_offset=0, saturation_offset=0, lightness_offset=0):
    """
    Offsets color with hue, saturation and lightness (brighten/darken) values
    :param rgb_color: tuple(float, float, float), RGB color in 0.0-1.0 float range
    :param hue_offset: float, hue offset in 0-360 range
    :param saturation_offset: float, saturation offset in 0-255 range
    :param lightness_offset: float, lightness value offset, lighten(0.2) or darken (-0.3) in -1.0 and 1.0 range
    :return: tuple(float, float, float), color in 0-1 range
    """

    if hue_offset:
        hsv = convert_rgb_to_hsv(list(rgb_color))
        new_hue = hsv[0] + hue_offset
        if new_hue > 360.0:
            new_hue -= 360.0
        elif new_hue < 360.0:
            new_hue += 360.0
        hsv = (new_hue, hsv[1], hsv[2])
        rgb_color = convert_hsv_to_rgb(list(hsv))
    if saturation_offset:
        hsv = convert_rgb_to_hsv(rgb_color)
        hsv = (hsv[0], clamp(hsv[1] + saturation_offset), hsv[2])
        rgb_color = convert_hsv_to_rgb(list(hsv))
    if lightness_offset:
        rgb_color = (
            clamp(rgb_color[0] + lightness_offset),
            clamp(rgb_color[1] + lightness_offset),
            clamp(rgb_color[2] + lightness_offset)
        )

    return rgb_color


def hsl_color_offset_int(rgb_color, hue_offset=0, saturation_offset=0, lightness_offset=0):
    """
    Offsets color with hue, saturation and lightness (brighten/darken) values
    :param rgb_color: tuple(float, float, float), RGB color in 0-255 integer range
    :param hue_offset: float, hue offset in 0-360 range
    :param saturation_offset: float, saturation offset in 0-255 range
    :param lightness_offset: float, lightness value offset, lighten(0.2) or darken (-0.3) in -1.0 and 1.0 range
    :return: tuple(float, float, float), color in 0-1 range
    """

    rgb_color = rgb_int_to_float(rgb_color)
    lightness_offset = float(lightness_offset) / 255.0
    saturation_offset = float(saturation_offset) / 255.0
    rgb_color = hsl_color_offset_float(
        rgb_color, hue_offset=hue_offset, saturation_offset=saturation_offset, lightness_offset=lightness_offset)

    return rgb_float_to_int(rgb_color)


def desaturate(color, level=1.0):
    """
    Returns a desaturated color
    :param color: tuple(int, int, int, int), color tuple
    :param level: float, level of desaturation from 0 to 1.0. 1.0 is full desaturation and 0 same saturation
    :return: tuple(int, int, int, int), desaturated color
    """

    saturation = convert_rgb_to_hsv(rgb_int_to_float(color))[1]
    saturation_offset = 0.0
    if saturation:
        saturation_offset = int((saturation * level) * -255.0)
    desaturated = hsl_color_offset_int(color, lightness_offset=-40, saturation_offset=saturation_offset)

    return desaturated


def offset_hue_color(hsv, offset):
    """
    Offsets the hue value in -360-360 range by the given offset amount and keeps range by looping
    :param hsv: list(float, float, float), list or tuple representing the hue saturation and value color
    :param offset: float, offset value to offset the saturation
    :return: list(float, float, float), offset hue saturation value color
    """

    if offset > 360:
        offset = 360
    elif offset < -360:
        offset = -360
    hsv[0] += offset
    if hsv[0] > 360:
        hsv[0] -= 360
    elif hsv[0] < 0:
        hsv[0] += 360

    return hsv


def offset_saturation(hsv, offset):
    """
    Offsets the saturation value in 0-1 range by the given offset amount
    :param hsv: list(float, float, float), list or tuple representing the hue saturation and value color
    :param offset: float, offset value to offset the saturation
    :return: list(float, float, float), offset hue saturation value color
    """

    hsv[1] += offset
    if hsv[1] > 1:
        hsv[1] = 1
    elif hsv[1] < 0:
        hsv[1] = 0

    return hsv


def offset_value(hsv, offset):
    """
    Offsets the value (brightness/darkness) in range 0-1 by the given offset amount
    :param hsv: list(float, float, float), list or tuple representing the hue saturation and value color
    :param offset: float, offset value to offset the color
    :return: list(float, float, float), offset hue saturation value color
    """

    hsv[2] += offset
    if hsv[2] > 1:
        hsv[2] = 1
    elif hsv[2] < 0:
        hsv[2] = 0

    return hsv


def offset_color(color_to_offset, offset=0):
    """
    Returns a color with the offset applied
    :param color_to_offset: tuple(int, int, int), color in for of tuple of 3 digits
    :param offset: int, color offset value
    :return: tuple(int, int, int), offset color
    """

    return tuple([clamp((color_channel + offset), 0, 255) for color_channel in color_to_offset])


def hue_shift(color_to_shift, shift_amount):
    """
    Shifts the hue of the given color
    :param color_to_shift: tuple(int, int, int), color to shift
    :param shift_amount: int, distance and direction of the color shift
    :return: tuple(int, int, int), color with shifted hue
    """

    rgb_rotator = RGBRotate()
    rgb_rotator.set_hue_rotation(shift_amount)

    return rgb_rotator.apply(*color_to_shift)


def string_is_hex(color_str):
    """
    Returns whether given string is a valid hexadecimal string
    :param color_str: str
    :return: bool
    """

    if color_str.startswith('#'):
        return len(color_str) in (4, 7, 9)
    else:
        return len(color_str) in (3, 6, 8)


def convert_kelvin_to_rgb(color_temperature):
    """
    Converts from Kelvin to RGB
    http://www.tannerhelland.com/4435/convert-temperature-rgb-algorithm-code/
    :param color_temperature: float, color temperate in kelvin degrees
    :return: tuple(int, int, int), SRGB color in 0-255 format
    """

    # range check
    if color_temperature < 1000:
        color_temperature = 1000
    elif color_temperature > 40000:
        color_temperature = 40000

    tmp_internal = color_temperature / 100.0

    # red
    if tmp_internal <= 66:
        red = 255
    else:
        tmp_red = 329.698727446 * math.pow(tmp_internal - 60, -0.1332047592)
        if tmp_red < 0:
            red = 0
        elif tmp_red > 255:
            red = 255
        else:
            red = tmp_red

    # green
    if tmp_internal <= 66:
        tmp_green = 99.4708025861 * math.log(tmp_internal) - 161.1195681661
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green
    else:
        tmp_green = 288.1221695283 * math.pow(tmp_internal - 60, -0.0755148492)
        if tmp_green < 0:
            green = 0
        elif tmp_green > 255:
            green = 255
        else:
            green = tmp_green

    # blue
    if tmp_internal >= 66:
        blue = 255
    elif tmp_internal <= 19:
        blue = 0
    else:
        tmp_blue = 138.5177312231 * math.log(tmp_internal - 10) - 305.0447927307
        if tmp_blue < 0:
            blue = 0
        elif tmp_blue > 255:
            blue = 255
        else:
            blue = tmp_blue

    return red, green, blue


class RGBRotate:
    """
    Hue Rotation, using the matrix rotation method.
    https://stackoverflow.com/questions/8507885/shift-hue-of-an-rgb-color
    """

    def __init__(self):
        super().__init__()

        self.matrix = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]

    def set_hue_rotation(self, degrees):
        cos_a = math.cos(math.radians(degrees))
        sin_a = math.sin(math.radians(degrees))
        self.matrix[0][0] = cos_a + (1.0 - cos_a) / 3.0
        self.matrix[0][1] = 1. / 3. * (1.0 - cos_a) - math.sqrt(1. / 3.) * sin_a
        self.matrix[0][2] = 1. / 3. * (1.0 - cos_a) + math.sqrt(1. / 3.) * sin_a
        self.matrix[1][0] = 1. / 3. * (1.0 - cos_a) + math.sqrt(1. / 3.) * sin_a
        self.matrix[1][1] = cos_a + 1. / 3. * (1.0 - cos_a)
        self.matrix[1][2] = 1. / 3. * (1.0 - cos_a) - math.sqrt(1. / 3.) * sin_a
        self.matrix[2][0] = 1. / 3. * (1.0 - cos_a) - math.sqrt(1. / 3.) * sin_a
        self.matrix[2][1] = 1. / 3. * (1.0 - cos_a) + math.sqrt(1. / 3.) * sin_a
        self.matrix[2][2] = cos_a + 1. / 3. * (1.0 - cos_a)

    def apply(self, r, g, b):

        rx = r * self.matrix[0][0] + g * self.matrix[0][1] + b * self.matrix[0][2]
        gx = r * self.matrix[1][0] + g * self.matrix[1][1] + b * self.matrix[1][2]
        bx = r * self.matrix[2][0] + g * self.matrix[2][1] + b * self.matrix[2][2]
        return clamp(rx, 0, 255), clamp(gx, 0, 255), clamp(bx, 0, 255)


def compare_rgb_colors_tolerance(first_rgb_color, second_rgb_color, tolerance):
    """
    Compares to RGB colors taking into account the given tolerance (margin for error)
    :param first_rgb_color: tuple(float, float, float), first color to compare
    :param second_rgb_color: tuple(float, float, float), second color to compare
    :param tolerance: float, range in which the colors can vary
    :return: bool, True if two colors matches within the given tolerance; False otherwise
    """

    for i, value in enumerate(first_rgb_color):
        if not abs(value - second_rgb_color[i]) <= tolerance:
            return False

    return True
