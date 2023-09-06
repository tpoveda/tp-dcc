from __future__ import annotations

from overrides import override

from tp.maya import api
from tp.maya.meta import base, metaproperty

from tp.libs.rig.freeform import consts
from tp.libs.rig.freeform.meta import character


class CommonProperty(metaproperty.MetaProperty):
	"""
	Base property class for any properties that can be added to anything.
	"""

	ID = 'freeformCommonProperty'

	@staticmethod
	@override
	def inherited_classes():
		return CommonProperty.__subclasses__()


class ExportProperty(CommonProperty):
	"""
	Property that marks whether and object should be exported.
	"""

	ID = 'freeformExportProperty'
	DEFAULT_NAME = 'export_property'

	@staticmethod
	@override
	def inherited_classes():
		return ExportProperty.__subclasses__()

	@override
	def meta_attributes(self) -> list[dict]:
		attrs = super().meta_attributes()

		attrs.extend(
			(
				dict(name=consts.EXPORT_ATTR, type=api.kMFnNumericBoolean),
			)
		)

		return attrs

	@override
	def act(self):
		return self.data()[consts.EXPORT_ATTR]


class JointProperty(metaproperty.MetaProperty):
	"""
	Property that marks a scene object as a joint.
	"""

	ID = 'freeformJointProperty'
	DEFAULT_NAME = 'joint_property'

	@staticmethod
	@override
	def inherited_classes():
		return JointProperty.__subclasses__()


class RegionMarkupProperty(JointProperty):
	"""
	Property that marks an object as part of a rigging region.
	Must always be made in pairs, one for the root and one for the end joint of the rigging region.
	"""

	ID = 'freeformRigMarkupProperty'
	DEFAULT_NAME = 'rig_markup_property'
	MULTI_ALLOWED = True

	@override
	def meta_attributes(self) -> list[dict]:
		attrs = super().meta_attributes()

		attrs.extend(
			(
				dict(name=consts.SIDE_ATTR, type=api.kMFnDataString),
				dict(name=consts.REGION_ATTR, type=api.kMFnDataString),
				dict(name=consts.TAG_ATTR, type=api.kMFnDataString),
				dict(name=consts.GROUP_ATTR, type=api.kMFnDataString),
				dict(name=consts.TEMPORARY_ATTR, type=api.kMFnNumericBoolean),
				dict(name=consts.LOCKED_LIST_ATTR, type=api.kMFnDataString),
				dict(name=consts.COM_WEIGHT_ATTR, type=api.kMFnNumericFloat),
				dict(name=consts.COM_REGION_ATTR, type=api.kMFnDataString),
				dict(name=consts.COM_OBJECT_ATTR, type=api.kMFnDataString),
			)
		)

		return attrs

	@override
	def on_add(self, node: api.DGNode):
		character_node = base.find_meta_node_from_node(node, character.FreeformCharacter)
		print('gogogogo', character_node)
