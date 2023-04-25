#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains base classes for Qt models
"""

from Qt.QtCore import Qt, Signal, QObject, QModelIndex, QItemSelection, QAbstractListModel, QAbstractTableModel
from Qt.QtCore import QAbstractItemModel

import tpDcc as tp
from tpDcc.libs.qt.core import qtutils


class ItemSelection(QItemSelection):
    """
    Extends QItemSelection functionality for view items
    """

    def __init__(self, *args):
        super(ItemSelection, self).__init__(*args)

    def indexes(self):
        """
        Override QItemSelection indexes() method

        :warning: Specific to Qt 4.7.0 the QModelIndexList destructor will cause a destructor crash.
            This method avoids that crash by overriding the indexes() method and manually building
            the index list with a python builtin list.
        :seealso: http://www.qtcentre.org/threads/16933
        :return: list<QModelIndex>, list of model indexes corresponding to the selected items
        """

        indexes = list()
        for i in range(self.count()):
            parent = self[i].parent()
            for c in range(self[i].left(), self[i].right() + 1):
                for r in range(self[i].top(), self[i].bottom() + 1):
                    indexes.append(self[i].model().index(r, c, parent))

        return indexes


class ListModel(QAbstractListModel, object):
    def __init__(self, data=None, parent=None):
        """
        Basic model for string lists
        :param data: list<string>, list of string items to add to the model
        :param parent: QWidget
        """

        if data is None:
            data = list()

        super(ListModel, self).__init__(parent=parent)
        self._items = data

    def headerData(self):
        return None

    def rowCount(self, parent=QModelIndex()):
        """
        Returns the length of the internal collection item list
        """

        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        """
        Returns the number of columns in this model
        """

        return 1

    def flags(self, index):
        """
        Gets the Qt.ItemFlags for the model data at a given index
        :param index: int, lookup key for the data
        :return: A valid combination of the Qt.Flags enum
        """

        # return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.item(index)

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets the model data at a given index, filtered by the given role to the value
        """

        return False

    def insertRows(self, position, rows, parent=QModelIndex()):
        """
        Inserts a row with empty AbstractDataItems into the model
        """

        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            self._items.insert(position, 'test')
        self.endInsertRows()

        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        """
        Removes a row from the model
        """

        self.beginRemoveRows(parent, position, position + rows - 1)
        for i in range(rows):
            value = self._items[position]
            self._items.remove(value)
        self.endRemoveRows()
        return True

    def clear(self):
        """
        Clears all data model
        """

        try:
            self._items.clear()
        except Exception:
            del self._items[:]

    def item(self, index):
        """
        Returns the internal data item given the index
        :param index: int, QModelIndex representing the index
        :return: item if the index is valid, None otherwise
        """

        if isinstance(index, (int, long)):
            return self._items[index]

        if isinstance(index, QModelIndex) and index.isValid():
            item = index.internalPointer()
            if item:
                return item
            return self._items[index.row()]

        return None

    def set_items(self, items):
        """
        Clears current model items and adds new ones
        :param items: list<string>, items to add to the model
        """

        self.clear()
        for item in items:
            self.append_item(item)

    def append_item(self, item):
        """
        Appends an existing AbstractDataItem into the model
        :param item: AbstractDataItem
        :return: bool
        """

        next_index = self.rowCount()
        last_index = next_index
        self.beginInsertRows(QModelIndex(), next_index, last_index)
        self._item_insert(item)
        self.endInsertRows()
        return True

    def _item_insert(self, item=None):
        """
        Internal function that inserts an item into the internal collection
        :param item: object, item to append to end of the internal collection
        """

        self._items.append(item)

    def _item_insert_position(self, item, index):
        """
        Internal item insert at specific index position
        :param item: object, item to append to end of the internal collection
        :param index: int, internal index of the item in the internal collection
        """

        self._items.insert(index, item)

    def _item_remove(self, item):
        """
        Internal item removal
        :param item: the item to remove from the internal collection
        """

        try:
            self._items.remove(item)
        except ValueError:
            pass

    def _item_remove_position(self, index):
        """
        Internal remove item at specific index position in the internal collection
        :param index: int, index of the item to remove from the internal collection
        """

        try:
            item = self._items.pop(index)
        except IndexError:
            pass


