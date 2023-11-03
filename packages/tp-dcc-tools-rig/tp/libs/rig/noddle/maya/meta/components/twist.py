from __future__ import annotations

import enum
import typing

from overrides import override
import maya.cmds as cmds

from tp.core import log
from tp.maya import api
from tp.libs.rig.noddle.maya.meta import animcomponent
from tp.libs.rig.noddle.functions import attributes, naming, curves, joints

if typing.TYPE_CHECKING:
	from tp.libs.rig.noddle.maya.meta.components.character import Character

logger = log.rigLogger


class TwistComponent(animcomponent.AnimComponent):

	ID = 'noddleTwist'

	class Hooks(enum.Enum):
		START_JOINT = 0
		END_JOINT = 1

	@property
	def twist_start_object(self) -> api.DagNode:
		return self.sourceNodeByName('twistStartObject')

	@property
	def twist_end_object(self) -> api.DagNode:
		return self.sourceNodeByName('twistEndObject')

	@property
	def start_joint(self) -> api.Joint:
		return self.sourceNodeByName('startJoint')

	@property
	def end_joint(self) -> api.Joint:
		return self.sourceNodeByName('endJoint')

	@property
	def skeleton_start_joint(self) -> api.Joint:
		return self.sourceNodeByName('skelStartJoint')

	@property
	def skeleton_end_joint(self) -> api.Joint:
		return self.sourceNodeByName('skelEndJoint')

	@override
	def meta_attributes(self) -> list[dict]:

		attrs = super().meta_attributes()

		attrs.extend([
			dict(name='twistStartObject', type=api.kMFnMessageAttribute),
			dict(name='twistEndObject', type=api.kMFnMessageAttribute),
			dict(name='startJoint', type=api.kMFnMessageAttribute),
			dict(name='endJoint', type=api.kMFnMessageAttribute),
			dict(name='skelStartJoint', type=api.kMFnMessageAttribute),
			dict(name='skelEndJoint', type=api.kMFnMessageAttribute)
		])

		return attrs

	@override(check_signature=False)
	def setup(
			self, parent: animcomponent.AnimComponent | None = None, character: Character | None = None,
			side: str | None = None, component_name: str = 'twist', start_joint: api.Joint | None = None,
			end_joint: api.Joint | None = None, num_joints: int = 2, start_object: api.DagNode | None = None,
			end_object: api.DagNode | None = None, mirrored_chain: bool = False, add_hooks: bool = False,
			tag: str = ''):

		side = side or parent.side
		component_name = '_'.join([parent.indexed_name, component_name])

		super().setup(parent=parent, component_name=component_name, side=side, character=character, tag=tag)

		self.addAttribute('negativeX', type=api.kMFnNumericBoolean, default=mirrored_chain)

		end_joint = end_joint or list(start_joint.iterateChildren())[0]
		start_object = start_object or start_joint
		end_object = end_object or end_joint

		print('goggoogoggo', end_object)


		skeleton_start_joint = parent.bind_joints()[parent.control_joints().index(start_joint)]
		skeleton_end_joint = parent.bind_joints()[parent.control_joints().index(end_joint)]

		curve_points = [list(jnt.translation(api.kWorldSpace)) for jnt in [start_joint, end_joint]]
		ik_curve = curves.curve_from_points(
			name=naming.generate_name(self.indexed_name, side=self.side, suffix='crv'), degree=1,
			points=curve_points, parent=self.no_scale_group)
		cmds.rebuildCurve(ik_curve.fullPathName(), d=3, ch=False)

		control_chain = joints.create_along_curve(
			ik_curve, num_joints + 2, joint_name=self.component_name, joint_side=self.side, joint_suffix='jnt',
			delete_curve=False)
		attributes.add_meta_parent_attribute(control_chain)
		for jnt in control_chain:
			cmds.matchTransform(jnt.fullPathName(), start_joint.fullPathName(), rot=True)
			cmds.makeIdentity(jnt.fullPathName(), apply=True)

		joints.create_chain(control_chain)
		control_chain[0].setParent(self.joints_group)

		ik_handle = api.node_by_name(
			cmds.ikHandle(
				name=naming.generate_name(self.indexed_name, side=self.side, suffix='ikh'),
				startJoint=control_chain[0].fullPathName(), endEffector=control_chain[-1].fullPathName(),
				curve=ik_curve.fullPathName(), sol='ikSplineSolver', rootOnCurve=True, parentCurve=False,
				createCurve=False, simplifyCurve=False)[0])
		ik_handle.setParent(self.parts_group)

		curve_ik_joint = api.node_by_name(
			cmds.joint(n=naming.generate_name([self.indexed_name, 'ik'], side=self.side, suffix='jnt')))
		cmds.matchTransform(curve_ik_joint.fullPathName(), start_joint.fullPathName())
		curve_ik_joint.setParent(start_joint)

		cmds.skinCluster(
			[curve_ik_joint.fullPathName()], ik_curve.fullPathName(),
			n=naming.generate_name(self.indexed_name, side=self.side, suffix='skin'))

		start_locator = api.node_by_name(
			cmds.spaceLocator(n=naming.generate_name([self.indexed_name, 'start'], side=self.side, suffix='loc'))[0])
		end_locator = api.node_by_name(
			cmds.spaceLocator(n=naming.generate_name([self.indexed_name, 'end'], side=self.side, suffix='loc'))[0])
		cmds.matchTransform(start_locator.fullPathName(), control_chain[0].fullPathName())
		cmds.matchTransform(end_locator.fullPathName(), control_chain[-1].fullPathName())
		start_locator.setParent(start_object)
		end_locator.setParent(end_object)

		ik_handle.dTwistControlEnable.set(True)
		ik_handle.dWorldUpType.set(4)
		self.attribute('negativeX').connect(ik_handle.dForwardAxis)
		start_locator.attribute('worldMatrix')[0].connect(ik_handle.dWorldUpMatrix)
		end_locator.attribute('worldMatrix')[0].connect(ik_handle.dWorldUpMatrixEnd)

		output_joints = joints.duplicate_chain(
			new_joint_name=[self.indexed_name, 'out'], new_joint_side=self.side, start_joint=control_chain[1],
			end_joint=control_chain[-2], new_parent=self.joints_group)
		for control_jnt, out_jnt in zip(control_chain[1:-1], output_joints):
			_, parent_constraint_nodes = api.build_constraint(
				out_jnt,
				drivers={
					'targets': (
						(control_jnt.fullPathName(partial_name=True, include_namespace=False), control_jnt),
					)
				},
				constraint_type='parent'
			)

		if add_hooks:
			self.add_hook(control_chain[0], 'start_joint')
			self.add_hook(control_chain[-1], 'end_joint')

		self._connect_bind_joints(output_joints)
		self._connect_control_joints(control_chain)
		self.add_util_nodes([start_locator, end_locator, curve_ik_joint])

		start_joint.message.connect(self.attribute('startJoint'))
		end_joint.message.connect(self.attribute('endJoint'))
		start_object.message.connect(self.attribute('twistStartObject'))
		end_object.message.connect(self.attribute('twistEndObject'))
		skeleton_start_joint.message.connect(self.attribute('skelStartJoint'))
		skeleton_end_joint.message.connect(self.attribute('skelEndJoint'))

		self.connect_to_character(character_component=character, parent=True)
		self.attach_to_component(parent, hook_index=None)

		ik_curve.inheritsTransform.set(False)
		self.joints_group.setVisible(False)
		self.parts_group.setVisible(False)

	@override
	def attach_to_skeleton(self):
		logger.info(f'{self} Attaching to skeleton...')
		if not self.twist_start_object == self.start_joint:
			found_parent_constraints = []
			parent_component = list(self.iterate_meta_parents(recursive=False))[0]
			for _, destination_plug in parent_component.bind_joints()[0].iterateConnections(source=False):
				node = destination_plug.node()
				if node and node.apiType() == api.kParentConstraint:
					found_parent_constraints.append(node)
			if found_parent_constraints:
				for parent_constraint in found_parent_constraints:
					parent_constraint.delete()

		self.bind_joints()[0].setParent(self.skeleton_start_joint)
