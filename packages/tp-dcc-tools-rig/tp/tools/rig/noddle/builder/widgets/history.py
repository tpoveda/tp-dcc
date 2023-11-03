from __future__ import annotations

import typing

from tp.core import log
from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.window import NoddleBuilderWindow
    from tp.tools.rig.noddle.builder.graph.core.history import SceneHistory

logger = log.rigLogger


class SceneHistoryWidget(qt.QListWidget):
    def __init__(self, main_window: NoddleBuilderWindow, parent: qt.QWidget | None = None):
        super().__init__(parent=parent or main_window)

        self._main_window = main_window
        self._tracked_history: SceneHistory | None = None

    def update_history_connection(self):

        self.clear()
        current_editor = self._main_window.current_editor
        if not current_editor:
            self._tracked_history = None
            return

        self._tracked_history = current_editor.scene.history
        self._tracked_history.signals.changed.connect(self._update_view)
        self._tracked_history.signals.stepChanged.connect(self._update_current_step)

        self._update_view()
        self._update_current_step(self._tracked_history.current_step)
        logger.debug(f'Tracking history: {self._tracked_history}')

    def _update_view(self):
        """
        Updates scene history view based on tracked history.
        """

        self.clear()
        for stamp in self._tracked_history.stack:
            list_item = qt.QListWidgetItem(stamp.get('desc', 'History edit'))
            self.addItem(list_item)

    def _update_current_step(self, step_value: int):
        """
        Internal function that updates current active history step.

        :param int step_value: step index.
        """

        if step_value >= 0:
            self.setCurrentRow(step_value)
