#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains functions related with OpenMaya attributes
"""

from __future__ import annotations

import re
from typing import Iterator

import maya.api.OpenMaya as OpenMaya

from tp.core import log
from tp.common.python import helpers
from tp.maya.om import dagpath

logger = log.tpLogger


def attr_mplug(attribute_name: str) -> OpenMaya.MPlug:
    """
    Returns the MPlug object for the given attribute.

    :param str attribute_name: the attribute to return the MPlug for
    :return: attribute plug.
    :rtype: OpenMaya.MPlug
    """

    attr_elem_list = attribute_name.split('.')
    attr_obj = dagpath.mobject(attr_elem_list[0])
    attr_obj_fn = OpenMaya.MFnDependencyNode(attr_obj)

    # get attribute element components (name, index)
    attr_elem = re.findall(r'\w+', attr_elem_list[1])

    # get MPlug to top level attribute
    attr_mplug = attr_obj_fn.findPlug(attr_elem[0], True)
    if len(attr_elem) == 2:
        attr_mplug = attr_mplug.elementByLogicalIndex(int(attr_elem[1]))

    # traverse to the lowest child attribute
    for i in range(2, len(attr_elem_list)):
        attr_elem = re.findall(r'\w+', attr_elem_list[i])
        for n in range(attr_mplug.numChildren()):
            child_plug = attr_mplug.child(n)
            logger.debug(f'Looking for "{attr_elem[0]}", found "{child_plug.partialName()}"')

    return attr_mplug


def connection_index(attribute_name: str, as_source: bool = True, connected_to: OpenMaya.MObject | None = None) -> int:
    """
    Return the index of the connection.

    :param str attribute_name: attribute we want to check connection index of.
    :param bool as_source: whether to check source connection.
    :param OpenMaya.MObject or None connected_to: optional node to check if found connected nodes are connected to it.
    :return: int
    :raises Exception: if no connections for given attribute found.
    """

    attr_plug = attr_mplug(attribute_name)

    # Get connected plugs.
    attr_plug_connections = OpenMaya.MPlugArray()
    connected = attr_plug.connectedTo(attr_plug_connections, not as_source, as_source)
    if not connected:
        connection_type = 'outgoinhg' if as_source else 'incoming'
        raise Exception('No {} connections found for attribute "{}"'.format(connection_type, attribute_name))

    # Get connected index
    for i in range(len(attr_plug_connections)):
        connected_plug = attr_plug_connections[i]
        connected_node = connected_plug.partialName(True, False, False, False, False).split('.')[0]
        if connected_to and not connected_to == connected_node:
            continue
        return connected_plug.logicalIndex()

    return -1


def connected_nodes(
        attribute_name: str, as_source: bool = True,
        connected_to: OpenMaya.MObject | None = None) -> list[OpenMaya.MObject]:
    """
    Returns a list of all connected nodes to given attribute.

    :param str attribute_name: attribute we want to check connection index of.
    :param bool as_source: whether to check source connection.
    :param OpenMaya.MObject or None connected_to: optional node to check if found connected nodes are connected to it.
    :return: list of connected nodes.
    :rtype: list[OpenMaya.MObject
    """

    connected_nodes: list[OpenMaya.MObject] = []

    attr_plug = attr_mplug(attribute_name)
    attr_plug_connections = OpenMaya.MPlugArray()
    connected = attr_plug.connectedTo(attr_plug_connections, not as_source, as_source)
    if not connected:
        return connected_nodes

    num_connections = len(attr_plug_connections)
    for i in range(num_connections):
        connected_plug = attr_plug_connections[i]
        connected_node = connected_plug.partialName(True, False, False, False, False)
        if connected_to and not connected_to == connected_node:
            continue
        connected_nodes.append(connected_node)

    return connected_nodes


def set_lock_state_on_attributes(mobj: OpenMaya.MObject, attribute_names: list[str], state: bool = True) -> bool:
    """
    Locks and unlocks the given attributes.

    :param OpenMaya.MObject mobj: node whose attributes we want to lock/unlock.
    :param list[str] attribute_names: list of attributes names to lock/unlock.
    :param bool state: whether to lock or unlock the attributes.
    :return: True if the attributes lock/unlock operation was successful; False otherwise.
    :rtype: bool
    """

    attributes = helpers.force_list(attribute_names)
    dep = OpenMaya.MFnDependencyNode(mobj)
    for attr in attributes:
        found_plug = dep.findPlug(attr, False)
        if found_plug.isLocked != state:
            found_plug.isLocked = state

    return True


def show_hidde_attributes(mobj: OpenMaya.MObject, attribute_names: list[str], state: bool = False) -> bool:
    """
    Shows or hides given attributes in the channel box.

    :param OpenMaya.MObject mobj: node whose attributes we want to show/hide.
    :param list[str] attribute_names: list of attributes names to lock/unlock
    :param bool state: whether to hide or show the attributes.
    :return: True if the attributes show/hide operation was successful; False otherwise.
    :rtype: bool
    """

    dep = OpenMaya.MFnDependencyNode(mobj)
    attributes = helpers.force_list(attribute_names)
    for attr in attributes:
        found_plug = dep.findPlug(attr, False)
        if found_plug.isChannelBox != state:
            found_plug.isChannelBox = state

    return True


def iterate_parents(attribute: OpenMaya.MObject) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields the parents from the given attribute.

    :param OpenMaya.MObject attribute: attribute to get parents of.
    :return: iterated parent attributes.
    :rtype: Iterator[OpenMaya.MObject]
    """

    fn_attribute = OpenMaya.MFnAttribute(attribute)
    current = fn_attribute.parent

    while not current.isNull():
        yield current
        fn_attribute.setObject(current)
        current = fn_attribute.parent


def iterate_children(attribute: OpenMaya.MObject) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields the children from the given attribute.

    :param OpenMaya.MObject attribute: attribute to get children of.
    :return: iterated children attributes.
    :rtype: Iterator[OpenMaya.MObject]
    """

    fn_attribute = OpenMaya.MFnCompoundAttribute(attribute)
    num_children = fn_attribute.numChildren()
    for i in range(num_children):
        yield fn_attribute.child(i)


def trace(attribute: OpenMaya.MObject) -> Iterator[OpenMaya.MObject]:
    """
    Returns a generator that yields all the attributes leading to the given attribute.

    :param OpenMaya.MObject attribute: attribute to get trace of.
    :return: all attributes leading to the given one.
    :rtype: Iterator[OpenMaya.MObject]
    """

    for parent in reversed(list(iterate_parents(attribute))):
        yield parent

    yield attribute
