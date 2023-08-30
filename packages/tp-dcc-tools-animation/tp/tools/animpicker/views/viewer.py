from __future__ import annotations

import typing
from typing import List, Callable

from overrides import override

from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.tools.animpicker import consts, uiutils
from tp.tools.animpicker.views import main
from tp.tools.animpicker.widgets import buttons, tabs, dialogs, lineedits

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.widgets.graphics import DropScene
	from tp.tools.animpicker.controller import AnimPickerController
	from tp.tools.animpicker.events import (
		PreRefreshEvent, RefreshEvent, LoadPickerNodeToMapEvent, PreMatchPrefixToMapEvent, MatchPrefixToMapEvent,
		PreLoadMapEvent, LoadMapEvent
	)


class AnimPickerViewer(qt.FramelessWindow):

	def __init__(self, controller: AnimPickerController, parent: qt.QWidget | None = None):

		self._controller = controller

		super().__init__(
			title=f'Animation Picker Launcher {main.AnimPickerView.VERSION}', width=800, height=600, parent=parent)

	@override
	def setup_ui(self):
		super().setup_ui()

		self.set_main_layout(qt.vertical_layout(margins=(0, 0, 0, 0)))
		main_layout = self.main_layout()
		self._viewer_widget = AnimPickerViewerWidget(controller=self._controller, parent=self)
		main_layout.addWidget(self._viewer_widget)


