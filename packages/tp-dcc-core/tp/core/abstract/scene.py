#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC scene abstract class implementation
"""

from tp.core import dcc, sceneobject
from tp.common.python import helpers, decorators


class AbstractScene(object):

    # ==============================================================================================
    # ABSTRACT FUNCTIONS
    # ==============================================================================================

    @decorators.abstractmethod
    def _dcc_objects(self, from_selection=False, wildcard='', object_type=None):
        """
        Internal function that returns DCC objects from current scene
        :param from_selection: bool, Whether to return only selected DCC objects or all objects in the scene
        :param wildcard: str, filter objects by its name
        :param object_type: int
        :return: list(variant)
        """

        raise NotImplementedError('Abstract Scene _dcc_objects function not implemented!')

    @decorators.abstractmethod
    def _rename_dcc_objects(self, dcc_native_objects, names, display=True):
        """
        Rename given DCC objects with the given new names
        :param dcc_native_objects: variant or list(variant)
        :param names: list(str)
        :param display: bool, Whether or not we want to rename internal dcc name or display name
        :return: bool, True if the operation is successful; False otherwise
        """

        raise NotImplementedError('Abstract Scene _remove_dcc_objects function not implemented!')

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def objects(self, wildcard='', object_type=None):
        """
        Returns a list of scene objects as SceneObjects
        :param wildcard: str, filter objects by its name
        :param object_type:
        :return: list(SceneObject)
        """

        return [sceneobject.SceneObject(self, obj) for obj in self._dcc_objects(
            from_selection=False, wildcard=wildcard, object_type=object_type)]

    def selected_objects(self, wildcard='', object_type=None):
        """
        Returns a list of selected objects in current scene as SceneObjects
        :param wildcard: str, filter objects by its name
        :param object_type: int
        :return: list(SceneObject)
        """

        return [sceneobject.SceneObject(self, obj) for obj in self._dcc_objects(
            from_selection=True, wildcard=wildcard, object_type=object_type)]

    def root_object(self):
        """
        Returns the DCC root object of the scene as SceneObject
        :return: SceneObject or None
        """

        dcc_root = self._dcc_root_object()
        if not dcc_root:
            return None

        return dcc.SceneObject(self, dcc_root)

    def remove_objects(self, objects):
        """
        Removes the given objects from the this scene
        :param objects: list(SceneObject)
        :return: bool, True if the operation was successful; False otherwise
        """

        objects = helpers.force_list(objects)
        return self._remove_dcc_objects([obj.dcc_native_object() for obj in objects if not obj.is_deleted()])

    def rename_objects(self, objects, names, display=True):
        """
        Rename given objects with the given new names
        :param objects: SceneObject or list(SceneObject)
        :param names: list(str)
        :param display: bool, Whether or not we want to rename internal dcc name or display name
        :return: bool, True if the operation is successful; False otherwise
        """

        objects = helpers.force_list(objects)
        names = helpers.force_list(names)

        if len(objects) != len(names):
            return False

        return self._rename_dcc_objects(
            [obj.dcc_native_object() for obj in objects if not obj.is_deleted()], names, display=display)

    def find_object_by_name(self, name):
        """
        Looks for an individual node for its name
        :param name: str, name of the object to find
        :return: SceneObject or None
        """

        dcc_object = self._find_dcc_object_by_name(name)
        if not dcc_object:
            return None

        return sceneobject.SceneObject(self, dcc_object)

    def find_object_by_id(self, unique_id):
        """
        Looks for an individual node for its name
        :param unique_id: unique identifier of the object to find in current scene
        :return: SceneObject or None
        """

        dcc_object = self._find_dcc_object_by_id(unique_id)
        if not dcc_object:
            return None

        return sceneobject.SceneObject(self, dcc_object)

    # ==============================================================================================
    # INTERNAL
    # ==============================================================================================

    def _dcc_root_object(self):
        """
        Internal function that returns DCC root object from current scene
        :return: variant
        """

        return dcc.root_node()

    def _remove_dcc_objects(self, dcc_native_objects):
        """
        Internal function that removes given DCC objects from current scene
        :param dcc_native_objects: variant or list(variant)
        :return: bool, True if the operation is successful; False otherwise
        """

        return dcc.delete_node(dcc_native_objects)

    def _find_dcc_object_by_name(self, name):
        """
        Internal function that returns a valid a DCC object by its name
        :param name: str
        :return: variant
        """

        return dcc.find_node_by_name(name)

    def _find_dcc_object_by_id(self, unique_id):
        """
        Internal function that returns a valid DCC object its ID
        :param unique_id: str
        :return: variant
        """

        return dcc.find_node_by_id(unique_id)
