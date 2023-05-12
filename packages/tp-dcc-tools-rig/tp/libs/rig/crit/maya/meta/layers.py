from __future__ import annotations

from overrides import override

import collections

import maya.cmds as cmds

from tp.maya import api
from tp.maya.meta import base
from tp.maya.om import plugs, mathlib as om_mathlib, nodes as om_nodes

from tp.libs.rig.crit import consts
from tp.libs.rig.crit.maya.meta import nodes as meta_nodes


class CritLayer(base.DependentNode):
	"""
	Base class for Crit layer nodes. Crit layers are used simply for organization purposes and can be used as the
	entry point ot access rig DAG related nodes.
	"""

	def __init__(self, node=None, name=None, parent=None, init_defaults=True, lock=True, mod=None):
		super().__init__(node=node, name=name, parent=parent, init_defaults=init_defaults, lock=lock, mod=mod)

	@override
	def meta_attributes(self) -> list[dict]:
		"""
		Overrides base meta_attributes function.
		Returns the list of default meta attributes that should 	be added into the meta node during creation.

		:return: list of attributes data within a dictionary.
		:rtype: list[dict]
		"""

		attrs = super().meta_attributes()

		attrs.extend(
			(
				dict(name=consts.CRIT_EXTRA_NODES_ATTR, isArray=True, type=api.kMFnMessageAttribute),
				dict(name=consts.CRIT_ROOT_TRANSFORM_ATTR, type=api.kMFnMessageAttribute),
				dict(name=consts.CRIT_CONNECTORS_ATTR, isArray=True, type=api.kMFnMessageAttribute),
				dict(
					name=consts.CRIT_SETTING_NODES_ATTR, type=api.kMFnCompoundAttribute, isArray=True,
					children=[
						dict(name=consts.CRIT_SETTING_NODE_ATTR, type=api.kMFnMessageAttribute),
						dict(name=consts.CRIT_SETTING_NAME_ATTR, type=api.kMFnDataString),
					]
				),
				dict(
					name=consts.CRIT_TAGGED_NODE_ATTR, type=api.kMFnCompoundAttribute, isArray=True,
					children=[
						dict(name=consts.CRIT_TAGGED_NODE_SOURCE_ATTR, type=api.kMFnMessageAttribute),
						dict(name=consts.CRIT_SETTING_NAME_ATTR, type=api.kMFnDataString),
					]
				)
			)
		)

		return attrs

	@override
	def delete(self, mod: api.OpenMaya.MDGModifier | None = None, apply: bool = True) -> bool:
		"""
		Deletes the node from the scene.

		:param OpenMaya.MDGModifier mod: modifier to add the delete operation into.
		:param bool apply: whether to apply the modifier immediately.
		:return: True if the node deletion was successful; False otherwise.
		:raises RuntimeError: if deletion operation fails.
		:rtype: bool
		"""

		self.lock(True)
		try:
			[s.delete(mod=mod, apply=apply) for s in list(
				self.settings_nodes()) + list(self.extra_nodes()) + list(self.annotations())]
			transform = self.root_transform()
			if transform:
				transform.lock(False)
				transform.delete(mod=mod, apply=apply)
		finally:
			self.lock(False)

		return super().delete(mod=mod, apply=apply)

	@override(check_signature=False)
	def serializeFromScene(self) -> dict:
		"""
		Serializes current layer into a dictionary compatible with JSON.

		:return: JSON compatible dictionary.
		:rtype: dict
		"""

		return dict()

	def show(self, mod: api.OpenMaya.MDGModifier | None = None, apply: bool = True):
		"""
		Sets the visibility for this node to 1.0.

		:param api.OpenMaya.MDGModifier or None mod: optional modifier to use to show this node.
		:param bool apply: whether to apply the operation immediately.
		:return: True if node was showed successfully; False otherwise.
		:rtype: bool
		"""

		root = self.root_transform()
		if root:
			root.show(mod=mod, apply=apply)
			return True

		return False

	def hide(self, mod: api.OpenMaya.MDGModifier | None = None, apply: bool = True) -> bool:
		"""
		Sets the visibility for this node to 0.0.

		:param OpenMaya.MDGModifier or None mod: optional modifier to use to hide this node.
		:param bool apply: whether to apply the operation immediately.
		:return: True if node was hidden successfully; False otherwise.
		:rtype: bool
		"""

		root = self.root_transform()
		if root:
			root.hide(mod=mod, apply=apply)
			return True

		return False

	def root_transform(self) -> api.DagNode:
		"""
		Returns the root transform node for this layer instance.

		:return: root transform instance.
		:rtype: api.DagNode
		"""

		return self.sourceNodeByName(consts.CRIT_ROOT_TRANSFORM_ATTR)

	def create_transform(self, name: str, parent: api.OpenMaya.MObject | api.DagNode | None = None):
		"""
		Creates the transform node within Maya scene linked to this meta node.

		:param str name: name of the transform node.
		:param api.OpenMaya.MObject or api.DagNode or None parent: optional parent node.
		:return: newly created transform node.
		:rtype:
		"""

		layer_transform = api.factory.create_dag_node(name=name, node_type='transform', parent=parent)
		layer_transform.setLockStateOnAttributes(consts.TRANSFORM_ATTRS)
		layer_transform.showHideAttributes(consts.TRANSFORM_ATTRS)
		self.connect_to(consts.CRIT_ROOT_TRANSFORM_ATTR, layer_transform)
		layer_transform.lock(True)

		return layer_transform

	def update_metadata(self, metadata: dict):
		"""
		Updates metadata attribute with given metadata dictionary contents.

		:param dict metadata: metadata dictionary contents.
		"""

		for meta_attr in metadata:
			attribute = self.attribute(meta_attr['name'])
			if attribute is None:
				self.addAttribute(**meta_attr)
			else:
				attribute.set_from_dict(**meta_attr)

	def iterate_extra_nodes(self) -> collections.Iterator[api.DGNode]:
		"""
		Generator function that iterates over all the extra nodes attached to this meta node instance.

		:return: iterated attached extra nodes.
		:rtype: collections.Iterator[api.DGNode]
		"""

		for element in self.attribute(consts.CRIT_EXTRA_NODES_ATTR):
			source = element.source()
			if source:
				yield source.node()

	def add_extra_nodes(self, nodes: list[api.DGNode]):
		"""
		Connects given nodes into this meta node instance as an extra node.

		:param list[api.DGNode] nodes: node to add as extra node.
		"""

		extras_array = self.attribute(consts.CRIT_EXTRA_NODES_ATTR)
		for node in nodes:
			if not node.object():
				continue
			element = extras_array.nextAvailableDestElementPlug()
			node.message.connect(element)

	def add_extra_node(self, node: api.DGNode):
		"""
		Connects given node into this meta node instance as an extra node.

		:param api.DGNode node: node to add as extra node.
		"""

		self.add_extra_nodes([node])

	def iterate_settings_nodes(self) -> collections.Iterator[meta_nodes.SettingsNode]:
		"""
		Generator function that iterates over all the attached settings nodes attached to this meta node instance.

		:return: iterated attached setting node instances.
		:rtype: collections.Iterator[meta_nodes.SettingsNode]
		"""

		settings_nodes_compound_attr = self.attribute(consts.CRIT_SETTING_NODES_ATTR)
		for element in settings_nodes_compound_attr:
			source_node = element.child(0).sourceNode()
			if source_node is not None:
				yield meta_nodes.SettingsNode(node=source_node.object())

	def setting_node(self, name:str) -> meta_nodes.SettingsNode | None:
		"""
		Finds and returns the settings node with given name it exists.

		:param str name: name of the settings node.
		:return: found settings node instance.
		:rtype: meta_nodes.SettingsNode or None
		"""

		for setting_node in self.iterate_settings_nodes():
			if setting_node.id() == name:
				return setting_node

		return None

	def create_settings_node(self, name: str, attr_name: str) -> meta_nodes.SettingsNode:
		"""
		Creates a CRIT setting nodes and adds it to the meta node with given name nad value.

		:param str name: name for the new settings node.
		:param str attr_name: meta attribute name.
		:return: newly created settings node instance.
		:rtype: meta_nodes.SettingsNode
		"""

		setting_node = self.setting_node(attr_name)
		if setting_node is not None:
			return setting_node

		setting_node = meta_nodes.SettingsNode()
		setting_node.create(name, id=attr_name)
		settings_nodes_attr = self.attribute(consts.CRIT_SETTING_NODES_ATTR)
		new_element = settings_nodes_attr.nextAvailableElementPlug()
		self.connect_to_by_plug(new_element.child(0), setting_node)
		new_element.child(1).set(attr_name)
		setting_node.lock(True)

		return setting_node


