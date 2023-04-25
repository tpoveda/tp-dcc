import maya.api.OpenMaya as OpenMaya

from tp.maya.api import consts


def is_valid_mobject_handle(mobj_handle):
	"""
	Returns whether the given MObjectHandle is valid in the scene and still alive.

	:param OpenMaya.MObjectHandle mobj_handle: handle to check.
	:return: True if given MObjectHandle is valid; False otherwise.
	:rtype: bool
	"""

	return mobj_handle.isValid() and mobj_handle.isAlive()


def is_valid_mobject(mobj):
	"""
	Returns whether given Maya object is valid in the scene.

	:param OpenMaya.MObject mobj: Maya object to validate.
	:return: True if given Maya object is valid; False otherwise.
	:rtype: bool
	"""

	return is_valid_mobject_handle(OpenMaya.MObjectHandle(mobj))


def int_to_mtransform_rotation_order(rotate_order):
	"""
	Converts given index to a rotation order that can be passed to a MTranform node.

	:param int rotate_order: rotation order index defined in tp.maya.api.consts.
	:return: OpenMaya.MTransformationMatrix kConstant value.
	"""

	return consts.kRotateOrders.get(rotate_order, -1)
