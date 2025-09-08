from __future__ import annotations

import typing

from Qt.QtWidgets import QVBoxLayout

from tp.libs.qt.widgets import Window
from tp.libs.qt import factory as qt

from . import tooltips
from .widgets.presets_table import PresetsTableWidget, PresetsTableController

if typing.TYPE_CHECKING:
    from .controllers.abstract import AMatchBakeController


class MatchBakeWindow(Window):
    """Main window for Match & Bake tool."""

    def __init__(self, controller: AMatchBakeController, **kwargs):
        self._controller = controller

        super().__init__(title="Match & Bake", **kwargs)

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        super().setup_widgets()

        self._maintain_offset_checkbox = qt.checkbox(
            text="Maintain Offset",
            checked=True,
            tooltip=tooltips.MAINTAIN_OFFSET_CHECKBOX_TOOLTIP,
            parent=self,
        )
        self._include_scale_checkbox = qt.checkbox(
            text="Scale Constraint",
            tooltip=tooltips.SCALE_CONSTRAINTS_CHECKBOX_TOOLTIP,
            parent=self,
        )
        self._auto_left_right_checkbox = qt.checkbox(
            text="Auto Right Side",
            tooltip=tooltips.AUTO_LEFT_RIGHT_CHECKBOX_TOOLTIP,
            parent=self,
        )

        self._source_combo = qt.combobox_widget(
            label_text="",
            searchable=True,
            parent=self,
        )
        self._target_combo = qt.combobox_widget(
            label_text="", searchable=True, parent=self
        )

        self._presets_table = PresetsTableWidget(parent=self)
        self._presets_controller = PresetsTableController(
            model=self._presets_table.model,
            view=self._presets_table.view,
            parent=self,
        )
        self._presets_table.set_controller(self._presets_controller)

        self._source_combo.add_items(self._presets_controller.preset_source_names)
        self._target_combo.add_items(self._presets_controller.preset_target_names)

    def setup_layouts(self, main_layout: QVBoxLayout):
        super().setup_layouts(main_layout)

        checkboxes_layout = qt.horizontal_layout()
        checkboxes_layout.addWidget(self._maintain_offset_checkbox)
        checkboxes_layout.addWidget(self._include_scale_checkbox)
        checkboxes_layout.addWidget(self._auto_left_right_checkbox)

        combos_layout = qt.horizontal_layout()
        combos_layout.addWidget(self._source_combo)
        combos_layout.addWidget(self._target_combo)

        main_layout.addLayout(checkboxes_layout)
        main_layout.addLayout(combos_layout)
        main_layout.addWidget(self._presets_table)
