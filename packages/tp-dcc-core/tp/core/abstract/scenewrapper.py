#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC scene wrapper abstract class implementation
"""

from tp.core import consts
from tp.common.python import decorators


class AbstractSceneWrapper(object):
    def __init__(self, scene, native_dcc_object):
        super(AbstractSceneWrapper, self).__init__()

        self._scene = scene
        self._dcc_native_object = native_dcc_object

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def __eq__(self, other):
        if isinstance(other, AbstractSceneWrapper):
            return other._dcc_native_object == self._dcc_native_object

        return False

    def __hash__(self):
        """
        Returns unique hash value for the current wrapped DCC object
        NOTE: If current DCC implementation does not supports unique ID, all objects will have a hash of 0
        :return: str
        """

        return self.unique_id()

    def __call__(self, return_type=consts.WrapperTypes.Pointer):
        """
        Returns the wrapped native DCC object of this object.
        Depending of DCC you can return different objects by giving a specific wrapper type
        :param return_type: consts.WrapperTypes, to request a specific wrapped object type
        :return: variant, wrapped native DCC object
        """

        return self._dcc_native_object

    def __str__(self):
        return '<%s (%s)>' % (
        super(AbstractSceneWrapper, self).__str__().split()[0].split('.')[-1], self.display_name())

    # ==============================================================================================
    # ABSTRACT FUNCTIONS
    # ==============================================================================================

    @decorators.abstractmethod
    def name(self):
        """
        Returns the name of the DCC object in current DCC scene
        :return: str, current name of the DCC object
        """

        raise NotImplementedError('Abstract Scene Wrapper name function not implemented!')

    @decorators.abstractmethod
    def display_name(self):
        """
        Returns the name of DCC object without special characters used by DCC.
        :return: str
        """

        raise NotImplementedError('Abstract Scene Wrapper display_name function not implemented!')

    @decorators.abstractmethod
    def set_display_name(self, new_name):
        """
        Sets the display name of the DCC object
        :param new_name: str, new display name
        """

        raise NotImplementedError('Abstract Scene Wrapper set_display_name function not implemented!')

    @decorators.abstractmethod
    def path(self):
        """
        Returns the full path of the DCC object in current DCC scene
        :return: str, current full path of the DCC object
        """

        raise NotImplementedError('Abstract Scene Wrapper path function not implemented!')

    @decorators.abstractmethod
    def namespace(self):
        """
        Returns DCC object namespace
        :return: str
        """

        raise NotImplementedError('Abstract Scene Wrapper namespace function not implemented!')

    @decorators.abstractmethod
    def set_namespace(self, namespace):
        """
        Sets DCC object namespace
        :param namespace: str, new namespace for the DCC object
        """

        raise NotImplementedError('Abstract Scene Wrapper set_namespace function not implemented!')

    @decorators.abstractmethod
    def unique_id(self):
        """
        Returns the unique identifier of the wrapped native DCC object in current DCC scene
        :return: int or str
        """

        raise NotImplementedError('Abstract Scene Wrapper unique_id function not implemented!')

    @decorators.abstractmethod
    def set_unique_id(self, value):
        """
        Set the unique id for this wrapper instance
        :param value: object
        :return:
        """

        raise NotImplementedError('Abstract Scene Wrapper set_unique_id function not implemented!')

    @decorators.abstractmethod
    def has_attribute(self, attribute_name):
        """
        Returns whether or not wrapped native DCC object has an attribute with the given name
        :param attribute_name: str, name of the attribute we are looking for
        :return: bool, True if the attribute exists in the wrapped native DCC object; False otherwise.
        """

        raise NotImplementedError('Abstract Scene Wrapper has_attribute function not implemented!')

    @decorators.abstractmethod
    def attribute_names(self, keyable=False, short_names=False, unlocked=True):
        """
        Returns a list of the attributes names linked to wrapped native DCC object
        :param keyable: bool, Whether or not list keyable attributes (animatable properties)
        :param short_names: bool, Whether or not to list attributes with their short name
        :param unlocked: bool, Whether or not list unlocked properties
        :return: list
        """

        raise NotImplementedError('Abstract Scene Wrapper attribute_names function not implemented!')

    @decorators.abstractmethod
    def _dcc_native_copy(self):
        """
        Internal function that returns a copy/duplicate of the wrapped DCC object
        :return: variant
        """

        raise NotImplementedError('Abstract Scene Wrapper _dcc_native_copy function not implemented!')

    @decorators.abstractmethod
    def _dcc_native_attribute(self, attribute_name, default=None):
        """
        Internal function that returns the value of the attribute of the wrapped DCC object
        :param attribute_name: str, name of the attribute we want retrieve value of
        :param default: variant, fallback default value if attribute does not exists in wrapped DCC object
        :return: variant
        """

        raise NotImplementedError('Abstract Scene Wrapper _dcc_native_attribute function not implemented!')

    @decorators.abstractmethod
    def _set_dcc_native_attribute(self, attribute_name, value):
        """
        Sets the value of the property defined by the given attribute name
        :param attribute_name: str, name of the attribute we want to set the value of
        :param value: variant, new value of the attribute
        :return: bool, True if the operation was successful; False otherwise.
        """

        raise NotImplementedError('Abstract Scene Wrapper _set_dcc_native_attribute function not implemented!')

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def scene(self):
        """
        Returns the DCC scene instance this object belongs to
        :return: Scene
        """

        return self._scene

    def dcc_native_object(self):
        """
        Returns the DCC native object being wrapped
        :return: variant
        """

        return self._dcc_native_object

    def copy(self):
        """
        Creates a copy of the wrapped DCC object in the current scene
        :return: SceneWrapper or None
        """

        dcc_native_copy = self._dcc_native_copy()
        if not dcc_native_copy:
            return None

        return self.__class__(self._scene, dcc_native_copy)

    def attribute(self, attribute_name, default=None):
        """
        Returns the value of the given property name
        :param attribute_name: str, name of the attribute we want retrieve value of
        :param default: variant, fallback default value if attribute does not exists in wrapped DCC object
        :return:
        """

        pass

    def set_attribute(self, attribute_name, value):
        """
        Sets the value of the given property
        :param attribute_name: str, name of the property we want set the value of
        :param value: variant, new value for the property
        """

        pass
