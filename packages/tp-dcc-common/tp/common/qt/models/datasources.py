from __future__ import annotations

import uuid
from typing import Iterator, Any

from overrides import override
from Qt.QtCore import Qt, QObject, QModelIndex, QAbstractItemModel, QSize
from Qt.QtWidgets import QStyledItemDelegate
from Qt.QtGui import QColor, QFont, QIcon

from tp.common.qt import dpi
from tp.common.qt.models import consts, delegates


class BaseDataSource(QObject):

	ENABLED_COLOR = QColor('@#C4C4C4')
	DISABLED_COLOR = QColor('@#5E5E5E')

	def __init__(
			self, header_text: str = '', model: QAbstractItemModel | None = None, parent: BaseDataSource | None = None):
		super().__init__()

		self._header_text = header_text
		self._model = model
		self._parent = parent
		self._children = list()			# type: list[Any]
		self._column_index = 0
		self._font = None
		self._uid = str(uuid.uuid4())
		self._default_text_margin = dpi.dpi_scale(5)

	def __eq__(self, other: BaseDataSource) -> bool:
		return isinstance(other, BaseDataSource) and self.uid == other.uid

	@property
	def uid(self) -> str:
		return self._uid

	@property
	def model(self) -> QAbstractItemModel | None:
		return self._model

	@model.setter
	def model(self, value: QAbstractItemModel | None):
		self._model = value

	@property
	def column_index(self) -> int:
		return self._column_index

	@column_index.setter
	def column_index(self, value: int):
		self._column_index = value

	@property
	def children(self) -> list[BaseDataSource]:
		return self._children

	def is_root(self) -> bool:
		"""
		Returns whether this data source is a root one (has no parent).

		:return: True if data source has no parent; False otherwise.
		:rtype: bool
		"""

		return self._parent is None

	def row_count(self) -> int:
		"""
		Returns the total row count for the data source. Defaults to the length of the data source children

		:return: total row count.
		:rtype: int
		"""

		return len(self._children)

	def column_count(self) -> int:
		"""
		Returns the total column count for the data source.

		:return: total column count.
		:rtype: int
		"""

		return 1

	def width(self) -> int:
		"""
		Returns item width.
		"""

		return 0

	def parent_source(self) -> BaseDataSource | None:
		"""
		Returns the parent of this item.

		:return: parent source item.
		:rtype: BaseDataSource | None
		"""

		return self._parent

	def set_parent_source(self, parent_source: BaseDataSource | None):
		"""
		Sets the parent for this item.

		:param BaseDataSource parent_source: parent source.

		..note:: The internal model of this item will be set to the parent model.
		"""

		if self._parent is not None:
			try:
				self._parent.children.remove(self)
			except ValueError:
				pass
		self.model = parent_source.model
		self._parent = parent_source
		parent_source.add_child(self)

	def iterate_children(self, recursive: bool = False) -> Iterator[BaseDataSource]:
		"""
		Generator function that iterates over children data sources.

		:param bool recursive: whether to iterate recursively.
		:return: iterated children.
		:rtype: Iterator[BaseDataSource]
		"""

		for child in self._children:
			yield child
			if not recursive:
				continue
			for sub_child in child.iterate_children(recursive=recursive):
				yield sub_child

	def insert_child(self, index: int, child: BaseDataSource) -> bool:
		"""
		Inserts a child into this data source.

		:param int index: column index.
		:param BaseDataSource child: child data source to insert.
		:return: True if the insert child operation was successful; False otherwise.
		:rtype: bool
		"""

		if child in self._children:
			return False

		child.model = self.model
		self._children.insert(index, child)
		return True

	def insert_children(self, index: int, children: list[BaseDataSource]):
		"""
		Inserts children into this data source.

		:param int index: column index.
		:param  list[BaseDataSource] children: children to insert.
		"""

		for child in children:
			child.model = self.model
		self._children[index:index] = children

	def index(self) -> int:
		"""
		Returns the index of this item within the model.

		:return: item index.
		:rtype: int
		"""

		parent = self.parent_source()

		return parent.children.index(self) if parent is not None and parent.children else 0

	def model_index(self) -> QModelIndex:
		"""
		Returns the model index that represents this data source.

		:return: model index.
		:rtype: QModelIndex
		"""

		if self._model is None:
			return QModelIndex()

		indices = self._model.match(
			self._model.index(0, 0), consts.uidRole, self.uid, 1, Qt.MatchExactly | Qt.MatchRecursive)

		return indices[0] if indices else QModelIndex()

	def has_children(self) -> bool:
		"""
		Returns whether this data source has children.

		:return: True if data source has children; False otherwise.
		:rtype: bool
		"""

		return self.row_count() > 0

	def child(self, index: int) -> BaseDataSource | None:
		"""
		Returns child of this item at given index.

		:param int index: child index.
		:return: child instance.
		:rtype :BaseDataSource or None
		"""

		return self._children[index] if index < self.row_count() else None

	def add_child(self, child: BaseDataSource) -> BaseDataSource | None:
		"""
		Adds given item instance as a child for this item instance.

		:param BaseDataSource child: child data source item.
		:return: added child data source item.
		:rtype: BaseDataSource or None
		"""

		if child in self._children:
			return None

		child.model = self.model
		self._children.append(child)

		return child

	def header_text(self, index: int) -> str:
		"""
		Returns the column header text.

		:param int index: column index.
		:return: header text.
		:rtype: str
		"""

		return self._header_text

	def header_icon(self, index: int) -> QIcon:
		"""
		Returns the column header icon.

		:param int index: column index.
		:return: header icon.
		:rtype: QIcon
		"""

		return QIcon()

	def data(self, index: int) -> str:
		"""
		Returns the text for the given column (starting from 0).

		:param int index: column index for the item.
		:return: column text.
		:rtype: Any
		"""

		return ''

	def set_data(self, index: int, value: str) -> bool:
		"""
		Sets the text for the given column index.

		:param int index: column index.
		:param str value: text value.
		:return: True if set data operation was successful; False otherwise.
		:rtype: bool
		"""

		return True

	def insert_column_data_sources(self, index: int, count: int) -> bool:
		"""
		Inserts column data sources for the given column index.

		:param int index: column index.
		:param int count: total number of columns to insert.
		:return: True if the insert column data sources operation was successful; False otherwise.
		:rtype: bool
		"""

		return False

	def remove_column_data_sources(self, index: int, count: int) -> bool:
		"""
		Removes column data sources for the given column index.

		:param int index: column index.
		:param int count: total number of columns to remove.
		:return: True if the remove column data sources operation was successful; False otherwise.
		:rtype: bool
		"""

		return False

	def insert_row_data_source(self, index: int) -> bool:
		"""
		Inserts row data source for the given column index.

		:param int index: column index.
		:return: True if the insert row data source operation was successful; False otherwise.
		:rtype: bool
		"""

		return False

	def insert_row_data_sources(self, index: int, count: int):
		"""
		Inserts row data sources for the given column index.

		:param int index: column index.
		:param int count: total number of rows to insert.
		:return: True if the insert row data sources operation was successful; False otherwise.
		:rtype: bool
		"""

		return None

	def remove_row_data_source(self, index: int) -> bool:
		"""
		Removes row data source for the given column index.

		:param int index: column index.
		:return: True if the remove row data source operation was successful; False otherwise.
		:rtype: bool
		"""

		if index < self.row_count():
			del self._children[index]
			return True

		return False

	def remove_row_data_sources(self, index: int, count: int) -> bool:
		"""
		Removes row data sources for the given column index.

		:param int index: column index.
		:param int count: total number of rows to remove.
		:return: True if the remove row data sources operation was successful; False otherwise.
		:rtype: bool
		"""

		if index < self.row_count():
			self._children = self._children[:index] + self._children[index + count:]
			return True

		return False

	def tooltip(self, index: int) -> str:
		"""
		Returns the tooltip for the given column index.

		:param int index: column index.
		:return: tooltip.
		:rtype: str
		"""

		return '' if not self.model else f'{self.header_text(index)}:{str(self.data(index))}\n'

	def set_tooltip(self, index: int, tooltip: str):
		"""
		Sets the tooltip for the given column index.

		:param int index: column index.
		:param str tooltip: tooltip to set.
		"""

		pass

	def is_enabled(self, index: int) -> bool:
		"""
		Returns whether this item is enabled.

		:param int index: column index for the item.
		:return: True if item is enabled; False otherwise.
		:rtype: bool
		"""

		return True

	def is_editable(self, index: int) -> bool:
		"""
		Returns whether this item is editable.

		:param int index: column index for the item.
		:return: True if item is editable; False otherwise.
		:rtype: bool
		"""

		return self.is_enabled(index)

	def is_selectable(self, index: int) -> bool:
		"""
		Returns whether this item is selectable.

		:param int index: column index for the item.
		:return: True if item is selectable; False otherwise.
		:rtype: bool
		"""

		return True

	def is_checkable(self, index: int) -> bool:
		"""
		Returns whether this item is checkable.

		:param int index: column index for the item.
		:return: True if item is checkable; False otherwise.
		:rtype: bool
		"""

		return False

	def supports_drag(self, index: int) -> bool:
		"""
		Returns whether the item at given column index supports drag operations.

		:param int index: column index for the item.
		:return: True if drag operations are supported; False otherwise.
		:rtype: bool
		"""

		return False

	def supports_drop(self, index: int) -> bool:
		"""
		Returns whether the item at given column index supports drop operations.

		:param int index: column index for the item.
		:return: True if drop operations are supported; False otherwise.
		:rtype: bool
		"""

		return False

	def font(self, index: int) -> QFont | None:
		"""
		Returns the font used by this item.

		:param int index: column index for the item.
		:return: QFont or None
		"""

		return self._font

	def icon(self, index: int) -> QIcon | None:
		"""
		Returns the icon for the given column index.

		:param int index: column index for the item.
		:return: QIcon or None
		"""

		return None

	def icon_size(self, index: int) -> QSize:
		"""
		Returns the icon size at given column index.

		:param int index: column index for the item.
		:return: icon size.
		:rtype: QSize
		"""

		return QSize(16, 16)

	def text_margin(self, index: int) -> int:
		"""
		Returns the text margin for the given column index.

		:param int index: column index for the item.
		:return: text margin.
		:rtype: int
		"""

		return self._default_text_margin

	def alignment(self, index: int) -> Qt.AlignmentFlag:
		"""
		Returns the alignment for the given column index.

		:param int index: column index for the item.
		:return: text alignment.
		:rtype: Qt.AlignmentFlag
		"""

		return Qt.AlignVCenter

	def background_color(self, index: int) -> QColor | None:
		"""
		Returns background color for this item.

		:param int index: column index for the item.
		:return: item background color.
		:rtype: QColor
		"""

		return None

	def foreground_color(self, index: int) -> QColor | None:
		"""
		Returns foreground color for this item.

		:param int index: column index for the item.
		:return: item background color.
		:rtype: QColor or None
		"""

		if self.is_enabled(index) and self.is_editable(index):
			return self.ENABLED_COLOR

		return self.DISABLED_COLOR

	def display_changed_color(self, index: int) -> int | None:
		"""
		Returns the display changed color.

		:param int index: column index for the item.
		:return: display changed color index.
		:rtype: int
		"""

		return None

	def user_objects(self) -> list[Any]:
		"""
		Returns list of user objects for this data source.

		:return: list of user objects.
		:rtype: list[Any]
		"""

		return self._children

	def set_user_objects(self, objects: list[Any]):
		"""
		Sets user objects for this data source.

		:param list[Any] objects: list of user objects.
		"""

		self._children = objects

	def user_object(self, index: int) -> Any:
		"""
		Returns the user object at given index.

		:param int index: user object index to retrieve.
		:return: user object instance.
		:rtype: Any
		"""

		if index < self.row_count():
			return self.user_objects()[index]

	def custom_roles(self, index: int) -> list[Qt.ItemDataRole]:
		"""
		Returns the custom roles at given index.

		:param int index: custom roles index to retrieve.
		:return: list of custom roles.
		:rtype: list[Qt.ItemDataRole]
		"""

		return list()

	def data_by_role(self, index: int, role: Qt.ItemDataRole) -> Any:
		"""
		Returns the data at given index with given role.

		:param int index: index to retrieve data of.
		:param Qt.ItemDataRole role: role to retrieve data of.
		:return: found data in given index and with given role.
		:rtype: Any
		"""

		return None

	def set_data_by_custom_role(self, index: int, data: Any, role: Qt.ItemDataRole) -> bool:
		"""
		Sets data at given index and with given role.

		:param int index: index to set data of.
		:param Any data: data to set.
		:param Qt.ItemDataRole role: role to set data of.
		:return: True if the set data operation was successful; False otherwise.
		:rtype: bool
		"""

		return False

	def on_vertical_header_selection(self, index: int):
		"""
		Triggered by the view (if this source is attached to one) when the vertical header of the view is clicked.

		:param int index: row index.
		"""

		pass

	def can_fetch_more(self) -> bool:
		"""
		Returns whether item can fetch more data.

		:return: True if item can fetch more data; False otherwise.
		:rtype: bool
		"""

		return False

	def fetch_more(self):
		"""
		Fetch more data for this item.
		"""

		pass

	def delegate(self, parent: QObject) -> QStyledItemDelegate:
		"""
		Returns custom delegate to write view with.

		:param QObject parent: parent view.
		:return: delegate instance.
		:rtype: QStyledItemDelegate
		"""

		return delegates.HtmlDelegate(parent)


class ColumnDataSource(BaseDataSource):
	def __init__(
			self, header_text: str = '', model: QAbstractItemModel | None = None, parent: BaseDataSource | None = None):
		super().__init__(header_text=header_text, model=model, parent=parent)

	@override(check_signature=False)
	def data(self, row_data_source: BaseDataSource, index: int) -> str:
		"""
		Returns the text for this column.

		:param BaseDataSource row_data_source: row data source model for the column index.
		:param index: column index for the text.
		:return: column text.
		:rtype: str
		"""

		return ''

