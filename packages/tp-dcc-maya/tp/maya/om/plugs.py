#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya MPlugs
"""

import copy
import contextlib

import maya.api.OpenMaya as OpenMaya

from tp.core import log
from tp.maya.api import attributetypes

logger = log.tpLogger


@contextlib.contextmanager
def set_locked_context(plug):
    """
    Context manager to set the plug lock state to False then reset back to its original lock state.

    :param OpenMaya.MPlug plug: lock to work with.
    """

    current = plug.isLocked
    if current:
        plug.isLocked = False
    yield
    plug.isLocked = current


def as_mplug(attr_name):
    """
    Returns the MPlug instance of the given name
    :param attr_name: str, name of the Maya node to convert to MPlug
    :return: MPlug
    """

    try:
        names = attr_name.split('.')
        sel = OpenMaya.MSelectionList()
        sel.add(names[0])
        node = OpenMaya.MFnDependencyNode(sel.getDependNode(0))
        return node.findPlug('.'.join(names[1:]), False)
    except RuntimeError:
        sel = OpenMaya.MSelectionList()
        sel.add(str(attr_name))
        return sel.getPlug(0)


def numeric_value(plug, ctx=OpenMaya.MDGContext.kNormal):
    """
    Returns the numeric value of the given plug.

    :param OpenMaya.MPlug plug: plug to get numeric value of.
    :param OpenMaya.MDGContext ctx: context to use.
    :return: plug numeric value.
    :rtype: int or float
    """

    obj = plug.attribute()
    n_attr = OpenMaya.MFnNumericAttribute(obj)
    data_type = n_attr.numericType()
    if data_type == OpenMaya.MFnNumericData.kBoolean:
        return attributetypes.kMFnNumericBoolean, plug.asBool(ctx)
    elif data_type == OpenMaya.MFnNumericData.kByte:
        return attributetypes.kMFnNumericByte, plug.asBool(ctx)
    elif data_type == OpenMaya.MFnNumericData.kShort:
        return attributetypes.kMFnNumericShort, plug.asShort(ctx)
    elif data_type == OpenMaya.MFnNumericData.kInt:
        return attributetypes.kMFnNumericInt, plug.asInt(ctx)
    elif data_type == OpenMaya.MFnNumericData.kLong:
        return attributetypes.kMFnNumericLong, plug.asInt(ctx)
    elif data_type == OpenMaya.MFnNumericData.kDouble:
        return attributetypes.kMFnNumericDouble, plug.asDouble(ctx)
    elif data_type == OpenMaya.MFnNumericData.kFloat:
        return attributetypes.kMFnNumericFloat, plug.asFloat(ctx)
    elif data_type == OpenMaya.MFnNumericData.kAddr:
        return attributetypes.kMFnNumericAddr, plug.asInt(ctx)
    elif data_type == OpenMaya.MFnNumericData.kChar:
        return attributetypes.kMFnNumericChar, plug.asChar(ctx)
    elif data_type == OpenMaya.MFnNumericData.k2Double:
        return attributetypes.kMFnNumeric2Double, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k2Float:
        return attributetypes.kMFnNumeric2Float, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k2Int:
        return attributetypes.kMFnNumeric2Int, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k2Long:
        return attributetypes.kMFnNumeric2Long, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k2Short:
        return attributetypes.kMFnNumeric2Short, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k3Double:
        return attributetypes.kMFnNumeric3Double, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k3Float:
        return attributetypes.kMFnNumeric3Float, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k3Int:
        return attributetypes.kMFnNumeric3Int, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k3Long:
        return attributetypes.kMFnNumeric3Long, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k3Short:
        return attributetypes.kMFnNumeric3Short, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()
    elif data_type == OpenMaya.MFnNumericData.k4Double:
        return attributetypes.kMFnNumeric4Double, OpenMaya.MFnNumericData(plug.asMObject(ctx)).getData()

    return None, None


def typed_value(plug, ctx=OpenMaya.MDGContext.kNormal):
    """
    Returns Maya type from the given plug.

    :param OpenMaya.MPlug plug: plug instance to get type of.
    :param OpenMaya.MDGContext ctx: context to use.
    :return: Maya type
    :rtype: tuple
    """

    typed_attr = OpenMaya.MFnTypedAttribute(plug.attribute())
    data_type = typed_attr.attrType()
    if data_type == OpenMaya.MFnData.kInvalid:
        return None, None
    elif data_type == OpenMaya.MFnData.kString:
        return attributetypes.kMFnDataString, plug.asString(ctx)
    elif data_type == OpenMaya.MFnData.kNumeric:
        return numeric_value(plug, ctx=ctx)
    elif data_type == OpenMaya.MFnData.kMatrix:
        return attributetypes.kMFnDataMatrix, OpenMaya.MFnMatrixData(plug.asMObject(ctx)).matrix()
    # elif data_type == OpenMaya.MFnData.kFloatArray:
    #     return attributetypes.kMFnDataFloatArray, OpenMaya.MFnFloatArrayData(plug.asMObject()).array()
    elif data_type == OpenMaya.MFnData.kDoubleArray:
        return attributetypes.kMFnDataDoubleArray, OpenMaya.MFnDoubleArrayData(plug.asMObject(ctx)).array()
    elif data_type == OpenMaya.MFnData.kIntArray:
        return attributetypes.kMFnDataIntArray, OpenMaya.MFnIntArrayData(plug.asMObject(ctx)).array()
    elif data_type == OpenMaya.MFnData.kPointArray:
        return attributetypes.kMFnDataPointArray, OpenMaya.MFnPointArrayData(plug.asMObject(ctx)).array()
    elif data_type == OpenMaya.MFnData.kVectorArray:
        return attributetypes.kMFnDataVectorArray, OpenMaya.MFnVectorArrayData(plug.asMObject(ctx)).array()
    elif data_type == OpenMaya.MFnData.kStringArray:
        return attributetypes.kMFnDataStringArray, OpenMaya.MFnStringArrayData(plug.asMObject(ctx)).array()
    elif data_type == OpenMaya.MFnData.kMatrixArray:
        return attributetypes.kMFnDataMatrixArray, OpenMaya.MFnMatrixArrayData(plug.asMObject(ctx)).array()

    return None, None


def plug_value_and_type(plug, ctx=OpenMaya.MDGContext.kNormal):
    """
    Returns the value and the type of the given plug.

    :param OpenMaya.MPlug plug: plug to get value and type of.
    :param OpenMaya.MDGContext ctx: context to use.
    :return: plug value and its data type (if possible Python default types).
    :rtype: tuple(int, any)
    """

    obj = plug.attribute()
    if plug.isArray:
        count = plug.evaluateNumElements()
        res = [None] * count, [None] * count
        data = [plug_value_and_type(plug.elementByPhysicalIndex(i)) for i in range(count)]
        for i in range(len(data)):
            res[0][i] = data[i][0]
            res[1][i] = data[i][1]
        return res

    if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
        return numeric_value(plug, ctx=ctx)
    elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
        unit_attr = OpenMaya.MFnUnitAttribute(obj)
        unit_type = unit_attr.unitType()
        if unit_type == OpenMaya.MFnUnitAttribute.kDistance:
            return attributetypes.kMFnUnitAttributeDistance, plug.asMDistance(ctx)
        elif unit_type == OpenMaya.MFnUnitAttribute.kAngle:
            return attributetypes.kMFnUnitAttributeAngle, plug.asMAngle(ctx)
        elif unit_type == OpenMaya.MFnUnitAttribute.kTime:
            return attributetypes.kMFnUnitAttributeTime, plug.asMTime(ctx)
    elif obj.hasFn(OpenMaya.MFn.kEnumAttribute):
        return attributetypes.kMFnkEnumAttribute, plug.asInt(ctx)
    elif obj.hasFn(OpenMaya.MFn.kTypedAttribute):
        return typed_value(plug, ctx=ctx)
    elif obj.hasFn(OpenMaya.MFn.kMessageAttribute):
        source = plug.source()
        if source is not None:
            return attributetypes.kMFnMessageAttribute, source.node()
        return attributetypes.kMFnMessageAttribute, None
    elif obj.hasFn(OpenMaya.MFn.kMatrixAttribute):
        return attributetypes.kMFnDataMatrix, OpenMaya.MFnMatrixData(plug.asMObject(ctx)).matrix()

    if plug.isCompound:
        count = plug.numChildren()
        res = [None] * count, [None] * count
        data = [plug_value_and_type(plug.child(i), ctx=ctx) for i in range(count)]
        for i in range(len(data)):
            res[0][i] = data[i][0]
            res[1][i] = data[i][1]
        return res

    return None, None


def plug_type(plug):
    """
    Returns the type of the give plug.

    :param OpenMaya.MPlug plug: plug to get type of.
    :return: plug type.
    :rtype: str
    """

    obj = plug.attribute()
    if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
        num_attr = OpenMaya.MFnNumericAttribute(obj)
        data_type = obj.apiType()
        if data_type == OpenMaya.MFn.kNumericAttribute:
            data_type = num_attr.numericType()
        return attributetypes.maya_numeric_type_to_internal_type(data_type)
    elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
        u_attr = OpenMaya.MFnUnitAttribute(obj)
        return attributetypes.maya_unit_type_to_internal_type(u_attr.unitType())
    elif obj.hasFn(OpenMaya.MFn.kTypedAttribute):
        t_attr = OpenMaya.MFnTypedAttribute(obj)
        return attributetypes.maya_mfn_data_type_to_internal_type(t_attr.attrType())
    elif obj.hasFn(OpenMaya.MFn.kEnumAttribute):
        return attributetypes.kMFnkEnumAttribute
    elif obj.hasFn(OpenMaya.MFn.kMessageAttribute):
        return attributetypes.kMFnMessageAttribute
    elif obj.hasFn(OpenMaya.MFn.kMatrixAttribute):
        return attributetypes.kMFnDataMatrix
    elif obj.hasFn(OpenMaya.MFn.kCompoundAttribute):
        return attributetypes.kMFnCompoundAttribute

    return None


def python_type_from_plug_value(plug, ctx=OpenMaya.MDGContext.kNormal):
    """
    Returns the Python for the given plug value.

    :param OpenMaya.MPlug plug: Plug to get python type from its value.
    :param OpenMay.MDGContext ctx: optional context.
    :return: Python type.
    :rtype: int, float, bool or list
    """

    data_type, value = plug_value_and_type(plug, ctx)
    types = (attributetypes.kMFnDataMatrix, attributetypes.kMFnDataFloatArray,
             attributetypes.kMFnDataFloatArray, attributetypes.kMFnDataDoubleArray,
             attributetypes.kMFnDataIntArray, attributetypes.kMFnDataPointArray, attributetypes.kMFnDataStringArray,
             attributetypes.kMFnNumeric2Double, attributetypes.kMFnNumeric2Float, attributetypes.kMFnNumeric2Int,
             attributetypes.kMFnNumeric2Long, attributetypes.kMFnNumeric2Short, attributetypes.kMFnNumeric3Double,
             attributetypes.kMFnNumeric3Float, attributetypes.kMFnNumeric3Int, attributetypes.kMFnNumeric3Long,
             attributetypes.kMFnNumeric3Short, attributetypes.kMFnNumeric4Double)
    if data_type is None or data_type == attributetypes.kMFnMessageAttribute:
        return None
    elif isinstance(data_type, (list, tuple)):
        res = []
        for idx, dt in enumerate(data_type):
            if dt == attributetypes.kMFnDataMatrix:
                res.append(tuple(value[idx]))
            elif dt in (
                    attributetypes.kMFnUnitAttributeDistance, attributetypes.kMFnUnitAttributeAngle,
                    attributetypes.kMFnUnitAttributeTime):
                res.append(value[idx].value)
            elif dt in types:
                res.append(tuple(value[idx]))
            else:
                res.append(value[idx])
        return res
    elif data_type in (attributetypes.kMFnDataMatrixArray, attributetypes.kMFnDataVectorArray):
        return list(map(tuple, value))
    elif data_type in (
            attributetypes.kMFnUnitAttributeDistance, attributetypes.kMFnUnitAttributeAngle,
            attributetypes.kMFnUnitAttributeTime):
        return value.value
    elif data_type in types:
        return tuple(value)

    return value


def plug_value(plug, ctx=OpenMaya.MDGContext.kNormal):
    """
    Returns value of the given plug.

    :param OpenMaya.MPlug plug: plug to get value of.
    :param OpenMaya.MDGContext ctx: context to use.
    :return: plug value.
    :rtype: any
    """

    return plug_value_and_type(plug, ctx=ctx)[1]


def set_plug_value(plug, value, mod=None, apply=True):
    """
    Sets the given lugs value to the given passed value.

    :param OpenMaya.MPlug plug: plug to set value of.
    :param any value: value to set.
    :param OpenMaya.MDGModifier mod: optional Maya modifier to apply.
    :param bool apply: whether to apply the modifier instantly or leave it to the caller
    :return: modifier used to set plug value.
    :rtype: OpenMaya.MDGModifier
    """

    mod = mod or OpenMaya.MDGModifier()

    if plug.isArray:
        count = plug.evaluateNumElements()
        if count != len(value):
            return mod
        for i in range(count):
            set_plug_value(plug.elementByPhysicalIndex(i), value[i], mod=mod)
        return mod
    elif plug.isCompound:
        count = plug.numChildren()
        if count != len(value):
            return  mod
        for i in range(count):
            set_plug_value(plug.child(i), value[i], mod=mod)
        return mod

    obj = plug.attribute()
    if obj.hasFn(OpenMaya.MFn.kUnitAttribute):
        unit_attr = OpenMaya.MFnUnitAttribute(obj)
        unit_type = unit_attr.unitType()
        if unit_type == OpenMaya.MFnUnitAttribute.kDistance:
            mod.newPlugValueMDistance(plug, OpenMaya.MDistance(value))
        elif unit_type == OpenMaya.MFnUnitAttribute.kTime:
            mod.newPlugValueMTime(plug, OpenMaya.MTime(value))
        elif unit_type == OpenMaya.MFnUnitAttribute.kAngle:
            mod.newPlugValueMAngle(plug, OpenMaya.MAngle(value))
    elif obj.hasFn(OpenMaya.MFn.kNumericAttribute):
        numeric_attr = OpenMaya.MFnNumericAttribute(obj)
        numeric_type = numeric_attr.numericType()
        if numeric_type in (
                OpenMaya.MFnNumericData.k2Double, OpenMaya.MFnNumericData.k2Float,
                OpenMaya.MFnNumericData.k2Int, OpenMaya.MFnNumericData.k2Long,
                OpenMaya.MFnNumericData.k2Short, OpenMaya.MFnNumericData.k3Double,
                OpenMaya.MFnNumericData.k3Float, OpenMaya.MFnNumericData.k3Int,
                OpenMaya.MFnNumericData.k3Long, OpenMaya.MFnNumericData.k3Short,
                OpenMaya.MFnNumericData.k4Double):
            data = OpenMaya.MFnNumericData(obj).setData(value)
            mod.newPlugValue(plug, data.object())
        elif numeric_type == OpenMaya.MFnNumericData.kDouble:
            mod.newPlugValueDouble(plug, value)
        elif numeric_type == OpenMaya.MFnNumericData.kFloat:
            mod.newPlugValueFloat(plug, value)
        elif numeric_type == OpenMaya.MFnNumericData.kBoolean:
            mod.newPlugValueBool(plug, value)
        elif numeric_type == OpenMaya.MFnNumericData.kChar:
            mod.newPlugValueChar(plug, value)
        elif numeric_type in (
                OpenMaya.MFnNumericData.kInt, OpenMaya.MFnNumericData.kInt64,
                OpenMaya.MFnNumericData.kLong, OpenMaya.MFnNumericData.kLast, OpenMaya.MFnNumericData.kShort):
            mod.newPlugValueInt(plug, value)
    elif obj.hasFn(OpenMaya.MFn.kEnumAttribute):
        mod.newPlugValueInt(plug, value)
    elif obj.hasFn(OpenMaya.MFn.kTypedAttribute):
        typed_attr = OpenMaya.MFnTypedAttribute(obj)
        typed_type = typed_attr.attrType()
        if typed_type == OpenMaya.MFnData.kMatrix:
            mat = OpenMaya.MFnMatrixData().create(OpenMaya.MMatrix(value))
            mod.newPlugValue(plug, mat)
        elif typed_type == OpenMaya.MFnData.kString:
            mod.newPlugValueString(plug, value)
    elif obj.hasFn(OpenMaya.MFn.kMatrixAttribute):
        mat = OpenMaya.MFnMatrixData().create(OpenMaya.MMatrix(value))
        mod.newPlugValue(plug, mat)
    elif obj.hasFn(OpenMaya.MFn.kMessageAttribute) and not value:
        # Message attributes doesn't have any values
        pass
    elif obj.hasFn(OpenMaya.MFn.kMessageAttribute) and isinstance(value, OpenMaya.MPlug):
        # connect the message attribute
        connect_plugs(plug, value, mod=mod, apply=False)
    else:
        raise ValueError('Currently data type "{}" is not supported'.format(obj.apiTypeStr))

    if apply and mod:
        mod.doIt()

    return mod


def set_plug_info_from_dict(plug, **kwargs):
    """
    Sets the plug attributes from the given keyword arguments.

    :param OpenMaya.MPlug plug: plug to change.
    :param dict kwargs: keyword arguments.
    :raises RuntimeError: if an exception is raised while setting plug info.

    .. code-block:: python
        data = {
            "type": 5, # attributetypes.kType
            "channelBox": true,
            "default": 1.0,
            "isDynamic": true,
            "keyable": true,
            "locked": false,
            "max": 99999,
            "min": 0.0,
            "name": "scale",
            "softMax": None,
            "softMin": None,
            "value": 1.0,
            "children": [{}] # in the same format as the parent info
          }
        new_plug = om2.MPlug()
        set_plug_info_from_dict(new_plug, **data)
    """

    children = kwargs.get('children', list())
    if plug.isCompound and not plug.isArray:
        child_count = plug.numChildren()
        if not children:
            children = [copy.deepcopy(kwargs) for i in range(child_count)]
            for i, child_info in enumerate(children):
                if not child_info:
                    continue
                if i in range(child_count):
                    value = child_info.get('value')
                    default_value = child_info.get('default')
                    if value is not None and i in range(len(value)):
                        child_info['value'] = value[i]
                    if default_value is not None and i in range(len(default_value)):
                        child_info['default'] = default_value[i]
                    set_plug_info_from_dict(plug.child(i), **child_info)
        else:
            for i, child_info in enumerate(children):
                if not child_info:
                    continue
                if i in range(child_count):
                    child_plug = plug.child(i)
                    try:
                        set_plug_info_from_dict(child_plug, **child_info)
                    except RuntimeError:
                        logger.error('Failed to set default values on plug: {}'.format(
                            child_plug.name()), extra={'attributeDict': child_info})
                        raise

    default = kwargs.get('default')
    min = kwargs.get('min')
    max = kwargs.get('max')
    soft_min = kwargs.get('softMin')
    soft_max = kwargs.get('softMax')
    value = kwargs.get('value')
    type = kwargs.get('type')
    channel_box = kwargs.get('channelBox')
    keyable = kwargs.get('keyable')
    locked = kwargs.get('locked')

    if default is not None:
        if type == attributetypes.kMFnDataString:
            default = OpenMaya.MFnStringData().create(default)
        elif type == attributetypes.kMFnDataMatrix:
            default = OpenMaya.MMatrix(default)
        elif type == attributetypes.kMFnUnitAttributeAngle:
            default = OpenMaya.MAngle(default, OpenMaya.MAngle.kRadians)
        elif type == attributetypes.kMFnUnitAttributeDistance:
            default = OpenMaya.MDistance(default)
        elif type == attributetypes.kMFnUnitAttributeTime:
            default = OpenMaya.MTime(default)
        try:
            set_plug_default(plug, default)
        except Exception:
            logger.error('Failed to set plug default values: {}'.format(plug.name()),
                         exc_info=True,
                         extra={'data': default})
            raise

    # some attribute types need to be casted
    if value is not None:
        if type == attributetypes.kMFnDataMatrix:
            value = OpenMaya.MMatrix(value)
        elif type == attributetypes.kMFnUnitAttributeAngle:
            value = OpenMaya.MAngle(value, OpenMaya.MAngle.kRadians)
        elif type == attributetypes.kMFnUnitAttributeDistance:
            value = OpenMaya.MDistance(value)
        elif type == attributetypes.kMFnUnitAttributeTime:
            value = OpenMaya.MTime(value)

    if value is not None and not plug.isCompound and not plug.isArray:
        set_plug_value(plug, value)
    if min is not None:
        set_min(plug, min)
    if max is not None:
        set_max(plug, max)
    if soft_min is not None:
        set_soft_min(plug, soft_min)
    if soft_max is not None:
        set_soft_max(plug, soft_max)
    if channel_box is not None:
        plug.isChannelBox = channel_box
    if keyable is not None:
        plug.isKeyable = keyable
    if locked is not None:
        plug.isLocked = locked



def plug_fn(mobj):
    """
    Returns the function set for the given plug Maya object

    :param OpenMaya.MObject mobj: plug Maya object instance to get function set of.
    :return: function of the given plug Maya object.
    :rtype: OpenMaya.MFn
    """

    if mobj.hasFn(OpenMaya.MFn.kCompoundAttribute):
        return OpenMaya.MFnCompoundAttribute
    elif mobj.hasFn(OpenMaya.MFn.kEnumAttribute):
        return OpenMaya.MFnEnumAttribute
    elif mobj.hasFn(OpenMaya.MFn.kGenericAttribute):
        return OpenMaya.MFnGenericAttribute
    elif mobj.hasFn(OpenMaya.MFn.kLightDataAttribute):
        return OpenMaya.MFnLightDataAttribute
    elif mobj.hasFn(OpenMaya.MFn.kMatrixAttribute):
        return OpenMaya.MFnMatrixAttribute
    elif mobj.hasFn(OpenMaya.MFn.kMessageAttribute):
        return OpenMaya.MFnMessageAttribute
    elif mobj.hasFn(OpenMaya.MFn.kNumericAttribute):
        return OpenMaya.MFnNumericAttribute
    elif mobj.hasFn(OpenMaya.MFn.kTypedAttribute):
        return OpenMaya.MFnTypedAttribute
    elif mobj.hasFn(OpenMaya.MFn.kUnitAttribute):
        return OpenMaya.MFnUnitAttribute

    return OpenMaya.MFnAttribute


def plug_default(plug):
    """
    Returns the default value for the given plug.

    :param OpenMaya.MPlug plug: plug we want to retrieve default value of.
    :return: plug default value.
    :rtype: any
    """

    obj = plug.attribute()
    if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
        attr = OpenMaya.MFnNumericAttribute(obj)
        if attr.numericType() == OpenMaya.MFnNumericData.kInvalid:
            return None
        return attr.default
    elif obj.hasFn(OpenMaya.MFn.kTypedAttribute):
        attr = OpenMaya.MFnTypedAttribute(obj)
        default = attr.default
        if default.apiType() == OpenMaya.MFn.kInvalid:
            return None
        elif default.apiType() == OpenMaya.MFn.kStringData:
            return OpenMaya.MFnStringData(default).string()
        return default
    elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
        attr = OpenMaya.MFnUnitAttribute(obj)
        return attr.default
    elif obj.hasFn(OpenMaya.MFn.kMatrixAttribute):
        attr = OpenMaya.MFnMatrixAttribute(obj)
        return attr.default
    elif obj.hasFn(OpenMaya.MFn.kEnumAttribute):
        attr = OpenMaya.MFnEnumAttribute(obj)
        return attr.default

    return None


def set_attribute_fn_default(attribute, default):
    """
    Sets the default value for the given attribute.

    :param OpenMaya.MObject attribute: attribute the Maya object to set default value of.
    :param any default: default attribute value.
    :return: True if the attribute default set was completed; False otherwise.
    :rtype: bool
    :raises ValueError: if an invalid attribute type was given.
    """

    if attribute.hasFn(OpenMaya.MFn.kNumericAttribute):
        attr = OpenMaya.MFnNumericAttribute(attribute)
        attr_type = attr.numericType()
        attr.default = tuple(default) if attr_type in attributetypes.MAYA_NUMERIC_MULTI_TYPES else default
        return True

    elif attribute.hasFn(OpenMaya.MFn.kTypedAttribute):
        if not isinstance(default, OpenMaya.MObject):
            raise ValueError(
                'Wrong type passed to MFnTypeAttribute must be on type MObject, received : {}'.format(type(default)))
        attr = OpenMaya.MFnTypedAttribute(attribute)
        attr.default = default
        return True

    elif attribute.hasFn(OpenMaya.MFn.kUnitAttribute):
        if not isinstance(default, (OpenMaya.MAngle, OpenMaya.MDistance, OpenMaya.MTime)):
            raise ValueError(
                'Wrong type passed to MFnUnitAttribute must be on type MAngle,MDistance or MTime, received : {}'.format(
                    type(default)))
        attr = OpenMaya.MFnUnitAttribute(attribute)
        attr.default = default
        return True

    elif attribute.hasFn(OpenMaya.MFn.kMatrixAttribute):
        attr = OpenMaya.MFnMatrixAttribute(attribute)
        attr.default = default
        return True

    elif attribute.hasFn(OpenMaya.MFn.kEnumAttribute):
        if not isinstance(default, (int, str)):
            raise ValueError(
                'Wrong type passed to MFnEnumAttribute must be on type int or float, received : {}'.format(
                    type(default)))
        attr = OpenMaya.MFnEnumAttribute(attribute)
        field_names = list()
        for i in range(attr.getMin(), attr.getMax() + 1):
            # enums can be a bit screwed, i.e 5 options but max 10
            try:
                field_names.append(attr.fieldName(i))
            except Exception:
                pass
        if isinstance(default, int):
            if default >= len(field_names):
                return False
            attr.default = default
        else:
            if default not in field_names:
                return False
            attr.setDefaultByName(default)
        return True

    return False


def set_plug_default(plug, default):
    """
    Sets the default value for the given plug.

    :param OpenMaya.MPlug plug: plug we want to set default value of.
    :param any default: default plug value.
    """

    return set_attribute_fn_default(plug.attribute(), default)


def has_plug_min(plug):
    """
    Returns whether given plug has a min value set.

    :param OpenMaya.MPlug plug: plug to check plug min.
    :return: True if the given plug has a min value set; False otherwise.
    :rtype: bool
    """

    obj = plug.attribute()
    try:
        if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
            attr = OpenMaya.MFnNumericAttribute(obj)
            return attr.hasMin()
        elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
            attr = OpenMaya.MFnUnitAttribute(obj)
            return attr.hasMin()
    except RuntimeError:
        return False
    return False


def has_plug_max(plug):
    """
    Returns whether given plug has a max value set.

    :param OpenMaya.MPlug plug: plug to check plug max.
    :return: True if the given plug has a max value set; False otherwise.
    :rtype: bool
    """

    obj = plug.attribute()
    try:
        if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
            attr = OpenMaya.MFnNumericAttribute(obj)
            return attr.hasMax()
        elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
            attr = OpenMaya.MFnUnitAttribute(obj)
            return attr.hasMax()
    except RuntimeError:
        return False
    return False


def has_plug_soft_min(plug):
    """
    Returns whether given plug has a soft min value set.

    :param OpenMaya.MPlug plug: plug to check plug soft min.
    :return: True if the given plug has a soft min value set; False otherwise.
    :rtype: bool
    """

    obj = plug.attribute()
    try:
        if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
            attr = OpenMaya.MFnNumericAttribute(obj)
            return attr.hasSoftMin()
        elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
            attr = OpenMaya.MFnUnitAttribute(obj)
            return attr.hasSoftMin()
    except RuntimeError:
        return False
    return False


def has_plug_soft_max(plug):
    """
    Returns whether given plug has a soft max value set.

    :param OpenMaya.MPlug plug: plug to check plug soft max.
    :return: True if the given plug has a soft max value set; False otherwise.
    :rtype: bool
    """

    try:
        obj = plug.attribute()
        if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
            attr = OpenMaya.MFnNumericAttribute(obj)
            return attr.hasSoftMax()
        elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
            attr = OpenMaya.MFnUnitAttribute(obj)
            return attr.hasSoftMax()
    except RuntimeError:
        return False
    return False


def plug_min(plug):
    """
    Returns the given plug min value.

    :param OpenMaya.MPlug plug: plug to get min value of.
    :return: min value of the given plug.
    :rtype: int
    """

    try:
        obj = plug.attribute()
        if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
            attr = OpenMaya.MFnNumericAttribute(obj)
            if attr.hasMin():
                return attr.getMin()
        elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
            attr = OpenMaya.MFnUnitAttribute(obj)
            if attr.hasMin():
                return attr.getMin()
        elif obj.hasFn(OpenMaya.MFn.kEnumAttribute):
            attr = OpenMaya.MFnEnumAttribute(obj)
            return attr.getMin()
    except RuntimeError:
        return


def plug_max(plug):
    """
    Returns the given plug max value.

    :param OpenMaya.MPlug plug: plug to get max value of.
    :return: max value of the given plug.
    :rtype: int
    """

    obj = plug.attribute()
    try:
        if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
            attr = OpenMaya.MFnNumericAttribute(obj)
            if attr.hasMax():
                return attr.getMax()
        elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
            attr = OpenMaya.MFnUnitAttribute(obj)
            if attr.hasMax():
                return attr.getMax()
        elif obj.hasFn(OpenMaya.MFn.kEnumAttribute):
            attr = OpenMaya.MFnEnumAttribute(obj)
            return attr.getMax()
    except RuntimeError:
        return


def soft_min(plug):
    """
    Returns the given plug soft min value.

    :param OpenMaya.MPlug plug: plug to get soft min value of.
    :return: soft min value of the given plug.
    :rtype: int
    """

    obj = plug.attribute()
    try:
        if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
            attr = OpenMaya.MFnNumericAttribute(obj)

            if attr.hasSoftMin():
                return attr.getSoftMin()

        elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
            attr = OpenMaya.MFnUnitAttribute(obj)
            if attr.hasSoftMin():
                return attr.getSoftMin()
    except RuntimeError:
        # occurs when the attrs data type ie. float3 doesn't support min
        return


def set_attr_soft_min(attribute, value):
    """
    Sets the given attribute soft min value.

    :param OpenMaya.MObject attribute: Maya object representing the attribute we want to set soft min value of.
    :param int value: plug sot min value.
    :return: True if the soft min value was set successfully; False otherwise.
    :rtype: bool
    """

    if attribute.hasFn(OpenMaya.MFn.kNumericAttribute):
        attr = OpenMaya.MFnNumericAttribute(attribute)
        attr.setSoftMin(value)
        return True
    elif attribute.hasFn(OpenMaya.MFn.kUnitAttribute):
        attr = OpenMaya.MFnUnitAttribute(attribute)
        attr.setSoftMin(value)
        return True

    return False


def set_soft_min(plug, value):
    """
    Sets the given plug soft min value.

    :param OpenMaya.MPlug plug: plug to set soft min value of.
    :param int value: plug sot min value.
    :return: True if the soft min value was set successfully; False otherwise.
    :rtype: bool
    """

    return set_attr_soft_min(plug.attribute(), value)


def soft_max(plug):
    """
    Returns the given plug soft max value.

    :param OpenMaya.MPlug plug: plug to get soft max value of.
    :return: soft max value of the given plug.
    :rtype: int
    """

    obj = plug.attribute()
    try:
        if obj.hasFn(OpenMaya.MFn.kNumericAttribute):
            attr = OpenMaya.MFnNumericAttribute(obj)
            if attr.hasSoftMax():
                return attr.getSoftMax()
        elif obj.hasFn(OpenMaya.MFn.kUnitAttribute):
            attr = OpenMaya.MFnUnitAttribute(obj)
            if attr.hasSoftMax():
                return attr.getSoftMax()
    except RuntimeError:
        pass


def set_attr_soft_max(attribute, value):
    """
    Sets the given attribute soft max value.

    :param OpenMaya.MObject attribute: Maya object representing the attribute we want to set soft max value of.
    :param int value: plug sot max value.
    :return: True if the soft max value was set successfully; False otherwise.
    :rtype: bool
    """

    if attribute.hasFn(OpenMaya.MFn.kNumericAttribute):
        attr = OpenMaya.MFnNumericAttribute(attribute)
        attr.setSoftMax(value)
        return True
    elif attribute.hasFn(OpenMaya.MFn.kUnitAttribute):
        attr = OpenMaya.MFnUnitAttribute(attribute)
        attr.setSoftMax(value)
        return True

    return False


def set_soft_max(plug, value):
    """
    Sets the given plug soft max value.

    :param OpenMaya.MPlug plug: plug to set soft max value of.
    :param int value: plug sot max value.
    :return: True if the soft max value was set successfully; False otherwise.
    :rtype: bool
    """

    return set_attr_soft_max(plug.attribute(), value)


def set_attr_min(attribute, value):
    """
    Sets the given attribute min value.

    :param OpenMaya.MObject attribute: Maya object representing the attribute we want to set min value of.
    :param int value: plug min value.
    :return: True if the min value was set successfully; False otherwise.
    :rtype: bool
    """

    if attribute.hasFn(OpenMaya.MFn.kNumericAttribute):
        attr = OpenMaya.MFnNumericAttribute(attribute)
        attr.setMin(value)
        return True
    elif attribute.hasFn(OpenMaya.MFn.kUnitAttribute):
        attr = OpenMaya.MFnUnitAttribute(attribute)
        attr.setMin(value)
        return True
    return False


def set_min(plug, value):
    """
    Sets the given plug min value.

    :param OpenMaya.MPlug plug: plug to set min value of.
    :param int value: plug min value.
    :return: True if the min value was set successfully; False otherwise.
    :rtype: bool
    """

    return set_attr_min(plug.attribute(), value)


def set_attr_max(attribute, value):
    """
    Sets the given attribute max value.

    :param OpenMaya.MObject attribute: Maya object representing the attribute we want to set max value of.
    :param int value: plug max value.
    :return: True if the max value was set successfully; False otherwise.
    :rtype: bool
    """

    if attribute.hasFn(OpenMaya.MFn.kNumericAttribute):
        attr = OpenMaya.MFnNumericAttribute(attribute)
        attr.setMax(value)
        return True
    elif attribute.hasFn(OpenMaya.MFn.kUnitAttribute):
        attr = OpenMaya.MFnUnitAttribute(attribute)
        attr.setMax(value)
        return True
    return False


def set_max(plug, value):
    """
    Sets the given plug max value.

    :param OpenMaya.MPlug plug: plug to set max value of.
    :param int value: plug max value.
    :return: True if the max value was set successfully; False otherwise.
    :rtype: bool
    """

    return set_attr_max(plug.attribute(), value)


def connect_plugs(source, target, mod=None, force=True, apply=True):
    """
    Connects given plugs together.

    :param OpenMaya.MPlug source: plug to connect.
    :param OpenMaya.MPlug target: target plag to connect into.
    :param OpenMaya.MDGModifier mod: optional Maya modifier to apply.
    :param bool force: whether to force the connection.
    :param bool apply: whether to apply the modifier instantly or leave it to the caller.
    :return:
    """

    modifier = mod or OpenMaya.MDGModifier()

    if target.isDestination:
        target_source = target.source()
        if force:
            modifier.disconnect(target_source, target)
        else:
            raise ValueError('Plug {} has incoming connection {}'.format(target.name(), target_source.name()))
    modifier.connect(source, target)
    if mod is None and apply:
        modifier.doIt()

    return modifier


def connect_vector_plugs(source_compound, destination_compound, connection_values, force=True, mod=None, apply=True):
    """
    Connects given compound plugs together.

    :param OpenMaya.MPlug source_compound:
    :param OpenMaya.MPlug destination_compound:
    :param list(bool) connection_values: bool values for each axis. If all axis are True, then just connect the
        compound attribute.
    :param bool force: whether to force the connection.
    :param maya.api.OpenMaya.MDGModifier modifier: optional Maya modifier to apply.
    :param bool apply: whether to apply the modifier instantly or leave it to the caller.
    :return: created Maya modifier.
    :rtype: DGModifier
    :raises ValueError: if connect values count is larger than the compound child count.
    """

    if all(connection_values):
        connect_plugs(source_compound, destination_compound, force=force, mod=mod, apply=apply)
        return

    source_count = source_compound.numChildren()
    child_count = destination_compound.numChildren()
    request_length = len(connection_values)
    if child_count < request_length or source_count < request_length:
        raise ValueError('Connection values argument is larger than the compound child count')

    mod = mod or OpenMaya.MDGModifier()
    for i in range(len(connection_values)):
        value = connection_values[i]
        child_source = source_compound.child(i)
        child_destination = destination_compound.child(i)
        if not value:
            if child_destination.isDestination:
                disconnect_plug(child_destination.source(), child_destination)
            continue
        connect_plugs(child_source, child_destination, mod=mod, force=force)

    if apply:
        mod.doIt()

    return mod


def disconnect_plug(plug, source=True, destination=True, modifier=None):
    """
    Disconnects the plug connections, if "source" is True and the plug is a destination then disconnect the source
    from this plug. If destination is True and plug is a source the disconnect this plug from the destination.
    Plugs are also locked (to avoid Maya raises an error).

    :param OpenMaya.MpLUG plug: plug to disconnect.
    :param bool source: if True, disconnect from the connected source plug if it has one.
    :param bool destination: if True, disconnect from the connected destination plug if it has one.
    :param maya.api.OpenMaya.MDGModifier modifier: optional Maya modifier to apply.
    :return: bool, True if succeed with the disconnection.
    """

    if plug.isLocked:
        plug.isLocked = False
    mod = modifier or OpenMaya.MDGModifier()
    if source and plug.isDestination:
        source_plug = plug.source()
        if source_plug.isLocked:
            source_plug.isLocked = False
        mod.disconnect(source_plug, plug)
    if destination and plug.isSource:
        for connection in plug.destinations():
            if connection.isLocked:
                connection.isLocked = False
            mod.disconnect(plug, connection)
    if not modifier:
        mod.doIt()

    return True, mod


def next_available_element_plug(array_plug):
    """
    Returns the next available element plug from the plug array.

    Loops through all current elements looking for an out connection, if one does not exist then this element plug is
    returned. If the plug array is a compound one then the children of immediate children of the compound are searched
    and the element parent plug will be returned if there is a connection.

    :param OpenMaya.MPlug array_plug: plug array to search.
    :return: next plug.
    :rtype: OpenMaya.MPlug
    """

    indices = array_plug.getExistingArrayAttributeIndices() or [0]
    count = max(indices)

    # we want to iterate further then the max index so we add two due to arrays starting a zero and 1 for the extra
    # available index maya creates
    count += 2
    for i in range(count):
        available_plug = array_plug.elementByLogicalIndex(i)
        if array_plug.isCompound:
            connected = False
            for child_index in range(available_plug.numChildren()):
                if available_plug.child(child_index).isSource:
                    connected = True
                    break
        else:
            connected = available_plug.isSource
        if connected or available_plug.isSource:
            continue

        return available_plug

    return None


def next_available_dest_element_plug(array_plug):
    """
    Returns the next available input plug from the plug array.

    :param OpenMaya.MPlug array_plug: plug array to search.
    :return: next input plug.
    :rtype: OpenMaya.MPlug
    """

    indices = array_plug.getExistingArrayAttributeIndices() or [0]
    count = max(indices)

    # we want to iterate further then the max index so we add two due to arrays starting a zero and 1 for the extra
    # available index maya creates
    count += 2
    for i in range(count):
        available_plug = array_plug.elementByLogicalIndex(i)
        if available_plug.isCompound:
            connected = False
            for child_index in range(available_plug.numChildren()):
                if available_plug.child(child_index).isDestination:
                    connected = True
                    break
            if connected:
                continue
        if available_plug.isDestination:
            continue

        return available_plug

    return None


def has_child_plug_by_name(parent_plug, child_name):
    """
    Returns whether the given parent plug has a child plug with given name.

    :param OpenMaya.MPlug parent_plug: plug to check child plug by name.
    :param str child_name: name of the child plug.
    :return: True if the given parent plug has a child plug with give name; False otherwise.
    :rtype: bool
    """

    for child in iterate_children(parent_plug):
        if child_name in child.partialName(
                includeNonMandatoryIndices=True, useLongNames=True, includeInstancedIndices=True):
            return True

    return False


def iterate_children(plug):
    """
    Iterator function to iterate over all children plugs of the given plug (it should be an array or compound plug).

    :param MPlug plug: array/compound plug to iterate.
    :return: generator of iterated plugs.
    :rtype: iterator(OpenMaya.MPlug)
    """

    if plug.isArray:
        for plug_found in range(plug.evaluateNumElements()):
            child = plug.elementByPhysicalIndex(plug_found)
            yield child
            for leaf in iterate_children(child):
                yield leaf
    elif plug.isCompound:
        for plug_found in range(plug.numChildren()):
            child = plug.child(plug_found)
            yield child
            for leaf in iterate_children(child):
                yield leaf


def remove_element_plug(plug, element_number, mod=None, apply=False):
    """
    Removes an element plug.

    :param OpenMaya.MPlug plug: plug array object.
    :param int element_number: element number to delete.
    :param OpenMaya.DGModifier mod: modifier to dad to. If None, one will be created.
    :param bool apply: if True, then plugs value will be set immediately with the modifier, if False, then is
        user is responsible to call modifier.doIt() function.
    :return: Maya DGModifier used for the operation.
    :rtype: OpenMaya.MDGModifier
    """

    with set_locked_context(plug):
        mod = mod or OpenMaya.MDGModifier()
        if element_number in plug.getExistingArrayAttributeIndices():
            mod.removeMultiInstance(plug.elementByLogicalIndex(element_number), True)
        if apply:
            try:
                mod.doIt()
            except RuntimeError:
                logger.error('Failed to remove element: {} from plug: {}'.format(element_number, plug.name()))
                raise

    return mod


def enum_names(plug):
    """
    Returns the plug enumeration field names.

    :param OpenMaya.MPlug plug: plug to query enum field names of.
    :return: list of plug enumeration field names.
    :rtype: list(str)
    """

    plug_attr = plug.attribute()
    enum_field_names = list()
    if not plug_attr.hasFn(OpenMaya.MFn.kEnumAttribute):
        return enum_field_names
    attr = OpenMaya.MFnEnumAttribute(plug_attr)
    for i in range(attr.getMin(), attr.getMax() + 1):
        # enums can be a bit screwed, i.e 5 options but max 10
        try:
            enum_field_names.append(attr.fieldName(i))
        except:
            pass
    return enum_field_names


def enum_indices(plug):
    """
    Returns the plug enumeration indices as list.

    :param OpenMaya.MPlug plug: plug we want to query enum indices of.
    :return: list of plug enumeration indices.
    :rtype: list(int)
    """

    obj = plug.attribute()
    if obj.hasFn(OpenMaya.MFn.kEnumAttribute):
        attr = OpenMaya.MFnEnumAttribute(obj)
        return range(attr.getMax() + 1)


def serialize_plug(plug):
    """
    Function that converts given OpenMaya.MPlug into a serialized dictionary.

    :param om.Plug plug: plug to serialize.
    :return: serialized plug as a dictionary.
    :rtype: dict
    """

    dynamic = plug.isDynamic
    data = {'isDynamic': dynamic}
    attr_type = plug_type(plug)
    if not dynamic:

        # skip any default attribute that has not changed value.
        if plug.isDefaultValue():
            return dict()
        elif plug.isArray:
            return dict()
        elif plug.isCompound:
            data['children'] = [serialize_plug(plug.child(i)) for i in range(plug.numChildren())]

    elif attr_type != attributetypes.kMFnMessageAttribute:
        if plug.isCompound:
            if plug.isArray:
                element = plug.elementByLogicalIndex(0)
                data['children'] = [serialize_plug(element.child(i)) for i in range(element.numChildren())]
            else:
                data['children'] = [serialize_plug(plug.child(i)) for i in range(plug.numChildren())]
        elif plug.isArray:
            pass
        else:
            min_value = plug_min(plug)
            max_value = plug_max(plug)
            soft_min_value = soft_min(plug)
            soft_max_value = soft_max(plug)
            if min_value is not None:
                data['min'] = min_value
            if max_value is not None:
                data['max'] = max_value
            if soft_min_value is not None:
                data['softMin'] = soft_min_value
            if soft_max_value is not None:
                data['softMax'] = soft_max_value

    if plug.isChannelBox:
        data['channelBox'] = plug.isChannelBox
    if plug.isKeyable:
        data['keyable'] = plug.isKeyable
    if plug.isLocked:
        data['locked'] = plug.isLocked
    if plug.isArray:
        data['isArray'] = plug.isArray
    if plug.isElement:
        data['isElement'] = True
    if plug.isChild:
        data['isChild'] = True

    data.update({
        'name': plug.partialName(includeNonMandatoryIndices=True, useLongNames=True, includeInstancedIndices=True),
        'default': attributetypes.maya_type_to_python_type(plug_default(plug)),
        'type': attr_type,
        'value': python_type_from_plug_value(plug),
    })

    if plug_type(plug) == attributetypes.kMFnkEnumAttribute:
        data['enums'] = enum_names(plug)

    return data


def serialize_connection(plug):
    """
    Function that converts the destination OpenMaya.MPlug and serializes the connection as a dictionary.

    :param OpenMaya.MPlug plug: plug that is the destination of a connection.
    :return: serialized connection.
    """

    source = plug.source()
    source_path = ''
    if source:
        source_node = source.node()
        source_path = OpenMaya.MFnDagNode(source_node).fullPathName() if source_node.hasFn(
            OpenMaya.MFn.kDagNode) else OpenMaya.MFnDependencyNode(source_node).name()
    destination_node = plug.node()
    return {
        'sourcePlug': source.partialName(
            includeNonMandatoryIndices=True, useLongNames=True, includeInstancedIndices=True),
        'destinationPlug': plug.partialName(
            includeNonMandatoryIndices=True, useLongNames=True, includeInstancedIndices=True),
        'source': source_path,
        'destination': OpenMaya.MFnDagNode(destination_node).fullPathName() if destination_node.hasFn(
            OpenMaya.MFn.kDagNode) else OpenMaya.MFnDependencyNode(destination_node).name()
    }
