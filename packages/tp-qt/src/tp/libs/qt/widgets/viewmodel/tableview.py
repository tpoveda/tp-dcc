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
from Qt.QtGui import QKeySequence, QKeyEvent

from tp.libs.qt import icons

from ... import uiconsts
from ..buttons import BaseButton
from ..search import SearchLineEdit
from ..comboboxes import BaseComboBox
from ..layouts import VerticalLayout, HorizontalLayout
from .models import TableModel, TableFilterProxyModel
from .modelutils import map_to_source_model

if typing.TYPE_CHECKING:
    from .data import BaseDataSource, ColumnDataSource


class TableView(QTableView):
    """Custom `QTableView` class that defines the `TableView`."""

    contextMenuRequested = Signal()
    copyRequested = Signal(object)
    pasteRequested = Signal(object)

    COPY_PASTE_SUPPORTED = False

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

    def keyPressEvent(self, event: QKeyEvent):
        """Overrides `QTableView.keyPressEvent` method to capture copy/paste events.

        Args:
            event: `QKeyEvent` with the event to process.
        """

        model = self.model()
        if not model or not self.COPY_PASTE_SUPPORTED:
            super().keyPressEvent(event)
            return

        selection = self.selectionModel().selectedRows()
        if event.matches(QKeySequence.Copy):
            self.copyRequested.emit(selection)
        elif event.matches(QKeySequence.Paste):
            self.pasteRequested.emit(selection)

        event.accept()


