#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains DCC scene object base class implementation
"""

from tp.core import dcc
from tp.core.abstract import sceneobject
from tp.common.python import decorators


class _MetaSceneObject(type):
    def __call__(self, *args, **kwargs):
        if dcc.is_maya():
            from tp.maya.cmds import sceneobject as maya_sceneobject
            return type.__call__(maya_sceneobject.MayaSceneObject, *args, **kwargs)
        else:
            return type.__call__(sceneobject.AbstractSceneObject, *args, **kwargs)


@decorators.add_metaclass(_MetaSceneObject)
class SceneObject(sceneobject.AbstractSceneObject):
    pass
