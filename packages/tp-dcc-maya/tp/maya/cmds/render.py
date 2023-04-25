#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions and classes related with render in Maya
"""

from tp.core import log, dcc
from tp.common.python import decorators

logger = log.tpLogger


@decorators.add_metaclass(decorators.Singleton)
class RenderGlobals(object):
    def __init__(self):
        render_globals_node = get_render_globals_node_name()
        self._attrs_dict = dict()
        all_attrs = dcc.list_attributes(render_globals_node)
        for attr in all_attrs:
            self._attrs_dict[attr] = dcc.attribute_default_value(render_globals_node, attr)

    def __getattr__(self, item):
        if item in self._attrs_dict:
            return get_render_globals_attribute(item, default_value=self._attrs_dict[item])

    def __setattr__(self, attr, value):
        object.__setattr__(self, attr, value)

        if attr in self._attrs_dict:
            if value is None:
                value = self._attrs_dict[attr]
            set_render_globals_attribute(attr, value)


@decorators.add_metaclass(decorators.Singleton)
class DefafultResolution(object):
    def __init__(self):
        default_resolution_node = get_default_resolution_node_name()
        self._attrs_dict = dict()
        all_attrs = dcc.list_attributes(default_resolution_node)
        for attr in all_attrs:
            self._attrs_dict[attr] = dcc.attribute_default_value(default_resolution_node, attr)

    def __getattr__(self, item):
        if item in self._attrs_dict:
            return get_default_resolution_attribute(item, default_value=self._attrs_dict[item])

    def __setattr__(self, attr, value):
        object.__setattr__(self, attr, value)

        if attr in self._attrs_dict:
            if value is None:
                value = self._attrs_dict[attr]
            set_default_resolution_attribute(attr, value)


def get_render_globals_node_name():
    """
    Returns the name of the render globals Maya node
    :return: str
    """

    return 'defaultRenderGlobals'


def get_default_resolution_node_name():
    """
    Returns the name of the default resolution Maya node
    :return: str
    """

    return 'defaultResolution'


def get_render_globals_attribute(attribute_name, default_value=None):
    """
    Internal function that returns value of the given attribute of the render global Maya node
    :param attribute_name: str, name of the attribute to get
    :param default_value: object, value that is returned if the attribute does not exists
    :return: object
    """

    render_globals_node = get_render_globals_node_name()
    if not dcc.attribute_exists(render_globals_node, attribute_name):
        logger.warning(
            'Attribute "{}" does not exists in RenderGlobals node "{}"!'.format(attribute_name, render_globals_node))
        return default_value

    return dcc.get_attribute_value(render_globals_node, attribute_name)


def set_render_globals_attribute(attribute_name, attribute_value):
    """
    Internal function that returns value of the given attribute of the render global Maya node
    :param attribute_name: str, name of the attribute to get
    :param attribute_value: object, value used to set attribute to
    :return: object
    """

    render_globals_node = get_render_globals_node_name()
    if not dcc.attribute_exists(render_globals_node, attribute_name):
        logger.warning(
            'Attribute "{}" does not exists in RenderGlobasls node "{}"!'.format(attribute_name, render_globals_node))
        return False

    try:
        return dcc.set_attribute_value(render_globals_node, attribute_name, attribute_value)
    except Exception as exc:
        logger.error(
            'Was impossible to set attribute "{}" in RenderGlobals node "{}" with value "{}" | "{}"'.format(
                attribute_name, render_globals_node, attribute_value, exc))
        return False


def get_default_resolution_attribute(attribute_name, default_value=None):
    """
    Internal function that returns value of the given attribute of the default resolution Maya node
    :param attribute_name: str, name of the attribute to get
    :param default_value: object, value that is returned if the attribute does not exists
    :return: object
    """

    default_resolution_node = get_default_resolution_node_name()
    if not dcc.attribute_exists(default_resolution_node, attribute_name):
        logger.warning(
            'Attribute "{}" does not exists in DefaultResolution node "{}"!'.format(
                attribute_name, default_resolution_node))
        return default_value

    return dcc.get_attribute_value(default_resolution_node, attribute_name)


def set_default_resolution_attribute(attribute_name, attribute_value):
    """
    Internal function that returns value of the given attribute of the render global Maya node
    :param attribute_name: str, name of the attribute to get
    :param attribute_value: object, value used to set attribute to
    :return: object
    """

    default_resolution_node = get_default_resolution_node_name()
    if not dcc.attribute_exists(default_resolution_node, attribute_name):
        logger.warning(
            'Attribute "{}" does not exists in DefafultResolution node "{}"!'.format(
                attribute_name, default_resolution_node))
        return False

    try:
        return dcc.set_attribute_value(default_resolution_node, attribute_name, attribute_value)
    except Exception as exc:
        logger.error(
            'Was impossible to set attribute "{}" in DefafultResolution node "{}" with value "{}" | "{}"'.format(
                attribute_name, default_resolution_node, attribute_value, exc))
        return False


def get_default_resolution_size_units():
    """
    Returns list with all default resolution size units
    NOTE: The order is VERY important, is the same order that there is in Maya Render Settings
    :return: list(str)
    """

    return ['pixels', 'inches', 'cm', 'mm', 'points', 'picas']


def get_default_resolution_units():
    """
    Returns list with all default resolutions units
    NOTE: The order is VERY important, is the same order that there is in Maya Render Settings
    :return: list(str)
    """

    return ['pixels/inch', 'pixels/cm']
