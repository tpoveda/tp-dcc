from __future__ import annotations

import os
import json

from tp.core import log
from tp.common.python import osplatform, path, folder, jsonio
from tp.common.naming import manager
from tp.preferences.interfaces import crit

PRESET_EXT = 'namingpreset'
CONFIG_EXT = 'namingcfg'
CRIT_PRESET = 'CRIT'

logger = log.rigLogger


class Preset:
	"""
	Class that represents a preset for the naming managers. A preset data has the form of:

	.. code-block:: json

	{
		"name": "Crit",
		"configs": [
		{
			"name": "critGlobalConfig",
			"critType": "global"
		}]
	}
	"""

	def __init__(self, name: str, file_path: str, parent: Preset):
		super().__init__()

		self._name = name
		self._file_path = file_path
		self._parent = parent
		self._managers_data = list()				# type: list[NameManagerData]
		self._children = list()						# type: list[Preset]

	def __repr__(self):
		return f'<{self.__class__.__name__}(name={self._name}) object at {hex(id(self))}>'

	@classmethod
	def load_from_path(cls, file_path: str) -> Preset | None:
		"""
		Loads the preset from a valid absolute preset file path.

		:param str file_path: absolute preset JSON file path to load.
		:return: new loaded preset instance.
		:rtype: Preset or None
		"""

		try:
			logger.debug(f'Loading Preset from path: {file_path}')
			data = jsonio.read_file(file_path)
		except json.decoder.JSONDecodeError:
			logger.error(f'Failed to load preset file: {file_path}', exc_info=True)
			return None

		return cls.load_from_data(data, file_path)

	@classmethod
	def load_from_data(cls, data: dict, file_path: str, parent: Preset | None = None):
		"""
		Loads the preset from the given valid preset data.

		:param dict data: raw preset data to load.
		:param str file_path: file path where preset data was retrieved from.
		:param Preset or None parent: optional parent preset instance.
		:return: new loaded preset instance.
		:rtype: Preset
		"""

		name = data.get('name')
		new_preset = cls(name=name, file_path=file_path, parent=parent)
		for config in data.get('configs', list()):
			config_type = config['type']
			name_manager_data = NameManagerData(config['name'], config_type)
			new_preset.managers_data.append(name_manager_data)

		return new_preset

	@property
	def name(self) -> str:
		"""
		Returns preset name.

		:return: preset name.
		:rtype: str
		"""

		return self._name

	@property
	def file_path(self) -> str:
		"""
		Returns preset file path.

		:return: preset absolute file path.]
		:rtype: str
		"""

		return self._file_path

	@property
	def managers_data(self) -> list[NameManagerData]:
		"""
		Returns list of name manager data for this preset.

		:return: list of naming manager data.
		:rtype: list(NameConfigData)
		"""

		return self._managers_data

	@property
	def children(self) -> list[Preset]:
		"""
		Returns the list of preset children for this preset instance.

		:return: list of preset children.
		:rtype: list(Preset)
		"""

		return self._children

	@property
	def parent(self) -> Preset:
		"""
		Returns the preset parent for this preset instance.

		:return: preset parent.
		:rtype: Preset or None
		"""

		return self._parent

	@parent.setter
	def parent(self, value: Preset):
		"""
		Sets the preset parent for this instance.

		:param Preset or None value: preset parent.
		"""

		self._parent = value

	def exists(self) -> bool:
		"""
		Returns whether this preset exists on disk.

		:return: True if preset exists on disk; False otherwise.
		:rtype: bool
		"""

		return path.is_file(self.file_path)

	def find_name_manager_data_by_type(self, crit_type: str, recursive: bool = True):
		"""
		Returns the configuration data instance stored on the preset with given type.

		:param str crit_type: Crit type to search for.
		:param bool recursive: whether to recursively check parent presets.
		:return: found config data instance with given type.
		:rtype: NameManagerData
		"""

		for name_manager_data in self._managers_data:
			if name_manager_data.crit_type == crit_type:
				return name_manager_data

		if self._parent is not None and recursive:
			return self._parent.find_name_manager_data_by_type(crit_type, recursive=recursive)

	def find_name_manager_data_by_name(self, name: str, recursive: bool = True):
		"""
		Returns the configuration data instance stored on the preset with given type.

		:param str name: name to search for.
		:param bool recursive: whether to recursively check parent presets.
		:return: found config data instance with given name.
		:rtype: NameManagerData
		"""

		for name_manager_data in self._managers_data:
			if name_manager_data.name == name:
				return name_manager_data

		if self._parent is not None and recursive:
			return self._parent.find_name_manager_data_by_name(name, recursive=recursive)

	def find_name_manager_for_type(self, crit_type: str, recursive: bool = True):
		"""
		Finds and returns the naming convention manager used to handle the nomenclature for the given type.

		:param str crit_type: Crit type to search for ('rig', 'module', etc).
		:param bool recursive: whether to recursively check parent presets.
		:return: naming manager instance.
		:rtype: tp.common.naming.manager.NameManager or None
		"""

		preset_config_data = self.find_name_manager_data_by_type(crit_type, recursive=recursive)
		if preset_config_data is None:
			return self.find_name_manager_data_by_type('global').manager

		return preset_config_data.manager

	def serialize(self):
		"""
		Returns the raw dict representing this preset.

		:return: serialized preset data.
		:rtype: dict
		"""

		return {
			'name': self.name,
			'managers_data': [i.serialize() for i in self._managers_data]
		}


