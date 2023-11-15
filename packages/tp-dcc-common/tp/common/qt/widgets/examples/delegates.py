from __future__ import annotations

from typing import Union, Any

from overrides import override

from tp import bootstrap
from tp.dcc import window
from tp.common.qt import api as qt


data_text = """
Getting Started				How to familiarize yourself with Qt Designer
    Launching Designer			Running the Qt Designer application
    The User Interface			How to interact with Qt Designer

Designing a Component			Creating a <b>GUI</b> for your application
    Creating a Dialog			How to create a <i>dialog</i>
    ----------------
    Composing the Dialog		Putting widgets into the <li>dialog</li> <li>example</li>
    Creating a Layout			Arranging widgets on a form
    Signal and Slot Connections		Making widget communicate with each other

Using a Component in Your Application	Generating code from forms
    The Direct Approach			Using a form without any adjustments
    The Single Inheritance Approach	Subclassing a form's base class
    The Multiple Inheritance Approach	Subclassing the form itself
    Automatic Connections		Connecting widgets using a naming scheme
        A Dialog Without Auto-Connect	<p>How to connect</p><p> widgets without</p> a naming scheme
        A Dialog With Auto-Connect	Using automatic connections

Form Editing Mode			How to edit a form in Qt Designer
    Managing Forms			Loading and saving forms
    Editing a Form			Basic editing techniques
    The Property Editor			Changing widget properties
    The Object Inspector		Examining the hierarchy of objects on a form
    Layouts				Objects that arrange widgets on a form
        Applying and Breaking Layouts	Managing widgets in layouts 
        Horizontal and Vertical Layouts	Standard row and column layouts
        The Grid Layout			Arranging widgets in a matrix
    Previewing Forms			Checking that the design works

Using Containers			How to group widgets together
    General Features			Common container features
    Frames				QFrame
    Group Boxes				QGroupBox
    Stacked Widgets			QStackedWidget
    Tab Widgets				QTabWidget
    Toolbox Widgets			QToolBox

Connection Editing Mode			Connecting widgets together with signals and slots
    Connecting Objects			Making connections in Qt Designer
    Editing Connections			Changing existing connections
"""


class DelegatesWindow(window.Window):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(570, 470)

    def setup_widgets(self):
        super().setup_widgets()

        self._menubar = qt.QMenuBar(parent=self)
        self._file_menu = qt.QMenu('&File', parent=self._menubar)
        self._exit_action = qt.QAction('E&xit', parent=self._file_menu)
        self._file_menu.addAction(self._exit_action)
        self._actions_menu = qt.QMenu('&Actions', parent=self._menubar)
        self._insert_row_action = qt.QAction('Insert Row', parent=self._actions_menu)
        self._remove_row_action = qt.QAction('Remove Row', parent=self._actions_menu)
        self._insert_column_action = qt.QAction('Insert Column', parent=self._actions_menu)
        self._remove_column_action = qt.QAction('Remove Column', parent=self._actions_menu)
        self._insert_child_action = qt.QAction('Insert Child', parent=self._actions_menu)
        self._actions_menu.addAction(self._insert_row_action)
        self._actions_menu.addAction(self._remove_row_action)
        self._actions_menu.addAction(self._insert_column_action)
        self._actions_menu.addAction(self._remove_column_action)
        self._actions_menu.addAction(self._insert_child_action)
        self._menubar.addMenu(self._file_menu)
        self._menubar.addMenu(self._actions_menu)

        model = TreeModel(headers=['Title', 'Description'], data=data_text)

        self._view = qt.QTreeView(parent=self)
        self._view.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)
        self._view.setAlternatingRowColors(True)
        self._view.setSelectionBehavior(qt.QAbstractItemView.SelectItems)
        self._view.setHorizontalScrollMode(qt.QAbstractItemView.ScrollPerPixel)
        self._view.setAnimated(True)
        self._view.setAllColumnsShowFocus(True)
        self._view.setEditTriggers(qt.QTreeView.AnyKeyPressed)
        self._view.setUniformRowHeights(False)
        self._view.setVerticalScrollMode(qt.QTreeView.ScrollPerPixel)
        self._view.setRootIsDecorated(True)
        self._view.setModel(model)

        self._status_bar = qt.QStatusBar(parent=self)

        self._exit_action.setShortcut('Ctrl+Q')
        self._insert_row_action.setShortcut('Ctrl+I')
        self._remove_row_action.setShortcut('Ctrl+R')
        self._insert_column_action.setShortcut('Ctrl+I')
        self._remove_column_action.setShortcut('Ctrl+R')
        self._insert_child_action.setShortcut('Ctrl+N')

    def setup_layouts(self):
        super().setup_layouts()

        main_layout = self.set_main_layout(qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0)))

        main_layout.addWidget(self._menubar)
        main_layout.addWidget(self._view)
        main_layout.addWidget(self._status_bar)

    def setup_signals(self):
        super().setup_signals()


