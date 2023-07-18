from __future__ import annotations

import glob
from typing import Tuple, List, Dict

from tp.core import log
from tp.common.python import path, jsonio, yamlio

logger = log.tpLogger

TP_SCENE_EXTENSION = 'tpScene'					# file extension for tpScene files.
META_INFO_EXTENSION = 'meta'					# file extension for meta file with tag and description data.
TP_INFO_VERSION = '0.0.1'						# current version for meta file format.
DEPENDENCY_FOLDER = 'fileDependencies'			# prefix of the dependency folder for file dependencies.
THUMBNAIL_FILE_NAME = 'thumbnail'				# name for thumbnail files.
INFO_ASSET = 'assetType'						# asset type key for the .meta dictionary and file.
INFO_CREATORS = 'creators'						# creators key for the .meta dictionary and file.
INFO_WEBSITES = 'websites'						# websites key for the .meta dictionary and file.
INFO_TAGS = 'tags'								# tags key for the .meta dictionary and file.
INFO_DESCRIPTION = 'description'				# description key for the .meta dictionary and file.
INFO_SAVE = 'saved'								# saved key for the .meta dictionary and file.
INFO_ANIM = 'animation'							# animation key for the .meta dictionary and file.
VERSION_KEY = 'version'							# version key for the .meta dictionary and file.
ASSET_TYPES = [
	'Not Specified', 'Hero Model', 'Prop Model', 'Background', 'Scene',
	'Background Lights', 'IBL', 'Lights',
	'Image', 'Texture', 'Shaders',
	'Animation', 'Camera', 'Control Curves'
]


def file_dependencies_list(scene_full_path: str, ignore_thumbnail: bool = False) -> Tuple[List[str], str]:
	"""
	Returns a list of all files in the dependency directory.

	:param str scene_full_path: full path to the .tpScene file.
	:param bool ignore_thumbnail: whether to ignore thumbnail files.
	:return: tuple with a list of short name files in the dependency subdirectory and the full directory path.
	:rtype: Tuple[List[str], str]
	"""

	found_dependency_names = []
	directory_path, file_name_no_ext, extension = path.split_path(scene_full_path, remove_extension_dot=True)

	new_directory = '_'.join([file_name_no_ext, extension, DEPENDENCY_FOLDER])
	full_dir_path = path.join_path(directory_path, new_directory)
	if not path.exists(full_dir_path):
		return found_dependency_names, ''

	glob_pattern = path.join_path(full_dir_path, file_name_no_ext)
	for file_name in glob.glob(f'{glob_pattern}.*'):
		found_dependency_names.append(path.basename(file_name))

	if not ignore_thumbnail:
		for file_name in glob.glob(path.join_path(full_dir_path, f'{THUMBNAIL_FILE_NAME}.*')):
			found_dependency_names.append(path.basename(file_name))

	return found_dependency_names, full_dir_path


def single_file_from_scene(scene_full_path: str, file_extension: str):
	"""
	Checks whether file exist in scene dependencies.

	Returns the name of the file if it exists with given extension from the given scene path. Also returns all the
	files in the subdirectory associated with the .tpScene file and filters for the file type.

	:param str scene_full_path: full path of the .tpScene file.
	:param str file_extension: file extension to find with no full stop (such as "fbx", "abc", ...).
	:return: file name with the given extension.
	:rtype: str
	"""

	ext_file_name = ''
	file_names_list, directory = file_dependencies_list(scene_full_path)
	if not directory:
		return ext_file_name

	for file_name in file_names_list:
		if file_name.lower().endswith(file_extension.lower()):
			return path.join_path(directory, file_name)

	return ext_file_name


def create_tag_info_dict(
		asset_type: str = '', creator: str = '', website: str = '', tags: str = '', description: str = '',
		save_info: List[str] | None = None, anim_info: str | None = None) -> Dict:
	"""
	Creates a dictionary ready to be stored within a meta file.

	:param str asset_type: information about asset type ('model', 'scene, 'lights', ...).
	:param str creator: optional information about creator/s.
	:param str website: optional information about creators website links.
	:param str tags: optional tags information.
	:param str description: optional description information.
	:param List[str] or None save_info: optional saved information ('alembic', 'animation', ...).
	:param str or None anim_info: animation information of the file.
	:return: dictionary with info data.
	:rtype: Dict
	"""

	return {
		INFO_ASSET: asset_type, INFO_CREATORS: creator, INFO_WEBSITES: website, INFO_TAGS: tags,
		INFO_DESCRIPTION: description, INFO_SAVE: save_info or [], INFO_ANIM: anim_info, VERSION_KEY: TP_INFO_VERSION
	}


def scene_info_from_file(scene_full_path: str, message: bool = True) -> Tuple[Dict, bool]:
	"""
	Returns other files from the .tpScene in disk.

	:param str scene_full_path: full path of the .tpScene file.
	:param bool message: whether to emit log messagse.
	:return: tuple containing with the dictionary with all the scene information and whether the info file was found.
	:rtype: Tuple[Dict, bool]
	"""

	info_path = single_file_from_scene(scene_full_path, META_INFO_EXTENSION)
	if not path.exists(info_path):
		if message:
			logger.warning('No meta file found!')
		return create_tag_info_dict(ASSET_TYPES[0]), False

	read_data = yamlio.read_file(info_path)
	read_data = read_data if read_data is not None else jsonio.read_file(info_path)

	return read_data, True


def info_dictionary(scene_file: str, directory: str) -> Dict:
	"""
	Generates a tp-dcc info dictionary.

	:param str scene_file: scene file path.
	:param str directory: directory path.
	:return: dictionary with data.
	:rtype: Dict
	"""

	full_path = path.join_path(directory, scene_file)

	info_dict, file_found = scene_info_from_file(full_path, message=False)
	if not file_found:
		info_dict = create_tag_info_dict()

	info_dict['filePath'] = full_path
	info_dict['extension'] = path.get_extension(full_path)

	return info_dict
