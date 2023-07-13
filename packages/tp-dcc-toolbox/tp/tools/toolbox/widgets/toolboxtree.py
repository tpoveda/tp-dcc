from __future__ import annotations

import uuid
import typing
from typing import Tuple, List, Dict

from overrides import override

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.toolbox.manager import ToolUisManager
	from tp.tools.toolbox.widgets.toolui import ToolUiWidget
	from tp.tools.toolbox.widgets.toolboxframe import ToolboxFrame

_TOOLBOX_TREE_WIDGET_ITEM_DATA = {}


class ToolboxTreeWidget(qt.GroupedTreeWidget):

	class ToolboxTreeWidgetItem(qt.QTreeWidgetItem):
		"""
		Custom tree widget item that represents a toolbox tool Ui within toolbox tree widget
		"""

		START_LARGEST = -1
		START_SMALLEST = 0

		def __init__(
				self, tool_ui_id: str = '', color: Tuple[int, int, int] = (255, 255, 255),
				tool_uis_manager: ToolUisManager | None = None, tree_widget: ToolboxTreeWidget | None = None,
				tool_ui_widget: ToolUiWidget | None = None, parent: ToolboxTreeWidget.ToolboxTreeWidgetItem | None = None):
			super().__init__(parent)

			self._color = color
			self._tree_item = self
			self._tool_ui_id = tool_ui_id
			self._tool_uis_manager = tool_uis_manager
			self._initial_row_height = -1
			self._widget_contents = None					# type: List[qt.QWidget]
			tool_ui_widget_class = self._tool_uis_manager.tool_ui(tool_ui_id)
			self._tool_ui_widget = tool_ui_widget or tool_ui_widget_class(
				icon_color=color, widget_item=self, tree_widget=tree_widget)
			self._stacked_layout = self._tool_ui_widget.stacked_widget
			self._display_mode = self._init_display_size(ToolboxTreeWidget.ToolboxTreeWidgetItem.START_SMALLEST)

			self._setup_ui()

		def __hash__(self):
			return hash(id(self))

		@property
		def hidden(self) -> bool:
			return self.isHidden()

		@property
		def widget(self) -> ToolUiWidget:
			return self._tool_ui_widget

		def id(self) -> str:
			"""
			Returns tool ui id.

			:return: tool ui id.
			:rtype: str
			"""

			return self._tool_ui_widget.id

		def set_icon_color(self, color: Tuple[int, int, int] = (255, 255, 255)):
			"""
			Sets the color for the tree widget item icon.

			:param Tuple[int, int, int] color: icon color.
			"""

			self._color = color
			self._tool_ui_widget.set_icon_color(color)

		def widget_data(self) -> Dict:
			"""
			Returns dictionary with the data of the tool ui widget.

			:return: tool ui widget data.
			:rtype: Dict
			"""

			return {'toolUiId': self.widget.id, 'properties': self.widget.properties}

		def apply_widget(self, activate: bool = True, recreate_widget: bool = False):
			"""
			Applies the item widget to the tree widget item.

			:param bool activate: whether to activate item widget.
			:param bool recreate_widget: whether to force the recreation of the item widget.
			"""

			if recreate_widget:
				tool_ui_widget_class = self._tool_uis_manager.tool_ui(self._tool_ui_id)
				self._tool_ui_widget = tool_ui_widget_class(
					icon_color=self._color, widget_item=self, tree_widget=self.treeWidget())

			self._tool_ui_widget.setParent(self.treeWidget())

			self.treeWidget().setItemWidget(self, 0, self._tool_ui_widget)
			self._initial_row_height = self.treeWidget().rowHeight(self.treeWidget().indexFromItem(self))

			self._setup_widget_signals()

			self._tool_ui_widget.pre_content_setup()
			self._widget_contents = self._tool_ui_widget.contents()
			for content_widget in self._widget_contents:
				self._tool_ui_widget.add_stacked_widget(content_widget)

			self._tool_ui_widget.auto_link_properties(self._widget_contents)
			self.setData(qt.GroupedTreeWidget.DATA_COLUMN, qt.Qt.EditRole, qt.GroupedTreeWidget.ITEM_TYPE_WIDGET)
			data_uuid = str(uuid.uuid4())
			_TOOLBOX_TREE_WIDGET_ITEM_DATA[data_uuid] = self.widget_data()
			saved_data = self.data(qt.GroupedTreeWidget.ITEM_WIDGET_INFO_COLUMN, qt.Qt.EditRole) or data_uuid
			self.setData(qt.GroupedTreeWidget.ITEM_WIDGET_INFO_COLUMN, qt.Qt.EditRole, saved_data)
			self._update_properties_from_data()
			self._tool_ui_widget.populate_widgets()
			self._tool_ui_widget.post_content_setup()
			self._tool_ui_widget.updatePropertyRequested.emit()
			self.set_current_index(self._display_mode, activate)
			self._tool_ui_widget.update_display_button()

		def set_current_index(self, index: int, activate: bool = True):
			"""
			Sets the active stacked content widget to display.

			:param int index: index of the content to display.
			:param bool activate: whether to activate the tool ui displayed.
			"""

			if index == -1:
				index  = self._tool_ui_widget.count() - 1
				# self._tool_ui_widget.display_mode_button.inita

			self._tool_ui_widget.save_properties()
			self._tool_ui_widget.set_current_index(index)
			self._display_mode = index

			if self.treeWidget() is not None:
				self.treeWidget().activate_item(self, activate=activate)

		def collapse(self):
			"""
			Collapses tool ui widget.
			"""

			self._tool_ui_widget.collapse()

		def expand(self, emit: bool = False):
			"""
			Expands tool ui widget.

			:param bool emit: whether to emit signals.
			"""

			self._tool_ui_widget.expand(emit=emit)

		def _update_properties_from_data(self):
			pass

		def _setup_ui(self):
			"""
			Internal function that initializes toolbox tree widget item UI.
			"""

			self.setChildIndicatorPolicy(qt.QTreeWidgetItem.DontShowIndicator)
			self.set_icon_color(self._color)
			self.setData(qt.GroupedTreeWidget.DATA_COLUMN, qt.Qt.EditRole, qt.GroupedTreeWidget.ITEM_TYPE_WIDGET)

		def _setup_widget_signals(self):
			"""
			Internal function that setup toolbox tree widget item signals.
			"""

			try:
				self._tool_ui_widget.maximized.disconnect()
			except (RuntimeError, TypeError):
				pass
			try:
				self._tool_ui_widget.deletePressed.disconnect()
			except (RuntimeError, TypeError):
				pass

			self._tool_ui_widget.maximized.connect(lambda: self.treeWidget().activate_item(self, activate=True))
			self._tool_ui_widget.minimized.connect(lambda: self.treeWidget().activate_item(self, activate=False))

		def _init_display_size(self, display_size: START_LARGEST):
			"""
			Internal function that initializes display size for the tool uis.

			:param int display_size: tool ui size.
			"""

			self._display_mode = display_size
			return display_size

	ACTIVE_ITEM_ACTIVE = 0
	ACTIVE_ITEM_INACTIVE = 1
	ACTIVE_ITEM_HIDDEN = 2

	toolUiHidden = qt.Signal(str)

	def __init__(self, tool_uis_manager: ToolUisManager | None = None, parent: ToolboxFrame | None = None):
		super().__init__(custom_tree_widget_item_class=ToolboxTreeWidget.ToolboxTreeWidgetItem, parent=parent)

		self._tool_uis_manager = tool_uis_manager
		self._toolbox_frame = parent
		self._last_hidden = []								# type: List[str]
		self._properties = {}
		self._toolset_ids_dragging = None
		self._toolbox_window = None
		self._toolbox_items = []

	@property
	def toolbox_frame(self) -> ToolboxFrame:
		return self._toolbox_frame

	@override(check_signature=False)
	def refresh(self, disable_scrollbars: bool = False):
		"""
		Internal function that updates tree widget.

		:param bool disable_scrollbars: whether scrollbars should be disabled.
		"""

		vertical_policy = None
		if disable_scrollbars:
			vertical_policy = self.verticalScrollBarPolicy()
			self.setVerticalScrollBarPolicy(qt.Qt.ScrollBarAlwaysOff)

		super().refresh()

		self._toolbox_frame.resizeRequested.emit()

		if vertical_policy is not None:
			self.setVerticalScrollBarPolicy(vertical_policy)

	def refresh_tree(self, delayed: bool = False):
		"""
		Similar to refresh function with some extra refreshes.

		:param bool delayed: whether to refresh with some delay.
		"""

		if delayed:
			qt.QTimer.singleShot(0, self.refresh_tree)
			return

		self.setUpdatesEnabled(False)
		try:
			self.refresh()
			self._toolbox_frame.toolbox_window.resize_window()
			self.refresh()
		finally:
			self.setUpdatesEnabled(False)

	def add_tool_ui(self, tool_ui_id: str, activate: bool = True) -> ToolboxTreeWidgetItem:
		"""
		Adds a new toolbox tree widget item that matches given tool Ui id.

		:param str tool_ui_id: ID of the tool ui to add.
		:param bool activate: whether to activate tree widget item after adding it.
		:return: newly created tool ui tree widget item.
		:rtype: ToolboxTreeWidgetItem
		"""

		index = self.invisibleRootItem().childCount()
		return self.insert_tool_ui(index, tool_ui_id, activate=activate)

	def insert_tool_ui(
			self, index: int, tool_ui_id: str, activate: bool = True,
			tree_parent: ToolboxTreeWidgetItem | None = None) -> ToolboxTreeWidgetItem:
		"""
		Inserts a new toolbox tree widget item that maches given tool Ui id.

		:param int index: index to insert item within tree widget.
		:param str tool_ui_id: ID of the tool ui to insert.
		:param bool activate: whether to activate tree widget item after adding it.
		:param ToolboxTreeWidgetItem or None tree_parent: optional tree widget item parent.
		:return: newly created tool ui tree widget item.
		:rtype: ToolboxTreeWidgetItem
		"""

		color = self._tool_uis_manager.tool_ui_color(tool_ui_id)
		root = tree_parent or self.invisibleRootItem()
		tree_widget_item = ToolboxTreeWidget.ToolboxTreeWidgetItem(
			tool_ui_id=tool_ui_id, color=color, tool_uis_manager=self._tool_uis_manager, tree_widget=self,
			parent=tree_parent)
		child_count = root.childCount()
		if index > child_count:
			index = root.childCount()
		root.insertChild(index, tree_widget_item)
		tree_widget_item.setFlags(self._item_widget_flags)
		tree_widget_item.apply_widget(activate=activate)

		return tree_widget_item

	def tool_ui(self, tool_ui_id: str) -> ToolboxTreeWidgetItem | None:
		"""
		Returns the toolbox tree widget item based on the given tool ui ID.

		:param str tool_ui_id: id of the tool uid tree widget item we want to retrieve.
		:return: found tree widget item that matches given id.
		:rtype: ToolboxTreeWidgetItem or None
		"""

		found_item = None
		for it in self.iterator():
			if it.id() == tool_ui_id:
				found_item = it
				break

		return found_item

	def activate_item(
			self, item: ToolboxTreeWidget.ToolboxTreeWidgetItem, activate: bool = True, close_others: bool = False):
		"""
		Activates given tree widget item.

		:param ToolboxTreeWidget.ToolboxTreeWidgetItem item: item to activate.
		:param bool activate: whether item should be activated or deactivated.
		:param bool close_others: whether other opened tree widget items should be closed.
		"""

		tool_ui_widget = item.widget
		tool_ui_widget.set_active(active=activate, emit=False)
		if close_others:
			for tree_item in qt.safe_tree_widget_iterator(self):
				if tree_item is not item:
					tree_item.collapse()

		qt.QTimer.singleShot(0, lambda: self.refresh())

	def active_items(self) -> List[Tuple[ToolboxTreeWidget.ToolboxTreeWidgetItem, int], ...]:
		"""
		Returns a list of tuples with the available item instances as the first tuple element and whether the item is
		active as a second tuple element.

		:return: list of active items.
		:rtype: List[Tuple[ToolboxTreeWidget.ToolboxTreeWidgetItem, int], ...]
		"""

		result = []
		for it in self.iterator():
			tree_item = it					# type: ToolboxTreeWidget.ToolboxTreeWidgetItem
			if tree_item is None:
				continue
			state = self.ACTIVE_ITEM_ACTIVE
			if not tree_item.widget.isVisible():
				state = self.ACTIVE_ITEM_HIDDEN
			elif tree_item.widget.collapsed:
				state = self.ACTIVE_ITEM_INACTIVE
			result.append((tree_item, state))

		return result

	def calculate_content_height(self) -> int:
		"""
		Returns the height of the contents within the tree.

		:return: content height.
		:rtype: int
		"""

		content_height = 0
		for i in range(self.topLevelItemCount()):
			item = self.topLevelItem(i)
			if isinstance(item, ToolboxTreeWidget.ToolboxTreeWidgetItem) and not item.hidden:
				content_height += item.widget.sizeHint().height()

		return content_height

	def _setup_ui(self):

		self.header().hide()

		super()._setup_ui()

		self.setMouseTracking(True)
		self.setIndentation(0)
		self._setup_drag_drop()
		self.setMinimumHeight(0)
		self.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Ignored)
		self.toolUiHidden.connect(self._on_tool_ui_hidden)

	def _on_tool_ui_hidden(self, tool_ui_id: str):
		"""
		Internal callback function that is called each time a tool UI is hidden.

		:param str too_ui_id: ID of the hidden tool UI.
		"""

		if tool_ui_id not in self._last_hidden:
			self._last_hidden.append(tool_ui_id)
