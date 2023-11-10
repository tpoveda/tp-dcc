from __future__ import annotations

import enum

from overrides import override

import maya.api.OpenMaya as OpenMaya

from tp.dcc.abstract import scene
from tp.maya.cmds import scene as cmds_scene


class FileExtensions(enum.IntEnum):
    """
    Enumerator that defines available file extensions for Maya
    """

    mb = 0
    ma = 1


class MayaScene(scene.AbstractScene):

    __slots__ = ()
    __extensions__ = FileExtensions

    @override
    def is_new_scene(self) -> bool:
        return cmds_scene.is_new_scene()

    @override
    def is_save_required(self) -> bool:
        return cmds_scene.current_scene_is_modified()

    @override(check_signature=False)
    def active_selection(self) -> list[OpenMaya.MObject]:
        selection = OpenMaya.MGlobal.getActiveSelectionList()       # type: OpenMaya.MSelectionList
        return [selection.getDependNode(i) for i in range(selection.length())]

    @override(check_signature=False)
    def set_active_selection(self, selection: list[OpenMaya.MObject], replace: bool = True):
        if not replace:
            selection.extend(self.active_selection())
