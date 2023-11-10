from __future__ import annotations

from typing import Callable

import maya.cmds as cmds

from tp.maya import api
from tp.common.python import decorators


class InvalidNodeError(Exception):
    def __init__(self):
        super().__init__(
            'An invalid object was selected. Scene Manager will not update until only valid objects are selected')


@decorators.add_metaclass(decorators.Singleton)
class SceneManager:
    """
    Manager that allows to register functions that will be executed when scene changes.
    """

    def __init__(self):

        self._scene_opened_id = -1
        self._selection_changed_id = -1
        self._scene_opened_enabled = True
        self._selection_changed_enabled = True
        self._update_methods = []                              # list[Callable]
        self._selection_change_methods = []                  # list[Callable]

        self.start_all_jobs()

    def enable_selection_changed(self):
        """
        Enables selectionChanged script job.
        """

        self._selection_changed_enabled = True

    def disable_selection_changed(self):
        """
        Disables selectionChanged script job.
        """

        self._selection_changed_enabled = False

    def start_all_jobs(self):
        """
        Starts a Maya scriptJob on 'SceneOpened' and on 'SelectionChanged' that will update and selection specific
        methods.
        """

        if self._scene_opened_id == -1:
            self._scene_opened_id = cmds.scriptJob(event=['SceneOpened', self._on_scene_updated])
        if self._selection_changed_id == -1:
            self._selection_changed_id = cmds.scriptJob(event=['SelectionChanged', self._on_selection_changed])

    def stop_all_jobs(self):
        """
        Stops and removes all scriptJobs.
        """

        cmds.scriptJob(kill=self._scene_opened_id, force=True)
        self._scene_opened_id = -1
        cmds.scriptJob(kill=self._selection_changed_id, force=True)
        self._selection_changed_id = -1

    def register_update_method(self, func: Callable):
        """
        Registers an update method, that will be called each time scene changes.

        :param Callable func: function to call.
        """

        if func not in self._update_methods:
            self._update_methods.append(func)

    def remove_method(self, func: Callable):
        """
        Removes method from scene manager.

        :param Callable func: method to remove.
        """

        update_methods_to_remove = []
        for update_method in self._update_methods:
            if update_method == func:
                update_methods_to_remove.append(update_method)
        for update_method_to_remove in update_methods_to_remove:
            self._update_methods.remove(update_method_to_remove)

        selection_change_methods_to_remove = []
        for selection_change_method in self._selection_change_methods:
            if selection_change_method == func:
                selection_change_methods_to_remove.append(selection_change_method)
        for selection_change_method_to_remove in selection_change_methods_to_remove:
            self._selection_change_methods.remove(selection_change_method_to_remove)

    def _on_scene_updated(self):
        """
        Internal callback function that runs all registered update methods.
        """

        if not self._scene_opened_enabled:
            return

        for func in self._update_methods:
            func()

    def _on_selection_changed(self):
        """
        Internal callback function that runs all registered update methods.
        """

        if not self._selection_changed_enabled:
            return

        try:
            selection_list = api.selected()
        except Exception:
            raise InvalidNodeError
        else:
            for func in self._selection_change_methods:
                func(selection_list)
