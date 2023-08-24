#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with Maya API math
"""

from __future__ import annotations

import math
from typing import Tuple

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.common.math import scalar

X_AXIS_VECTOR = OpenMaya.MVector(1, 0, 0)
Y_AXIS_VECTOR = OpenMaya.MVector(0, 1, 0)
Z_AXIS_VECTOR = OpenMaya.MVector(0, 0, 1)
X_AXIS_INDEX = 0
Y_AXIS_INDEX = 1
Z_AXIS_INDEX = 2
NEGATIVE_X_AXIS_INDEX = 3
NEGATIVE_Y_AXIS_INDEX = 4
NEGATIVE_Z_AXIS_INDEX = 5
AXIS_VECTOR_BY_INDEX = [
	X_AXIS_VECTOR, Y_AXIS_VECTOR, Z_AXIS_VECTOR, X_AXIS_VECTOR * - 1, Y_AXIS_VECTOR * -1, Z_AXIS_VECTOR * -1]
AXIS_NAME_BY_INDEX = ['X', 'Y', 'Z', 'X', 'Y', 'Z']
AXIS_INDEX_BY_NAME = {'X': 0, 'Y': 1, 'Z': 2}
AXIS_NAMES = ['X', 'Y', 'Z']


def magnitude(vector=(0, 0, 0)):
	"""
	Returns the magnitude (length) or a given vector.

	:param tuple(float, float, float) vector: vector to return the length of.
	:return: vector magnitude.
	:rtype: float
	"""

	return OpenMaya.MVector(vector[0], vector[1], vector[2]).length()


def is_vector_negative(vector: OpenMaya.MVector) -> bool:
	"""
	Returns whether given vector is negative by checking whether the sum of the XYZ components is less than 0.0.

	:param OpenMaya.MVector vector: vector to check.
	:return: True if given vector is negative; False otherwise.
	:rtype: bool
	"""

	return sum(vector) < 0.0


def axis_vector(transform, vector):
	"""
	Returns the vector matrix product.

	If you give a vector [1, 0, 0], it will return the transform's X point
	If you give a vector [0, 1, 0], it will return the transform's Y point
	If you give a vector [0, 0, 1], it will return the transform's Z point
	:param transform: str, name of a transforms. Its matrix will be checked
	:param vector: list<int>, A vector, X = [1,0,0], Y = [0,1,0], Z = [0,0,1]
	:return: list<int>, the result of multiplying the vector by the matrix
	Useful to get an axis in relation to the matrix
	"""

	xform = OpenMaya.MFnTransform(transform)

	# TODO: Not working properly
	OpenMaya.MGlobal.displayWarning('get_vector_matrix_product() does not work properly yet ...!')
	vct = OpenMaya.MVector()
	vct.x = vector[0]
	vct.y = vector[1]
	vct.z = vector[2]
	space = OpenMaya.MSpace.kWorld
	orig_vct = xform.translation(space)
	vct *= xform.transformation().asMatrix()
	vct += orig_vct

	return vct.x, vct.y, vct.z


def normalize_vector(vector=(0, 0, 0)):
	"""
	Returns normalized version of the input vector.

	:param vector: tuple, vector to normalize
	:return: tuple
	"""

	normal = OpenMaya.MVector(vector[0], vector[1], vector[2]).normal()

	return normal.x, normal.y, normal.z


def two_point_normal(
		point_a: OpenMaya.MVector, point_b: OpenMaya.MVector, normal: OpenMaya.MVector) -> OpenMaya.MVector:
	"""
	Returns the plane normal based on the given two points and the additional normal vector.

	:param OpenMaya.MVector point_a: first vector.
	:param OpenMaya.MVector point_b: second vector.
	:param OpenMaya.MVector normal: additional normal which will be crossed with the distance vector.
	:return: plane normal.
	:rtype: OpenMaya.MVector
	"""

	line_vec = point_b - point_a

	# find the normal between the line formed by 2 points and the given normal
	first_normal = (normal ^ line_vec).normalize()

	# find the cross product between the line and the first normal

	return (first_normal ^ line_vec).normalize()


def three_point_normal(
		point_a: OpenMaya.MVector, point_b: OpenMaya.MVector, point_c: OpenMaya.MVector) -> OpenMaya.MVector:
	"""
	Retursn the plane normal based on the given three points.

	:param OpenMaya.MVector point_a: first vector.
	:param OpenMaya.MVector point_b: second vector.
	:param OpenMaya.MVector point_c: third vector.
	:return: plane normal.
	:rtype: OpenMaya.MVector
	"""

	return ((point_c - point_b) ^ (point_b - point_a)).normalize()


def dot_product(vector1=(0.0, 0.0, 0.0), vector2=(0.0, 0.0, 0.0)):
	"""
	Returns the dot product (inner product) of two given vectors.

	:param vector1: tuple, first vector for the dot product operation
	:param vector2: tuple, second vector for the dot product operation
	:return: float
	"""

	vec1 = OpenMaya.MVector(vector1[0], vector1[1], vector1[2])
	vec2 = OpenMaya.MVector(vector2[0], vector2[1], vector2[2])

	return vec1 * vec2


def cross_product(vector1=(0.0, 0.0, 0.0), vector2=(0.0, 0.0, 0.0)):
	"""
	Returns the cross product of two given vectors.

	:param vector1: tuple, first vector for the dot product operation
	:param vector2: tuple, second vector for the dot product operation
	:return: tuple
	"""

	vec1 = OpenMaya.MVector(vector1[0], vector1[1], vector1[2])
	vec2 = OpenMaya.MVector(vector2[0], vector2[1], vector2[2])
	cross_product = vec1 ^ vec2

	return cross_product.x, cross_product.y, cross_product.z


def distance_between(point1=[0.0, 0.0, 0.0], point2=[0.0, 0.0, 0.0]):
	"""
	Returns the distance between two given points.

	:param point1: tuple, start point of the distance calculation
	:param point2: tuple, end point of the distance calculation
	:return: float
	"""

	pnt1 = OpenMaya.MVector(point1[0], point1[1], point1[2])
	pnt2 = OpenMaya.MVector(point2[0], point2[1], point2[2])

	return OpenMaya.MVector(pnt1 - pnt2).length()


def offset_vector(point1, point2):
	"""
	Returns the offset vector between point1 and point2.

	:param tuple(float, float, float) point1: start point of the offset calculation.
	:param tuple(float, float, float) point2: end point of the offset calculation.
	:return: offset vector as a tuple.
	:rtype: tuple(float, float, float)
	"""

	pnt1 = OpenMaya.MVector(point1[0], point1[1], point1[2])
	pnt2 = OpenMaya.MVector(point2[0], point2[1], point2[2])
	vec = pnt2 - pnt1

	return vec.x, vec.y, vec.z


def closest_point_on_line(pnt, line1, line2, clamp_segment=False):
	"""
	Find the closest point (to a given position) on the line given by the given inputs.

	:param pnt: tuple, we will try to find the closes line point from this position
	:param line1: tuple, start point of line
	:param line2: tuple, end point of line
	:param clamp_segment: bool, Whether to return clamped value or not
	:return: tuple
	"""

	pnt_offset = offset_vector(line1, pnt)
	line_offset = offset_vector(line1, line2)

	# vector comparison
	dot = dot_product(pnt_offset, line_offset)

	if clamp_segment:
		if dot < 0.0:
			return line1
		if dot > 1.0:
			return line2

	# project Vector
	return [line1[0] + (line_offset[0] * dot), line1[1] + (line_offset[1] * dot), line1[2] + (line_offset[2] * dot)]


def closest_point_on_plane(point: OpenMaya.MVector, plane: OpenMaya.MPlane) -> OpenMaya.MVector:
	"""
	Returns the closest point on the given plan by projecting the point on the plane.

	:param OpenMaya.MVector point: point to project on to the plane.
	:param OpenMaya.MPlane plane: plane instance to get closes point.
	:return: closest point.
	:rtype: OpenMaya.MVector
	"""

	return point - (plane.normal() * plane.distanceToPoint(point, signed=True))


def inverse_distance_weight_3d(point_array, sample_point):
	"""
	Returns the inverse distance weight for a given sample point given an array of scalar values
	:param point_array: variant, tuple || list, point array to calculate weights from
	:param sample_point: variant, tuple || list, sample point to calculate weights for
	:return: float
	"""

	dst_array = list()
	total_inv_dst = 0.0

	for i in range(len(point_array)):
		dst = distance_between(sample_point, point_array[i])
		# Check zero distance
		if dst < 0.00001:
			dst = 0.00001

		dst_array.append(dst)
		total_inv_dst += 1.0 / dst

	# Normalize value weights
	weight_array = [(1.0 / d) / total_inv_dst for d in dst_array]

	return weight_array


def distance_between_nodes(source_node=None, target_node=None):
	"""
	Returns the distance between 2 given nodes.

	:param str source_node: first node to start measuring distance from. If not given, first selected node will be used.
	:param str target_node: second node to end measuring distance to. If not given, second selected node will be used.
	:return: distance between 2 nodes.
	:rtype: float
	"""

	if source_node is None or target_node is None:
		sel = cmds.ls(sl=True, type='transform')
		if len(sel) != 2:
			return 0
		source_node, target_node = sel

	source_pos = OpenMaya.MPoint(*cmds.xform(source_node, query=True, worldSpace=True, translation=True))
	target_pos = OpenMaya.MPoint(*cmds.xform(target_node, query=True, worldSpace=True, translation=True))

	return source_pos.distanceTo(target_pos)


def direction_vector_between_nodes(source_node=None, target_node=None):
	"""
	Returns the direction vector between 2 given nodes
	:param str source_node: first node to start getting direction. If not given, first selected node will be used.
	:param str target_node: second node to end getting direction. If not given, second selected node will be used.
	:return: direction vector between 2 nodes.
	:rtype: OpenMaya.MVector
	"""

	if source_node is None or target_node is None:
		sel = cmds.ls(sl=True, type='transform')
		if len(sel) != 2:
			return 0
		source_node, target_node = sel

	source_pos = OpenMaya.MPoint(*cmds.xform(source_node, query=True, worldSpace=True, translation=True))
	target_pos = OpenMaya.MPoint(*cmds.xform(target_node, query=True, worldSpace=True, translation=True))

	return target_pos - source_pos


def identity_matrix():
	"""
	Returns identity matrix.

	:return: OpenMaya.MMatrix
	"""

	return OpenMaya.MMatrix()


def multiply_matrix(matrix4x4_list1, matrix4x4_list2):
	"""
	Multiplies the two given matrices.

	matrix1 and matrix2 are just the list of numbers of a 4x4 matrix
	(like the ones returned by cmds.getAttr('transform.worldMatrix) for example.

	:param matrix4x4_list1:
	:param matrix4x4_list2:
	:return: OpenMaya.MMatrix
	"""

	mat1 = OpenMaya.MMatrix(matrix4x4_list1)
	mat2 = OpenMaya.MMatrix(matrix4x4_list2)

	return mat1 * mat2


def to_euler_xyz(rotation_matrix, degrees=False):
	"""
	Converts given rotation matrix to a rotation with XYZ rotation order.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to convert.
	:param bool degrees: whether to convert result in degrees or radians.
	:return: euler rotation.
	:rtype: OpenMaya.MEulerRotation
	"""

	rotation_z = rotation_matrix[2]
	if scalar.is_equal(rotation_z, 1.0, 2):
		z = math.pi
		y = -math.pi * 0.5
		x = -z + math.atan2(-rotation_matrix[4], -rotation_matrix[7])
	elif scalar.is_equal(rotation_z, -1.0, 2):
		z = math.pi
		y = math.pi * 0.5
		x = z + math.atan2(rotation_matrix[4], rotation_matrix[7])
	else:
		y = -math.asin(rotation_z)
		cos_y = math.cos(y)
		x = math.atan2(rotation_matrix[6] * cos_y, rotation_matrix[10] * cos_y)
		z = math.atan2(rotation_matrix[1] * cos_y, rotation_matrix[0] * cos_y)
	angles = x, y, z

	if degrees:
		return list(map(math.degrees, angles))

	return OpenMaya.MEulerRotation(angles)


def to_euler_xzy(rotation_matrix, degrees=False):
	"""
	Converts given rotation matrix to a rotation with XZY rotation order.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to convert.
	:param bool degrees: whether to convert result in degrees or radians.
	:return: euler rotation.
	:rtype: OpenMaya.MEulerRotation
	"""

	rotation_yy = rotation_matrix[1]
	z = math.asin(rotation_yy)
	cos_z = math.cos(z)

	x = math.atan2(-rotation_matrix[9] * cos_z, rotation_matrix[5] * cos_z)
	y = math.atan2(-rotation_matrix[2] * cos_z, rotation_matrix[0] * cos_z)

	angles = x, y, z

	if degrees:
		return list(map(math.degrees, angles))

	return OpenMaya.MEulerRotation(angles)


def to_euler_yxz(rotation_matrix, degrees=False):
	"""
	Converts given rotation matrix to a rotation with YXZ rotation order.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to convert.
	:param bool degrees: whether to convert result in degrees or radians.
	:return: euler rotation.
	:rtype: OpenMaya.MEulerRotation
	"""

	rotation_z = rotation_matrix[6]
	x = math.asin(rotation_z)
	cos_x = math.cos(x)

	y = math.atan2(-rotation_matrix[2] * cos_x, rotation_matrix[10] * cos_x)
	z = math.atan2(-rotation_matrix[4] * cos_x, rotation_matrix[5] * cos_x)

	angles = x, y, z

	if degrees:
		return list(map(math.degrees, angles))

	return OpenMaya.MEulerRotation(angles)


def to_euler_yzx(rotation_matrix, degrees=False):
	"""
	Converts given rotation matrix to a rotation with YZX rotation order.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to convert.
	:param bool degrees: whether to convert result in degrees or radians.
	:return: euler rotation.
	:rtype: OpenMaya.MEulerRotation
	"""

	rotation_yx = rotation_matrix[4]
	z = -math.asin(rotation_yx)
	cos_z = math.cos(z)

	x = math.atan2(rotation_matrix[6] * cos_z, rotation_matrix[5] * cos_z)
	y = math.atan2(rotation_matrix[8] * cos_z, rotation_matrix[0] * cos_z)

	angles = x, y, z

	if degrees:
		return list(map(math.degrees, angles))

	return OpenMaya.MEulerRotation(angles)


def to_euler_zxy(rotation_matrix, degrees=False):
	"""
	Converts given rotation matrix to a rotation with ZXY rotation order.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to convert.
	:param bool degrees: whether to convert result in degrees or radians.
	:return: euler rotation.
	:rtype: OpenMaya.MEulerRotation
	"""

	rotation_zy = rotation_matrix[9]
	x = -math.asin(rotation_zy)
	cos_x = math.cos(x)

	z = math.atan2(rotation_matrix[1] * cos_x, rotation_matrix[5] * cos_x)
	y = math.atan2(rotation_matrix[8] * cos_x, rotation_matrix[10] * cos_x)

	angles = x, y, z

	if degrees:
		return list(map(math.degrees, angles))

	return OpenMaya.MEulerRotation(angles)


def to_euler_zyx(rotation_matrix, degrees=False):
	"""
	Converts given rotation matrix to a rotation with ZYX rotation order.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to convert.
	:param bool degrees: whether to convert result in degrees or radians.
	:return: euler rotation.
	:rtype: OpenMaya.MEulerRotation
	"""

	rotation_zx = rotation_matrix[8]
	y = math.asin(rotation_zx)
	cos_y = math.cos(y)

	x = math.atan2(-rotation_matrix[9] * cos_y, rotation_matrix[10] * cos_y)
	z = math.atan2(-rotation_matrix[4] * cos_y, rotation_matrix[0] * cos_y)

	angles = x, y, z

	if degrees:
		return list(map(math.degrees, angles))

	return OpenMaya.MEulerRotation(angles)


def to_euler(rotation_matrix, rotate_order, degrees=False):
	"""
	Converts given rotation matrix to an euler rotation.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to convert.
	:param OpenMaya.MTransformationMatrix.kRotateOrder rotate_order: rotation order.
	:param bool degrees: whether to convert result in degrees or radians.
	:return: euler rotation.
	:rtype: OpenMaya.MEulerRotation
	"""

	if rotate_order == OpenMaya.MTransformationMatrix.kXYZ:
		return to_euler_xyz(rotation_matrix, degrees)
	elif rotate_order == OpenMaya.MTransformationMatrix.kXZY:
		return to_euler_xzy(rotation_matrix, degrees)
	elif rotate_order == OpenMaya.MTransformationMatrix.kYXZ:
		return to_euler_yxz(rotation_matrix, degrees)
	elif rotate_order == OpenMaya.MTransformationMatrix.kYZX:
		return to_euler_yzx(rotation_matrix, degrees)
	elif rotate_order == OpenMaya.MTransformationMatrix.kZXY:
		return to_euler_zxy(rotation_matrix, degrees)

	return to_euler_zyx(rotation_matrix, degrees)


def mirror_xy(rotation_matrix):
	"""
	Mirrors given rotation matrix along XY plane.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to mirror.
	:return: mirrored rotation matrix.
	:rtype: OpenMaya.MMatrix
	"""

	rotation_matrix = OpenMaya.MMatrix(rotation_matrix)
	rotation_matrix[0] *= -1
	rotation_matrix[1] *= -1
	rotation_matrix[4] *= -1
	rotation_matrix[5] *= -1
	rotation_matrix[8] *= -1
	rotation_matrix[9] *= -1

	return rotation_matrix


def mirror_yz(rotation_matrix):
	"""
	Mirrors given rotation matrix along YZ plane.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to mirror.
	:return: mirrored rotation matrix.
	:rtype: OpenMaya.MMatrix
	"""

	rotation_matrix = OpenMaya.MMatrix(rotation_matrix)
	rotation_matrix[1] *= -1
	rotation_matrix[2] *= -1
	rotation_matrix[5] *= -1
	rotation_matrix[6] *= -1
	rotation_matrix[9] *= -1
	rotation_matrix[10] *= -1

	return rotation_matrix


def mirror_xz(rotation_matrix):
	"""
	Mirrors given rotation matrix along XZ plane.

	:param OpenMaya.MMatrix rotation_matrix: rotation matrix to mirror.
	:return: mirrored rotation matrix.
	:rtype: OpenMaya.MMatrix
	"""

	rotation_matrix = OpenMaya.MMatrix(rotation_matrix)
	rotation_matrix[0] *= -1
	rotation_matrix[2] *= -1
	rotation_matrix[4] *= -1
	rotation_matrix[6] *= -1
	rotation_matrix[8] *= -1
	rotation_matrix[10] *= -1

	return rotation_matrix


def quaternion_dot(qa, qb):
	"""
	Calculates the dot product based on given quaternions.

	:param OpenMaya.MQuaternion qa: quaternion to calculate dot product with.
	:param OpenMaya.MQuaternion qb: quaternion to calculate dot product with.
	:return: quaternion dot product.
	:rtype: float
	"""

	return qa.w * qb.w + qa.x * qb.x + qa.y * qb.y + qa.z * qb.z


def slerp(qa, qb, weight):
	"""
	Calculates the spherical interpolation  between two given quaternions.

	:param OpenMaya.MQuaternion qa: quaternion to calculate spherical interpolation with.
	:param OpenMaya.MQuaternion qb: quaternion to calculate spherical interpolation with.
	:param float weight: how far we want to interpolate.
	:return: result of the spherical interpolation.
	:rtype: OpenMaya.MQuaternion
	"""

	qc = OpenMaya.MQuaternion()
	dot = quaternion_dot(qa, qb)
	if abs(dot >= 1.0):
		qc.w = qa.w
		qc.x = qa.x
		qc.y = qa.y
		qc.z = qa.z
		return qc

	half_theta = math.acos(dot)
	sin_half_theta = math.sqrt(1.0 - dot * dot)
	if scalar.is_equal(math.fabs(sin_half_theta), 0.0, 2):
		qc.w = (qa.w * 0.5 + qb.w * 0.5)
		qc.x = (qa.x * 0.5 + qb.x * 0.5)
		qc.y = (qa.y * 0.5 + qb.y * 0.5)
		qc.z = (qa.z * 0.5 + qb.z * 0.5)
		return qc

	ratio_a = math.sin((1.0 - weight) * half_theta) / sin_half_theta
	ratio_b = math.sin(weight * half_theta) / sin_half_theta

	qc.w = (qa.w * ratio_a + qb.w * ratio_b)
	qc.x = (qa.x * ratio_a + qb.x * ratio_b)
	qc.y = (qa.y * ratio_a + qb.y * ratio_b)
	qc.z = (qa.z * ratio_a + qb.z * ratio_b)

	return qc


def convert_to_scene_units(value):
	"""
	Converts the given value to the current Maya scene units (metres, inches, etc).

	:param float or int or OpenMaya.MVector value: value to convert to the scene units.
	:return: newly converted value.
	:rtype: float or int or OpenMaya.MVector
	..note:: only meters, feet and inches are supported.
	"""

	scene_units = OpenMaya.MDistance.uiUnit()
	if scene_units == OpenMaya.MDistance.kMeters:
		return value / 100.0
	elif scene_units == OpenMaya.MDistance.kInches:
		return value / 2.54
	elif scene_units == OpenMaya.MDistance.kFeet:
		return value / 30.48

	return value


def convert_from_scene_units(value):
	"""
	Converts the given value from the current Maya scene units back to centimeters.

	:param int or float or OpenMaya.MVector value: value to convert to the scene units.
	:return: newly converted value.
	:rtype: float or int or OpenMaya.MVector
	..note:: only meters, feet and inches are supported.
	"""

	scene_units = OpenMaya.MDistance.uiUnit()
	if scene_units == OpenMaya.MDistance.kMeters:
		return value * 100
	elif scene_units == OpenMaya.MDistance.kInches:
		return value * 2.54
	elif scene_units == OpenMaya.MDistance.kFeet:
		return value * 30.48

	return value


def look_at(
		source_position: OpenMaya.MVector, aim_position: OpenMaya.MVector, aim_vector: OpenMaya.MVector | None = None,
		up_vector: OpenMaya.MVector | None = None, world_up_vector: OpenMaya.MVector | None = None,
		constraint_axis: OpenMaya.MVector = OpenMaya.MVector(1, 1, 1)) -> OpenMaya.MQuaternion:
	"""
	Returns the rotation to apply to a node to aim to another one.

	:param OpenMaya.MVector source_position: source position which as the eye.
	:param OpenMaya.MVector aim_position: target position to aim at.
	:param OpenMaya.MVector or None  aim_vector: vector for the aim axis.
	:param OpenMaya.MVector or None up_vector: vector for the up axis.
	:param OpenMaya.MVector or None world_up_vector: alternative world up vector.
	:param OpenMaya.MVector constraint_axis: axis vector to constraint the aim to.
	:return: aim rotation to apply.
	:rtype: OpenMaya.MQuaternion
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
		angle = math.acos(up_rotated * eye_v)
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
		source, target, aim_vector=None, up_vector=None, world_up_vector=None, constraint_axis=OpenMaya.MVector(1, 1, 1)):
	"""
	Aims one node at another using quaternions.

	:param OpenMaya.MObject source: node to aim towards the target node.
	:param OpenMaya.MObject target: node which the source will aim at.
	:param OpenMaya.MVector aim_vector: vector for the aim axis.
	:param OpenMaya.MVector up_vector: vector for the up axis.
	:param OpenMaya.MVector world_up_vector: alternative world up vector.
	:param OpenMaya.MVector constraint_axis: axis vector to constraint the aim on.
	"""

	source_dag = OpenMaya.MDagPath.getAPathTo(source)
	target_dag = OpenMaya.MDagPath.getAPathTo(target)
	source_transform_fn = OpenMaya.MFnTransform(source_dag)
	source_pivot_pos = source_transform_fn.rotatePivot(OpenMaya.MSpace.kWorld)
	target_transform_fn = OpenMaya.MFnTransform(target_dag)
	target_pivot_pos = target_transform_fn.rotatePivot(OpenMaya.MSpace.kWorld)
	rotation = look_at(source_pivot_pos, target_pivot_pos, aim_vector, up_vector, world_up_vector, constraint_axis)
	target_transform_fn.setObject(source_dag)
	target_transform_fn.setRotation(rotation, OpenMaya.MSpace.kWorld)


def perpendicular_axis_from_align_vectors(
		aim_vector: OpenMaya.MVector, up_vector: OpenMaya.MVector) -> Tuple[int, bool]:
	"""
	Given an aim and up vectors, this function returns which axis is not being used and determines whether to get
	positive values from an incoming attribute whether it needs to be negated.

	:param OpenMaya.MVector aim_vector: aim vector.
	:param OpenMaya.MVector up_vector: up vector.
	:return: tuple containing the axis number (0='X', 1='Y', 2='Z') and whether it should be negated.
	:rtype: Tuple[int, bool]
	"""

	perpendicular_vector = OpenMaya.MVector(aim_vector) ^ OpenMaya.MVector(up_vector)
	axis_index = Z_AXIS_INDEX
	is_negative = is_vector_negative(perpendicular_vector)

	for axis_index, value in enumerate(perpendicular_vector):
		if int(value) != 0:
			break

	return axis_index, is_negative
