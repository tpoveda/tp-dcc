from __future__ import annotations

import typing
import weakref
from typing import cast, Type, Any
from collections.abc import Generator

from Qt.QtCore import Qt, Signal, QTimer
from Qt.QtWidgets import QSizePolicy, QTreeWidgetItem

from tp.libs import qt
from tp.core import ToolUiData
from tp.managers import ToolsManager
from tp.libs.qt.widgets import GroupedTreeWidget

from .toolpanel import ToolPanelWidget

if typing.TYPE_CHECKING:
    from .hubframe import HubFrame
    from ..view import HubWindow


class ToolPanelWidgetTreeItem(QTreeWidgetItem):
    # noinspection PyShadowingBuiltins
    def __init__(
        self,
        id: str,
        tool_panel_widget_class: Type[ToolPanelWidget],
        tree_widget: ToolPanelsTreeWidget,
        color: tuple[int, int, int] | None = None,
        ui_data: ToolUiData | None = None,
    ) -> None:
        """Initialize the tool panel tree item.

        Args:
            id: The tool panel id.
            tool_panel_widget_class: The tool panel widget class to instantiate.
            tree_widget: The tree widget to add the tool panel to.
            color: The color to use for the tool panel icon.
            ui_data: The tool panel UI data.
        """

        super().__init__()

        self._id = id
        self._color = color
        self._widget = tool_panel_widget_class(
            icon_color=color,
            tree_widget=tree_widget,
            ui_data=ui_data,
        )

        self.setChildIndicatorPolicy(QTreeWidgetItem.DontShowIndicator)
        self.set_icon_color(color)
        self.setData(
            GroupedTreeWidget.DATA_COLUMN,
            Qt.EditRole,
            GroupedTreeWidget.GroupedTreeItemType.Widget,
        )

    @classmethod
    def create_from_tool_id(
        cls,
        tool_id,
        tree_widget: ToolPanelsTreeWidget,
        color: tuple[int, int, int] | None = None,
    ) -> ToolPanelWidgetTreeItem | None:
        """Creates a tool panel tree item from the given tool id.

        Args:
            tool_id: The tool panel id.
            tree_widget: The tree widget to add the tool panel to.
            color: The color to use for the tool panel icon.

        Returns:
            The tool panel tree item or None if the tool panel could not be
                found.
        """

        tools_managers = cast(ToolsManager, ToolsManager())
        tool_class = tools_managers.tool_class(tool_id)
        if not tool_class:
            return None

        tool_panel_class = tool_class.tool_panel_class
        tool_panel_class = tool_panel_class or ToolPanelWidget

        tool_panel = cls(
            id=tool_id,
            tool_panel_widget_class=tool_panel_class,
            tree_widget=tree_widget,
            color=color,
            ui_data=tool_class.ui_data,
        )

        return tool_panel

    def id(self) -> str:
        """Return the tool panel id.

        Returns:
            The tool panel id.
        """

        return self._id

    # region === Setup === #

    @property
    def widget(self) -> ToolPanelWidget:
        """The tool panel widget instance."""

        return self._widget

    def apply_widget(self, activate: bool = True) -> None:
        tree_widget = cast(ToolPanelsTreeWidget, self.treeWidget())

        self._widget.setParent(self.treeWidget())
        tree_widget.setItemWidget(self, 0, self._widget)

        self._widget.maximized.connect(
            lambda: tree_widget.activate_tool_panel(self, activate=True)
        )
        self._widget.minimized.connect(
            lambda: tree_widget.activate_tool_panel(self, activate=False)
        )
        self._widget.deletePressed.connect(self.toggle_hidden)
        self._widget.deletePressed.connect(
            lambda: tree_widget.toolPanelHidden.emit(self.id())
        )

        tools_managers = cast(ToolsManager, ToolsManager())
        tool_class = tools_managers.tool_class(self.id())

        # Set up the widget.
        self._widget.setup(tool_id=tool_class.id if tool_class else None)

        self.setData(
            GroupedTreeWidget.DATA_COLUMN,
            Qt.EditRole,
            GroupedTreeWidget.GroupedTreeItemType.Widget,
        )

        self._widget.set_active(activate)

    def set_icon_color(self, color: tuple[int, int, int]) -> None:
        """Sets the icon color of the tool panel tree item.

        Args:
            color: The RGB color to set.
        """

        self._color = color
        self._widget.set_icon_color(color)

    # endregion

    # region === Visibility === #

    def setHidden(self, hide: bool) -> None:
        super().setHidden(hide)

        if hide:
            self._widget.toolPanelHidden.emit()
        else:
            self._widget.toolPanelShown.emit()

    def toggle_hidden(self, activate: bool = True) -> None:
        """Toggles the hidden state of the tool panel.

        Args:
            activate: Whether to activate the tool panel if it is being shown.
        """

        self.setHidden(not self.isHidden())
        self._widget.set_active(activate)

    # endregion


