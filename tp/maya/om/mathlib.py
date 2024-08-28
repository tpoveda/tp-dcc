from __future__ import annotations

from maya.api import OpenMaya

X_AXIS_VECTOR = OpenMaya.MVector(1, 0, 0)
Y_AXIS_VECTOR = OpenMaya.MVector(0, 1, 0)
Z_AXIS_VECTOR = OpenMaya.MVector(0, 0, 1)
X_AXIS_INDEX = 0
Y_AXIS_INDEX = 1
Z_AXIS_INDEX = 2
NEGATIVE_X_AXIS_INDEX = 3
NEGATIVE_Y_AXIS_INDEX = 4
NEGATIVE_Z_AXIS_INDEX = 5
# noinspection PyTypeChecker
AXIS_VECTOR_BY_INDEX = [
    X_AXIS_VECTOR,
    Y_AXIS_VECTOR,
    Z_AXIS_VECTOR,
    X_AXIS_VECTOR * -1,
    Y_AXIS_VECTOR * -1,
    Z_AXIS_VECTOR * -1,
]
AXIS_NAME_BY_INDEX = ["X", "Y", "Z", "X", "Y", "Z"]
AXIS_INDEX_BY_NAME = {"X": 0, "Y": 1, "Z": 2}
AXIS_NAMES = ["X", "Y", "Z"]


def convert_to_scene_units(
    value: int | float | OpenMaya.MVector,
) -> int | float | OpenMaya.MVector:
    """
    Converts the given value to the current Maya scene units (metres, inches, ...).

    :param value: value to convert to the scene units.
    :return: newly converted value.
    .note:: only meters, feet and inches are supported.
    """

    scene_units = OpenMaya.MDistance.uiUnit()
    if scene_units == OpenMaya.MDistance.kMeters:
        return value / 100.0
    elif scene_units == OpenMaya.MDistance.kInches:
        return value / 2.54
    elif scene_units == OpenMaya.MDistance.kFeet:
        return value / 30.48

    return value


def convert_from_scene_units(
    value: int | float | OpenMaya.MVector,
) -> int | float | OpenMaya.MVector:
    """
    Converts the given value from the current Maya scene units back to centimeters.

    :param value: value to convert to the scene units.
    :return: newly converted value.
    .note:: only meters, feet and inches are supported.
    """

    scene_units = OpenMaya.MDistance.uiUnit()
    if scene_units == OpenMaya.MDistance.kMeters:
        return value * 100
    elif scene_units == OpenMaya.MDistance.kInches:
        return value * 2.54
    elif scene_units == OpenMaya.MDistance.kFeet:
        return value * 30.48

    return value