class AnimPickerViewerWidget(qt.QWidget):

	TAB_WIDGET_CLASS = tabs.TabWidget

	def __init__(
			self, controller: AnimPickerController, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._controller = controller

		self._top_menu_visible = True
		self._pose_global_data = []
		self._pose_nodes = None
		self._pose_channels = None
		self._block_callback = False
		self._recent_directory = ''
		self._auto_key_state = False
		self._select_guide_dialog = None
		self._callbacks = []

		self.setup_ui()
		self.setup_signals()

	@property
	def tab_widget(self) -> tabs.TabWidget | tabs.EditableTabWidget:
		return self._tab_widget

	@property
	def group_line_edit(self) -> lineedits.PopupLineEdit:
		return self._group_line_edit

	def setup_ui(self):
		"""
		Setup animation picker viewer UI.
		"""

		main_layout = qt.vertical_layout(margins=(2, 2, 2, 2))
		self.setLayout(main_layout)

		self.setWindowFlags(self.windowFlags() ^ qt.Qt.WindowContextHelpButtonHint)
		self.setLocale(qt.QLocale(qt.QLocale.English))
		self.setFocusPolicy(qt.Qt.StrongFocus)
		self._upper_toolbar = qt.QToolBar(parent=self)
		self._upper_toolbar.setContextMenuPolicy(qt.Qt.PreventContextMenu)
		self._upper_toolbar.setFloatable(False)
		self._upper_toolbar.setIconSize(qt.QSize(16, 16))
		self._lower_toolbar = qt.QToolBar(parent=self)
		self._lower_toolbar.setContextMenuPolicy(qt.Qt.PreventContextMenu)
		self._lower_toolbar.setFloatable(False)
		self._lower_toolbar.setIconSize(qt.QSize(32, 32))
		top_menu_toggle_layout = qt.horizontal_layout(margins=(1, 0, 1, 1))
		self._top_menu_toggle_button = buttons.ArrowToggleButton(parent=self)
		self._top_menu_toggle_button.setToolButtonStyle(qt.Qt.ToolButtonIconOnly)
		self._top_menu_toggle_button.setIconSize(qt.QSize(8, 8))
		self._top_menu_toggle_button.setMinimumSize(qt.QSize(0, 12))
		self._top_menu_toggle_button.upside_down = False
		top_menu_toggle_layout.addWidget(self._top_menu_toggle_button)
		self._tab_widget = self.TAB_WIDGET_CLASS(parent=self)

		main_layout.addWidget(self._upper_toolbar)
		main_layout.addWidget(self._lower_toolbar)
		main_layout.addLayout(top_menu_toggle_layout)
		main_layout.addWidget(self._tab_widget)

		self._setup_actions()
		self._setup_upper_toolbar_menu()
		self._setup_lower_toolbar_menu()
		self._dispatcher = uiutils.ThreadDispatcher(self)
		self._dispatcher.start()

	def setup_signals(self):
		"""
		Connect widget signals and bind widgets to controller.
		"""

		self._controller.preRefresh.emit(self._on_pre_refresh)
		self._controller.doRefresh.connect(self._on_refresh)
		self._controller.loadPickerNodeToMap.connect(self._on_load_picker_node_to_map)
		self._controller.preMatchPrefixToMap.connect(self._on_pre_match_prefix_to_map)
		self._controller.matchPrefixToMap.connect(self._on_match_prefix_to_map)
		self._controller.preLoadMap.connect(self._on_pre_load_map)
		self._controller.loadMap.connect(self._on_load_map)


		self._setup_tab_signals()

	def _setup_tab_signals(self):
		"""
		Internal function that setup tab widget related signals.
		"""

		self.tab_widget.currentChanged.connect(self.set_tab_data)

	def refresh(self, *args):
		"""
		Refreshes viewer.
		"""

		self._controller.refresh(*args)

	def set_tab_data(self, index: int):
		"""
		Sets the data of tab widget with given index.

		:param int index: tab widget index.
		"""

		tab = self._tab_widget.widget(index)
		if not tab:
			return
		if tab.use_prefix:
			self._prefix_checkbox.setChecked(True)
			self._prefix_line_edit.setText(tab.prefix)
		else:
			self._prefix_checkbox.setChecked(False)
			self._prefix_line_edit.setText('')
			self._controller.match_prefix_to_map(index)
		self._controller.load_map(index)

	def map_name(self, index: int = -1) -> str:
		"""
		Returns the name of the map with given index.

		:param int index: map index.
		:return: map name.
		:rtype: str
		"""

		if index < 0:
			index = self.tab_widget.currentIndex()
		return self.tab_widget.tabText(index)

	def tear_off_dialogs(self) -> List[dialogs.TearOffDialog]:
		"""
		Returns all tear off dialogs attached to this viewer.

		:return: list of tear off dialogs.
		:rtype: List[dialogs.TearOffDialog]
		"""

		return self.findChildren(dialogs.TearOffDialog)

	@uiutils.scene_exists
	def select_current_all_items(self, scene: DropScene = None):
		"""
		Selects all scene items if it exists.

		:param DropScene scene: argument that is filled with the scene whose items we want to select.
		"""

		if not scene:
			return

		scene.select_in_rect(scene.itemsBoundingRect())
		scene.do_all_items('Select', 'All')

	@uiutils.scene_exists
	def reset_all(self, scene: DropScene = None):
		"""
		Deselects all scene items if it exists.

		:param DropScene scene: argument that is filled with the scene whose items we want to select.
		"""

		if not scene:
			return

		scene.select_in_rect(scene.itemsBoundingRect())
		scene.do_all_items('Select', 'All')

	@uiutils.scene_exists
	def reset_transform(self, scene: DropScene = None):
		"""
		Reset all scene items transforms.

		:param DropScene scene: argument that is filled with the scene whose items we want to select.
		"""

		if not scene:
			return

		scene.do_all_items('Reset', 'Transform')

	@uiutils.scene_exists
	def reset_defined(self, scene: DropScene = None):
		"""
		Reset all scene items defined attributes.

		:param DropScene scene: argument that is filled with the scene whose items we want to select.
		"""

		if not scene:
			return

		scene.do_all_items('Reset', 'Defined')

	@uiutils.scene_exists
	def key_all(self, scene: DropScene = None):
		"""
		Key all scene items transforms.

		:param DropScene scene: scene where items are located.
		"""

		if not scene:
			return

		scene.do_all_items('Key', 'All')

	@uiutils.scene_exists
	def key_transform(self, scene: DropScene = None):
		"""
		Key all scene items transforms.

		:param DropScene scene: scene where items are located.
		"""

		if not scene:
			return

		scene.do_all_items('Key', 'Transform')

	@uiutils.scene_exists
	def key_defined(self, scene: DropScene = None):
		"""
		Key all scene items user defined attributes.

		:param DropScene scene: scene where items are located.
		"""

		if not scene:
			return

		scene.do_all_items('Key', 'Defined')

	def show_selected_list(self, *args):
		"""
		Shows a dialog with all current selected nodes.
		"""

		raise NotImplementedError

	def _create_action(
			self, text: str, slot: Callable | None = None, shortcut: str | qt.QKeySequence | None = None,
			icon: qt.QIcon | None = None, tooltip: str | None = None, checkable: bool = False,
			signal: str = 'triggered') -> qt.QAction:
		"""
		Internal function that creates a new action.

		:param str text: action text.
		:param Callable or None slot: optional function that should be called when action signal is emitted.
		:param str or qt.QKeySequence shortcut: optional action shortcut.
		:param qt.QIcon or None icon: optional action icon.
		:param str or None tooltip: optional action tooltip.
		:param bool checkable: sets whether action is checkable.
		:param str signal: signal name that should be called.
		:return: newly created action.
		:rtype: qt.QAction
		"""

		action = qt.QAction(text, self)
		if icon is not None:
			action.setIcon(icon)
		if shortcut is not None:
			action.setShortcut(shortcut)
		if tooltip is not None:
			action.setToolTip(tooltip)
			action.setStatusTip(tooltip)
		if slot is not None:
			getattr(action, signal).connect(slot)
		if checkable:
			action.setCheckable(True)

		return action

	def _setup_actions(self):
		"""
		Internal function that setup actions.
		"""

		self._refresh_action = self._create_action(
			'Refresh', self.refresh, icon=resources.icon('refresh'),
			tooltip='Reload maps within current map group from picker nodes in scene.')
		self._load_file_action = self._create_action(
			'Load Map File', self._on_load_map_file_action_triggered, icon=resources.icon('open'),
			tooltip='Load a data file or files.\nYou can select multiple files.')
		self._info_action =self._create_action(
			'Info', self._on_info_action_triggered, icon=resources.icon('help'),
			tooltip='Open the link for documentation.')

	def _setup_upper_toolbar_menu(self):
		"""
		Internal function that setup toolbar menu.
		"""

		for action in [self._load_file_action, self._info_action, self._refresh_action]:
			self._upper_toolbar.addAction(action)
			self._upper_toolbar.widgetForAction(action).setFixedSize(24, 24)
		self._setup_upper_common_actions()

	def _setup_upper_common_actions(self):
		"""
		Internal function that set up the common actions that will appear on the upper toolbar menu.
		"""

		self._group_line_edit = lineedits.PopupLineEdit(parent=self)
		self._prefix_checkbox = qt.checkbox('Prefix', tooltip=consts.COPY_PREFIX_TOOLTIP, parent=self)
		self._prefix_checkbox.setFixedSize(qt.QSize(47, 18))

		self._copy_prefix_button = qt.tool_button(icon='play', tooltip=consts.COPY_PREFIX_TOOLTIP, parent=self)
		self._copy_prefix_button.setFixedSize(qt.QSize(20, 20))
		self._copy_prefix_button.setEnabled(False)
		self._copy_prefix_button.setAutoRaise(False)

		self._prefix_line_edit = qt.line_edit(
			tooltip='Type in prefix.\nOr click the arrow button on the left to copy prefix from selected object.',
			parent=self)
		self._prefix_line_edit.setFixedWidth(96)
		self._prefix_line_edit.setFocusPolicy(qt.Qt.StrongFocus)
		self._prefix_line_edit.setEnabled(False)

		self._upper_toolbar.addWidget(self._group_line_edit)
		self._upper_toolbar.addWidget(self._prefix_checkbox)
		self._upper_toolbar.addWidget(self._copy_prefix_button)
		self._upper_toolbar.addWidget(self._prefix_line_edit)

	def _setup_lower_toolbar_menu(self):
		"""
		Internal function that setup lower toolbar menu.
		"""

		pass

	def _on_load_map_file_action_triggered(self):
		"""
		Internal callback function that is called each time Load Map File action is triggered by the user.
		"""

		print('Loading map file ...')

	def _on_info_action_triggered(self):
		"""
		Internal callback function that is called each time Info action is triggered by the user.
		"""

		print('Showing info ...')

	def _on_pre_refresh(self, event: PreRefreshEvent):
		if event.args and event.args[0]:
			for dlg in self.tear_off_dialogs():
				dlg.setParent(None)
				dlg.close()
		current_index = self.tab_widget.currentIndex() if isinstance(self.sender(), qt.QAction) else -1
		event.current_index = current_index
		self._tab_widget.clear()
		if not event.nodes:
			event.result = False
			self._group_line_edit.clear()
		else:
			event.result = True

	def _on_refresh(self, event: RefreshEvent):
		self._group_line_edit.labels = event.group_names
		self._group_line_edit.setText(event.current_group_name)
		current_index = event.current_index
		if current_index > 0:
			self._tab_widget.setCurrentIndex(current_index)
		else:
			current_index = 0
		self._controller.load_picker_node_to_map(event.filtered_nodes)
		self.set_tab_data(current_index)

	def _on_load_picker_node_to_map(self, event: LoadPickerNodeToMapEvent):

		with qt.block_signals(self._tab_widget):
			compares = [(dlg.character_name, dlg.map_name) for dlg in self.tear_off_dialogs()]
			for index, picker_node in enumerate(event.nodes):
				character_name = event.character_names[index]
				subset = event.subsets[index]
				if (character_name, subset) in compares:
					continue
				self.tab_widget.add_graphics_tab(subset, change_current=False)
				size = event.sizes[index]
				if size:
					size = qt.QSize(*[int(v) for v in size.split(',')])
					scene = self.tab_widget.scene_at_index(index)
					scene.map_size = size
				view = self.tab_widget.view_at_index(index)
				view.picker_node = picker_node
				tab = self.tab_widget.widget(index)
				tab.use_prefix = event.use_prefixes[index]
				tab.prefix = event.prefixes[index]
				if event.referenced[index]:
					self.tab_widget.setTabIcon(index, resources.icon('lock'))

	def _on_pre_match_prefix_to_map(self, event: PreMatchPrefixToMapEvent):
		"""
		Internal callback function that is called before match prefix to map runs by controller.

		:param PreMatchPrefixToMapEvent event: event.
		"""

		event.map_name = self.map_name(event.index)
		event.result = True

	def _on_match_prefix_to_map(self, event: MatchPrefixToMapEvent):
		"""
		Internal callback function that handles match prefix.

		:param MatchPrefixToMapEvent event: event.
		"""

		self._prefix_checkbox.setChecked(event.use_prefix)
		prefix = event.prefix
		if prefix:
			self._prefix_line_edit.setText(prefix)
		else:
			split = event.picker_node.rsplit(':', 1)
			if len(split) == 2:
				self._prefix_line_edit.setText(f'{split[0]}:')
				self._prefix_checkbox.setChecked(True)
			else:
				self._prefix_line_edit.setText('')
		event.result = True

	def _on_pre_load_map(self, event: PreLoadMapEvent):
		view = self.tab_widget.view_at_index(event.index)
		event.result = False
		if view and not view.loaded:
			event.picker_node = view.picker_node
			event.result = True

	def _on_load_map(self, event: LoadMapEvent):
		pass