class TableModel(QAbstractTableModel, object):
    def __init__(self, data=[], horizontal_headers=[], vertical_headers=[], parent=None):
        """
        Basic model for table models
        :param data: list<list>, multi dimensional array in row-column order
        :param parent: QWidget
        """

        super(TableModel, self).__init__(parent=parent)
        self._items = data
        self._headers = {
            Qt.Horizontal: horizontal_headers,
            Qt.Vertical: vertical_headers
        }

    def headerData(self, section, orientation, role):

        if role != Qt.DisplayRole:
            return None

        header_data = self._headers.get(orientation, None)
        return header_data[section] if header_data else None

    def rowCount(self, parent=QModelIndex()):
        """
        Returns the length of the internal collection item list
        """

        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        """
        Returns the length of the first element of the internal collection item list
        """

        return len(self._headers[Qt.Horizontal])

    def flags(self, index):
        """
        Gets the Qt.ItemFlags for the model data at a given index
        :param index: int, lookup key for the data
        :return: A valid combination of the Qt.Flags enum
        """

        # return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def data(self, index, role):

        if role == Qt.DisplayRole:
            return self.item(index=index)

    def setData(self, index, value, role=Qt.EditRole):
        """
        Sets the model data at a given index, filtered by the given role to the value
        """

        return False

    def insertRows(self, position, rows, parent=QModelIndex()):
        """
        Inserts a new item into the table
        """

        self.beginInsertRows(parent, position, position + rows - 1)
        for i in range(rows):
            default_values = ['' for i in range(self.columnCount())]
            self._items.insert(position, default_values)
        self.endInsertRows()

        return True

    def insertColumns(self, position, columns, parent=QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        row_count = len(self._items)
        for i in range(columns):
            for j in range(row_count):
                self._items[j].insert(position, '')
        self.endInsertColumns()

        return True

    def clear(self):
        """
        Clears all data model
        """

        try:
            self._items.clear()
        except Exception:
            del self._items[:]

    def item(self, index):
        """
        Returns the internal data item given the index
        :param index: int, QModelIndex representing the index
        :return: item if the index is valid, None otherwise
        """

        if isinstance(index, (int, long)):
            return self._items[index]

        if isinstance(index, QModelIndex) and index.isValid():
            item = index.internalPointer()
            if item:
                return item

            if len(self._items) > 0:
                return self._items[index.row()][index.column()]
        return None

    def set_items(self, items):
        """
        Clears current model items and adds new ones
        :param items: list<list>, items to add to teh model
        """

        self.clear()
        for item in items:
            self.append_item(item=item)

    def append_item(self, item):
        """
        Appends an existing AbstractDataItem into the model
        :param item: AbstractDataItem
        :return: bool
        """

        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._item_insert(item)
        self.endInsertRows()

        return True

    def _item_insert(self, item):
        """
        Internal function that inserts an item into the internal collection
        :param item: object, item to append to end of the internal collection
        """

        self._items.append(item)

    def _item_insert_position(self, item, index):
        """
        Internal item insert at specific index position
        :param item: object, item to append to end of the internal collection
        :param index: int, internal index of the item in the internal collection
        """

        self._items.insert(index, item)


class BaseTreeItem(QObject):

    childAdded = Signal(object)
    childRemoved = Signal(object)

    if qtutils.is_pyside2():
        dataChanging = Signal(object, object, object)
        dataChanged = Signal(object, object, object)
    else:
        dataChanging = Signal(object, object)
        dataChanged = Signal(object, object)

    def __init__(self, data, parent=None):
        self._item_data = data or list()
        self._child_items = list()
        super(BaseTreeItem, self).__init__(parent)

    def data(self, column):
        return self._item_data[column]

    def set_data(self, column, value):
        if column <= 0 or column >= len(self._item_data):
            return False

        self._item_data[column] = value

        return True

    def row(self):
        """
        Returns the row index of this item within the parent's child collection
        :return: QModelIndex, the respective index if parent is valid; O otherwise
        """

        if self.parent():
            return self.parent().child_index(self)

        return 0

    def column(self):
        """
        Returns the column index of this item within the parent's child collection
        :return: QModelIndex, the respective index if the parent is valid; 0 otherwise
        """

        return 0

    def data(self, column):
        """
        Gets the data in the given column
        :param column: int
        :return: variant
        """

        return self._item_data[column]

    def flags(self, column):
        """
        Get the Qt.ItemFlags for the model data at a given index
        :return: A valid combination of the QtCore.Qt.QFlags enum.
        """

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def column_count(self):
        """
         Returns number of columns stored at this item
         :return: int, number of columns at this item
         """

        return len(self._item_data)

    def row_count(self):
        """
        Returns number of rows stored at this item
        :return: int, number of rows at this item
        """

        return len(self._child_items)

    def child(self, row):
        """
        Returns the child BaseTreeItem at the given row index
        :param row: int, index into the list of children
        :return: BaseTreeItem, respective item if row is valid; None otherwise
        """

        return self._child_items[row] if 0 <= row < len(self._child_items) else None

    def has_children(self):
        """
        Returns whether or not this item has children
        :return: bool
        """

        return bool(self._child_items)

    def child_count(self):
        """
        Returns the number of children this item has
        :return: int, number of children this item has
        """

        return len(self._child_items)

    def child_index(self, child):
        """
        Returns the index of the given item in the internal list of children of this item
        :param child: BaseTreeItem, item in the list of children
        :return: int, lowest index in collection that item appears
        """

        return self._child_items.index(child)

    def is_root(self):
        """
        Returns whether or not current node is a root one (has no parents)
        :return: bool
        """

        return not bool(self.parent())

    def append_child(self, item):
        """
        Appends a child item to the internal collection of children
        :return: object, item to append
        """

        self._child_items.append(item)
        item.setParent(self)
        self.childAdded.emit(item)

    def insert_child(self, position, item):
        """
        Inserts a child item into the internal collection of children
        :param position: int, position to insert item into
        :param item: object, item to insert
        """

        if position < 0 or position > len(self._child_items):
            return False

        self._child_items.insert(position, item)
        item.setParent(self)
        self.childAdded.emit(item)

    def remove_child(self, item):
        """
        Removes an item from the children list
        :param item: object, item to remove
        """

        return self.remove_index(self.child_index(item))

    def remove(self):
        """
        Removes current item from its parent
        """

        if self.parent():
            self.parent().remove_child(self)
        for child in self._child_items:
            self.remove_child(child)

    def clear(self):
        """
        Clears all data from the item (and its children)
        """

        for child in self._child_items:
            child.clear()
        self.clear()


class TreeModel(QAbstractItemModel, object):
    def __init__(self, header_data=['']):
        self._root = self._create_root(header_data)
        super(TreeModel, self).__init__()

    # =================================================================================================================
    # OVERRIDES
    # =================================================================================================================

    def columnCount(self, parent=QModelIndex()):
        """
        Overrides columnCount base function
        Returns the number of columns in the model
        :param parent: QModelIndex
        :return: int
        """

        parent_item = self.item(parent)
        return parent_item.column_count()

    def rowCount(self, parent=QModelIndex()):
        """
        Overrides rowCount base function
        Returns the number of rows in this model
        :param parent: QModelIndex
        :return: int
        """

        parent_item = self.item(parent)
        return parent_item.row_count()

    def data(self, index, role):
        """
        Overrides base data function
        Returns the model data for the given index, filtered by the given role
        :param index: QModelIndex
        :param role: QtRole
        :return: variant
        """

        if not index.isValid():
            return None

        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None

        item = self.item(index)
        return item.data(index.column()) if item else None

    def setData(self, index, value, role=Qt.EditRole):
        """
        Overrides setData base function
        Sets the model data at a given index, filtered by the given role to the value
        :param index: QModelIndex
        :param value: variant
        :param role: QtRole
        """

        if role != Qt.EditRole:
            return False

        item = self.item(index)
        if not item:
            return False

        res = item.set_data(index.column(), value)
        if not res:
            return False

        self.dataChanged.emit(index, value)

        return res

    def flags(self, index):
        """
        Overrides flags base function
        Get the Qt.ItemFlags for the model data at a given index
        :param index: int, lookup key to the data
        :return: A valid combination of the Qt.QFlags enum
        """

        if not index.isValid():
            return 0

        item = self.item(index)
        if item:
            return item.flags(index.column())

        return Qt.NoItemFlags

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        """
        Overrides headerData base function
        Returns the header dat for this model
        """

        if orientation == Qt.Horizontal and role == Qt.DisplayRole and self._root:
            return self._root.data(section)

        return None

    def index(self, row, column, parent=QModelIndex()):
        """
        Returns the index of the internal data item in the model specified by the given row, column and parent index
        :param row: int, row index into the model
        :param column: int column index into the model
        :param parent: QModelIndex, option parent QModelIndex
        :return: QModelIndex, QModelIndex of the lookuo operation
        """

        if not self.hasIndex(row, column, parent) or (parent.isValid() and parent.column() != 0):
            return QModelIndex()

        parent_item = self.item(parent)
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def insertRows(self, position, rows, parent=QModelIndex()):
        """
        Inserts a new BaseTreeItem into the model
        :param position: int, position to insert the row
        :param rows: int, number of rows to insert
        :param parent: QModelIndex, index of the parent item in the model
        :return: bool, True if the insertion was successful; False otherwise
        """

        parent_item = self.item(parent)
        end_index = position + rows
        next_index = position
        last_index = end_index - 1
        self.beginInsertRows(parent, next_index, last_index)
        for i in range(next_index, end_index):
            self._item_insert(parent_item, self.create_item(parent_item), i)
        self.endInsertRows()

        return True

    def removeRows(self, position, rows, parent=QModelIndex()):
        """
        Removes BaseTreeItem from the model
        :param position: int, position to remove the row
        :param rows: int, number of rows to remove
        :param parent: QModelIndex, index of the parent item in the model
        :return: bool, True if the removal was successful; False otherwise
        """

        parent_item = self.item(parent)
        end_index = position + rows
        next_index = position
        last_index = end_index - 1
        self.beginRemoveRows(parent, next_index, last_index)
        for i in sorted(range(next_index, end_index), reverse=True):
            self._item_remove_position(parent_item, i)
        self.endRemoveRows()

        return True

    def insertColumns(self, position, columns, parent=QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        success = self.rootItem.insertColumns(position, columns)
        self.endInsertColumns()

        return success

    def removeColumns(self, position, columns, parent=QModelIndex()):
        self.beginRemoveColumns(parent, position, position + columns - 1)
        success = self.rootItem.removeColumns(position, columns)
        self.endRemoveColumns()

        if self.rootItem.columnCount() == 0:
            self.removeRows(0, self.rowCount())

        return success

    # =================================================================================================================
    # BASE
    # =================================================================================================================

    def root(self):
        """
        Returns root item
        :return: BaseTreeItem
        """

        return self._root

    def create_item(self, *args):
        """
        Generates a new instance of the internal data root item wit the given arguments
        :param args: list, list or arguments to pass on the root item
        :return: BaseTreeItem, root item created
        """

        return BaseTreeItem(*args)

    def item(self, index):
        """
        Returns the internal data item given the index
        :param index: QModelIndex, QModelIndex representing the item
        :return: AbstractDataTreeItem, respective item if the index is valid; None otherwise
        """

        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self._root

    def item_index(self, item):
        """
        Returns the index for a given item
        :param item: BaseTreeItem, item already in the model
        :return: QModelIndex, lookup operation
        """

        if not item or item == self._root:
            return QModelIndex()

        return self.createIndex(item.row(), item.column(), item)

    def parent(self, index):
        """
        Overrides parent base function
        :param index: QModelIndex, QModelIndex to be used in lookup
        :return: QModelIndex, QModelIndex of the respective parent item
        """

        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()
        if parent_item is None or parent_item == self._root:
            return QModelIndex()

        return self.createIndex(parent_item.row(), parent_item.column(), parent_item)

    def append_item(self, item, parent=QModelIndex()):
        """
        Appends an existing AbstractDataTreeItem into the model
        :param item: AbstractDataTreeItem, item to insert
        :param parent: QModelIndex, index of the parent item in the model
        :return: bool, True if the insertion was successful; False otherwise
        """

        parent_item = self.item(parent)
        next_index = parent_item.child_count()
        last_index = next_index

        self.beginInsertRows(parent, next_index, last_index)

        self._item_insert(parent_item, item, next_index)

        self.endInsertRows()

        return self.item_index(item)

    def remove_item(self, item, parent=QModelIndex()):
        """
        Removes an existing AbstractDataTreeItem from the model
        :param item: AbstractDataTreeItem, item to remove
        :param parent: QModelIndex, index of the parent item in the model
        :return: bool, True if the removal was successful; False otherwise
        """

        return self.removeRows(item.row(), 1, parent)

    def clear(self):
        """
        Clears the model data
        """

        if self.hasChildren():
            self.removeRows(0, self.rowCount())

    def delete(self):
        """
        Prepares the model for destruction
        """

        self._root.clear()
        self.clear()

    # =================================================================================================================
    # INTERNAL
    # =================================================================================================================

    def _create_root(self, *args):
        """
        Internal function that creates a new instance of the internal data root item with the given arguments
        :param args: list, list of arguments to pass on the root item
        :return: BaseTreeItem
        """

        return BaseTreeItem(*args)

    def _item_changing(self, id, role):
        """
        Internal data item changed event handler
        """

        item = self.sender()
        index = self.createIndex(item.row(), id, item)

    def _item_changed(self, id, role):
        """
        Internal item changed event handler
        """

        item = self.sender()
        index = self.createIndex(item.row(), id, item)
        if qtutils.is_pyside2():
            self.dataChanged.emit(index, index, None)
        elif qtutils.is_pyside():
            self.dataChanged.emit(index, index)
        else:
            tp.logger.error('You have neither PySide or PySide2, that functionality is not supported!')

    def _item_append(self, parent, item):
        """
        Internal item append
        :param parent: BaseTreeItem, parent that will contain the item
        :param item: BaseTreeItem, item to append to end of the parent's internal collection
        """

        parent.append_child(item)
        item.setParent(parent)
        self._item_connect(item)

    def _item_insert(self, parent, item, position):
        """
        Internal item insert function
        :param parent: BaseTreeItem, parent that will contain the item
        :param item: BaseTreeItem, item to insert into parent's internal collection
        :param position: int, position of the item in the parent's internal collection
        """

        parent.insert_child(position, item)
        item.setParent(parent)
        self._item_connect(item)

    def _item_remove(self, parent, item):
        """
        Internal item removal function
        :param parent: AbstractDataTreeItem, parent from we want to remove item
        :param item: AbstractDataTreeItem, item we want to remove
        """

        parent.remove_child(item)
        item.setParent(None)
        self._item_disconnect(item)

    def _item_remove_position(self, parent, index):
        """
        Internal item removal at position function
        :param parent: AbstractDataTreeItem, parent from we want to remove item
        :param index: int, index of the chld we want to remove from parent's internal collection
        """

        item = parent.remove_index(index)
        item.setParent(None)
        self._item_disconnect(item)

    def _item_connect(self, item):
        """
        Internal item signal connection
        :param item: AbstractDataTreeItem, item we want to connect signals to
        """

        item.dataChanging.connect(self._item_changing)
        item.dataChanged.connect(self._item_changed)

    def _item_disconnect(self, item):
        """
        Internal item signal disconnection
        :param item: AbstractDataTreeItem, item we want to disconnect signals from
        """

        item.dataChanging.disconnect()
        item.dataChanged.disconnect()
