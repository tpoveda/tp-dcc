from __future__ import annotations

import typing
from typing import List, Dict

from tp.common.qt import api as qt
from tp.tools.scenesbrowser.widgets import thumbsbrowser

if typing.TYPE_CHECKING:
	from tp.preferences.assets import BrowserPreference
	from tp.tools.toolbox.widgets.toolui import ToolUiWidget
	from tp.tools.scenesbrowser.controller import ScenesBrowserController


class ScenesBrowserView(qt.QWidget):
	def __init__(
			self, tool_ui_widget: ToolUiWidget | None = None, controller: ScenesBrowserController | None = None,
			properties: List[Dict] | None = None, uniform_icons: bool = False, parent: qt.QWidget | None = None):
		super().__init__(parent=parent)

		self._tool_ui_widget = tool_ui_widget
		self._controller = controller
		self._thumbs_browser = None						# type: thumbsbrowser.ThumbsBrowser
		self._browser_model = None						# type: thumbsbrowser.SuffixFilterModel

		self._setup_widgets()
		self._setup_layouts()
		self._setup_signals()

		self.refresh_thumbs()

	def refresh_thumbs(self):
		"""
		Refreshes the thumb browser.
		"""

		self._thumbs_browser.refresh_thumbs()

	def _setup_widgets(self):
		"""
		Internal function that setup all scene browser widgets.
		"""

		browser_preferences = self._controller.scene_prefs().scene_assets		# type: BrowserPreference
		uniform_icons = browser_preferences.browser_uniform_icons()
		directories = browser_preferences.browser_folder_paths()

		self._thumbs_browser = thumbsbrowser.ThumbsBrowser(
			tool_ui_widget=self._tool_ui_widget, columns=3, fixed_height=382, uniform_icons=uniform_icons,
			item_name='Scene', apply_text='Load Scene', apply_icon='maya', create_text='Save', new_active=False,
			snapshot_active=True, clipboard_active=True, select_directories_active=True, parent=self)
		self._thumbs_browser.dots_menu.set_directory_active(False)
		self._thumbs_browser.dots_menu.set_create_active(True)
		self._thumbs_browser.dots_menu.set_rename_active(False)
		self._thumbs_browser.dots_menu.set_delete_active(True)
		self._thumbs_browser.dots_menu.set_snapshot_active(True)
		self._thumbs_browser.filter_menu.setEnabled(False)
		self._thumbs_browser.filter_menu.hide()
		self._thumbs_browser.dots_menu.insert_action_index(1, 'Import Scene', action_icon='import', data='import')
		self._thumbs_browser.dots_menu.insert_action_index(2, 'Reference Scene', action_icon='reference', data='reference')
		self._thumbs_browser.dots_menu.insert_action_index(3, 'Open Help', action_icon='help', data='help')

		self._browser_model = self._controller.browser_model(
			view=self._thumbs_browser, directories=directories, uniform_icons=uniform_icons,
			browser_preferences=browser_preferences)
		self._thumbs_browser.set_model(self._browser_model)

	def _setup_layouts(self):
		"""
		Internal function that setup all scene browser layouts.
		"""

		self._main_layout = qt.vertical_layout(
			spacing=0, margins=(
				qt.consts.WINDOW_SIDE_PADDING, qt.consts.WINDOW_TOP_PADDING,
				qt.consts.WINDOW_SIDE_PADDING, qt.consts.WINDOW_BOTTOM_PADDING))
		self.setLayout(self._main_layout)

		self._main_layout.addWidget(self._thumbs_browser)

	def _setup_signals(self):
		"""
		Internal function that setup widget signal connections.
		"""

		self._browser_model.itemSelectionChanged.connect(self._on_browser_model_selection_changed)
		self._browser_model.doubleClicked.connect(self._on_browser_model_double_clicked)

		self._thumbs_browser.dots_menu.applyAction.connect(self._on_thumbs_browser_dots_menu_apply_action_triggered)
		self._thumbs_browser.dots_menu.createAction.connect(self._on_thumbs_browser_dots_menu_create_action_triggered)
		self._thumbs_browser.dots_menu.refreshAction.connect(self._on_thumbs_browser_dots_menu_refresh_action_triggered)

	def _on_browser_model_selection_changed(self, file_name: str, item: thumbsbrowser.FileItem):
		"""
		Internal callback function that is called each time an item is selected within browser.

		:param str file_name: file name of the selected item without extension.
		:param thumbsbrowser.FileModel.FileItem item: selected item.
		"""

		default_items = self._controller.scene_prefs().scene_assets.default_asset_items()
		if default_items:
			pass

		self._controller.selected_item = item

	def _on_browser_model_double_clicked(self):
		"""
		Internal callback function that is called each time browser model doubleClicked signal is emitted.
		This happens when a browser item is double-clicked by the user and forces the load of the double-clicked item
		scene file. Loads the current selected scene.
		"""

		self._controller.load_scene()

	def _on_thumbs_browser_dots_menu_apply_action_triggered(self):
		"""
		Internal callback function that is called each time Thumbs Browser Dots Menu apply action is triggered by the
		user. Loads the current selected scene.
		"""

		self._controller.load_scene()

	def _on_thumbs_browser_dots_menu_create_action_triggered(self):
		"""
		Internal callback function that is called each time Thumbs Browser Dots Menu create action is triggered by the
		user. Saves current selected scene.
		"""

		directory = self._thumbs_browser.save_directory()
		if not directory:
			return

		self._controller.save_scene(directory=directory, file_type='mayaAscii')
		self.refresh_thumbs()

	def _on_thumbs_browser_dots_menu_refresh_action_triggered(self):
		"""
		Internal callback function that is called each time Thumbs Browser Dots Menu refresh action is triggered by the
		user. Refreshes thumb browser items.
		"""

		self.refresh_thumbs()
