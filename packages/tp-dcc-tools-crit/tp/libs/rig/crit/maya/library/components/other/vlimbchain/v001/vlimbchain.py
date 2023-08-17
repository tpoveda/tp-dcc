from __future__ import annotations

from tp.maya import api

from tp.libs.rig.crit.maya.core import component
from tp.libs.rig.crit.maya.library.functions import joints


class SpineComponent(component.Component):

	ID = 'spine'

	@classmethod
	def build(self, name='spine', side='c', rig=None, tag='body'):

		instance = super(SpineComponent, self).build(name=name, side=side, rig=rig, tag=tag)

		return instance


class FKIKSpineComponent(SpineComponent):

	ID = 'fkikspine'

	@classmethod
	def build(
			cls, name='spine', side='c', rig=None, hook=0, start_joint: str | None = None,
			end_joint: str = None, up_axis='y', forward_axis='x', tag='body'):
		instance = super().build(rig=rig, name=name, side=side, tag=tag)

		# make sure start and joints are converted to DagNode instance
		start_joint = api.node_by_name(start_joint) if start_joint else None
		end_joint = api.node_by_name(end_joint) if end_joint else None

		# add meta attributes
		instance.meta.addAttribute('fkControls', type=api.kMFnMessageAttribute, multi=True)
		instance.meta.addAttribute('midControl', type=api.kMFnMessageAttribute)
		instance.meta.addAttribute('ikCurve', type=api.kMFnMessageAttribute)

		# joint chains
		joint_chain = joints.joint_chain(start_joint, end_joint)
		joints.validate_rotations(joint_chain)
		ctl_chain = joints.duplicate_chain(
			new_joint_name=[instance.indexed_name(), 'ctl'], new_joint_side=instance.side(), original_chain=joint_chain)

		return instance
