#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with Maya MPlugs
"""

from __future__ import annotations

import re
import copy
import contextlib
from collections import deque
from typing import Iterator, Any

import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.core import log
from tp.common.python import helpers
from tp.maya.om import dagpath, attributes, undo
from tp.maya.api import attributetypes

logger = log.tpLogger

__plug_parser__ = re.compile(r'([a-zA-Z0-9_]+)(?:\[([0-9]+)\])?')


@contextlib.contextmanager
def set_locked_context(plug: OpenMaya.MPlug):
    """
    Context manager to set the plug lock state to False then reset back to its original lock state.

    :param OpenMaya.MPlug plug: lock to work with.
    """

    current = plug.isLocked
    if current:
        plug.isLocked = False
    yield
    plug.isLocked = current


def api_type(obj: OpenMaya.MObject | OpenMaya.MPlug) -> int:
    """
    Returns the attribute type from the given plug.

    :param OpenMaya.MObject or OpenMaya.MPlug obj: object or plug to get attribute type of.
    :return: attribute type.
    :rtype: int
    """

    if isinstance(obj, OpenMaya.MObject):
        return obj.apiType()
    elif isinstance(obj, OpenMaya.MPlug):
        return obj.attribute().apiType()

    return OpenMaya.MFn.kUnknown


def as_mplug(attr_name: str) -> OpenMaya.MPlug:
    """
    Returns the MPlug instance of the given name.

    :param str attr_name: name of the Maya node to convert to MPlug
    :return: plug with given name.
    :rtype: OpenMaya.MPlug
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


def numeric_value(
        plug: OpenMaya.MPlug,
        ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal) -> tuple[int | None, bool | int | float]:
    """
    Returns the numeric value of the given plug.

    :param OpenMaya.MPlug plug: plug to get numeric value of.
    :param OpenMaya.MDGContext ctx: context to use.
    :return: tuple containing the plug type and its numeric value.
    :rtype: tuple[int, bool or int or float]
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


def typed_value(plug: OpenMaya.MPlug, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal) -> tuple[int | None, Any]:
    """
    Returns Maya type from the given plug.

    :param OpenMaya.MPlug plug: plug instance to get type of.
    :param OpenMaya.MDGContext ctx: context to use.
    :return: tuple containing the plug type and its typed value.
    :rtype: tuple[int or None, Any]
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


def plug_value_and_type(
        plug: OpenMaya.MPlug, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal) -> tuple[int | None, Any]:
    """
    Returns the value and the type of the given plug.

    :param OpenMaya.MPlug plug: plug to get value and type of.
    :param OpenMaya.MDGContext ctx: context to use.
    :return: plug value and its data type (if possible Python default types).
    :rtype: tuple[int | None, Any]
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


def plug_type(plug: OpenMaya.MPlug) -> int | None:
    """
    Returns the type of the give plug.

    :param OpenMaya.MPlug plug: plug to get type of.
    :return: plug type.
    :rtype: int or None
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


