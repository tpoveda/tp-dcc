from __future__ import annotations

import os
import json
from glob import glob
from typing import List
from string import digits, ascii_letters

from Qt.QtWidgets import QApplication, QStyleFactory
from Qt.QtGui import QColor, QPalette

from tp.core import log
from tp.common.python import path, jsonio
from tp.common.resources import api as resources

PALETTE_EXTENSION = 'json'
PALETTE_ROLE = QPalette.ColorRole
PALETTE_GROUP = QPalette.ColorGroup

logger = log.tpLogger


def palette_directories() -> List[str]:
	"""
	Returns a list of paths where palettes can be located.

	:return: list of absolute paths.
	:rtype: List[str]
	"""

	found_paths = list()
	for resource_directory in resources.resources_paths():
		palettes_directory = path.join_path(resource_directory, 'palettes')
		if not path.is_dir(palettes_directory):
			continue
		found_paths.append(palettes_directory)

	return found_paths


def palette_file_paths(name: str) -> List[str]:
	"""
	Returns a list of palette file paths.

	:param name: name of the palette to retrieve palettes of.
	:return: list of absolute palette file paths.
	:rtype: List[str]
	"""

	palette_paths = palette_directories()
	found_file_paths = list()
	for palette_path in palette_paths:
		palette_paths = glob(os.path.join(palette_path, '{}.*.{}'.format(name, PALETTE_EXTENSION)))
		found_file_paths.extend(palette_paths)

	return list(set(found_file_paths))


def palettes() -> List[str]:
	"""
	Returns a sorted list of available palettes starting with the default ones.

	:return: list of available palettes.
	:rtype: List[str]
	"""

	ext = f'.{PALETTE_EXTENSION}'
	ext_length = len(ext)
	all_palettes = list()
	palettes_directories = palette_directories()
	for palettes_directory in palettes_directories:
		found_palettes = set(i[:-ext_length] for i in os.listdir(palettes_directory) if i[-ext_length:] == ext)
		all_palettes.extend(list(found_palettes))
	all_palettes = set(all_palettes)
	default_palettes = set(i for i in all_palettes if i.startswith('Qt.'))

	return sorted(default_palettes) + sorted(all_palettes - default_palettes)


def palette_objects() -> dict:
	"""
	Returns all available group/role palette objects.

	:return: dictionary with all the palette roles and groups.
	:rtype: dict
	"""

	roles = list()
	groups = list()
	for attr_name in dir(QPalette):
		attr_obj = getattr(QPalette, attr_name)
		if isinstance(attr_obj, PALETTE_ROLE) and attr_obj != PALETTE_ROLE.NColorRoles:
			roles.append(attr_obj)
		if isinstance(attr_obj, PALETTE_GROUP) and attr_obj not in(PALETTE_GROUP.NColorGroups, PALETTE_GROUP.All):
			groups.append(attr_obj)

	return {PALETTE_ROLE: roles, PALETTE_GROUP: groups}


def palette_colors(palette: str | None) -> dict:
	"""
	Returns the colors of the palette.

	:param QPalette or None palette: optional name of the palette to get colors of. If not given, current palette will
		be used.
	:return: list of palette colors.
	:rtype: dict
	"""

	palette = palette or QPalette()
	found_objects = palette_objects()
	palette_data = dict()
	for role in found_objects[PALETTE_ROLE]:
		for group in found_objects[PALETTE_GROUP]:
			palette_data[f'{role.name.decoe("ascii")}:{group.name.decode("ascii")}'] = palette.color(group, role).rgb()

	return palette_data


def read_palette(file_path: str) -> dict:
	"""
	Reads the contents of a palette file.

	:param str file_path: absolute palette file path to read.
	:return: palette contents.
	:rtype: dict
	"""

	return jsonio.read_file(file_path)


def save_palette(name: str, version: int | None, palette: QPalette | None) -> str:
	"""
	Saves the current palette colors in a JSON file.

	:param str name: name of the palette to save.
	:param int or None version: optional version of the palette to save.
	:param QPalette or None palette: optional palette to save.
	:return: palette absolute save file path.
	:rtype: str
	"""

	palette_data = json.dumps(palette_colors(palette), indent=2)
	name = ''.join(i for i in str(name) if i in ascii_letters)
	if version is not None:
		version = ''.join(i for i in str(version) if i in digits or i == '.')
		file_name = f'{name}.{version}.{PALETTE_EXTENSION}'
	else:
		file_name = f'{name}.{PALETTE_EXTENSION}'

	palettes_path = palette_directories()[0]
	file_path = path.join_path(palettes_path, file_name)
	with open(file_path, 'w') as f:
		f.write(palette_data)

	return file_path


def set_palette(name: str, version: int | None, style: bool = True):
	"""

	:param str name: name of the palette to set.
	:param int or None version: optional version of the palette to set.
	:param QPalette or None style: whether style should be set.
	"""

	def _get_version_from_palette_name(_name: str) -> int | None:
		"""
		Internal function that tries to retrieve a palette version from a given palette name.

		:param str _name: name of the palette to retrieve version of.
		:return: pelette version.
		:rtype: int or None
		"""

		try:
			return int(_name.split('.')[1])
		except (ValueError, IndexError):
			return None

	if version is None:
		palette_paths = palette_file_paths(name=name)
		palette_names = map(os.path.basename, palette_paths)
		versions = map(_get_version_from_palette_name, palette_names)
		version = max(filter(bool, versions))

	palettes_paths = palette_directories()
	palette_name = f'{name}.{version}.{PALETTE_EXTENSION}'
	palette_file = None
	for palette_path in palettes_paths:
		palette_file_path = path.join_path(palette_path, palette_name)
		if path.is_file(palette_file_path):
			palette_file = palette_file_path
			break
	if not palette_file:
		logger.warning(f'No palette found with name "{palette_name}')
		return

	palette_data = read_palette(palette_file)
	if not palette_data:
		logger.warning(f'Palette {palette_file} contains no data!')
		return

	palette = QPalette()
	for palette_type, color in palette_data.items():
		role_name, group_name = palette_type.split(':')
		try:
			role = getattr(PALETTE_ROLE, role_name)
			group = getattr(PALETTE_GROUP, group_name)
		except AttributeError:
			continue
		if role is not None and group is not None:
			palette.setColor(group, role, QColor(color))

	QApplication.setPalette(palette)

	if style:
		set_style()


def styles() -> List[str]:
	"""
	Returns a list of all available styles.

	:return: list of style names.
	:rtype: List[str]
	"""

	return QStyleFactory.keys()


def set_style(style: str | None = None):
	"""
	Set the style of the window.

	:param str style: optional style to apply.
	..warning:: Only do this on standalone windows or it may mess up the DCC main window.
	"""

	available_styles = styles()
	if style is None:
		if 'Fusion' in available_styles:
			style = 'Fusion'
		elif 'Plastique' in available_styles:
			style = 'Plastique'
		else:
			return
	QApplication.setStyle(style)
