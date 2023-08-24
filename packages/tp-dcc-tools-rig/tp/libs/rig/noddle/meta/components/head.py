from __future__ import annotations

import enum
import typing
from typing import List

from overrides import override

from tp.maya import api
from tp.libs.rig.noddle.meta import animcomponent
from tp.libs.rig.noddle.meta.components import fk
from tp.libs.rig.noddle.functions import transforms

if typing.TYPE_CHECKING:
	from tp.libs.rig.noddle.core.control import Control
	from tp.libs.rig.noddle.meta.components.character import Character


class HeadComponent(fk.FKComponent):

	ID = 'noddleHead'

	class Hooks(enum.Enum):
		HEAD = -1
		NECK_BASE = 0

	@property
	def head_control(self) -> Control:
		return self.controls()[-1]

	@property
	def neck_controls(self) -> List[Control]:
		return self.controls()[:-1]

	@override(check_signature=False)
	def setup(
			self, parent: animcomponent.AnimComponent | None = None, hook: int | None = None,
			character: Character | None = None, side: str = 'c', component_name: str = 'head',
			start_joint: str | None = None, end_joint: str | None = None, head_joint_index: int = -2,
			lock_translate: bool = False, tag: str = ''):

		super().setup(
			parent=parent, component_name=component_name, side=side, character=character, hook=hook,
			start_joint=start_joint, end_joint=end_joint, add_end_control=head_joint_index == -1,
			lock_translate=lock_translate, tag=tag)

		self.addAttribute('headJointIndex', type=api.kMFnNumericLong, keyable=False, default=head_joint_index, lock=True)

		control_chain = self.control_joints()
		head_control_move_vector = transforms.get_vector(control_chain[-2], control_chain[-1])
		self.head_control.set_shape('circle_pointed')
		scale_dict = {self.head_control: 0.4}
		self.scale_controls(scale_dict)
		self.head_control.rotate_shape((0, 0, 90))
		self.head_control.move_shapes(head_control_move_vector)
