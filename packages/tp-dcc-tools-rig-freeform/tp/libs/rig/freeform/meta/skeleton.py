from __future__ import annotations

from typing import Iterator

from overrides import override

from tp.maya import api
from tp.maya.meta import base

from tp.libs.rig.freeform import consts
from tp.libs.rig.freeform.meta import character


class FreeformSkeleton(base.DependentNode):

	ID = consts.SKELETON_TYPE
	DEPENDENT_NODE_CLASS = character.FreeformCharacter


class FreeformJoints(base.DependentNode):

	ID = consts.JOINTS_TYPE
	DEPENDENT_NODE_CLASS = FreeformSkeleton

	@property
	def root_joint(self) -> api.Joint:
		return self.sourceNodeByName(consts.ROOT_JOINT_ATTR)

	@override
	def meta_attributes(self) -> list[dict]:
		attrs = super().meta_attributes()

		attrs.extend(
			(
				dict(name=consts.ROOT_JOINT_ATTR, type=api.kMFnMessageAttribute),
				dict(name=consts.JOINTS_ATTR, type=api.kMFnMessageAttribute, isArray=True)
			)
		)

		return attrs

	@override(check_signature=False)
	def setup(self, root: api.Joint):
		self.connect_to(consts.ROOT_JOINT_ATTR, root)

	def iterate_joint_plugs(self) -> Iterator[api.Plug]:
		"""
		Generator function that iterates over all joint plugs.

		:return: iterated joint plugs.
		:rtype: Iterator[api.Plug]
		"""

		for i in self.attribute(consts.JOINTS_ATTR):
			yield i

	def iterate_joints(self) -> Iterator[api.Joint]:
		"""
		Generator function that iterates over all connected joints.

		:return: iterated joints.
		:rtype: Iterator[api.Joint]
		"""

		for i in self.iterate_joint_plugs():
			source = i.sourceNode()
			if source:
				yield source

	def joints(self) -> list[api.Joint]:
		"""
		Returns all connected joints.

		:return: list of joints.
		:rtype: list[api.Joint]
		"""

		return list(self.iterate_joints())


class FreeformRegions(base.DependentNode):

	ID = consts.REGIONS_TYPE
	DEPENDENT_NODE_CLASS = character.FreeformCharacter

	@override
	def meta_attributes(self) -> list[dict]:
		attrs = super().meta_attributes()

		attrs.extend(
			(
				dict(name=consts.MARKUP_NODES_ATTR, type=api.kMFnMessageAttribute, isArray=True),
			)
		)

		return attrs

	def iterate_markup_nodes_plugs(self) -> Iterator[api.Plug]:
		"""
		Generator function that iterates over all markup nodes plugs.

		:return: iterated markup nodes plugs.
		:rtype: Iterator[api.Plug]
		"""

		for i in self.attribute(consts.MARKUP_NODES_ATTR):
			yield i

	def iterate_markup_nodes(self) -> Iterator[api.DGNode]:
		"""
		Generator function that iterates over all connected markup nodes.

		:return: iterated markup nodes.
		:rtype: Iterator[api.DGNode]
		"""

		for i in self.iterate_markup_nodes_plugs():
			source = i.sourceNode()
			if source:
				yield source

	def markup_nodes(self) -> list[api.DGNode]:
		"""
		Returns all connected markup nodes.

		:return: list of markup nodes.
		:rtype: list[api.DGNode]
		"""

		return list(self.iterate_markup_nodes())
