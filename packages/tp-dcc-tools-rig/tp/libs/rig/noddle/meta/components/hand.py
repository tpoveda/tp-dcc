from __future__ import annotations

import typing
from typing import List, Dict, Iterator

from overrides import override
import maya.cmds as cmds

from tp.maya import api
from tp.maya.meta import base
from tp.libs.rig.noddle import consts
from tp.libs.rig.noddle.core import control
from tp.libs.rig.noddle.meta import animcomponent
from tp.libs.rig.noddle.meta.components import fk

if typing.TYPE_CHECKING:
	from tp.libs.rig.noddle.core.hook import Hook
	from tp.libs.rig.noddle.meta.components.character import Character


class HandComponent(animcomponent.AnimComponent):

	ID = 'noddleHand'

	@property
	def fingers(self) -> List[fk.FKComponent]:

		for finger_plug in self.attribute('fingers'):
			finger_node = finger_plug.sourceNode()
			if not finger_plug:
				continue
			yield base.MetaBase(node=finger_node.object())

	@override
	def meta_attributes(self) -> List[Dict]:

		attrs = super().meta_attributes()

		attrs.extend([
			dict(name='fingers', type=api.kMFnMessageAttribute, isArray=True, indexMatters=False),
		])

		return attrs

	@override(check_signature=False)
	def setup(
			self, parent: animcomponent.AnimComponent | None = None, character: Character | None = None,
			side: str | None = None, component_name: str = 'hand', hook: int | None = None, tag: str = 'body'):

		side = side or parent.side

		super().setup(parent=parent, side=side, component_name=component_name, character=character, tag=tag)

		self.connect_to_character(character_component=character, parent=True)
		self.attach_to_component(parent, hook)

	@override
	def iterate_controls(self) -> Iterator[control.Control]:
		for finger_plug in self.attribute('fingers'):
			finger_node = finger_plug.sourceNode()
			if not finger_node:
				continue
			for control_plug in finger_node.attribute('controls'):
				control_node = control_plug.sourceNode()
				if not control_node:
					continue
				yield control.Control(node=control_node.object())

	@override
	def attach_to_component(
			self, parent_component: animcomponent.AnimComponent, hook_index: int | None = None) -> Hook | None:

		result = super().attach_to_component(parent_component=parent_component, hook_index=hook_index)

		in_hook = self.in_hook()
		if in_hook:
			cmds.matchTransform(self.root_group.fullPathName(), in_hook.fullPathName())
			_, parent_constraint_nodes = api.build_constraint(
				self.controls_group,
				drivers={
					'targets': ((in_hook.fullPathName(partial_name=True, include_namespace=False), in_hook),)},
				constraint_type='parent'
			)
			self.add_util_nodes(parent_constraint_nodes)

		return result

	def add_fk_finger(
			self, start_joint: api.Joint, end_joint: api.Joint | None = None, name: str = 'finger',
			end_control: bool = False) -> fk.FKComponent:
		"""
		Adds a new finger FK component and attaches it to this hand component instance.

		:param api.Joint start_joint: start joint of the finger.
		:param api.Joint or None end_joint: end joint of the finger.
		:param str name: finger fk component name.
		:param bool end_control: whether to add an end fk control.
		:return: newly created finger FK component.
		:rtype: fk.FKComponent
		"""

		name = name if 'finger' in name else f'{name}_finger'
		fk_component = fk.FKComponent(
			component_name=name,
			side=self.side,
			start_joint=start_joint,
			end_joint=end_joint,
			add_end_control=end_control,
			lock_translate=False,
			hook=None,
			parent=self
		)
		fk_component.root_group.setParent(self.controls_group)
		fk_component.attribute(consts.MPARENT_ATTR_NAME).connect(
			self.attribute('fingers').nextAvailableDestElementPlug())
		fk_component.controls()[0].set_shape('pin')
		fk_component.controls()[0].scale_shapes(1.0, 0.5)
		for fk_ctrl in fk_component.controls()[1:]:
			fk_ctrl.set_shape('cube')
			fk_ctrl.scale_shapes(1.0, 2.0)

		return fk_component

	def five_finger_setup(
			self, thumb_start: api.Joint, index_start: api.Joint, middle_start: api.Joint, ring_start: api.Joint,
			pinky_start: api.Joint, thumb_end: api.Joint | None = None, index_end: api.Joint | None = None,
			middle_end: api.Joint | None = None, ring_end: api.Joint | None = None, pinky_end: api.Joint | None = None,
			tip_control: bool = False) -> List[fk.FKComponent]:
		"""
		Creates a five FK finger setup.

		:param api.Joint thumb_start:
		:param api.Joint index_start:
		:param api.Joint middle_start:
		:param api.Joint ring_start:
		:param api.Joint pinky_start:
		:param api.Joint or None thumb_end:
		:param api.Joint or None index_end:
		:param api.Joint or None middle_end:
		:param api.Joint or None ring_end:
		:param api.Joint or None pinky_end:
		:param bool tip_control:
		:return: list of created fk finger components.
		:rtype: List[fk.FKComponent]
		"""

		names = ['thumb', 'index', 'middle', 'ring', 'pinky']
		out_fingers = []
		for name, start_end_joints in zip(names, (
				(thumb_start, thumb_end),
				(index_start, index_end),
				(middle_start, middle_end),
				(ring_start, ring_end),
				(pinky_start, pinky_end))):
			out_fingers.append(self.add_fk_finger(
				start_end_joints[0], end_joint=start_end_joints[1], name=f'{name}_finger', end_control=tip_control))

		return out_fingers
