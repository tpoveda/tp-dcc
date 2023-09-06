#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains implementation for Freeform library Preference interface.
"""

from __future__ import annotations

import os

from tp.preferences import preference
from tp.common.python import path


class FreeformInterface(preference.PreferenceInterface):

	ID = 'freeform'
	_RELATIVE_PATH = 'prefs/maya/freeform.pref'

	def content_path(self, root: str | None = None) -> str:
		"""
		Returns project content path.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: absolute path to where content project data is located.
		:rtype: str
		"""

		project_settings = self.settings(root=root).get('settings', {}).get('project', {})
		project_drive = path.clean_path(project_settings.get('drive', ''))
		project_root = path.clean_path(project_settings.get('rootPath', ''))
		engine_content_root = path.clean_path(project_settings.get('engineContentPath', ''))

		return path.join_path(project_drive, os.sep, project_root, engine_content_root)

	def check_project(self, root: str | None = None) -> bool:
		"""
		Returns whether project should be checked.

		:param str root: root name to search. If None, then all roots will be searched until relativePath is found.
		:return: True if project should be checked; False otherwise.
		:rtype: bool
		"""

		use_project = self.settings(root=root).get('settings', {}).get('project', {}).get('useProject', False)
		content_path = self.content_path()
		if use_project and path.is_dir(content_path):
			return True

		return False

	def auto_freeze_skeleton(self, root: str | None = None) -> bool:
		"""
		Returns whether auto freeze skeleton rigging feature is enabled.

		:return: True if auto freeze skeleton feature is enabled; False otherwise.
		:rtype: bool
		"""

		return self.settings(root=root).get('settings', {}).get('rigging', {}).get('autoFreezeSkeleton', True)
