from __future__ import annotations

import typing
from typing import List

from tp.common.python import decorators

if typing.TYPE_CHECKING:
	from tp.common.python.path import DirectoryPath
	from tp.preferences.assets import BrowserPreference
	from tp.preferences.preference import PreferenceInterface
	from tp.tools.toolbox.widgets.toolui import ToolUiWidget
	from tp.tools.scenesbrowser.widgets.thumbsbrowser import ThumbsBrowser, SuffixFilterModel


class ScenesBrowserController:
	def __init__(self, tool_ui_widget: ToolUiWidget):
		super().__init__()

		self._tool_ui_widget = tool_ui_widget
		self._scene_prefs = None

	@decorators.abstractmethod
	def scene_prefs(self) -> PreferenceInterface | None:
		return None

	def browser_model(
			self, view: ThumbsBrowser, directories: List[DirectoryPath] | None = None,
			uniform_icons: bool = False, browser_preferences: BrowserPreference | None = None) -> SuffixFilterModel:
		return SuffixFilterModel(
			view, extensions=[], directories=directories, uniform_icons=uniform_icons,
			browser_preferences=browser_preferences)
