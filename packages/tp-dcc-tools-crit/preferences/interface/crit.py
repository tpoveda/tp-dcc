#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for CRIT library Preference interface.
"""

from __future__ import annotations

import os
from typing import List, Dict

from tp.preferences import preference
from tp.common.python import helpers, path, folder


BUILD_SCRIPT_PATHS_KEY = 'buildScriptPaths'
NAMING_PRESET_HIERARCHY = 'namingPresetHierarchy'
NAMING_PRESET_SAVE_PATH = 'namingPresetSavePath'
NAMING_PRESET_PATHS = 'namingPresetPaths'
COMPONENTS_PATHS_KEY = 'componentsPaths'


class CritInterface(preference.PreferenceInterface):

	ID = 'crit'
	_RELATIVE_PATH = 'prefs/maya/crit.pref'

	def upgrade_preferences(self):
		"""
		Upgrades the local preferences from the default preferences.
		"""

		pass

	def upgrade_assets(self):
		"""
		Upgrades the local assets.
		"""

		asset_pkg = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
		local_folder = path.join_path(self.manager.asset_path(), 'crit')

		folder.copy_directory_contents_safe(asset_pkg, local_folder, skip_exists=True, overwrite_modified=True)

	def default_build_script_path(self) -> str:
		"""
		Returns the absolute path where default build scripts are located.

		:return: default build script absolute path.
		:rtype: str
		"""

		return path.join_path(self.manager.asset_path(), 'crit', 'buildscripts')

	def user_build_script_paths(self, root: str | None = None) -> List[str]:
		"""
		Returns the user build script folder paths.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of folder paths.
		:rtype: List[str]
		"""

		build_script_paths = self.settings(root=root).get('settings', {}).get(BUILD_SCRIPT_PATHS_KEY, [])
		default_scripts = [self.default_build_script_path()]
		return list(set(build_script_paths).union(default_scripts))

	def user_build_scripts(self, root: str | None = None) -> List[str]:
		"""
		Returns a list of build script IDs which should by executing during rig building processes.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of build script IDs.
		:rtype: List[str]
		"""

		return self.settings(root=root).get('settings', {}).get('buildScripts', [])

	def default_naming_config_path(self) -> str:
		"""
		Returns the absolute path where default naming presets are located.

		:return: default naming presets absolute path.
		:rtype: str
		"""

		return path.join_path(self.manager.asset_path(), 'crit', 'namingpresets')

	def naming_preset_paths(self, root: str | None = None) -> List[str]:
		"""
		Returns the paths whether presets are located.

		:return: list of naming preset paths.
		:rtype: List[str]
		"""

		preset_paths = self.settings(root=root).get('settings', {}).get(NAMING_PRESET_PATHS, [])
		return helpers.remove_dupes([self.default_naming_config_path()] + preset_paths)

	def naming_preset_hierarchy(self, root: str | None = None) -> Dict:
		"""
		Returns the naming preset hierarchies from CRIT preference file.

		:return: dictionary with naming presets hierarchy.
		:rtype: Dict
		"""

		return self.settings(root=root).get('settings', {}).get(NAMING_PRESET_HIERARCHY, {})

	def naming_preset_save_path(self, root: str | None = None) -> str:
		"""
		Returns path where new naming presets will be stored into.

		:return: absolute presets save folder.
		:rtype: str
		"""

		return self.settings(root=root).get('settings', {}).get(
			NAMING_PRESET_PATHS, list()) or self.default_naming_config_path()

	def set_naming_preset_paths(self, paths: List[str], save: bool = True):
		"""
		Sets the naming preset paths for CRIT preferences file.

		:param List[str] paths: list of naming preset paths.
		:param bool save: whether to save preferences file changes.
		"""

		settings = self.settings(root=None)
		settings['settings'][NAMING_PRESET_PATHS] = paths
		if save:
			settings.save()

	def set_naming_preset_hierarchy(self, hierarchy: Dict, save: bool = True):
		"""
		Sets the naming preset hierarchies for CRIT preferences file.

		:param Dict hierarchy: preset hierarchy dictionary.
		:param bool save: whether to save preferences file changes.
		"""

		settings = self.settings(root=None)
		settings['settings'][NAMING_PRESET_HIERARCHY] = hierarchy
		if save:
			settings.save()

	def set_naming_preset_save_path(self, save_path: str, save: bool = True):
		"""
		Sets the naming preset save path for CRIT preferences file.

		:param str save_path: preset save path to set.
		:param bool save: whether to save preferences file changes.
		"""

		default_naming_path = self.default_naming_config_path()
		if path.clean_path(save_path) == default_naming_path:
			return
		settings = self.settings(root=None)
		settings['settings'][NAMING_PRESET_SAVE_PATH] = save_path
		if save:
			settings.save()

	def user_components_paths(self, root: str | None = None) -> List[str]:
		"""
		Returns the user component folder paths.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of folder paths.
		:rtype: List[str]
		"""

		return self.settings(root=root).get('settings', {}).get(COMPONENTS_PATHS_KEY, [])
