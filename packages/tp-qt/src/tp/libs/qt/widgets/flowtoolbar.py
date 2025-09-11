from __future__ import annotations

from Qt.QtCore import Qt, QSize
from Qt.QtWidgets import QWidget, QFrame
from Qt.QtGui import QIcon

from .. import icons
from .dialogs import BaseDialog
from .buttons import IconMenuButton
from .layouts import VerticalLayout, HorizontalLayout, FlowLayout


class FlowToolBar(QFrame):
    def __init__(
        self,
        menu_indicator_icon: QIcon | None = None,
        icon_size: int = 20,
        icon_padding: int = 2,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._icon_size = icon_size
        self._icon_padding = icon_padding
        self._menu_indicator_icon = menu_indicator_icon or icons.icon("arrow_menu")
        self._overflow_icon = icons.icon("sort_down")
        self._overflow_menu = False

        self._setup_widgets()
        self._setup_layouts()

    # region === Setup === #

    @property
    def flow_layout(self) -> FlowLayout:
        """The layout of the overflow menu."""

        return self._flow_layout

    def _setup_widgets(self) -> None:
        """Set up the widgets for the toolbar."""

        self._overflow_menu_button = IconMenuButton(parent=self)
        self._overflow_menu_button.set_icon(
            self._overflow_icon, size=self._icon_size, color_offset=40
        )
        self._overflow_menu_button.double_click_enabled = False
        self._overflow_menu_button.setFixedWidth(29)
        self._overflow_menu_button.setVisible(False)

    def _setup_layouts(self) -> None:
        """Set up the layouts for the toolbar."""

        main_layout = HorizontalLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignTop)
        self.setLayout(main_layout)

        self._flow_layout = FlowLayout(margin=0, spacing_x=1, spacing_y=1)
        self._flow_layout.addWidget(self._overflow_menu_button)

        main_layout.addLayout(self._flow_layout)

    # endregion

    # region === Overflow Menu === #

    def overflow_menu_active(self, active: bool) -> None:
        """Sets whether the overflow menu is active or not.

        Args:
            active: Whether the overflow menu is active or not.
        """

        self._overflow_menu = active
        self._overflow_menu_button.setVisible(active)

    # endregion


class FlowToolBarMenu(BaseDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_layouts()

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)

    # region === Setup === #

    def _setup_layouts(self) -> None:
        """Set up the layouts for the menu."""

        main_layout = VerticalLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    # endregion

    # region === Overrides === #

    def sizeHint(self) -> QSize:
        """Override size hint to return the minimum size.

        Returns:
            The minimum size of the menu.
        """

        return self.minimumSize()

    def show(self) -> None:
        """Override the `show` method to adjust the size of the menu before
        showing it.
        """

        super().show()
        self.resize(self.sizeHint())

    # endregion
