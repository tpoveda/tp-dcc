#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Noddle library Preference interface.
"""

from __future__ import annotations

from collections import deque

from tp.preferences import preference
from tp.common.python import path, folder


class NoddleInterface(preference.PreferenceInterface):

	ID = 'noddle'
	_RELATIVE_PATH = 'prefs/maya/noddle.pref'

	def upgrade_assets(self):
		"""
		Upgrades the local assets.
		"""

		templates_path = self.default_user_templates_path()
		folder.ensure_folder_exists(templates_path)

	def default_user_templates_path(self) -> str:
		"""
		Returns the default CRIT templates path.

		:return: CRIT assets/crit/templates absolute path.
		:rtype: str
		"""

		return path.join_path(self.manager.asset_path(), 'crit', 'templates')

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

	def previous_project(self) -> str:
		"""
		Returns previous project path.

		:return: previous project path.
		:rtype: str
		"""

		return self.settings().get('settings', {}).get('project', {}).get('previousProject', '')

	def set_previous_project(self, project_path: str):
		"""
		Sets given path as the previous project path.

		:param str project_path: project path.
		"""

		self.settings().setdefault('settings', {}).setdefault('project', {})['previousProject'] = str(project_path)

	def add_recent_project(self, name: str, project_path: str):
		"""
		Adds given project name and path entry as a recent project.

		:param str name: name of the project to add as recent one.
		:param str project_path: path of the project to add as a recent one.
		:return: True if project was added into the list of recent projects; False otherwise.
		:rtype: bool
		"""

		recent_projects = self.recent_projects_queue()
		entry = [name, project_path]
		if entry in recent_projects:
			return False
		recent_projects.appendleft(entry)
		self.settings().setdefault('settings', {}).setdefault('project', {})['recentProjects'] = list(recent_projects)
		self.save_settings()

	def refresh_recent_projects(self):
		"""
		Refreshes recent projects by removing recent project folders that do not exist.
		"""

		recent_projects = self.recent_projects_queue()
		existing_projects = []
		for recent_project in recent_projects:
			if not path.is_dir(recent_project):
				continue
			existing_projects.append(recent_project)
		self.settings().setdefault('settings', {}).setdefault('project', {})['recentProjects'] = existing_projects
		self.save_settings()

	def asset_types(self, root: str | None = None) -> list[str]:
		"""
		Returns list of asset types.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: list of asset type names.
		:rtype: list[str]
		"""

		return self.settings(root=root).get('settings', {}).get('assets', {}).get('types', [])

	def builder_history_enabled(self, root: str | None = None) -> bool:
		"""
		Returns whether builder history is enabled.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: True if builder history is enabled; False otherwise.
		:rtype: bool
		"""

		return self.settings(root=root).get('settings', {}).get('builder', {}).get('history', {}).get('enabled', True)

	def builder_history_size(self, root: str | None = None) -> int:
		"""
		Returns builder history size.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: builder history size.
		:rtype: bool
		"""

		return self.settings(root=root).get('settings', {}).get('builder', {}).get('history', {}).get('size', 32)

	def builder_node_title_font(self, root: str | None = None) -> tuple[str, int]:
		"""
		Returns default node title font.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: tuple with the name of the default font and its size.
		:rtype: tuple[str, int]
		"""

		return self.settings(root=root).get('settings', {}).get('builder', {}).get('titleFont', ['Roboto', 10])

	def naming_templates(self, root: str | None = None) -> dict:
		"""
		Returns CRIT naming templates.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: crit naming templates.
		:rtype: Dict
		"""

		return self.settings(root=root).get('settings', {}).get('naming', {}).get('templates', {})

	def current_naming_template(self, root: str | None = None) -> str:
		"""
		Returns current CRIT naming template.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: current CRIT naming template name.
		:rtype: str
		"""

		return self.settings(root=root).get(
			'settings', {}).get('naming', {}).get('profile', {}).get('template', 'default')

	def name_start_index(self, root: str | None = None) -> int:
		"""
		Returns the CRIT naming start index.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: name start index.
		:rtype: int
		"""

		return self.settings(root=root).get('settings', {}).get('naming', {}).get('profile', {}).get('startIndex', 2)

	def name_index_padding(self, root: str | None = None) -> int:
		"""
		Returns the CRIT naming index padding.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: name index padding.
		:rtype: int
		"""

		return self.settings(root=root).get('settings', {}).get('naming', {}).get('profile', {}).get('indexPadding', 2)

	def rig_display_line_width(self, root: str | None = None) -> float:
		"""
		Returns the default display line width for newly created rig controls.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: display line width.
		:rtype: float
		"""

		return self.settings(root=root).get('settings', {}).get('rig', {}).get('display', {}).get('lineWidth', 2.0)

	def skin_file_format(self, root: str | None = None) -> str:
		"""
		Returns the format to use when saving skin weights.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: skin file format.
		:rtype: str
		"""

		return self.settings(root=root).get(
			'settings', {}).get('rig', {}).get('io', {}).get('skin', {}).get('fileFormat', 'pickle')
