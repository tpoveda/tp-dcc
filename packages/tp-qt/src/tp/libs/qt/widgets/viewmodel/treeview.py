from __future__ import annotations

import typing

from Qt import QtCompat
from Qt.QtCore import (
    Qt,
    Signal,
    QPoint,
    QSize,
    QModelIndex,
    QItemSelectionModel,
    QItemSelection,
)
from Qt.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QMenu,
    QAction,
    QTreeView,
    QHeaderView,
)
from Qt.QtGui import QMouseEvent

from . import modelutils
from .sortmodel import LeafTreeFilterProxyModel
from ..menus import Menu
from ..labels import ClippedLabel
from ..search import SearchLineEdit
from ..layouts import VerticalLayout, HorizontalLayout
from ... import dpi

if typing.TYPE_CHECKING:
    from .data import BaseDataSource
    from .treemodel import TreeModel


class TreeView(QTreeView):
    """Custom TreeView that supports double-click expansion and shift-based"""

    itemDoubleClicked = Signal(QModelIndex)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._support_shift_expand = True

        self.setFocusPolicy(Qt.StrongFocus)

        self.expanded.connect(self.expand_from)

    @property
    def support_shift_expand(self) -> bool:
        """Whether the tree view supports shift-based expansion."""

        return self._support_shift_expand

    @support_shift_expand.setter
    def support_shift_expand(self, flag: bool):
        """Set whether the tree view supports shift-based expansion."""

        self._support_shift_expand = flag

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """Handle double-click events to expand or collapse the item."""

        index = self.indexAt(event.pos())
        if not index.isValid():
            super().mouseDoubleClickEvent(event)
            return

        source_index, _ = modelutils.map_to_source_model(index)
        self.itemDoubleClicked.emit(source_index)

        super().mouseDoubleClickEvent(event)

    def expand_from(self, index: QModelIndex, expand: bool = True):
        """Expand or collapse all children of the given index based on the
        Shift key state.

        Args:
            index: The index to expand or collapse children from.
            expand: If True, expand the children; if False, collapse them.
        """

        modifier_pressed = QApplication.keyboardModifiers() == Qt.ShiftModifier
        if not modifier_pressed and self._support_shift_expand:
            return

        for i in range(self.model().rowCount(index)):
            child_index = self.model().index(i, 0, index)
            if not child_index.isValid():
                continue
            self.setExpanded(child_index, expand)


class TreeViewWidgetSelectionChangedEvent(object):
    def __init__(self, current: QItemSelection, previous: QItemSelection):
        """Initialize the selection changed event for the tree view widget.

        Args:
            current: The current selection.
            previous: The previous selection.
        """

        self._indices = current.indexes()
        self._prev_indices = previous.indexes()

    @property
    def current_items(self) -> list[BaseDataSource]:
        """The currently selected items in the tree view."""

        items: list[BaseDataSource] = []
        for i in self._indices:
            source_index, source_model = modelutils.map_to_source_model(i)
            # noinspection PyUnresolvedReferences
            items.append(source_model.item_from_index(source_index))

        return items

    @property
    def prev_items(self) -> list[BaseDataSource]:
        """The previously selected items in the tree view."""

        items: list[BaseDataSource] = []
        for i in self._prev_indices:
            source_index, model = modelutils.map_to_source_model(i)
            # noinspection PyUnresolvedReferences
            items.append(model.item_from_index(source_index))

        return items


