from __future__ import annotations

import typing
import weakref
from typing import cast, Type, Any
from collections.abc import Generator

from Qt.QtCore import Qt
from Qt.QtWidgets import QSizePolicy, QTreeWidgetItem

from tp.libs import qt
from tp.libs.qt.widgets import GroupedTreeWidget

from ..managers import ToolPanelsManager

if typing.TYPE_CHECKING:
    from .hubframe import HubFrame
    from .toolpanel import ToolPanelWidget
    from ..view import HubWindow


class ToolPanelWidgetTreeItem(QTreeWidgetItem):
    def __init__(
        self,
        tool_panel_widget_class: Type[ToolPanelWidget],
        tree_widget: ToolPanelsTreeWidget,
        color: tuple[int, int, int] | None = None,
    ):
        super().__init__()

        self._color = color
        self._widget = tool_panel_widget_class(
            icon_color=color, widget_item=self, tree_widget=tree_widget
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

        tool_panels_manager = cast(ToolPanelsManager, ToolPanelsManager())
        tool_panel_class = tool_panels_manager.tool_panel_class(tool_id)
        if not tool_panel_class:
            return None

        return cls(
            tool_panel_widget_class=tool_panel_class,
            tree_widget=tree_widget,
            color=color,
        )

    def id(self) -> str:
        """Return the tool panel id.

        Returns:
            The tool panel id.
        """

        return self._widget.id

    # region === Setup === #

    def apply_widget(self, activate: bool = True) -> None:
        self._widget.setParent(self.treeWidget())
        self.treeWidget().setItemWidget(self, 0, self._widget)

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
    def __init__(self, hub_frame: HubFrame):
        super().__init__(
            custom_tree_widget_item_class=ToolPanelWidgetTreeItem, parent=hub_frame
        )

        self._tool_panels_manager = cast(ToolPanelsManager, ToolPanelsManager())
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

        color = self._tool_panels_manager.tool_panel_color(tool_id)
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

    # endregion
