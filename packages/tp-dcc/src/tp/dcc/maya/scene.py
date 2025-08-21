from __future__ import annotations

from typing import Iterator

from maya.api import OpenMaya

from tp.libs.maya.om import dagutils
from tp.libs.maya.cmds import scene as sceneutils

from ..abstract.scene import AFnScene


class FnScene(AFnScene):
    """Overloads `AFnScene` exposing functions to handle Maya scenes."""

    def is_new_scene(self) -> bool:
        """Returns whether the current scene is new or not.

        :return: Whether the current scene is new or not.
        """

        return sceneutils.is_new_scene()

    def is_save_required(self) -> bool:
        """Returns whether the current scene requires saving or not.

        :return: Whether the current scene requires saving or not.
        """

        return sceneutils.is_save_required()

    def new(self):
        """Creates a new scene."""

        return sceneutils.new_scene()

    def save(self):
        """Saves any changes to the current scene file."""

        sceneutils.save_scene()

    def save_as(self, file_path: str):
        """Saves the current scene to the given file path.

        :param file_path: File path to save the current scene to.
        """

        sceneutils.save_scene_as(file_path)

    def iterate_nodes(self) -> Iterator[OpenMaya.MObject]:
        """Generator function that iterates over all nodes in the scene.

        :return: Iterator to iterate over all nodes in the scene.
        """

        return dagutils.iterate_nodes(api_type=OpenMaya.MFn.kDagNode)

    def active_selection(self) -> list[OpenMaya.MObject]:
        """Returns the current active scene selection.

        :return: list of selected nodes.
        """

        selection: OpenMaya.MSelectionList = OpenMaya.MGlobal.getActiveSelectionList()
        return [selection.getDependNode(i) for i in range(selection.length())]

    def set_active_selection(
        self, selection: list[OpenMaya.MObject], replace: bool = True
    ):
        """Updates current active scene selection with given nodes.

        :param selection: nodes to set as the active selection.
        :param replace: Whether to replace current selection or not.
        """

        if not replace:
            selection.extend(self.active_selection())

        selection_list = dagutils.create_selection_list(selection)
        OpenMaya.MGlobal.setActiveSelectionList(selection_list)

    def clear_active_selection(self):
        """Clears current active scene selection."""

        OpenMaya.MGlobal.clearSelectionList()
