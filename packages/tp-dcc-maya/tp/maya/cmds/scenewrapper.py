#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya scene wrapper class implementation
"""

import maya.cmds
import maya.api.OpenMaya

from tp.core import dcc
from tp.core.abstract import scenewrapper
from tp.maya.cmds import node as node_utils


class MayaSceneWrapper(scenewrapper.AbstractSceneWrapper, object):
    def __init__(self, scene, native_dcc_object):

        # NOTE: Instead of working with Maya MObjects (which in some scenarios such as long time, opening new
        # file ..., are automatically invalidated and Maya will crash if we try to use them because we are accessing
        # an invalid memory, we use MObjectHandles which does not suffer this problem.
        self._native_handle = None

        super(MayaSceneWrapper, self).__init__(scene=scene, native_dcc_object=native_dcc_object)

    # ==============================================================================================
    # PROPERTIES
    # ==============================================================================================

    @property
    def _dcc_native_object(self):
        return self._native_handle.object()

    @_dcc_native_object.setter
    def _dcc_native_object(self, dcc_object):
        if dcc_object is None:
            dcc_object = maya.api.OpenMaya.MObject()
        self._native_handle = maya.api.OpenMaya.MObjectHandle(dcc_object)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def name(self):
        """
        Returns the name of the DCC object in current DCC scene
        :return: str, current name of the DCC object
        """

        return node_utils.get_name(mobj=self._dcc_native_object, fullname=False)

    def display_name(self):
        """
        Returns the name of DCC object without special characters used by DCC.
        :return: str
        """

        return self.name().split(':')[-1]

    def set_display_name(self, new_name):
        """
        Sets the display name of the DCC object
        :param new_name: str, new display name
        """

        namespace = self.namespace()
        if namespace:
            return maya.cmds.rename(self.path(), ':'.join([self.namespace(), new_name]))
        else:
            return maya.cmds.rename(self.path(), new_name)

    def path(self):
        """
        Returns the full path of the DCC object in current DCC scene
        :return: str, current full path of the DCC object
        """

        return node_utils.get_name(mobj=self._dcc_native_object, fullname=True)

    def namespace(self):
        """
        Returns DCC object namespace
        :return: str
        """

        node_name = node_utils.get_name(self._dcc_native_object, fullname=False)
        split = node_name.split(':')[0]
        if len(split) > 1:
            return ':'.join(split[:-1])

        return ''

    def set_namespace(self, namespace):
        """
        Sets DCC object namespace
        :param namespace: str, new namespace for the DCC object
        """

        node_name = node_utils.get_name(self._dcc_native_object, fullname=False)
        display_name = node_name.split(':')[-1]
        if not namespace:
            maya.cmds.rename(self.path(), self.display_name())
        else:
            if not maya.cmds.namespace(exists=namespace):
                maya.cmds.namespace(add=namespace)
            maya.cmds.rename(self.path(), ':'.join([namespace, display_name]))

        return True

    def unique_id(self):
        """
        Returns the unique identifier of the wrapped native DCC object in current DCC scene
        :return: int or str
        """

        if dcc.version() >= 2016:
            node_name = node_utils.get_name(self._dcc_native_object, fullname=True)
            return maya.cmds.ls(node_name, uuid=True)[0]
        else:
            property_value = self._dcc_native_attribute('uuid', default=None)
            if property_value is None:
                return self._native_handle.hashCode()

    def set_unique_id(self, value):
        """
        Set the unique id for this wrapper instance
        The unique ID is generated automatically by Maya and cannot be modified
        :param value: object
        """

        return False

    def has_attribute(self, attribute_name):
        """
        Returns whether or not wrapped native DCC object has an attribute with the given name
        :param attribute_name: str, name of the attribute we are looking for
        :return: bool, True if the attribute exists in the wrapped native DCC object; False otherwise.
        """

        node_name = node_utils.get_name(self._dcc_native_object, fullname=True)
        return dcc.attribute_exists(node_name, attribute_name)

    def attribute_names(self, keyable=False, short_names=False, unlocked=True):
        """
        Returns a list of the attributes names linked to wrapped native DCC object
        :param keyable: bool, Whether or not list keyable attributes (animatable properties)
        :param short_names: bool, Whether or not to list attributes with their short name
        :param unlocked: bool, Whether or not list unlocked properties
        :return: list
        """

        node_name = node_utils.get_name(self._dcc_native_object, fullname=True)
        return dcc.list_attributes(node_name, keyable=keyable, unlocked=unlocked, shortNames=short_names)

    def _dcc_native_copy(self):
        """
        Internal function that returns a copy/duplicate of the wrapped DCC object
        :return: variant
        """

        node_name = node_utils.get_name(self._dcc_native_object, fullname=True)
        return dcc.duplicate_node(node_name)

    def _dcc_native_attribute(self, attribute_name, default=None):
        """
        Internal function that returns the value of the attribute of the wrapped DCC object
        :param attribute_name: str, name of the attribute we want retrieve value of
        :param default: variant, fallback default value if attribute does not exists in wrapped DCC object
        :return:
        """

        node_name = node_utils.get_name(self._dcc_native_object, fullname=True)
        try:
            return dcc.get_attribute_value(node_name, attribute_name)
        except Exception:
            return default

    def _set_dcc_native_attribute(self, attribute_name, value):
        """
        Sets the value of the property defined by the given attribute name
        :param attribute_name: str, name of the attribute we want to set the value of
        :param value: variant, new value of the attribute
        :return: bool, True if the operation was successful; False otherwise.
        """

        node_name = node_utils.get_name(self._dcc_native_object, fullname=True)

        return dcc.set_attribute_value(node_name, attribute_name, value)
