from __future__ import annotations

from typing import Any

from overrides import override
from Qt import QtCompat
from Qt.QtCore import Qt, QObject, QModelIndex, QAbstractTableModel

from tp.common.qt.models import consts, datasources


class BaseTableModel(QAbstractTableModel):
	def __init__(self, parent: QObject | None = None):
		super().__init__(parent=parent)

		self._row_data_source = None								# type: datasources.BaseDataSource
		self._column_data_sources = list()							# type: list[datasources.ColumnDataSource]

	@property
	def column_data_sources(self) -> list[datasources.BaseDataSource]:
		return self._column_data_sources

	@column_data_sources.setter
	def column_data_sources(self, value: list[datasources.BaseDataSource]):
		self._column_data_sources = value

	@property
	def row_data_source(self) -> datasources.BaseDataSource:
		return self._row_data_source

	@row_data_source.setter
	def row_data_source(self, value: datasources.BaseDataSource):
		self._row_data_source = value

	@override
	def rowCount(self, parent: QModelIndex = ...) -> int:
		if parent.column() > 0 and self._row_data_source or not self._column_data_sources:
			return 0

		return self._row_data_source.row_count()

	@override
	def columnCount(self, parent: QModelIndex = ...) -> int:
		if not self._row_data_source or not self._column_data_sources:
			return 0

		return len(self._column_data_sources) + 1

	@override
	def data(self, index: QModelIndex, role: Qt.ItemDataRole = ...) -> Any:
		if not index.isValid():
			return None

		column = int(index.column())
		row = int(index.row())
		data_source = self.data_source(column)
		if data_source is None:
			return None

		if column == 0:
			kwargs = {'index': row}
		else:
			kwargs = {'row_data_source': self._row_data_source, 'index': row}
		role_to_fn = {
			Qt.DisplayRole: data_source.data,
			Qt.EditRole: data_source.data,
			Qt.ToolTipRole: data_source.tooltip,
			Qt.DecorationRole: data_source.icon,
			consts.textMarginRole: data_source.text_margin,
			consts.editChangedRole: data_source.display_changed_color,
			Qt.TextAlignmentRole: data_source.alignment,
			Qt.FontRole: data_source.font,
			Qt.BackgroundRole: data_source.background_color,
			Qt.ForegroundRole: data_source.foreground_color
		}
		fn = role_to_fn.get(role)
		if fn is not None:
			return fn(**kwargs)
		elif role == Qt.CheckStateRole and data_source.is_checkable(**kwargs):
			return Qt.Checked if data_source.data(**kwargs) else Qt.Unchecked
		elif role == consts.minValue:
			return data_source.minimum(**kwargs)
		elif role == consts.maxValue:
			return data_source.maximum(**kwargs)
		elif role == consts.enumsRole:
			return data_source.enums(**kwargs)
		elif role == consts.userObject:
			return data_source.user_object(row)
		elif role == data_source.custom_roles(**kwargs):
			return data_source.data_by_role(role=role, **kwargs)

	def data_source(self, index: int) -> datasources.BaseDataSource:
		"""
		Returns the data source at given index.

		:param int index: data source index.
		:return: datasources.BaseDataSource
		"""

		return self._row_data_source if index == 0 else self._column_data_sources[index - 1]

	def refresh(self):
		"""
		Hard reloads the model.
		"""

		self.modelReset.emit()

