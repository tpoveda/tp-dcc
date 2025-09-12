from __future__ import annotations

import typing

from tp.preferences.interfaces import rigging
from tp.libs.qt.widgets import VerticalLayout, ThumbBrowser
from tp.tools.hub.widgets import ToolPanelWidget, ToolPanelUiData

if typing.TYPE_CHECKING:
    from tp.preferences.assets import BrowserPreference


class ControlsCreatorToolPanel(ToolPanelWidget):
    id = "tp.rigging.controls.creator"
    ui_data = ToolPanelUiData(
        label="Control Creator",
        icon="star_control",
        tooltip="Tool for creating control curves",
    )

    # noinspection PyAttributeOutsideInit
    def pre_contents_setup(self) -> None:
        """Operations to run before setting up the contents of the tool panel."""

        self._control_prefs = rigging.controls_creator_interface()
        self._control_assets_prefs: BrowserPreference = (
            self._control_prefs.control_assets
        )

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self) -> None:
        uniform_icons = self._control_assets_prefs.browser_uniform_icons()

        self._thumb_browser = ThumbBrowser(
            columns=4, fixed_height=382, uniform_icons=uniform_icons
        )

    def setup_layouts(self, main_layout: VerticalLayout) -> None:
        main_layout.addWidget(self._thumb_browser)
