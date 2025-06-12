from __future__ import annotations

from typing import Type, Any

from maya.api import OpenMaya

kMFnNumericBoolean = 0
kMFnNumericShort = 1
kMFnNumericInt = 2
kMFnNumericLong = kMFnNumericInt
kMFnNumericLongLegacy = 3
kMFnNumericByte = 4
kMFnNumericFloat = 5
kMFnNumericDouble = 6
kMFnNumericAddr = 7
kMFnNumericChar = 8
kMFnUnitAttributeDistance = 9
kMFnUnitAttributeAngle = 10
kMFnUnitAttributeTime = 11
kMFnkEnumAttribute = 12
kMFnDataString = 13
kMFnDataMatrix = 14
kMFnDataFloatArray = 15
kMFnDataDoubleArray = 16
kMFnDataIntArray = 17
kMFnDataPointArray = 18
kMFnDataVectorArray = 19
kMFnDataStringArray = 20
kMFnDataMatrixArray = 21
kMFnCompoundAttribute = 22
kMFnNumericInt64 = 23
kMFnNumericLast = 24
kMFnNumeric2Double = 25
kMFnNumeric2Float = 26
kMFnNumeric2Int = 27
kMFnNumeric2Long = 28
kMFnNumeric2Short = 29
kMFnNumeric3Double = 30
kMFnNumeric3Float = 31
kMFnNumeric3Int = 32
kMFnNumeric3Long = 33
kMFnNumeric3Short = 34
kMFnNumeric4Double = 35
kMFnMessageAttribute = 36


_INTERNAL_TYPE_TO_MAYA_NUMERIC_TYPE = {
    kMFnNumericBoolean: (
        OpenMaya.MFnNumericAttribute,
        OpenMaya.MFnNumericData.kBoolean,
    ),
    kMFnNumericByte: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kByte),
    kMFnNumericShort: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kShort),
    kMFnNumericInt: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kInt),
    kMFnNumericLongLegacy: (
        OpenMaya.MFnNumericAttribute,
        OpenMaya.MFnNumericData.kLong,
    ),
    # backwards compatible with kLong
    kMFnNumericDouble: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kDouble),
    kMFnNumericFloat: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kFloat),
    kMFnNumericAddr: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kAddr),
    kMFnNumericChar: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kChar),
    kMFnNumeric2Double: (
        OpenMaya.MFnNumericAttribute,
        OpenMaya.MFnNumericData.k2Double,
    ),
    kMFnNumeric2Float: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Float),
    kMFnNumeric2Int: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Int),
    kMFnNumeric2Long: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Long),
    kMFnNumeric2Short: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Short),
    kMFnNumeric3Double: (
        OpenMaya.MFnNumericAttribute,
        OpenMaya.MFnNumericData.k3Double,
    ),
    kMFnNumeric3Float: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Float),
    kMFnNumeric3Int: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Int),
    kMFnNumeric3Long: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Long),
    kMFnNumeric3Short: (OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Short),
    kMFnNumeric4Double: (
        OpenMaya.MFnNumericAttribute,
        OpenMaya.MFnNumericData.k4Double,
    ),
}


_MAYA_TYPE_FROM_TYPE = dict(
    kMFnNumericBoolean=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kBoolean),
    kMFnNumericByte=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kByte),
    kMFnNumericShort=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kShort),
    kMFnNumericInt=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kInt),
    kMFnNumericLongLegacy=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kLong),
    kMFnNumericDouble=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kDouble),
    kMFnNumericFloat=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kFloat),
    kMFnNumericAddr=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kAddr),
    kMFnNumericChar=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.kChar),
    kMFnNumeric2Double=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Double),
    kMFnNumeric2Float=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Float),
    kMFnNumeric2Int=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Int),
    kMFnNumeric2Long=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Long),
    kMFnNumeric2Short=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k2Short),
    kMFnNumeric3Double=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Double),
    kMFnNumeric3Float=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Float),
    kMFnNumeric3Int=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Int),
    kMFnNumeric3Long=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Long),
    kMFnNumeric3Short=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k3Short),
    kMFnNumeric4Double=(OpenMaya.MFnNumericAttribute, OpenMaya.MFnNumericData.k4Double),
    kMFnUnitAttributeDistance=(
        OpenMaya.MFnUnitAttribute,
        OpenMaya.MFnUnitAttribute.kDistance,
    ),
    kMFnUnitAttributeAngle=(
        OpenMaya.MFnUnitAttribute,
        OpenMaya.MFnUnitAttribute.kAngle,
    ),
    kMFnUnitAttributeTime=(OpenMaya.MFnUnitAttribute, OpenMaya.MFnUnitAttribute.kTime),
    kMFnkEnumAttribute=(OpenMaya.MFnEnumAttribute, OpenMaya.MFn.kEnumAttribute),
    kMFnDataString=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kString),
    kMFnDataMatrix=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kMatrix),
    kMFnDataFloatArray=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kFloatArray),
    kMFnDataDoubleArray=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kDoubleArray),
    kMFnDataIntArray=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kIntArray),
    kMFnDataPointArray=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kPointArray),
    kMFnDataVectorArray=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kVectorArray),
    kMFnDataStringArray=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kStringArray),
    kMFnDataMatrixArray=(OpenMaya.MFnTypedAttribute, OpenMaya.MFnData.kMatrixArray),
    kMFnMessageAttribute=(OpenMaya.MFnMessageAttribute, OpenMaya.MFn.kMessageAttribute),
)

