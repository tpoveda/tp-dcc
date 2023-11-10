from __future__ import annotations

from tp.common.qt import api as qt


class RigScriptView(qt.FramelessWindow):
    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._stack = qt.sliding_opacity_stacked_widget()
        self.main_layout().addWidget(self._stack)
