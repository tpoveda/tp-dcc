from __future__ import annotations

import copy

from tp.bootstrap import log
from tp.common.python import profiler
from tp.maya import api
from tp.maya.cmds import helpers

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.core import errors, naming
from tp.libs.rig.crit.maya.descriptors import component
from tp.libs.rig.crit.maya.library.functions import names
from tp.libs.rig.crit.maya.meta import layers, component as meta_component

logger = log.tpLogger


def construct_component_order(components: list[Component]) -> dict[Component, Component]:
	"""
	Handles the component order based on DG order. Parent components will be built before child components.

	:param list[Component] components: list of components to build.
	:return: list of components ordered by build order.
	:rtype: dict[Component, Component]
	"""

	unsorted = dict()
	for found_component in components:
		parent = found_component.parent()
		unsorted[found_component] = parent

	ordered = dict()
	while unsorted:
		for child, parent in list(unsorted.items()):
			if parent in unsorted:
				continue
			else:
				del(unsorted[child])
				ordered[child] = parent

	return ordered


def reset_joint_transforms(skeleton_layer: layers.CritSkeletonLayer, guide_layer_descriptor: 'tp.libs.rig.crit.maya.descriptors.layers.GuideLayerDescriptor', id_mapping):
	"""
	Resets all joints on the given skeleton layer to match the guide descriptor.

	:param layers.CritSkeletonLayer deform_layer: component skeleton layer instance.
	:param tp.libs.rig.crit.maya.descriptors.layers.GuideLayerDescriptor guide_layer_descriptor: component guide layer
		descriptor instance.
	:param dict id_mapping:
	"""

	descriptor_id_map = id_mapping[consts.SKELETON_LAYER_TYPE]
	joint_mapping = {v: k for k, v  in descriptor_id_map.items()}
	guide_descriptors = {i.id: i for i in guide_layer_descriptor.find_guides(*descriptor_id_map.keys()) if i is not None}
	for joint in skeleton_layer.iterate_joints():
		guide_id = joint_mapping.get(joint.id())
		if not guide_id:
			continue
		guide_descriptor = guide_descriptors.get(guide_id)
		world_matrix = guide_descriptor.transformationMatrix(scale=False)
		world_matrix.setScale((1, 1, 1), api.kWorldSpace)
		joint.resetTransform()
		joint.setWorldMatrix(world_matrix.asMatrix())