def python_type_from_plug_value(
        plug: OpenMaya.MPlug, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal) -> type | None | tuple | list:
    """
    Returns the Python for the given plug value.

    :param OpenMaya.MPlug plug: Plug to get python type from its value.
    :param OpenMaya.MDGContext ctx: optional context.
    :return: Python type.
    :rtype: type or None or tuple or list
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


def find_plug(node: OpenMaya.MObject, path: str) -> OpenMaya.MPlug:
    """
    Returns the plug derived from the given path relative to the given node.
    Unliked OpenMaya API method derived from MFnDependencyNode this function supports both, indices and children.
    Also accepts partial paths in that a parent attribute can be omitted and still resolved.

    :param OpenMaya.MObject node: node to get plug from.
    :param str path: plug path relative to node.
    :return: found plug instance.
    :rtype: OpenMaya.MPlug
    :raises TypeError: if attribute name does not exist within node.
    """

    node = dagpath.mobject(node)
    groups = __plug_parser__.findall(path)
    num_groups = len(groups)
    if num_groups == 0:
        raise TypeError('findPlug() unable to split path: "%s"!' % path)

    # Evaluate if attribute exists
    fn_depend_node = OpenMaya.MFnDependencyNode(node)
    node_name = fn_depend_node.name()
    attribute_name = groups[-1][0]
    attribute = fn_depend_node.attribute(attribute_name)
    if attribute.isNull():
        raise TypeError(f'findPlug() cannot find "{node_name}.{attribute_name}" attribute!')

    # Trace plug path
    found_attributes = list(attributes.trace(attribute))
    indices = {attribute: int(index) for (attribute, index) in groups if not helpers.is_null_or_empty(index)}

    fn_attribute = OpenMaya.MFnAttribute()
    plug = None
    for (i, attribute) in enumerate(found_attributes):
        # Get next child plug
        if i == 0:
            plug = OpenMaya.MPlug(node, attribute)
        else:
            plug = plug.child(attribute)
        # Check if plug was indexed and make sure to check both the short and long names!
        fn_attribute.setObject(attribute)
        index = indices.get(fn_attribute.name, indices.get(fn_attribute.shortName, None))
        if index is not None:
            plug = plug.elementByLogicalIndex(index)
        else:
            continue

    return plug


def find_plug_index(plug: OpenMaya.MPlug, logical: bool = True) -> int | None:
    """
    Returns the index of the given plug.

    :param OpenMaya.MPlug plug: plug to get index of.
    :param bool logical: whether to check logical index or element index.
    :return: plug index.
    :rtype: int or None
    """

    if plug.isNull:
        return

    if plug.isArray and plug.isElement:
        return plug.logicalIndex() if logical else list(iterate_elements(plug.parent())).index(plug)
    elif plug.isChild:
        return list(iterate_children(plug.parent())).index(plug)
    else:
        return list(attributes.iterate_top_level_attributes(plug.node())).index(plug.attribute())


def plug_value(plug: OpenMaya.MPlug, ctx: OpenMaya.MDGContext = OpenMaya.MDGContext.kNormal) -> Any:
    """
    Returns value of the given plug.

    :param OpenMaya.MPlug plug: plug to get value of.
    :param OpenMaya.MDGContext ctx: context to use.
    :return: plug value.
    :rtype: Any
    """

    return plug_value_and_type(plug, ctx=ctx)[1]


def set_plug_value(
        plug: OpenMaya.MPlug, value: Any,
        mod: OpenMaya.MDGModifier | None = None, apply: bool = True) -> OpenMaya.MDGModifier:
    """
    Sets the given lugs value to the given passed value.

    :param OpenMaya.MPlug plug: plug to set value of.
    :param Any value: value to set.
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


def connect_plugs(
        source: OpenMaya.MPlug, target: OpenMaya.MPlug, mod: OpenMaya.MDGModifier | None = None,
        force: bool = True, apply: bool = True) -> OpenMaya.MDGModifier:
    """
    Connects given plugs together.

    :param OpenMaya.MPlug source: plug to connect.
    :param OpenMaya.MPlug target: target plag to connect into.
    :param OpenMaya.MDGModifier or None mod: optional Maya modifier to apply.
    :param bool force: whether to force the connection.
    :param bool apply: whether to apply the modifier instantly or leave it to the caller.
    :return: modifier used to connect plugs.
    :rtype: OpenMaya.MDGModifier
    :raises TypeError: if one of the given plugs is not valid.

    """

    if not isinstance(source, OpenMaya.MPlug) or not isinstance(target, OpenMaya.MPlug):
        raise TypeError('connect_plugs() expects 2 plugs!')
    if source.isNull or target.isNull:
        raise TypeError('connect_plugs() expects 2 valid plugs!')

    if target.isDestination:
        target_source = target.source()
        if not target_source.isNull:
            if force:
                break_connections(target, source=True, destination=False)
                # modifier.disconnect(target_source, target)
            else:
                raise ValueError(f'connect_plugs() {target.info} plug has an incoming connection!')

    modifier = mod or OpenMaya.MDGModifier()
    logger.debug(f'Connecting "{source.info}" > "{target.info}"')
    modifier.connect(source, target)

    if mod is None and apply:
        undo.commit(modifier.doIt, modifier.undoIt)
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


