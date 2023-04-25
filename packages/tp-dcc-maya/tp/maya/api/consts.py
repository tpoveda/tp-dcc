import maya.api.OpenMaya as OpenMaya

kRotateOrder_XYZ = 0
kRotateOrder_YZX = 1
kRotateOrder_ZXY = 2
kRotateOrder_XZY = 3
kRotateOrder_YXZ = 4
kRotateOrder_ZYX = 5

kRotateOrderNames = ('xyz', 'yzx', 'zxy', 'xzy', 'yxz', 'zyx')

kRotateOrders = {
	kRotateOrder_XYZ: OpenMaya.MTransformationMatrix.kXYZ,
	kRotateOrder_YZX: OpenMaya.MTransformationMatrix.kYZX,
	kRotateOrder_ZXY: OpenMaya.MTransformationMatrix.kZXY,
	kRotateOrder_XZY: OpenMaya.MTransformationMatrix.kXZY,
	kRotateOrder_YXZ: OpenMaya.MTransformationMatrix.kYXZ,
	kRotateOrder_ZYX: OpenMaya.MTransformationMatrix.kZYX
}
kMayaToRotateOrder = {
	OpenMaya.MTransformationMatrix.kXYZ: kRotateOrder_XYZ,
	OpenMaya.MTransformationMatrix.kYZX: kRotateOrder_YZX,
	OpenMaya.MTransformationMatrix.kZXY: kRotateOrder_ZXY,
	OpenMaya.MTransformationMatrix.kXZY: kRotateOrder_XZY,
	OpenMaya.MTransformationMatrix.kYXZ: kRotateOrder_YXZ,
	OpenMaya.MTransformationMatrix.kZYX: kRotateOrder_ZYX
}