class ToolPanelsTreeWidget(GroupedTreeWidget):
    toolPanelHidden = Signal(str)

    def __init__(self, hub_frame: HubFrame):
        super().__init__(
            custom_tree_widget_item_class=ToolPanelWidgetTreeItem, parent=hub_frame
        )

        self._hub_frame = weakref.ref(hub_frame)

        self.setMouseTracking(True)
        self.setIndentation(0)
        self.setMinimumHeight(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)

    @property
    def hub_frame(self) -> HubFrame | None:
        """The hub frame instance."""

        return self._hub_frame()

    @property
    def hub_window(self) -> HubWindow | None:
        """The hub window instance."""

        hub_frame = self._hub_frame()
        return hub_frame.hub_window if hub_frame else None

    # region === Tool Panels === #

    def item_exists(self, item: ToolPanelWidgetTreeItem) -> bool:
        """Returns whether the given tool panel tree item exists in the tree.

        Args:
            item: The tool panel tree item to check.

        Returns:
            `True` if the item exists; `False` otherwise.
        """

        for existing_item in self.iterator():
            if type(item) == type(existing_item):
                return True
            if existing_item.id() == item.id():
                return True

        return False

    def iterator(self) -> Generator[ToolPanelWidgetTreeItem, Any, None]:
        """Generator that iterates over all tool panel tree items.

        Yields:
            The next tool panel tree item.
        """

        return cast(Generator[ToolPanelWidgetTreeItem, Any, None], super().iterator())

    def tool_panel_ids(self) -> list[str]:
        """Returns all tool panel ids.

        Returns:
            List of all tool panel ids.
        """

        return [item.id() for item in self.iterator()]

    def tool_panel_items(self) -> list[ToolPanelWidgetTreeItem]:
        """Returns all tool panel tree items.

        Returns:
            List of all tool panel tree items.
        """

        return [item for item in self.iterator()]

    def tool_panel_item(self, tool_id: str) -> ToolPanelWidgetTreeItem | None:
        """Returns the tool panel tree item for the given tool id.

        Args:
            tool_id: The tool panel id.

        Returns:
            The tool panel tree item or None if not found.
        """

        found_panel_item: ToolPanelWidgetTreeItem | None = None

        for panel_item in self.iterator():
            if panel_item.id() == tool_id:
                found_panel_item = panel_item
                break

        return found_panel_item

    def add_tool_panel_item(self, tool_panel_item: ToolPanelWidgetTreeItem) -> bool:
        """Adds a tool panel tree item to the tree.

        Args:
            tool_panel_item: The tool panel tree item to add.

        Returns:
            `True` if the tool panel item was added; `False` if it already
                exists.
        """

        if self.item_exists(tool_panel_item):
            return False

        self.addTopLevelItem(tool_panel_item)
        tool_panel_item.setFlags(self._item_widget_flags)

        return True

    def add_tool_panel(
        self, tool_id: str, activate: bool = True
    ) -> ToolPanelWidgetTreeItem | None:
        """Adds a tool panel to the tree.

        Args:
            tool_id: The tool panel id.
            activate: Whether to activate the tool panel if it's being shown.

        Returns:
            The tool panel tree item or None if the tool panel could not be
                found or added.
        """

        index = self.invisibleRootItem().childCount()
        return self.insert_tool_panel(tool_id, index, activate=activate)

    def insert_tool_panel(
        self,
        tool_id: str,
        index: int,
        activate: bool = True,
        parent: QTreeWidgetItem | None = None,
    ) -> ToolPanelWidgetTreeItem | None:
        """Inserts a tool panel at the given index in the tree.

        Args:
            tool_id: The tool panel id.
            index: The index to insert the tool panel at.
            activate: Whether to activate the tool panel if it's being shown.
            parent: The parent tree item to insert the tool panel under. If
                `None`, the tool panel will be inserted at the top level.

        Returns:
            The tool panel tree item or None if the tool panel could not be
                found or added.
        """

        color = cast(ToolsManager, ToolsManager()).tool_color(tool_id)
        tree_widget_item = ToolPanelWidgetTreeItem.create_from_tool_id(
            tool_id=tool_id, tree_widget=self, color=color
        )

        root = parent or self.invisibleRootItem()
        child_count = root.childCount()
        index = root.childCount() if index > child_count else index
        root.insertChild(index, tree_widget_item)

        tree_widget_item.setFlags(self._item_widget_flags)
        tree_widget_item.apply_widget(activate=activate)

        return tree_widget_item

    def activate_tool_panel(
        self,
        tool_panel_item: ToolPanelWidgetTreeItem,
        activate: bool = True,
        close_others: bool = False,
    ) -> None:
        """Activates or deactivates the given tool panel tree item.

        Args:
            tool_panel_item: The tool panel tree item to activate or deactivate.
            activate: Whether to activate or deactivate the tool panel.
            close_others: Whether to close other tool panels when activating
                this one.
        """

        widget = cast(ToolPanelWidget, tool_panel_item.widget)
        widget.set_active(activate, emit=False)

        if close_others:
            for tree_item in qt.safe_tree_widget_iterator(self):
                if tree_item is not tool_panel_item:
                    # noinspection PyUnresolvedReferences
                    tree_item.collapse()

        QTimer.singleShot(0, lambda: self.update_tree_widget())

    def update_tree_widget(self, disable_scroll_bars: bool = False) -> None:
        vertical_policy: Qt.ScrollBarPolicy | None = None
        if disable_scroll_bars:
            vertical_policy = self.verticalScrollBarPolicy()
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        super().update_tree_widget()

        self._hub_frame().resizeRequested.emit()

        if vertical_policy is not None:
            self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    # endregion

    # region === Resizing === #

    def calculate_content_height(self) -> int:
        """Calculate the total height of all visible tool panel widgets in the
        tree.

        Notes:
            - This method is used to determine the size hint for the hub frame
                based on the contents of the tree.
            - This method ignores hidden tool panels.

        Returns:
            The total height of all visible tool panel widgets.
        """

        total_height: int = 0
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if isinstance(item, ToolPanelWidgetTreeItem) and not item.isHidden():
                total_height += item.widget.sizeHint().height()

        return total_height

    # endregion
