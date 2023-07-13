from __future__ import annotations

import typing
from typing import List

from overrides import override

from tp.preferences.interfaces import assets
from tp.tools.scenesbrowser import controller
from tp.tools.scenesbrowser.widgets import thumbsbrowser

if typing.TYPE_CHECKING:
	from tp.common.python.path import DirectoryPath
	from tp.preferences.assets import BrowserPreference
	from tp.preferences.preference import PreferenceInterface


class MayaScenesBrowserController(controller.ScenesBrowserController):

	@override
	def scene_prefs(self) -> PreferenceInterface | None:
		if not self._scene_prefs:
			self._scene_prefs = assets.maya_scenes_interface()

		return self._scene_prefs

	@override(check_signature=False)
	def browser_model(
			self, view: thumbsbrowser.ThumbsBrowser, directories: List[DirectoryPath] | None = None,
			uniform_icons: bool = False, browser_preferences: BrowserPreference | None = None) -> thumbsbrowser.MayaFileModel:
		return thumbsbrowser.MayaFileModel(
			view=view, directories=directories, uniform_icons=uniform_icons, browser_preferences=browser_preferences)
