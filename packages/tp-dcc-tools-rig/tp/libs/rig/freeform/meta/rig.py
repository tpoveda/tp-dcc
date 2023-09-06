from __future__ import annotations

from overrides import override

from tp.maya import api
from tp.maya.meta import base

from tp.libs.rig.freeform import consts
from tp.libs.rig.freeform.meta import character


class FreeformRig(base.DependentNode):

	ID = consts.RIG_TYPE
	DEPENDENT_NODE_CLASS = character.FreeformCharacter

	@override
	def meta_attributes(self) -> list[dict]:
		attrs = super().meta_attributes()

		attrs.extend(
			(
				dict(name=consts.ROOT_TRANSFORM_ATTR, type=api.kMFnMessageAttribute),
			)
		)

		return attrs

	@override(check_signature=False)
	def setup(self, character_group: api.DagNode):
		self.create_transform('Rigging_Components', parent=character_group)

	def root_transform(self) -> api.DagNode | None:
		"""
		Returns the root transform node for this component instance.

		:return: root transform instance.
		:rtype: api.DagNode or None
		"""

		return self.sourceNodeByName(consts.ROOT_TRANSFORM_ATTR)

	def create_transform(self, name: str, parent: api.DagNode | None = None) -> api.DagNode:
		"""
		Creates the transform node within Maya scene linked to this meta node.

		:param str name: name of the transform node.
		:param api.DagNode or None parent: optional parent node.
		:return: newly created transform node.
		:rtype: api.DagNode
		"""

		root_transform = api.factory.create_dag_node(name=name, node_type='transform', parent=parent)
		root_transform.setLockStateOnAttributes(consts.TRANSFORM_ATTRS)
		root_transform.showHideAttributes(('translate', 'rotate', 'scale'))
		self.connect_to(consts.ROOT_TRANSFORM_ATTR, root_transform)
		# root_transform.lock(True)

		return root_transform
