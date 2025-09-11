from __future__ import annotations

from Qt.QtWidgets import QPushButton

from tp.libs.qt.widgets import VerticalLayout
from tp.tools.hub.widgets import ToolPanelWidget, ToolPanelUiData


class ControlsCreatorToolPanel(ToolPanelWidget):
    id = "tp.rigging.controls.creator"
    ui_data = ToolPanelUiData(
        label="Control Creator",
        icon="star_control",
        tooltip="Tool for creating control curves",
    )

    def setup_widgets(self) -> None:
        self._button = QPushButton("Create Control", self)

    def setup_layouts(self, main_layout: VerticalLayout) -> None:
        main_layout.addWidget(self._button)

        print('gogogogogog')
