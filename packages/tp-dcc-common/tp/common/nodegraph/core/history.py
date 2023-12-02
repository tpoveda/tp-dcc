from __future__ import annotations

import typing
from itertools import islice
from collections import deque

from tp.core import log
from tp.common.qt import api as qt
from tp.preferences.interfaces import noddle
from tp.common.nodegraph.core import serializer

if typing.TYPE_CHECKING:
    from tp.common.nodegraph.core.graph import NodeGraph

logger = log.rigLogger


class SceneHistory:

    SCENE_INIT_DESCRIPTION = 'SceneInit'

    class Signals(qt.QObject):
        changed = qt.Signal()
        stepChanged = qt.Signal(int)

    def __init__(self, graph: NodeGraph):
        super().__init__()

        self._graph = graph
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
                'nodes': [node.uuid for node in self._graph.selected_nodes],
                'edges': [edge.uuid for edge in self._graph.selected_edges]
            }
            return {
                'desc': description,
                'snapshot': serializer.serialize_graph(self._graph),
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
            logger.debug(f'> {description}')
        else:
            set_modified = False

        if set_modified:
            self._graph.has_been_modified = True

        self._signals.changed.emit()
        self._signals.stepChanged.emit(self._current_step)

    def set_current_step(self, value: int):
        """
        Sets current active step.

        :param int value: current step index.
        """

        if value > len(self._stack) - 1:
            logger.error(f'Out of bounds step: {value}')
            return

        logger.debug(f'New step {value}, current step {self._current_step}')
        if self._current_step < value:
            while self._current_step < value:
                self.redo()
        elif self._current_step > value:
            while self._current_step > value:
                self.undo()

    def undo(self):
        """
        Undoes last history step.
        """

        if not self._enabled:
            logger.warning('History is disabled')
            return

        if self._current_step > 0:
            logger.info(f'> Undo {self._stack[self._current_step]["desc"]}')
            self._current_step -= 1
            self.restore_history()

            print(self._graph.model.nodes)

            self.signals.stepChanged.emit(self._current_step)
        else:
            logger.warning('No more steps to undo')

    def redo(self):
        """
        Redoes previous history step.
        """

        if not self._enabled:
            logger.warning('History is disabled')
            return

        if self._current_step + 1 < len(self._stack):
            self._current_step += 1
            self.restore_history()
            self.signals.stepChanged.emit(self._current_step)
        else:
            logger.warning('No more steps to redo')

    def restore_history(self):
        """
        Restores history based on current step.
        """

        self._enabled = False
        try:
            self._restore_stamp(self._stack[self._current_step])
            self._graph.has_been_modified = True
        finally:
            self._enabled = True

    def clear(self):
        """
        Clears history.
        """

        self._stack.clear()
        self._current_step = -1

    def _restore_stamp(self, stamp: dict):
        """
        Restores given scene stamp.

        :param dict stamp: scene stamp to restore.
        """

        try:
            serializer.deserialize_graph(self._graph, stamp['snapshot'])
            self._graph.graphics_scene.clearSelection()
            for edge_uid in stamp['selection']['edges']:
                for edge in self._graph.edges:
                    if edge.uuid == edge_uid:
                        edge.graphics_edge.setSelected(True)
                        break
            for node_uid in stamp['selection']['nodes']:
                for node in self._graph.nodes:
                    if node.uuid == node_uid:
                        node.view.setSelected(True)
                    break
        except Exception:
            logger.exception('Restore history stamp exception.')
            raise
