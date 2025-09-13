from __future__ import annotations

import typing

from Qt.QtWidgets import QWidget

from tp.libs import qt
from tp.libs.qt.widgets import ThumbBrowser

if typing.TYPE_CHECKING:
    from .model import ControlsCreatorModel


class ControlsCreatorView(QWidget):
    def __init__(self, model: ControlsCreatorModel, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._model = model

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    # region === Setup ===

    @property
    def thumb_browser(self) -> ThumbBrowser:
        """The thumbnail browser widget."""

        return self._thumb_browser

    def _setup_widgets(self) -> None:
        """Set up the widgets for the controls creator view."""

        self._thumb_browser = ThumbBrowser(
            columns=4,
            fixed_height=382,
            uniform_icons=True,
            item_name="Curve Control",
            create_text="Save New",
            apply_text="Change/Build Control",
            apply_icon=qt.icon("starburst_shape"),
            select_directories_active=True,
            parent=self,
        )
        self._thumb_browser.set_model(self._model.browser_model)

    def _setup_layouts(self) -> None:
        """Set up the layouts for the controls creator view."""

        main_layout = qt.factory.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        main_layout.addWidget(self._thumb_browser)

    def _setup_signals(self) -> None:
        """Set up the signals for the controls creator view."""
        pass

    # endregion
