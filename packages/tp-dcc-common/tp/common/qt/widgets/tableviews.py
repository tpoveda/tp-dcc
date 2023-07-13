from __future__ import annotations

from typing import List

from Qt import QtCompat
from Qt.QtCore import Qt, Signal, QPoint, QItemSelectionModel
from Qt.QtWidgets import QWidget, QFrame, QHeaderView, QTableView, QMenu

from tp.common.qt.widgets import layouts, search
from tp.common.qt.models import datasources, tablemodel, sortmodel


class ExtendedTableView(QFrame):

	selectionChanged = Signal(object)
	contextMenuRequested = Signal(list, object)
	refreshRequested = Signal()

	def __init__(self, searchable: bool = False, manual_reload: bool = True, parent: QWidget | None = None):
		super().__init__(parent)

		self._refreshing = False
		self._model = None								# type: tablemodel.BaseTableModel
		self._row_data_source = None					# type: datasources.BaseDataSource
		self._column_data_sources = list()				# type: list[datasources.BaseDataSource]

		self._setup_ui()
		self._setup_signals()

	@property
	def table_view(self) -> BaseTableView:
		return self._table_view

	def refresh(self):
		"""
		Refreshes view.
		"""

		if self._refreshing:
			return
		self._refreshing = True
		try:
			self.refreshRequested.emit()
			row_data_source = self._model.row_data_source
			column_data_sources = self._model.column_data_sources
			header_items = list()
			for i in range(len(column_data_sources)):
				header_items.append(column_data_sources[i].header_text(i))
			self._search_widget.set_header_items([row_data_source.header_text(0)] + header_items)
		finally:
			self._refreshing = False

	def model(self) -> sortmodel.TableFilterProxyModel:
		"""
		Returns table view model.

		:return: proxy model.
		:rtype: sortmodel.TableFilterProxyModel
		"""

		return self._table_view.model()

	def set_model(self, model: tablemodel.BaseTableModel):
		"""
		Sets the model to use by this table view.

		:param tablemodel.BaseTableModel model: table model to use.
		"""

		self._proxy_search.setSourceModel(model)
		self._proxy_search.setDynamicSortFilter(True)

		self._model = model
		if self._row_data_source:
			self._row_data_source.model = model
		for i in iter(self._column_data_sources):
			i.model = model

	def register_row_data_source(self, data_source: datasources.BaseDataSource):
		"""
		Register given data source as the row data source used by this list view.

		:param datasources.BaseDataSource data_source: data source to register.
		"""

		self._row_data_source = data_source
		data_source.column_index = 0
		if hasattr(data_source, 'delegate'):
			delegate = data_source.delegate(self._table_view)
			self._table_view.setItemDelegateForColumn(0, delegate)

		self._row_data_source.model = self._model
		self._model.row_data_source = data_source
		self._table_view.verticalHeader().sectionClicked.connect(self._row_data_source.on_vertical_header_selection)
		self._search_widget.set_visibility_items(self._row_data_source.header_text(0))
		width = data_source.width()
		if width > 0:
			self._table_view.setColumnWidth(0, width)

	def register_column_data_sources(self, data_sources: list[datasources.BaseDataSource]):
		"""
		Register given column data sources into the model.

		:param list data_sources:
		"""

		if not self._row_data_source:
			raise ValueError('Must assign row data source before columns')

		self._column_data_sources = data_sources
		visible_items = list()
		for i in range(len(data_sources)):
			source = data_sources[i]
			source.model = self._model
			source.column_index = i + 1
			if hasattr(source, 'delegate'):
				delegate = source.delegate(self._table_view)
				self._table_view.setItemDelegateForColumn(i + 1, delegate)
			visible_items.append(source.header_text(i))
			width = source.width()
			if width > 0:
				self._table_view.setColumnWidth(i + 1, width)

		self._model.column_data_sources = data_sources
		self._search_widget.set_visibility_items([self._row_data_source.header_text(0)] + visible_items)

	def selection_model(self) -> QItemSelectionModel:
		"""
		Returns current selection model.

		:return: selection model.
		:rtype: QItemSelectionModel
		"""

		return self._table_view.selectionModel()

	def selected_rows(self) -> List[int]:
		"""
		From all the selected indices returns the row numbers.

		:return: list of row numbers.
		:rtype: List[int]
		"""

		return list(set([i.row() for i in self.selection_model().selectedIndexes()]))

	def _setup_ui(self):
		"""
		Internal function that creates list view widgets.
		"""

		self._main_layout = layouts.vertical_layout(parent=self)

		self._table_view = BaseTableView(parent=self)
		self._table_view.contextMenuRequested.connect(self._on_context_menu_requested)
		self._setup_filter()

		self._main_layout.addWidget(self._table_view)

		self._proxy_search = sortmodel.TableFilterProxyModel(parent=self)
		self._table_view.setModel(self._proxy_search)

	def _setup_signals(self):
		"""
		Internal function that connects signals.
		"""

		self._search_widget.columnFilterIndexChanged.connect(self._on_search_box_column_filter_index_changed)

	def _setup_filter(self):
		"""
		Internal function that setup table view filtering widgets.
		"""

		self._search_widget = search.ViewSearchWidget(parent=self)

		self._search_layout = layouts.horizontal_layout(spacing=0)
		self._search_layout.addWidget(self._search_widget)
		self._main_layout.addLayout(self._search_layout)

	def _on_context_menu_requested(self, pos: QPoint):
		"""
		Internal callback function that is called each time context menu is requested by the user.

		:param QPoint pos: context menu position.
		"""

		menu = QMenu(self)
		selection = self.selected_rows()
		if self._row_data_source:
			self._row_data_source.context_menu(selection, menu)
		self.contextMenuRequested.emit(selection, menu)
		menu.exec_(self._table_view.viewport().mapToGlobal(pos))

	def _on_search_box_column_filter_index_changed(self, index: int, text: str):
		"""
		Internal callback function that is called each time search box column filter index changes.

		:param int index: current index.
		:param str text: current search text.
		"""

		self._proxy_search.setFilterKeyColumn(index)


class BaseTableView(QTableView):

	contextMenuRequested = Signal()

	def __init__(self, parent: QWidget | None = None):
		super().__init__(parent)

		self.setSelectionMode(QTableView.ExtendedSelection)
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.setSortingEnabled(True)
		self.setShowGrid(False)
		self.setAlternatingRowColors(True)
		self.horizontalHeader().setStretchLastSection(True)
		QtCompat.setSectionResizeMode(self.verticalHeader(), QHeaderView.ResizeMode.ResizeToContents)
		self.sortByColumn(0, Qt.AscendingOrder)
		self.customContextMenuRequested.connect(self.contextMenuRequested.emit)
