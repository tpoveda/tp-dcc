from __future__ import annotations

import typing

from overrides import override

from tp.maya import api
from tp.libs.rig.noddle.core import control
from tp.libs.rig.noddle.meta import animcomponent
from tp.libs.rig.noddle.functions import attributes, joints

if typing.TYPE_CHECKING:
	from tp.libs.rig.noddle.core.hook import Hook
	from tp.libs.rig.noddle.meta.components.character import Character


class FKComponent(animcomponent.AnimComponent):

	ID = 'noddleFk'

	@override(check_signature=False)
	def setup(
			self, parent: animcomponent.AnimComponent | None = None, hook: int = 0, character: Character | None = None,
			side: str = 'c', component_name: str = 'fk_component', start_joint: str | None = None,
			end_joint: str | None = None, add_end_control: bool = True, lock_translate: bool = True, tag: str = ''):

		super().setup(parent=parent, component_name=component_name, side=side, character=character, tag=tag)

		joint_chain = joints.joint_chain(
			api.node_by_name(start_joint), end_joint=api.node_by_name(end_joint) if end_joint else None)
		joints.validate_rotations(joint_chain)
		attributes.add_meta_parent_attribute(joint_chain)
		control_chain = joints.duplicate_chain(
			new_joint_name=[self.indexed_name, 'fk', 'ctl'], new_joint_side=self.side, original_chain=joint_chain,
			new_parent=self.joints_group)

		fk_controls = []
		next_parent = self.controls_group
		skeleton_chain = control_chain if add_end_control else control_chain[:-1]
		free_attrs = 'r' if lock_translate else 'tr'
		for joint in skeleton_chain:
			fk_control = control.Control.create(
				name=f'{self.indexed_name}_fk', side=self.side, guide=joint, parent=next_parent,
				not_locked_attributes=free_attrs, shape='circle_crossed', tag='fk')
			_, parent_constraint_nodes = api.build_constraint(
				joint,
				drivers={
					'targets': ((fk_control.fullPathName(partial_name=True, include_namespace=False), fk_control),)},
				constraint_type='parent', maintainOffset=True
			)
			self.add_util_nodes(parent_constraint_nodes)
			next_parent = fk_control
			fk_controls.append(fk_control)

		self._connect_bind_joints(joint_chain)
		self._connect_control_joints(control_chain)
		self._connect_controls(fk_controls)

		for ctl in fk_controls:
			self.add_hook(ctl, 'fk')

		self.connect_to_character(character_component=character, parent=True)
		self.attach_to_component(parent, hook)

		scale_dict = {}
		for ctl in fk_controls:
			scale_dict[ctl] = 0.2
		self.scale_controls(scale_dict)

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
				self.controls()[0].group,
				drivers={
					'targets': ((in_hook.fullPathName(partial_name=True, include_namespace=False), in_hook),)},
				constraint_type='parent', maintainOffset=True
			)
			self.add_util_nodes(parent_constraint_nodes)

		return result
