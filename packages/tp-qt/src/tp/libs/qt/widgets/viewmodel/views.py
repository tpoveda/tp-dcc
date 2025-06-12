from __future__ import annotations

import typing
from typing import Any

from Qt import QtCompat
from Qt.QtCore import (
    Qt,
    Signal,
    QPoint,
    QModelIndex,
    QItemSelectionModel,
    QItemSelection,
)
from Qt.QtWidgets import (
    QWidget,
    QLabel,
    QFrame,
    QTableView,
    QAbstractItemView,
    QHeaderView,
    QMenu,
)
from Qt.QtGui import QIcon

from tp.python import paths

from ... import uiconsts
from ..buttons import BaseButton
from ..search import SearchLineEdit
from ..comboboxes import BaseComboBox
from ..layouts import VerticalLayout, HorizontalLayout
from .models import (
    TableModel,
    TableFilterProxyModel,
    data_model_index_from_proxy_model_index,
)

if typing.TYPE_CHECKING:
    from .data import BaseDataSource, ColumnDataSource


class TableView(QTableView):
    """
    Custom QTableView class that defines the TableView.
    """

    contextMenuRequested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.setSortingEnabled(True)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.horizontalHeader().setStretchLastSection(True)
        # noinspection PyUnresolvedReferences
        QtCompat.setSectionResizeMode(
            self.verticalHeader(), QHeaderView.ResizeMode.ResizeToContents
        )
        self.sortByColumn(0, Qt.AscendingOrder)

        self.customContextMenuRequested.connect(self.contextMenuRequested.emit)


