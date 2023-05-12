from __future__ import annotations

import json
import contextlib
import collections

from tp.core import log
from tp.common.python import profiler
from tp.maya import api

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.core import errors, naming
from tp.libs.rig.crit.maya.core import config, component
from tp.libs.rig.crit.maya.meta import rig
from tp.libs.rig.crit.maya.library.functions import rigs

logger = log.rigLogger


class Rig:
	"""
	Main entry class for any given rig, which is composed by a root node and a meta node.
	This class handles the construction and destruction of rig components.
	"""

	def __init__(self, rig_config: config.RigConfiguration | None = None, meta: rig.CritRig | None = None):
		super().__init__()

		self._meta = meta
		self._components_cache = set()					# type: set[component.Component]
		self._config = rig_config or config.RigConfiguration()

	def __repr__(self) -> str:
		return f'<{self.__class__.__name__}> name:{self.name()}'

	def __bool__(self) -> bool:
		return self.exists()

	def __eq__(self, other: Rig) -> bool:
		return self._meta == other.meta

	def __ne__(self, other: Rig) -> bool:
		return self._meta != other.meta

	def __hash__(self):
		return hash(self._meta) if self._meta is not None else hash(id(self))

	def __len__(self) -> int:
		return len(self.components())

	def __contains__(self, item: component.Component) -> bool:
		return True if self.component(item.name(), item.side()) else False

	def __getattr__(self, item: str):
		if item.startswith('_'):
			return super(Rig, self).__getattribute__(item)
		splitter = item.split('_')
		if len(splitter) < 2:
			return super(Rig, self).__getattribute__(item)
		component_name = '_'.join(splitter[:-1])
		component_side = splitter[-1]
		component_found = self.component(component_name, component_side)
		if component_found is not None:
			return component_found

		return super(Rig, self).__getattribute__(item)

	@property
	def meta(self) -> rig.CritRig:
		return self._meta

	@property
	def configuration(self) -> config.RigConfiguration:
		return self._config

	@profiler.fn_timer
	def start_session(self, name: str | None = None, namespace: str | None = None):
		"""
		Starts a rig session for the rig with given name.

		:param str or None name: optional rig name to initialize, if it does not exist, one will be created.
		:param namespace: optional rig namespace.
		:return: root meta node instance for this rig.
		:rtype: rig.CritRig
		"""

		meta = self._meta
		if meta is None:
			meta = rigs.root_rig_by_name(name=name, namespace=namespace)
		if meta is not None:
			self._meta = meta
			logger.info(f'Found rig in scene, initializing rig "{self.name()}" for session')
			self.configuration.update_from_rig(self)
			return self._meta

		namer = self.naming_manager()
		meta = rig.CritRig(name=namer.resolve('rigMeta', {'rigName': name, 'type': 'meta'}))
		meta.attribute(consts.CRIT_NAME_ATTR).set(name)
		meta.attribute(consts.CRIT_ID_ATTR).set(name)
		meta.create_transform(namer.resolve('rigHrc', {'rigName': name, 'type': 'hrc'}))
		meta.create_selection_sets(namer)
		self._meta = meta

		return self._meta

	def exists(self) -> bool:
		"""
		Returns whether this rig exists by checking the existing of the meta node.

		:return: True if rig exists within current scene; False otherwise.
		:rtype: bool
		"""

		return self._meta is not None and self._meta.exists()

	def name(self) -> str:
		"""
		Retursn the name of the rig by accessing meta node data.

		:return: rig name.
		:rtype: str
		"""

		return self._meta.rig_name() if self.exists() else ''

	def naming_manager(self) -> 'tp.common.naming.manager.NameManager':
		"""
		Returns the naming manager for the current rig instance.

		:return: naming manager.
		:rtype: tp.common.naming.manager.NameManager
		"""

		return self.configuration.find_name_manager_for_type('rig')

	def cached_configuration(self):
		"""
		Returns the configuration cached on the rigs meta node config attribute as a dictionary.

		:return: configuration dict.
		:rtype: dict
		"""

		config_plug = self._meta.attribute(consts.CRIT_RIG_CONFIG_ATTR)
		try:
			config_data = config_plug.value()
			if config_data:
				return json.loads(config_data)
		except ValueError:
			pass

		return dict()

	@profiler.fn_timer
	def save_configuration(self) -> dict:
		"""
		Serializes and saves the configuration for this rig on the meta node instance.

		:return: saved serialized configuration.
		:rtype: dict
		"""

		config_data = self.configuration.serialize()
		if config_data:
			config_plug = self._meta.attribute(consts.CRIT_RIG_CONFIG_ATTR)
			config_plug.set(json.dumps(config_data))

		return config_data

	def root_transform(self) -> 'tp.maya.api.DagNode' | None:
		"""
		Returns the root transform node for this rig instance.

		:return: root transform instance.
		:rtype: tp.maya.api.DagNode or None
		"""

		return self._meta.root_transform() if self.exists() else None

	def components_layer(self) -> 'tp.libs.rig.crit.maya.meta.layers.CritComponentsLayer' | None:
		"""
		Returns the components layer instance from this rig by querying the attached meta node.

		:return: components layer instance.
		:rtype: tp.libs.rig.crit.maya.meta.componentslayer.CritComponentsLayer or None
		"""

		return self._meta.components_layer()

	def get_or_create_components_layer(self) -> 'tp.libs.rig.crit.maya.meta.layers.CritComponentsLayer':
		"""
		Returns the components layer if it is attached to this rig or creates a new one and attaches it.

		:return: components layer instance.
		:rtype: tp.libs.rig.crit.maya.meta.layers.CritComponentsLayer
		"""

		components_layer = self.components_layer()
		if not components_layer:
			namer = self.naming_manager()
			hierarchy_name, meta_name = naming.compose_rig_names_for_layer(
				namer, self.name(), consts.COMPONENTS_LAYER_TYPE)
			components_layer = self._meta.create_layer(
				consts.COMPONENTS_LAYER_TYPE, hierarchy_name=hierarchy_name, meta_name=meta_name,
				parent=self._meta.root_transform())

		return components_layer

	def create_component(
			self, component_type: str | None = None, name: str | None = None, side: str | None = None,
			descriptor: 'tp.libs.rig.crit.maya.descriptors.component.ComponentDescriptor' | None = None):
		"""
		Adds a new component instance to the rig and creates the root node structure for that component.

		:param str component_type: component type (which is the class name of the component to create).
		:param str name: name of the new component.
		:param str side: side of the new component.
		:param tp.rigtoolkit.crit.lib.maya.core.descriptor.component.ComponentDescriptor descriptor: optional component
			descriptor.
		:return: new instance of the created component.
		:rtype: tp.libs.rig.crit.maya.descriptors.component.ComponentDescriptor
		:raises errors.CritMissingComponentType: if not component with given type is registered.
		"""

		if descriptor:
			component_type = component_type or descriptor['type']
			name = name or descriptor['name']
			side = side or descriptor['side']
		else:
			descriptor = self.configuration.initialize_component_descriptor(component_type)

		component_class = self.configuration.components_manager().find_component_by_type(component_type)
		if not component_class:
			raise errors.CritMissingComponentType(component_type)

		name = name or descriptor['name']
		side = side or descriptor['side']
		unique_name = naming.unique_name_for_component_by_rig(self, name, side)
		components_layer = self.get_or_create_components_layer()

		descriptor['side'] = side
		descriptor['name'] = unique_name
		init_component = component_class(rig=self, descriptor=descriptor)
		init_component.create(parent=components_layer)
		self._components_cache.add(init_component)

		return init_component

	def has_component(self, name: str, side: str = 'M') -> bool:
		"""
		Returns whether a component with given name and side exists for this rig instance.

		:param str name: name of the component.
		:param str side: side of the component.
		:return: True if component with given name and side exists for this rig; False otherwise.
		:rtype: bool
		"""

		for component_found in self.iterate_components():
			if component_found.name() == name and component_found.side() == side:
				return True

		return False

	def components(self) -> list[component.Component]:
		"""
		Returns a list of all component instances initialized within current scene for this rig.

		:return: list of components for this rig.
		:rtype: list[component.Component]
		"""

		return list(self.iterate_components())

	def iterate_root_components(self) -> collections.Iterator[component.Component]:
		"""
		Generator function that iterates over all root components in this rig.

		:return: iterated root components.
		:rtype: collections.Iterator[component.Component]
		"""

		for component in self.iterate_components():
			if not component.has_parent():
				yield component

	def iterate_components(self) -> collections.Iterator[component.Component]:
		"""
		Generator function that iterates over all components in this rig.

		:return: iterated components.
		:rtype: collections.Iterator[component.Component]
		:raises ValueError: if something happens when retrieving a component from manager instance.
		"""

		found_components = set()
		visited_meta = set()

		for component in self._components_cache:
			if not component.exists():
				continue
			found_components.add(component)
			visited_meta.add(component.meta)
			yield component

		components_layer = self.components_layer()
		if components_layer is None:
			return

		components_manager = self.configuration.components_manager()
		for component_metanode in components_layer.iterate_components():
			try:
				if component_metanode in visited_meta:
					continue
				component = components_manager.from_meta_node(rig=self,  meta=component_metanode)
				found_components.add(component)
				visited_meta.add(component.meta)
				yield component
			except ValueError:
				logger.error('Failed to initialize component: {}'.format(component_metanode.name()), exc_info=True)
				raise errors.CritInitializeComponentError(component_metanode.name())

		self._components_cache = found_components

	def component(self, name: str, side: str = 'M') -> component.Component | None:
		"""
		Tries to find the component by name and side by first check the component cache for this rig instance and
		after that checking the components via meta node network.

		:param str name: component name to find.
		:param str side: component side to find.
		:return: found component instance.
		:rtype: component.Component or None
		"""

		for component_found in self._components_cache:
			if component_found.name() == name and component_found.side() == side:
				return component_found

		components_layer = self.get_or_create_components_layer()
		if components_layer is None:
			return None

		components_manager = self.configuration.components_manager()
		for component_metanode in components_layer.iterate_components():
			component_name = component_metanode.attribute(consts.CRIT_NAME_ATTR).asString()
			component_side = component_metanode.attribute(consts.CRIT_SIDE_ATTR).asString()
			if component_name == name and component_side == side:
				return components_manager.from_meta_node(rig=self, meta=component_metanode)

		return None

	@contextlib.contextmanager
	def build_script_context(self, build_script_type: str, **kwargs):
		"""
		Executes all build scripts assigned in the buildScript configuration.

		:param str build_script_type:
		:param dict kwargs: keyword arguments for the build script.
		"""

		pre_fn_name, post_fn_name = consts.BUILD_SCRIPT_FUNCTIONS_MAPPING.get(build_script_type)

		script_configuration = self.meta.build_script_configuration()
		if pre_fn_name:
			for script in self.configuration.build_scripts:
				if hasattr(script, pre_fn_name):
					logger.info('Executing pre build script function: {}'.format(
						'.'.join((script.__class__.__name__, pre_fn_name))))
					script_properties = script_configuration.get(script.ID, dict())
					script.rig = self
					getattr(script, pre_fn_name)(properties=script_properties, **kwargs)
		yield
		if post_fn_name:
			for script in self.configuration.build_scripts:
				if hasattr(script, post_fn_name):
					logger.info('Executing post build script function: {}'.format(
						'.'.join((script.__class__.__name__, pre_fn_name))))
					script_properties = script_configuration.get(script.ID, dict())
					script.rig = self
					getattr(script, pre_fn_name)(properties=script_properties, **kwargs)

	@profiler.fn_timer
	def build_guides(self, components: list[component.Component] | None = None):
		"""
		Builds all the guides for the current rig initialized components. If a component has guides already built it
		will be skipped.

		:param list[component.Component] or None components: list of components to
			build guides for. If None, all components guides for this rig instance will be built.
		:return: True if the build guides operation was successful; False otherwise.
		:rtype: bool
		"""

		self.configuration.update_from_rig(self)
		child_parent_relationship = {component: component.parent() for component in self.iterate_components()}
		components = components or list(child_parent_relationship.keys())

		with self.build_script_context(consts.GUIDE_FUNCTION_TYPE):
			self._build_components(components, child_parent_relationship, 'build_guide')
			mod = api.DGModifier()
			for comp in components:
				comp.update_naming(layer_types=(consts.GUIDE_LAYER_TYPE,), mod=mod, apply=False)
			mod.doIt()
			self.set_guide_visibility(
				state_type=consts.GUIDE_LAYER_TYPE,
				control_value=self.configuration.guide_control_visibility,
				guide_value=self.configuration.guide_pivot_visibility)

		return True

	def set_guide_visibility(self, state_type, include_root=False, **kwargs):
		"""
		Sets all components guides visibility.

		:param str state_type: state type to set visibility of.
		:param bool include_root: whether to set visibility of the root guide.
		:param dict kwargs: extra keyword arguments.
		"""

		is_guide_type = state_type == consts.GUIDE_PIVOT_STATE or state_type == consts.GUIDE_PIVOT_CONTROL_STATE
		is_control_type = state_type == consts.GUIDE_CONTROL_STATE or state_type == consts.GUIDE_PIVOT_CONTROL_STATE
		control_value = kwargs.get('controlValue')
		guide_value = kwargs.get('guideValue')
		if is_control_type:
			self.configuration.guide_control_visibility = control_value
		if is_guide_type:
			self.configuration.guide_pivot_visibility = guide_value

		self.save_configuration()

		modifier = api.DGModifier()
		for component_found in self.iterate_components():
			if not component_found.has_guide():
				continue
			guide_layer = component_found.guide_layer()
			root_transform = guide_layer.root_transform()
			if root_transform is not None:
				root_transform.setVisible(True, mod=modifier, apply=False)
			if is_control_type:
				guide_layer.set_guide_control_visible(control_value)
			_include_root = (False if include_root is None else True) or component_found.has_parent()
			if is_guide_type:
				guide_layer.set_guides_visible(guide_value, include_root=include_root)
		modifier.doIt()

	def _build_components(
			self, components: list[component.Component],
			child_parent_relationship: dict, build_fn_name: str, **kwargs) -> bool:
		"""
		Internal function that handles the build of the component based on the given build function name.

		:param list[component.Component] components: list of components to build.
		:param dict child_parent_relationship: dictionary that maps each component with its parent component.
		:param str build_fn_name: name of the component build function to execute.
		:param dict kwargs: keyword arguments to pass to the build function.
		:return: True if the build operation was successful; False otherwise.
		:rtype: bool
		"""

		def _process_component(comp, parent_component):

			# first build parent component if any
			if parent_component is not None and parent_component not in visited:
				_process_component(parent_component, current_components[parent_component])
			if comp in visited:
				return False
			visited.add(comp)

			parent_descriptor = comp.descriptor.parent
			if parent_descriptor:
				# this situation can happen when rebuilding a rig from a template for example, where it is likely that
				# parent has not been added, by they are defined within component descriptor, so we rebuild them if
				# possible.
				logger.info('Component descriptor has parents defined, adding them...')
				existing_component = self.component(*parent_descriptor.split(':'))
				if existing_component is not None:
					comp.set_parent(existing_component)

			try:
				logger.info('Building component: {}, with method: {}'.format(comp, build_fn_name))
				getattr(comp, build_fn_name)(**kwargs)
				return True
			except errors.CritBuildComponentUnknownError:
				logger.error('Failed to build for: {}'.format(comp))
				return False

		component_build_order = component.construct_component_order(components)
		current_components = child_parent_relationship
		visited = set()

		for child, parent in component_build_order.items():
			success = _process_component(child, parent)
			if not success:
				return False

		return True
