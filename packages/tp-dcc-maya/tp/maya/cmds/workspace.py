from __future__ import annotations

import os

import maya.mel as mel
import maya.cmds as cmds

from tp.core import log
from tp.common.python import path

logger = log.tpLogger


def current_workspace() -> str:
	"""
	Returns path to current Maya project directory.

	:return:  absolute path to current project directory.
	:rtype: str
	"""

	return cmds.workspace(query=True, rootDirectory=True)


def project_sub_directory(sub_directory: str = 'scenes') -> str:
	"""
	Returns the path of the current Maya project subdirectory.

	:param str sub_directory: subdirectory name to get path of.
	:return: path pointing to Maya project subdirectory.
	:rtype: str
	"""

	project_directory = current_workspace()
	directory = path.join_path(project_directory, sub_directory)
	if not path.is_dir(directory):
		home_directory = os.path.expanduser('~')
		logger.warning(f'Directory "{directory}" does not exist, returning home directory: "{home_directory}" instead!')
		directory = home_directory

	return directory


def find_workspace_from_scene(file_path: str, max_depth: int = 999) -> str | None:
	"""
	Function that recursively tries to find workspace from given file path.

	:param str file_path: path pointing to a Maya file.
	:param int max_depth: maximum number of recursion level.
	:return: found workspace directory.
	:rtype: str or None
	"""

	file_dir = path.dirname(file_path)
	dir_pos = file_dir
	for _ in range(max_depth):
		parent_dir = os.path.dirname(dir_pos)
		if file_dir == parent_dir:
			return None
		workspace = path.normalize_path(path.join_path(parent_dir, 'workspace.mel'))
		_current_workspace = path.normalize_path(current_workspace())
		if path.exists(workspace) and path.normalize_path(parent_dir) != _current_workspace:
			return path.normalize_path(parent_dir)
		dir_pos = parent_dir

	return None


def set_project(workspace_path: str):
	"""
	Sets given path as the active Maya workspace.

	:param str workspace_path: workspace path to set as the active Maya workspace.
	"""

	mel.eval('setProject \"' + workspace_path.replace('\\', '\\\\') + '\"')


def switch_workspace(workspace_path: str) -> str | None:
	"""
	Tries to switch to given workspace path.

	:param str workspace_path: path pointing to a Maya workspace.
	:return: 'changed' if workspace was changed successfully, 'no' if workspace was not set or 'cancel' if switch
		operation was cancelled by the user. None if no workspace was found.
	:rtype: str or None
	"""

	# import here to avoid cyclic imports
	from tp.common.qt.widgets import popups

	found_workspace = find_workspace_from_scene(workspace_path)
	if not found_workspace:
		return None

	short_path = path.shorten_path(workspace_path)
	result = popups.show_question(
		title='Set Maya Project?',
		message=f'Project detected. Would you like to switch the projec to:\n\n {short_path}?',
		button_a='Yes', button_b='No', button_c='Cancel')
	if result == 'A':
		set_project(workspace_path)
		return 'changed'
	elif result == 'B':
		return 'no'

	return 'cancel'