_TYPE_TO_STRING = {
    kMFnNumericBoolean: "kMFnNumericBoolean",
    kMFnNumericByte: "kMFnNumericByte",
    kMFnNumericShort: "kMFnNumericShort",
    kMFnNumericInt: "kMFnNumericInt",
    kMFnNumericLong: "kMFnNumericLong",
    kMFnNumericDouble: "kMFnNumericDouble",
    kMFnNumericFloat: "kMFnNumericFloat",
    kMFnNumericAddr: "kMFnNumericAddr",
    kMFnNumericChar: "kMFnNumericChar",
    kMFnNumeric2Double: "kMFnNumeric2Double",
    kMFnNumeric2Float: "kMFnNumeric2Float",
    kMFnNumeric2Int: "kMFnNumeric2Int",
    kMFnNumeric2Long: "kMFnNumeric2Long",
    kMFnNumeric2Short: "kMFnNumeric2Short",
    kMFnNumeric3Double: "kMFnNumeric3Double",
    kMFnNumeric3Float: "kMFnNumeric3Float",
    kMFnNumeric3Int: "kMFnNumeric3Int",
    kMFnNumeric3Long: "kMFnNumeric3Long",
    kMFnNumeric3Short: "kMFnNumeric3Short",
    kMFnNumeric4Double: "kMFnNumeric4Double",
    kMFnUnitAttributeDistance: "kMFnUnitAttributeDistance",
    kMFnUnitAttributeAngle: "kMFnUnitAttributeAngle",
    kMFnUnitAttributeTime: "kMFnUnitAttributeTime",
    kMFnkEnumAttribute: "kMFnkEnumAttribute",
    kMFnDataString: "kMFnDataString",
    kMFnDataMatrix: "kMFnDataMatrix",
    kMFnDataFloatArray: "kMFnDataFloatArray",
    kMFnDataDoubleArray: "kMFnDataDoubleArray",
    kMFnDataIntArray: "kMFnDataIntArray",
    kMFnDataPointArray: "kMFnDataPointArray",
    kMFnDataVectorArray: "kMFnDataVectorArray",
    kMFnDataStringArray: "kMFnDataStringArray",
    kMFnDataMatrixArray: "kMFnDataMatrixArray",
    kMFnMessageAttribute: "kMFnMessageAttribute",
    kMFnCompoundAttribute: "kMFnCompoundAttribute",
}

_PM_TYPE_TO_TYPE = {
    "bool": kMFnNumericBoolean,
    "short": kMFnNumericShort,
    "long": kMFnNumericLong,
    "byte": kMFnNumericByte,
    "float": kMFnNumericFloat,
    "double": kMFnNumericDouble,
    "char": kMFnNumericChar,
    "angle": kMFnUnitAttributeAngle,
    "time": kMFnUnitAttributeTime,
    "enum": kMFnkEnumAttribute,
    "string": kMFnDataString,
    "matrix": kMFnDataMatrix,
    "fltMatrix": kMFnDataFloatArray,
    "compound": kMFnCompoundAttribute,
    "short2": kMFnNumeric2Short,
    "short3": kMFnNumeric3Short,
    "long2": kMFnNumeric2Long,
    "long3": kMFnNumeric3Long,
    "float2": kMFnNumeric2Float,
    "float3": kMFnNumeric3Float,
    "double2": kMFnNumeric2Double,
    "double3": kMFnNumeric3Double,
    "message": kMFnMessageAttribute,
}

