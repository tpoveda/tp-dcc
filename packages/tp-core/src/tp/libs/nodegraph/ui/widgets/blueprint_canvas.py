from __future__ import annotations

from Qt.QtWidgets import QWidget

from tp.libs.qt import factory as qt

from ..canvas.canvas_base import CanvasBase


class BlueprintCanvas(CanvasBase):
    pass


class BlueprintCanvasWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__()

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self):
        """Set up widgets for the blueprint canvas."""

        self._canvas = BlueprintCanvas(parent=self)

    def _setup_layouts(self):
        """Set up layouts for the blueprint canvas."""

        main_layout = qt.vertical_main_layout()
        self.setLayout(main_layout)

        main_layout.addWidget(self._canvas)
