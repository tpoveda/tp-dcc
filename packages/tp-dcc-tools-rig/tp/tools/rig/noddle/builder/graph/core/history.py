from __future__ import annotations

import typing
from itertools import islice
from collections import deque

from tp.core import log
from tp.common.qt import api as qt
from tp.preferences.interfaces import noddle

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.graph.core.scene import Scene

logger = log.rigLogger


class SceneHistory:

    SCENE_INIT_DESCRIPTION = 'SceneInit'

    class Signals(qt.QObject):
        changed = qt.Signal()
        stepChanged = qt.Signal(int)

    def __init__(self, scene: Scene):
        super().__init__()

        self._scene = scene
        self._prefs = noddle.noddle_interface()
        self._signals = SceneHistory.Signals()
        self._enabled = self._prefs.builder_history_enabled()
        self._size = self._prefs.builder_history_size()
        self._stack = deque(maxlen=self._size)
        self._current_step = -1

    def __len__(self) -> int:
        return len(self._stack)

    @property
    def signals(self) -> Signals:
        return self._signals

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value: int):
        self._size = value
        self._stack = deque(self._stack, maxlen=value)

    @property
    def stack(self) -> deque:
        return self._stack

    @property
    def current_step(self) -> int:
        return self._current_step

    def store_history(self, description: str, set_modified: bool = True):
        """
        Stores new state within history stack.

        :param str description: change description.
        :param bool set_modified: whether to mark scene as modified.
        """

        def _create_stamp():
            selection = {
                'nodes': [node.uid for node in self._scene.selected_nodes],
                'edges': [edge.uid for edge in self._scene.selected_edges]
            }
            return {
                'desc': description,
                'snapshot': self._scene.serialize(),
                'selection': selection
            }

        if not self._enabled:
            return

        # If the pointer (current_step) is not at the end of stack
        if self._current_step + 1 < len(self._stack):
            self._stack = deque(islice(self._stack, self._current_step + 1))

        hs = _create_stamp()
        self._stack.append(hs)

        if not self._stack.maxlen or self._current_step + 1 < self._stack.maxlen:
            self._current_step += 1

        if description != SceneHistory.SCENE_INIT_DESCRIPTION:
            logger.info(f'> {description}')
        else:
            set_modified = False

        if set_modified:
            self._scene.has_been_modified = True

        self._signals.changed.emit()
        self._signals.stepChanged.emit(self._current_step)

    def clear(self):
        """
        Clears history.
        """

        self._stack.clear()
        self._current_step = -1
