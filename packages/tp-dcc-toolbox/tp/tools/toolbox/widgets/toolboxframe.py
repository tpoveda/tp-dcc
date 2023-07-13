from __future__ import annotations

import typing
from typing import Tuple, Type

from tp.common.qt import api as qt
from tp.common.python import helpers
from tp.tools.toolbox.widgets import toolboxtoolbar, toolboxtree, toolboxmenubutton

if typing.TYPE_CHECKING:
	from tp.tools.toolbox.view import ToolBoxWindow
	from tp.tools.toolbox.manager import ToolUisManager


class ToolboxFrame(qt.QFrame):
	"""
	Custom frame that contains the main body of the toolbox UI, which includes the title bar.
	"""

	resizeRequested = qt.Signal()
	toolUiToggled = qt.Signal()
	toolUiClosed = qt.Signal()

	def __init__(
			self, toolbox_window: ToolBoxWindow, tool_uis_manager: ToolUisManager,
			icon_color: Tuple[int, int, int] = (255, 255, 255), hue_shift: int = -30, show_menu_button: bool = True,
			initial_group: str | None = None, icon_size: int = 20, icon_padding: int = 2, start_hidden: bool = False,
			switch_on_click: bool = True, toolbar_hidden: bool = False, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		if start_hidden:
			self.hide()

		self._current_group = None								# type: str
		self._toolbox_window = toolbox_window
		self._tool_uis_manager = tool_uis_manager
		self._icon_color = icon_color
		self._hue_shift = hue_shift
		self._switch_on_click = switch_on_click

		self._main_layout = qt.vertical_layout(margins=(0, 0, 0, 0), parent=self)
		self._top_bar_layout = qt.horizontal_layout(margins=(0, 3, 0, 0))
		self._toolbar = toolboxtoolbar.ToolboxToolBar(
			toolbox_frame=self, tool_uis_manager=self._tool_uis_manager, icon_size=icon_size, icon_padding=icon_padding,
			start_hidden=toolbar_hidden, parent=self)
		self._toolbar.set_icon_padding(1)
		self._toolbar.set_icon_size(18)
		self._toolbar.flow_layout.set_spacing_y(qt.dpi_scale(3))
		self._tree = toolboxtree.ToolboxTreeWidget(tool_uis_manager=self._tool_uis_manager, parent=self)
		self._menu_button = toolboxmenubutton.ToolboxMenuButton(
			tool_uis_manager=self._tool_uis_manager, size=16, parent=self)
		self._menu_button.menu_align = qt.Qt.AlignRight
		self._menu_button.setVisible(False)

		toolbox_group_type = helpers.first_in_list(self._tool_uis_manager.group_types())
		self.set_group(initial_group or toolbox_group_type)

		self._setup_ui()

	@property
	def tree(self) -> toolboxtree.ToolboxTreeWidget:
		return self._tree

	@property
	def menu_button(self) -> toolboxmenubutton.ToolboxMenuButton:
		return self._menu_button

	@property
	def toolbox_window(self) -> ToolBoxWindow:
		return self._toolbox_window

	def force_refresh(self):
		"""
		Forces toolbox frame UI refresh.
		"""

		qt.QApplication.processEvents()
		self._toolbar.update_widgets_overflow()
		window = self._toolbox_window.parent_container
		self.setUpdatesEnabled(False)
		try:
			size = window.size()
			window.setUpdatesEnabled(False)
			window.resize(size.width() + 1, size.height())
			window.resize(size.width(), size.height())
		finally:
			window.setUpdatesEnabled(True)
			self.setUpdatesEnabled(True)

		self.update_colors()

	def set_group(self, group_type: str | None):
		"""
		Updates the icons in the toolbar based on the given toolbox type ("Assets", "Rigging", "Animation", ...).

		:param str group_type: toolbox type to set as the active one. If None, nothing happens.
		"""

		if not group_type or self._current_group == group_type:
			return

		self._current_group = group_type

		self._toolbar.clear()
		self._icon_color = self._tool_uis_manager.group_color(group_type)

		tool_ui_classes = self._tool_uis_manager.tool_uis(group_type)
		for tool_ui_class in tool_ui_classes:
			self._add_tool_ui(tool_ui_class)

		qt.QTimer.singleShot(0, self.force_refresh)

	def toggle_tool_ui(
			self, tool_ui_id: str, activate: bool = True, hidden: bool = False,
			keep_open: bool = False) -> toolboxtree.ToolboxTreeWidget.ToolboxTreeWidgetItem:
		"""
		Toggles tool Ui with given id.

		:param str tool_ui_id: id of the tool Ui to toggle.
		:param bool activate: whether to activate tool ui.
		:param bool hidden: whether to show the tool Ui widget.
		:param bool keep_open: whether to keep open tool ui.
		:return: newly created tool ui widget.
		:rtype: toolboxtree.ToolboxTreeWidget.ToolboxTreeWidgetItem
		"""

		item = self._tree.tool_ui(tool_ui_id)
		if item:
			if not keep_open or item.hidden:
				item.toggle_hidden(activate=activate)
		else:
			item = self._tree.add_tool_ui(tool_ui_id, activate=activate)
			if self._switch_on_click:
				group_type = self._tool_uis_manager.group_from_tool_ui(tool_ui_id)
				self.set_group(group_type)

		if hidden:
			item.setHidden(True)

		self.resizeRequested.emit()
		self.toolUiToggled.emit()
		self.update_colors()

		return item

	def update_colors(self):
		"""
		Function that updates the colors of the toolbar buttons.
		"""

		widgets = [r.widget() for r in self._toolbar.flow_layout.items_list] + qt.layout_widgets(self._toolbar.overflow_layout)
		active_items = self._tree.active_items()
		actives = []
		for a in actives:
			item = a[0]
			if a[1] != toolboxtree.ToolboxTreeWidget.ACTIVE_ITEM_HIDDEN:
				actives.append(item.widget.id)

		# self._menu_button._toolbox_popup.update_colors(actives)

		for w in widgets:
			pass

	def calculate_size_hint(self) -> qt.QSize:
		"""
		Returns the height of the toolbox frame based on the contents of the tree.

		:return: toolbox frame size hint.
		:rtype: qt.QSize
		"""

		width = self.width()
		height = self._tree.calculate_content_height()

		return qt.QSize(width, height)

	def _setup_ui(self):
		"""
		Internal function that initializes toolbox frame widgets.
		"""

		self._top_bar_layout.addWidget(self._toolbar)
		self._top_bar_layout.addSpacing(0)
		self._main_layout.addLayout(self._top_bar_layout)
		self._main_layout.addWidget(self._tree)

	def _add_tool_ui(self, tool_ui_class: Type):
		"""
		Creates a new toolbar button associated with the given tool ui class.

		:param Type tool_ui_class: tool ui class to associate to button.
		"""

		new_button = self._toolbar.add_tool_ui(tool_ui_class, toggle_connect=self._on_toggle_select)
		new_button.rightClicked.disconnect()
		new_button.rightClicked.connect(
			lambda: self._on_tool_ui_right_click_menu(new_button.property('toolUiId'), new_button))\

	def _on_toggle_select(self, tool_ui_id: str, activate: bool = True, hidden: bool = False, keep_open: bool = False):
		"""
		Internal callback function that toggles tool UI.

		:param tool_ui_id:
		:param activate:
		:param hidden:
		:param keep_open:
		:return:
		"""

		pass

	def _on_tool_ui_right_click_menu(self, tool_ui_id: str, button):
		pass