class NameManagerData(object):
	"""
	Data class which stores the config name, critType, and linked name manager on a preset.
	"""

	def __init__(self, name: str, crit_type: str):
		super().__init__()

		self._name = name
		self._crit_type = crit_type
		self._manager = None				# type: tp.common.naming.manager.NameManager

	def __eq__(self, other: NameManagerData) -> bool:
		if not isinstance(other, NameManagerData):
			return False
		return self.name == other.name and self.crit_type == other.crit_type

	def __ne__(self, other: NameManagerData) -> bool:
		if not isinstance(other, NameManagerData):
			return True
		return self.name != other.name or self.crit_type != other.crit_type

	def __repr__(self) -> str:
		return f'{self.__class__.__name__}(name={self.name}, type={self.crit_type}'

	@property
	def name(self) -> str:
		return self._name

	@property
	def crit_type(self) -> str:
		return self._crit_type

	@property
	def manager(self) -> 'tp.common.naming.manager.NameManager':
		return self._manager

	@manager.setter
	def manager(self, value: 'tp.common.naming.manager.NameManager'):
		self._manager = value

	def serialize(self):
		"""
		Returns the raw representation of this naming manager data.

		:return: serialized data.
		:rtype: dict
		"""

		return {
			'name': self.name,
			'type': self.crit_type
		}


