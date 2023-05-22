from __future__ import annotations

from Qt.QtCore import (
	Qt, Signal, QPoint, QSize, QAbstractItemModel, QItemSelectionModel, QSortFilterProxyModel, QItemSelection
)
from Qt.QtWidgets import QWidget, QFrame, QListView, QMenu

from tp.common.qt import dpi
from tp.common.qt.widgets import layouts, search, labels, sliding
from tp.common.qt.models import datasources, listmodel


class ExtendedListView(QFrame):

	class ExtendedListViewSelectionChangedEvent:
		def __init__(self, current: QItemSelection, previous: QItemSelection, parent: ExtendedListView):
			self.indices = current.indexes()
			self.prev_indices = previous.indexes()
			model = parent.root_model()
			self.current_items = [model.item_from_index(parent.proxy_search.mapToSource(i)) for i in self.indices]
			self.prev_items = [model.item_from_index(parent.proxy_search.mapToSource(i)) for i in self.prev_indices]

	refreshRequested = Signal()
	selectionChanged = Signal(object)
	contextMenuRequested = Signal(list, object)

	def __init__(self, title: str = '', searchable: bool = False, parent: QWidget | None = None):
		super().__init__(parent)

		self._title = title
		self._model = None								# type: listmodel.BaseListModel
		self._row_data_source = None					# type: datasources.BaseDataSource

		self._setup_ui()
		self._setup_signals()

		self.set_searchable(searchable)

	@property
	def proxy_search(self) -> QSortFilterProxyModel:
		return self._proxy_search

	def refresh(self):
		"""
		Emits refreshRequested signal.
		"""

		self.refreshRequested.emit()

	def root_model(self) -> listmodel.BaseListModel:
		"""
		Returns view root model.

		:return: root model.
		:rtype: listmodel.BaseListModel
		"""

		return self._model

	def set_model(self, model: listmodel.BaseListModel):
		"""
		Sets the model to use by this list view.

		:param listmodel.BaseListModel model: list model to use.
		"""

		self._model = model

		self._proxy_search.setSourceModel(model)
		self._list_view.setModel(self._proxy_search)
		if self._row_data_source:
			self._row_data_source.model = model

		self._search_edit.textChanged.connect(self._proxy_search.setFilterRegExp)

	def set_searchable(self, flag: bool):
		"""
		Sets whether search functionality is enabled.

		:param bool flag:True to enable search functionality; False otherwise.
		"""

		self._search_edit.setVisible(flag)

	def model(self) -> QAbstractItemModel | listmodel.BaseListModel:
		"""
		Returns lit view model.

		:return: model.
		:rtype: QAbstractItemModel or listmodel.BaseListModel
		"""

		return self._list_view.model()

	def selection_model(self) -> QItemSelectionModel:
		"""
		Returns list view selection model.

		:return: selection model.
		:rtype: QItemSelectionModel
		"""

		return self._list_view.selectionModel()

	def register_row_data_source(self, data_source: datasources.BaseDataSource):
		"""
		Register given data source as the row data source used by this list view.

		:param datasources.BaseDataSource data_source: data source to register.
		"""

		self._row_data_source = data_source
		if hasattr(data_source, 'delegate'):
			delegate = data_source.delegate(self._list_view)
			self._list_view.setItemDelegateForColumn(0, delegate)
		if self._model is not None:
			self._model.row_data_source = data_source

	def _setup_ui(self):
		"""
		Internal function that creates list view widgets.
		"""

		self._main_layout = layouts.vertical_layout(spacing=1, margins=(2, 2, 2, 2), parent=self)
		self.setLayout(self._main_layout)

		self._list_view = QListView(parent=self)
		self._list_view.setSelectionMode(QListView.ExtendedSelection)
		self._list_view.setContextMenuPolicy(Qt.CustomContextMenu)

		self._setup_filter()
		self._main_layout.addWidget(self._list_view)

		self._list_view.customContextMenuRequested.connect(self._on_custom_context_menu_requested)

		self._proxy_search = QSortFilterProxyModel(parent=self)
		self._proxy_search.setFilterCaseSensitivity(Qt.CaseInsensitive)
		self._list_view.setModel(self._proxy_search)
		selection_model = self.selection_model()
		selection_model.selectionChanged.connect(self._on_selection_changed)

	def _setup_filter(self):
		"""
		Internal function that setup table view filtering widgets.
		"""

		self._search_edit = search.SearchLineEdit(parent=self)
		self._search_edit.setMinimumSize(dpi.size_by_dpi(QSize(21, 20)))
		self._title_label = labels.ClippedLabel(text=self._title.upper(), parent=self)
		self._sliding_widget = sliding.SlidingWidget(parent=self)
		self._sliding_widget.set_widgets(self._search_edit, self._title_label)

		self._toolbar_layout = layouts.horizontal_layout(spacing=0, margins=(10, 6, 6, 0))
		self._toolbar_layout.addWidget(self._sliding_widget)
		self._main_layout.addLayout(self._toolbar_layout)

		self.set_searchable(False)

	def _setup_signals(self):
		"""
		Internal function that connects signals.
		"""

		self._search_edit.textChanged.connect(self._proxy_search.setFilterRegExp)

	def _on_selection_changed(self, current: QItemSelection, previous: QItemSelection):
		"""
		Internal callback function that is called each time an item in the tree view is selected by the user.

		:param QItemSelection current: current selected items.
		:param QItemSelection previous: previous selected items.
		"""

		event = ExtendedListView.ExtendedListViewSelectionChangedEvent(current=current, previous=previous, parent=self)
		self.selectionChanged.emit(event)

	def _on_custom_context_menu_requested(self, pos: QPoint):
		"""
		Internal callback function that is called when context menu is opened.

		:param QPoint pos: context menu position.
		"""

		menu = QMenu(parent=self)
		selection = [int(i.row()) for i in self.selection_model().selectedIndexes()]
		if self._row_data_source:
			self._row_data_source.context_menu(selection, menu)
		self.contextMenuRequested.emit(selection, menu)
		menu.exec_(self._list_view.viewport().mapToGlobal(pos))