def disconnect_plug(
        plug: OpenMaya.MPlug, source: bool = True, destination: bool = True,
        modifier: OpenMaya.MDGModifier | None = None) -> tuple[bool, OpenMaya.MDGModifier]:
    """
    Disconnects the plug connections, if "source" is True and the plug is a destination then disconnect the source
    from this plug. If destination is True and plug is a source the disconnect this plug from the destination.
    Plugs are also locked (to avoid Maya raises an error).

    :param OpenMaya.MPlug plug: plug to disconnect.
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


def disconnect_plugs(source: OpenMaya.MPlug, destination: OpenMaya.MPlug, modifier: OpenMaya.MDGModifier | None = None):
    """
    Disconnects two plugs using a DG modifier.

    :param OpenMaya.MPlug source: source plug to disconnect.
    :param OpenMaya.MPlug destination: destination plug to disconnect.
    :param OpenMaya.MDGModifier or None modifier: optional modifier to use to disconnect plugs.
    :raises TypeError: if one of the given plugs is not valid.
    """

    if not isinstance(source, OpenMaya.MPlug) or not isinstance(destination, OpenMaya.MPlug):
        raise TypeError('disconnect_plugs() expects 2 plugs!')
    if source.isNull or destination.isNull:
        raise TypeError('disconnect_plugs() expects 2 valid plugs!')

    # Check if disconnection is legal.
    other_plug = destination.source()
    if other_plug != source or other_plug.isNull:
        logger.debug(f'{source.info} is not connected to {destination.info}!')
        return

    modifier = modifier or OpenMaya.MDGModifier()
    modifier.disconnect(source, destination)
    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()


def break_connections(
        plug: OpenMaya.MPlug, source: bool = True, destination: bool = True, recursive: bool = False,
        modifier: OpenMaya.MDGModifier | None = None):
    """
    Breaks the connections to the given plug.

    :param OpenMaya.MPlug plug: plug to break connections of.
    :param bool source: if True, disconnect from the connected source plug if it has one.
    :param bool destination: if True, disconnect from the connected destination plug if it has one.
    :param bool recursive: whether to break connections in a recursive way.
    :param OpenMaya.MDGModifier or None modifier: optional modifier to use to break plug connections.
    """

    modifier = modifier or OpenMaya.MDGModifier()

    # Check if the source plug should be broken.
    other_plug = plug.source()
    if source and not other_plug.isNull:
        modifier.disconnect(other_plug, plug)

    # Check if the destination plugs should be broken
    other_plugs = plug.destinations()
    if destination and len(other_plugs) > 0:
        for other_plug in other_plugs:
            modifier.disconnect(plug, other_plug)

    # Check if children should be broken as well
    if recursive:
        for child_plug in walk(plug):
            # Check if the source plug and destination plugs should be broken
            other_plug = child_plug.source()
            if source and not other_plug.isNull:
                modifier.disconnect(other_plug, child_plug)
            other_plugs = child_plug.destinations()
            if destination and len(other_plugs) > 0:
                for other_plug in other_plugs:
                    modifier.disconnect(child_plug, other_plug)

    undo.commit(modifier.doIt, modifier.undoIt)
    modifier.doIt()


def iterate_top_level_plugs(node: OpenMaya.MObject, **kwargs) -> Iterator[OpenMaya.MPlug]:
    """
    Returns a generator that yields top-level plugs from the given node.

    :param OpenMaya.MObject node: object to get top level plugs from.
    :key bool readable: whether to retrieve readable plugs.
    :key bool writable: whether to retrieve writable plugs.
    :key bool keyable: whether to retrieve keyable plugs.
    :key bool affect_world_space: whether to retrieve world space related plugs.
    :key bool skip_user_attributes: whether to skip user created plugs.
    :return: iterated top-level plugs from the given node.
    :rtype: Iterator[OpenMaya.MPlug]
    """

    fn_attribute = OpenMaya.MFnAttribute()
    readable = kwargs.get('readable', False)
    writable = kwargs.get('writable', False)
    keyable = kwargs.get('keyable', False)
    affects_world_space = kwargs.get('affect_world_space', False)
    skip_user_attributes = kwargs.get('skip_user_attributes', False)

    for attribute in attributes.iterate_top_level_attributes(node):
        fn_attribute.setObject(attribute)
        if readable and not fn_attribute.readable:
            continue
        if writable and not fn_attribute.writable:
            continue
        if keyable and not fn_attribute.keyable:
            continue
        if affects_world_space and not fn_attribute.affectsWorldSpace:
            continue
        if skip_user_attributes and fn_attribute.dynamic:
            continue
        yield OpenMaya.MPlug(node, attribute)


def iterate_channel_box_plugs(node: OpenMaya.MPlug, **kwargs) -> Iterator[OpenMaya.MPlug]:
    """
    Returns a generator that yields plugs that are in the channel-box.

    :param OpenMaya.MObject node: object to get channel-box plugs from.
    :key bool readable: whether to retrieve readable plugs.
    :key bool writable: whether to retrieve writable plugs.
    :key bool keyable: whether to retrieve keyable plugs.
    :key bool non_default: whether to retrieve plugs that has no default value.
    :key bool affect_world_space: whether to retrieve world space related plugs.
    :key bool skip_user_attributes: whether to skip user created plugs.
    :return: iterated top-level plugs from the given node.
    :rtype: Iterator[OpenMaya.MPlug]
    """

    for plug in iterate_top_level_plugs(node, **kwargs):
        if plug.isCompound and not plug.isArray:
            yield from iterate_children(plug, keyable=True, channelBox=True)
        elif (plug.isKeyable or plug.isChannelBox) and is_numeric(plug):
            yield plug


def iterate_elements(plug: OpenMaya.MPlug, **kwargs) -> Iterator[OpenMaya.MPlug]:
    """
    Returns a generator that yields all elements from the given plug.

    :param OpenMaya.MPlug plug: plug to iterate elements from.
    :key bool writable: whether to retrieve writable plugs.
    :key bool non_default: whether to retrieve plugs that has no default value.
    :return: iterated element plugs from the given plug.
    ..warning:: This generator only works on array plugs and not elements!
    """

    if not plug.isArray or plug.isElement:
        return iter([])

    # Iterate through plug elements.
    writable = kwargs.get('writable', False)
    non_default = kwargs.get('non_default', False)
    indices = plug.getExistingArrayAttributeIndices()
    for physical_index, logical_index in enumerate(indices):
        element = plug.elementByPhysicalIndex(physical_index)
        if writable and not (element.isFreeToChange() == OpenMaya.MPlug.kFreeToChange):
            continue
        if non_default and element.isDefaultValue:
            continue
        yield element


def iterate_children(plug: OpenMaya.MPlug, recursive: bool = False, **kwargs) -> Iterator[OpenMaya.MPlug]:
    """
    Recursive function that returns a generator that yields the children plugs from the given plug.

    :param OpenMaya.MPlug plug: plug to iterate children plugs from.
    :param bool recursive: whether to return children recursively.
    :key bool readable: whether to retrieve readable plugs.
    :key bool writable: whether to retrieve writable plugs.
    :key bool keyable: whether to retrieve keyable plugs.
    :key bool non_default: whether to retrieve plugs that has no default value.
    :key bool channel_box: whether to retrieve plugs that are in channel-box.
    :return: iterated children plugs from the given plug.
    :rtype: Iterator[OpenMaya.MPlug]
    """

    writable = kwargs.get('writable', False)
    non_default = kwargs.get('non_default', False)
    keyable = kwargs.get('keyable', False)
    channel_box = kwargs.get('channel_box', False)

    if plug.isArray:
        # num_children = plug.numChildren()
        # for i in range(num_children):
        #     child = plug.child(i)
        #     if writable and not (child.isFreeToChange() == om.MPlug.kFreeToChange):
        #         continue
        #     if non_default and child.isDefaultValue:
        #         continue
        #     if keyable and not child.isKeyable:
        #         continue
        #     if channel_box and (not child.isChannelBox and not child.isKeyable):
        #         continue
        #     yield child
        for plug_found in range(plug.evaluateNumElements()):
            child = plug.elementByPhysicalIndex(plug_found)     # type: OpenMaya.MPlug
            if writable and not (child.isFreeToChange() == OpenMaya.MPlug.kFreeToChange):
                continue
            if non_default and child.isDefaultValue():
                continue
            if keyable and not child.isKeyable:
                continue
            if channel_box and (not child.isChannelBox and not child.isKeyable):
                continue
            yield child
            for leaf in iterate_children(child, recursive=recursive, **kwargs):
                yield leaf
    elif plug.isCompound:
        for plug_found in range(plug.numChildren()):
            child = plug.child(plug_found)                      # type: OpenMaya.MPlug
            if writable and not (child.isFreeToChange() == OpenMaya.MPlug.kFreeToChange):
                continue
            if non_default and child.isDefaultValue():
                continue
            if keyable and not child.isKeyable:
                continue
            if channel_box and (not child.isChannelBox and not child.isKeyable):
                continue
            yield child
            if recursive:
                for leaf in iterate_children(child, recursive=recursive, **kwargs):
                    yield leaf


def walk(
        plug: OpenMaya.MPlug, writable: bool = False, channel_box: bool = False,
        keyable: bool = False) -> Iterator[OpenMaya.MPlug]:
    """
    Returns a generator that yields descendants from the given plug.

    :param OpenMaya.MPlug plug: plug to iterate descendants plugs from.
    :param bool writable: whether to retrieve writable plugs.
    :param bool channel_box: whether to retrieve plugs that are in channel-box.
    :param bool keyable: whether to retrieve keyable plugs.
    :return: iterated descendants plugs from the given plug.
    :rtype: Iterator[OpenMaya.MPlug]
    """

    elements = list(iterate_elements(plug, writable=writable))
    children = list(iterate_children(plug, writable=writable, channel_box=channel_box, keyable=keyable))

    queue = deque(elements + children)
    while len(queue):
        plug = queue.popleft()
        yield plug
        if plug.isArray and not plug.isElement:
            queue.extend(list(iterate_elements(plug, writable=writable)))
        elif plug.isCompound:
            queue.extend(list(iterate_children(plug, writable=writable, channel_box=channel_box, keyable=keyable)))


def remove_multi_instances(plug: OpenMaya.MPlug, indices: list[int]):
    """
    Removes the indexed elements from the given plug.

    :param OpenMaya.MPlug plug: plug to remove indexed elements of.
    :param list[int] indices: list of element indexes to remove.
    ..warning:: This method expects the plug to be an array and not an element!
    """

    plug_name = plug.partialName(includeNodeName=True, useFullAttributePath=True, useLongNames=True)
    for index in indices:
        element_name = f'{plug_name}[{index}]'
        logger.info(f'Removing {element_name} element...')
        cmds.removeMultiInstance(element_name)


def connected_nodes(
        plug: OpenMaya.MPlug, include_null_objects: bool = False) -> OpenMaya.MObject | OpenMaya.MObjectArray:
    """
    Returns the nodes connected to the given plug.

    :param OpenMaya.MPlug plug: plug to get connected nodes of.
    :param bool include_null_objects: whether to skip null objects.
    :return: list of connected nodes.
    :rtype: OpenMaya.MObject or OpenMaya.MObjectArray
    ..warning:: If the plug is an array or compound then a list of nodes is returned instead!
    """

    nodes = OpenMaya.MObjectArray()
    if plug.isArray and not plug.isElement:
        # Iterate through plug elements
        for element in iterate_elements(plug):
            nodes += connected_nodes(element, include_null_objects=include_null_objects)
    elif plug.isCompound:
        # Iterate through plug children.
        for child in iterate_children(plug):
            nodes += connected_nodes(child, include_null_objects=include_null_objects)
    else:
        # Get source plug.
        other_plug = plug.source()
        if not other_plug.isNull:
            nodes.append(other_plug.node())
        elif include_null_objects:
            nodes.append(OpenMaya.MObject.kNullObj)

    return nodes


def find_connected_message(
        depend_node: OpenMaya.MObject,
        attribute: OpenMaya.MObject = OpenMaya.MObject.kNullObj) -> OpenMaya.MPlug | None:
    """
    Locates the connected destination plug for the given dependency node.

    :param OpenMaya.MObject depend_node: dependency node to get connected message node of.
    :param OpenMaya.MObject attribute: attribute to get connected message of.
    :return: found connected message plug.
    :rtype: OpenMaya.MPlug or None
    """

    fn_depdend_node = OpenMaya.MFnDependencyNode(depend_node)
    plug = fn_depdend_node.findPlug('message', True)
    destinations = plug.destinations()
    destination_count = len(destinations)
    attribute_supplied = not attribute.isNull()
    if destination_count == 0:
        return None
    elif destination_count == 1:
        destination = destinations[0]
        if attribute_supplied:
            return destination if (destination.attribute() == attribute) else None
        else:
            return destination
    elif attribute_supplied:
        for destination in destinations:
            if destination.attribute() == attribute:
                return destination
        return None

    return None


def next_available_element(plug: str | OpenMaya.MPlug) -> int | None:
    """
    Finds the next available plug element a value can be set to.
    If there are no gaps then the last element will be returned.

    :param str or OpenMaya.MPlug plug: plug to get next available element for.
    :return: next available element plug.
    :rtype: int or None
    """

    if not plug.isArray:
        return None

    indices = plug.getExistingArrayAttributeIndices()
    num_indices = len(indices)
    for physical_index, logical_index in enumerate(indices):
        # Check if physical index does not match logical index
        if physical_index != logical_index:
            return physical_index

    return indices[-1] + 1 if num_indices > 0 else 0


def next_available_element_plug(array_plug: OpenMaya.MPlug) -> OpenMaya.MPlug | None:
    """
    Returns the next available element plug from the plug array.
    Loops through all current elements looking for an out connection, if one does not exist then this element plug is
    returned. If the plug array is a compound one then the children of immediate children of the compound are searched
    and the element parent plug will be returned if there is a connection.

    :param OpenMaya.MPlug array_plug: plug array to search.
    :return: next plug.
    :rtype: OpenMaya.MPlug or None
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


