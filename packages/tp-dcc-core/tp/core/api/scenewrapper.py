#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base scene wrapper class implementation
"""

from tp.core import dcc
from tp.core.abstract import scenewrapper as abstract_scenewrapper
from tp.common.python import decorators


class _MetaSceneWrapper(type):
    def __call__(self, *args, **kwargs):
        if dcc.is_maya():
            from tp.maya.cmds import scenewrapper as maya_scenewrapper
            return maya_scenewrapper.MayaSceneWrapper
        else:
            return abstract_scenewrapper.AbstractSceneWrapper


@decorators.add_metaclass(_MetaSceneWrapper)
class SceneWrapper(abstract_scenewrapper.AbstractSceneWrapper):
    pass