class Component:
	"""
	Component class that encapsulates a single rigging component.
	"""

	ID = ''
	DOCUMENTATION = ''
	REQUIRED_PLUGINS = list()

	def __init__(
			self, rig: 'tp.libs.rig.crit.maya.core.rig.Rig', descriptor: component.ComponentDescriptor | None = None,
			meta: meta_component.CritComponent | None = None):
		super().__init__()

		self._meta = meta
		self._rig = rig
		self._descriptor = None
		self._original_descriptor = None					# type: component.ComponentDescriptor
		self._container = None
		self._configuration = rig.configuration
		self._is_building_guide = False
		self._is_building_skeleton = False
		self._is_building_rig = False
		self._build_objects_cache = dict()

		if descriptor is None and meta is not None:
			no_component_type = False
			component_type = meta.attribute(consts.CRIT_COMPONENT_TYPE_ATTR).asString()
			if not component_type:
				no_component_type = True
				component_type = self.ID
			component_descriptor = self.configuration.initialize_component_descriptor(component_type)
			if no_component_type:
				meta.attribute(consts.CRIT_COMPONENT_TYPE_ATTR).set(component_type)
			self._original_descriptor = self.configuration.components_manager().load_component_descriptor(
				component_type)
			scene_state = self._descriptor_from_scene()
			if scene_state:
				scene_data = component.migrate_to_latest_version(scene_state, original_descriptor=component_descriptor)
				component_descriptor.update(scene_data)
			self._descriptor = component_descriptor
		elif descriptor and meta:
			self._original_descriptor = copy.deepcopy(descriptor)
			self._descriptor = self._descriptor_from_scene()
		else:
			self._original_descriptor = descriptor
			self._descriptor = copy.deepcopy(descriptor)

		self.logger = log.get_logger('.'.join([__name__, '_'.join([self.name(), self.side()])]))

	def __hash__(self):
		return hash(self._meta) if self._meta is not None else hash(id(self))

	def __repr__(self) -> str:
		return f'<{self.__class__.__name__}>-{self.name()}:{self.side()}'

	def __bool__(self) -> bool:
		return self.exists()

	def __eq__(self, other: Component) -> bool:
		return other is not None and isinstance(other, Component) and self._meta == other.meta

	def __ne__(self, other: Component) -> bool:
		return other is not None and isinstance(other, Component) and self._meta != other.meta

	@classmethod
	def load_required_plugins(cls):
		"""
		Loads all required plugins for this component to work as expected.

		:raises Exception: if something went wrong while loading plugins.
		"""

		for plugin_name in cls.REQUIRED_PLUGINS:
			if not helpers.is_plugin_loaded(plugin_name):
				try:
					logger.info(f'Loading plugin {plugin_name} required by {cls}')
					helpers.load_plugin(plugin_name, quiet=True)
				except Exception:
					logger.exception(f'Failed to load plugin {plugin_name} required by {cls}')
					raise

	@property
	def meta(self) -> meta_component.CritComponent:
		"""
		Returns component meta node instance.

		:return: meta node instance.
		:rtype: meta_component.CritComponent
		"""

		return self._meta

	@meta.setter
	def meta(self, value: meta_component.CritComponent):
		"""
		Sets component meta node instance.

		:param meta_component.CritComponent value: meta node instance to set.
		"""

		self._meta = value

	@property
	def configuration(self) -> 'tp.libs.rig.crit.maya.core.config.RigConfiguration':
		"""
		Returns component configuration instance.

		:return: configuration instance.
		:rtype: tp.libs.rig.crit.maya.core.config.RigConfiguration
		"""

		return self._configuration

	@property
	def component_type(self) -> str:
		"""
		Returns the component type for this component instance.

		:return: component type name.
		:rtype: str
		"""

		return self.__class__.__name__ if not self.exists() else self.meta.attribute(
			consts.CRIT_COMPONENT_TYPE_ATTR).asString()

	@property
	def rig(self) -> 'tp.libs.rig.crit.maya.core.rig.Rig':
		"""
		Returns the current rig instance this component belongs to.

		:return: rig instance.
		:rtype: tp.libs.rig.crit.maya.core.rig.Rig
		"""

		return self._rig

	@property
	def descriptor(self) -> component.ComponentDescriptor:
		"""
		Returns the component descriptor instance.

		:return: component descriptor instance.
		:rtype: component.ComponentDescriptor
		"""

		return self._descriptor

	@descriptor.setter
	def descriptor(self, value: component.ComponentDescriptor):
		"""
		Sets the component descriptor.

		:param component.ComponentDescriptor value: component descriptor to set.
		"""

		if type(value) == dict:
			value = component.load_descriptor(value, self._original_descriptor)

		self._descriptor = value

	@property
	def blackBox(self) -> bool:
		"""
		Returns whether this component asset container is blackboxed.

		:return: True if component asset container is blackboxed; False otherwise.
		:rtype: bool
		"""

		container = self.container()

		return False if not container or not container.blackBox else True

	@blackBox.setter
	def blackBox(self, flag: bool):
		"""
		Sets whether this component asset container is blackboxed.

		:param bool flag: True to blackbox component asset container; False otherwise.
		"""

		container = self.container()
		if container:
			container.blackBox = flag

	@profiler.fn_timer
	def create(
			self, parent: 'tp.libs.rig.crit.maya.meta.rig.CritRig' | None = None) -> meta_component.CritComponent:
		"""
		Creates the component within current scene.

		:param tp.libs.rig.crit.maya.meta.rig.CritRig parent: optional rig parent layer which component will connect
			to via its meta node instance.
		:return: newly created component meta node instance.
		:rtype: meta_component.CritComponent
		"""

		if not parent or not isinstance(parent, layers.CritComponentsLayer):
			parent = None

		self.load_required_plugins()

		self.logger.debug('Creating component stub in current scene...')
		descriptor = self.descriptor
		naming_manager = self.naming_manager()
		component_name, side = self.name(), self.side()
		hierarchy_name, meta_name = naming.compose_component_root_names(naming_manager, component_name, side)
		self.logger.debug('Creating Component meta node instance...')
		meta_node = meta_component.CritComponent(name=meta_name, parent=parent)
		meta_node.attribute(consts.CRIT_NAME_ATTR).set(component_name)
		meta_node.attribute(consts.CRIT_SIDE_ATTR).set(side)
		meta_node.attribute(consts.CRIT_ID_ATTR).set(component_name)
		meta_node.attribute(consts.CRIT_VERSION_ATTR).set(descriptor.get('version', ''))
		meta_node.attribute(consts.CRIT_COMPONENT_TYPE_ATTR).set(descriptor.get('type', ''))
		notes = meta_node.attribute('notes')
		if notes is None:
			meta_node.addAttribute('notes', type=api.kMFnDataString, value=self.DOCUMENTATION)
		else:
			notes.set(self.DOCUMENTATION)
		parent_transform = parent.root_transform() if parent else None
		meta_node.create_transform(hierarchy_name, parent=parent_transform)
		self._meta = meta_node

		return meta_node

	def exists(self) -> bool:
		"""
		Returns whether this component exists within current scene.

		:return: True if component meta node and its root transform node exist within current scene; False otherwise.
		:rtype: bool
		"""

		try:
			return True if self._meta and self._meta.exists() else False
		except AttributeError:
			self.logger.warning('Component does not exist: {}'.format(self.descriptor.name), exc_info=True)

		return False

	def name(self) -> str:
		"""
		Returns the name of the component from its descriptor.

		:return: component name.
		:rtype: str
		"""

		return self.descriptor.name

	def indexed_name(self) -> str:
		"""
		Returns indexed name from meta node name.

		:return: indexed name.
		:rtype: str
		"""

		return names.deconstruct_name(self.meta.fullPathName()).indexed_name if self.exists() else ''

	def side(self) -> str:
		"""
		Returns the side of the component from its descriptor.

		:return: component side.
		:rtype: str
		"""

		return self.descriptor.side if self.descriptor else names.deconstruct_name(self.meta.fullPathName()).side

	def root_transform(self) -> api.DagNode | None:
		"""
		Returns the root transform node for this component instance.

		:return: root transform instance.
		:rtype: api.DagNode or None
		"""

		return self._meta.root_transform() if self.exists() else None

	def has_parent(self) -> bool:
		"""
		Returns whether this component has a parent component.

		:return: True if this component has a parent component; False otherwise.
		:rtype: bool
		"""

		if self._meta is None:
			return False

		for parent_meta in self._meta.iterate_meta_parents():
			if parent_meta.hasAttribute(consts.CRIT_IS_COMPONENT_ATTR):
				return True

		return False

	def parent(self) -> Component | None:
		"""
		Returns the parent component object for this component.

		:return: parent component.
		:rtype: Component or None
		"""

		if self._meta is None:
			return None

		if self._is_building_guide or self._is_building_skeleton or self._is_building_rig:
			return self._build_objects_cache.get('parent')

		for parent_meta in self._meta.iterate_meta_parents(recursive=False):
			if parent_meta.hasAttribute(consts.CRIT_IS_COMPONENT_ATTR):
				return self._rig.component(
					parent_meta.attribute(consts.CRIT_NAME_ATTR).value(),
					parent_meta.attribute(consts.CRIT_SIDE_ATTR).value()
				)

	def namespace(self) -> str:
		"""
		Returns the current namespace for this component.

		:return: component namespace.
		:rtype: str
		"""

		if self._meta is None:
			return ':'.join([api.OpenMaya.MNamespace.currentNamespace(), self.name()])

		name = api.OpenMaya.MNamespace.getNamespaceFromName(self._meta.fullPathName())
		root = api.OpenMaya.MNamespace.rootNamespace()
		if not name.startswith(root):
			name = root + name

		return name

	def parent_namespace(self) -> str:
		"""
		Returns the parent namespace of this component namespace.

		:return: parent component namespace.
		:rtype: str
		"""

		namespace = self.namespace()
		if not namespace:
			return api.OpenMaya.MNamespace.rootNamespace()

		current_namespace = api.OpenMaya.MNamespace.currentNamespace()
		api.OpenMaya.MNamespace.setCurrentNamespace(namespace)
		try:
			parent = api.OpenMaya.MNamespace.parentNamespace()
			api.OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
		except RuntimeError:
			parent = api.OpenMaya.MNamespace.rootNamespace()

		return parent

	def rename_namespace(self, namespace: str) -> bool:
		"""
		Renames the namespace which ascts as the component name.

		:param str namespace: new namespace.
		:return: True if rename namespace operation was successful; False otherwise.
		:rtype: bool
		"""

		component_namespace = self.namespace()
		if api.OpenMaya.MNamespace.namespaceExists(namespace):
			return False

		parent_namespace = self.parent_namespace()
		if parent_namespace == api.OpenMaya.MNamespace.rootNamespace():
			return False

		current_namespace = api.OpenMaya.MNamespace.currentNamespace()
		api.OpenMaya.MNamespace.setCurrentNamespace(parent_namespace)
		try:
			api.OpenMaya.MNamespace.renameNamespace(component_namespace, namespace)
			api.OpenMaya.MNamespace.setCurrentNamespace(current_namespace)
		except RuntimeError:
			self.logger.error(f'Failed to rename namespace: {component_namespace}-> {namespace}')
			return False

		return True

	def remove_namespace(self) -> bool:
		"""
		Deletes the namespace of this component and moves all children to the root namespace.

		:return: True if the remove namespace operation was successful; False otherwise.
		:rtype: bool
		"""

		namespace = self.namespace()
		if namespace:
			api.OpenMaya.MNamespace.moveNamespace(namespace, api.OpenMaya.MNamespace.rootNamespace(), True)
			api.OpenMaya.MNamespace.removeNamespace(namespace)
			return True

		return False

	def has_container(self) -> bool:
		"""
		Returns whether this component has a container.

		:return: True if component has a container; False otherwise.
		:rtype: bool
		"""

		return self.container() is not None

	def create_container(self) -> api.ContainerAsset:
		"""
		Creates a new asset container if it is not already created and attaches it to this component instance.

		:return: newly created container asset instance.
		:rtype: api.ContainerAsset
		..note:: this operation will not merge component nodes into the container.
		"""

		if not self.configuration.use_containers:
			return None

		container = self.container()
		if container is not None:
			return container

		container = api.ContainerAsset()
		name, side = self.name(), self.side()
		container_name = naming.compose_container_name(self.naming_manager(), name, side)
		container.create(container_name)
		container.message.connect(self._meta.container)
		self._container = container

		return container

	def container(self) -> api.ContainerAsset | None:
		"""
		Returns the container node which is retrieved from the meta node instance.

		:return: api.ContainerAsset or None
		"""

		if not self._meta or not self._meta.exists() or not self.configuration.use_containers:
			return None

		source = self._meta.container.source()
		if source is not None:
			return api.ContainerAsset(source.node().object())

	def delete_container(self) -> bool:
		"""
		Deletes the container of this component and all its contents.

		:return: True if the container deletion operation was successful; False otherwise.
		:rtype: bool
		"""

		container = self.container()
		if not container:
			return False

		container.delete()

		return True

	def naming_manager(self) -> 'tp.common.naming.manager.NameManager':
		"""
		Returns the naming configuration for this component instance.

		:return: naming manager.
		:rtype: tp.common.naming.manager.NameManager
		"""

		naming_manager = self._build_objects_cache.get('naming')
		if naming_manager is not None:
			return naming_manager

		return self.configuration.find_name_manager_for_type(
			self.component_type, preset_name=self.current_naming_preset().name)

	def current_naming_preset(self) -> 'tp.libs.rig.crit.core.namingpreset.Preset':
		"""
		Returns the current naming convention preset instance for this component.

		:return: naming convention preset.
		:rtype: tp.libs.rig.crit.core.namingpreset.Preset
		"""

		local_override = self.descriptor.get(consts.NAMING_PRESET_DESCRIPTOR_KEY)
		local_preset = self.configuration.name_presets_manager().find_preset(local_override) if local_override else None

		return local_preset if local_preset is not None else self.configuration.current_naming_preset

	def update_naming(self, layer_types: tuple | None = None, mod: api.DGModifier | None = None, apply: bool = True):
		"""
		Updates any nodes names on the component from the current naming manager instance.

		:param tuple[str] layer_types: a tuple of layer types whose nodes we want to rename.
		:param api.DGModifier or None mod: modifier to use when renaming a node.
		:param bool apply: whether to run the modifier immediately.
		:return: modifier instance used, or the created one if None is given.
		:rtype: api.DGModifier
		"""

		layer_types = layer_types or (consts.GUIDE_LAYER_TYPE, consts.SKELETON_LAYER_TYPE)

		self._generate_objects_cache()
		mod = mod or api.DGModifier()
		name_manager = self.naming_manager()
		meta = self._meta
		root_transform = self.root_transform()
		container = self.container()
		component_name, component_side = self.name(), self.side()

		nodes_to_lock = [meta, root_transform]
		if container is not None:
			nodes_to_lock.append(container)
		for node_to_lock in nodes_to_lock:
			node_to_lock.lock(False, mod=mod, apply=False)

		try:
			hierarchy_name, meta_name = naming.compose_component_root_names(name_manager, component_name, component_side)
			meta.rename(meta_name, mod=mod, apply=False)
			root_transform.rename(hierarchy_name, mod=mod, apply=False)
			if container is not None:
				container_name = naming.compose_container_name(name_manager, component_name, component_side)
				container.rename(container_name, mod=mod, apply=False)
			if consts.GUIDE_LAYER_TYPE in layer_types and self.has_guide():
				self._set_guide_naming(name_manager, mod)
			if consts.SKELETON_LAYER_TYPE in layer_types and self.has_skeleton():
				self._set_deform_naming(name_manager, mod)
			for node_to_lock in nodes_to_lock:
				node_to_lock.lock(True, mod=mod, apply=False)
			if apply:
				mod.doIt()
		finally:
			self._build_objects_cache.clear()

		return mod

	def set_guide_naming(self, naming_manager: 'tp.common.naming.manager.NameManager', mod: api.DGModifier):
		"""
		Function that can be overridden in subclasses to update the naming convention for the guides.

		:param tp.common.naming.manager.NameManager naming_manager: name manager instance for this component.
		:param api.DGModifier mod: modifier instance to use when renaming nodes.
		"""

		pass

	def set_skeleton_naming(self, naming_manager: 'tp.common.naming.manager.NameManager', mod: api.DGModifier):
		"""
		Function that can be overridden in subclasses to update the naming convention for skeleton layer, input layer
		and output layer.

		:param tp.common.naming.manager.NameManager naming_manager: name manager instance for this component.
		:param api.DGModifier mod: modifier instance to use when renaming nodes.
		"""

		pass

	def has_guide(self) -> bool:
		"""
		Returns whether the guides for this component are already been built.

		:return: True if guides are already built; False otherwise.
		:rtype: bool
		"""

		return self.exists() and self.meta.attribute(consts.CRIT_HAS_GUIDE_ATTR).value()

	def has_skeleton(self) -> bool:
		"""
		Returns whether the skeleton for this component is already been built.

		:return: True if skeleton is already built; False otherwise.
		:rtype: bool
		"""

		return self.exists() and self.meta.attribute(consts.CRIT_HAS_SKELETON_ATTR).value()

	def has_rig(self) -> bool:
		"""
		Returns whether the rig for this component is already been built.

		:return: True if rig is already built; False otherwise.
		:rtype: bool
		"""

		return self.exists() and self.meta.attribute(consts.CRIT_HAS_RIG_ATTR).value()

	def has_polished(self) -> bool:
		"""
		Returns whether this component is already polished.

		:return: True if rig is already polished; False otherwise.
		:rtype: bool
		"""

		return self.exists() and self.meta.attribute(consts.CRIT_HAS_POLISHED_ATTR).value()

	def save_descriptor(self, descriptor_to_save: component.ComponentDescriptor):
		"""
		Saves the given descriptor as the descriptor cache and bakes the descriptor into the component meta node
		instance.

		:param dict or tp.rigtoolkit.crit.lib.maya.core.descriptor.component.ComponentDescriptor descriptor_to_save: descriptor
			data to save.
		"""

		if type(descriptor_to_save) == dict:
			descriptor_to_save = component.load_descriptor(descriptor_to_save, self._original_descriptor)

		self._descriptor = descriptor_to_save
		self.logger.debug('Saving descriptor...')
		self._meta.save_descriptor_data(descriptor_to_save.to_scene_data())

	def find_layer(self, layer_type: str) -> layers.CritLayer | None:
		"""
		Finds and returns the layer instance of given type for this component.

		:param str layer_type: layer type to get.
		:return: found layer meta node instance.
		:rtype: layers.CritLayer or None
		:raises ValueError: if given layer type is not supported.
		"""

		if layer_type not in consts.LAYER_TYPES:
			raise ValueError('Unsupported layer type: {}, supported types: {}'.format(layer_type, consts.LAYER_TYPES))
		if not self.exists():
			return None

		return self._meta.layer(layer_type)

	def input_layer(self) -> layers.CritInputLayer | None:
		"""
		Returns the input layer meta node instance for this component.

		:return: input layer meta node instance.
		:rtype: layers.CritInputLayer or None
		"""

		root = self._meta
		if not root:
			return
		if self._is_building_guide or self._is_building_skeleton or self._is_building_rig:
			return self._build_objects_cache.get(layers.CritInputLayer.ID)

		return root.layer(consts.INPUT_LAYER_TYPE)

	def output_layer(self) -> layers.CritOutputLayer | None:
		"""
		Returns the output layer meta node instance for this component.

		:return: output layer meta node instance.
		:rtype: layers.CritOutputLayer or None
		"""

		root = self._meta
		if not root:
			return
		if self._is_building_guide or self._is_building_skeleton or self._is_building_rig:
			return self._build_objects_cache.get(layers.CritOutputLayer.ID)

		return root.layer(consts.OUTPUT_LAYER_TYPE)

	def guide_layer(self) -> layers.CritGuideLayer | None:
		"""
		Returns the guide layer meta node instance for this component.

		:return: guide's layer meta node instance.
		:rtype: layers.CritGuideLayer or None
		"""

		root = self._meta
		if not root:
			return
		if self._is_building_guide or self._is_building_skeleton or self._is_building_rig:
			return self._build_objects_cache.get(layers.CritGuideLayer.ID)

		return root.layer(consts.GUIDE_LAYER_TYPE)

	def skeleton_layer(self) -> layers.CritSkeletonLayer | None:
		"""
		Returns skeleton layer meta node instance for this component.

		:return: skeleton layer meta node instance.
		:rtype: layers.CritSkeletonLayer or None
		"""

		root = self._meta
		if not root:
			return
		if self._is_building_guide or self._is_building_skeleton or self._is_building_rig:
			return self._build_objects_cache.get(layers.CritSkeletonLayer.ID)

		return root.layer(consts.SKELETON_LAYER_TYPE)

	def rig_layer(self) -> layers.CritRigLayer | None:
		"""
		Returns rig layer meta node instance for this component.

		:return: deform layer meta node instance.
		:rtype: layers.CritRigLayer or None
		"""

		root = self._meta
		if not root:
			return
		if self._is_building_guide or self._is_building_skeleton or self._is_building_rig:
			return self._build_objects_cache.get(layers.CritRigLayer.ID)

		return root.layer(consts.RIG_LAYER_TYPE)

	def geometry_layer(self) -> layers.CritGeometryLayer | None:
		"""
		Returns geometry layer meta node instance for this component.

		:return: geometry layer meta node instance.
		:rtype: layers.CritGeometryLayer or None
		"""

		root = self._meta
		if not root:
			return
		if self._is_building_guide or self._is_building_skeleton or self._is_building_rig:
			return self._build_objects_cache.get(layers.CritGeometryLayer.ID)

		return root.layer(consts.GEOMETRY_LAYER_TYPE)

	# def control_panel(self):
	# 	"""
	# 	Returns control panel instance for this rig layer instance.
	#
	# 	:return: control panel node from the scene.
	# 	:rtype: nodes.SettingNode or None
	# 	"""
	#
	# 	rig_layer = self.rig_layer()
	# 	if not rig_layer:
	# 		return None
	#
	# 	return rig_layer.setting_node(consts.CONTROL_PANEL_TYPE)

	@profiler.fn_timer
	def build_guide(self):
		"""
		Builds the guide system for this component. This method handles:
			- Creation of the guide system.
			- Setting up guide layer metadata.

		:raises errors.CritComponentDoesNotExistError: if the component does not exist.
		:raises errors.CritBuildComponentGuideUnknownError: if an unknown error occurs while building the guide system.
		"""

		if not self.exists():
			raise errors.CritComponentDoesNotExistError

		self._generate_objects_cache()
		if self.has_guide():
			self.guide_layer().root_transform().show()
		if self.has_polished():
			self._set_has_polished(False)
		has_skeleton = self.has_skeleton()
		if has_skeleton:
			self._set_has_skeleton(False)

		self.logger.info('Building guide: {}'.format(self.name()))
		self._is_building_guide = True
		container = self.container()
		if container is None:
			container = self.create_container()
			self._build_objects_cache['container'] = container
		if container is not None:
			container.makeCurrent(True)
			container.lock(False)

		self.logger.info('Starting guide building with namespace: {}'.format(self.namespace()))
		try:
			hierarchy_name, meta_name = naming.compose_names_for_layer(
				self.naming_manager(), self.name(), self.side(), consts.GUIDE_LAYER_TYPE)
			guide_layer = self._meta.create_layer(
				consts.GUIDE_LAYER_TYPE, hierarchy_name, meta_name, parent=self._meta.root_transform())
			guide_layer.update_metadata(self.descriptor.guideLayer.get(consts.METADATA_DESCRIPTOR_KEY, list()))
			self._build_objects_cache[layers.CritGuideLayer.ID] = guide_layer
			self.pre_setup_guide()
			self.setup_guide()
			self.post_setup_guide()
			self.save_descriptor(self._descriptor)
			self._set_has_guide(True)
			if has_skeleton:
				reset_joint_transforms(self.skeleton_layer(), self.descriptor.guideLayer, self.id_mapping())
		except Exception as exc:
			self.logger.error('Failed to setup guides: {}'.format(exc), exc_info=True)
			self._set_has_guide(False)
			raise errors.CritBuildComponentGuideUnknownError('Failed {}'.format('_'.join([self.name(), self.side()])))
		finally:
			if container is not None:
				container.makeCurrent(False)
			self._is_building_guide = False
			self._build_objects_cache.clear()

		return True

	def pre_setup_guide(self):
		"""
		Pre setup guide function that is run before build_guide function is called. This function handles:
			- The creation of the guides structure using the component descriptor data.
		"""

		self.logger.info('Running pre-setup guide...')
		self._setup_guide_settings()

		self.logger.info('Generating guides from descriptor...')
		guide_layer = self.guide_layer()
		current_guides = {guide_node.id(): guide_node for guide_node in guide_layer.iterate_guides()}
		component_name, component_side = self.name(), self.side()
		name_manager = self.naming_manager()

		# re-parent existing guides if required
		post_parenting = list()
		for guide_descriptor in self.descriptor.guideLayer.iterate_guides():
			guide_id = guide_descriptor['id']
			current_scene_guide = current_guides.get(guide_id)
			guide_name = name_manager.resolve(
				'guideName', {'componentName': component_name, 'side': component_side, 'id': guide_id, 'type': 'guide'})
			if current_scene_guide is not None:
				current_scene_guide.create_attributes_from_dict({v['name']: v for v in guide_descriptor.get('attributes', list())})
				current_scene_guide.rename(guide_name)
				_, parent_id = current_scene_guide.guide_parent()
				if parent_id != guide_descriptor['parent']:
					post_parenting.append((current_scene_guide, guide_descriptor['parent']))
				continue

			shape_transform = guide_descriptor.get('shapeTransform', dict())
			new_guide = guide_layer.create_guide(
				id=guide_descriptor['id'],
				name=guide_name,
				translate=guide_descriptor.get('translate', (0.0, 0.0, 0.0)),
				rotate=guide_descriptor.get('rotate', (0.0, 0.0, 0.0, 1.0)),
				scale=guide_descriptor.get('scale', (1.0, 1.0, 1.0)),
				rotateOrder=guide_descriptor.get('rotateOrder', 0),
				shape=guide_descriptor.get('shape'),
				locShape=guide_descriptor.get('locShape'),
				color=guide_descriptor.get('color'),
				shapeTransform={
					'translate': shape_transform.get('translate', (0.0, 0.0, 0.0)),
					'rotate': shape_transform.get('rotate', (0.0, 0.0, 0.0, 1.0)),
					'scale': shape_transform.get('scale', (1.0, 1.0, 1.0)),
					'rotateOrder': shape_transform.get('rotateOrder', 0),
					'worldMatrix': shape_transform.get('worldMatrix'),
					'matrix': shape_transform.get('matrix')
				},
				parent=guide_descriptor.get('parent', 'root'),
				root=guide_descriptor.get('root', False),
				worldMatrix=guide_descriptor.get('worldMatrix'),
				matrix=guide_descriptor.get('matrix'),
				srts=guide_descriptor.get('srts', list()),
				selectionChildHighlighting=self.configuration.selection_child_highlighting,
				pivotShape=guide_descriptor.get('pivotShape', 0),
				pivotColor=guide_descriptor.get('pivotColor', consts.DEFAULT_GUIDE_PIVOT_COLOR),
				attributes=guide_descriptor.get('attributes', list())
			)
			current_guides[guide_id] = new_guide

			shape_node = new_guide.shape_node()
			if shape_node:
				[guide_layer.add_extra_nodes(cns.utility_nodes() for cns in api.iterate_constraints(shape_node))]

		for child_guide, parent_id in post_parenting:
			child_guide.setParent(current_guides[parent_id])

		self.logger.info('Completed pre-setup guide successfully!')

	def setup_guide(self):
		"""
		Main guide setup function. Can be overriden to customize the way guides are created in custom components.
		"""

		pass

	def post_setup_guide(self):
		"""
		Post setup guide function that is run after setup_guide function is called.
		"""

		self.logger.info('Running post-setup guide...')
		guide_layer = self.guide_layer()
		guide_layer_transform = guide_layer.root_transform()

		# delete guides in the scene that does not need to exist
		scene_guides = {found_guide.id() for found_guide in guide_layer.iterate_guides()}
		default_guides = {guide_descriptor['id'] for guide_descriptor in self.descriptor.guideLayer.iterate_guides()}
		to_delete = [guide_id for guide_id in scene_guides if guide_id not in default_guides]
		if to_delete:
			guide_layer.delete_guides(*to_delete)

		container = self._merge_component_into_container()
		if container is not None:
			self.logger.info('Publishing guide settings to container')
			container.lock(False)
			settings = guide_layer.setting_node(consts.GUIDE_LAYER_TYPE)
			if settings is not None:
				container.unPublishAttributes()
				container.removeUnboundAttributes()
				container.publishAttributes(
					[i for i in settings.iterateExtraAttributes() if i.partialName(include_node_name=False) not in consts.ATTRIBUTES_TO_SKIP_PUBLISH and not i.isChild and not i.isElement])
			container.blackBox = self.configuration.blackbox

		connectors_group = guide_layer.sourceNodeByName(consts.CRIT_GUIDE_CONNECTORS_GROUP_ATTR)
		name_manager = self.naming_manager()
		component_name, component_side = self.name(), self.side()
		if connectors_group is None:
			name = naming.compose_connectors_group_name(name_manager, component_name, component_side)
			connectors_group = api.factory.create_dag_node(name, 'transform')
			connectors_group.setParent(guide_layer_transform)
			guide_layer.connect_to(consts.CRIT_GUIDE_CONNECTORS_GROUP_ATTR, connectors_group)

		self.logger.debug('Tagging and annotating guide structure')
		guides = list(guide_layer.iterate_guides())
		nodes_to_publish = list()
		for guide in guides:
			parent_guide, id_plug = guide.guide_parent()
			if parent_guide is not None:
				pass
			guide.lock(True)
			nodes_to_publish.append(guide)
			shape_node = guide.shape_node()
			if shape_node:
				nodes_to_publish.append(shape_node)
		if nodes_to_publish and container is not None:
			container.publishNodes(nodes_to_publish)

	def _descriptor_from_scene(self) -> component.ComponentDescriptor | None:
		"""
		Internal function that tries to retrieve the descriptor from this component meta node instance.

		:return: component descriptor.
		:rtype: component.ComponentDescriptor or None
		"""

		if not self._meta or not self._meta.exists():
			return None

		data = self._meta.raw_descriptor_data()
		translated_data = component.parse_raw_descriptor(data)
		return component.load_descriptor(translated_data, self._original_descriptor)

	def _generate_objects_cache(self):
		"""
		Internal function that initializes internal build objects cache.
		"""

		self._build_objects_cache = self._meta.layer_id_mapping()
		self._build_objects_cache['container'] = self.container()
		self._build_objects_cache['parent'] = self.parent()
		self._build_objects_cache['naming'] = self.naming_manager()

	def _set_has_guide(self, flag: bool):
		"""
		Internal function that updates the has guide attribute of the meta node instance.

		:param bool flag: True if component has guides; False otherwise.
		"""

		self.logger.debug('Setting hasGuide to: {}'.format(flag))
		has_guide_attr = self._meta.attribute(consts.CRIT_HAS_GUIDE_ATTR)
		has_guide_attr.isLocked = False
		has_guide_attr.setBool(flag)

	def _set_has_skeleton(self, flag: bool):
		"""
		Internal function that updates the has skeleton attribute of the meta node instance.

		:param bool flag: True if component has skeleton; False otherwise.
		"""

		self.logger.debug('Setting hasSkeleton to: {}'.format(flag))
		has_skeleton_attr = self._meta.attribute(consts.CRIT_HAS_SKELETON_ATTR)
		has_skeleton_attr.isLocked = False
		has_skeleton_attr.setBool(flag)

	def _set_has_rig(self, flag: bool):
		"""
		Internal function that updates the has rig attribute of the meta node instance.

		:param bool flag: True if component has a rig; False otherwise.
		"""

		self.logger.debug('Setting hasRig to: {}'.format(flag))
		has_rig_attr = self._meta.attribute(consts.CRIT_HAS_RIG_ATTR)
		has_rig_attr.isLocked = False
		has_rig_attr.setBool(flag)

	def _set_has_polished(self, flag: bool):
		"""
		Internal function that updates the has hasPolished attribute of the meta node instance.

		:param bool flag: True if component has been polished; False otherwise.
		"""

		self.logger.debug('Setting hasPolished to: {}'.format(flag))
		has_rig_attr = self._meta.attribute(consts.CRIT_HAS_POLISHED_ATTR)
		has_rig_attr.isLocked = False
		has_rig_attr.setBool(flag)

	def _setup_guide_settings(self):
		"""
		Internal function that setup guide settings.
		"""

		self.logger.info('Creating guide settings from descriptor...')
		guide_layer = self.guide_layer()
		component_settings = self.descriptor.guideLayer.settings
		if not component_settings:
			return
		existing_settings = guide_layer.guide_settings()
		outgoing_connections = dict()
		if existing_settings is not None:
			existing_settings.attribute('message').disconnect_all()
			for attr in existing_settings.iterateExtraAttributes():
				if attr.isSource:
					outgoing_connections[attr.partialName()] = list(attr.destinations())
			existing_settings.delete()

		name = self.naming_manager().resolve(
			'settingsName', {
				'componentName': self.name(), 'side': self.side(), 'section': consts.GUIDE_LAYER_TYPE,
				'type': 'settings'})
		settings_node = guide_layer.create_settings_node(name, attr_name=consts.GUIDE_LAYER_TYPE)
		modifier = api.DGModifier()
		for setting_descriptor in iter(component_settings):
			if not settings_node.hasAttribute(setting_descriptor.name):
				attr = settings_node.addAttribute(**setting_descriptor)
			else:
				attr = settings_node.attribute(setting_descriptor.name)
				attr.set_from_dict(setting_descriptor)
			conns = outgoing_connections.get(setting_descriptor.name, list())
			for dest in conns:
				if not dest.exists():
					continue
				attr.connect(dest, mod=modifier, apply=False)
		modifier.doIt()

	@profiler.fn_timer
	def _merge_component_into_container(self) -> api.ContainerAsset | None:
		"""
		Internal function that takes all connected nodes recursively and add them to the container. A new container
		will be created if it does not exist.

		:return: component asset container.
		:rtype: api.ContainerAsset or None
		"""

		container = self.container()
		if container is None and self.configuration.use_containers:
			container = self.create_container()
		if container is None:
			return None

		self.logger.debug('Merging nodes which are missing from container')
		meta = self._meta
		root_transform = meta.root_transform()
		nodes_to_add = [root_transform, meta]

		for found_layer in meta.layers_by_id((
				consts.INPUT_LAYER_TYPE, consts.OUTPUT_LAYER_TYPE, consts.GUIDE_LAYER_TYPE,
				consts.SKELETON_LAYER_TYPE, consts.RIG_LAYER_TYPE, consts.XGROUP_LAYER_TYPE)).values():
			if not found_layer:
				continue
			objects = [found_layer, found_layer.root_transform()] + list(found_layer.iterate_settings_nodes())
			objects.extend(list(found_layer.iterate_extra_nodes()))
			nodes_to_add.extend(object for obj in objects if obj not in nodes_to_add)

		if nodes_to_add:
			container.addNodes(nodes_to_add)

		return container

	def _set_guide_naming(self, naming_manager: 'tp.common.naming.manager.NameManager', mod: api.OpenMaya.MDGModifier):
		"""
		Internal function that updates the node names of the guide layer nodes.

		:param tp.common.naming.manager.NameManager naming_manager: naming manager instance to use.
		:param api.MDGModifier mod: optional modifier to use to rename the nodes.
		"""

		def _change_lock_guide_layer(state, apply=True):
			"""
			Internal function that sets the lock state of the guide layer nodes.

			:param bool state: True to lock the guide; False otherwise.
			:param bool apply: whether to apply lock guide change status.
			"""

			guide_layer.lock(state, mod=mod, apply=False)
			transform.lock(state, mod=mod, apply=False)
			for found_guide in guides:
				found_guide.lock(state, mod=mod, apply=False)
			guide_settings.lock(state, mod=mod, apply=apply)

		component_name, component_side = self.name(), self.side()
		hierarchy_name, meta_name = naming.compose_names_for_layer(
			naming_manager, component_name, component_side, consts.GUIDE_LAYER_TYPE)
		guide_layer = self.guide_layer()
		transform = guide_layer.root_transform()
		guides = list(guide_layer.iterate_guides(include_root=True))
		guide_settings = guide_layer.setting_node(consts.GUIDE_LAYER_TYPE)

		_change_lock_guide_layer(False, apply=True)

		try:
			name = naming_manager.resolve(
				'settingsName', {
					'componentName': component_name, 'side': component_side,
					'section': consts.GUIDE_LAYER_TYPE, 'type': 'settings'})
			guide_settings.rename(name, mod=mod, apply=False)
			for found_guide in guides:
				tag = found_guide.controller_tag()
				if tag is None:
					continue
				tag.rename('_'.join([found_guide.name(), 'tag']), mod=mod, apply=False)

			connectors_group = guide_layer.attribute(consts.CRIT_GUIDE_CONNECTORS_GROUP_ATTR).sourceNode()
			connectors_group.rename(naming.compose_connectors_group_name(naming_manager, component_name, component_side))
			guide_layer.rename(meta_name, mod=mod, apply=False)
			transform.rename(hierarchy_name, mod=mod, apply=False)
			self.set_guide_naming(naming_manager, mod)
		finally:
			_change_lock_guide_layer(True)