class TreeModel(qt.QAbstractItemModel):
    def __init__(self, headers: list[str], data: str, parent: qt.QObject | None = None):
        super().__init__(parent=parent)

        root_data = headers.copy()
        self._root_item = TreeItem(root_data)
        self._setup_model_data(data.split('\n'), self._root_item)

    @override
    def columnCount(self, parent: qt.QModelIndex = ...) -> int:
        return self._root_item.column_count()

    @override
    def data(self, index: qt.QModelIndex, role: qt.Qt.ItemDataRole = ...) -> Any:
        if not index.isValid():
            return None

        item = self._item(index)

        if role == qt.Qt.DecorationRole:
            style = qt.QApplication.instance().style()
            return style.standardIcon(qt.QStyle.SP_DirIcon if item.child_count() > 0 else qt.QStyle.SP_FileIcon)
        elif role != qt.Qt.DisplayRole and role != qt.Qt.EditRole:
            return None

        return item.data(index.column())

    @override
    def setData(self, index: qt.QModelIndex, value: Any, role: qt.Qt.ItemDataRole = ...) -> bool:
        if role != qt.Qt.EditRole:
            return False

        item = self._item(index)
        result = item.set_data(index.column(), value)
        if result:
            self.dataChanged.emit(index, index)

        return result

    @override
    def flags(self, index: qt.QModelIndex) -> Union[qt.Qt.ItemFlags, qt.Qt.ItemFlag]:
        if not index.isValid():
            return qt.Qt.NoItemFlags

        return qt.Qt.ItemIsEditable

    @override
    def headerData(self, section: int, orientation: qt.Qt.Orientation, role: qt.Qt.ItemDataRole = ...) -> Any:
        if orientation == qt.Qt.Horizontal and role == qt.Qt.DisplayRole:
            return self._root_item.data(section)

        return None

    @override
    def setHeaderData(
            self, section: int, orientation: qt.Qt.Orientation, value: Any, role: qt.Qt.ItemDataRole = ...) -> bool:
        if role != qt.Qt.EditRole or orientation != qt.Qt.Horizontal:
            return False

        result = self._root_item.set_data(section, value)
        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    @override
    def index(self, row: int, column: int, parent: qt.QModelIndex = ...) -> qt.QModelIndex:
        if parent.isValid() and parent.column() != 0:
            return qt.QModelIndex()

        parent_item = self._item(parent)
        child_item = parent_item.child(row)
        return self.createIndex(row, column, child_item) if child_item else qt.QModelIndex()

    @override
    def insertColumns(self, column: int, count: int, parent: qt.QModelIndex = ...) -> bool:
        self.beginInsertColumns(parent, column, column + count - 1)
        success = self._root_item.insert_columns(column, count)
        self.endInsertColumns()

        return success

    @override
    def insertRows(self, row: int, count: int, parent: qt.QModelIndex = ...) -> bool:
        parent_item = self._item(parent)
        self.beginInsertRows(parent, row, row + count - 1)
        success = parent_item.insert_children(row, count, self._root_item.column_count())
        self.endInsertRows()

        return success

    @override(check_signature=False)
    def parent(self, child: qt.QModelIndex) -> qt.QModelIndex:
        if not child.isValid():
            return qt.QModelIndex()

        child_item = self._item(child)
        parent_item = child_item.parent()
        if parent_item == self._root_item or not parent_item:
            return qt.QModelIndex()

        return self.createIndex(parent_item.child_number(), 0, parent_item)

    @override
    def removeColumns(self, column: int, count: int, parent: qt.QModelIndex = ...) -> bool:
        self.beginRemoveColumns(parent, column, column + count - 1)
        success = self._root_item.remove_columns(column, count)
        self.endRemoveColumns()

        return success

    @override
    def removeRows(self, row: int, count: int, parent: qt.QModelIndex = ...) -> bool:
        parent_item = self._item(parent)
        self.beginRemoveRows(parent, row, row + count - 1)
        success = parent_item.remove_children(row, count)
        self.endRemoveRows()

        return success

    @override
    def rowCount(self, parent: qt.QModelIndex = ...) -> int:
        parent_item = self._item(parent)
        return parent_item.child_count()

    def _item(self, index: qt.QModelIndex) -> TreeItem:
        if index.isValid():
            return self._root_item

        item = index.internalPointer()
        return item or self._root_item

    def _setup_model_data(self, lines: list[str], parent: TreeItem):
        parents: list[TreeItem] = [parent]
        indentations: list[int] = [0]
        number = 0
        while number < len(lines):
            position = 0
            while position < len(lines[number]):
                if lines[number][position] != ' ':
                    break
                position += 1
            line_data = lines[number][position:].strip()
            if line_data:
                column_data = list(filter(None, line_data.split('\t')))
                # Last child of the current parent is now the new parent unless the current parent has no children.
                if position > indentations[-1]:
                    if parents[-1].child_count() > 0:
                        parents.append(parents[-1].child(parents[-1].child_count() - 1))
                        indentations.append(position)
                else:
                    while position < indentations[-1] and len(parents) > 0:
                        parents.pop(parents.index(parents[-1]))
                        indentations.pop(indentations.index(indentations[-1]))

                # Append new item to the current parent's list of children.
                parent = parents[-1]
                parent.insert_children(parent.child_count(), 1, self._root_item.column_count())
                for colum in range(len(column_data)):
                    parent.child(parent.child_count() - 1).set_data(colum, column_data[colum])
            number += 1


