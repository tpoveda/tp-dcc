#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC scene object abstract class implementation
"""

from tp.core import consts, dcc
from tp.core.api import scenewrapper
from tp.core.abstract import scenewrapper as abstract_scenewrapper
from tp.common.python import helpers


class AbstractSceneObject(abstract_scenewrapper.AbstractSceneWrapper, object):

    _object_type = consts.ObjectTypes.Generic
    _sub_classes = dict()

    def __init__(self, scene, native_dcc_object):
        super(AbstractSceneObject, self).__init__(scene=scene, native_dcc_object=native_dcc_object)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def __new__(cls, scene, native_dcc_object, *args, **kwargs):
        if not cls._sub_classes:
            for sub_class in helpers.itersubclasses(cls):
                if not sub_class._object_type == consts.ObjectTypes.Generic:
                    cls._sub_classes[sub_class._object_type] = sub_class

        scene_object_type = dcc.node_tpdcc_type(native_dcc_object)

        if scene_object_type in cls._sub_classes:
            sub_class = cls._sub_classes[scene_object_type]
            return scenewrapper.SceneWrapper.__new__(sub_class)

        return scenewrapper.SceneWrapper.__new__(cls)

    # ==============================================================================================
    # BASE
    # ==============================================================================================

    def is_root(self):
        """
        Returns whether or not the current wrapped DCC node is the scene root node
        :return: bool
        """

        return dcc.node_is_root(self._dcc_native_object)

    def is_deleted(self):
        """
        Returns whether or not the current wrapped DCC node is being deleted from current scene
        :return: bool
        """

        return not dcc.node_exists(self._dcc_native_object)

    def is_selected(self):
        """
        Returns whether or not the current wrapped DCC node is selected or not
        :return: bool
        """

        return dcc.node_is_selected(self._dcc_native_object)

    def is_box_mode(self):
        """
        Returns whether or not the current wrapped DCC node is being displayed in box mode
        :return: bool
        """

        return dcc.node_is_box_mode(self._dcc_native_object)

    def is_hidden(self):
        """
        Returns whether or not the current wrapped DCC node is hidden or not
        :return: bool
        """

        return dcc.node_is_hidden(self._dcc_native_object)