class CritComponentsLayer(CritLayer):

	ID = consts.COMPONENTS_LAYER_TYPE

	@override
	def meta_attributes(self) -> list[dict]:
		"""
		Overrides base meta_attributes function.
		Returns the list of default meta attributes that should be added into the meta node during creation.

		:return: list of attributes data within a dictionary.
		:rtype: list[dict]
		"""

		attrs = super().meta_attributes()

		attrs.extend([
			{
				'name': 'componentGroups',
				'isArray': True,
				'locked': False,
				'type': api.kMFnDataString,
				'children': [
					{
						'name': 'groupName',
						'type': api.kMFnDataString
					},
					{
						'name': 'groupComponents',
						'type': api.kMFnMessageAttribute,
						'isArray': False,
						'locked': False
					}
				]
			},
		])

		return attrs

	def components(self, depth_limit: int = 256) -> list['tp.libs.rig.crit.maya.meta.component.CritComponent']:
		"""
		Returns all components in order as a list.

		:param int depth_limit: recursive depth limit.
		:return: list of components linked to this layer.
		:rtype: list[tp.libs.rig.crit.maya.meta.component.CritComponent]
		"""

		return list(self.iterate_components(depth_limit=depth_limit))

	def iterate_components(
			self, depth_limit: int = 256) -> collections.Iterator['tp.libs.rig.crit.maya.meta.component.CritComponent']:
		"""
		Generator function that iterates over all components linked to this layer.

		:param int depth_limit: recursive depth limit.
		:return: iterated components linked to this layer.
		:rtype: collections.Iterator[tp.libs.rig.crit.maya.meta.component.CritComponent]
		"""

		for meta_child in self.iterate_meta_children(depth_limit):
			if meta_child.hasAttribute(consts.CRIT_COMPONENT_TYPE_ATTR):
				yield meta_child


