from __future__ import annotations

import typing
import weakref

from Qt.QtCore import Qt, Signal, QSize
from Qt.QtWidgets import QWidget, QFrame

from tp.libs import qt
from tp.libs.qt.widgets import FlowToolBar

from .toolpanelsbutton import ToolPanelsMenuButton
from .toolpanelstree import ToolPanelsTreeWidget, ToolPanelWidgetTreeItem
from ..managers import ToolPanelsManager

if typing.TYPE_CHECKING:
    from ..view import HubWindow


class HubFrame(QFrame):
    resizeRequested = Signal()
    toolPanelToggled = Signal()
    toolPanelClosed = Signal(object)

    def __init__(
        self,
        window: HubWindow,
        icon_color: tuple[float, float, float] | None = None,
        hue_shift: int = 30,
        icon_size: int = 18,
        icon_padding: int = 1,
        switch_on_click: bool = True,
        toolbar_hidden: bool = False,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._hub_window = weakref.ref(window)
        self._tool_panels_manager = ToolPanelsManager()
        self._icon_color = icon_color
        self._hue_shift = hue_shift
        self._icon_size = icon_size
        self._icon_padding = icon_padding
        self._switch_on_click = switch_on_click
        self._toolbars_hidden = toolbar_hidden

        self._setup_widgets()
        self._setup_layouts()

    @property
    def hub_window(self) -> HubWindow | None:
        """The hub window instance."""

        return self._hub_window()

    @property
    def tool_panels_menu_button(self) -> ToolPanelsMenuButton:
        """The tool panels manager instance."""

        return self._tool_panels_menu_button

    @property
    def tree_widget(self) -> ToolPanelsTreeWidget:
        """The tool panels tree widget."""

        return self._tree

    # region === Setup === #

    def _setup_widgets(self):
        """Set up the widgets for the frame."""

        self._toolbar = HubToolBar(
            hub_frame=self,
            icon_size=self._icon_size,
            icon_padding=self._icon_padding,
            start_hidden=self._toolbars_hidden,
        )
        self._toolbar.flow_layout.set_spacing_y(qt.dpi_scale(3))
        self._tool_panels_menu_button = ToolPanelsMenuButton(size=16, parent=self)
        self._tool_panels_menu_button.menu_align = Qt.AlignRight
        self._tree = ToolPanelsTreeWidget(hub_frame=self)

    def _setup_layouts(self):
        """Set up the layouts for the frame."""

        main_layout = qt.factory.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        top_bar_layout = qt.factory.horizontal_layout(spacing=0, margins=(0, 0, 0, 0))
        top_bar_layout.addWidget(self._tool_panels_menu_button)
        top_bar_layout.addWidget(self._toolbar)

        main_layout.addLayout(top_bar_layout)
        main_layout.addWidget(self._tree)

    # region === Tool Panels === #

    def toggle_tool_panel(
        self,
        tool_id: str,
        activate: bool = True,
        hidden: bool = False,
        keep_open: bool = False,
    ) -> ToolPanelWidgetTreeItem:
        """Add or remove a tool panel from the stack.

        Args:
            tool_id: The tool panel id.
            activate: Whether to activate the tool panel.
            hidden: Whether to hide the tool panel.
            keep_open: Whether to keep the tool panel open.

        Returns:
            The tool panel widget.
        """

        tool_panel_item = self._tree.tool_panel_item(tool_id)

        if tool_panel_item is not None:
            if not keep_open or tool_panel_item.isHidden():
                tool_panel_item.toggle_hidden(activate=activate)
        else:
            tool_panel_item = self._tree.add_tool_panel(tool_id, activate=activate)
            # if self._switch_on_click:
            #     group_type = self._tool_panels_manager.group_from_tool_panel_id(tool_id)
            #     self.set_group(group_type)

        if hidden:
            tool_panel_item.setHidden(True)

        self.resizeRequested.emit()
        self.toolPanelToggled.emit()

        self.update_colors()

        return tool_panel_item

    def update_colors(self) -> None:
        """Update the colors of the toolbar buttons."""

        pass

    # endregion

    # region === Resizing === #

    def calculate_size_hint(self) -> QSize:
        """Calculates the size hint for the frame based on the contents of
        the tree.

        Returns:
            The size hint for the frame.
        """

        size = self.sizeHint()
        width = size.width()
        height = self._tree.calculate_content_height()
        return QSize(width, height)

    # endregion


class HubToolBar(FlowToolBar):
    def __init__(
        self,
        hub_frame: HubFrame,
        icon_size: int = 20,
        icon_padding: int = 2,
        start_hidden: bool = True,
    ):
        super().__init__(
            icon_size=icon_size,
            icon_padding=icon_padding,
            parent=hub_frame,
        )

        self._hub_frame = weakref.ref(hub_frame)

        if start_hidden:
            self.hide()

        self.overflow_menu_active(False)
