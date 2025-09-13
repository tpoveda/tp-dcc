from __future__ import annotations

import typing
import weakref
from typing import cast

from Qt.QtCore import Signal, QSize, QTimer
from Qt.QtGui import QMouseEvent

from tp.libs import qt
from tp.core import ToolUiData
from tp.managers import ToolsManager
from tp.libs.qt.widgets import StackItem, BaseButton, VerticalLayout

if typing.TYPE_CHECKING:
    from ..toolpanelstree import ToolPanelsTreeWidget
    from ...view import HubWindow


class BaseToolPanelWidget(StackItem):
    ui_data: ToolUiData = ToolUiData()

    toolPanelHidden = Signal()
    toolPanelActivated = Signal()
    toolPanelDeactivated = Signal()
    toolPanelShown = Signal()
    toolPanelClosed = Signal()
    toolPanelDragged = Signal()
    toolPanelDropped = Signal()
    toolPanelDragCancelled = Signal()
    toolPanelMousePressed = Signal()

    def __init__(
        self,
        tree_widget: ToolPanelsTreeWidget | None = None,
        icon_color: tuple[float, float, float] | None = None,
        ui_data: ToolUiData | None = None,
    ):
        self.ui_data = ui_data or self.ui_data
        self._icon_color = icon_color
        self._tree_widget = (
            weakref.ref(tree_widget) if tree_widget is not None else None
        )

        super().__init__(
            title=self.ui_data.get("label"),
            collapsed=True,
            icon=qt.icon(self.ui_data.get("icon")),
            shift_arrows_enabled=False,
            title_editable=False,
            title_upper=True,
            parent=tree_widget,
        )

        self.show_expand_indicator(False)
        self.set_title_text_mouse_transparent(True)
        self.set_icon_color(self._icon_color)
        self.visual_update(collapse=True)

    @property
    def hub_window(self) -> HubWindow | None:
        """The hub window instance the panel is attached to."""

        if self._tree_widget is None:
            return None

        tree_widget = self._tree_widget()
        return tree_widget.hub_window if tree_widget else None

    # region === Setup === #

    def setup(self, tool_id: str | None = None):
        """Set up the tool panel widget.

        This method can be overridden in subclasses to handle the creation
        and setup of the widget contained within the tool panel.

        Args:
            tool_id: Optional tool id to set up the panel with. If not
                specified, the `id` class attribute will be used.

        Notes:
            - This method is called when ToolsPanelsTreeWidget is setting up
                the tool panel widgets (by calling `apply_widget` method).
        """

        if tool_id is not None:
            tools_managers = cast(ToolsManager, ToolsManager())
            tool_class = tools_managers.tool_class(tool_id)
            if tool_class is not None:
                view = tool_class.setup()
                if view is not None:
                    self.main_layout.addWidget(view)

    @property
    def main_layout(self) -> VerticalLayout:
        """The main layout of the tool panel widget."""

        return self._main_layout

    def _setup_widgets(self) -> None:
        """Set up the widgets for the tool panel widget."""

        super()._setup_widgets()

        self._title_frame.mouseReleaseEvent = self._activate_event
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

    def _activate_event(self, event: QMouseEvent) -> None:
        """Handle the mouse release event on the title frame to toggle
        contents.
        """

        self.toggle_contents(emit=True)
        event.ignore()

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