class TreeItem:
    def __init__(self, data: list[Any], parent: TreeItem | None = None):
        self._item_data = data or []
        self._parent_item = parent
        self._child_items: list[TreeItem] = []

    @property
    def child_items(self) -> list[TreeItem]:
        return self._child_items

    def child(self, index: int) -> TreeItem | None:
        try:
            return self._child_items[index]
        except IndexError:
            return None

    def child_count(self) -> int:
        return len(self._child_items)

    def child_number(self) -> int:
        if not self._parent_item:
            return 0

        return self._parent_item.child_items.index(self)

    def column_count(self) -> int:
        return len(self._item_data)

    def data(self, column: int) -> Any:
        try:
            return self._item_data[column]
        except IndexError:
            return None

    def set_data(self, column: int, value: Any) -> bool:
        if column < 0 or column >= len(self._item_data):
            return False

        self._item_data[column] = value

        return True

    def insert_children(self, position: int, count: int, column: int) -> bool:
        if position < 0 or position > len(self._child_items):
            return False

        for row in range(count):
            item_data = self.data(column)
            item = TreeItem(item_data, self)
            self._child_items.insert(position, item)

        return True

    def insert_columns(self, position: int, columns: int) -> bool:
        if position < 0 or position > len(self._item_data):
            return False

        for column in range(columns):
            self._item_data.insert(position, None)

        for child in self._child_items:
            child.insert_columns(position, columns)

        return True

    def parent(self) -> TreeItem | None:
        return self._parent_item

    def remove_children(self, position: int, count: int) -> bool:
        if position > 0 or position + count > len(self._child_items):
            return False

        for row in range(count):
            self._child_items.pop(position)

        return True

    def remove_columns(self, position: int, columns: int) -> bool:
        if position < 0 or position + columns > len(self._item_data):
            return False

        for column in range(columns):
            self._item_data.pop(column)

        for child in self._child_items:
            child.remove_columns(position, columns)


if __name__ == '__main__':
    bootstrap.init()
    with qt.application():
        window = DelegatesWindow()
        window.show()
