from __future__ import annotations

from typing import List

from Qt import QtCompat
from Qt.QtCore import Qt, Signal, QPoint, QSize, QModelIndex, QItemSelectionModel, QItemSelection
from Qt.QtWidgets import QApplication, QWidget, QFrame, QTreeView, QMenu, QAction, QAbstractItemView
from Qt.QtGui import QMouseEvent

from tp.common.qt import dpi, qtutils
from tp.common.qt.models import utils, datasources, treemodel, sortmodel
from tp.common.qt.widgets import layouts, search, sliding, labels, menus


class BaseTreeView(QTreeView):
	"""
	Extended QTreeView that extends default QTreeView with the following functionality:
		- Adds itemDoubleClicked signal that is emitted when user double-click on an item.
		- If shift ke is pressed, all the children items of the expanded/collapsed item will be also expanded/collapsed.
	"""

	itemDoubleClicked = Signal(QModelIndex)

	def __init__(self, parent: QWidget | None = None):
		super().__init__(parent)

		self._supports_shift_expand = True
		self.expanded.connect(self._on_expanded)

		self.setFocusPolicy(Qt.StrongFocus)

	def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
		index = self.indexAt(event.pos())
		if index.isValid():
			data_model_index, _ = utils.data_model_index_from_index(index)
			self.itemDoubleClicked.emit(data_model_index)

		super().mouseDoubleClickEvent(event)

	def _on_expanded(self, index: QModelIndex, expand: bool = True):
		"""
		Internal callback function that is called each time a tree view item is expanded.
		If shift key is pressed, all the children items of the expanded/collapsed item will be also expanded/collapsed.

		:param QModelIndex index: expanded model index.
		:param bool expand: whether the item was expanded/collapsed.
		"""

		modifier_pressed = QApplication.instance().keyboardModifiers() == Qt.ShiftModifier
		if not modifier_pressed and self._supports_shift_expand:
			return

		for i in range(self.model().rowCount(index)):
			child_index = self.model().index(i, 0, index)
			self.setExpanded(child_index, expand)


