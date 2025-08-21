from __future__ import annotations

import pickle
from typing import Any

from Qt import QtCompat
from Qt.QtCore import Qt, QObject, QModelIndex, QAbstractItemModel, QMimeData

from . import roles
from .data import BaseDataSource


class TreeModel(QAbstractItemModel):
    """A model for displaying hierarchical data sources in a tree structure."""

    def __init__(self, root: BaseDataSource, parent: QObject | None = None):
        """Initialize the TreeModel with a root data source.

        Args:
            root: The root data source for the model. This should be an instance
                of `BaseDataSource` or a subclass.
            parent: The parent QObject for the model.
        """

        super().__init__(parent=parent)

        self._root = root
        if self._root:
            self._root.model = self

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows for the given parent index.

        Args:
            parent: The parent index to count rows for. If invalid, it
                counts rows for the root data source.

        Returns:
            The number of rows for the given parent index.
        """

        return self.item_from_index(parent).row_count() if self._root is not None else 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns for the given parent index.

        Args:
            parent: The parent index to count columns for. If invalid, it
                counts columns for the root data source.

        Returns:
            The number of columns for the given parent index.
        """

        return (
            self.item_from_index(parent).column_count() if self._root is not None else 0
        )

    def index(
        self, row: int, column: int, parent: QModelIndex = QModelIndex()
    ) -> QModelIndex:
        """Return the index for the given row and column under the specified parent.

        Args:
            row: The row index.
            column: The column index.
            parent: The parent index to create the index under. If invalid,
                it creates an index for the root data source.

        Returns:
            A `QModelIndex` representing the specified row and column under the parent.
        """

        if not self._root or not self.hasIndex(row, column, parent):
            return QModelIndex()

        parent_item = self.item_from_index(parent)
        child_item = parent_item.child(row)

        return (
            self.createIndex(row, column, child_item) if child_item else QModelIndex()
        )

    def hasChildren(self, parent: QModelIndex = QModelIndex()) -> bool:
        """Check if the given parent index has children.

        Args:
            parent: The parent index to check. If invalid, it checks
                for the root data source.

        Returns:
            True if the parent index has children, False otherwise.
        """

        return (
            self.item_from_index(parent).has_children()
            if self._root is not None
            else super().hasChildren(parent)
        )

    def parent(self, index: QModelIndex) -> QModelIndex:
        """Return the parent index of the given index.

        Args:
            index: The `QModelIndex` to retrieve the parent for.

        Returns:
            The parent index of the given index, or an invalid index if
            the index has no parent.
        """

        if not index.isValid() or self._root is None:
            return QModelIndex()

        child_item: BaseDataSource = index.internalPointer()
        parent_item = child_item.parent_source()

        if parent_item is None or parent_item == self._root:
            return QModelIndex()

        return self.createIndex(parent_item.index(), 0, parent_item)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: Qt.ItemDataRole = Qt.DisplayRole,
    ) -> Any:
        """Return the header data for the given section and orientation.

        Args:
            section: The section index.
            orientation: The orientation of the header (horizontal or vertical).
            role: The role of the header data. Defaults to `Qt.DisplayRole`.

        Returns:
            The header data for the given section and orientation.
        """

        if orientation != Qt.Horizontal:
            return None

        if role == Qt.DisplayRole:
            return self.root().header_text(section)
        elif role == Qt.DecorationRole:
            icon = self.root().header_icon()
            return icon.pixmap(icon.availableSizes()[-1]) if not icon.isNull else None

        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag | Qt.ItemFlags:
        """Return the flags for the given index.

        Args:
            index: The `QModelIndex` to retrieve flags for.

        Returns:
            The flags associated with the given index.
        """

        if not index.isValid() or self._root is None:
            return Qt.ItemIsDropEnabled

        item: BaseDataSource = index.internalPointer()
        column = index.column()

        flags = Qt.ItemIsEnabled
        if item.supports_drag(column):
            flags |= Qt.ItemIsDragEnabled
        if item.supports_drop(column):
            flags |= Qt.ItemIsDropEnabled
        if item.is_editable(column):
            flags |= Qt.ItemIsEditable
        if item.is_selectable(column):
            flags |= Qt.ItemIsSelectable
        if item.is_enabled(column):
            flags |= Qt.ItemIsEnabled
        if item.is_checkable(column):
            flags |= Qt.ItemIsUserCheckable

        return flags

    def canFetchMore(self, parent: QModelIndex) -> bool:
        """Check if more data can be fetched for the given parent index.

        Args:
            parent: The parent index to check.

        Returns:
            True if more data can be fetched, False otherwise.
        """

        if not parent.isValid():
            return False

        item = self.item_from_index(parent)
        return item.can_fetch_more() if item is not None else False

    def fetchMore(self, parent: QModelIndex):
        """Fetch more data for the given parent index.

        Args:
            parent: The parent index to fetch more data for.
        """

        if not parent.isValid():
            return

        item = self.item_from_index(parent)
        item.fetch_more() if item is not None else None

    def data(self, index: QModelIndex, role: Qt.DisplayRole = Qt.DisplayRole) -> Any:
        """Return the data for the given index and role.

        Args:
            index: The `QModelIndex` to retrieve data for.
            role: The role of the data to retrieve. Defaults to `Qt.DisplayRole`.

        Returns:
            The data associated with the given index and role, or None if
            the index is invalid or the role is not supported.
        """

        if not index.isValid() or self._root is None:
            return None

        item: BaseDataSource = index.internalPointer()
        column = index.column()

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return item.data(column)
        elif role == Qt.ToolTipRole:
            return item.tooltip(column)
        elif role == Qt.DecorationRole:
            return item.icon(column)
        elif role == Qt.CheckStateRole and item.is_checkable(column):
            return Qt.Checked if item.data(column) else Qt.Unchecked
        elif role == Qt.BackgroundRole:
            return item.background_color(column)
        elif role == Qt.ForegroundRole:
            return item.foreground_color(column)
        elif role == Qt.TextAlignmentRole:
            return item.alignment(column)
        elif role == Qt.FontRole:
            return item.font(column)
        elif role == roles.TEXT_MARGIN_ROLE:
            return item.text_margin(column)
        elif role in (roles.SORT_ROLE, roles.FILTER_ROLE):
            return item.data(column)
        elif role == roles.ENUMS_ROLE:
            return item.enums(column)
        elif role == roles.USER_OBJECT_ROLE:
            return item
        elif role == roles.UID_ROLE:
            return item.uid
        elif role in item.custom_roles(column):
            return item.data_by_role(column, role)

        return None

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = Qt.EditRole
    ) -> bool:
        """Set the data for the given index and role.

        Args:
            index: The `QModelIndex` to set data for.
            value: The value to set.
            role: The role of the data to set. Defaults to `Qt.EditRole`.

        Returns:
            True if the data was set successfully, False otherwise.
        """

        if not index.isValid() or self._root is None:
            return False

        item: BaseDataSource = index.internalPointer()
        column = index.column()

        has_changed = False

        if role == Qt.EditRole:
            has_changed = item.set_data(column, value)
        elif role == Qt.ToolTipRole:
            has_changed = item.set_tooltip(column, value)
        elif role in item.custom_roles(column):
            has_changed = item.set_data_by_custom_role(column, role, value)

        if has_changed:
            # noinspection PyUnresolvedReferences
            QtCompat.dataChanged(self, index, index, [role])

        return has_changed

    def supportedDropActions(self) -> Qt.DropAction | Qt.DropActions:
        """Return the supported drop actions for the model.

        Returns:
            The supported drop actions.
        """

        return Qt.CopyAction | Qt.MoveAction

    def mimeTypes(self) -> list[str]:
        """Return the MIME types supported by the model for drag and drop.

        Returns:
            A list of supported MIME types.
        """

        return ["application/x-datasource"]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData | None:
        """Return the MIME data for the given indexes.

        Args:
            indexes: A list of `QModelIndex` objects to create MIME data for.

        Returns:
            The MIME data containing the data sources from the given indexes.
        """

        data: list[Any] = []
        for i in indexes:
            item = self.item_from_index(i)
            item_data = item.mime_data(i.column())
            if item_data:
                data.append(item_data)

        mime_data = QMimeData()
        if data:
            mime_data.setData("application/x-datasource", pickle.dumps(data))

        return mime_data

    def dropMimeData(
        self,
        mime_data: QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex = QModelIndex(),
    ) -> bool:
        """Handle dropping MIME data into the model.

        Args:
            mime_data: The `QMimeData` containing the data to drop.
            action: The drop action (copy or move).
            row: The row index to drop the data at.
            column: The column index to drop the data at.
            parent: The parent index to drop the data under. If invalid,
                it drops under the root data source.

        Returns:
            True if the drop was successful, False otherwise.
        """

        if action == Qt.IgnoreAction:
            return False

        if not mime_data.hasFormat("application/x-datasource"):
            return super(TreeModel, self).dropMimeData(
                mime_data, action, row, column, parent
            )
        data = bytes(mime_data.data("application/x-datasource"))
        items = pickle.loads(data)
        if not items:
            return False

        drop_parent = self.item_from_index(parent)
        return_kwargs = drop_parent.drop_mime_data(items, action)
        if not return_kwargs:
            return False

        self.insertRows(row, len(items), parent, **return_kwargs)
        if action == Qt.CopyAction:
            return False

        return True

    def insertRow(
        self, row: int, parent: QModelIndex = QModelIndex(), **kwargs
    ) -> bool:
        """Insert a new row at the specified position under the given parent.

        Args:
            row: The row index to insert at.
            parent: The parent index to insert the row under. If invalid,
                it inserts under the root data source.

        Returns:
            True if the row was inserted successfully, False otherwise.
        """

        parent_item = self.item_from_index(parent)
        row = max(0, min(parent_item.row_count(), row))
        self.beginInsertRows(parent, row, row)
        parent_item.insert_row_data_source(row, **kwargs)
        self.endInsertRows()

        return True

    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex(), **kwargs
    ) -> bool:
        """Insert multiple rows at the specified position under the given parent.

        Args:
            row: The row index to start inserting at.
            count: The number of rows to insert.
            parent: The parent index to insert the rows under. If invalid,
                it inserts under the root data source.

        Returns:
            True if the rows were inserted successfully, False otherwise.
        """

        parent_item = self.item_from_index(parent)
        row = max(0, min(parent_item.row_count(), row))
        last_row = max(0, row + count - 1)

        self.beginInsertRows(parent, row, last_row)
        parent_item.insert_row_data_sources(row, count, **kwargs)
        self.endInsertRows()

        return True

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        """Remove a row at the specified position under the given parent.

        Args:
            row: The row index to remove.
            parent: The parent index to remove the row from. If invalid,
                it removes from the root data source.

        Returns:
            True if the row was removed successfully, False otherwise.
        """

        return self.removeRows(row, 1, parent)

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex(), **kwargs
    ) -> bool:
        """Remove multiple rows at the specified position under the given parent.

        Args:
            row: The row index to start removing from.
            count: The number of rows to remove.
            parent: The parent index to remove the rows from. If invalid,
                it removes from the root data source.

        Returns:
            True if the rows were removed successfully, False otherwise.
        """

        parent_item = self.item_from_index(parent)
        row = max(0, min(parent_item.row_count(), row))
        last_row = max(0, row + count - 1)

        self.beginRemoveRows(parent, row, last_row)
        result = parent_item.remove_row_data_sources(row, count, **kwargs)
        self.endRemoveRows()

        return result

    def moveRow(
        self,
        source_parent: QModelIndex,
        source_row: int,
        destination_parent: QModelIndex,
        destination_child_row: int,
    ) -> bool:
        """Move a row from one parent to another.

        Args:
            source_parent: The parent index of the source row.
            source_row: The row index to move.
            destination_parent: The parent index to move the row to.
            destination_child_row: The child row index to insert the moved row at.

        Returns:
            True if the row was moved successfully, False otherwise.
        """

        return self.moveRows(
            source_parent, source_row, 1, destination_parent, destination_child_row
        )

    def moveRows(
        self,
        source_parent: QModelIndex,
        source_row: int,
        count: int,
        destination_parent: QModelIndex,
        destination_child_row: int,
    ) -> bool:
        """Move multiple rows from one parent to another.

        Args:
            source_parent: The parent index of the source rows.
            source_row: The starting row index to move.
            count: The number of rows to move.
            destination_parent: The parent index to move the rows to.
            destination_child_row: The child row index to insert the moved rows at.

        Returns:
            True if the rows were moved successfully, False otherwise.
        """

        indices: list[QModelIndex] = []
        for i in range(source_row, source_row + count):
            child_index = self.index(i, 0, parent=source_parent)
            if child_index.isValid():
                indices.append(child_index)
        mime_data = self.mimeData(indices)
        self.removeRows(source_row, count, parent=source_parent)
        self.dropMimeData(
            mime_data, Qt.MoveAction, destination_child_row, 0, destination_parent
        )

        return True

    def root(self) -> BaseDataSource | None:
        """The root data source of the model."""

        return self._root

    def set_root(self, root: BaseDataSource | None, refresh: bool = False):
        """Set the root data source of the model.

        Args:
            root: The new root data source to set.
            refresh: If True, the model will be refreshed after setting
                the root.
        """

        self._root = root
        if self._root:
            self._root.model = self

        if refresh:
            self.reload()

    def reload(self):
        """Hard reload the model. This can be useful when the data source
        tree structure has already been rebuilt and calling `insertRows`
        would create duplicates.
        """

        self.modelReset.emit()

    def item_from_index(self, index: QModelIndex) -> BaseDataSource | None:
        """Return the data source from the given index.

        Args:
            index: The `QModelIndex` to retrieve the data source from.

        Returns:
            The data source associated with the given index, or the root
            data source if the index is invalid.
        """

        return index.data(roles.USER_OBJECT_ROLE) if index.isValid() else self._root

    def print_tree(self, item: BaseDataSource | None = None):
        """Print the tree structure of the model starting from the given item.

        Args:
            item: The item to start printing from. If None, it starts from
                the root.
        """

        def _print_tree(
            _item: BaseDataSource,
            _prefix: str = "",
            _last: bool = True,
        ):
            """Recursive function to print the tree structure of the model.

            Args:
                _item: The current item to print.
                _prefix: The prefix string for the current level of the tree.
                _last: A boolean indicating if the current item is the last
                    child of its parent.
            """

            tree_separator = "`- " if _last else "|- "
            values = [_prefix, tree_separator] + [
                _item.data(0) if not _item.is_root() else "root"
            ]
            msg = "".join(values)
            print(msg)
            _prefix += "   " if _last else "|  "
            child_count = item.row_count()
            for i, child in enumerate(_item.children):
                _last = i == (child_count - 1)
                _print_tree(child, _prefix, _last)

        _print_tree(item or self._root)
