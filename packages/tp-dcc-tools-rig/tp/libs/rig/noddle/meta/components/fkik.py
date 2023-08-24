from __future__ import annotations

import enum
import typing
from typing import List, Iterator, Dict

from overrides import override
import maya.cmds as cmds

from tp.maya import api
from tp.libs.rig.noddle import consts
from tp.libs.rig.noddle.core import control
from tp.libs.rig.noddle.meta import animcomponent
from tp.libs.rig.noddle.functions import attributes, naming, transforms, joints, nodes, rig

if typing.TYPE_CHECKING:
	from tp.libs.rig.noddle.core.hook import Hook
	from tp.libs.rig.noddle.meta.components.character import Character


class FKIKComponent(animcomponent.AnimComponent):

	ID = 'noddleFkIk'

	class Hooks(enum.Enum):
		START_JOINT = 0
		END_JOINT = 1

	@property
	def joints_offset_group(self) -> api.DagNode:
		return self.sourceNodeByName('jointOffsetGrp')

	@property
	def ik_control(self) -> control.Control:
		return control.Control(node=self.sourceNodeByName('ikControl').object())

	@property
	def pole_vector_control(self) -> control.Control:
		return control.Control(node=self.sourceNodeByName('poleVectorControl').object())

	@property
	def param_control(self) -> control.Control:
		return control.Control(node=self.sourceNodeByName('paramControl').object())

	@property
	def ik_handle(self) -> api.IkHandle:
		return self.sourceNodeByName('ikHandle')

	@override
	def meta_attributes(self) -> List[Dict]:

		attrs = super().meta_attributes()

		attrs.extend([
			dict(name='fkControls', type=api.kMFnMessageAttribute, isArray=True, indexMatters=False),
			dict(name='ikControl', type=api.kMFnMessageAttribute),
			dict(name='poleVectorControl', type=api.kMFnMessageAttribute),
			dict(name='paramControl', type=api.kMFnMessageAttribute),
			dict(name='matchingHelper', type=api.kMFnMessageAttribute),
			dict(name='jointOffsetGrp', type=api.kMFnMessageAttribute),
			dict(name='jointOffsetGrp', type=api.kMFnMessageAttribute),
			dict(name='ikHandle', type=api.kMFnMessageAttribute)
		])

		return attrs

	@override(check_signature=False)
	def setup(
			self, parent: animcomponent.AnimComponent | None = None, hook: int = 0, character: Character | None = None,
			side: str = 'c', component_name: str = 'fkik_component', start_joint: str | None = None,
			end_joint: str | None = None, ik_world_orient: bool = False, default_state: int = 1,
			param_locator: api.DagNode | None = None, tag: str = ''):

		super().setup(parent=parent, component_name=component_name, side=side, character=character, tag=tag)

		joint_chain = joints.joint_chain(api.node_by_name(start_joint), api.node_by_name(end_joint))
		joints.validate_rotations(joint_chain)
		attributes.add_meta_parent_attribute(joint_chain)
		control_chain = joints.duplicate_chain(
			new_joint_name=[self.indexed_name, 'ctl'], new_joint_side=self.side, original_chain=joint_chain,
			new_parent=self.joints_group)

		joint_offset_group = nodes.create(
			'transform', [self.indexed_name, 'constr'], self.side, suffix='grp', p=self.joints_group.fullPathName())
		attributes.add_meta_parent_attribute([joint_offset_group])
		cmds.matchTransform(joint_offset_group.fullPathName(), control_chain[0].fullPathName())
		control_chain[0].setParent(joint_offset_group)

		fk_controls = []
		next_parent = self.controls_group
		for control_joint in control_chain:
			fk_control = control.Control.create(
				name=f'{self.indexed_name}_fk', side=self.side, guide=control_joint, parent=next_parent,
				not_locked_attributes='r', shape='circle_crossed', tag='fk')
			next_parent = fk_control
			fk_controls.append(fk_control)

		for fk_control, control_joint in zip(fk_controls[:-1], control_chain):
			_, orient_constraint_nodes = api.build_constraint(
				control_joint,
				drivers={
					'targets': ((fk_control.fullPathName(partial_name=True, include_namespace=False), fk_control),)},
				constraint_type='orient'
			)
			self.add_util_nodes(orient_constraint_nodes)

		ik_control = control.Control.create(
			name=f'{self.indexed_name}_ik', side=self.side, guide=control_chain[-1], match_orient=not ik_world_orient,
			delete_guide=False, parent=self.controls_group, not_locked_attributes='tr', shape='cube', tag='ik')
		ik_handle = api.node_by_name(
			cmds.ikHandle(
				name=naming.generate_name(self.component_name, side=self.side, suffix='ikh'),
				startJoint=control_chain[0].fullPathName(), endEffector=control_chain[-1].fullPathName(),
				sol='ikRPsolver')[0])
		cmds.parent(ik_handle.fullPathName(), ik_control.fullPathName())
		attributes.add_meta_parent_attribute([ik_handle])

		matching_helper = api.factory.create_dag_node(
			naming.generate_name([self.indexed_name, 'matchingHelper'], side=self.side, suffix='grp'), 'transform')
		matching_helper.setParent(fk_controls[-1])
		attributes.add_meta_parent_attribute([matching_helper])

		pole_locator = joints.pole_vector_locator(control_chain)
		pole_vector_control = control.Control.create(
			name=f'{self.indexed_name}_pv', side=self.side, guide=pole_locator, delete_guide=True,
			parent=self.controls_group, not_locked_attributes='tr', shape='pole_vector', tag='poleVector')
		pole_vector_constraint = api.node_by_name(cmds.poleVectorConstraint(
			pole_vector_control.fullPathName(), ik_handle.fullPathName())[0])
		self.add_util_nodes([pole_vector_constraint])

		if len(control_chain) % 2:
			wire_source = control_chain[(len(control_chain) - 1) // 2]
		else:
			wire_source = control_chain[len(control_chain) // 2]
		pole_vector_control.add_wire(wire_source)

		param_control = control.Control.create(
			name=f'{self.indexed_name}_param', side=self.side, guide=control_chain[-1], match_orient=False,
			delete_guide=False, offset_group=False, parent=self.controls_group, not_locked_attributes='',
			shape='small_cog', orient_axis='y')
		_, parent_constraint_nodes = api.build_constraint(
			param_control.group,
			drivers={
				'targets': ((control_chain[-1].fullPathName(partial_name=True, include_namespace=False), control_chain[-1]),)},
			constraint_type='parent'
		)
		self.add_util_nodes(parent_constraint_nodes)

		param_control.addAttribute(
			'fkik', type=api.kMFnNumericFloat, niceName='FK/IK', min=0.0, max=1.0, default=default_state, keyable=True)

		reverse_fk_ik = api.factory.create_dg_node(
			name=naming.generate_name([self.indexed_name, 'fkik'], side=self.side, suffix='rev'), node_type='reverse')
		param_control.fkik.connect(reverse_fk_ik.inputX)
		param_control.fkik.connect(ik_control.group.visibility)
		param_control.fkik.connect(pole_vector_control.group.visibility)
		reverse_fk_ik.outputX.connect(fk_controls[0].group.visibility)
		param_control.fkik.connect(ik_handle.ikBlend)

		for ctrl in fk_controls + [ik_control, pole_vector_control]:
			ctrl.addProxyAttribute(param_control.fkik, 'FK/IK')

		ikfk_orient_offset = nodes.create(
			'transform', name=[self.indexed_name, 'ikfk_or'], side=self.side, suffix='grp')
		ikfk_orient_offset.setParent(fk_controls[-1])
		cns, last_orient_constraint_nodes = api.build_constraint(
			ikfk_orient_offset,
			drivers={
				'targets': ((fk_controls[-1].fullPathName(partial_name=True, include_namespace=False), fk_controls[-1]),)},
			constraint_type='orient', maintainOffset=True
		)
		self.add_util_nodes(last_orient_constraint_nodes)
		ikfk_orient_offset.setParent(ik_control)
		reverse_fk_ik.outputX.connect(cns.constraint_node.target[0].child(cns.CONSTRAINT_TARGET_INDEX))
		param_control.fkik.connect(cns.constraint_node.target[1].child(cns.CONSTRAINT_TARGET_INDEX))

		self._connect_bind_joints(joint_chain)
		self._connect_control_joints(control_chain)
		self._connect_controls(fk_controls + [ik_control, pole_vector_control, param_control])
		self._connect_settings([param_control.attribute('fkik')])

		for fk_ctrl in fk_controls:
			fk_ctrl.attribute(consts.MPARENT_ATTR_NAME).connect(
				self.attribute('fkControls').nextAvailableDestElementPlug())
		ik_control.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('ikControl'))
		matching_helper.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('matchingHelper'))
		joint_offset_group.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('jointOffsetGrp'))
		ik_handle.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('ikHandle'))
		pole_vector_control.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('poleVectorControl'))
		param_control.attribute(consts.MPARENT_ATTR_NAME).connect(self.attribute('paramControl'))

		self.add_hook(control_chain[0], 'start_joint')
		self.add_hook(control_chain[-1], 'end_joint')

		self.connect_to_character(character_component=character, parent=True)
		self.attach_to_component(parent, hook)

		scale_dict = {
			ik_control: 0.1,
			pole_vector_control: 0.1,
			param_control: 0.05
		}
		for fk_ctrl in fk_controls:
			scale_dict[fk_ctrl] = 0.2
		self.scale_controls(scale_dict)

		param_locator = param_locator or rig.param_control_locator(
			side=self.side, anchor_transform=joint_chain[-1], move_axis='y')
		param_move_vector = transforms.get_vector(param_control, param_locator)
		param_control.move_shapes(param_move_vector)
		param_locator.delete()

		ik_handle.setVisible(False)
		if self.character:
			self.parts_group.setVisible(False)
			self.joints_group.setVisible(False)

	@override
	def attach_to_component(
			self, parent_component: animcomponent.AnimComponent, hook_index: int | None = None) -> Hook | None:
		result = super().attach_to_component(parent_component=parent_component, hook_index=hook_index)

		in_hook = self.in_hook()
		if in_hook:
			_, parent_constraint_nodes = api.build_constraint(
				self.joints_offset_group,
				drivers={
					'targets': ((in_hook.fullPathName(partial_name=True, include_namespace=False), in_hook),)},
				constraint_type='parent', maintainOffset=True
			)
			self.add_util_nodes(parent_constraint_nodes)
			_, parent_constraint_nodes = api.build_constraint(
				self.fk_controls()[0].group,
				drivers={
					'targets': ((in_hook.fullPathName(partial_name=True, include_namespace=False), in_hook),)},
				constraint_type='parent', maintainOffset=True
			)
			self.add_util_nodes(parent_constraint_nodes)

		return result

	def iterate_fk_controls(self) -> Iterator[control.Control]:
		"""
		Generator function that iterates over all fk controls of this component.

		:return: iterated fk controls.
		:rtype: Iterator[control.Control]
		"""

		for control_plug in self.attribute('fkControls'):
			control_node = control_plug.sourceNode()
			if not control_node:
				continue
			yield control.Control(node=control_node.object())

	def fk_controls(self) -> List[control.Control]:
		"""
		Returns all fk controls of this component.

		:return: fk controls.
		:rtype: List[control.Control]
		"""

		return list(self.iterate_fk_controls())
