from tp.common.python import path, folder, yamlio, timedate

from tp.libs.rig.crit.library.functions import files


class Asset:

	_INSTANCE = None			# type: Asset

	def __init__(self, project: 'tp.libs.rig.crit.core.project.Project', name: str, asset_type: str):
		super().__init__()

		self._name = name
		self._type = asset_type
		self._project = project
		if not self._project:
			raise Exception('Project is not given!')
		self._path = path.join_path(self._project.path, f'{self._type.lower()}s', self._name)

		# create asset directories
		folder.ensure_folder_exists(self._path)
		self._controls = folder.ensure_folder_exists(path.join_path(self._path, 'controls'))
		self._skeleton = folder.ensure_folder_exists(path.join_path(self._path, 'skeleton'))
		self._build = folder.ensure_folder_exists(path.join_path(self._path, 'build'))
		self._rig = folder.ensure_folder_exists(path.join_path(self._path, 'rig'))
		self._settings = folder.ensure_folder_exists(path.join_path(self._path, 'settings'))

		files.create_empty_scene(path.join_path(self._skeleton, f'{self._name}_skeleton.0000.ma'))
		files.create_empty_scene(path.join_path(self._rig, f'{self._name}_rig.0000.ma'))

		# set environment variables
		Asset._INSTANCE = self
		self._project.update_meta()
		self.update_meta()

	def __repr__(self):
		return f'Asset: {self.name}({self.type}), Model: {self.model_path}'

	@property
	def name(self) -> str:
		return self._name

	@property
	def path(self) -> str:
		return self._path

	@property
	def type(self) -> str:
		return self._type

	@property
	def project(self) -> 'tp.libs.rig.crit.core.project.Project':
		return self._project

	@property
	def meta_path(self) -> str:
		return path.join_path(self.path, f'{self.name}.meta')

	@property
	def meta_data(self) -> dict:
		return yamlio.read_file(self.meta_path) if path.is_file(self.meta_path) else dict()

	@property
	def controls(self) -> str:
		return self._controls

	@property
	def skeleton(self) -> str:
		return self._skeleton

	@property
	def build(self) -> str:
		return self._build

	@property
	def rig(self) -> str:
		return self._rig

	@property
	def settings(self) -> str:
		return self._settings

	@property
	def model_path(self) -> str:
		return self.meta_data.get('model', '')

	@property
	def latest_skeleton_path(self) -> str:
		return files.latest_file(f'{self.name}_skeleton', self.skeleton, extension='ma', full_path=True)

	@property
	def new_skeleton_path(self) -> str:
		return files.new_versioned_file(f'{self.name}_skeleton', self.skeleton, extension='ma', full_path=True)

	@property
	def latest_rig_path(self) -> str:
		return files.latest_file(f'{self.name}_rig', self.rig, extension='ma', full_path=True)

	@property
	def new_rig_path(self) -> str:
		return files.new_versioned_file(f'{self.name}_rig', self.rig, extension='ma', full_path=True)

	@property
	def latest_build_path(self) -> str:
		return files.latest_file(f'{self.name}_build', self.build, extension='ma', full_path=True)

	@property
	def new_build_path(self) -> str:
		return files.new_versioned_file(f'{self.name}_build', self.build, extension='ma', full_path=True)

	@classmethod
	def get(cls):
		"""
		Returns current active CRIT asset instance.

		:return: active CRIT asset instance.
		:rtype: Asset or None
		"""

		return cls._INSTANCE

	def set_data(self, key: str, value: str):
		"""
		Sets given pair key/value within project metadata file.

		:param str key: metadata key to set value of.
		:param str value: metadata value to set.
		"""

		data_dict = self.meta_data
		data_dict[key] = value
		data_dict['modified'] = timedate.get_date_and_time()
		yamlio.write_to_file(data_dict, self.meta_path)

	def update_meta(self):
		"""
		Updates metadata file with the internal data of this instance.
		"""

		meta_dict = self.meta_data
		meta_dict.update({
			'name': self.name,
			'type': self.type,
			'modified': timedate.get_date_and_time(),
		})
		meta_dict['model'] = meta_dict.get('model', '')
		if 'created' not in meta_dict:
			meta_dict['created'] = timedate.get_date_and_time()
		yamlio.write_to_file(meta_dict, self.meta_path)
