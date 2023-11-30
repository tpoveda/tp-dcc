#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for CRIT library Preference interface.
"""

from __future__ import annotations

import os

from tp.preferences import preference
from tp.common.python import helpers, path, folder


BUILD_SCRIPT_PATHS_KEY = 'buildScriptPaths'
NAMING_PRESET_HIERARCHY = 'namingPresetHierarchy'
NAMING_PRESET_SAVE_PATH = 'namingPresetSavePath'
NAMING_PRESET_PATHS = 'namingPresetPaths'
COMPONENTS_PATHS_KEY = 'componentsPaths'
TEMPLATE_PATHS_KEY = 'templatePaths'
TEMPLATE_SAVE_PATH_KEY = 'templateSavePath'
EXPORT_PLUGINS_KEY = 'exporterPluginPaths'
EXPORT_PLUGIN_OVERRIDES_KEY = 'exporterPluginOverrides'


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

		should_include_defaults = self.settings(name='includeDefaultAssets')

		templates_path = self.default_user_template_path()
		build_script_path = self.default_build_script_path()
		exporter_path = self.default_export_plugin_path()
		folder.ensure_folder_exists(templates_path)
		folder.ensure_folder_exists(build_script_path)
		folder.ensure_folder_exists(exporter_path)

		build_script_init_path = os.path.join(build_script_path, '__init__.py')
		exporter_init_path = os.path.join(exporter_path, '__init__.py')
		if not os.path.exists(build_script_init_path):
			with open(build_script_init_path, 'w') as f:
				pass
		if not os.path.exists(exporter_init_path):
			with open(exporter_init_path, 'w') as f:
				pass
		if not should_include_defaults:
			return

		asset_pkg = self.repository_asset_path()
		template_custom_path = os.path.join(templates_path, 'custom')
		folder.ensure_folder_exists(template_custom_path)

		local_folder = path.join_path(self.manager.asset_path(), 'crit')
		folder.copy_directory_contents_safe(asset_pkg, local_folder, skip_exists=True, overwrite_modified=True)

	def repository_asset_path(self) -> str:
		"""
		Returns the absolute path containing all CRIT related assets (templates, build scripts, etc).

		:return: default assets absolute path.
		:rtype: str
		"""

		return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'assets'))

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

		build_script_paths = self.settings(root=root).get('settings', {}).get(BUILD_SCRIPT_PATHS_KEY, [])
		default_scripts = [self.default_build_script_path()]
		return list(set(build_script_paths).union(default_scripts))

	def user_build_scripts(self, root: str | None = None) -> list[str]:
		"""
		Returns a list of build script IDs which should by executing during rig building processes.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of build script IDs.
		:rtype: list[str]
		"""

		return self.settings(root=root).get('settings', {}).get('buildScripts', [])

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

		preset_paths = self.settings(root=root).get('settings', {}).get(NAMING_PRESET_PATHS, [])
		return helpers.remove_dupes([self.default_naming_config_path()] + preset_paths)

	def naming_preset_hierarchy(self, root: str | None = None) -> dict:
		"""
		Returns the naming preset hierarchies from CRIT preference file.

		:return: dictionary with naming presets hierarchy.
		:rtype: dict
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

		return self.settings(root=root).get('settings', {}).get(COMPONENTS_PATHS_KEY, [])

	def default_user_template_path(self) -> str:
		"""
		Returns the absolute path where default templates are located.

		:return: default templates absolute path.
		:rtype: str
		"""

		return path.join_path(self.manager.asset_path(), 'crit', 'templates')

	def user_template_paths(self, root: str | None = None) -> list[str]:
		"""
		Returns the user template folders paths for the user.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of user template folder paths.
		:rtype: list[str]
		"""

		settings = self.settings(root=root).get('settings', {}).get(TEMPLATE_PATHS_KEY, [])
		return settings or [self.default_user_template_path()]

	def user_template_save_path(self, root: str | None = None) -> str:
		"""
		Returns the path where user templates should be stored.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: root folder path for saving templates.
		:rtype: str
		"""

		user_spec = self.settings(root=root).get('settings', {}).get(TEMPLATE_SAVE_PATH_KEY, '')
		resolved = os.path.expandvars(os.path.expanduser(user_spec))
		if not os.path.exists(resolved):
			user_spec = os.getenv('CRIT_TEMPLATE_SAVE_PATH', '')
			resolved = os.path.expandvars(os.path.expanduser(user_spec))
			if not os.path.exists(resolved):
				user_spec = self.default_user_template_path()

		return user_spec

	def exporter_plugin_overrides(self, root: str | None = None) -> dict[str, str]:
		"""
		Returns the exporter plugin ID overrides done by the user.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: mapping key is the exporter plugin ID and the value is the remapped plugin ID to use.
		:rtype: dict[str, str]
		"""

		return self.settings(root=root).get('settings', {}).get(EXPORT_PLUGIN_OVERRIDES_KEY, {})

	def default_export_plugin_path(self) -> str:
		"""
		Returns the absolute path for CRIT export plugin.

		:return: default exporters absolute path.
		:rtype: str
		"""

		return path.join_path(self.manager.asset_path(), 'crit', 'exporters')

	def exporter_plugin_paths(self, root: str | None = None) -> list[str]:
		"""
		Returns the list of exporter plugin paths.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of exporter plugin paths.
		:rtype: list[str]
		"""

		settings = self.settings(root=root).get('settings', {}).get(TEMPLATE_PATHS_KEY)
		return settings or [self.default_export_plugin_path()]
