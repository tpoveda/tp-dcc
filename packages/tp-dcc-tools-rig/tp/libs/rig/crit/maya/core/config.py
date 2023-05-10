from __future__ import annotations

import os

from tp.common import plugin
from tp.common.python import helpers
from tp.maya.cmds import helpers as maya_helpers
from tp.preferences.interfaces import crit

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.core import namingpresets, buildscript


def initialize_components_manager(reload=False):
	"""
	Initializes CRIT components manager.

	:param bool reload: whether to force reload of components manager if it is already initialized
	"""

	pass

	# if reload or RigConfiguration.COMPONENTS_MANAGER is None:
	# 	components_manager = managers.ComponentsManager()
	# 	components_manager.refresh()
	# 	Configuration.COMPONENTS_MANAGER = components_manager


def initialize_build_scripts_manager(preference_interface, reload=False):
	"""
	Initializes CRIT build scripts manager.

	:param preference_interface: CRIT preference interface instance.
	:param bool reload: whether to force reload of the naming preset manager if it is already initialized
	"""

	if reload or RigConfiguration.BUILD_SCRIPTS_MANAGER is None:
		build_scripts_manager = plugin.PluginFactory(
			interface=buildscript.BaseBuildScript, plugin_id='ID', package_name='crit')
		paths = os.getenv(RigConfiguration.BUILD_SCRIPTS_VAR, '').split(os.pathsep)
		paths += preference_interface.user_build_script_paths()
		helpers.add_to_environment('TPDCC_BASE_PATHS', paths)
		build_scripts_manager.register_paths_from_env_var(RigConfiguration.BUILD_SCRIPTS_VAR, package_name='crit')
		build_scripts_manager.register_paths(preference_interface.user_build_script_paths(), package_name='crit')
		build_scripts_manager.load_all_plugins(package_name='crit')
		RigConfiguration.BUILD_SCRIPTS_MANAGER = build_scripts_manager


def initialize_naming_preset_manager(preference_interface, reload=False):
	"""
	Initializes Naming preset manager.

	:param preference_interface: CRIT preference interface instance.
	:param bool reload: whether to force reload of the naming preset manager if it is already initialized
	"""

	if reload or RigConfiguration.NAMING_PRESET_MANAGER is None:
		presets_manager = namingpresets.PresetsManager()
		hierarchy = preference_interface.naming_preset_hierarchy()
		presets_manager.load_from_hierarchy(hierarchy)
		RigConfiguration.NAMING_PRESET_MANAGER = presets_manager


