from __future__ import annotations

from typing import Union, Any

from overrides import override
from Qt import QtCompat
from Qt.QtCore import Qt, QObject, QModelIndex, QAbstractItemModel

from tp.common.qt.models import consts, datasources


class BaseTreeModel(QAbstractItemModel):
	def __init__(self, root: datasources.BaseDataSource, parent: QObject | None):
		super().__init__(parent)

		self._root = root
		if self._root:
			self._root.model = self

	@property
	def root(self) -> datasources.BaseDataSource:
		return self._root

	@override
	def rowCount(self, parent: QModelIndex = ...) -> int:
		return 0 if self.root is None else self.item_from_index(parent).row_count()

	@override
	def columnCount(self, parent: QModelIndex = ...) -> int:
		return 0 if self.root is None else self.item_from_index(parent).column_count()

	@override
	def index(self, row: int, column: int, parent: QModelIndex = ...) -> QModelIndex:
		if not self.hasIndex(row, column, parent):
			return QModelIndex()

		parent_item = self.item_from_index(parent)
		child_item = parent_item.child(row)
		if child_item:
			return self.createIndex(row, column, child_item)

		return QModelIndex()

	@override(check_signature=False)
	def parent(self, child: QModelIndex) -> QModelIndex:
		if not child.isValid():
			return QModelIndex()

		child_item = child.internalPointer()		# type: datasources.BaseDataSource
		parent_item = child_item.parent_source()
		if parent_item is None or parent_item == self.root:
			return QModelIndex()

		return self.createIndex(parent_item.index(), 0, parent_item)

	@override
	def hasChildren(self, parent: QModelIndex = ...) -> bool:
		if not parent.isValid():
			return super().hasChildren(parent)

		return self.item_from_index(parent).has_children()

	@override
	def flags(self, index: QModelIndex) -> Union[Qt.ItemFlags,Qt.ItemFlag]:
		if not index.isValid():
			return Qt.ItemIsDropEnabled
		item = index.internalPointer()			# type: datasources.BaseDataSource
		column = index.column()

		flags = Qt.ItemIsEnabled
		if item.supports_drag(column):
			flags |= Qt.ItemIsDragEnabled
		if item.supports_drop(column):
			flags |= Qt.ItemIsDropEnabled
		if item.is_editable(column):
			flags |= Qt.ItemIsEditable
		if item.is_selectable(column):
			flags |= Qt.ItemIsSelectable
		if not item.is_enabled(column):
			flags |~ Qt.ItemIsEnabled
		if item.is_checkable(column):
			flags |= Qt.ItemIsUserCheckable

		return flags

	@override
	def supportedDropActions(self) -> Union[Qt.DropActions, Qt.DropAction]:
		return Qt.CopyAction | Qt.MoveAction

	@override
	def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = ...) -> Any:
		if orientation == Qt.Horizontal:
			if role == Qt.DisplayRole:
				return self.root.header_text(section)
			elif role == Qt.DecorationRole:
				icon = self.root.header_icon()
				return icon.pixmap(icon.availableSizes()[-1]) if not icon.isNull else None

		return None

	@override
	def data(self, index: QModelIndex, role: Qt.ItemDataRole = ...) -> Any:
		if not index.isValid():
			return None
		item = index.internalPointer()			# type: datasources.BaseDataSource
		column = index.column()

		if role == Qt.DisplayRole or role == Qt.EditRole:
			return item.data(column)
		elif role == Qt.ToolTipRole:
			return item.tooltip(column)
		elif role == Qt.DecorationRole:
			return item.icon(column)
		elif role == consts.textMarginRole:
			return item.text_margin(column)
		elif role == Qt.CheckStateRole and item.is_checkable(column):
			return Qt.Checked if item.data(column) else Qt.Unchecked
		elif role == Qt.BackgroundRole:
			return item.background_color(column) or None
		elif role == Qt.ForegroundRole:
			return item.foreground_color(column) or None
		elif role == Qt.TextAlignmentRole:
			return item.alignment(column)
		elif role == Qt.FontRole:
			return item.font(column)
		elif role in (consts.sortRole, consts.filterRole):
			return item.data(column)
		elif role == consts.enumsRole:
			return item.enums(column)
		elif role == consts.userObject:
			return item
		elif role == consts.uidRole:
			return item.uid
		elif role in item.custom_roles(column):
			return item.data_by_role(column, role)

	@override
	def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = ...) -> bool:
		if not index.isValid():
			return False
		item = index.internalPointer()		# type: datasources.BaseDataSource
		column = index.column()
		has_changed = False

		if role == Qt.EditRole:
			has_changed = item.set_data(column, value)
		elif role == Qt.ToolTipRole:
			has_changed = item.set_tooltip(column, value)
		elif role in item.custom_roles(column):
			has_changed = item.set_data_by_custom_role(column, value, role)
		if has_changed:
			QtCompat.dataChanged(self, index, index, [role])
			return True

		return False

	@override
	def canFetchMore(self, parent: QModelIndex) -> bool:
		if not parent.isValid():
			return False

		item = self.item_from_index(parent)

		return item.can_fetch_more() if item is not None else False

	@override
	def fetchMore(self, parent: QModelIndex) -> None:
		if not parent.isValid():
			return None

		item = self.item_from_index(parent)
		if item is None:
			return None

		item.fetch_more()

	def set_root(self, root: datasources.BaseDataSource | None, refresh: bool = False):
		"""
		Sets the root data source for this model.

		:param datasources.BaseDataSoruce or None root: root data source.
		:param bool refresh: whether to reset model after setting root data source.
		"""

		self._root = root
		self._root.model = self
		if refresh:
			self.refresh()

	def refresh(self):
		"""
		Hard reloads the model,
		"""

		self.modelReset.emit()

	def item_from_index(self, index: QModelIndex) -> datasources.BaseDataSource | None:
		"""
		Returns the data source for the given model index.

		:param QModelIndex index: Qt model index.
		:return: found data source instance.
		:rtype: datasource.BaseDataSource or None
		"""

		return index.data(consts.userObject) if index.isValid() else self.root
