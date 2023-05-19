from __future__ import annotations

from overrides import override
from Qt.QtCore import Qt, QRegExp, QModelIndex, QAbstractItemModel, QSortFilterProxyModel
from Qt.QtWidgets import QWidget

from tp.common.qt.models import datasources, treemodel


class LeafTreeFilterProxyModel(QSortFilterProxyModel):
	def __init__(self, sort: bool = True, parent: QWidget | None = None):
		super().__init__(parent)

		self.setSortCaseSensitivity(Qt.CaseInsensitive)

		if sort:
			self.setDynamicSortFilter(True)
			self.setFilterKeyColumn(0)

	@override
	def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
		search_exp = self.filterRegExp()					# type: QRegExp
		search_exp.setCaseSensitivity(Qt.CaseInsensitive)
		if search_exp.isEmpty():
			return True

		# check item and its children to see if we should keep or cull
		model = self.sourceModel()							# type: treemodel.BaseTreeModel | QAbstractItemModel
		if not source_parent.isValid():
			item = model.root.child(source_row)				# type: datasources.BaseDataSource
		else:
			model_index = source_parent.child(source_row, self.filterKeyColumn())
			item = model.item_from_index(model_index)		# type: datasources.BaseDataSource

		return self._match(search_exp, item, self.filterKeyColumn())

	@override
	def setFilterFixedString(self, pattern: str) -> None:
		return super().setFilterFixedString(pattern if len(pattern) >= 2 else '')

	def _match(self, search_expr: QRegExp, item: datasources.BaseDataSource, column: int) -> bool:
		"""
		Internal function that recursively checks whether the given regex expression matches the given item
		or its children.

		:param QRegExp search_expr: regular expression to match.
		:param datasource.BaseDataSource item: data source item.
		:param int column: filter key column index.
		:return: True if item matches regular expression; False otherwise.
		:rtype: bool
		"""

		if search_expr.indexIn(item.data(column)) != -1:
			return True
		for index in range(item.row_count()):
			child_item = item.child(index)
			if self._match(search_expr, child_item, column):
				return True

		return False
