from __future__ import annotations

import logging
from uuid import uuid4
from typing import Any

import pymxs

from ..abstract import callback

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
# noinspection SpellCheckingInspection
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class FnCallback(callback.AFnCallback):
    """
    Overloads of AFnCallback function set class to handle behaviour for 3ds Max callbacks.
    """

    __slots__ = ()

    def unregister_callback(self, callback_id: Any):
        """
        Unregisters the given DCC callback ID.

        :param Any callback_id: ID of the callback to remove.
        """

        if pymxs.runtime.isKindOf(callback_id, pymxs.runtime.Name):
            logger.info(f'Removing callback: {callback_id}')
            pymxs.runtime.callbacks.removeScripts(id=callback_id)

    def add_pre_file_open_callback(self, func: callable):
        """
        Adds callback that is called before a new scene is opened.

        :param callable func: callback function.
        """

        callback_id = pymxs.runtime.Name(uuid4().hex)
        pymxs.runtime.callbacks.addScript(pymxs.runtime.Name('filePreOpen'), func, id=callback_id, persistent=False)
        self.register_callback(self.Callback.PreFileOpen, callback_id)

    def add_post_file_open_callback(self, func: callable):
        """
        Adds callback that is called after a new scene is opened.

        :param callable func: callback function.
        """

        callback_id = pymxs.runtime.Name(uuid4().hex)
        pymxs.runtime.callbacks.addScript(pymxs.runtime.Name('filePostOpen'), func, id=callback_id, persistent=False)
        self.register_callback(self.Callback.PostFileOpen, callback_id)

    def add_selection_changed_callback(self, func: callable):
        """
        Adds callback that is called when the active selection is changed.

        :param callable func: callback function.
        """

        callback_id = pymxs.runtime.nodeEventCallback(selectionChanged=func, subobjectSelectionChanged=func)
        self.register_callback(self.Callback.SelectionChanged, callback_id)

    def add_undo_callback(self, func: callable):
        """
        Adds callback that is called each time the user undoes a command.

        :param callable func: callback function.
        """

        callback_id = pymxs.runtime.Name(uuid4().hex)
        pymxs.runtime.callbacks.addScript(pymxs.runtime.Name('sceneUndo'), func, id=callback_id, persistent=False)
        self.register_callback(self.Callback.Undo, callback_id)

    def add_redo_callback(self, func: callable):
        """
        Adds callback that is called each time the user redoes a command.

        :param callable func: callback function.
        """

        callback_id = pymxs.runtime.Name(uuid4().hex)
        pymxs.runtime.callbacks.addScript(pymxs.runtime.Name('sceneRedo'), func, id=callback_id, persistent=False)
        self.register_callback(self.Callback.Redo, callback_id)

    def clear(self):
        """
        Removes all callbacks.
        """

        super().clear()

        pymxs.runtime.gc(light=True)