_MAYA_NUMERIC_TYPE_TO_INTERNAL_TYPE = {
    OpenMaya.MFnNumericData.kBoolean: kMFnNumericBoolean,
    OpenMaya.MFnNumericData.kByte: kMFnNumericByte,
    OpenMaya.MFnNumericData.kShort: kMFnNumericShort,
    OpenMaya.MFnNumericData.kInt: kMFnNumericInt,
    OpenMaya.MFnNumericData.kLong: kMFnNumericLong,
    OpenMaya.MFnNumericData.kDouble: kMFnNumericDouble,
    OpenMaya.MFnNumericData.kFloat: kMFnNumericFloat,
    OpenMaya.MFnNumericData.kAddr: kMFnNumericAddr,
    OpenMaya.MFnNumericData.kChar: kMFnNumericChar,
    OpenMaya.MFnNumericData.k2Double: kMFnNumeric2Double,
    OpenMaya.MFnNumericData.k2Float: kMFnNumeric2Float,
    OpenMaya.MFnNumericData.k2Int: kMFnNumeric2Int,
    OpenMaya.MFnNumericData.k2Long: kMFnNumeric2Long,
    OpenMaya.MFnNumericData.k2Short: kMFnNumeric2Short,
    OpenMaya.MFnNumericData.k3Double: kMFnNumeric3Double,
    OpenMaya.MFnNumericData.k3Float: kMFnNumeric3Float,
    OpenMaya.MFnNumericData.k3Int: kMFnNumeric3Int,
    OpenMaya.MFnNumericData.k3Long: kMFnNumeric3Long,
    OpenMaya.MFnNumericData.k3Short: kMFnNumeric3Short,
    OpenMaya.MFnNumericData.k4Double: kMFnNumeric4Double,
    OpenMaya.MFn.kAttribute2Int: kMFnNumeric2Int,
    OpenMaya.MFn.kAttribute3Int: kMFnNumeric3Int,
    OpenMaya.MFn.kAttribute2Short: kMFnNumeric2Short,
    OpenMaya.MFn.kAttribute3Short: kMFnNumeric3Short,
    OpenMaya.MFn.kAttribute2Double: kMFnNumeric2Double,
    OpenMaya.MFn.kAttribute3Double: kMFnNumeric3Double,
    OpenMaya.MFn.kAttribute4Double: kMFnNumeric4Double,
    OpenMaya.MFn.kAttribute2Float: kMFnNumeric2Float,
    OpenMaya.MFn.kAttribute3Float: kMFnNumeric3Float,
}

_MAYA_UNIT_TYPE_TO_INTERNAL_TYPE = {
    OpenMaya.MFnUnitAttribute.kDistance: kMFnUnitAttributeDistance,
    OpenMaya.MFnUnitAttribute.kAngle: kMFnUnitAttributeAngle,
    OpenMaya.MFnUnitAttribute.kTime: kMFnUnitAttributeTime,
}

_MAYA_MFN_DATA_TYPE_TO_INTERNAL_TYPE = {
    OpenMaya.MFnData.kString: kMFnDataString,
    OpenMaya.MFnData.kMatrix: kMFnDataMatrix,
    OpenMaya.MFnData.kFloatArray: kMFnDataFloatArray,
    OpenMaya.MFnData.kDoubleArray: kMFnDataDoubleArray,
    OpenMaya.MFnData.kIntArray: kMFnDataIntArray,
    OpenMaya.MFnData.kPointArray: kMFnDataPointArray,
    OpenMaya.MFnData.kVectorArray: kMFnDataVectorArray,
    OpenMaya.MFnData.kStringArray: kMFnDataStringArray,
    OpenMaya.MFnData.kMatrixArray: kMFnDataMatrixArray,
}

_MAYA_TYPE_TO_INTERNAL_TYPE = {
    OpenMaya.MFn.kEnumAttribute: kMFnkEnumAttribute,
    OpenMaya.MFn.kMessageAttribute: kMFnMessageAttribute,
    OpenMaya.MFn.kMatrixAttribute: kMFnDataMatrix,
}

MAYA_NUMERIC_MULTI_TYPES = (
    OpenMaya.MFnNumericData.k2Double,
    OpenMaya.MFnNumericData.k2Float,
    OpenMaya.MFnNumericData.k2Int,
    OpenMaya.MFnNumericData.k2Long,
    OpenMaya.MFnNumericData.k2Short,
    OpenMaya.MFnNumericData.k3Double,
    OpenMaya.MFnNumericData.k3Float,
    OpenMaya.MFnNumericData.k3Int,
    OpenMaya.MFnNumericData.k3Long,
    OpenMaya.MFnNumericData.k3Short,
    OpenMaya.MFnNumericData.k4Double,
)