class TableViewWidget(QFrame):
    """
    Custom QFrame that extends QTableView functionality.
    """

    selectionChanged = Signal(object)
    contextMenuRequested = Signal(object, object)
    refreshRequested = Signal()

    def __init__(
        self,
        searchable: bool = False,
        manual_reload: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._model: TableModel | None = None
        self._row_data_source: BaseDataSource | None = None
        self._column_data_sources: list[ColumnDataSource] = []
        self._refreshing: bool = False

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

        self.set_searchable(searchable)
        self.set_allow_manual_refresh(manual_reload)

    @property
    def table_view(self) -> TableView:
        """
        Getter method that returns the internal TableView of the TableViewWidget.

        :return: TableView with the internal TableView.
        """

        return self._table_view

    def model(self) -> TableModel:
        """
        Returns the model of the TableViewWidget.

        :return: model used by the view.
        """

        # noinspection PyTypeChecker
        return self._table_view.model()

    def set_model(self, model: TableModel):
        """
        Sets the model of the TableViewWidget.

        :param model: sets the model used by this view.
        """

        self._model = model
        if self._row_data_source:
            self._row_data_source.model = model
        for i in iter(self._column_data_sources):
            i.model = model
        self._proxy_search.setSourceModel(model)
        self._proxy_search.setDynamicSortFilter(True)

    def selection_model(self) -> QItemSelectionModel:
        """
        Returns the selection model of the TableViewWidget.

        :return: QItemSelectionModel with the selection model of the TableViewWidget.
        """

        return self._table_view.selectionModel()

    def selected_rows(self) -> list[int]:
        """
        Returns the list of selected rows.

        :return: selected row indexes.
        """

        return list(set([i.row() for i in self.selection_model().selectedIndexes()]))

    def selected_columns(self) -> list[int]:
        """
        Returns the list of selected columns.

        :return: selected column indexes.
        """

        return list(set([i.column() for i in self.selection_model().selectedColumns()]))

    def selected_items(self) -> list[Any]:
        """
        Returns the list of selected items.

        :return: selected items.
        """

        indices = self.selection_model().selection()
        model_indices = self._proxy_search.mapSelectionToSource(indices).indexes()
        model = self._model

        return list(map(model.item_from_index, model_indices))

    def selected_rows_indexes(self) -> list[QModelIndex]:
        """
        Returns the list of selected rows indices.

        :return: selected row indices.
        """

        selected_rows = set([i.row() for i in self.selection_model().selectedIndexes()])
        indices: list[QModelIndex] = []
        for row in selected_rows:
            index, _ = data_model_index_from_proxy_model_index(
                self._model.index(row, 0)
            )
            indices.append(index)

        return sorted(indices, key=lambda x: x.row())

    def selected_indexes(self) -> list[QModelIndex]:
        """
        Returns the list of selected indices.

        :return: selected indices.
        """

        return self._proxy_search.mapSelectionToSource(
            self.selection_model().selection()
        ).indexes()

    def register_row_data_source(self, data_source: BaseDataSource):
        """
        Registers a row data source.

        :param data_source: BaseDataSource with the row data source to register.
        """

        self._row_data_source = data_source
        data_source.column_index = 0
        if hasattr(data_source, "delegate"):
            delegate = data_source.delegate(self._table_view)
            self._table_view.setItemDelegateForColumn(0, delegate)

        self._row_data_source.model = self._model
        self._model.row_data_source = data_source
        self._table_view.verticalHeader().sectionClicked.connect(
            self._row_data_source.on_vertical_header_selection
        )
        self._search_widget.set_visibility_items([self._row_data_source.header_text(0)])
        width = data_source.width()
        if width > 0:
            self._table_view.setColumnWidth(0, width)

    def register_column_data_sources(self, data_sources: list[ColumnDataSource]):
        """
        Registers a list of column data sources.

        :param data_sources: list of column data sources to register.
        :raises ValueError: If row data source is not assigned before columns.
        """

        if not self._row_data_source:
            raise ValueError("Must register row_data_source before columns.")

        self._column_data_sources = data_sources
        visited_items: list[str] = []
        for i in range(len(data_sources)):
            source = data_sources[i]
            source.model = self._model
            source._columnIndex = i + 1
            if hasattr(source, "delegate"):
                delegate = source.delegate(self._table_view)
                self._table_view.setItemDelegateForColumn(i + 1, delegate)
            visited_items.append(source.header_text(i))
            width = source.width()
            if width > 0:
                self._table_view.setColumnWidth(i + 1, width)

        self._model.column_data_sources = data_sources
        self._search_widget.set_visibility_items(
            [self._row_data_source.header_text(0)] + visited_items
        )

    def refresh(self):
        """
        Refresh the items of the TableViewWidget.
        """

        if self._refreshing:
            return

        self._refreshing = True
        try:
            self.refreshRequested.emit()
            row_data_source = self._model.row_data_source
            column_data_sources = self._model.column_data_sources
            header_items: list[str] = []
            for i in range(len(column_data_sources)):
                header_items.append(column_data_sources[i].header_text(i))
            self._search_widget.set_header_items(
                [row_data_source.header_text(0)] + header_items
            )
        finally:
            self._refreshing = False

    def set_searchable(self, flag: bool):
        """
        Sets the searchable flag of the TableViewWidget.

        :param flag: bool with the flag to set.
        """

        self._search_widget.setVisible(flag)

    def set_allow_manual_refresh(self, flag: bool):
        """
        Sets the manual refresh flag of the TableViewWidget.

        :param flag: bool with the flag to set.
        """

        self._reload_button.setVisible(flag)

    def set_drag_drop_mode(self, mode: QAbstractItemView.DragDropMode):
        """
        Sets the drag and drop mode of the TableViewWidget.

        :param mode: drag and drop mode to set.
        """

        self._table_view.setDragDropMode(mode)
        self._table_view.setDragEnabled(True)
        self._table_view.setDropIndicatorShown(True)
        self._table_view.setAcceptDrops(True)
        self._table_view.setDragDropOverwriteMode(False)
        self._table_view.setDefaultDropAction(Qt.MoveAction)

    def open_persistent_editor(self, index: QModelIndex):
        """
        Opens the persistent editor for the given index.

        :param index: QModelIndex with the index to open the persistent editor.
        """

        self._table_view.openPersistentEditor(index)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder):
        """
        Sorts the table by the given column and order.

        :param column: int with the column to sort.
        :param order: Qt.SortOrder with the order to sort.
        """

        self._table_view.sortByColumn(column, order)

    def _setup_widgets(self):
        """
        Internal function that sets up the widgets of the TableViewWidget.
        """
        self._table_view = TableView(parent=self)
        self._proxy_search = TableFilterProxyModel(parent=self)
        self._table_view.setModel(self._proxy_search)
        self._reload_button = BaseButton(
            button_icon=QIcon(
                paths.canonical_path("../../../resources/icons/reload_64.png")
            ),
            parent=self,
        )
        self._search_widget = ViewSearchWidget(parent=self)

    def _setup_layouts(self):
        """
        Internal function that sets up the layouts of the widget.
        """

        main_layout = VerticalLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        search_layout = HorizontalLayout()
        search_layout.setSpacing(0)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.addWidget(self._reload_button)
        search_layout.addStretch()
        search_layout.addWidget(self._search_widget)

        main_layout.addLayout(search_layout)
        main_layout.addWidget(self._table_view)

    def _setup_signals(self):
        """
        Internal function that sets up the signals of the widget.
        """

        selection_model = self.selection_model()
        selection_model.selectionChanged.connect(self._on_selection_changed)
        self._search_widget.columnFilterIndexChanged.connect(
            self._on_search_widget_column_filter_index_changed
        )
        self._search_widget.searchTextChanged.connect(
            self._proxy_search.setFilterRegularExpression
        )
        self._search_widget.columnVisibilityIndexChanged.connect(
            self._on_search_widget_column_visibility_index_changed
        )
        self._table_view.contextMenuRequested.connect(
            self._on_table_view_context_menu_requested
        )
        self._reload_button.clicked.connect(self._on_reload_button_clicked)

    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ):
        """
        Internal callback function that is called when the selection changes.

        :param selected: QItemSelection with the selected items.
        :param deselected: QItemSelection with the deselected items.
        """

        indexes = selected.indexes()
        self.selectionChanged.emit([self._model.item_from_index(i) for i in indexes])

    def _on_search_widget_column_filter_index_changed(self, index: int, text: str):
        """
        Internal callback function that is called when the column filter index changes.

        :param index: int with the index of the column.
        :param text: str with the text to filter.
        """

        self._proxy_search.setFilterKeyColumn(index)

    def _on_search_widget_column_visibility_index_changed(
        self, column: int, state: Qt.CheckState
    ):
        """
        Internal callback function that is called when the column visibility index changes.

        :param column: int with the column index.
        :param state: Qt.CheckState with the state of the checkbox.
        """

        self._table_view.setColumnHidden(column, state == Qt.Unchecked)

    def _on_table_view_context_menu_requested(self, position: QPoint):
        """
        Internal callback function that is called when the custom context menu is requested.

        :param position: QPoint with the position of the context menu.
        """

        menu = QMenu(parent=self)
        selection = self.selected_rows()
        if self._row_data_source:
            self._row_data_source.context_menu(selection, menu)
        self.contextMenuRequested.emit(selection, menu)
        menu.exec_(self._table_view.viewport().mapToGlobal(position))

    def _on_reload_button_clicked(self):
        """
        Internal callback function that is called when the reload button is clicked.
        """

        self.refresh()


