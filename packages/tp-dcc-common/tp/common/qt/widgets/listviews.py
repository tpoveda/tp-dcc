from __future__ import annotations

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QFrame, QListView

from tp.common.qt.widgets import layouts
from tp.common.qt.models import datasources, listmodel


class ExtendedListView(QFrame):
	def __init__(self, title: str = '', searchable: bool = False, parent: QWidget | None = None):
		super().__init__(parent)

		self._model = None								# type: listmodel.BaseListModel
		self._row_data_source = None					# type: datasources.BaseDataSource

		self._setup_ui()

	def set_model(self, model: listmodel.BaseListModel):
		"""
		Sets the model to use by this list view.

		:param listmodel.BaseListModel model: list model to use.
		"""

		self._model = model

		if self._row_data_source:
			self._row_data_source.model = model

	# def set_searchable(self, flag: bool):
	# 	"""
	# 	Sets whether search functionality is enabled.
	#
	# 	:param bool flag:True to enable search functionality; False otherwise.
	# 	"""
	#
	# 	pass

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

		self._main_layout = layouts.vertical_layout(spacing=1)
		self.setLayout(self._main_layout)

		self._list_view = QListView(parent=self)
		self._list_view.setSelectionMode(QListView.ExtendedSelection)
		self._list_view.setContextMenuPolicy(Qt.CustomContextMenu)
		self._main_layout.addWidget(self._list_view)
