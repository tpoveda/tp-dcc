from __future__ import annotations

import time

from Qt.QtCore import Qt, QPoint, QSize, QTimer
from Qt.QtWidgets import QSizePolicy, QWidget, QVBoxLayout
from Qt.QtGui import QResizeEvent, QCloseEvent

from tp.libs import qt
from tp.libs.qt.widgets import Window

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
        self._resized_height = 0
        self._icon_color = icon_color
        self._hue_shift = hue_shift
        self._always_resize_to_tree = True
        self._last_focused_time = time.time()

        super().__init__(
            title="Hub",
            width=width,
            height=height,
            always_show_all_title=True,
            init_pos=init_pos,
            parent=parent,
            maximize_button=False,
            settings_path="tp/hub",
        )

        self._hub_frame.setUpdatesEnabled(False)
        try:
            [self.toggle_tool_panel(tool_id) for tool_id in (tool_ids or [])]
        finally:
            self._hub_frame.setUpdatesEnabled(True)

        self.set_highlight(True, update_hub_windows=True)

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

    def closeEvent(self, event: QCloseEvent) -> None:
        """Overridden Qt method that is called when the window is closed.

        Args:
            event: The close event.
        """

        self._hub_frame.tree_widget.closeEvent(event)

        super().closeEvent(event)

        try:
            self._HUB_INSTANCES.remove(self)
            self._HUB_FRAME_INSTANCES.remove(self.hub_frame)
        except ValueError:
            pass

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

    # region === Resizing === #

    def resizeEvent(self, event: QResizeEvent) -> None:
        """Overridden Qt method that is called when the window is resized.

        Args:
            event: The resize event.
        """

        super().resizeEvent(event)
        self._resized_height = event.size().height()

    def maximize(self) -> None:
        """Maximizes the window.

        Overrides the default maximize behavior to adjust the height based on
        the contents of the tree widget.
        """

        width = self._saved_size.width()
        calculated_height = self._calculate_height()
        self._set_ui_minimized(False)
        self._minimized = False

        # Use the resized height
        if calculated_height < self._resized_height:
            self.window().resize(width, self._resized_height)
        else:
            self.window().resize(width, calculated_height)

    def resize_window(
        self, disable_scroll_bars: bool = True, delayed: bool = False
    ) -> None:
        """Resize the window based on the contents of the tree widget.

        Args:
            disable_scroll_bars: Whether to disable the scroll bars while
                resizing.
            delayed: If True, the resize will be performed after a short delay.
        """

        if delayed:
            QTimer.singleShot(
                0,
                lambda: self.resize_window(
                    disable_scroll_bars=disable_scroll_bars, delayed=False
                ),
            )
            return

        if not self.is_docked():
            if disable_scroll_bars:
                self._hub_frame.tree_widget.setVerticalScrollBarPolicy(
                    Qt.ScrollBarAlwaysOff
                )

            self._max_height = self._max_window_height()
            new_height = (
                self.window().minimumSizeHint().height()
                + self._hub_frame.calculate_size_hint().height()
            )
            new_height = (
                self._max_height if new_height > self._max_height else new_height
            )
            width = self.window().rect().width()

            if new_height < self._resized_height and not self._always_resize_to_tree:
                self.window().resize(width, self._resized_height)
            else:
                self.window().resize(width, new_height)
                self._resized_height = new_height

            # if disable_scroll_bars:
            #     self._hub_frame.tree_widget.setVerticalScrollBarPolicy(
            #         Qt.ScrollBarAsNeeded
            #     )
        else:
            self.setMinimumSize(QSize(self.width(), 300))
            self.setMinimumSize(QSize(0, 0))

    def _max_window_height(self) -> int:
        """Calculate the maximum height of the window based on its contents.

        Returns:
            The maximum height of the window.
        """

        pos = self.mapToGlobal(QPoint(0, 0))
        screen_geometry = qt.screen_from_widget(self).geometry()
        relative_pos = pos - QPoint(screen_geometry.left(), screen_geometry.top())

        return screen_geometry.height() - relative_pos.y() - 50

    def _calculate_height(self) -> int:
        """Calculate the height of the window based on the contents of the tree
        widget.

        Returns:
            The calculated height of the window.
        """

        self._max_height = self._max_window_height()
        new_height = (
            self.window().minimumSizeHint().height()
            + self._hub_frame.calculate_size_hint().height()
        )
        new_height = self._max_height if new_height > self._max_height else new_height
        return new_height

    # region === Visual === #

    def set_highlight(self, highlight: bool, update_hub_windows: bool = False) -> None:
        """Sets whether the window is highlighted.

        Args:
            highlight: Whether to highlight the window.
            update_hub_windows: Whether to update the highlight state of all
                hub windows.
        """

        if self.is_minimized() and not highlight:
            self._title_bar.set_logo_highlight(True)
            return

        self._last_focused_time = time.time()

        if highlight and update_hub_windows:
            for t in HubWindow.hubs():
                if not t.is_minimized():
                    t.title_bar.set_logo_highlight(False)
            self.title_bar.set_logo_highlight(True)

    # endregion