def api_type_from_pymel_type(pymel_type: str) -> int:
    """
    Returns OpenMaya API type from PyMEL type.

    :param pymel_type: PyMEL attribute type.
    :return: OpenMaya type.
    """

    type_conversion = _PM_TYPE_TO_TYPE.get(pymel_type, None)

    return type_conversion


def maya_numeric_type_to_internal_type(maya_type: OpenMaya.MFnNumericData) -> int:
    """
    Returns the internal attribute type for the given Maya numeric type.

    :param maya_type: Maya attribute type.
    :return: internal API type.
    """

    return _MAYA_NUMERIC_TYPE_TO_INTERNAL_TYPE.get(maya_type)


def numeric_type_to_maya_fn_type(
    api_attribute_type: int,
) -> tuple[
    Type[OpenMaya.MFnNumericAttribute] | None, OpenMaya.MFnNumericData.kInt | None
]:
    """
    Returns the numeric attribute function object and the data type numericDataType for the given API type.

    :param api_attribute_type: internal API attribute type.
    :return: tuple of the numeric attribute and the data type.
    """

    type_conversion = _INTERNAL_TYPE_TO_MAYA_NUMERIC_TYPE.get(api_attribute_type)
    if not type_conversion:
        return None, None

    return type_conversion


def maya_unit_type_to_internal_type(maya_type: OpenMaya.MFnUnitAttribute) -> int:
    """
    Returns the internal API attribute type for the given Maya unit attribute type.

    :param maya_type: Maya attribute type.
    :return: internal API attribute type.
    """

    return _MAYA_UNIT_TYPE_TO_INTERNAL_TYPE.get(maya_type)


def maya_mfn_data_type_to_internal_type(maya_type: OpenMaya.MFnData) -> int:
    """
    Returns the internal API attribute type for the given Maya typed attribute.

    :param maya_type: Maya attribute type.
    :return: internal API attribute type.
    """

    return _MAYA_MFN_DATA_TYPE_TO_INTERNAL_TYPE.get(maya_type)


def maya_type_to_internal_type(maya_type: OpenMaya.MFnAttribute) -> int:
    """
    Returns the internal API attribute type for the given Maya attribute type.

    :param maya_type: Maya attribute type.
    :return: internal API type.
    """

    return _MAYA_TYPE_TO_INTERNAL_TYPE.get(maya_type)


def internal_type_to_string(api_attribute_type: int, default: str | None = None) -> str:
    """
    Coverts Maya attribute type as a string.

    :param api_attribute_type: internal API attribute type.
    :param default: default value to get.
    """

    return _TYPE_TO_STRING.get(api_attribute_type, default)


def maya_type_from_internal_type(
    api_type: int,
) -> tuple[OpenMaya.MFnAttribute | None, int | None]:
    """
    Returns the Maya type from the given internal API type.

    :param int api_type: internal API attribute type.
    :return: str
    """

    # noinspection PyTypeChecker
    type_conversion = _MAYA_TYPE_FROM_TYPE.get(api_type)
    if not type_conversion:
        return None, None

    return type_conversion


# noinspection PyTypeChecker
def maya_type_to_python_type(
    maya_type: OpenMaya.MFnAttribute,
) -> int | float | str | list:
    """
    Returns the python type from the given Maya type.

    :param maya_type: Maya attribute type.
    :return: Python type.
    :rtype: int, float, string or list
    """

    if isinstance(maya_type, (OpenMaya.MDistance, OpenMaya.MTime, OpenMaya.MAngle)):
        return maya_type.value
    elif isinstance(
        maya_type,
        (
            OpenMaya.MMatrix,
            OpenMaya.MVector,
            OpenMaya.MPoint,
            OpenMaya.MQuaternion,
            OpenMaya.MEulerRotation,
        ),
    ):
        return list(maya_type)

    return maya_type


def python_type_to_maya_type(python_type: Type, value: Any):
    """
    Returns the Maya type for the given Python type.

    :param python_type: Python type.
    :param value: Python value.
    :return: Maya attribute type.
    """

    if python_type == kMFnDataMatrixArray:
        # noinspection PyTypeChecker
        return list(map(OpenMaya.MMatrix, value))
    elif python_type == kMFnDataVectorArray:
        # noinspection PyTypeChecker
        return list(map(OpenMaya.MVector, value))
    elif python_type == kMFnUnitAttributeDistance:
        return OpenMaya.MDistance(value)
    elif python_type == kMFnUnitAttributeAngle:
        return OpenMaya.MAngle(value, OpenMaya.MAngle.kDegrees)
    elif python_type == kMFnUnitAttributeTime:
        return OpenMaya.MTime(value)

    return value