def next_available_connection(
        plug: str | OpenMaya.MPlug, child_attribute: OpenMaya.MObject = OpenMaya.MObject.kNullObj) -> int | None:
    """
    Finds the next available plug element a connection can be made to.
    If there are no gaps then the last element will be returned.

    :param str or OpenMaya.MPlug plug: plug to get next available connection of.
    :param OpenMaya.MObject child_attribute: optional attribute if the element to test is nested.
    :return: next available plug element a connection can be made to.
    :rtype: int | None
    """

    if not plug.isArray:
        return None

    indices = plug.getExistingArrayAttributeIndices()
    num_indices = len(indices)
    for physical_index, logical_index in enumerate(indices):
        # Check if physical index matched logical index.
        element = plug.elementByLogicalIndex(logical_index)
        if not child_attribute.isNull():
            element = element.child(child_attribute)

        # Check if physical index does not match logical index.
        # Otherwise, check if element is connected.
        if physical_index != logical_index:
            return physical_index
        elif not element.isConnected:
            return logical_index

    return indices[-1] + 1 if num_indices > 0 else 0


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


def set_compound_as_proxy(compound_plug, source_plug):
    """
    Sets given compound as a proxy to the source plug by turning all chld plugs to proxy, since Maya does not
    support doing this at the compound level. After that we do the connection to the matching children.

    :param OpenMaya.MPlug compound_plug: compound plug to set as proxy.
    :param OpenMaya.MPlug source_plug: source plug.
    """

    for child_index in range(compound_plug.numChildren()):
        child_plug = compound_plug.child(child_index)
        child_attr = child_plug.attribute()
        plug_fn(child_attr)(child_attr).isProxyAttribute = True
        connect_plugs(source_plug.child(child_index), child_plug)


