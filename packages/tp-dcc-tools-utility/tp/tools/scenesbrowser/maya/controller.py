from __future__ import annotations

import os
import typing
from typing import List

from overrides import override

import maya.cmds as cmds

from tp.core import log
from tp.preferences.interfaces import assets
from tp.common.python import strings, path
from tp.common.qt import api as qt
from tp.maya.cmds import decorators, scene, workspace
from tp.tools.scenesbrowser import controller
from tp.tools.scenesbrowser.widgets import thumbsbrowser

if typing.TYPE_CHECKING:
    from tp.preferences.assets import BrowserPreference
    from tp.preferences.preference import PreferenceInterface

logger = log.tpLogger


class MayaScenesBrowserController(controller.ScenesBrowserController):

    @override
    def scene_prefs(self) -> PreferenceInterface | None:
        if not self._scene_prefs:
            self._scene_prefs = assets.maya_scenes_interface()

        return self._scene_prefs

    @override(check_signature=False)
    def browser_model(
            self, view: thumbsbrowser.ThumbsBrowser, directories: List[path.DirectoryPath] | None = None,
            uniform_icons: bool = False, browser_preferences: BrowserPreference | None = None) -> thumbsbrowser.MayaFileModel:
        return thumbsbrowser.MayaFileModel(
            view=view, directories=directories, uniform_icons=uniform_icons, browser_preferences=browser_preferences)

    @decorators.undo
    @override
    def load_scene(self):

        file_path = self.file_path()
        if not file_path:
            return

        dialog_result = scene.scene_modified_dialogue()
        if dialog_result == 'cancel':
            return

        if workspace.switch_workspace(self._selected_item.file_path) == 'cancel':
            return

        cmds.file(self._selected_item.file_path, force=True, options='v=0', ignoreVersion=True, open=True)

    @override
    def save_scene(self, directory: str, file_type: str = ''):
        """
        Saves scene within given directory and with the given file type.

        :param str directory: directory where current active scene will be saved into.
        :param str file_type: file type to save with.
        """

        file_type = file_type or 'mayaAscii'
        forced_type = self._forced_type()
        if forced_type:
            file_type = forced_type
            logger.warning(f'Unknown node/plugins found. Forcing save type: {forced_type}')

        file_name = self._prepare_save(directory, file_type)
        if not file_name:
            return

        cmds.file(rename=file_name)
        cmds.file(save=True, type=file_type)
        logger.info(f'File saved successfully: "{file_name}"!')

    def _forced_type(self) -> str | None:
        """
        Internal function that checks where there are unknown nodes within scene and returns the correct file type
        to save/export with.

        :return: type to save file with.
        :rtype: str or None
        """

        if scene.has_unknown_nodes() or scene.has_unknown_plugins():
            return scene.scene_file_type()

    def _prepare_save(self, directory: str, file_type: str = 'mayaAscii') -> str | None:

        name = self.scene_name_input()
        if not name:
            logger.info('File saved cancelled')
            return None

        file_extension = 'ma' if file_type == 'mayaAscii' else 'mb'
        folder_name = self._prepare_folder(directory, name)
        name = strings.file_safe_name(name)
        folder_full_path = path.join_path(directory, folder_name)
        file_name = path.join_path(folder_full_path, os.path.extsep.join([name, file_extension]))
        if path.exists(file_name):
            unique_name = strings.trailing_number_tuple(folder_full_path)
            choice, _ = qt.show_multi_choice(
                title='Existing file found', message='File already exists. Override?',
                choices=['Override.', f'Rename to {path.basename(unique_name)}'], button_b='Cancel')
            if choice == 0:
                pass
            elif choice == 1:
                new_name = unique_name
                file_name = path.normalize_path(
                    path.join_path(folder_full_path, os.path.extsep.join([new_name, file_extension])))
            else:
                return None

        return file_name
