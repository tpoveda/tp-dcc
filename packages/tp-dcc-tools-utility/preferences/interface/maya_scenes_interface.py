#! /usr/bin/env python
# -*- coding: utf-8 -*-

from tp.preferences import preference, assets


class MayaScenesInterface(preference.PreferenceInterface):

	ID = 'maya_scenes_interface'
	_RELATIVE_PATH = 'prefs/maya/maya_scenes.pref'

	def __init__(self, preferences_manager):
		super().__init__(preferences_manager)

		self.scene_assets = assets.BrowserPreference('maya_scenes', preference_interface=self)