def is_constrained(plug: OpenMaya.MPlug) -> bool:
    """
    Returns whether given plug is constrained.

    :param OpenMaya.MPlug plug: plug to check.
    :return: True if given plug is constrained; False otherwise.
    :rtype: bool
    """

    if not plug.isDestination:
        return False

    node = plug.source().node()
    return any(map(node.hasFn, (OpenMaya.MFn.kConstraint, OpenMaya.MFn.kPluginConstraintNode)))


def is_animated(plug: OpenMaya.MPlug) -> bool:
    """
    Returns whether given plug is animated.

    :param OpenMaya.MPlug plug: plug to check.
    :return: True if given plug is animated; False otherwise.
    :rtype: bool
    """

    if not plug.isKeyable or plug.isDestination:
        return False

    # Evaluate connected node.
    fn_node = OpenMaya.MFnDependencyNode(plug.source().node())
    classification = fn_node.classification(fn_node.typeName)

    return classification == 'animation' and not is_constrained(plug)  # Constraints are classified under `animation`


def is_animatable(plug: OpenMaya.MPlug) -> bool:
    """
    Returns whether given plug is animatable.

    :param OpenMaya.MPlug plug: plug to check.
    :return: True if given plug is animatable; False otherwise.
    :rtype: bool
    """

    if not (plug.isKeyable or plug.isDestination):
        return False

    # Evaluate connections. If connected, make sure source node accepts keyframe data!
    if plug.isDestination:
        return is_animated(plug)

    return True


