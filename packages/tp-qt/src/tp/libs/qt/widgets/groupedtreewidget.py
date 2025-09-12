from __future__ import annotations

import enum
from typing import Type
from collections.abc import Generator

from loguru import logger
from Qt.QtCore import Qt, QTimer
from Qt.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
)

from tp.libs import qt


class GroupedTreeWidget(QTreeWidget):
    WIDGET_COLUMN = 1
    DATA_COLUMN = 2
    DEFAULT_GROUP_NAME = "Group"

    class GroupedTreeItemType(str, enum.Enum):
        """Enum for the different types of items in the grouped tree widget."""

        Group = "GROUP"
        Widget = "WIDGET"

    def __init__(
        self,
        locked: bool = False,
        allow_sub_groups: bool = True,
        custom_tree_widget_item_class: Type[QTreeWidgetItem] = QTreeWidgetItem,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        self._locked = locked
        self._allow_sub_groups = allow_sub_groups
        self._custom_tree_widget_item_class = custom_tree_widget_item_class

        self._group_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
        self._group_unlocked_flags = Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        self._item_widget_flags = (
            Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsDragEnabled
        )
        self._item_widget_unlocked_flags = Qt.ItemIsDragEnabled

        self.set_locked(locked)

        self._header_item = QTreeWidgetItem(["Widget"])
        self.setHeaderItem(self._header_item)
        self.header().hide()

        self.resizeColumnToContents(1)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setIndentation(qt.dpi_scale(10))
        self.setFocusPolicy(Qt.NoFocus)

        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setAcceptDrops(True)

    def iterator(self) -> Generator[QTreeWidgetItem, None, None]:
        """Generator that iterates over all items in the tree widget.

        Yields:
            Each item in the tree widget.
        """

        for tree_item in qt.safe_tree_widget_iterator(self):
            yield tree_item

    # region === Tree Items === #

    def itemWidget(
        self, item: QTreeWidgetItem | None, column: int | None = None
    ) -> QWidget | None:
        """Returns the widget for the given item and column.

        Args:
            item: The tree item to get the widget for.
            column: The column to get the widget for.

        Returns:
            The widget for the given item and column.
        """

        return super().itemWidget(
            item, column if column is not None else GroupedTreeWidget.WIDGET_COLUMN
        )

    # noinspection PyMethodMayBeStatic
    def item_type(self, tree_item: QTreeWidgetItem) -> GroupedTreeItemType | None:
        """Returns the type of the given tree item.

        Args:
            tree_item: The tree item to get the type of.

        Returns:
            The type of the tree item.
        """

        return GroupedTreeWidget.GroupedTreeItemType(
            tree_item.data(GroupedTreeWidget.DATA_COLUMN, Qt.EditRole)
        )

    def get_item_name(self, tree_item: QTreeWidgetItem) -> str:
        """Returns the name of the given tree item.

        Args:
            tree_item: The tree item to get the name of.

        Returns:
            The name of the tree item.
        """

        item_type = self.item_type(tree_item)
        item_widget: QWidget = self.itemWidget(tree_item)

        if item_type == GroupedTreeWidget.GroupedTreeItemType.Group:
            return tree_item.text(GroupedTreeWidget.WIDGET_COLUMN)
        elif (
            item_type == GroupedTreeWidget.GroupedTreeItemType.Widget
            and item_widget is not None
        ):
            if isinstance(item_widget, ItemWidgetLabel):
                return item_widget.text()
            return (
                item_widget.name
                if hasattr(item_widget, "name")
                else tree_item.text(GroupedTreeWidget.WIDGET_COLUMN)
            )
        else:
            logger.warning(
                f"Unknown item type: {item_type}. Returning empty string as item name."
            )
            return ""

    # region === Groups === #

    def get_unique_group_name(self) -> str:
        """Generates a unique group name based on existing groups in the
        tree widget.

        The group names are in the format "Group X", where X is a number.
        For example, if there are already two groups named "Group 1" and
        "Group 2", the next unique group name will be "Group 3".

        Returns:
            A unique group name.
        """

        num = len(
            self.findItems(self.DEFAULT_GROUP_NAME + " *", Qt.MatchFlag.MatchWildcard)
        )
        return f"{self.DEFAULT_GROUP_NAME} {num + 1}"

    # endregion

    # region === Lock / Unlock === #

    def set_locked(self, flag: bool) -> None:
        """Sets whether the tree widget is locked or not.

        Args:
            flag: Whether to lock or unlock the tree widget.
        """

        self._locked = flag

        if flag:
            self._group_flags = self._group_flags & ~self._group_unlocked_flags
            self._item_widget_flags = (
                self._item_widget_flags & ~self._item_widget_unlocked_flags
            )
        else:
            self._group_flags = self._group_flags | self._group_unlocked_flags
            self._item_widget_flags = (
                self._item_widget_flags | self._item_widget_unlocked_flags
            )

        self._apply_flags()

    def _apply_flags(self) -> None:
        """Applies the current flags to all items in the tree widget."""

        for tree_item in self.iterator():
            item_type = self.item_type(tree_item)
            if item_type == GroupedTreeWidget.GroupedTreeItemType.Group:
                tree_item.setFlags(self._group_flags)
            elif item_type == GroupedTreeWidget.GroupedTreeItemType.Widget:
                tree_item.setFlags(self._item_widget_flags)

    # endregion

    # region === Update === #

    def update_tree_widget(self, delay: bool = False) -> None:
        """Update the tree widget so the row heights are recalculated.

        Notes:
            - This method is a workaround for a Qt issue where the row heights
                are not recalculated when the widget is resized or when the
                contents are changed. This can lead to items cut off or not
                fully visible.

        Args:
            delay: Whether to delay the update to the next event loop iteration.
        """

        def _delay_process() -> None:
            QApplication.processEvents()
            self.update_tree_widget(delay=False)

        self.setUpdatesEnabled(False)
        try:
            if delay:
                QTimer.singleShot(0, _delay_process)
                return

            self.insertTopLevelItem(0, QTreeWidgetItem())
            self.takeTopLevelItem(0)

        finally:
            self.setUpdatesEnabled(True)

    # endregion


class ItemWidgetLabel(QLabel):
    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(name, parent=parent)