class RigConfiguration:
	"""
	Class that handles the configuration of a rig.
	This configuration handles lot of different rig related data that can be retrieved from a file in disk or from
	metadata from a node within a scene.
	"""

	BUILD_SCRIPTS_VAR = 'CRIT_BUILD_SCRIPTS_PATH'

	NAMING_PRESET_MANAGER = None			# type: tp.libs.rig.crit.core.presets.PresetsManager
	BUILD_SCRIPTS_MANAGER = None  			# type: tp.common.plugin.factory.PluginFactory
	COMPONENTS_MANAGER = None				# type: tp.libs.rig.crit.maya.core.managers.ComponentsManager

	def __init__(self):
		super().__init__()

		self._config_cache = dict()
		self._current_naming_preset = None							# type: tp.libs.rig.crit.core.naming.Preset
		self._build_scripts = list()								# type: list[str]
		self._use_proxy_attributes = True
		self._use_containers = False
		self._blackbox = False
		self._selection_child_highlighting = False
		self._auto_align_guides = True
		self._delete_on_fail = False
		self._preferences_interface = crit.crit_Interface()
		self._single_chain_hierarchy = True
		self._guide_control_visibility = False
		self._guide_pivot_visibility = True
		self._build_skeleton_marking_menu = False

		self._initialize_managers()
		self._initialize_environment()

	@classmethod
	def name_presets_manager(cls) -> 'tp.libs.rig.crit.core.presets.PresetsManager':
		"""
		Returns the naming presets manager used by this configuration.

		:return: naming presets manager.
		:rtype: tp.libs.rig.crit.core.presets.PresetsManager
		"""

		return cls.NAMING_PRESET_MANAGER

	@property
	def preferences_interface(self) -> 'CritPreferenceInterface':
		"""
		Returns CRIT preferences interface instance.

		:return: CRIT preferences interface.
		:rtype: CritPreferenceInterface
		"""

		return self._preferences_interface

	@property
	def use_containers(self) -> bool:
		"""
		Returns whether component asset container should be created.

		:return: True to create containers; False otherwise.
		:rtype: bool
		"""

		return self._use_containers

	@property
	def blackbox(self) -> bool:
		"""
		Returns whether component asset container should be black boxed.

		:return: True if component asset container should be black boxed; False otherwise.
		:rtype: bool
		"""

		return self._blackbox

	@property
	def delete_on_fail(self) -> bool:
		"""
		Returns whether a component should be automatically deleted if it fails to build.

		:return: True if this feature is enabled; False otherwise.
		:rtype: bool
		"""

		return self._delete_on_fail

	@property
	def current_naming_preset(self) -> 'tp.libs.rig.crit.core.naming.Preset' | None:
		"""
		Returns current naming preset.

		:return: naming preset.
		:rtype: tp.libs.rig.crit.core.naming.Preset or None
		"""

		return self._current_naming_preset

	@property
	def build_scripts(self) -> list[str]:
		"""
		Returns list of directories or Python file paths which can be run during build time.

		:return: list of build script absolute paths.
		:rtype: list(str)
		"""

		return self._build_scripts

	@property
	def selection_child_highlighting(self) -> bool:
		"""
		Returns whether selection child highlighting should be enabled when building rig controls.

		:return: True if selection child highlighting feature should be enabled; False otherwise.
		:rtype: bool
		"""

		return self._selection_child_highlighting

	@property
	def auto_align_guides(self) -> bool:
		"""
		Returns whether auto alignment should be run when building the skeleton layer.

		:return: True if guides auto alignment should be run; False otherwise.
		:rtype: bool
		"""

		return self._auto_align_guides

	@property
	def single_chain_hierarchy(self) -> bool:
		"""
		Returns whether skeleton will be created under a unique chain hierarchy (so it is suitable for games).

		:return: True if skeleton will be created under a unique chain hierarchy; False otherwise.
		:rtype: bool
		"""

		return self._single_chain_hierarchy

	@property
	def guide_control_visibility(self) -> bool:
		"""
		Returns whether guide controls are visible.

		:return: True if guide controls are visible; False otherwise.
		:rtype: bool
		"""

		return self._guide_control_visibility

	@property
	def guide_pivot_visibility(self) -> bool:
		"""
		Returns whether guide pivot is visible.

		:return: True if guide pivot is visible; False otherwise.
		:rtype: bool
		"""

		return self._guide_pivot_visibility

	@property
	def build_skeleton_marking_menu(self) -> bool:
		"""
		Returns whether skeleton custom marking menu should be created.

		:return: True if skeleton custom marking menu should be created; False otherwise.
		:rtype: bool
		"""

		return self._build_skeleton_marking_menu

	def update_from_rig(self, rig: 'tp.libs.rig.crit.maya.core.rig.Rig'):
		"""
		Updates this configuration from the given scene rig instance.

		:param tp.libs.rig.maya.core.rig.Rig rig: rig instance to pull configuration data from.
		:return: updated configuration dictionary.
		:rtype: dict
		"""

		cache = rig.cached_configuration()
		self.update_from_cache(cache)
		return cache

	def update_from_cache(self, cache: dict, rig: 'tp.libs.rig.crit.maya.core.rig.Rig' | None = None):
		"""
		Updates this configuration from the given configuration dictionary.

		:param dict cache: configuration dictionary to update this configuration from.
		:param tp.libs.rig.crit.maya.core.rig.Rig rig: optional rig instance to pull configuration data from.
		"""

		if rig is not None:
			blackbox = cache.get('blackBox')
			if blackbox is not None:
				rig.blackBox = blackbox
			guide_controls_visibility = cache.get('guideControlVisibility')
			guide_pivot_visibility = cache.get('guidePivotVisibility')
			if guide_controls_visibility is not None or guide_pivot_visibility is not None:
				control_state = -1 if guide_controls_visibility is None else consts.GUIDE_CONTROL_STATE
				guide_state = -1 if guide_pivot_visibility is None else consts.GUIDE_PIVOT_STATE
				if control_state == consts.GUIDE_PIVOT_STATE and guide_state == consts.GUIDE_PIVOT_STATE:
					visibility_state = consts.GUIDE_PIVOT_CONTROL_STATE
				elif control_state == consts.GUIDE_CONTROL_STATE:
					visibility_state = consts.GUIDE_CONTROL_STATE
				else:
					visibility_state = consts.GUIDE_PIVOT_STATE
				rig.set_guide_visibility(
					visibility_state,
					control_value=guide_controls_visibility,
					guide_value=guide_pivot_visibility,
					include_root=False)

		try:
			preset_name = cache['namingPreset']
			self.set_naming_preset_by_name(preset_name)
		except KeyError:
			pass

		for setting, value in cache.items():

			if setting == 'buildScripts':
				self.set_build_scripts(value)
				continue

			if hasattr(self, setting):
				setattr(self, setting ,value)

	def serialize(self) -> dict:
		"""
		Serializes current configuration data.

		:return: serialized data.
		:rtype: dict
		"""

		cache = self._config_cache
		overrides = dict()

		for setting in ('useProxyAttributes',
						'useContainers',
						'blackBox',
						'requiredMayaPlugins',
						'selectionChildHighlighting',
						'autoAlignGuides',
						'guidePivotVisibility',
						'guideControlVisibility'):
			config_state = cache.get(setting)
			if hasattr(self, setting):
				current_state = getattr(self, setting)
				if current_state != config_state:
					overrides[setting] = current_state

		for build_script in self._build_scripts:
			properties = build_script.get(build_script.ID, dict())
			overrides.setdefault('buildScripts', list()).append([build_script.ID, properties])

		if self._current_naming_preset.name != consts.DEFAULT_BUILTIN_PRESET_NAME:
			overrides[consts.NAMING_PRESET_DESCRIPTOR_KEY] = self._current_naming_preset.name

		return overrides

	def find_name_manager_for_type(self, crit_type: str, preset_name: str | None = None):
		"""
		Finds and returns the naming convention manager used to handle the nomenclature for the given type.

		:param str crit_type: Crit type to search for ('rig', 'module', etc).
		:param str or None preset_name: optional preset to use find the Crit type.
		:return: naming manager instance.
		:rtype: tp.common.naming.manager.NameManager or None
		"""

		preset = self._current_naming_preset
		if preset_name:
			preset = self.NAMING_PRESET_MANAGER.find_preset(preset_name)

		return preset.find_name_manager_for_type(crit_type)

	def set_naming_preset_by_name(self, name: str):
		"""
		Sets the current naming convention preset by the given name.

		:param str name: name of the preset to set as active.
		"""

		preset = self.NAMING_PRESET_MANAGER.find_preset(name)
		if preset is None:
			preset = self.NAMING_PRESET_MANAGER.find_preset(consts.DEFAULT_PRESET_NAME)

		self._current_naming_preset = preset

	def set_build_scripts(self, script_ids):
		"""
		Sets the current build scripts that should be executed for the rigs using this configuration.

		:param list(str) script_ids: list of script IDs to set.
		"""

		build_scripts_manager = self.BUILD_SCRIPTS_MANAGER
		self._build_scripts.clear()
		for build_script_id in script_ids:
			build_script = build_scripts_manager.get_loaded_plugin_from_id(build_script_id, package_name='crit')
			if build_script:
				self._build_scripts.append(build_script)

	def _initialize_managers(self, force: bool = False):
		"""
		Internal function handles the initialization of all the configuration managers.

		:param bool force: whether to force the reloading of the managers.
		"""

		initialize_components_manager(reload=force)
		initialize_build_scripts_manager(self._preferences_interface, reload=force)
		initialize_naming_preset_manager(self._preferences_interface, reload=force)

	def _initialize_environment(self):
		"""
		Internal function that handles the loading and setup of CRIT preferences from settings.
		"""

		# we update the cache to optimize speed
		self._config_cache = self._preferences_interface.settings().get('settings', dict())

		for plugin_required in self._config_cache.get('requiredMayaPlugins', list()):
			maya_helpers.load_plugin(plugin_required)

		self._use_proxy_attributes = self._config_cache.get('useProxyAttributes', self._use_proxy_attributes)
		self._use_containers = self._config_cache.get('useContainers', self._use_containers)
		self._blackbox = self._config_cache.get('blackBox', self._blackbox)
		self._selection_child_highlighting = self._config_cache.get(
			'selectionChildHighlighting', self._selection_child_highlighting)
		self._guide_control_visibility = self._config_cache.get('guideControlVisibility',
																self._guide_control_visibility)
		self._guide_pivot_visibility = self._config_cache.get('guidePivotVisibility', self._guide_pivot_visibility)

		self.set_build_scripts(self._config_cache.get('buildScripts', list()))
		self.set_naming_preset_by_name(self._config_cache.get('defaultNamingPreset', consts.DEFAULT_PRESET_NAME))
