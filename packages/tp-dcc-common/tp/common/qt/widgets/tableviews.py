from __future__ import annotations

from Qt import QtCompat
from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QFrame, QHeaderView, QTableView

from tp.common.qt.widgets import layouts
from tp.common.qt.models import datasources, tablemodel


class ExtendedTableView(QFrame):
	def __init__(self, searchable: bool = False, manual_reload: bool = True, parent: QWidget | None = None):
		super().__init__(parent)

		self._refreshing = False
		self._model = None								# type: tablemodel.BaseTableModel
		self._row_data_source = None					# type: datasources.BaseDataSource
		self._column_data_sources = list()				# type: list[datasources.BaseDataSource]

		self._setup_ui()

	@property
	def table_view(self) -> BaseTableView:
		return self._table_view

	def set_model(self, model: tablemodel.BaseTableModel):
		"""
		Sets the model to use by this table view.

		:param tablemodel.BaseTableModel model: table model to use.
		"""

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

	def _setup_ui(self):
		"""
		Internal function that creates list view widgets.
		"""

		self._main_layout = layouts.vertical_layout()
		self.setLayout(self._main_layout)

		self._table_view = BaseTableView(parent=self)
		self._main_layout.addWidget(self._table_view)


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
