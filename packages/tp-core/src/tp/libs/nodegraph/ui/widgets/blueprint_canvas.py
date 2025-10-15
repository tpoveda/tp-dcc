from __future__ import annotations

import typing

from Qt.QtWidgets import QWidget

from tp.libs.qt import factory as qt

from ..canvas.canvas_base import CanvasBase

if typing.TYPE_CHECKING:
    from ...core.graph_manager import GraphManager


class BlueprintCanvas(CanvasBase):
    pass


class BlueprintCanvasWidget(QWidget):
    def __init__(self, graph_manager: GraphManager, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._graph_manager = graph_manager

        self._setup_widgets()
        self._setup_layouts()

    def _setup_widgets(self) -> None:
        """Set up widgets for the blueprint canvas."""

        self._canvas = BlueprintCanvas(parent=self)

    def _setup_layouts(self) -> None:
        """Set up layouts for the blueprint canvas."""

        main_layout = qt.vertical_main_layout()
        self.setLayout(main_layout)

        main_layout.addWidget(self._canvas)
