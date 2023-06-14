import maya.cmds as cmds
import maya.api.OpenMaya as OpenMaya

from tp.core import dcc
from tp.core.abstract import scene
from tp.common.python import helpers
from tp.maya.cmds import helpers, name as name_utils, node as node_utils


class MayaScene(scene.AbstractScene):
    def __init__(self):
        super().__init__()

    def _objects(self, from_selection=False, wildcard='', object_type=None):
        """
        Internal function that returns a list of all the objects in the current scene wrapped inside a SceneObject
        :param from_selection: bool
        :param wildcard: str
        :param object_type: int
        :return: list(SceneObject)
        """

        maya_objects = list()

        for obj in self._dcc_objects(from_selection=from_selection, wildcard=wildcard, object_type=object_type):
            if obj.apiType() == OpenMaya.MFn.kWorld:
                continue
            maya_objects.append(dcc.SceneObject(self, obj))

        return maya_objects

    def _dcc_objects(self, from_selection=False, wildcard='', object_type=None):
        """
        Returns DCC objects from current scene
        :param from_selection: bool, Whether to return only selected DCC objects or all objects in the scene
        :param wildcard: str, filter objects by its name
        :param object_type: int
        :return: list(variant)
        """

        expression_regex = name_utils.wildcard_to_regex(wildcard)

        if from_selection:
            objects = helpers.selection_iterator()
        else:
            if helpers.is_string(object_type):
                objects = cmds.ls(type=object_type, long=True)
            else:
                maya_type = dcc.node_types().get(
                    object_type, (OpenMaya.MFn.kDagNode, OpenMaya.MFn.kCharacter))
                objects = list(helpers.objects_of_mtype_iterator(maya_type))

        if (object_type is not None and object_type != 0) or wildcard:
            objects_list = list()
            for obj in objects:
                if helpers.is_string(object_type):
                    type_check = True if not object_type else dcc.node_tpdcc_type(obj, as_string=True) == object_type
                else:
                    type_check = True if not object_type else dcc.node_tpdcc_type(obj) == object_type
                if wildcard:
                    obj_name = node_utils.get_name(mobj=obj, fullname=False)
                    wildcard_check = expression_regex.match(obj_name)
                else:
                    wildcard_check = False
                if type_check and wildcard_check:
                    if helpers.is_string(obj):
                        obj = node_utils.get_mobject(obj)
                    objects_list.append(obj)
            objects = objects_list

        return objects

    def _rename_dcc_objects(self, dcc_native_objects, names, display=True):
        """
        Rename given DCC objects with the given new names
        :param dcc_native_objects: variant or list(variant)
        :param names: list(str)
        :param display: bool, whether we want to rename internal dcc name or display name
        :return: bool, True if the operation is successful; False otherwise
        """

        return node_utils.set_names(dcc_native_objects, names)
