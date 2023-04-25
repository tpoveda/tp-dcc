#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains Maya scene object class implementation
"""

import maya.api.OpenMaya

from tp.core.abstract import sceneobject
from tp.maya.cmds import scenewrapper, node as node_utils, shape as shape_utils


class MayaSceneObject(sceneobject.AbstractSceneObject, scenewrapper.MayaSceneWrapper):
    def __init__(self, scene, native_dcc_object):

        # We make sure that we store native Maya object as an OpenMaya.MObject
        # Also we store transform and shape information of the wrapped object
        mobj = node_utils.get_mobject(native_dcc_object)
        if mobj.apiType() == maya.api.OpenMaya.MFn.kWorld:
            native_dcc_object = mobj
            self._maya_shape = None
        else:
            native_dcc_object = shape_utils.get_transform(native_dcc_object)
            self._maya_shape = node_utils.shape(native_dcc_object)

        super(MayaSceneObject, self).__init__(scene, native_dcc_object)

    # ==============================================================================================
    # OVERRIDES
    # ==============================================================================================

    def _type_of_dcc_scene_object_as_string(self):
        """
         Returns the type of the stored native DCC object as a string
         :return: str
         """

        pass
