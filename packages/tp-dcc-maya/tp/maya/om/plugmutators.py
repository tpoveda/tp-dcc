from __future__ import annotations

from typing import Any
from collections.abc import MutableMapping

import maya.api.OpenMaya as OpenMaya
import maya.api.OpenMayaAnim as OpenMayaAnim

from tp.core import log
from tp.common.python import helpers
from tp.maya.cmds import scene
from tp.maya.om import plugs, decorators, undo
from tp.maya.om.animation import animcurves, plugs as anim_plugs

logger = log.tpLogger


def as_boolean(plug: OpenMaya.MPlug, **kwargs: dict) -> bool:
    """
    Returns the boolean value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve boolean value from.
    :param dict kwargs: keyword arguments.
    :return: boolean value.
    :rtype: bool
    """

    return plug.asBool()


def as_integer(plug: OpenMaya.MPlug, **kwargs) -> int:
    """
    Returns the integer value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve integer value from.
    :param dict kwargs: keyword arguments.
    :return: integer value.
    :rtype: int
    """

    return plug.asInt()


def as_integer_array(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MIntArray:
    """
    Returns the integer array value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve integer array value from.
    :param dict kwargs: keyword arguments.
    :return: integer array value.
    :rtype: OpenMaya.MIntArray
    """

    try:
        return OpenMaya.MFnIntArrayData(plug.asMObject()).array()
    except RuntimeError:
        return OpenMaya.MIntArray()


def as_float(plug: OpenMaya.MPlug, **kwargs) -> float:
    """
    Returns the float value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve float value from.
    :param dict kwargs: keyword arguments.
    :return: float value.
    :rtype: float
    """

    return plug.asFloat()


def as_double_array(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MDoubleArray:
    """
    Returns the double array value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve double array value from.
    :param dict kwargs: keyword arguments.
    :return: double array value.
    :rtype: OpenMaya.MDoubleArray
    """

    try:
        return OpenMaya.MFnDoubleArrayData(plug.asMObject()).array()
    except RuntimeError:
        return OpenMaya.MDoubleArray()


def as_string(plug: OpenMaya.MPlug, **kwargs) -> str:
    """
    Returns the c value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve string value from.
    :param dict kwargs: keyword arguments.
    :return: string value.
    :rtype: str
    """

    return plug.asString()


def as_string_array(plug: OpenMaya.MPlug, **kwargs) -> list[str]:
    """
    Returns the double array value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve string array value from.
    :param dict kwargs: keyword arguments.
    :return: string array value.
    :rtype: list[str]
    """

    try:
        return OpenMaya.MFnStringArrayData(plug.asMObject()).array()
    except RuntimeError:
        return []


def as_matrix(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MMatrix:
    """
    Returns the matrix value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve matrix value from.
    :param dict kwargs: keyword arguments.
    :return: matrix value.
    :rtype: OpenMaya.MMatrix
    """

    fn_matrix_data = OpenMaya.MFnMatrixData(plug.asMObject())
    if fn_matrix_data.isTransformation():
        return fn_matrix_data.transformation().asMatrix()
    else:
        return fn_matrix_data.matrix()


def as_matrix_array(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MMatrixArray:
    """
    Returns the matrix array value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve matrix array value from.
    :param dict kwargs: keyword arguments.
    :return: matrix array value.
    :rtype: OpenMaya.MMatrixArray
    """

    try:
        return OpenMaya.MFnMatrixArrayData(plug.asMObject()).array()
    except RuntimeError:
        return OpenMaya.MMatrixArray()


def as_mobject(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MObject:
    """
    Returns the Maya object from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve Maya object from.
    :param dict kwargs: keyword arguments.
    :return: Maya object.
    :rtype: OpenMaya.MObject
    """

    return plug.asMObject()


def as_angle(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MAngle:
    """
    Returns the angle value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve angle value from.
    :param dict kwargs: keyword arguments.
    :return: angle value.
    :rtype: OpenMaya.MAngle
    """

    return plug.asMAngle()


def as_distance(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MDistance:
    """
    Returns the distance value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve distance value from.
    :param dict kwargs: keyword arguments.
    :return: distance value.
    :rtype: OpenMaya.MDistance
    """

    return plug.asMDistance()


def as_time(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MTime:
    """
    Returns the time value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve time value from.
    :param dict kwargs: keyword arguments.
    :return: time value.
    :rtype: OpenMaya.MTime
    """

    return plug.asMTime()


def as_message(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MObject:
    """
    Returns the connected node from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve connected node from.
    :param dict kwargs: keyword arguments.
    :return: connected node object.
    :rtype: OpenMaya.MObject
    """

    source = plug.source()
    return source.node() if not source.isNull else OpenMaya.MObject.kNullObj


def as_generic(plug: OpenMaya.MPlug, **kwargs):
    """
    Returns the generic value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve generic value from.
    :param dict kwargs: keyword arguments.
    """

    # TODO: Implement support for generic types!
    return None


def as_any(plug: OpenMaya.MPlug, **kwargs):
    """
    Returns the value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve any value from.
    :param dict kwargs: keyword arguments.
    """

    # TODO: Implement support for any types!
    return None


def as_compound(plug: OpenMaya.MPlug, **kwargs) -> dict[str, Any]:
    """
    Returns all the child values from the compound plug.

    :param OpenMaya.MPlug plug: plug to retrieve child values from.
    :param dict kwargs: keyword arguments.
    :return: child values.
    :rtype: dict[str, Any]
    """

    values: dict[str, Any] = {}
    for child in plugs.iterate_children(plug):
        name = child.partialName(useLongNames=True)
        values[name] = value(child)

    return values


__get_numeric_value__ = {
    OpenMaya.MFnNumericData.kByte: as_integer,
    OpenMaya.MFnNumericData.kBoolean: as_boolean,
    OpenMaya.MFnNumericData.kShort: as_integer,
    OpenMaya.MFnNumericData.kLong: as_integer,
    OpenMaya.MFnNumericData.kInt: as_integer,
    OpenMaya.MFnNumericData.kFloat: as_float,
    OpenMaya.MFnNumericData.kDouble: as_float,
    OpenMaya.MFnNumericData.kMatrix: as_matrix
}


__get_typed_value__ = {
    OpenMaya.MFnData.kMatrix: as_matrix,
    OpenMaya.MFnData.kMatrixArray: as_matrix_array,
    OpenMaya.MFnData.kNurbsCurve: as_mobject,
    OpenMaya.MFnData.kNurbsSurface: as_mobject,
    OpenMaya.MFnData.kLattice: as_mobject,
    OpenMaya.MFnData.kComponentList: as_mobject,
    OpenMaya.MFnData.kMesh: as_mobject,
    OpenMaya.MFnData.kString: as_string,
    OpenMaya.MFnData.kIntArray: as_integer_array,
    OpenMaya.MFnData.kFloatArray: as_double_array,
    OpenMaya.MFnData.kDoubleArray: as_double_array,
    OpenMaya.MFnData.kStringArray: as_string_array,
    OpenMaya.MFnData.kAny: as_any
}


__get_unit_value__ = {
    OpenMaya.MFnUnitAttribute.kAngle: as_angle,
    OpenMaya.MFnUnitAttribute.kDistance: as_distance,
    OpenMaya.MFnUnitAttribute.kTime: as_time
}


def numeric_type(attribute: OpenMaya.MObject) -> int:
    """
    Returns the numeric type from the given numeric attribute.

    :param OpenMaya.MObject attribute: numeric attribute.
    :return: numeric type.
    :rtype: int
    """

    return OpenMaya.MFnNumericAttribute(attribute).numericType()


def numeric_value(plug: OpenMaya.MPlug, **kwargs) -> bool | int | float | tuple:
    """
    Returns the numeric value from the given plug.

    :param OpenMaya.MPlug plug: plug to get numeric value from.
    :param dict kwargs: keyword arguments.
    :return: numeric value.
    :rtype: bool or int or float or tuple
    """

    return __get_numeric_value__[numeric_type(plug.attribute())](plug, **kwargs)


def unit_type(attribute: OpenMaya.MObject) -> int:
    """
    Returns the unit type from the given unit attribute.

    :param OpenMaya.MObject attribute: unit attribute.
    :return: unit type.
    :rtype: int
    """

    return OpenMaya.MFnUnitAttribute(attribute).unitType()


def unit_value(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MDistance | OpenMaya.MAngle:
    """
    Returns the unit value from the given plug.

    :param OpenMaya.MPlug plug: plug to get unit value from.
    :param dict kwargs: keyword arguments.
    :return: unit value.
    :rtype: OpenMaya.MDistance or OpenMaya.MAngle
    """

    return __get_unit_value__[unit_type(plug.attribute())](plug, **kwargs)


def data_type(attribute: OpenMaya.MObject) -> int:
    """
    Returns the data type from the given unit attribute.

    :param OpenMaya.MObject attribute: data attribute.
    :return: data type.
    :rtype: int
    """

    return OpenMaya.MFnTypedAttribute(attribute).attrType()


def typed_value(plug: OpenMaya.MPlug, **kwargs) -> OpenMaya.MMatrix | OpenMaya.MObject:
    """
    Returns the typed value from the given plug.

    :param OpenMaya.MPlug plug: plug to get typed value from.
    :param dict kwargs: keyword arguments.
    :return: typed value.
    :rtype: OpenMaya.MMatrix or OpenMaya.MObject
    """

    return __get_typed_value__[data_type(plug.attribute())](plug, **kwargs)


__get_value__ = {
    OpenMaya.MFn.kNumericAttribute: numeric_value,
    OpenMaya.MFn.kUnitAttribute: unit_value,
    OpenMaya.MFn.kTypedAttribute: typed_value,
    OpenMaya.MFn.kEnumAttribute: as_integer,
    OpenMaya.MFn.kMatrixAttribute: as_matrix,
    OpenMaya.MFn.kMessageAttribute: as_message,
    OpenMaya.MFn.kCompoundAttribute: as_compound,
    OpenMaya.MFn.kDoubleAngleAttribute: as_angle,
    OpenMaya.MFn.kDoubleLinearAttribute: as_distance,
    OpenMaya.MFn.kGenericAttribute: as_generic
}


def value(plug: OpenMaya.MPlug, convert_units: bool = True, best_layer: bool = False) -> Any:
    """
    Returns the value from the given plug.

    :param OpenMaya.MPlug plug: plug to retrieve value of.
    :param bool convert_units: whether to convert internal values to UI values.
    :param bool best_layer: whether the value from the active animation layer is returned instead.
    :return: plug value.
    :rtype: Any
    """

    if plug.isNull:
        return None

    # Evaluate plug type
    if plug.isArray and not plug.isElement:
        indices = plug.getExistingArrayAttributeIndices()
        num_indices = len(indices)
        plug_values = [None] * num_indices
        for (physical_index, logical_index) in enumerate(indices):
            element = plug.elementByLogicalIndex(logical_index)
            plug_values[physical_index] = value(element, convert_units=convert_units)
        return plug_values
    elif plugs.is_compound_numeric(plug):
        # Return list of values from parent plug.
        return [value(child, convert_units=convert_units) for child in plugs.iterate_children(plug, recursive=False)]
    else:
        # Check if active anim-layer should be evaluated.
        if best_layer and plugs.is_animated(plug):
            plug = anim_plugs.find_animated_plug(plug)
            return value(plug, convert_units=convert_units)

        # Get value from plug and check if any units require converting.
        attribute_type = plugs.api_type(plug)
        plug_value = __get_value__[attribute_type](plug)

        if convert_units and isinstance(plug_value, (OpenMaya.MDistance, OpenMaya.MAngle, OpenMaya.MTime)):
            return plug_value.asUnits(plug_value.uiUnit())

        return plug_value


def set_boolean(plug: OpenMaya.MPlug, value_to_set: bool, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the boolean value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set boolean value of.
    :param bool value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    modifier.newPlugValueBool(plug, bool(value_to_set))


def set_integer(plug: OpenMaya.MPlug, value_to_set: int, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the integer value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set integer value of.
    :param int value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    modifier.newPlugValueInt(plug, int(value_to_set))


def set_integer_array(
        plug: OpenMaya.MPlug, value_to_set: list[int] | OpenMaya.MIntArray, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the integer array value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set integer array value of.
    :param list[int] or OpenMaya.MIntArray value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    :raises TypeError: if given value to set is not a sequence of integers.
    """

    if isinstance(value_to_set, (list, tuple)):
        fn_int_array_data = OpenMaya.MFnDoubleArrayData()
        int_array_data = fn_int_array_data.create()
        fn_int_array_data.set(value_to_set)
    elif isinstance(value_to_set, (OpenMaya.MFloatArray, OpenMaya.MDoubleArray)):
        int_array_data = OpenMaya.MFnDoubleArrayData(value_to_set).object()
    elif isinstance(value_to_set, OpenMaya.MObject):
        int_array_data = value_to_set
    else:
        raise TypeError(f'set_integer_array() expects a sequence of integers ({type(value_to_set).__name__} given)!')
    modifier.newPlugValue(plug, int_array_data)


def set_float(plug: OpenMaya.MPlug, value_to_set: float, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the integer value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set float value of.
    :param float value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    modifier.newPlugValueFloat(plug, float(value_to_set))


def set_double_array(
        plug: OpenMaya.MPlug, value_to_set: list[int] | OpenMaya.MFloatArray, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the float array value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set float array value of.
    :param list[float] or OpenMaya.MFloatArray value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    :raises TypeError: if given value to set is not a sequence of floats.
    """

    if isinstance(value_to_set, (list, tuple)):
        fn_double_array_data = OpenMaya.MFnDoubleArrayData()
        double_array_data = fn_double_array_data.create()
        fn_double_array_data.set(value_to_set)
    elif isinstance(value_to_set, (OpenMaya.MFloatArray, OpenMaya.MDoubleArray)):
        double_array_data = OpenMaya.MFnDoubleArrayData(value_to_set).object()
    elif isinstance(value_to_set, OpenMaya.MObject):
        double_array_data = value_to_set
    else:
        raise TypeError(f'set_double_array() expects a sequence of floats ({type(value_to_set).__name__} given)!')
    modifier.newPlugValue(plug, double_array_data)


def set_string(plug: OpenMaya.MPlug, value_to_set: str, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the string value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set string value of.
    :param str value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    modifier.newPlugValueString(plug, value_to_set)


def set_string_array(
        plug: OpenMaya.MPlug, value_to_set: list[str], modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the string array value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set string array value of.
    :param list[str] value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    :raises TypeError: if given value to set is not a sequence of strings.
    """

    if isinstance(value, (list, tuple)):
        fn_string_array_data = OpenMaya.MFnStringArrayData()
        string_array_data = fn_string_array_data.create()
        fn_string_array_data.set(value)
    elif isinstance(value, OpenMaya.MObject):
        string_array_data = value
    else:
        raise TypeError(f'set_string_array() expects a sequence of strings ({type(value).__name__} given)!')
    modifier.newPlugValue(plug, string_array_data)


def set_matrix(plug: OpenMaya.MPlug, value_to_set: OpenMaya.MMatrix, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the matrix value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set matrix value of.
    :param OpenMaya.MMatrix value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    fn_matrix_data = OpenMaya.MFnMatrixData()
    matrix_data = fn_matrix_data.create()
    fn_matrix_data.set(value_to_set)
    modifier.newPlugValue(plug, matrix_data)


def set_matrix_array(
        plug: OpenMaya.MPlug, value_to_set: list[OpenMaya.MMatrix] | OpenMaya.MMatrixArray,
        modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the matrix array value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set matrix array value of.
    :param list[OpenMaya.MMatrix] or OpenMaya.MMatrixArray value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    :raises TypeError: if given value to set is not a sequence of matrices.
    """

    if isinstance(value_to_set, (list, tuple)):
        fn_matrix_array_data = OpenMaya.MFnMatrixArrayData()
        matrix_array_data = fn_matrix_array_data.create()
        fn_matrix_array_data.set(value_to_set)
    elif isinstance(value_to_set, OpenMaya.MMatrixArray):
        matrix_array_data = OpenMaya.MFnMatrixArrayData(value_to_set).object()
    elif isinstance(value_to_set, OpenMaya.MObject):
        matrix_array_data = value_to_set
    else:
        raise TypeError('set_matrix_array() expects a sequence of matrices!')
    modifier.newPlugValue(plug, matrix_array_data)


def set_mobject(plug: OpenMaya.MPlug, value_to_set: OpenMaya.MObject, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the Maya object for the given plug.

    :param OpenMaya.MPlug plug: plug we want to set Maya object of.
    :param OpenMaya.MObject value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    modifier.newPlugValue(plug, value)


def set_angle(plug: OpenMaya.MPlug, value_to_set: OpenMaya.MAngle, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the angle value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set angle value of.
    :param OpenMaya.MAngle value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    if not isinstance(value_to_set, OpenMaya.MAngle):
        convert_units = kwargs.get('convert_units', True)
        unit = OpenMaya.MAngle.uiUnit() if convert_units else OpenMaya.MAngle.internalUnit()
        value_to_set = OpenMaya.MAngle(value_to_set, unit=unit)
    modifier.newPlugValueMAngle(plug, value_to_set)


def set_distance(plug: OpenMaya.MPlug, value_to_set: OpenMaya.MDistance, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the distance value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set distance value of.
    :param OpenMaya.MDistance value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    if not isinstance(value_to_set, OpenMaya.MDistance):
        convert_units = kwargs.get('convert_units', True)
        unit = OpenMaya.MDistance.uiUnit() if convert_units else OpenMaya.MDistance.internalUnit()
        value_to_set = OpenMaya.MDistance(value_to_set, unit=unit)
    modifier.newPlugValueMDistance(plug, value_to_set)


def set_time(plug: OpenMaya.MPlug, value_to_set: OpenMaya.MTime, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the time value on the given plug.

    :param OpenMaya.MPlug plug: plug we want to set time value of.
    :param OpenMaya.MTime value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    if not isinstance(value_to_set, OpenMaya.MTime):
        value_to_set = OpenMaya.MTime(value, OpenMaya.MTime.uiUnit())
    modifier.newPlugValueMTime(plug, value_to_set)


def set_message(plug: OpenMaya.MPlug, value_to_connect: OpenMaya.MObject, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the connected messages plug node.

    :param OpenMaya.MPlug plug: plug we want to connect nodes to.
    :param OpenMaya.MObject value_to_connect: node to connect.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    if not value_to_connect.isNull():
        other_plug = OpenMaya.MFnDependencyNode(value).findPlug('message', True)
        plugs.connect_plugs(other_plug, plug, force=True)
    else:
        plugs.break_connections(plug, source=True, destination=False)


def set_compound(plug: OpenMaya.MPlug, values: list[Any] | dict[str, Any], modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the compound value for the given plug.

    :param OpenMaya.MPlug plug: plug we want to update compound value of.
    :param list[Any] or dict[str, Any] values: values to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    :raises TypeError: if given arguments are not of a valid type.
    """

    if isinstance(values, MutableMapping):
        fn_depend_node = OpenMaya.MFnDependencyNode(plug.node())
        for name, value_to_set in values.items():
            if not fn_depend_node.hasAttribute(name):
                continue
            # Get child plug
            # TODO: Improve child plug lookup logic
            attribute = fn_depend_node.attribute(name)
            fn_attribute = OpenMaya.MFnAttribute(attribute)
            parent_attribute = fn_attribute.parent
            has_parent = plug != parent_attribute and not parent_attribute.isNull()
            if has_parent:
                child_plug = plug.child(parent_attribute).child(attribute)
            else:
                child_plug = plug.child(attribute)
            # Update child plug.
            set_value(child_plug, value_to_set, modifier=modifier, **kwargs)
    elif helpers.is_array_like(values):  # Maya dataclasses aren't derived from the `Sequence` abstract base class!
        # Iterate through values.
        fn_compound_attribute = OpenMaya.MFnCompoundAttribute(plug.attribute())
        child_count = fn_compound_attribute.numChildren()
        for i, value in enumerate(values):
            # Check if indexed value is in range.
            if 0 <= i < child_count:
                child_attribute = fn_compound_attribute.child(i)
                child_plug = plug.child(child_attribute)
                set_value(child_plug, values[i], **kwargs)
    else:

        raise TypeError(f'set_compound() expects either a dict or tuple ({type(values).__name__} given)!')


__set_numeric_value__ = {
    OpenMaya.MFnNumericData.kByte: set_integer,
    OpenMaya.MFnNumericData.kBoolean: set_boolean,
    OpenMaya.MFnNumericData.kShort: set_integer,
    OpenMaya.MFnNumericData.kLong: set_integer,
    OpenMaya.MFnNumericData.kInt: set_integer,
    OpenMaya.MFnNumericData.kFloat: set_float,
    OpenMaya.MFnNumericData.kDouble: set_float,
    OpenMaya.MFnNumericData.kMatrix: set_matrix
}


__set_typed_value__ = {
    OpenMaya.MFnData.kMatrix: set_matrix,
    OpenMaya.MFnData.kMatrixArray: set_matrix_array,
    OpenMaya.MFnData.kNurbsCurve: set_mobject,
    OpenMaya.MFnData.kNurbsSurface: set_mobject,
    OpenMaya.MFnData.kLattice: set_mobject,
    OpenMaya.MFnData.kComponentList: set_mobject,
    OpenMaya.MFnData.kMesh: set_mobject,
    OpenMaya.MFnData.kString: set_string,
    OpenMaya.MFnData.kIntArray: set_integer_array,
    OpenMaya.MFnData.kFloatArray: set_double_array,
    OpenMaya.MFnData.kDoubleArray: set_double_array,
    OpenMaya.MFnData.kStringArray: set_string_array
}


__set_unit_value__ = {
    OpenMaya.MFnUnitAttribute.kAngle: set_angle,
    OpenMaya.MFnUnitAttribute.kDistance: set_distance,
    OpenMaya.MFnUnitAttribute.kTime: set_time
}


def set_numeric_value(
        plug: OpenMaya.MPlug, value_to_set: bool | int | float | tuple, modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the numeric value for the given plug.

    :param OpenMaya.MPlug plug: plug we want to update value of.
    :param bool or int or float or tuple value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    return __set_numeric_value__[numeric_type(plug.attribute())](plug, value_to_set, modifier=modifier, **kwargs)


def set_unit_value(
        plug: OpenMaya.MPlug, value_to_set: OpenMaya.MDistance | OpenMaya.MAngle,
        modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the unit value for the given plug.

    :param OpenMaya.MPlug plug: plug we want to update value of.
    :param OpenMaya.MDistance or OpenMaya.MAngle value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    return __set_unit_value__[unit_type(plug.attribute())](plug, value_to_set, modifier=modifier, **kwargs)


def set_typed_value(
        plug: OpenMaya.MPlug, value_to_set: OpenMaya.MMatrix | OpenMaya.MObject,
        modifier: OpenMaya.MDGModifier, **kwargs):
    """
    Updates the typed value for the given plug.

    :param OpenMaya.MPlug plug: plug we want to update value of.
    :param OpenMaya.MMatrix or OpenMaya.MObject value_to_set: value to set.
    :param OpenMaya.MDGModifier modifier: modifier to use to set value with.
    :param dict kwargs: keyword arguments.
    """

    return __set_typed_value__[data_type(plug.attribute())](plug, value_to_set, modifier=modifier, **kwargs)


__set_value__ = {
    OpenMaya.MFn.kNumericAttribute: set_numeric_value,
    OpenMaya.MFn.kUnitAttribute: set_unit_value,
    OpenMaya.MFn.kTimeAttribute: set_time,
    OpenMaya.MFn.kDoubleAngleAttribute: set_unit_value,
    OpenMaya.MFn.kDoubleLinearAttribute: set_unit_value,
    OpenMaya.MFn.kTypedAttribute: set_typed_value,
    OpenMaya.MFn.kEnumAttribute: set_integer,
    OpenMaya.MFn.kMatrixAttribute: set_matrix,
    OpenMaya.MFn.kMessageAttribute: set_message,
    OpenMaya.MFn.kCompoundAttribute: set_compound,
    OpenMaya.MFn.kAttribute2Float: set_compound,
    OpenMaya.MFn.kAttribute3Float: set_compound,
    OpenMaya.MFn.kAttribute2Double: set_compound,
    OpenMaya.MFn.kAttribute3Double: set_compound,
    OpenMaya.MFn.kAttribute4Double: set_compound,
    OpenMaya.MFn.kAttribute2Int: set_compound,
    OpenMaya.MFn.kAttribute3Int: set_compound,
    OpenMaya.MFn.kAttribute2Short: set_compound,
    OpenMaya.MFn.kAttribute3Short: set_compound
}


@decorators.locksmith
def set_value(plug: OpenMaya.MPlug, value_to_set: Any, modifier: OpenMaya.MDGModifier | None = None, **kwargs):
    """
    Updates the value for the given plug.

    :param OpenMaya.MPlug plug: plug we want to update value of.
    :param Any value_to_set: new plug value.
    :param OpenMaya.MDGModifier or None modifier: optional modifier to use to set plug value with.
    :param dict kwargs: keyword arguments.
    :raises TypeError: if we are setting an array plug but the given value is not a sequence.
    """

    if plug.isNull:
        return

    modifier = modifier or OpenMaya.MDGModifier()

    if plug.isArray and not plug.isElement:
        if not isinstance(value_to_set, (list, tuple)):
            raise TypeError('set_value() expects a sequence of values for array plugs!')

        # Check if space should be reallocated.
        num_elements = plug.numElements()
        num_items = len(value_to_set)
        if num_items > num_elements:
            plug.setNumElements(num_items)
        elif num_items < num_elements:
            plugs.remove_multi_instances(plug, list(range(num_items, num_elements)))

        # Assign values to plug elements and remove any excess elements
        for physical_index, item in enumerate(value_to_set):
            element = plug.elementByLogicalIndex(physical_index)
            set_value(element, item, modifier=modifier, **kwargs)
        if num_elements > num_items:
            plugs.remove_multi_instances(plug, list(range(num_items, num_elements)))
    elif plug.isCompound:
        set_compound(plug, value_to_set, modifier=modifier, **kwargs)
    else:
        # Check if plug is changeable.
        state = plug.isFreeToChange()
        if state != OpenMaya.MPlug.kFreeToChange:
            logger.debug(f'Plug is not free-to-change: {plug.info}')
            return
        # Check if auto-key is enabled
        auto_key = scene.auto_key()
        if auto_key and plugs.is_animatable(plug):
            key_value(plug, value_to_set)
        else:
            attribute_type = plugs.api_type(plug)
            __set_value__[attribute_type](plug, value_to_set, modifier=modifier, **kwargs)

    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()


def reset_value(plug: OpenMaya.MPlug, modifier: OpenMaya.MDGModifier | None = None, **kwargs):
    """
    Resets the value for the given plug back to its default value.

    :param OpenMaya.MPlug plug: plug we want to update value of.
    :param OpenMaya.MDGModifier or None modifier: optional modifier to use to reset plug value with.
    :param dict kwargs: keyword arguments.
    """

    if plug.isNull:
        return

    # Check if this is an array plug.
    if plug.isArray and not plug.isElement:
        num_elements = plug.numElements()
        for i in range(num_elements):
            reset_value(plug.elementByPhysicalIndex(i), modifier=modifier, **kwargs)
    elif plug.isCompound:
        num_children = plug.numChildren()
        for i in range(num_children):
            reset_value(plug.child(i), modifier=modifier, **kwargs)
    else:
        attribute = plug.attribute()
        default_value = OpenMaya.MObject.kNullObj
        if attribute.hasFn(OpenMaya.MFn.kNumericAttribute):
            default_value = OpenMaya.MFnNumericAttribute(attribute).default
        elif attribute.hasFn(OpenMaya.MFn.kUnitAttribute):
            default_value = OpenMaya.MFnUnitAttribute(attribute).default
        elif attribute.hasFn(OpenMaya.MFn.kEnumAttribute):
            default_value = OpenMaya.MFnEnumAttribute(attribute).default
        # Reset plug.
        set_value(plug, default_value, modifier=modifier, **kwargs)


def key_value(
        plug: OpenMaya.MPlug, value_to_key: Any, time: int | float | None = None, convert_units: bool = True,
        change: OpenMayaAnim.MAnimCurveChange | None = None):
    """
    Keys the plug at the given time.

    :param OpenMaya.MPlug plug: plug to key value of.
    :param Any value_to_key: plug value to key.
    :param int or float or None time: time to set key value.
    :param bool convert_units: whether to convert units.
    :param OpenMayaAnim.MAnimCurveChange or None change: optional animation curve change.
    :raises NotImplementedError: if blend mode is not supported.
    """

    if not plugs.is_animatable(plug):
        return

    # Check if value requires unit conversion.
    if convert_units:

        anim_curve_type = animcurves.anim_curve_type(plug.attribute())
        value_to_key = anim_plugs.ui_to_internal_unit(value_to_key, anim_curve_type=anim_curve_type)

    # Check if an anim-curve change was supplied
    change = change or OpenMayaAnim.MAnimCurveChange()

    # Check if plug is in an anim-layer
    # If so, adjust the value to compensate for the additive layer!
    # TODO: Add support for override layers!
    animated_plug = anim_plugs.find_animated_plug(plug)
    animated_node = animated_plug.node()

    is_anim_blend = anim_plugs.is_animation_blend(animated_node)
    if is_anim_blend:
        other_plug = anim_plugs.opposite_blend_input(animated_plug)
        other_value = value(other_plug, convert_units=False)
        blend_mode = anim_plugs.blend_mode(animated_node)
        if blend_mode == 0:  # Additive
            value_to_key = anim_plugs.expand_units(
                value_to_key, as_internal=True) - anim_plugs.expand_units(other_value, as_internal=True)
        elif blend_mode == 1:  # Multiply
            value_to_key = anim_plugs.expand_units(
                value_to_key, as_internal=True) / anim_plugs.expand_units(other_value, as_internal=True)
        else:
            raise NotImplementedError(f'key_value() no support for "{value_to_key.name}" blend mode!')

    # Find associated anim-curve from plug.
    anim_curve = animcurves.find_anim_curve(animated_plug, create=True)
    fn_anim_curve = OpenMayaAnim.MFnAnimCurve(anim_curve)

    # Check if time input already exists.
    time = scene.time() if time is None else time
    index = fn_anim_curve.find(time)

    if index is None:

        logger.debug(f'Updating {fn_anim_curve.name()} anim-curve: {value} @ {time}')
        fn_anim_curve.addKey(
            OpenMaya.MTime(
                time, unit=OpenMaya.MTime.uiUnit()), value, tangentInType=fn_anim_curve.kTangentAuto,
            tangentOutType=fn_anim_curve.kTangentAuto, change=change)
    else:

        logger.debug(f'Updating {fn_anim_curve.name()} anim-curve: {value} @ {time}')
        fn_anim_curve.setValue(index, value, change=change)

    # Cache anim-curve changes
    undo.commit(change.redoIt, change.undoIt)