class TableViewWidget(QFrame):
    """Custom QFrame that extends QTableView functionality."""

    selectionChanged = Signal(object)
    contextMenuRequested = Signal(object, object)
    refreshRequested = Signal()

    def __init__(
        self,
        searchable: bool = False,
        manual_reload: bool = True,
        parent: QWidget | None = None,
    ) -> None:
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
        """The table view contained in the `TableViewWidget`."""

        return self._table_view

    def model(self) -> TableModel:
        """Return the model of the `TableViewWidget`.

        Returns:
            The model used by the view.

        """

        # noinspection PyTypeChecker
        return self._table_view.model()

    def set_model(self, model: TableModel) -> None:
        """Sets the model of the `TableViewWidget`.

        Args:
            model: `TableModel` to set as the model of the view.
        """

        self._model = model

        if self._row_data_source:
            self._row_data_source.model = model

        for i in iter(self._column_data_sources):
            i.model = model

        self._proxy_search.setSourceModel(model)
        self._proxy_search.setDynamicSortFilter(True)

    def selection_model(self) -> QItemSelectionModel:
        """Return the selection model of the `TableViewWidget`.

        Returns:
            `QItemSelectionModel` with the selection model of the
                `TableViewWidget`.
        """

        return self._table_view.selectionModel()

    def selected_rows(self) -> list[int]:
        """Return the list of selected rows.

        Returns:
            Selected row indexes.
        """

        return list(set([i.row() for i in self.selection_model().selectedIndexes()]))

    def selected_columns(self) -> list[int]:
        """Return the list of selected columns.

        Returns:
            Selected column indexes.
        """

        return list(set([i.column() for i in self.selection_model().selectedColumns()]))

    def selected_items(self) -> list[Any]:
        """Return the list of selected items.

        Returns:
            Selected items.
        """

        indices = self.selection_model().selection()
        model_indices = self._proxy_search.mapSelectionToSource(indices).indexes()
        model = self._model

        return list(map(model.item_from_index, model_indices))

    def selected_rows_indexes(self) -> list[QModelIndex]:
        """Returns the list of selected rows indices.

        Returns:
            Selected row indices.
        """

        selected_rows = set([i.row() for i in self.selection_model().selectedIndexes()])
        indices: list[QModelIndex] = []
        for row in selected_rows:
            index, _ = map_to_source_model(self._model.index(row, 0))
            indices.append(index)

        return sorted(indices, key=lambda x: x.row())

    def selected_indexes(self) -> list[QModelIndex]:
        """Return the list of selected indices.

        Returns:
            Selected indices.
        """

        return self._proxy_search.mapSelectionToSource(
            self.selection_model().selection()
        ).indexes()

    def register_row_data_source(self, data_source: BaseDataSource) -> None:
        """Registers a row data source.

        Args:
            data_source: `BaseDataSource` with the row data source to register.
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

    def register_column_data_sources(
        self, data_sources: list[ColumnDataSource]
    ) -> None:
        """Registers a list of column data sources.

        Args:
            data_sources: list of column data sources to register.

        Raises:
            ValueError: If the row data source is not assigned before columns.
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
        """Refresh the items of the `TableViewWidget`."""

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

    def set_searchable(self, flag: bool) -> None:
        """Sets the searchable flag of the `TableViewWidget`.

        Args:
            flag: bool with the flag to set.
        """

        self._search_widget.setVisible(flag)

    def set_allow_manual_refresh(self, flag: bool) -> None:
        """Sets the manual refresh flag of the `TableViewWidget`.

        Args:
            flag: bool with the flag to set.
        """

        self._reload_button.setVisible(flag)

    def set_drag_drop_mode(self, mode: QAbstractItemView.DragDropMode) -> None:
        """Sets the drag and drop mode of the `TableViewWidget`.

        Args:
            mode: `QAbstractItemView.DragDropMode` with the drag and drop
                mode to set.
        """

        self._table_view.setDragDropMode(mode)
        self._table_view.setDragEnabled(True)
        self._table_view.setDropIndicatorShown(True)
        self._table_view.setAcceptDrops(True)
        self._table_view.setDragDropOverwriteMode(False)
        self._table_view.setDefaultDropAction(Qt.MoveAction)

    def open_persistent_editor(self, index: QModelIndex) -> None:
        """Opens the persistent editor for the given index.

        Args:
            index: `QModelIndex` with the index to open the persistent editor.
        """

        self._table_view.openPersistentEditor(index)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Sort the table by the given column and order.

        Args:
            column: Number with the column to sort.
            order: The `Qt.SortOrder` with the order to sort.
        """

        self._table_view.sortByColumn(column, order)

    def toggle_column(self, column: int, state: Qt.CheckState) -> None:
        """Toggles the visibility of the given column.

        Args:
            column: Number with the column index.
            state: The `Qt.CheckState` with the state of the checkbox.
        """

        self._table_view.setColumnHidden(column, state == Qt.Unchecked)

    def _setup_widgets(self):
        """Set up the widgets of the `TableViewWidget`."""

        self._table_view = TableView(parent=self)
        self._proxy_search = TableFilterProxyModel(parent=self)
        self._table_view.setModel(self._proxy_search)
        self._reload_button = BaseButton(
            button_icon=icons.icon("reload"),
            parent=self,
        )
        self._search_widget = ViewSearchWidget(parent=self)

    def _setup_layouts(self):
        """Set up the layouts of the widget."""

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
        """Set up the signals of the widget."""

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

    # noinspection PyUnusedLocal
    def _on_selection_changed(
        self, selected: QItemSelection, deselected: QItemSelection
    ) -> None:
        """Called when the selection changes.

        Args:
            selected: The `QItemSelection` with the selected items.
            deselected: The `QItemSelection` with the deselected items.
        """

        indexes = selected.indexes()
        self.selectionChanged.emit([self._model.item_from_index(i) for i in indexes])

    # noinspection PyUnusedLocal
    def _on_search_widget_column_filter_index_changed(
        self, index: int, text: str
    ) -> None:
        """Called when the column filter index changes.

        Args:
            index: int with the index of the column.
            text: str with the text to filter.
        """

        self._proxy_search.setFilterKeyColumn(index)

    def _on_search_widget_column_visibility_index_changed(
        self, column: int, state: Qt.CheckState
    ) -> None:
        """Called when the column visibility index changes.

        Args:
            column: Number with the column index.
            state: The `Qt.CheckState` with the state of the checkbox.
        """

        self._table_view.setColumnHidden(column, state == Qt.Unchecked)

    def _on_table_view_context_menu_requested(self, position: QPoint) -> None:
        """Called when the context menu is requested.

        Args:
            position: The `QPoint` with the position of the context menu.
        """

        menu = QMenu(parent=self)
        selection = self.selected_rows()
        if self._row_data_source:
            self._row_data_source.context_menu(selection, menu)
        self.contextMenuRequested.emit(selection, menu)
        menu.exec_(self._table_view.viewport().mapToGlobal(position))

    def _on_reload_button_clicked(self) -> None:
        """Called when the reload button is clicked."""

        self.refresh()


class ViewSearchWidget(QWidget):
    """Custom `QWidget` that allow to visualize column/row view (such as tables)."""

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

    def set_header_visibility(self, state: bool) -> None:
        """Set the visibility of the header combo box.

        Args:
            state: A `bool` with the state of the visibility.
        """

        self._search_label.setVisible(state)
        self._search_header_combo.setVisible(state)

    def set_header_items(self, items: list[str]) -> None:
        """Set the header items of the header combo box.

        Args:
            items: Items to set.
        """

        self._search_header_combo.clear()
        for item in items:
            self._search_header_combo.addItem(item, is_checkable=False)

    def set_visibility_items(self, items: list[str]) -> None:
        """Set the visibility items of the header combo box.

        Args:
            items: Items to set.
        """

        self._show_column_visibility_combo.clear()
        for item in items:
            self._show_column_visibility_combo.addItem(item, is_checkable=True)

    def _setup_widgets(self, show_column_visibility_box: bool = True):
        """Set up the widgets of the `TableViewWidget`."""

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
        """Set up the layouts of the widget."""

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
        """Set up the signals of the widget."""

        self._search_header_combo.itemSelected.connect(
            self.columnFilterIndexChanged.emit
        )
        self._search_widget.textChanged.connect(self.searchTextChanged.emit)

    def _on_show_column_visibility_combo_check_state_changed(
        self, index: int, state: bool
    ):
        """Called when the check state of the column visibility combo changes.

        Args:
            index: Index of the clumn.
            state: State of the checkbox.
        """

        self.columnVisibilityIndexChanged.emit(index, state)
