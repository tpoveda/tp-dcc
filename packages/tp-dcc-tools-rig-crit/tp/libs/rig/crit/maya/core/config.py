from __future__ import annotations

import typing

from overrides import override

from tp.maya.cmds import helpers as maya_helpers

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.core import config
from tp.libs.rig.crit.maya.core import managers

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.rig import Rig


def initialize_components_manager(reload: bool = False):
	"""
	Initializes CRIT components manager.

	:param bool reload: whether to force reload of components manager if it is already initialized
	"""

	if reload or MayaConfiguration.COMPONENTS_MANAGER is None:
		components_manager = managers.ComponentsManager()
		components_manager.refresh()
		MayaConfiguration.COMPONENTS_MANAGER = components_manager


class MayaConfiguration(config.Configuration):
	"""
	Class that handles CRIT configuration.
	This configuration handles lot of different rig related data that can be retrieved from a file in disk or from
	metadata from a node within a scene.
	"""

	COMPONENTS_MANAGER: managers.ComponentsManager | None = None

	def __init__(self):

		self._use_proxy_attributes = True
		self._use_containers = False
		self._blackbox = False
		self._hide_control_shapes_in_outliner = True

		super().__init__()

	@classmethod
	def components_manager(cls) -> managers.ComponentsManager:
		"""
		Returns the current component manager instance.

		:return: components manager instance.
		:rtype: managers.ComponentsManager
		"""

		return cls.COMPONENTS_MANAGER

	@property
	def use_containers(self) -> bool:
		"""
		Returns whether component asset container should be created.

		:return: True to create containers; False otherwise.
		:rtype: bool
		"""

		return self._use_containers

	@use_containers.setter
	def use_containers(self, flag: bool):
		"""
		Sets whether component asset container should be created.

		:param bool flag: True to enable asset container; False otherwise.
		"""

		self._use_containers = flag

	@property
	def blackbox(self) -> bool:
		"""
		Returns whether component asset container should be black boxed.

		:return: True if component asset container should be black boxed; False otherwise.
		:rtype: bool
		"""

		return self._blackbox

	@override(check_signature=False)
	def update_from_cache(self, cache: dict, rig: Rig | None = None):
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

			shapes_hidden = cache.get('hideControlShapesInOutliner', None)
			if shapes_hidden is not None:
				for component in rig.iterate_components():
					rig_layer = component.rig_layer()
					if rig_layer is None:
						continue
					for control in rig_layer.iterate_controls():
						for shape in control.iterate_shapes():
							shape.attribute('hiddenInOutliner').set(shapes_hidden)

		super().update_from_cache(cache)

	@override
	def _initialize_managers(self, force: bool = False):
		"""
		Internal function handles the initialization of all the configuration managers.

		:param bool force: whether to force the reloading of the managers.
		"""

		initialize_components_manager(reload=force)
		super()._initialize_managers(force=force)

	@override
	def _initialize_environment(self):
		"""
		Internal function that handles the loading and setup of CRIT preferences from settings.
		"""

		super()._initialize_environment()

		for plugin_required in self._config_cache.get('requiredMayaPlugins', []):
			maya_helpers.load_plugin(plugin_required)

		self._use_proxy_attributes = self._config_cache.get('useProxyAttributes', self._use_proxy_attributes)
		self._use_containers = self._config_cache.get('useContainers', self._use_containers)
		self._blackbox = self._config_cache.get('blackBox', self._blackbox)
		self._hide_control_shapes_in_outliner = self._config_cache.get(
			'hideControlShapesInOutliner', self._hide_control_shapes_in_outliner)

	def components_paths(self):
		"""
		Returns all current registered components paths.

		:return: list of paths.
		:rtype: list(str)
		"""

		return self.COMPONENTS_MANAGER.components_paths()

	def initialize_component_descriptor(self, component_type):
		"""
		Initializes the component descriptor of given type.

		:param str component_type: component type (which is the class name of the component to create).
		:return: initialized component descriptor.
		:rtype: tp.rigtoolkit.crit.lib.maya.core.descriptor.component.ComponentDescriptor
		"""

		return self.COMPONENTS_MANAGER.initialize_component_descriptor(component_type)

	def container_type(self) -> str:
		"""
		Returns the default container type to use ('asset', 'set' or None).

		:return: container type.
		:rtype: str
		"""

		return self._config_cache.get('defaultContainerType', 'asset')
