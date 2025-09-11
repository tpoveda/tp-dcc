from __future__ import annotations

import typing

from Qt.QtWidgets import QVBoxLayout

from tp.libs.qt import icons
from tp.libs.qt.widgets import Window
from tp.libs.qt import factory as qt

from . import tooltips

if typing.TYPE_CHECKING:
    from .controllers.abstract import ASkinningToolboxController


class SkinningToolboxWindow(Window):
    """Main window for Skinning toolbox."""

    def __init__(self, controller: ASkinningToolboxController, **kwargs):
        self._controller = controller

        super().__init__(title="Skinning Toolbox", **kwargs)

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        super().setup_widgets()

        self._skin_transfer_button = qt.left_aligned_button(
            text="Skin Transfer",
            tooltip=tooltips.SKIN_TRANSFER_TOOLTIP,
            button_icon=icons.icon("data_transfer"),
            parent=self,
        )

        self._reset_bind_pose_button = qt.left_aligned_button(
            text="Reset Bind Pose",
            tooltip=tooltips.RESET_BIND_POSE_TOOLTIP,
            button_icon=icons.icon("toggle_on"),
            parent=self,
        )

    def setup_layouts(self, main_layout: QVBoxLayout):
        super().setup_layouts(main_layout)

        skin_transfer_layout = qt.horizontal_layout()
        skin_transfer_layout.addWidget(self._skin_transfer_button)
        skin_transfer_layout.addWidget(self._reset_bind_pose_button)

        main_layout.addLayout(skin_transfer_layout)

    def setup_signals(self):
        super().setup_signals()

        self._skin_transfer_button.clicked.connect(self._controller.skin_transfer)
        self._reset_bind_pose_button.clicked.connect(self._controller.skin_toggle)