class TreeViewWidget(QFrame):
    selectionChanged = Signal(TreeViewWidgetSelectionChangedEvent)
    contextMenuRequested = Signal(list, object)

    def __init__(
        self,
        title: str = "",
        expand: bool = True,
        sorting: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)

        self._sorting = sorting
        self._title = title
        self._model: TreeModel | None = None

        self._proxy_model = LeafTreeFilterProxyModel(sort=False, parent=self)

        self._setup_widgets()
        self._setup_layouts()

        # This call forces the proxy model to be set to the tree view.
        self.set_sorting_enabled(sorting)

        self._setup_signals()

        self.setFrameStyle(QFrame.NoFrame | QFrame.Plain)

        if expand:
            self.expand_all()

    @property
    def tree_view(self) -> TreeView:
        """The tree view associated with this widget."""

        return self._tree_view

    @property
    def toolbar_layout(self) -> HorizontalLayout:
        """The toolbar layout associated with this widget."""

        return self._toolbar_layout

    @property
    def model(self) -> TreeModel | None:
        """The source model associated with this widget."""

        return self._model

    @property
    def proxy_model(self) -> LeafTreeFilterProxyModel:
        """The proxy model associated with this widget."""

        return self._proxy_model

    def set_model(self, model: TreeModel):
        """Set the source model for the tree view.

        Args:
            model: The model to set as the source model for the tree view.
        """

        self._model = model
        self._proxy_model.setSourceModel(model)
        self._proxy_model.setDynamicSortFilter(self._sorting)

    def set_searchable(self, flag: bool):
        """Set whether the tree view is searchable.

        Args:
            flag: If True, the tree view will be searchable.
        """

        self._search_line_edit.setVisible(flag)

    def set_show_title_label(self, flag: bool):
        """Set whether the title label is visible.

        Args:
            flag: If True, the title label will be visible.
        """

        self._title_label.setVisible(flag)

    def set_header_hidden(self, flag: bool):
        """Set whether the header of the tree view is hidden.

        Args:
            flag: If True, the header will be hidden.
        """

        self._tree_view.setHeaderHidden(flag)

    def set_indentation(self, indentation: int):
        """Set the indentation for the tree view.

        Args:
            indentation: The indentation level to set.
        """

        self._tree_view.setIndentation(indentation)

    def set_support_shift_expansion(self, flag: bool):
        """Set whether the tree view supports shift-based expansion.

        Args:
            flag: If True, the tree view will support shift-based expansion.
        """

        self._tree_view.support_shift_expand = flag

    def set_sorting_enabled(self, enabled: bool):
        """Enable or disable sorting for the tree view.

        Args:
            enabled: Whether to enable sorting or not.
        """

        self._sorting = enabled
        self._tree_view.setModel(self._proxy_model)
        self._tree_view.setSortingEnabled(enabled)
        self._tree_view.sortByColumn(0 if enabled else -1, Qt.AscendingOrder)
        self._proxy_model.setDynamicSortFilter(enabled)
        if enabled:
            self._proxy_model.setFilterKeyColumn(0)

    def set_drag_drop_mode(self, mode: QTreeView.DragDropMode):
        """Set the drag and drop mode for the tree view.

        Args:
            mode: The drag and drop mode to set.
        """

        self._tree_view.setDragDropMode(mode)
        self._tree_view.setDragEnabled(True)
        self._tree_view.setDropIndicatorShown(True)
        self._tree_view.setAcceptDrops(True)

    def refresh(self):
        """Refresh the tree view by resizing columns."""

        if not self._model:
            return

        for i in range(self._model.columnCount(QModelIndex())):
            self._tree_view.resizeColumnToContents(i)
            new_width = self._tree_view.columnWidth(i) + 10
            self._tree_view.setColumnWidth(i, new_width)

    def selection_model(self) -> QItemSelectionModel:
        """Get the selection model of the tree view."""

        return self._tree_view.selectionModel()

    def header_items(self) -> list[str]:
        """Get the header items of the tree view.

        Returns:
            A list of header items from the source model.
        """

        header_items: list[str] = []
        for index in range(self._model.columnCount(QModelIndex())):
            header_items.append(self._model.root().header_text(index))

        return header_items

    def selected_items(self) -> list[BaseDataSource]:
        """Get the selected items in the tree view.

        Returns:
            A list of selected items from the source model.
        """

        source_model_indices: list[QModelIndex] = []
        for index in self.selection_model().selection().indexes():
            source_model_indices.append(modelutils.map_to_source_model(index)[0])

        # noinspection PyTypeChecker
        source_model: TreeModel = modelutils.get_source_model(self._model)
        if source_model is None:
            return []

        return list(map(source_model.item_from_index, source_model_indices))

    def selected_indexes(self) -> list[QModelIndex]:
        """Get the selected indexes in the tree view.

        Returns:
            A list of selected indexes from the source model.
        """

        return self._proxy_model.mapSelectionToSource(
            self.selection_model().selection()
        ).indexes()

    def expand_all(self):
        """Expand all items in the tree view."""

        self._tree_view.expandAll()

    def collapse_all(self):
        """Collapse all items in the tree view."""

        self._tree_view.collapseAll()

    def open_persistent_editor(self, index: QModelIndex):
        """Open the persistent editor for the given index.

        Notes:
            If no editor exists, it will create one.

        Args:
            index: The index for which to open the persistent editor.
        """

        self._tree_view.openPersistentEditor(index)

    def resize_to_contents(self):
        """Resize the tree view columns to their contents."""

        header = self._tree_view.header()
        # noinspection PyUnresolvedReferences
        QtCompat.setSectionResizeMode(header, QHeaderView.ResizeToContents)

    def _setup_widgets(self):
        """Set up the widgets for the tree view."""

        self._title_label = ClippedLabel(self._title.upper(), parent=self)
        self._search_line_edit = SearchLineEdit(parent=self)
        self._search_line_edit.setMinimumSize(dpi.size_by_dpi(QSize(21, 20)))

        self._tree_view = TreeView(parent=self)
        self._tree_view.setSelectionMode(QTreeView.ExtendedSelection)
        self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree_view.header().setContextMenuPolicy(Qt.CustomContextMenu)

    def _setup_layouts(self):
        """Set up the layouts for the tree view widget."""

        main_layout = VerticalLayout()
        main_layout.setSpacing(2)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        self._toolbar_layout = HorizontalLayout()
        self._toolbar_layout.setSpacing(2)
        self._toolbar_layout.setContentsMargins(5, 2, 2, 0)
        self._toolbar_layout.addWidget(self._title_label)
        self._toolbar_layout.addWidget(self._search_line_edit)

        main_layout.addLayout(self._toolbar_layout)
        main_layout.addWidget(self._tree_view)

    def _setup_signals(self):
        """Set up the signals for the tree view widget."""

        self._search_line_edit.textChanged.connect(
            self._proxy_model.setFilterRegularExpression
        )
        self.selection_model().selectionChanged.connect(self._on_selection_changed)
        self._tree_view.header().customContextMenuRequested.connect(
            self._on_header_custom_context_menu_requested
        )
        self._tree_view.customContextMenuRequested.connect(
            self._on_custom_context_menu_requested
        )

    def _toggle_column(self, column: int, state: Qt.CheckState):
        """Toggle the visibility of a column in the tree view."""

        if column == 0:
            if state == Qt.Checked:
                self._tree_view.showColumn(0)
            else:
                self._tree_view.hideColumn(0)
        else:
            if state == Qt.Checked:
                self._tree_view.showColumn(column)
            else:
                self._tree_view.hideColumn(column)

    def _on_selection_changed(self, current: QItemSelection, previous: QItemSelection):
        """Handle selection changes in the tree view.

        Args:
            current: The current selection.
            previous: The previous selection.
        """

        event = TreeViewWidgetSelectionChangedEvent(current=current, previous=previous)
        self.selectionChanged.emit(event)

    def _on_header_custom_context_menu_requested(self, position: QPoint):
        """Handle custom context menu requests for the header.

        Args:
            position: The position where the context menu was requested.
        """

        global_position = self.mapToGlobal(position)
        menu = QMenu(parent=self)
        headers = self.header_items()
        for i in range(len(headers)):
            item = QAction(headers[i], menu, checkable=True)
            menu.addAction(item)
            item.setChecked(not self._tree_view.header().isSectionHidden(i))
            item.setData({"index": i})
        selected_item = menu.exec_(global_position)
        self._toggle_column(
            selected_item.data()["index"],
            Qt.Checked if selected_item.isChecked() else Qt.Unchecked,
        )

    def _on_custom_context_menu_requested(self, position: QPoint):
        """Handle custom context menu requests for the tree view.

        Args:
            position: The position where the context menu was requested.
        """

        menu = Menu(parent=self)
        selection = self.selected_items()
        # noinspection PyTypeChecker
        source_model: TreeModel = modelutils.get_source_model(self._model)
        if source_model is None:
            return

        if source_model.root() is not None:
            source_model.root().context_menu(selection, menu)
        self.contextMenuRequested.emit(selection, menu)

        if max(len(menu.children()) - 4, 0) != 0:
            menu.exec_(self._tree_view.viewport().mapToGlobal(position))
