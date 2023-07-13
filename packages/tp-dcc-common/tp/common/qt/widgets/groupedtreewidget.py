from __future__ import annotations

from typing import List, Type, Callable, Iterator

from overrides import override
from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import (
	QSizePolicy, QWidget, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QAbstractItemView, QToolButton, QSpacerItem, QLabel
)
from Qt.QtGui import QIcon, QMouseEvent

from tp.common.qt import consts, dpi, qtutils
from tp.common.qt.widgets import layouts, frames, lineedits
from tp.common.resources import api as resources


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
		"""
		Item widget used by grouped tree widget.
		"""

		def __init__(self, name: str, flags: Qt.ItemFlags, parent: GroupedTreeWidget, after: QTreeWidgetItem | None = None):
			super().__init__(parent, after)

			self.setText(GroupedTreeWidget.WIDGET_COLUMN, name)
			self.setFlags(flags)

	class ItemWidgetLabel(QLabel):

		triggered = Signal()

		def __init__(self, name: str, parent: QWidget | None = None):
			super().__init__(name, parent=parent)

			self._name = name
			self._emit_target = None					# type: Callable

			self._setup_ui()

		@property
		def name(self) -> str:
			return self._name

		@name.setter
		def name(self, value: str):
			self._name = value

		@override
		def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
			self.triggered.emit()

		@override
		def mousePressEvent(self, ev: QMouseEvent) -> None:
			ev.ignore()

		@override
		def mouseReleaseEvent(self, ev: QMouseEvent) -> None:
			ev.ignore()

		@override
		def text(self):
			return self._name

		def connect_event(self, func: Callable):
			"""
			Connects triggered signal with given function.

			:param Callable func: function to call when item is triggered.
			"""

			self._emit_target = func
			self.triggered.connect(func)

		def copy(self) -> GroupedTreeWidget.ItemWidgetLabel:
			"""
			Creates a copy instance of this item widget.

			:return: item widget copy instance.
			:rtype: GroupedTreeWidget.ItemWidgetLabel
			"""

			current_type = type(self)
			result = current_type(self.text())
			result.name = self.name
			result.setStyleSheet(self.styleSheet())
			# _tooltip.copy_expanded_tooltips(self, result)

			return result

		def _setup_ui(self):
			"""
			Internal function that setups item wiget UI.
			"""

			pass

	class GroupWidget(QWidget):
		"""
		Widget used for groups for grouped tree widget items.
		"""

		def __init__(
				self, title: str = '', tree_item: GroupedTreeWidget.TreeWidgetItem | None = None,
				hide_title_frame: bool = False, parent: QWidget | None = None):
			super().__init__(parent)

			self._tree_item = tree_item
			self._collapsed = False
			self._color = consts.Colors.DARK_BACKGROUND_COLOR

			self._main_layout = layouts.horizontal_layout(parent=self)
			self._main_layout.setContentsMargins(0, 0, 0, 0)

			self._expand_toggle_button = QToolButton(parent=self)
			self._folder_icon = QToolButton(parent=self)
			self._title_frame = frames.BaseFrame(parent=self)
			self._title_frame.setContentsMargins(1, 1, 4, 0)
			self._horizontal_layout = layouts.horizontal_layout(parent=self._title_frame)
			self._horizontal_layout.setContentsMargins(0, 0, 0, 0)
			self._group_text_edit = lineedits.EditableLineEditOnClick(title, single=False, parent=self)
			self._title_extras_layout = QHBoxLayout()
			self._delete_button = QToolButton(parent=self)

			if hide_title_frame:
				self._title_frame.hide()

			self._setup_ui()
			self._setup_signals()

		def _setup_ui(self):
			"""
			Internal function that setups group widget UI.
			"""

			self.setLayout(self._main_layout)
			self._folder_icon.setIcon(resources.icon('open_folder'))
			self._delete_button.setIcon(resources.icon('close'))

			self._setup_title_frame()

		def _setup_title_frame(self):
			"""
			Internal function that builds the title part of the group widget.
			"""

			self.layout().addWidget(self._title_frame)

			self._title_frame.mousePressEvent = self.mousePressEvent
			self._expand_toggle_button.setParent(self._title_frame)
			if self._collapsed:
				self._expand_toggle_button.setIcon(resources.icon('sort_closed'))
			else:
				self._expand_toggle_button.setIcon(resources.icon('sort_down'))
			self._folder_icon.setAttribute(Qt.WA_TransparentForMouseEvents)
			spacer_item = QSpacerItem(10, 10, QSizePolicy.Expanding, QSizePolicy.Minimum)

			self._horizontal_layout.addWidget(self._expand_toggle_button)
			self._horizontal_layout.addWidget(self._folder_icon)
			self._horizontal_layout.addItem(spacer_item)
			self.setMinimumSize(self._title_frame.sizeHint().width(), self._title_frame.sizeHint().height() + 3)
			self._horizontal_layout.addWidget(self._group_text_edit)
			self._horizontal_layout.addLayout(self._title_extras_layout)
			self._horizontal_layout.addWidget(self._delete_button)
			self._horizontal_layout.setStretchFactor(self._group_text_edit, 4)

		def _setup_signals(self):
			"""
			Internal function that setups group widget signals.
			"""

			pass

	def __init__(
			self, locked: bool = False, allow_sub_groups: bool = True,
			custom_tree_widget_item_class: Type = QTreeWidgetItem, parent: QWidget | None = None):
		super().__init__(parent)

		self._dropped_items = None													# type: List[GroupedTreeWidget.TreeWidgetItem]
		self._drop_cancelled = False
		self._dragged_items = None													# type: List[GroupedTreeWidget.TreeWidgetItem]
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

	@override(check_signature=False)
	def itemWidget(self, item: QTreeWidgetItem, column: int | None = None) -> QWidget:
		return self._item_widget(item, column)

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

	def set_drag_drop_enabled(self, flag: bool):
		"""
		Disables or enables drag and drop functionality for this tree widget.

		:param bool flag: True to enable drag and drop; False to disable it.
		"""

		if flag:
			self._item_widget_flags = self._item_widget_flags | Qt.ItemIsDragEnabled
			self._item_widget_unlocked_flags = self._item_widget_unlocked_flags | Qt.ItemIsDragEnabled
			self._group_unlocked_flags = self._group_flags | Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
		else:
			self._item_widget_flags = self._item_widget_flags & ~Qt.ItemIsDragEnabled
			self._item_widget_unlocked_flags = self._item_widget_unlocked_flags & ~Qt.ItemIsDragEnabled
			self._group_unlocked_flags = self._group_flags & ~Qt.ItemIsDragEnabled & ~Qt.ItemIsDropEnabled

		self._apply_flags()

	def iterator(self) -> Iterator[GroupedTreeWidget.TreeWidgetItem]:
		"""
		Generator function that iterates over all tree widget items.

		:return: iterated tree widget items.
		:rtype: Iterator[GroupedTreeWidget.TreeWidgetItem]
		"""

		for item in qtutils.safe_tree_widget_iterator(self):
			yield item

	def item_widgets(
			self, item_type: str | None = None, tree_item: GroupedTreeWidget.TreeWidgetItem | None = None) -> List[QWidget]:
		"""
		Returns list of widgets of all the tree items.

		:param str or None item_type: optional item type to get widgets for.
		:param GroupedTreeWidget.TreeWidgetItem or None tree_item: optional parent tree item to get widgets for.
		:return: list of widgets found.
		:rtype: List[QWidget]
		"""

		iterator_item = tree_item if tree_item is not None else self

		widgets = []
		for found_tree_item in qtutils.safe_tree_widget_iterator(iterator_item):
			if found_tree_item is not None:
				item_widget = self._item_widget(found_tree_item)
				if item_widget is None:
					continue
				if (item_type is not None and self._item_type(found_tree_item) == item_type) or item_type is None:
					widgets.append(item_widget)

		return widgets

	def add_new_item(
			self, name: str, widget: QWidget | None = None, item_type: str = ITEM_TYPE_WIDGET,
			widget_info: str | int | None = None, icon: QIcon | None = None) -> GroupedTreeWidget.TreeWidgetItem:
		"""
		Adds a new item based on given type. Supported types are:
			- 'WIDGET': tree widget item with customized widget. Cannot have children.
			- 'GROUP': tree widget item without customized widget. Can have children.

		:param str name: name for the item.
		:param QWidget or None widget: optional widget to insert into the tree widget item.
		:param str item_type: item type to create ('WIDGET' or 'GROUP').
		:param str or int or None widget_info: optinal widget info data.
		:param QIcon or None icon: optional tree widget item icon.
		:return: newly created tree widget item.
		:rtype: GroupedTreeWidget.TreeWidgetItem
		"""

		flags = self._item_widget_flags if item_type == self.ITEM_TYPE_WIDGET else self._group_flags
		item = self.currentItem()
		tree_parent = self if item is not None else None

		new_tree_item = GroupedTreeWidget.TreeWidgetItem(name=name, flags=flags, after=item, parent=tree_parent)
		new_tree_item.setData(GroupedTreeWidget.DATA_COLUMN, Qt.EditRole, item_type)
		new_tree_item.setData(GroupedTreeWidget.ITEM_WIDGET_INFO_COLUMN, Qt.EditRole, widget_info)

		if icon is not None:
			new_tree_item.setIcon(GroupedTreeWidget.WIDGET_COLUMN, icon)

		self.addTopLevelItem(new_tree_item)

		if widget:
			widget.setParent(self)
			if self.updatesEnabled():
				self.refresh()
			self.setItemWidget(new_tree_item, GroupedTreeWidget.WIDGET_COLUMN, widget)
			if hasattr(widget, 'toggleExpandRequested'):
				widget.toggleExpandRequested.connect(self.refresh)
				widget.toggleExpandRequested.connect(new_tree_item.setExpanded)

		self.setCurrentItem(new_tree_item)

		return new_tree_item

	def refresh(self, delay: bool = False):
		"""
		Updates the tree widget so the row heights of the tree widget items matches the desired sizeHint.

		:param bool delay: whether to refresh it with delay.
		"""

		self.setUpdatesEnabled(False)
		if delay:
			def _process():
				qtutils.process_ui_events()
				self.refresh(delay=False)
			qtutils.single_shot_timer(_process)
			return

		self.insertTopLevelItem(0, QTreeWidgetItem())
		self.takeTopLevelItem(0)
		self.setUpdatesEnabled(True)

	def filter(self, text: str):
		"""
		Hides anything that does not contain the filtered text.

		:param str text: filter text.
		"""

		for tree_item in qtutils.safe_tree_widget_iterator(self):
			name = self._item_name(tree_item)
			tree_item.setHidden(text not in name.lower())

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

		self.itemSelectionChanged.connect(self._on_tree_selection_changed)

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

	def _item_name(self, tree_item: QTreeWidgetItem) -> str:
		"""
		Returns the name of the given tree item.

		:param QTreeWidgetItem tree_item: tree item to get name of.
		:return: tree item name.
		:rtype: str
		"""

		item_type = self._item_type(tree_item)
		widget = self._item_widget(tree_item)
		if item_type == self.ITEM_TYPE_WIDGET:
			if isinstance(widget, GroupedTreeWidget.ItemWidgetLabel):
				return widget.text()
			try:
				return widget.name
			except AttributeError:
				return tree_item.text(self.WIDGET_COLUMN)
		elif item_type == self.ITEM_TYPE_GROUP:
			return tree_item.text(self.WIDGET_COLUMN)

	def _item_widget(self, tree_item: QTreeWidgetItem, column: int | None = None) -> QWidget:
		"""
		Returns the intenral tree item widget.

		:param QTreeWidgetItem tree_item: tree item to get widget of.
		:param int column: column to get widget for.
		:return: tree item widget.
		:rtype: QWidget
		"""

		return super().itemWidget(tree_item, column or self.WIDGET_COLUMN)

	def _apply_flags(self):
		"""
		Internal function that applies internal group and item widget flags to all current tree widget items.
		"""

		for tree_item in qtutils.safe_tree_widget_iterator(self):
			if self._item_type(tree_item) == self.ITEM_TYPE_WIDGET:
				tree_item.setFlags(self._item_widget_flags)
			elif self._item_type(tree_item) == self.ITEM_TYPE_GROUP:
				tree_item.setFlags(self._group_flags)

	def _on_tree_selection_changed(self):
		"""
		Internal callback function that is called each time tree item selection changes.
		"""

		pass