class ViewSearchWidget(QWidget):
    """
    Custom QWidget that allow to visualize column/row view (such as tables).
    """

    columnVisibilityIndexChanged = Signal(int, int)
    columnFilterIndexChanged = Signal(int, int)
    searchTextChanged = Signal(str)
    searchTextCleared = Signal()

    def __init__(
        self, show_column_visibility_box: bool = True, parent: QWidget | None = None
    ):
        super().__init__(parent=parent)

        self._setup_widgets(show_column_visibility_box=show_column_visibility_box)
        self._setup_layouts()
        self._setup_signals()

    def set_header_visibility(self, state: bool):
        """
        Sets the visibility of the header combo box.

        :param state: bool with the state of the visibility.
        """

        self._search_label.setVisible(state)
        self._search_header_combo.setVisible(state)

    def set_header_items(self, items: list[str]):
        """
        Sets the items of the header combo box.

        :param items: list[str] with the items to set.
        """

        self._search_header_combo.clear()
        for item in items:
            self._search_header_combo.addItem(item, is_checkable=False)

    def set_visibility_items(self, items: list[str]):
        """
        Sets the visibility items of the header combo box.

        :param items: list[str] with the items to set.
        """

        self._show_column_visibility_combo.clear()
        for item in items:
            self._show_column_visibility_combo.addItem(item, is_checkable=True)

    def _setup_widgets(self, show_column_visibility_box: bool = True):
        """
        Internal function that sets up the widgets of the TableViewWidget.
        """

        self._search_label = QLabel("Search By:", parent=self)
        self._search_header_combo = BaseComboBox(parent=self)
        self._search_widget = SearchLineEdit(parent=self)
        self._search_widget.setMaximumHeight(self._search_header_combo.size().height())
        self._search_widget.setMinimumHeight(self._search_header_combo.size().height())

        self._show_column_visibility_combo: BaseComboBox | None = None
        if show_column_visibility_box:
            self._show_column_visibility_combo = BaseComboBox(parent=self)
            self._show_column_visibility_combo.setMinimumWidth(150)
            self._show_column_visibility_combo.checkStateChanged.connect(
                self._on_show_column_visibility_combo_check_state_changed
            )

    def _setup_layouts(self):
        """
        Internal function that sets up the layouts of the widget.
        """

        main_layout = HorizontalLayout()
        main_layout.setSpacing(uiconsts.SMALL_SPACING)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        if self._show_column_visibility_combo:
            main_layout.addWidget(self._show_column_visibility_combo)
        main_layout.addWidget(self._search_label)
        main_layout.addWidget(self._search_header_combo)
        main_layout.addWidget(self._search_widget)

    def _setup_signals(self):
        """
        Internal function that sets up the signals of the widget.
        """

        self._search_header_combo.itemSelected.connect(
            self.columnFilterIndexChanged.emit
        )
        self._search_widget.textChanged.connect(self.searchTextChanged.emit)

    def _on_show_column_visibility_combo_check_state_changed(
        self, index: int, state: bool
    ):
        """
        Internal callback function that is called when the check state of the column visibility combo changes.

        :param index: int with the index of the column.
        :param state: bool with the state of the checkbox.
        """

        self.columnVisibilityIndexChanged.emit(index, state)
