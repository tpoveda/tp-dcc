from __future__ import annotations

from overrides import override

import maya.OpenMaya as OpenMaya

from tp.maya import api
from tp.maya.meta import base

from tp.libs.rig.crit import consts


class CritRig(base.MetaBase):

	ID = consts.RIG_TYPE

	def __init__(
			self, node: OpenMaya.MObject | None = None, name: str | None = None, init_defaults: bool = True,
			lock: bool = True, mod: OpenMaya.MDagModifier | None = None):
		super().__init__(node=node, name=name, init_defaults=init_defaults, lock=lock, mod=mod)

	@override
	def meta_attributes(self):
		attrs = super().meta_attributes()

		attrs.extend([
			dict(name=consts.CRIT_NAME_ATTR, type=api.kMFnDataString),
			dict(name=consts.CRIT_ID_ATTR, type=api.kMFnDataString),
			dict(name=consts.CRIT_IS_CRIT_ATTR, value=True, type=api.kMFnNumericBoolean),
			dict(name=consts.CRIT_IS_ROOT_ATTR, value=True, type=api.kMFnNumericBoolean),
			dict(name=consts.CRIT_ROOT_TRANSFORM_ATTR, type=api.kMFnMessageAttribute),
			dict(name=consts.CRIT_RIG_CONFIG_ATTR, type=api.kMFnDataString),
			dict(name=consts.CRIT_CONTROL_DISPLAY_LAYER_ATTR, type=api.kMFnMessageAttribute),
			dict(name=consts.CRIT_ROOT_SELECTION_SET_ATTR, type=api.kMFnMessageAttribute),
			dict(name=consts.CRIT_CONTROL_SELECTION_SET_ATTR, type=api.kMFnMessageAttribute),
			dict(name=consts.CRIT_SKELETON_SELECTION_SET_ATTR, type=api.kMFnMessageAttribute),
			dict(name=consts.CRIT_BUILD_SCRIPT_CONFIG_ATTR, type=api.kMFnDataString),
		])

		return attrs

	def root_transform(self) -> api.DagNode:
		"""
		Returns the root transform node for this rig instance.

		:return: root transform instance.
		:rtype: api.DagNode
		"""

		return self.sourceNodeByName(consts.CRIT_ROOT_TRANSFORM_ATTR)

	def create_transform(self, name: str, parent: api.DagNode | None = None) -> api.DagNode:
		"""
		Creates the transform node within Maya scene linked to this meta node.

		:param str name: name of the transform node.
		:param OpenMaya.DagNode or None parent: optional parent node.
		:return: newly created transform node.
		:rtype:
		"""

		layer_transform = api.factory.create_dag_node(name=name, node_type='transform', parent=parent)
		layer_transform.setLockStateOnAttributes(consts.TRANSFORM_ATTRS)
		layer_transform.showHideAttributes(consts.TRANSFORM_ATTRS)
		self.connect_to(consts.CRIT_ROOT_TRANSFORM_ATTR, layer_transform)

		return layer_transform

	def selection_sets(self) -> dict[str, api.DGNode]:
		"""
		Returns a list of all selection sets for this rig within current scene.

		:return: list of selection sets instances.
		:rtype:
		"""

		return {
			'ctrls': self.sourceNodeByName(consts.CRIT_CONTROL_SELECTION_SET_ATTR),
			'skeleton': self.sourceNodeByName(consts.CRIT_SKELETON_SELECTION_SET_ATTR),
			'root': self.sourceNodeByName(consts.CRIT_ROOT_SELECTION_SET_ATTR)
		}

	def create_selection_sets(self, name_manager: 'tp.common.naming.manager.NameManager') -> dict[str, api.DGNode]:
		"""
		Creates the selection sets for this rig instance.

		:param tp.common.naming.manager.NameManager name_manager: name manager instanced used to solve valid selection
			set names.
		:return: list of created selection sets.
		:rtype: list(DGNode)
		..note:: if the selection sets already exists within scene, they will not be created.
		"""

		existing_selection_sets = self.selection_sets()
		rig_name = self.attribute(consts.CRIT_NAME_ATTR).value()

		if existing_selection_sets.get('root', None) is None:
			name = name_manager.resolve('rootSelectionSet', {'rigName': rig_name, 'type': 'objectSet'})
			root = api.factory.create_dg_node(name, 'objectSet')
			self.connect_to(consts.CRIT_ROOT_SELECTION_SET_ATTR, root)
			existing_selection_sets['root'] = root
		if existing_selection_sets.get('ctrls', None) is None:
			name = name_manager.resolve(
				'selectionSet', {'rigName': rig_name, 'selectionSet': 'ctrls', 'type': 'objectSet'})
			object_set = api.factory.create_dg_node(name, 'objectSet')
			root.addMember(object_set)
			self.connect_to(consts.CRIT_CONTROL_SELECTION_SET_ATTR, object_set)
			existing_selection_sets['ctrls'] = object_set
		if existing_selection_sets.get('skeleton', None) is None:
			name = name_manager.resolve(
				'selectionSet', {'rigName': rig_name, 'selectionSet': 'skeleton', 'type': 'objectSet'})
			object_set = api.factory.create_dg_node(name, 'objectSet')
			root.addMember(object_set)
			self.connect_to(consts.CRIT_SKELETON_SELECTION_SET_ATTR, object_set)
			existing_selection_sets['skeleton'] = object_set

		return existing_selection_sets