def is_numeric(plug: OpenMaya.MPlug) -> bool:
    """
    Returns whether given plug represents a numeric value.

    :param OpenMaya.MPlug plug: plug to check.
    :return: True if given plug is a numerical plug; False otherwise.
    :rtype: bool
    """

    return any(
        map(plug.attribute().hasFn, (
            OpenMaya.MFn.kNumericAttribute, OpenMaya.MFn.kUnitAttribute, OpenMaya.MFn.kEnumAttribute)))


def is_compound_numeric(plug: OpenMaya.MPlug) -> bool:
    """
    Returns whether given plug represents a compound numeric value.

    :param OpenMaya.MPlug plug: plug to check.
    :return: True if given plug is a compound numerical plug; False otherwise.
    :rtype: bool
    """

    return all([is_numeric(child) for child in iterate_children(plug, recursive=False)]) if plug.isCompound else False


def is_string(plug: OpenMaya.MPlug) -> bool:
    """
    Returns whether given plug represents a string value.

    :param OpenMaya.MPlug plug: plug to check.
    :return: True if given plug is a string plug; False otherwise.
    :rtype: bool
    """

    attribute = plug.attribute()
    if attribute.hasFn(OpenMaya.MFn.kTypedAttribute):
        return OpenMaya.MFnTypedAttribute(attribute).attrType() == OpenMaya.MFnData.kString

    return False


