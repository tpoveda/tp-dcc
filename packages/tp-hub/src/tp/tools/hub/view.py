from __future__ import annotations

from typing import cast

from Qt.QtWidgets import QSizePolicy, QWidget, QVBoxLayout, QTreeWidget

from tp.libs import qt
from tp.libs.qt.widgets import Window

from .managers import ToolPanelsManager
from .widgets import HubFrame, ToolPanelWidgetTreeItem


class HubWindow(Window):
    # noinspection PyUnreachableCode
    def __init__(
        self,
        width=390,
        height=20,
        max_height=800,
        init_pos: tuple[int, int] | None = None,
        icon_color: tuple[int, int, int] = (231, 133, 255),
        hue_shift: int = -30,
        tool_ids: list[str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize the hub window.

        Args:
            width: The width of the window.
            height: The height of the window.
            max_height: Maximum height of the window.
            init_pos: Initial position of the window.
            icon_color: RGB color of the window icon.
            hue_shift: Hue shift to apply to the window icon.
            tool_ids: List of tool ids to show in the hub.
            parent: The parent widget of the window.
        """

        self._max_height = qt.dpi_scale(max_height)
        self._icon_color = icon_color
        self._hue_shift = hue_shift
        self._tool_panels_manager = cast(ToolPanelsManager, ToolPanelsManager())

        super().__init__(
            title="Hub",
            width=width,
            height=height,
            always_show_all_title=True,
            init_pos=init_pos,
            parent=parent,
            maximize_button=False,
        )

        self._hub_frame.setUpdatesEnabled(False)
        try:
            [self.toggle_tool_panel(tool_id) for tool_id in (tool_ids or [])]
        finally:
            self._hub_frame.setUpdatesEnabled(True)

        HubWindow.add_hub(self)

    # region === Instances === #

    _HUB_INSTANCES: list[HubWindow] = []
    _HUB_FRAME_INSTANCES: list[HubFrame] = []

    @classmethod
    def hubs(cls) -> list[HubWindow]:
        """Returns the list of hub instances.

        Returns:
            List of hub instances.
        """

        return cls._HUB_INSTANCES

    @classmethod
    def hub_frames(cls) -> list[HubFrame]:
        """Returns the list of hub frame instances.

        Returns:
            List of hub frame instances.
        """

        return cls._HUB_FRAME_INSTANCES

    @classmethod
    def add_hub(cls, hub: HubWindow) -> None:
        """Adds a hub instance to the list of instances.

        Args:
            hub: The hub instance to add.
        """

        cls._HUB_INSTANCES.append(hub)
        cls.add_hub_frame(hub.hub_frame)

    @classmethod
    def add_hub_frame(cls, hub_frame: HubFrame) -> None:
        """Adds a hub frame instance to the list of instances.

        Args:
            hub_frame: The hub frame instance to add.
        """

        if hub_frame in cls._HUB_FRAME_INSTANCES:
            return
        cls._HUB_FRAME_INSTANCES.append(hub_frame)

    # endregion

    # region === Setup === #

    @property
    def hub_frame(self) -> HubFrame:
        """The hub frame instance."""

        return self._hub_frame

    # noinspection PyAttributeOutsideInit
    def setup_widgets(self):
        super().setup_widgets()

        self._hub_frame = HubFrame(
            window=self,
            icon_color=self._icon_color,
            hue_shift=self._hue_shift,
            toolbar_hidden=False,
        )
        self._hub_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._title_bar.contents_layout.addWidget(self._hub_frame)
        self._title_bar.corner_contents_layout.addWidget(
            self._hub_frame.tool_panels_menu_button
        )

    def setup_layouts(self, main_layout: QVBoxLayout):
        super().setup_layouts(main_layout)

        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._hub_frame.tree_widget)
        main_layout.setStretch(1, 1)

    def setup_signals(self):
        super().setup_signals()

        self._hub_frame.resizeRequested.connect(self.resize_window)

    # endregion

    # region === Tool Panels === #

    def toggle_tool_panel(
        self, tool_id: str, activate: bool = True, keep_open: bool = False
    ) -> ToolPanelWidgetTreeItem:
        """Toggles the visibility of a tool panel in the hub.

        Args:
            tool_id: The id of the tool panel to toggle.
            activate: Whether to activate the tool panel if it's being shown.
            keep_open: If True, the tool panel will remain open even if
                another tool panel is activated.

        Returns:
            The tool panel widget.
        """

        return self._hub_frame.toggle_tool_panel(
            tool_id, activate=activate, keep_open=keep_open
        )

    # endregion