class CritGuideLayer(CritLayer):

	ID = consts.GUIDE_LAYER_TYPE

	@override
	def meta_attributes(self) -> list[dict]:
		"""
		Overrides base meta_attributes function.
		Returns the list of default meta attributes that should be added into the meta node during creation.

		:return: list of attributes data within a dictionary.
		:rtype: list(dict)
		"""

		attrs = super().meta_attributes()

		attrs.extend(
			(
				dict(
					name=consts.CRIT_GUIDES_ATTR, type=api.kMFnCompoundAttribute, isArray=True, locked=False,
					children=[
						dict(name=consts.CRIT_GUIDE_NODE_ATTR, type=api.kMFnMessageAttribute, isArray=False),
						dict(name=consts.CRIT_GUIDE_ID_ATTR, type=api.kMFnDataString, isArray=False),
						dict(name=consts.CRIT_GUIDE_SRTS_ATTR, type=api.kMFnMessageAttribute, isArray=True),
						dict(name=consts.CRIT_GUIDE_SHAPE_NODE_ATTR, type=api.kMFnMessageAttribute, isArray=False),
						dict(
							name=consts.CRIT_GUIDE_SOURCE_GUIDES_ATTR, type=api.kMFnCompoundAttribute,
							isArray=True,
							children=[
								dict(name=consts.CRIT_GUIDE_SOURCE_GUIDE_ATTR, type=api.kMFnMessageAttribute, isArray=False),
								dict(name=consts.CRIT_GUIDE_SOURCE_GUIDE_CONSTRAINT_NODES_ATTR, type=api.kMFnMessageAttribute, isArray=True)
							]
						),
						dict(name=consts.CRIT_GUIDE_MIRROR_ROTATION_ATTR, type=api.kMFnNumericBoolean),
						dict(name=consts.CRIT_GUIDE_AUTO_ALIGN_ATTR, type=api.kMFnNumericBoolean),
						dict(name=consts.CRIT_GUIDE_AIM_VECTOR_ATTR, type=api.kMFnNumeric3Float),
						dict(name=consts.CRIT_GUIDE_UP_VECTOR_ATTR, type=api.kMFnNumeric3Float),
					]),
				dict(name=consts.CRIT_GUIDE_VISIBILITY_ATTR, type=api.kMFnNumericBoolean, default=True, value=True),
				dict(name=consts.CRIT_GUIDE_CONTROL_VISIBILITY_ATTR, type=api.kMFnNumericBoolean, default=False, value=False),
				dict(name=consts.CRIT_GUIDE_PIN_SETTINGS_ATTR, type=api.kMFnCompoundAttribute, children=[
					dict(name=consts.CRIT_GUIDE_PIN_PINNED_ATTR, type=api.kMFnNumericBoolean),
					dict(name=consts.CRIT_GUIDE_PIN_PINNED_CONSTRAINTS_ATTR, type=api.kMFnDataString),
				]),
				dict(name=consts.CRIT_GUIDE_LIVE_LINK_NODES_ATTR, type=api.kMFnMessageAttribute, isArray=True),
				dict(name=consts.CRIT_GUIDE_IS_LIVE_LINK_ACTIVE_ATTR, type=api.kMFnNumericBoolean, default=False, value=False),
				dict(name=consts.CRIT_GUIDE_CONNECTORS_GROUP_ATTR, type=api.kMFnMessageAttribute),
				dict(name=consts.CRIT_GUIDE_DG_GRAPH_ATTR, type=api.kMFnCompoundAttribute, isArray=True, locked=False, children=[
						dict(name=consts.CRIT_GUIDE_DG_GRAPH_ID_ATTR, type=api.kMFnDataString),
						dict(name=consts.CRIT_GUIDE_DG_GRAPH_NAME_ATTR, type=api.kMFnDataString),
						dict(name=consts.CRIT_GUIDE_DG_GRAPH_METADATA_ATTR, type=api.kMFnDataString),
						dict(name=consts.CRIT_GUIDE_DG_GRAPH_INPUT_NODE_ATTR, type=api.kMFnMessageAttribute),
						dict(name=consts.CRIT_GUIDE_DG_GRAPH_OUTPUT_NODE_ATTR, type=api.kMFnMessageAttribute),
						dict(name=consts.CRIT_GUIDE_DG_GRAPH_NODES_ATTR, type=api.kMFnCompoundAttribute, isArray=True, children=[
								dict(name=consts.CRIT_GUIDE_DG_GRAPH_NODE_ID_ATTR, type=api.kMFnDataString),
								dict(name=consts.CRIT_GUIDE_DG_GRAPH_NODE_ATTR, type=api.kMFnMessageAttribute),
							]),
					]),
			)
		)

		return attrs

	@override(check_signature=False)
	def serializeFromScene(self):
		"""
		Serializes current layer into a dictionary compatible with JSON.

		:return: JSON compatible dictionary.
		:rtype: dict
		"""

		root = self.guide_root()
		dag = list()
		if root:
			dag.append(
				root.serializeFromScene(extra_attributes_only=True, include_namespace=False, use_short_names=True))

		setting_nodes = list()
		for setting_node in iter(self.iterate_settings_nodes()):
			setting_nodes.extend(setting_node.serializeFromScene())

		metadata = list()
		for attr_name in (
				consts.CRIT_GUIDE_VISIBILITY_ATTR,
				consts.CRIT_GUIDE_CONTROL_VISIBILITY_ATTR,
				consts.CRIT_GUIDE_PIN_PINNED_CONSTRAINTS_ATTR,
				consts.CRIT_GUIDE_PIN_PINNED_ATTR):
			metadata.append(self.attribute(attr_name).serializeFromScene())

		data = {
			consts.GUIDE_LAYER_DESCRIPTOR_KEY: {
				consts.DAG_DESCRIPTOR_KEY: dag,
				consts.SETTINGS_DESCRIPTOR_KEY: setting_nodes,
				consts.METADATA_DESCRIPTOR_KEY: metadata,
				consts.DG_DESCRIPTOR_KEY: list()
			}
		}

		return data

	@override
	def delete(self, mod: api.OpenMaya.MDGModifier | None = None, apply: bool = True) -> bool:
		"""
		Deletes the node from the scene.

		:param OpenMaya.MDGModifier mod: modifier to add the delete operation into.
		:param bool apply: whether to apply the modifier immediately.
		:return: True if the node deletion was successful; False otherwise.
		:raises RuntimeError: if deletion operation fails.
		:rtype: bool
		"""

		for guide in self.iterate_guides():
			guide.lock(False)

		return super().delete(mod=mod, apply=apply)

	def guide_root(self) -> meta_nodes.Guide:
		"""
		Returns the guide which contains the expected root attribute as True.

		:return: root guide.
		:rtype: meta_nodes.Guide or None
		"""

		if not self.exists() or not self.hasAttribute(consts.CRIT_GUIDES_ATTR):
			return None

		for element in self.iterate_guides_compound_attribute():
			is_root_flag = element.child(2)
			if not is_root_flag:
				continue
			source = element.child(0).sourceNode()
			if source is not None:
				return meta_nodes.Guide(source.object())

		return None

	def iterate_guides_compound_attribute(self) -> collections.Iterator[api.Plug]:
		"""
		Generator function that iterates over the attribute that links this layer meta node instance with the different
		guide nodes within current scene.

		:return: guide's compound attribute iterator.
		:rtype: collections.Iterator[api.Plug]
		"""

		guide_plug = self.attribute(consts.CRIT_GUIDES_ATTR)
		for i in range(guide_plug.evaluateNumElements()):
			yield guide_plug.elementByPhysicalIndex(i)

	def iterate_guides(self, include_root: bool = True) -> collections.Iterator[meta_nodes.Guide]:
		"""
		Generator function that iterates through the guides connected to this layer. The iteration is done based on the
		order the guides were added to the layer meta node instance.

		:param bool include_root: whether to include root guide.
		:return: generator of iterated guide instances.
		:rtype: collections.Iterator[meta_nodes.Guide]
		"""

		if not self.exists() or not self.hasAttribute(consts.CRIT_GUIDES_ATTR):
			return
		for element in self.iterate_guides_compound_attribute():
			guide_plug = element.child(0)
			source = guide_plug.sourceNode()
			if source is None:
				continue
			if not include_root and element.child(1).asString() == 'root':
				continue
			if meta_nodes.Guide.is_guide(source):
				yield meta_nodes.Guide(source.object())

	def guide(self, name: str) -> meta_nodes.Guide | None:
		"""
		Returns the guide node instance with given attached to this layer.

		:param str name: short name of the guide to retrieve.
		:return: found guide with given name.
		:rtype: meta_nodes.Guide or None
		"""

		if not self.exists():
			return None

		for found_guide in self.iterate_guides():
			if found_guide.id() == name:
				return found_guide

		return None

	def guide_count(self) -> int:
		"""
		Returns the total amount of guides attached to this layer.

		:return: total amount of guides.
		:rtype: int
		"""

		guide_plug = self.attribute(consts.CRIT_GUIDES_ATTR)
		return guide_plug.evaluateNumElements()

	def find_guides(self, *guide_ids: tuple) -> list[meta_nodes.Guide | None]:
		"""
		Searches and returns guides with given IDs.

		:param tuple[str] guide_ids: list of guide IDs to search for.
		:return: list of found guides.
		:rtype: list[meta_nodes.Guide | None]
		"""

		if not self.exists():
			return list()

		results = [None] * len(guide_ids)
		for found_guide in self.iterate_guides():
			guide_id = found_guide.id()
			if guide_id in guide_ids:
				results[guide_ids.index(guide_id)] = found_guide

		return results

	def are_guides_visible(self) -> bool:
		"""
		Returns whether guides within this layer instance are visible.

		:return: True if guides are visible; False otherwise.
		:rtype: bool
		"""

		return self.guideVisibiilty.value()

	def set_guides_visible(
			self, flag: bool, include_root: bool = True, mod: api.DGModifier | None = None,
			apply: bool = True) -> api.DGModifier:
		"""
		Sets whether guides are visible.

		:param bool flag: True to make guides visible; False otherwise.
		:param bool include_root: whether to include root guide.
		:param api.DGModifier mod: optional modifier to use to set guides visibility.
		:param bool apply: whether to apply changes immediately.
		:return: modifier used to set guides visibility.
		:rtype: api.DGModifier
		"""

		modifier = mod or api.DGModifier()
		connectors = self.connectors()
		for guide in self.iterate_guides(include_root=include_root):
			if guide.visibility.isLocked:
				continue
			guide.setVisible(flag, mod=modifier, apply=False)
		for connector in connectors:
			if connector.visibility.isLocked:
				continue
			connector.setVisible(flag, mod=modifier, apply=True)
		self.guideVisibility.set(flag, mod=modifier, apply=apply)
		if mod or apply:
			modifier.doIt()

		return modifier

	def are_guides_controls_visible(self) -> bool:
		"""
		Returns whether guide controls within this layer instance are visible.

		:return: True if guides controls are visible; False otherwise.
		:rtype: bool
		"""

		return self.guideControlVisibility.value()

	def set_guides_controls_visible(self, flag: bool, mod: api.DGModifier = None, apply: bool = True):
		"""
		Sets whether guides controls are visible.

		:param bool flag: True to make guides visible; False otherwise.
		:param api.DGModifier mod: optional modifier to use to set guides visibility.
		:param bool apply: whether to apply changes immediately.
		"""

		for guide in self.iterate_guides():
			shape = guide.shape_node()
			if shape is None:
				continue
			shape.setVisible(flag, mod=mod, apply=apply)
		self.guideControlVisibility.set(flag)

	def create_guide(self, **kwargs) -> meta_nodes.Guide:
		"""
		Creates a new guide node into current scene and attaches it the guide layer.

		:keyword str id: guide unique identifier relative to the guide layer instance.
		:keyword str name: guide's name.
		:keyword list(float) translate: translate X, Y, Z in world space.
		:keyword list(float) rotate: rotation X, Y, Z in world space.
		:keyword list(float) scale: scale X, Y, Z in world space.
		:keyword int rotateOrder: rotate order using tp.maya.api.attributetypes.kConstant value.
		:keyword str or dict shape: if str then the shape name will be used, otherwise serialized shape will be used.
		:keyword dict locShape: BaseLoc attributes to set.
		:keyword list(float) color: shape color to use.
		:keyword dict shapeTransform: shape pivot transform.
		:keyword dict shapeTransform: shape pivot transform.
		:keyword str or tp.maya.api.DagNode parent: optional guide parent.
		:keyword bool root: whether this guide is the root guide of the component.
		:keyword list(float) or api.Matrix worldMatrix: world matrix for the guide, which takes priority over the
			local transform.
		:keyword list(float) or api.Matrix matrix: local matrix for the guide.
		:keyword list(dict): list of SRTS transforms data to create.
		:keyword bool selectionChildHighlighting: whether to enable selection child highlighting feature.
		:keyword bool requiresPivotShape: sets whether pivot display is required.
		:keyword int pivotShape: index to set for the guide (0: ball; 1: pyramid; 2: pivot).
		:keyword list(float) pivotColor: guide pivot color.
		:keyword list(dict) attributes: list contaiing the extra attributes to create for the guide.
		:return:
		"""

		parent = kwargs.get('parent')
		parent = self.root_transform() if parent is None else self.guide(parent)
		kwargs['parent'] = parent

		new_guide = meta_nodes.Guide()
		new_guide.create(**kwargs)
		self.add_child_guide(new_guide)
		guide_plug = self.guide_plug_by_id(kwargs.get('id', ''))
		if guide_plug is None:
			return new_guide

		srt_plug = guide_plug.child(2)
		new_guide.set_shape_parent(self.root_transform())
		parent_node = new_guide.parent() or self.root_transform()
		srts = kwargs.get('srts', list())
		for srt in srts:
			if parent_node is not None:
				parent_node = parent_node.object()
			new_srt = api.DagNode(om_nodes.deserialize_node(srt, parent=parent_node)[0])
			parent_node = new_srt
			srt_element = srt_plug.nextAvailableDestElementPlug()
			new_srt.message.connect(srt_element)

		new_guide.setParent(parent_node, use_srt=False)

		return new_guide

	def add_child_guide(self, guide: meta_nodes.Guide):
		"""
		Attaches given guide node to this layer.

		:param meta_nodes.Guide guide: guide to attach to this layer.
		:raises ValueError: if given node is not a valid DagNode instance.
		"""

		if not isinstance(guide, api.DagNode):
			raise ValueError('Child node must be a DagNode instance')

		self._add_guide_to_meta(guide)

	def guide_plug_by_id(self, guide_id: str) -> api.Plug | None:
		"""
		Returns the guide node instance with given attached to this layer with given ID.

		:param str guide_id: guide's name.
		:return: found guide plug with given name attached to this layer.
		:rtype: api.Plug or None
		"""

		for element in self.iterate_guides_compound_attribute():
			id_plug = element.child(1)
			if id_plug.asString() == guide_id:
				return element

		return None

	def guide_node_by_id(self, guide_id: str) -> meta_nodes.Guide | None:
		"""
		Returns the guide node instance with given attached to this layer with given ID.

		:param str guide_id: guide's name.
		:return: found guide with given name attached to this layer.
		:rtype: meta_nodes.Guide or None
		"""

		guide_element_plug = self.guide_plug_by_id(guide_id)
		if not guide_element_plug:
			return None

		return guide_element_plug.child(0)

	def source_guide_by_id(self, guide_id: str, source_index: int) -> meta_nodes.Guide | None:
		"""
		Returns source guide from given ID.

		:param str guide_id: guide's name.
		:param source_index: source index.
		:return: meta_nodes.Guide or None
		"""

		guide_element_plug = self.guide_plug_by_id(guide_id)
		if not guide_element_plug:
			return None

		return guide_element_plug.child(4)[source_index]

	def duplicate_guide(self, guide: meta_nodes.Guide, name: str, guide_id: str, parent: meta_nodes.Guide | None):
		"""
		Duplicates given guide.

		:param meta_nodes.Guide guide: guide to duplicate.
		:param str name: name of the duplicated guide.
		:param guide_id: ID of the duplicated guide.
		:param meta_nodes.Guide or None parent: optional guide parent.
		:return: duplicated guide.
		:rtype: meta_nodes.Guide
		"""

		guide_data = guide.serializeFromScene()
		guide_data['parent'] = parent or guide
		guide_data['name'] = name
		guide_data['id'] = guide_id
		duplicated_guide = self.create_guide(**guide_data)

		return duplicated_guide

	@api.lock_node_context
	def delete_guides(self, *guide_ids: tuple):
		"""
		Deletes all guides from the layer.

		:param tuple[str] guide_ids: list of guide IDs to delete.
		"""

		if not self.exists() or not self.hasAttribute(consts.CRIT_GUIDES_ATTR):
			return

		for element in self.iterate_guides_compound_attribute():
			guide_plug = element.child(0)
			source = guide_plug.sourceNode()
			if source is None or not meta_nodes.Guide.is_guide(source):
				continue
			guide = meta_nodes.Guide(source.object())
			if guide_ids and guide.id() not in guide_ids:
				continue
			connectors = set()
			for destination in guide.message.destinations():
				if destination.partialName().startswith('critConn'):
					connectors.add(destination.node())
					break
			for connector in connectors:
				connector.delete()
			guide.delete()
			element.delete()

	def guide_settings(self) -> meta_nodes.SettingsNode:
		"""
		Returns guide settings node

		:return: guide settings node instance.
		:rtype: meta_nodes.SettingsNode
		"""

		return self.setting_node(consts.GUIDE_LAYER_TYPE)

	def is_pinned(self) -> bool:
		"""
		Returns whether guides attached to this layer are pinned.

		:return: True if guides are pinned; False otherwise.
		:rtype: bool
		"""

		return self.attribute(consts.CRIT_GUIDE_PIN_PINNED_ATTR).value() if self.exists() else False

	def align_guides(self):
		"""
		Aligns all guides attached to this layer instance.
		"""

		guides = list(self.iterate_guides(include_root=False))
		if not guides:
			return

		matrices = list()
		align_guides = list()
		new_transforms = dict()
		for guide in guides:
			aim_state = guide.attribute(consts.CRIT_AUTO_ALIGN_ATTR).asBool()
			if not aim_state:
				continue
			up_vector = guide.atribute(consts.CRIT_AUTO_ALIGN_UP_VECTOR_ATTR).value()
			aim_vector = guide.attribute(consts.CRIT_AUTO_ALIGN_AIM_VECTOR_ATTR).value()
			child = None																# type: meta_nodes.Guide or None
			for child in guide.iterate_child_guides(recursive=False):
				break
			if child is None:
				parent_guide, _ = guide.guide_parent()
				parent_matrix = new_transforms.get(parent_guide.id(), guide.worldMatrix())
				transform_matrix = api.TransformationMatrix(parent_matrix)
				transform_matrix.setTranslation(guide.translation(api.kWorldSpace), api.kWorldSpace)
				transform_matrix.setScale(guide.scale(api.kWorldSpace), api.kWorldSpace)
				matrix = transform_matrix.asMatrix()
			else:
				transform_matrix = guide.transformationMatrix()
				rotation = om_mathlib.look_at(
					guide.translation(), child.translation(), api.Vector(aim_vector), api.Vector(up_vector))
				transform_matrix.setRotation(rotation)
				matrix = transform_matrix.asMatrix()
			new_transforms[guide.id()] = matrix
			matrices.append(matrix)
			align_guides.append(guide)

		if align_guides and matrices:
			meta_nodes.Guide.set_guides_world_matrix(align_guides, matrices)

	def is_live_link(self) -> bool:
		"""
		Returns whether current layer is set to be linked to the live guiding system.

		:return: True if live link is enabled; False otherwise.
		:rtype: bool
		"""

		return self.attribute(consts.CRIT_GUIDE_IS_LIVE_LINK_ACTIVE_ATTR).asBool()

	def set_live_link(self, offset_node: meta_nodes.SettingsNode, state: bool = True):
		"""
		Live link the guides on the current guide layer to the given offset node.

		:param meta_nodes.SettingsNode offset_node: input guide offset node which contains the local matrices.
		:param flag state: if True, then the joints will be connected to the bindPreMatrix and the offset node matrices
			will be connected to the local transform of the joint.
		..info:: this system works by directly connecting the worldInverseMatrix plug to the skin clusters bindPreMatrix.
			By doing this, we allow all the joint transforms without effect the skin.
		"""

		current_state = self.is_live_link()
		if state == current_state:
			return

		metadata_attr = self.attribute(consts.CRIT_GUIDE_LIVE_LINK_NODES_ATTR)

		for source, dest in offset_node.iterateConnections(source=False, destination=True):
			if plugs.plug_type(dest) == api.attributetypes.kMFnDataMatrix:
				dest.disconnect(source)

		source_nodes_to_delete = list()
		for element in metadata_attr:
			source = element.sourceNode()
			if source is not None:
				source_nodes_to_delete.append(source.fullPathName())
		if source_nodes_to_delete:
			cmds.delete(source_nodes_to_delete)

		self.attribute(consts.CRIT_GUIDE_IS_LIVE_LINK_ACTIVE_ATTR).set(state)
		if not state:
			return

		transform_array = offset_node.attribute(consts.CRIT_GUIDE_OFFSET_TRANSFORMS_ATTR)
		transform_elements = {i.child(0).asString(): i for i in transform_array}
		for guide in self.iterate_guides():
			guide_transform_plug = transform_elements[guide.id()]
			local_matrix_plug = guide_transform_plug.child(1)
			world_matrix_plug = guide_transform_plug.child(2)
			parent_matrix_plug = guide_transform_plug.child(3)
			parent_guide, parent_id = guide.guide_parent()
			metadata_plug = metadata_attr.nextAvailableDestElementPlug()
			metadata_index = metadata_plug.logicalIndex()
			guide.attribute('worldMatrix')[0].connect(world_matrix_plug)
			if parent_id is None:
				local_matrix = guide.attribute('matrix')
			else:
				pick_mat_dest = parent_guide
				if parent_id == 'root':
					pick_mat_dest = parent_guide.srt()
				guide.attribute('parentMatrix')[0].connect(parent_matrix_plug)
				live_mult = api.factory.create_dg_node('_'.join([parent_guide.name(), 'liveGuideMult']), 'multMatrix')
				world_matrix = guide.attribute('worldMatrix')[0]
				world_inverse_matrix = pick_mat_dest.attribute('worldInverseMatrix')[0]
				pick_matrix = api.factory.create_dg_node('_'.join([parent_guide.name(), 'pickScale']), 'pickMatrix')
				pick_matrix.useTranslate = False
				pick_matrix.useRotate = False
				pick_matrix.useScale = False
				world_matrix.connect(live_mult.matrixIn[0])
				world_inverse_matrix.connect(live_mult.matrixIn[1])
				pick_matrix.outputMatrix.connect(live_mult.matrixIn[2])
				local_matrix = live_mult.matrixSum
				live_mult.message.connect(metadata_plug)
				pick_matrix.message.connect(metadata_attr[metadata_index + 1])
				pick_mat_dest.attribute('worldMatrix')[0].connect(pick_matrix.inputMatrix)

			local_matrix.connect(local_matrix_plug)

	def _add_guide_to_meta(self, guide: meta_nodes.Guide) -> api.Plug:
		"""
		Internal function that adds given guide into the meta node attributes.

		:param meta_nodes.Guide guide: guide to attach to this layer.
		:return: guide's compound plug.
		:rtype: api.Plug
		"""

		guides_compound_attribute = self.attribute(consts.CRIT_GUIDES_ATTR)
		is_locked_attribute = guides_compound_attribute.isLocked
		guides_compound_attribute.isLocked = False
		element = guides_compound_attribute.nextAvailableDestElementPlug()
		guide.message.connect(element.child(0))
		element.child(1).set(guide.id())
		shape_node = guide.shape_node()
		if shape_node is not None:
			shape_node.message.connect(element.child(3))
		element.child(5).setAsProxy(guide.attribute(consts.CRIT_MIRROR_ATTR))
		element.child(6).setAsProxy(guide.attribute(consts.CRIT_AUTO_ALIGN_ATTR))
		element.child(7).setAsProxy(guide.attribute(consts.CRIT_AUTO_ALIGN_AIM_VECTOR_ATTR))
		element.child(8).setAsProxy(guide.attribute(consts.CRIT_AUTO_ALIGN_UP_VECTOR_ATTR))
		guides_compound_attribute.isLocked = is_locked_attribute

		return guides_compound_attribute

	def _serialize_graphs(self):
		"""
		Internal function that serializes network nodes connected to this layer.

		:return: serialized nodes JSON compatible dictionaries.
		:rtype: list(dict)
		"""

		graphs = list()
		for graph_element in self.attribute(consts.CRIT_GUIDE_DG_GRAPH_ATTR):
			graph_id = graph_element.child(self.DG_GRAPH_ID_INDEX).value()
			node_data = list()
			for node_element in graph_element.child(self.DG_GRAPH_NODES_INDEX):
				node_id = node_element.child(self.DG_GRAPH_NODE_ID_INDEX).value()
				node = node_element.child(self.DG_GRAPH_NODE_INDEX).sourceNode()
				if node is None:
					continue
				data = node.serializeFromScene(include_connections=True)
				node_data.append({'id': node_id, 'data': data})
			graphs.append({'id': graph_id, 'nodes': node_data})

		return graphs


class CritOutputLayer(CritLayer):

	ID = consts.OUTPUT_LAYER_TYPE


class CritSkeletonLayer(CritLayer):

	ID = consts.SKELETON_LAYER_TYPE


class CritInputLayer(CritLayer):

	ID = consts.INPUT_LAYER_TYPE


class CritRigLayer(CritLayer):

	ID = consts.RIG_LAYER_TYPE


class CritXGroupLayer(CritLayer):

	ID = consts.XGROUP_LAYER_TYPE


class CritGeometryLayer(CritLayer):

	ID = consts.GEOMETRY_LAYER_TYPE
