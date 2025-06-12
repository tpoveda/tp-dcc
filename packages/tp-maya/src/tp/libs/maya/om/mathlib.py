from __future__ import annotations

import math
from typing import Iterator

from maya.api import OpenMaya

from ...math import scalar

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


def is_vector_negative(vector: OpenMaya.MVector) -> bool:
    """
    Returns whether the given vector has any negative component.

    :param vector: vector to check for negative components.
    :return: whether the vector has any negative component.
    """

    return sum(vector) < 0


def primary_axis_name_from_vector(vector: OpenMaya.MVector) -> str:
    """
    Returns the primary axis name from the given vector.

    :param vector: vector to get the primary axis name from.
    :return: primary axis name.
    """

    return "X" if vector[0] != 0.0 else "Y" if vector[1] != 0.0 else "Z"


def primary_axis_index_from_vector(vector: OpenMaya.MVector) -> int:
    """
    Returns the primary axis index from the given vector.

    :param vector: vector to get the primary axis index from.
    :return: primary axis index.
    """

    return (
        X_AXIS_INDEX
        if vector[0] != 0.0
        else Y_AXIS_INDEX
        if vector[1] != 0.0
        else Z_AXIS_INDEX
    )


def look_at(
    source_position: OpenMaya.MVector,
    aim_position: OpenMaya.MVector,
    aim_vector: OpenMaya.MVector | None = None,
    up_vector: OpenMaya.MVector | None = None,
    world_up_vector: OpenMaya.MVector | None = None,
    constraint_axis: OpenMaya.MVector = OpenMaya.MVector(1, 1, 1),
) -> OpenMaya.MQuaternion:
    """
    Returns the rotation to apply to a node to aim to another one.

    :param source_position: source position which as the eye.
    :param aim_position: target position to aim at.
    :param aim_vector: vector for the aim axis.
    :param up_vector: vector for the up axis.
    :param world_up_vector: alternative world up vector.
    :param constraint_axis: axis vector to constraint the aim on.
    :return: aim rotation to apply.
    :rtype: rotation as quaternion.
    """

    eye_aim = aim_vector or X_AXIS_VECTOR
    eye_up = up_vector or Y_AXIS_VECTOR
    world_up = world_up_vector or OpenMaya.MGlobal.upAxis()
    eye_pivot_pos = source_position
    target_pivot_pos = aim_position

    aim_vector = target_pivot_pos - eye_pivot_pos
    eye_u = aim_vector.normal()
    eye_w = (eye_u ^ OpenMaya.MVector(world_up.x, world_up.y, world_up.z)).normal()
    eye_v = eye_w ^ eye_u
    quat_u = OpenMaya.MQuaternion(eye_aim, eye_u)

    up_rotated = eye_up.rotateBy(quat_u)
    try:
        angle = math.acos(
            scalar.clamp(up_rotated * eye_v, min_value=-1.0, max_value=1.0)
        )
    except (ZeroDivisionError, ValueError):
        angle = 0.0 if sum(eye_up) > 0 else -math.pi

    quat_v = OpenMaya.MQuaternion(angle, eye_u)

    if not eye_v.isEquivalent(up_rotated.rotateBy(quat_v), 1.0e-5):
        angle = (2 * math.pi) - angle
        quat_v = OpenMaya.MQuaternion(angle, eye_u)

    quat_u *= quat_v
    rot = quat_u.asEulerRotation()
    if not constraint_axis.x:
        rot.x = 0.0
    if not constraint_axis.y:
        rot.y = 0.0
    if not constraint_axis.z:
        rot.z = 0.0

    return rot.asQuaternion()


def aim_to_node(
    source: OpenMaya.MObject,
    target: OpenMaya.MObject,
    aim_vector: OpenMaya.MVector | None = None,
    up_vector: OpenMaya.MVector | None = None,
    world_up_vector: OpenMaya.MVector | None = None,
    constraint_axis: OpenMaya.MVector = OpenMaya.MVector(1, 1, 1),
):
    """
    Aims one node at another using quaternions.

    :param source: node to aim towards the target node.
    :param target: node which the source will aim at.
    :param aim_vector: vector for the aim axis.
    :param up_vector: vector for the up axis.
    :param world_up_vector: alternative world up vector.
    :param constraint_axis: axis vector to constraint the aim on.
    """

    source_dag = OpenMaya.MDagPath.getAPathTo(source)
    target_dag = OpenMaya.MDagPath.getAPathTo(target)
    source_transform_fn = OpenMaya.MFnTransform(source_dag)
    source_pivot_pos = source_transform_fn.rotatePivot(OpenMaya.MSpace.kWorld)
    target_transform_fn = OpenMaya.MFnTransform(target_dag)
    target_pivot_pos = target_transform_fn.rotatePivot(OpenMaya.MSpace.kWorld)
    rotation = look_at(
        source_pivot_pos,
        target_pivot_pos,
        aim_vector,
        up_vector,
        world_up_vector,
        constraint_axis,
    )
    target_transform_fn.setObject(source_dag)
    target_transform_fn.setRotation(rotation, OpenMaya.MSpace.kWorld)


