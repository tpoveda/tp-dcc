#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains abstract definition of basic DCC scene wrappers
"""

from tp.core import dcc
from tp.core.abstract import scene as abstract_scene
from tp.common.python import decorators


class AbstractSceneWrapper(object):
    def __init__(self, scene, native_pointer=None):
        super(AbstractSceneWrapper, self).__init__()

        self._scene = scene
        self._native_pointer = native_pointer

    def __eq__(self, other):
        if isinstance(other, AbstractSceneWrapper):
            return other._native_pointer == self._native_pointer

        return False

    def __hash__(self):
        """
        Returns unique id of the object, if unique_id() is not implemented, this function will return 0
        :return:
        """

        return self.unique_id()

    def __call__(self, ret_type=None):
        """
        Returns native pointer wrapped by this object
        If you specify a ret_type, depending on the DCC, you will return a different pointer
        :param ret_type: str
        :return: object
        """

        return self._native_pointer

    def __str__(self):
        return '<{} ({})>'.format(
            super(AbstractSceneWrapper, self).__str__().split()[0].split('.')[-1], self.display_name())

    @decorators.abstractmethod
    def name(self):
        """
        Returns the name of the scene wrapped node instance
        :return: str
        """

        raise NotImplementedError('abstract function name() not implemented!')

    @decorators.abstractmethod
    def display_name(self):
        """
        Returns the display name for this wrapped node instance.
        :return: str
        """

        raise NotImplementedError('abstract function display_name() not implemented!')


class _MetaScene(type):
    def __call__(self, *args, **kwargs):
        if dcc.is_maya():
            from tp.maya.cmds import scene as maya_scene
            return type.__call__(maya_scene.MayaScene, *args, **kwargs)
        else:
            return type.__call__(abstract_scene.AbstractScene, *args, **kwargs)


@decorators.add_metaclass(_MetaScene)
class Scene(abstract_scene.AbstractScene):
    pass
