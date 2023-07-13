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

