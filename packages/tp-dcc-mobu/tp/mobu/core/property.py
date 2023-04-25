#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with MotionBuilder properties
"""

import re

import pyfbsdk

from tp.core import log

logger = log.tpLogger

PROPERTY_TYPES = dict(
    Action = [pyfbsdk.FBPropertyType.kFBPT_Action, 'Action'],
    Enum = [pyfbsdk.FBPropertyType.kFBPT_enum, 'Enum'],
    Integer = [pyfbsdk.FBPropertyType.kFBPT_int,'Integer'],
    Bool = [pyfbsdk.FBPropertyType.kFBPT_bool,'Bool'],
    Double = [pyfbsdk.FBPropertyType.kFBPT_double,'Number'],
    CharPtr = [pyfbsdk.FBPropertyType.kFBPT_charptr, 'String'],
    Float = [pyfbsdk.FBPropertyType.kFBPT_float,'Float'],
    Time = [pyfbsdk.FBPropertyType.kFBPT_Time, 'Time'],
    Object = [pyfbsdk.FBPropertyType.kFBPT_object, 'Object'],
    StringList = [pyfbsdk.FBPropertyType.kFBPT_stringlist, 'StringList'],
    Vector4D = [pyfbsdk.FBPropertyType.kFBPT_Vector4D, 'Vector'],
    Vector3D = [pyfbsdk.FBPropertyType.kFBPT_Vector3D, 'Vector'],
    Vector2D = [pyfbsdk.FBPropertyType.kFBPT_Vector2D, 'Vector'],
    ColorRGB = [pyfbsdk.FBPropertyType.kFBPT_ColorRGB, 'Color'],
    ColorRGBA = [pyfbsdk.FBPropertyType.kFBPT_ColorRGBA, 'ColorAndAlpha'],
    TimeSpan = [pyfbsdk.FBPropertyType.kFBPT_TimeSpan, 'Time'])


def list_properties(node, pattern=None, property_type=None, **kwargs):

    def _passes_optional_test(x):
        for arg, challenge in kwargs.items():
            fn = getattr(x, arg, None)
            if fn and fn() != challenge:
                return False
        return True

    def _passes_name_test(x, _pattern):
        if _pattern:
            if '*' in _pattern:
                _pattern = _pattern.replace('*', '.*')
                return re.match(pattern, x.GetName())
            else:
                return _pattern == x.GetName()
        return True

    def _passes_type_test(x, _property_type):
        if _property_type and _property_type in PROPERTY_TYPES:
            prop_type = PROPERTY_TYPES[_property_type][0]
            return x.GetPropertyType() == prop_type
        return True

    properties = list()
    for prop in node.PropertyList:
        if prop is None:
            continue
        if not _passes_optional_test(prop):
            continue
        if not _passes_type_test(prop, property_type):
            continue
        if not _passes_name_test(prop, pattern):
            continue
        properties.append(prop)

    return properties


def get_property(node, property_name, raise_exception=False):

    prop = node.PropertyList.Find(property_name) or None
    if prop is None and raise_exception:
        raise Exception('Could not find property name "{}" for object "{}"'.format(property_name, node.Name))

    return prop


def get_property_value(node, property_name):
    """
    Returns a property value from the given node
    :param node:
    :param property_name: str
    :return: object
    """

    prop = get_property(node, property_name)
    if prop is None:
        return None

    return prop.Data


def set_property_value(node, property_name, property_value):
    """
    Sets a property value of the given node
    :param node:
    :param property_name: str
    :param property_value: object
    """

    prop = get_property(node, property_name)
    if prop is None:
        return None

    prop.Data = property_value


def add_property(node, property_name, property_type, animatable=True, user=True, raise_exception=False):
    """
    Adds a new property to the given node
    :param node:
    :param property_name: str, name of the property to add
    :param property_type: str, data type of the property
    :param animatable: bool
    :param user:
    :param raise_exception: bool
    :return: bool
    :return:
    """

    if list_properties(node, pattern=property_name):
        exc_msg = 'Could not add property "{}". Already exists on object "{}"'.format(property_name, node)
        if raise_exception:
            raise Exception(exc_msg)
        else:
            logger.warning(exc_msg)
            return False

    try:
        type_data = PROPERTY_TYPES[property_type]
    except KeyError:
        exc_msg = 'Invalid property type "{}". Valid types are: "{}"'.format(
            property_type, ', '.join(list(PROPERTY_TYPES.keys())))
        if raise_exception:
            raise Exception(exc_msg)
        else:
            logger.warning(exc_msg)
            return False

    type_data.extend([animatable, user, None])

    node.PropertyCreate(property_name, *type_data)

    return True


def remove_property(node, property_name, raise_exception=False):
    """
    Removes property with given name from given node
    :param node:
    :param property_name: str
    :param raise_exception: bool
    :return: bool
    """

    prop = get_property(node, property_name)
    if prop is None:
        return False

    if prop.IsUserProperty():
        node.PropertyRemove(prop)
    else:
        exc_msg = 'Property is flagged as non-user. Unable to remove property "{}" from object "{}"'.format(
            property_name, node.Name)
        if raise_exception:
            raise Exception(exc_msg)
        else:
            logger.warning(exc_msg)
            return False

    return True
