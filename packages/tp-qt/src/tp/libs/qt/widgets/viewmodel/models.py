from __future__ import annotations

import pickle
import typing
from typing import Any

from Qt import QtCompat
from Qt.QtCore import (
    Qt,
    QObject,
    QMimeData,
    QRegularExpression,
    QModelIndex,
    QAbstractTableModel,
    QAbstractItemModel,
    QAbstractProxyModel,
    QSortFilterProxyModel,
)

from . import roles

if typing.TYPE_CHECKING:
    from .data import BaseDataSourceType, ColumnDataSourceType


def data_model_from_proxy_model(
    proxy_model: QSortFilterProxyModel,
) -> TableModel | None:
    """
    Returns the root source data model from the given model.
    Useful when you have a stack of proxy models, and you want to retrieve the source model.

    :param proxy_model: proxy model to walk.
    :return: root data source item model.
    """

    if proxy_model is None:
        return None

    current_model = proxy_model
    while isinstance(current_model, QAbstractProxyModel):
        current_model = current_model.sourceModel()
        if not current_model:
            return None

    # noinspection PyTypeChecker
    return current_model


def data_model_index_from_proxy_model_index(
    model_index: QModelIndex,
) -> tuple[QModelIndex, QAbstractItemModel]:
    """
    Returns the index from the root data model by walking the proxy model stack (if present).
    If the given model index is not from a proxy model, then it will be immediately returned.

    :param model_index: model index from proxy model.
    :return: model index from root data model.
    """

    data_model = model_index.model()
    model_index_mapped = model_index
    while isinstance(data_model, QAbstractProxyModel):
        # noinspection PyUnresolvedReferences
        model_index_mapped = data_model.mapToSource(model_index_mapped)
        if not model_index_mapped.isValid():
            return model_index_mapped, data_model
        data_model = model_index_mapped.model()

    return model_index_mapped, data_model