def even_linear_point_distribution(
    start: OpenMaya.MVector, end: OpenMaya.MVector, count: int
) -> Iterator[tuple[OpenMaya.MVector, float]]:
    """
    Generator function that evenly distributes points between two given vectors.

    :param start: start vector.
    :param end: end vector.
    :param count: number of points to generate.
    :return: tuple with the generated point and the multiplier.
    """

    direction_vector = end - start
    fraction = direction_vector.normal().length() / (count + 1)
    for i in range(1, count + 1):
        multiplier = fraction * i
        pos = start + (direction_vector * multiplier)
        yield OpenMaya.MVector(pos), multiplier


def first_last_offset_linear_point_distribution(
    start: OpenMaya.MVector, end: OpenMaya.MVector, count: int, offset: float
) -> Iterator[tuple[OpenMaya.MVector, float]]:
    """
    Generator function that distributes points between two given vectors with an
    offset at the start and end.

    :param start: start vector.
    :param end: end vector.
    :param count: number of points to generate.
    :param offset: offset to apply at the start and end.
    :return: tuple with the generated point and the multiplier.
    """

    direction_vector = end - start
    fraction = direction_vector.normal().length()
    first_last_fraction = fraction / (count + 1)
    primary_fraction = fraction / (count - 1)
    multiplier = first_last_fraction * offset
    yield start + (direction_vector * multiplier), multiplier

    for i in range(count - 2):
        multiplier = primary_fraction * (i + 1)
        pos = start + (direction_vector * multiplier)
        yield pos, multiplier

    multiplier = 1.0 - first_last_fraction * offset
    yield start + (direction_vector * multiplier), multiplier


def perpendicular_axis_from_align_vector(
    aim_vector: OpenMaya.MVector, up_vector: OpenMaya.MVector
) -> tuple[int, bool]:
    """
    Given an aim and up vector, this function returns which axis is not being used and
    determine whether to get positive values from an incoming attribute whether it needs
    to be negated.

    :param aim_vector: aim vector to use.
    :param up_vector: up vector to use.
    :return: axis index and whether to negate the incoming value.
    """

    perpendicular_vector = aim_vector ^ up_vector
    axis_index = Z_AXIS_INDEX
    is_negative = is_vector_negative(perpendicular_vector)

    for axis_index, value in enumerate(perpendicular_vector):
        if int(value) != 0:
            break

    return axis_index, is_negative


def closest_point_on_plane(
    point: OpenMaya.MVector, plane: OpenMaya.MPlane
) -> OpenMaya.MVector:
    """
    Returns the closest point on a plane from a given point, by projecting the point on
    the plane.

    :param point: point to get the closest point from.
    :param plane: plane to get the closest point on.
    :return: closest point on the plane.
    """

    return point - (plane.normal() * plane.distanceToPoint(point, signed=True))


def basis_vector_from_matrix(
    matrix: OpenMaya.MMatrix,
) -> tuple[OpenMaya.MVector, OpenMaya.MVector, OpenMaya.MVector]:
    """
    Returns 3 orthonormal basis vectors (X, Y, Z) that represent the orientation of
    the given transformation matrix.

    Useful for:
        - Extracting the orientation of an object in world/local space.
        - Obtaining the X, Y, Z direction vectors for custom transformations.
        - Debugging transforms in Maya.

    |  0   1   2   3  |  -> X-axis (Right)
    |  4   5   6   7  |  -> Y-axis (Up)
    |  8   9  10  11  |  -> Z-axis (Forward)
    | 12  13  14  15  |  -> Translation (Ignored)

    :param matrix: the matrix to return the orthonormal basis from.
    :return: tuple with the 3 orthonormal basis vectors.
    """

    return (
        OpenMaya.MVector(matrix[0], matrix[1], matrix[2]),
        OpenMaya.MVector(matrix[4], matrix[5], matrix[6]),
        OpenMaya.MVector(matrix[8], matrix[9], matrix[10]),
    )


def basis_x_vector_from_matrix(matrix: OpenMaya.MMatrix) -> OpenMaya.MVector:
    """
    Returns the X basis vector from the given matrix.

    :param matrix: matrix to get the X basis vector from.
    :return: X basis vector.
    """

    return OpenMaya.MVector(matrix[0], matrix[1], matrix[2])


def basis_y_vector_from_matrix(matrix: OpenMaya.MMatrix) -> OpenMaya.MVector:
    """
    Returns the Y basis vector from the given matrix.

    :param matrix: matrix to get the Y basis vector from.
    :return: Y basis vector.
    """

    return OpenMaya.MVector(matrix[4], matrix[5], matrix[6])


def basis_z_vector_from_matrix(matrix: OpenMaya.MMatrix) -> OpenMaya.MVector:
    """
    Returns the Z basis vector from the given matrix.

    :param matrix: matrix to get the Z basis vector from.
    :return: Z basis vector.
    """

    return OpenMaya.MVector(matrix[8], matrix[9], matrix[10])
