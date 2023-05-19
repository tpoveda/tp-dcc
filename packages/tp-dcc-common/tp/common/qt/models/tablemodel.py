from __future__ import annotations

import typing

from overrides import override
from Qt import QtCompat
from Qt.QtCore import Qt, QObject, QModelIndex, QAbstractTableModel

from tp.common.qt.models import consts, datasources


class BaseTableModel(QAbstractTableModel):
	def __init__(self, parent: QObject | None = None):
		super().__init__(parent=parent)

		self._row_data_source = None								# type: datasources.BaseDataSource
		self._column_data_sources = list()							# type: list[datasources.BaseDataSource]

	@property
	def column_data_sources(self) -> list[datasources.BaseDataSource]:
		return self._column_data_sources

	@column_data_sources.setter
	def column_data_sources(self, value: list[datasources.BaseDataSource]):
		self._column_data_sources = value
