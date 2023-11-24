from __future__ import annotations

import os
from typing import List

from tp.common.python import path, folder, fileio


def templates_folders() -> List[str]:
	"""
	Return paths where templates are located.

	:return: list of paths where component editor templates are located.
	:rtype: List[str]
	"""

	return os.environ.get('CRIT_COMPONENTS_EDITOR_TEMPLATE_PATHS', '').split(os.pathsep)


def descriptor_templates_folders() -> List[str]:
	"""
	Returns paths were template descriptors are located.

	:return: list of paths where component editor templates descriptors are located.
	:rtype: List[str]
	"""

	return [path.join_path(template_path, 'descriptors') for template_path in templates_folders()]


def descriptor_template_file_paths() -> List[str]:
	"""
	Returns all available descriptor template file paths ordered by its version.

	:return: list of absolute template file paths.
	:rtype: List[str]
	"""

	found_template_files = []
	for descriptor_templates_folder in descriptor_templates_folders():
		template_files = folder.get_files(
			descriptor_templates_folder, full_path=True, recursive=True, pattern='*.descriptor')
		found_template_files.extend(template_files)
	if not found_template_files:
		return found_template_files

	found_template_files = sorted(found_template_files, key=lambda x: path.basename(x).split('.')[1])

	return found_template_files


def latest_descriptor_template() -> str | None:
	"""
	Returns the latest available descriptor template data.

	:return: latest descriptor template data.
	:rtype: str or None
	"""

	available_template_files = descriptor_template_file_paths()
	template_file_path = available_template_files[0] if available_template_files else None
	if not path.is_file(template_file_path):
		return None

	template_data = fileio.get_file_text(template_file_path)

	return template_data


def component_templates_folders():
	"""
	Return paths where descriptor templates are located.

	:return: list of paths where component editor templates are located.
	:rtype: List[str]
	"""

	return [path.join_path(template_path, 'components') for template_path in templates_folders()]


def component_template_file_paths() -> List[str]:
	"""
	Returns all available component template file paths ordered by its version.

	:return: list of absolute template file paths.
	:rtype: List[str]
	"""

	found_template_files = []
	for descriptor_templates_folder in component_templates_folders():
		template_files = folder.get_files(
			descriptor_templates_folder, full_path=True, recursive=True, pattern='*.py')
		found_template_files.extend(template_files)
	if not found_template_files:
		return found_template_files

	found_template_files = sorted(found_template_files, key=lambda x: path.basename(x).split('.')[1])

	return found_template_files


def latest_component_template() -> str | None:
	"""
	Returns the latest available component template data.

	:return: latest component template data.
	:rtype: str or None
	"""

	available_template_files = component_template_file_paths()
	template_file_path = available_template_files[0] if available_template_files else None
	if not path.is_file(template_file_path):
		return None

	template_data = fileio.get_file_text(template_file_path)

	return template_data