class TableModel(QAbstractTableModel):
    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self._row_data_source: BaseDataSourceType | None = None
        self._column_data_sources: list[ColumnDataSourceType] = []

    @property
    def row_data_source(self) -> BaseDataSourceType | None:
        """
        Getter method that returns the row data source of the model.

        :return: row data source of the model.
        """

        return self._row_data_source

    @row_data_source.setter
    def row_data_source(self, value: BaseDataSourceType | None):
        """
        Setter method that sets the row data source of the model.

        :param value: row data source to set.
        """

        self._row_data_source = value

    @property
    def column_data_sources(self) -> list[ColumnDataSourceType]:
        """
        Getter method that returns the column data sources of the model.

        :return: column data sources of the model.
        """

        return self._column_data_sources

    @column_data_sources.setter
    def column_data_sources(self, value: list[ColumnDataSourceType]):
        """
        Setter method that sets the column data sources of the model.

        :param value: column data sources to set.
        """

        self._column_data_sources = value

    def rowCount(self, parent: QModelIndex = QModelIndex()):
        """
        Overrides `rowCount` method to return the number of rows of the given parent index.

        :param parent: parent index to get the number of rows for.
        :return: number of rows of the given parent index.
        """

        if (
            parent.column() > 0
            or not self._row_data_source
            or not self._column_data_sources
        ):
            return 0

        return self._row_data_source.row_count()

    def columnCount(self, parent: QModelIndex = QModelIndex()):
        """
        Overrides `columnCount` method to return the number of columns of the given parent index.

        :param parent: parent index to get the number of columns for.
        :return: number of columns of the given parent index.
        """

        if not self._row_data_source or not self._column_data_sources:
            print(self._column_data_sources)
            return 0

        return len(self._column_data_sources) + 1

    def data(self, index: QModelIndex, role: Qt.ItemDataRole = Qt.DisplayRole) -> Any:
        """
        Overrides `data` method to return the data for the given model index and role.

        :param index: model index to get data for.
        :param role: role to get data for.
        :return: data for the given model index and role.
        """

        if not index.isValid():
            return None

        column = int(index.column())
        row = int(index.row())
        data_source = self.data_source(column)
        if data_source is None:
            return None

        kwargs = {"index": row}
        if column != 0:
            kwargs["row_data_source"] = self._row_data_source

        role_to_func = {
            Qt.DisplayRole: data_source.data,
            Qt.EditRole: data_source.data,
            Qt.ToolTipRole: data_source.tooltip,
            Qt.DecorationRole: data_source.icon,
            roles.TEXT_MARGIN_ROLE: data_source.text_margin,
            roles.EDIT_CHANGED_ROLE: data_source.display_changed_color,
            Qt.TextAlignmentRole: data_source.alignment,
            Qt.FontRole: data_source.font,
            Qt.BackgroundRole: data_source.background_color,
            Qt.ForegroundRole: data_source.foreground_color,
        }
        func = role_to_func.get(role)

        if func is not None:
            # noinspection PyArgumentList
            return func(**kwargs)
        elif role == Qt.CheckStateRole and data_source.is_checkable(**kwargs):
            if data_source.data(**kwargs):
                return Qt.Checked
            return Qt.Unchecked
        elif role == roles.MIN_VALUE_ROLE:
            return data_source.minimum(**kwargs)
        elif role == roles.MAX_VALUE_ROLE:
            return data_source.maximum(**kwargs)
        elif role == roles.ENUMS_ROLE:
            return data_source.enums(**kwargs)
        elif role == roles.USER_OBJECT_ROLE:
            return data_source.user_object(row)
        elif role in data_source.custom_roles(**kwargs):
            return data_source.data_by_role(role=role, **kwargs)

    def setData(
        self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = Qt.EditRole
    ) -> bool:
        """
        Overrides `setData` method to set the data for the given model index and role.

        :param index: model index to set data for.
        :param value: value to set.
        :param role: role to set data for.
        :return: whether the data was set successfully or not.
        """

        if not index.isValid() or not self._row_data_source:
            return False

        if role == Qt.EditRole:
            column = index.column()
            row_data_source = self._row_data_source
            if column == 0:
                result = row_data_source.set_data(index.row(), value)
            else:
                result = self._column_data_sources[column - 1].set_data(
                    row_data_source, index.row(), value
                )
            if result:
                # noinspection PyUnresolvedReferences
                QtCompat.dataChanged(self, index, index)
                return True
        elif role == roles.ENUMS_ROLE:
            column = index.column()
            row_data_source = self._row_data_source
            if column == 0:
                result = row_data_source.set_enums(index.row(), value)
            else:
                result = self._column_data_sources[column - 1].set_enums(
                    row_data_source, index.row(), value
                )
            if result:
                # noinspection PyUnresolvedReferences
                QtCompat.dataChanged(self, index, index)
                return True

        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags | Qt.ItemFlag:
        """
        Overrides `flags` method to return the flags for the given model index.

        :param index: model index to get the flags for.
        :return: flags for the given model index.
        """

        row_data_source = self._row_data_source
        if not index.isValid():
            return (
                Qt.ItemIsDropEnabled
                if row_data_source.supports_drop(-1)
                else Qt.NoItemFlags
            )

        row = index.row()
        column = index.column()
        data_source = self.data_source(column)

        kwargs = {"index": row}
        if column != 0:
            kwargs["row_data_source"] = self._row_data_source
        flags = Qt.ItemIsEnabled
        if row_data_source.supports_drag(row):
            flags |= Qt.ItemIsDragEnabled
        if row_data_source.supports_drop(row):
            flags |= Qt.ItemIsDropEnabled
        if data_source.is_editable(**kwargs):
            flags |= Qt.ItemIsEditable
        if data_source.is_selectable(**kwargs):
            flags |= Qt.ItemIsSelectable
        if data_source.is_enabled(**kwargs):
            flags |= Qt.ItemIsEnabled
        if data_source.is_checkable(**kwargs):
            flags |= Qt.ItemIsUserCheckable

        return flags

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: Qt.ItemDataRole = Qt.DisplayRole,
    ) -> Any:
        """
        Overrides `headerData` method to return the header data for the given section, orientation and role.

        :param section: section to get the header data for.
        :param orientation: orientation to get the header data for.
        :param role: role to get the header data for.
        :return: header data for the given section, orientation and role.
        """

        if orientation == Qt.Horizontal:
            data_source = self.data_source(section)

            if role == Qt.DisplayRole:
                return data_source.header_text(section)
            elif role == Qt.DecorationRole:
                icon = data_source.header_icon()
                if icon.isNull:
                    return
                return icon.pixmap(icon.availableSizes()[-1])

        elif orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                return self._row_data_source.header_vertical_text(section)
            elif role == Qt.DecorationRole:
                icon = self._row_data_source.header_vertical_icon(section)
                if icon.isNull():
                    return
                return icon.pixmap(icon.availableSizes()[-1])

        return None

    def supportedDropActions(self) -> Qt.DropActions:
        """
        Overrides `supportedDropActions` method to return the supported drop actions.

        :return: supported drop actions.
        """

        return Qt.CopyAction | Qt.MoveAction

    def mimeTypes(self) -> list[str]:
        """
        Overrides `mimeTypes` method to return the supported MIME types.

        :return: supported MIME types.
        """

        return ["application/x-datasource"]

    def mimeData(self, indexes: list[QModelIndex]) -> QMimeData:
        """
        Overrides `mimeData` method to return the MIME data for the given indexes.

        :param indexes: indexes to get the MIME data for.
        :return: MIME data for the given indexes.
        """

        row_data_source = self._row_data_source
        visited = set()
        indexes = []
        for index in indexes:
            if index.row() in visited:
                continue
            visited.add(index.row())
            indexes.append(index)
        data = row_data_source.mime_data(indexes)
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
        parent: QModelIndex,
    ) -> bool:
        """
        Overrides `dropMimeData` method to handle the drop MIME data action.

        :param mime_data: MIME data to drop.
        :param action: drop action to handle.
        :param row: row to drop the MIME data at.
        :param column: column to drop the MIME data at.
        :param parent: parent index to drop the MIME data at.
        :return: whether the MIME data was dropped successfully or not.
        """

        if action == Qt.IgnoreAction:
            return False

        if not mime_data.hasFormat("application/x-datasource"):
            return super().dropMimeData(mime_data, action, row, column, parent)

        data = bytes(mime_data.data("application/x-datasource"))
        items = pickle.loads(data)
        if not items:
            return False

        row_data_source = self._row_data_source
        return_kwargs = row_data_source.drop_mime_data(items, action)
        if not return_kwargs:
            return False

        begin_row = row
        if row == -1:
            if parent.isValid():
                # Insert above the current row.
                begin_row = parent.row() + 1
            else:
                begin_row = self.rowCount(parent)

        # When dropping onto a row and between rows the parent is the row,
        # which isn't valid in tables since indexes don't have children in tables,
        # so insert to the rootIndex
        self.insertRows(begin_row, len(items), QModelIndex(), **return_kwargs)

        if action == Qt.CopyAction:
            # Do not delete, just copy over.
            return False

        return True

    # noinspection PyMethodOverriding
    def insertRow(self, row: int, parent: QModelIndex, **kwargs) -> bool:
        """
        Inserts a row at the given row index and parent index.

        :param row: row index to insert the row at.
        :param parent: parent index to insert the row at.
        :param kwargs: additional keyword arguments to pass to the data source.
        :return: whether the row was inserted successfully or not.
        """

        return self.insertRows(row, 1, parent, **kwargs)

    # noinspection PyMethodOverriding
    def insertRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex(), **kwargs
    ) -> bool:
        """
        Inserts rows at the given row index and parent index.

        :param row: row index to insert the rows at.
        :param count: number of rows to insert.
        :param parent: parent index to insert the rows at.
        :param kwargs: additional keyword arguments to pass to the data source.
        :return: whether the rows were inserted successfully or not.
        """

        if not self._row_data_source:
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        # noinspection PyArgumentList
        result = self._row_data_source.insert_row_data_sources(row, count, **kwargs)
        self.endInsertRows()

        return result

    def insertColumns(
        self, column: int, count: int, parent: QModelIndex = QModelIndex()
    ) -> bool:
        """
        Inserts columns at the given column index and parent index.

        :param column: column index to insert the columns at.
        :param count: number of columns to insert.
        :param parent: parent index to insert the columns at.
        :return: whether the columns were inserted successfully or not.
        """

        if not self._row_data_source:
            return False

        self.beginInsertColumns(parent, column, column + count - 1)
        result = self._row_data_source.insert_column_data_sources(column, count)
        self.endInsertColumns()

        return result

    def removeRow(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        """
        Removes a row at the given row index and parent index.

        :param row: row index to remove the row at.
        :param parent: parent index to remove the row at.
        :return: whether the row was removed successfully or not.
        """

        return self.removeRows(row, 1, parent)

    def removeRows(
        self, row: int, count: int, parent: QModelIndex = QModelIndex(), **kwargs
    ) -> bool:
        """
        Removes rows at the given row index and parent index.

        :param row: row index to remove the rows at.
        :param count: number of rows to remove.
        :param parent: parent index to remove the rows at.
        :param kwargs: additional keyword arguments to pass to the data source.
        :return: whether the rows were removed successfully or not.
        """

        if not self._row_data_source:
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        # noinspection PyArgumentList
        result = self._row_data_source.remove_row_data_sources(row, count, **kwargs)
        for column in self._column_data_sources:
            # noinspection PyArgumentList
            column.remove_row_data_sources(self._row_data_source, row, count, **kwargs)
        self.endRemoveRows()

        return result

    # noinspection PyMethodOverriding
    def removeColumn(self, column: int, parent: QModelIndex) -> bool:
        """
        Removes a column at the given column index and parent index.

        :param column: column index to remove the column at.
        :param parent: parent index to remove the column at.
        :return: whether the column was removed successfully or not.
        """

        return True

    # noinspection PyMethodOverriding
    def removeColumns(self, column: int, count: int, parent: QModelIndex) -> bool:
        """
        Removes columns at the given column index and parent index.

        :param column: column index to remove the columns at.
        :param count: number of columns to remove.
        :param parent: parent index to remove the columns at.
        :return: whether the columns were removed successfully or not.
        """

        return True

    def moveRow(
        self,
        source_parent: QModelIndex,
        source_row: int,
        destination_parent: QModelIndex,
        destination_child: int,
    ) -> bool:
        """
        Moves a row from the source parent to the destination parent.

        :param source_parent: source parent index to move the row from.
        :param source_row: source row index to move the row from.
        :param destination_parent: destination parent index to move the row to.
        :param destination_child: destination row index to move the row to.
        :return: whether the row was moved successfully or not.
        """

        return self.moveRows(
            source_parent,
            source_row,
            1,
            destination_parent,
            destination_child,
        )

    def moveRows(
        self,
        source_parent: QModelIndex,
        source_row: int,
        count: int,
        destination_parent: QModelIndex,
        destination_child: int,
    ) -> bool:
        """
        Moves rows from the source parent to the destination parent.

        :param source_parent: source parent index to move the rows from.
        :param source_row: source row index to move the rows from.
        :param count: number of rows to move.
        :param destination_parent: destination parent index to move the rows to.
        :param destination_child: destination row index to move the rows to.
        :return: whether the rows were moved successfully or not.
        """

        if not self._row_data_source:
            return False

        indices = []
        for i in range(source_row, source_row + count):
            child_index = self.index(i, 0, parent=source_parent)
            if child_index.isValid():
                indices.append(child_index)
        mime_data = self.mimeData(indices)
        self.removeRows(source_row, count, parent=source_parent)
        self.dropMimeData(
            mime_data, Qt.MoveAction, destination_child, 0, destination_parent
        )

        return True

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """
        Overrides `sort` method to sort the model by the given column and order.

        :param column: column to sort by.
        :param order: order to sort by.
        """

        self.layoutAboutToBeChanged.emit()
        if column == 0:
            self._row_data_source.sort(index=column, order=order)
        else:
            self._column_data_sources[column - 1].sort(
                row_data_source=self._row_data_source, index=column, order=order
            )
        self.layoutChanged.emit()

    def item_from_index(self, index: QModelIndex) -> BaseDataSourceType:
        """
        Returns the item from the given index.

        :param index: index to get the item from.
        :return: item from the given index.
        """

        return (
            index.data()
            if index.isValid()
            else self._row_data_source.user_object(index.row())
        )

    def data_source(self, index: int) -> BaseDataSourceType:
        """
        Returns the data source for the given index.
        If the index is 0, then the row data source will be returned; otherwise, the column data source will be returned.

        :param index: index to get the data source for.
        :return: data source for the given index.
        """

        return (
            self._row_data_source
            if index == 0
            else self._column_data_sources[index - 1]
        )

    def column_data_source(self, index: int) -> ColumnDataSourceType | None:
        """
        Returns the column data source for the given index.

        :param index: index to get the column data source for.
        :return: column data source for the given index.
        """

        if not self._column_data_sources:
            return

        return self._column_data_sources[index - 1]

    def reload(self):
        """
        Hard reloads the model.
        """

        self.modelReset.emit()


class TableFilterProxyModel(QSortFilterProxyModel):
    """
    Custom QSortFilterProxyModel class that defines a filter proxy model for table views with
    the following behaviour:
        - If a parent item does not match the filter, None of its children will be shown.
    """

    def __init__(self, parent: QObject | None = None):
        super().__init__(parent=parent)

        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.setDynamicSortFilter(True)
        self.setFilterKeyColumn(0)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        """Overrides `filterAcceptsRow` method to return whether the given row should be shown or not.

        :param source_row: row index to check if it should be shown or not.
        :param source_parent: parent index of the row to check if it should be shown or not.
        :returns: whether the given row should be shown or not.
        """

        search_exp = self.filterRegularExpression()
        search_exp.setPatternOptions(QRegularExpression.CaseInsensitiveOption)
        if not search_exp.isValid():
            return True

        # noinspection PyTypeChecker
        model = data_model_from_proxy_model(self.sourceModel())
        if not model:
            return True

        column = self.filterKeyColumn()
        if column == 0:
            data = model.row_data_source.data(source_row)
        else:
            data = model.column_data_sources[column - 1].data(
                model.row_data_source, source_row
            )
        if search_exp.match(str(data)).capturedStart() != -1:
            return True

        return False

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """
        Overrides `sort` method to sort the model by the given column and order.

        :param column: column to sort by.
        :param order: order to sort by.
        """

        # noinspection PyTypeChecker
        model = data_model_from_proxy_model(self.sourceModel())
        if not model:
            return

        self.layoutAboutToBeChanged.emit()
        if column == 0:
            model.row_data_source.sort(index=column, order=order)
        else:
            model.column_data_sources[column - 1].sort(
                row_data_source=model.row_data_source, index=column, order=order
            )
        self.layoutChanged.emit()
