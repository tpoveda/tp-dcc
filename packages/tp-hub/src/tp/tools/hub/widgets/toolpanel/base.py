from __future__ import annotations

import typing
import weakref
from dataclasses import dataclass

from Qt.QtCore import Signal, QSize, QTimer
from Qt.QtWidgets import QWidget

from tp.libs import qt
from tp.libs.qt.widgets import StackItem, BaseButton, VerticalLayout

if typing.TYPE_CHECKING:
    from ..toolpanelstree import ToolPanelsTreeWidget, ToolPanelWidgetTreeItem


@dataclass
class ToolPanelUiData:
    label: str = ""
    icon: str = "tpdcc"
    tooltip: str = ""
    default_action_double_click: bool = False
    help_url: str = ""


class BaseToolPanelWidget(StackItem):
    id: str = ""
    ui_data: ToolPanelUiData = ToolPanelUiData()

    toolPanelHidden = Signal()
    toolPanelShown = Signal()

    def __init__(
        self,
        tree_widget: ToolPanelsTreeWidget,
        icon_color: tuple[float, float, float] | None = None,
    ):
        self._icon_color = icon_color
        self._tree_widget = weakref.ref(tree_widget)

        super().__init__(
            title=self.ui_data.label,
            collapsed=True,
            icon=qt.icon(self.ui_data.icon),
            shift_arrows_enabled=False,
            title_editable=False,
            title_upper=True,
            parent=tree_widget,
        )

        self.show_expand_indicator(False)
        self.set_title_text_mouse_transparent(True)
        self.set_icon_color(self._icon_color)
        self.visual_update(collapse=True)

    # region === Setup === #

    def pre_contents_setup(self) -> None:
        """Operations to run before setting up the contents of the tool panel.

        This method can be overridden by subclasses.
        """

    def setup_widgets(self) -> None:
        """Set up the custom user widgets.

        This method can be overridden by subclasses.
        """

    def setup_layouts(self, main_layout: VerticalLayout) -> None:
        """Set up the custom user layouts.

        This method can be overridden by subclasses.
        """

    @property
    def main_layout(self) -> VerticalLayout:
        """The main layout of the tool panel widget."""

        return self._main_layout

    def _setup_widgets(self) -> None:
        """Set up the widgets for the tool panel widget."""

        super()._setup_widgets()

        self._help_button = BaseButton(parent=self)
        self._help_button.set_icon(qt.icon("help"))
        self._help_button.setIconSize(QSize(15, 15))

    def _setup_layouts(self) -> None:
        """Set up the layouts for the tool panel widget."""

        super()._setup_layouts()

        self._title_frame.main_layout.addWidget(self._help_button)

        self._main_layout = VerticalLayout()
        self._main_layout.setSpacing(0)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._contents_layout.addLayout(self._main_layout)

    # endregion

    # region === Visibility === #

    def set_active(self, active: bool = True, emit: bool = True):
        if active:
            self.expand(emit=emit)
        else:
            self.collapse(emit=emit)
            QTimer.singleShot(0, lambda: self.toolPanelHidden.emit())

        self.visual_update()

    # endregion

    # region === Visuals === #

    def set_icon_color(
        self,
        color: tuple[float, float, float] | None,
        set_color: bool = True,
    ):
        if set_color:
            self._icon_color = color

        self.set_item_icon_color(color)
        self._help_button.set_icon_color(
            (color[0] * 0.8, color[1] * 0.8, color[2] * 0.8)
            if color is not None
            else None
        )
        self.set_delete_button_color(color)

    def visual_update(self, collapse: bool = True):
        pass

    # endregion
