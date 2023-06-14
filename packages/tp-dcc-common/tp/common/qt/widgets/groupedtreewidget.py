from __future__ import annotations

from typing import Type

from Qt.QtCore import Qt
from Qt.QtWidgets import QWidget, QTreeWidget, QTreeWidgetItem, QAbstractItemView

from tp.common.qt import dpi, qtutils


class GroupedTreeWidget(QTreeWidget):
	"""
	Custom Qt tree widget this grouping capabilities.
	"""

	ITEM_TYPE_WIDGET = 'WIDGET'
	ITEM_TYPE_GROUP = 'GROUP'

	WIDGET_COLUMN = 0
	ITEM_WIDGET_INFO_COLUMN = 1
	DATA_COLUMN = 2

	class TreeWidgetItem(QTreeWidgetItem):
		def __init__(self, name: str, flags: Qt.ItemFlags, parent: QTreeWidgetItem, after: QTreeWidgetItem | None = None):
			super().__init__(parent, after)

			self.setText(GroupedTreeWidget.WIDGET_COLUMN, name)
			self.setFlags(flags)

	def __init__(
			self, locked: bool = False, allow_sub_groups: bool = True,
			custom_tree_widget_item_class: Type = QTreeWidgetItem, parent: QWidget | None = None):
		super().__init__(parent)

		self._dropped_items = None
		self._drop_cancelled = False
		self._dragged_items = None
		self._drop_target = None
		self._header_item = None													# type: QTreeWidgetItem
		self._allow_sub_groups = allow_sub_groups
		self._locked = locked
		self._custom_tree_widget_item_class = custom_tree_widget_item_class
		self._group_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
		self._group_unlocked_flags = Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
		self._item_widget_flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
		self._item_widget_unlocked_flags = Qt.ItemIsDragEnabled
		self._drag_widget = None
		self._drag_widget_align = None

		self.setRootIsDecorated(False)

		self.set_locked(locked)
		self._setup_ui()
		self._setup_signals()

	def set_locked(self, flag: bool):
		"""
		Sets whether tree widget allows for drag and drop functionality.

		:param bool flag: True to enabled drag and drop functionality; False otherwise.
		"""

		self._locked = flag
		if flag:
			self._group_flags = self._group_flags & ~self._group_unlocked_flags
			self._item_widget_flags = self._item_widget_flags & ~self._item_widget_unlocked_flags
		else:
			self._group_flags = self._group_flags | self._group_unlocked_flags
			self._item_widget_flags = self._item_widget_flags | self._item_widget_unlocked_flags

		self._apply_flags()

	def _setup_ui(self):
		"""
		Internal function that setup grouped tree widget UI.
		"""

		self._header_item = QTreeWidgetItem(['Widget'])
		self.setHeaderItem(self._header_item)
		self.header().hide()

		self._setup_drag_drop()

		self.resizeColumnToContents(1)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
		self.setIndentation(dpi.dpi_scale(10))
		self.setFocusPolicy(Qt.NoFocus)

	def _setup_signals(self):
		"""
		Internal function that setups grouped tree widget signals.
		"""

		pass

	def _setup_drag_drop(self):
		"""
		Internal function that initializes drag and drop settings for this widget.
		"""

		self.setDragEnabled(True)
		self.setDropIndicatorShown(True)
		self.setDragDropMode(QAbstractItemView.DragDrop)
		self.setDefaultDropAction(Qt.MoveAction)
		self.setAcceptDrops(True)

	def _item_type(self, tree_item: QTreeWidgetItem) -> str:
		"""
		Internal function that returns the type of the given item ('WIDGET' or 'GROUP').

		:param QTreeWidgetItem tree_item: tree item widget instance.
		:return: item type.
		:rtype: str
		"""

		return tree_item.data(self.DATA_COLUMN, Qt.EditRole)

	def _apply_flags(self):
		"""
		Internal function that applies internal group and item widget flags to all current tree widget items.
		"""

		for tree_item in qtutils.safe_tree_widget_iterator(self):
			if self._item_type(tree_item) == self.ITEM_TYPE_WIDGET:
				tree_item.setFlags(self._item_widget_flags)
			elif self._item_type(tree_item) == self.ITEM_TYPE_GROUP:
				tree_item.setFlags(self._group_flags)