class PresetsManager(object):
	"""
	Manager to handle the different naming presets used by CRIT.
	"""

	ENV_VAR = 'CRIT_NAME_PRESET_PATH'

	def __init__(self):
		super().__init__()

		# CRIT preference interface instance.
		self._preferences_interface = crit.crit_Interface()

		# full list of preset instances
		self._presets = list()									# type: list[tp.common.naming.rule.Rule]

		# root preset loaded from naming preset hierarchy
		self._root_preset = None								# type: tp.common.naming.rule.Rule or None

		# dictionary containing all naming managers
		self._naming_managers = dict()							# type: dict[str, tp.common.naming.manager.NameManager]

		# dictionary containing all available naming manager types
		self._available_manager_types = set()

	def contains_path(self, file_path: str) -> bool:
		"""
		Returns whether given file path is already registered within this manager.

		:param str file_path: file path pointing to a naming preset file.
		:return: True if given file path is already registered; False otherwise.
		:rtype: bool
		"""

		file_path = path.clean_path(file_path)
		for preset in self._presets:
			if path.clean_path(preset.file_path) == file_path:
				return True

		return False

	def load_from_file(self, file_path: str) -> manager.NameManager | Preset | None:
		"""
		Loads the naming preset or naming manager data from given absolute preset file path.

		:param str file_path: absolute file path to load.
		:return: the loaded preset from given file.
		:rtype: manager.NameManager or Preset or None
		"""

		if not path.is_file(file_path):
			return

		if file_path.endswith('.' + PRESET_EXT):
			loaded_preset = Preset.load_from_path(path.clean_path(file_path))
			if loaded_preset is not None:
				self._presets.append(loaded_preset)
				for manager_data in loaded_preset.managers_data:
					self._available_manager_types.add(manager_data.crit_type)
				return loaded_preset
		elif file_path.endswith('.' + CONFIG_EXT):
			loaded_manager = manager.NameManager.from_path(file_path)
			self._naming_managers[loaded_manager.name] = loaded_manager

	def load_from_directory_path(self, directory: str):
		"""
		Loads all naming preset from the given folder in a recursive way.

		:param str directory: absolute directory path to a folder.
		"""

		if not path.is_dir(directory):
			return

		for root, dirs, files in os.walk(directory):
			for preset_file in files:
				file_path = path.join_path(root, preset_file)
				self.load_from_file(file_path)

	def load_from_hierarchy(self, hierarchy: dict):
		"""
		Loads all presets and constructs the preset hierarchy based on the given preset hierarchy data.

		:param dict hierarchy: hierarchy data:
			{'name': 'CRIT', 'children': [
				{'name': 'defaultPreset', 'children': []},
				{'name': 'UE5Preset', 'children': [
					{'name': 'UE5ClaviclePreset', 'children': []}, {'name': 'UE5ThumbPreset', 'children': []}]}]}
		..info: by calling this function, the cache will be clear.
		"""

		self._presets.clear()
		self._root_preset = None
		self._naming_managers.clear()
		self._available_manager_types.clear()

		paths = osplatform.get_env_var(self.ENV_VAR, default='').split(os.pathsep)
		pref_paths = self._preferences_interface.naming_preset_paths()

		visited = set()
		for _path in paths + pref_paths:
			_path = path.clean_path(_path)
			if _path in visited:
				continue
			visited.add(_path)
			if self.contains_path(_path):
				continue
			if path.is_dir(_path):
				self.load_from_directory_path(_path)
			elif path.is_file(_path):
				self.load_from_file(_path)
			elif not path.exists(_path):
				logger.warning('Invalid missing preset path will be ignored: {}'.format(_path))
				continue

		self._load_preset_hierarchy(hierarchy)

	def hierarchy_data(self) -> dict:
		"""
		Returns the current hierarchy raw data from the current preset hierarchy.

		:return: preset hierarchy.
		:rtype: dict
		"""

		def _serialize_hierarchy(preset):
			"""
			Internal function that recursively serializes the given preset.

			:param Preset preset: preset to serialize/
			:return: serialized preset.
			:rtype: dict
			"""

			return {
				'name': preset.name,
				'children': [_serialize_hierarchy(child_preset) for child_preset in preset.children]
			}

		return dict() if not self._root_preset else _serialize_hierarchy(self._root_preset)

	def create_preset(self, name: str, directory: str, parent: Preset | None = None) -> Preset:
		"""
		Creates a new preset instance.

		:param str name: name for the new preset.
		:param str directory: directory where the preset should be created.
		:param Preset or None parent: optional parent for the new preset.
		:return: newly created preset instance.
		:rtype: Preset
		..info:: the new created preset will not be saved into disk.
		"""

		file_path = path.join_path(directory, os.path.extsep.join((name, PRESET_EXT)))
		new_preset = Preset(name=name, file_path=file_path, parent=parent)
		if parent is not None:
			parent.children.append(new_preset)
		self._presets.append(new_preset)

		return new_preset

	def find_preset(self, name: str) -> Preset | None:
		"""
		Returns the present instance with given name.

		:param str name: name of the preset to find.
		:return: found preset instance.
		:rtype: Preset or None
		"""

		for found_preset in self._presets:
			if found_preset.name == name:
				return found_preset

		return None

	def remove_preset(self, name: str) -> bool:
		"""
		Removes the preset by name and returns whether deletion operation was successful. Preste only will be removed
		from memory not from disk.

		:param str name: name of the preset to remove.
		:return: True if the preset remove operation was successful; False otherwise.
		:rtype: bool
		..note:: this function will also modify the parent preset.
		"""

		found_preset = self.find_preset(name)
		if found_preset is None:
			return False

		parent_preset = found_preset.parent
		if parent_preset is not None:
			parent_preset.children.remove(found_preset)

		self._presets.remove(found_preset)

		return True

	def delete_preset(self, preset: Preset) -> bool:
		"""
		Deletes the given preset instance from the manager and deletes the preset file.

		:param Preset preset: preset instance to remove.
		:return: True if the preset delete operation was successful; False otherwise.
		:rtype: bool
		"""

		if preset.exists():
			logger.debug(f'Deleting Preset file: {preset.file_path}')
			os.remove(preset.file_path)

		for manager_data in preset.managers_data:
			found_manager = manager_data.manager
			file_path = found_manager.config_path
			if path.is_file(file_path):
				logger.debug(f'Deleting configuratin file: "{file_path}"')
				os.remove(file_path)

		return self.remove_preset(preset.name)

	def config_save_folder(self) -> str:
		"""
		Returns the current folder which all new presets will be saved into.

		:return: absolute presets save folder.
		:rtype: str
		"""

		return self._preferences_interface.naming_preset_save_path()

	def save_manager(self, naming_manager: manager.NameManager) -> bool:
		"""
		Saves the given naming manage instance to disk.

		:param manager.NameManager naming_manager: manager instance to save.
		:return: True if manager data was saved successfully; False otherwise.
		:rtype: bool
		"""

		if not naming_manager.config_path:
			config_folder = self.config_save_folder()
			file_path = path.join_path(config_folder, os.path.extsep.join([naming_manager.name, CONFIG_EXT]))
			naming_manager.config_path = file_path
		else:
			config_folder = path.dirname(naming_manager.config_path)
		logger.info(f'Saving Naming data: "{naming_manager.config_path}"')
		folder.ensure_folder_exists(config_folder)
		jsonio.write_to_file(naming_manager.serialize(), naming_manager.config_path)

		return True

	def _load_preset_hierarchy(self, hierarchy):
		"""
		Internal function that handles the loading of the given naming hierarchy data.

		:param dict hierarchy: hierarchy data:
			{'name': 'CRIT', 'children': [
				{'name': 'defaultPreset', 'children': []},
				{'name': 'UE5Preset', 'children': [
					{'name': 'UE5ClaviclePreset', 'children': []}, {'name': 'UE5ThumbPreset', 'children': []}]}]}
		"""

		def _process_child(child_hierarchy, parent):
			"""
			Internal recursive function that process the given hierarchy.

			:param dict child_hierarchy: child data.
			:param Preset or None parent: parent preset to load.
			:return: newly processed Preset instance.
			:rtype: Preset or None
			"""

			name = child_hierarchy['name']
			try:
				child_preset = current_presets[name]
			except KeyError:
				logger.error('Missing naming manager preset: {}'.format(name))
				return
			if parent:
				parent.children.append(child_preset)
			child_preset.parent = parent

			for name_manager_data in child_preset.managers_data:
				name_manager = self._naming_managers.get(name_manager_data.name)
				if name_manager is None:
					# if no manager found we set it to the CRIT global one
					name_manager_data.manager = global_config
					continue
				name_manager_data.manager = name_manager
				parent_manager = global_config if name_manager_data.crit_type != 'global' else None
				if parent is not None:
					parent_manager = parent.find_name_manager_for_type(name_manager_data.crit_type)
				name_manager.parent_manager = parent_manager

			for _child_hierarchy in child_hierarchy.get('children', list()):
				_process_child(_child_hierarchy, parent=child_preset)

			return child_preset

		current_presets = {i.name: i for i in self._presets}
		global_config = self._naming_managers['critGlobalConfig']

		if hierarchy:
			root = _process_child(hierarchy, parent=None)
		else:
			root = self.find_preset(CRIT_PRESET)

		for preset in self._presets:
			if preset.parent is None and preset != root:
				preset.parent = root
				root.children.append(preset)

		self._root_preset = root
