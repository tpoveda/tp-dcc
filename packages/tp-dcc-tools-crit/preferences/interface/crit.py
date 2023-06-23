#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for CRIT library Preference interface.
"""

from __future__ import annotations

import os
from collections import deque

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

		templates_path = self.default_user_templates_path()
		folder.ensure_folder_exists(templates_path)

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

	def user_build_script_paths(self, root: str | None = None) -> list[str]:
		"""
		Returns the user build script folder paths.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of folder paths.
		:rtype: list[str]
		"""

		build_script_paths = self.settings(root=root).get('settings', dict()).get(BUILD_SCRIPT_PATHS_KEY, list())
		default_scripts = [self.default_build_script_path()]
		return list(set(build_script_paths).union(default_scripts))

	def user_build_scripts(self, root: str | None = None) -> list[str]:
		"""
		Returns a list of build script IDs which should by executing during rig building processes.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of build script IDs.
		:rtype: list[str]
		"""

		return self.settings(root=root).get('settings', dict()).get('buildScripts', list())

	def default_naming_config_path(self) -> str:
		"""
		Returns the absolute path where default naming presets are located.

		:return: default naming presets absolute path.
		:rtype: str
		"""

		return path.join_path(self.manager.asset_path(), 'crit', 'namingpresets')

	def naming_preset_paths(self, root: str | None = None) -> list[str]:
		"""
		Returns the paths whether presets are located.

		:return: list of naming preset paths.
		:rtype: list[str]
		"""

		preset_paths = self.settings(root=root).get('settings', dict()).get(NAMING_PRESET_PATHS, list())
		return helpers.remove_dupes([self.default_naming_config_path()] + preset_paths)

	def naming_preset_hierarchy(self, root: str | None = None) -> dict:
		"""
		Returns the naming preset hierarchies from CRIT preference file.

		:return: dictionary with naming presets hierarchy.
		:rtype: dict
		"""

		return self.settings(root=root).get('settings', dict()).get(NAMING_PRESET_HIERARCHY, dict())

	def naming_preset_save_path(self, root: str | None = None) -> str:
		"""
		Returns path where new naming presets will be stored into.

		:return: absolute presets save folder.
		:rtype: str
		"""

		return self.settings(root=root).get('settings', dict()).get(
			NAMING_PRESET_PATHS, list()) or self.default_naming_config_path()

	def set_naming_preset_paths(self, paths: list[str], save: bool = True):
		"""
		Sets the naming preset paths for CRIT preferences file.

		:param list[str] paths: list of naming preset paths.
		:param bool save: whether to save preferences file changes.
		"""

		settings = self.settings(root=None)
		settings['settings'][NAMING_PRESET_PATHS] = paths
		if save:
			settings.save()

	def set_naming_preset_hierarchy(self, hierarchy: dict, save: bool = True):
		"""
		Sets the naming preset hierarchies for CRIT preferences file.

		:param dict hierarchy: preset hierarchy dictionary.
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

	def user_components_paths(self, root: str | None = None) -> list[str]:
		"""
		Returns the user component folder paths.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of folder paths.
		:rtype: list[str]
		"""

		return self.settings(root=root).get('settings', dict()).get(COMPONENTS_PATHS_KEY, list())

	def default_user_templates_path(self) -> str:
		"""
		Returns the default CRIT templates path.

		:return: CRIT assets/crit/templates absolute path.
		:rtype: str
		"""

		return path.join_path(self.manager.asset_path(), 'crit', 'templates')

	def naming_templates(self, root: str | None = None) -> dict:
		"""
		Returns CRIT naming templates.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: crit naming templates.
		:rtype: dict
		"""

		return self.settings(root=root).get('settings', dict()).get('naming', dict()).get('templates', dict())

	def current_naming_template(self, root: str | None = None) -> str:
		"""
		Returns current CRIT naming template.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: current CRIT naming template name.
		:rtype: str
		"""

		return self.settings(root=root).get(
			'settings', dict()).get('naming', dict()).get('profile', dict()).get('template', 'default')

	def name_start_index(self, root: str | None = None) -> int:
		"""
		Returns the CRIT naming start index.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: name start index.
		:rtype: int
		"""

		return self.settings(root=root).get(
			'settings', dict()).get('naming', dict()).get('profile', dict()).get('startIndex', 2)

	def name_index_padding(self, root: str | None = None) -> int:
		"""
		Returns the CRIT naming index padding.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: name index padding.
		:rtype: int
		"""

		return self.settings(root=root).get(
			'settings', dict()).get('naming', dict()).get('profile', dict()).get('indexPadding', 2)

	def empty_scenes_path(self) -> str:
		"""
		Returns the absolute path where empty scene templates are located.

		:return: CRIT assets/crit/templates/emptyScenes absolute path.
		:rtype: str
		"""

		return path.join_path(self.default_user_templates_path(), 'emptyScenes')

	def recent_max(self):
		"""
		Returns the maximum number of recent projects to retrieve.

		:return: maximum number of recent projects.
		:rtype: int
		"""

		return self.manager.find_setting(self._RELATIVE_PATH, root=None, name='maxRecent', default=3)

	def recent_projects_queue(self):
		"""
		Returns a queue of recent projects.

		:return: recent projects.
		:rtype: deque
		"""

		max_length = self.recent_max()
		projects = self.manager.find_setting(self._RELATIVE_PATH, root=None, name='recentProjects', default=[])
		if not projects:
			return deque(maxlen=max_length)

		return deque(projects, maxlen=max_length)

	def add_recent_project(self, name: str, path: str):
		"""
		Adds given project name and path entry as a recent project.

		:param str name: name of the project to add as recent one.
		:param str path: path of the project to add as a recent one.
		:return: True if project was added into the list of recent projects; False otherwise.
		:rtype: bool
		"""

		recent_projects = self.recent_projects_queue()
		entry = [name, path]
		if entry in recent_projects:
			return False
		recent_projects.appendleft(entry)
		self.settings().setdefault(
			'settings', dict()).setdefault('project', dict())['recentProjects'] = list(recent_projects)
		self.save_settings()