class ExtendedTreeView(QFrame):

	class ExtendedTreeViewSelectionChangedEvent:
		def __init__(self, current: QItemSelection, previous: QItemSelection, parent: ExtendedTreeView):
			self.indices = current.indexes()
			self.prev_indices = previous.indexes()
			self.current_items = [
				parent.model.item_from_index(utils.data_model_index_from_index(i)[0]) for i in self.indices]
			self.prev_items = [
				parent.model.item_from_index(utils.data_model_index_from_index(i)[0]) for i in self.prev_indices]

	selectionChanged = Signal(ExtendedTreeViewSelectionChangedEvent)
	contextMenuRequested = Signal(list, object)
	refreshRequested = Signal()

	def __init__(self, title: str = '', parent: QWidget | None = None, expand: bool = True, sorting: bool = True):
		super().__init__(parent)

		self.setFrameStyle(QFrame.NoFrame | QFrame.Plain)

		self._title = title
		self._sorting = sorting
		self._model = None								# type: treemodel.BaseTreeModel
		self._column_data_sources = list()

		self._setup_ui()
		self._setup_signals()

		if expand:
			self.expand_all()

	@property
	def model(self) -> treemodel.BaseTreeModel:
		return self._model

	@property
	def proxy_search(self) -> sortmodel.LeafTreeFilterProxyModel:
		return self._proxy_search

	@property
	def tree_view(self) -> BaseTreeView:
		return self._tree_view

	def selection_model(self) -> QItemSelectionModel:
		"""
		Returns selection model for current model.

		:return: selection model.
		:rtype: QItemSelectionModel
		"""

		return self._tree_view.selectionModel()

	def set_model(self, model: treemodel.BaseTreeModel):
		"""
		Set the source model used by this view.

		:param treemodel.BaseTreeModel model: model to use.
		"""

		self._proxy_search.setSourceModel(model)
		self._proxy_search.setDynamicSortFilter(self._sorting)
		self._model = model

	def set_sorting_enabled(self, flag: bool):
		"""
		Sets whether sort is enabled witihn tree view model.

		:param bool flag: True to sort model; False otheriwse.
		"""

		self._tree_view.setModel(self._proxy_search)
		self._tree_view.setSortingEnabled(flag)
		self._tree_view.sortByColumn(0, Qt.AscendingOrder)
		self._proxy_search.setDynamicSortFilter(flag)
		if flag:
			self._proxy_search.setFilterKeyColumn(0)

	def set_alternating_color_enabled(self, flag: bool):
		"""
		Sets whether view should display tree rows with alternating colors.

		:param bool flag: True to alternate tree view row colors; False otherwise.
		"""

		qtutils.set_stylesheet_object_name(self._tree_view, '' if flag else 'disableAlternatingColor')
		self._tree_view.setAlternatingRowColors(flag)

	def set_toolbar_visible(self, flag: bool):
		"""
		Sets whether toolbar is visible.

		:param bool flag: True to make the toolbar visible; False otherwise.
		"""

		self._sliding_widget.setVisible(flag)

	def set_searchable(self, flag: bool):
		"""
		Sets whether tree view searching feature is enabled.

		:param bool flag: True to enable searchable feature; False to disable it.
		"""

		self._search_edit.setVisible(flag)

	def set_show_title_label(self, flag: bool):
		"""
		Sets whether title label should be visible.

		:param bool flag: True to show title label; False to hide it.
		"""

		self._title_label.setVisible(flag)

	def set_drag_drop_mode(self, mode: QAbstractItemView.DragDropMode):
		"""
		Sets tree view drag drop mode.

		:param QAbstractItemView.DragDropMode mode: drag drop mode.
		"""

		self._tree_view.setDragDropMode(mode)
		self._tree_view.setDragEnabled(True)
		self._tree_view.setDropIndicatorShown(True)
		self._tree_view.setAcceptDrops(True)

	def expand_all(self):
		"""
		Expands all tree view contents.
		"""

		self._tree_view.expandAll()

	def collapse_all(self):
		"""
		Collapses all tree view contents.
		"""

		self._tree_view.collapseAll()

	def resize_to_contents(self):
		"""
		Resizes tree view header to fit contents.
		"""

		header = self._tree_view.header()
		QtCompat.setSectionResizeMode(header, header.ResizeMode.ResizeToContents)

	def selected_indices(self) -> List[QModelIndex]:
		"""
		Returns a list of selected model indices.

		:return: List[QModelIndex]
		"""

		return self._proxy_search.mapSelectionToSource(self.selection_model().selection()).indexes()

	def selected_items(self) -> List[datasources.BaseDataSource]:
		"""
		Returns a list of selected data source items.

		:return: list of selected items.
		:rtype: List[datasources.BaseDataSource]
		"""

		indices = self.selection_model().selection()
		model_indices = self._proxy_search.mapSelectionToSource(indices).indexes()
		return list(map(self._model.item_from_index, model_indices))

	def header_items(self) -> List[str]:
		"""
		List of header item names.

		:return: header item names.
		:rtype: List[str]
		"""

		header_items = list()
		for i in range(self._model.columnCount(QModelIndex())):
			header_items.append(self._model.root.header_text(i))

		return header_items

	def refresh(self):
		"""
		Refreshes tree view based on the model contents and adjust columns to the displayed contents.
		"""

		for index in range(self._model.columnCount(QModelIndex())):
			self._tree_view.resizeColumnToContents(index)
			self._tree_view.setColumnWidth(index, self._tree_view.columnWidth(index) + 10)

	def _setup_ui(self):
		"""
		Internal function that creates tree view widgets.
		"""

		self._main_layout = layouts.vertical_layout(parent=self)

		self._tree_view = BaseTreeView(parent=self)
		self._tree_view.setSelectionMode(QTreeView.ExtendedSelection)
		self._tree_view.setContextMenuPolicy(Qt.CustomContextMenu)

		self._setup_filter()
		self._main_layout.addWidget(self._tree_view)

		self._proxy_search = sortmodel.LeafTreeFilterProxyModel(sort=False, parent=self)
		self.set_sorting_enabled(self._sorting)
		self.set_alternating_color_enabled(True)

		self._tree_view.customContextMenuRequested.connect(self._on_custom_context_menu_requested)

	def _setup_filter(self):
		"""
		Internal function that setup table view filtering widgets.
		"""

		self._sliding_widget = sliding.SlidingWidget(parent=self)
		self._title_label = labels.ClippedLabel(text=self._title.upper(), parent=self)
		self._search_edit = search.SearchLineEdit(parent=self)
		self._search_edit.setMinimumSize(dpi.size_by_dpi(QSize(21, 21)))
		self._sliding_widget.set_widgets(self._search_edit, self._title_label)

		self._toolbar_layout = layouts.horizontal_layout(spacing=0, margins=(10, 6, 6, 0))
		self._toolbar_layout.addWidget(self._sliding_widget)
		self._main_layout.addLayout(self._toolbar_layout)

	def _setup_signals(self):
		"""
		Internal function that connects signals.
		"""

		self._search_edit.textChanged.connect(self._proxy_search.setFilterRegExp)
		selection_model = self.selection_model()
		selection_model.selectionChanged.connect(self._on_selection_changed)
		self._tree_view.header().setContextMenuPolicy(Qt.CustomContextMenu)
		self._tree_view.header().customContextMenuRequested.connect(self._on_header_custom_context_menu_requested)

	def _toggle_column(self, column: int, state: bool):
		"""
		Toggles column state.

		:param int column: column index.
		:param bool state: whether column is enabled.
		"""

		if column == 0:
			self._tree_view.showColumn(0) if state == Qt.Checked else self._tree_view.hideColumn(0)
		else:
			self._tree_view.showColumn(column) if state == Qt.Checked else self._tree_view.hideColumn(column)

	def _on_selection_changed(self, current: QItemSelection, previous: QItemSelection):
		"""
		Internal callback function that is called each time an item in the tree view is selected by the user.

		:param QItemSelection current: current selected items.
		:param QItemSelection previous: previous selected items.
		"""

		event = ExtendedTreeView.ExtendedTreeViewSelectionChangedEvent(current=current, previous=previous, parent=self)
		self.selectionChanged.emit(event)

	def _on_custom_context_menu_requested(self, pos: QPoint):
		"""
		Internal callback function that is called when context menu is opened.

		:param QPoint pos: context menu position.
		"""

		context_menu = menus.extended_menu(parent=self)
		selection = self.selected_items()
		if self._model.root is not None:
			self._model.root.context_menu(selection, context_menu)
		self.contextMenuRequested.emit(selection, context_menu)
		if max(len(context_menu.children()) - 4, 0) != 0:
			context_menu.exec_(self._tree_view.viewport().mapToGlobal(pos))

	def _on_header_custom_context_menu_requested(self, pos: QPoint):
		"""
		Internal callback function that is called when header context menu is opened.

		:param QPoint pos: context menu position.
		"""

		global_pos = self.mapToGlobal(pos)
		context_menu = QMenu(parent=self)
		headers = self.header_items()
		for i in range(len(headers)):
			item = QAction(headers[i], context_menu, checkable=True)
			context_menu.addAction(item)
			item.setChecked(not self._tree_view.header().isSectionHidden(i))
			item.setData({'index': i})
		selected_item = context_menu.exec_(global_pos)
		self._toggle_column(selected_item.data()['index'], Qt.Checked if selected_item.isChecked() else Qt.Unchecked)
