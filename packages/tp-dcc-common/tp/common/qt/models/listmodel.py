from __future__ import annotations

from typing import Union, Any

from overrides import override
from Qt import QtCompat
from Qt.QtCore import Qt, QObject, QModelIndex, QAbstractListModel

from tp.common.qt.models import consts, datasources


class BaseListModel(QAbstractListModel):
	def __init__(self, parent: QObject | None = None):
		super().__init__(parent=parent)

		self._row_data_source = None								# type: datasources.BaseDataSource

	@property
	def row_data_source(self) -> datasources.BaseDataSource:
		return self._row_data_source

	@row_data_source.setter
	def row_data_source(self, value: datasources.BaseDataSource):
		self._row_data_source = value

	@override
	def rowCount(self, parent: QModelIndex = ...) -> int:
		return 0 if parent.column() > 0 or not self._row_data_source else self._row_data_source.row_count()

	@override
	def columnCount(self, parent: QModelIndex) -> int:
		return 1

	@override
	def flags(self, index: QModelIndex) -> Union[Qt.ItemFlags, Qt.ItemFlag]:
		if not index.isValid():
			return Qt.NoItemFlags
		row = index.row()
		data_source = self._row_data_source

		flags = Qt.ItemIsEnabled
		if data_source.supports_drag(row):
			flags |= Qt.ItemIsDragEnabled
		if data_source.supports_drop(row):
			flags |= Qt.ItemIsDropEnabled
		if data_source.is_editable(row):
			flags |= Qt.ItemIsEditable
		if data_source.is_selectable(row):
			flags |= Qt.ItemIsSelectable
		if not data_source.is_enabled(row):
			flags |~ Qt.ItemIsEnabled
		if data_source.is_checkable(row):
			flags |= Qt.ItemIsUserCheckable

		return flags

	@override
	def supportedDropActions(self) -> Union[Qt.DropActions, Qt.DropAction]:
		return Qt.CopyAction | Qt.MoveAction

	@override
	def headerData(self, section: int, orientation: Qt.Orientation, role: Qt.ItemDataRole = ...) -> Any:
		data_source = self._row_data_source
		if role == Qt.DisplayRole:
			return data_source.header_text(section)
		elif role == Qt.DecorationRole:
			icon = data_source.header_icon(section)
			return icon.pixmap(icon.availableSizes()[-1]) if not icon.isNull else None

		return None

	@override
	def data(self, index: QModelIndex, role: Qt.ItemDataRole = ...) -> Any:
		if not index.isValid():
			return None
		row = int(index.row())
		data_source = self._row_data_source
		if data_source is None:
			return None

		kwargs = {'index': row}
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
			Qt.ForegroundRole: data_source.foreground_color,
			consts.userObject: data_source.user_object,
			consts.iconSizeRole: data_source.icon_size
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
		elif role == data_source.custom_roles(**kwargs):
			return data_source.data_by_role(role=role, **kwargs)

	@override
	def setData(self, index: QModelIndex, value: Any, role: Qt.ItemDataRole = ...) -> bool:
		if not index.isValid() or not self._row_data_source:
			return False
		row_data_source = self._row_data_source
		row = index.row()
		has_changed = False

		if role == Qt.EditRole:
			has_changed = row_data_source.set_data(row, value)
		elif role == Qt.ToolTipRole:
			has_changed = row_data_source.set_tooltip(row, value)
		elif role == consts.enumsRole:
			has_changed = row_data_source.set_enums(row, value)
		elif role in row_data_source.custom_roles(row):
			has_changed = row_data_source.set_data_by_custom_role(row, value, role)
		if has_changed:
			QtCompat.dataChanged(self, index, index, [role])
			return True

		return False

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

		return index.data(consts.userObject) if index.isValid() else self._row_data_source.user_object(index.row())
