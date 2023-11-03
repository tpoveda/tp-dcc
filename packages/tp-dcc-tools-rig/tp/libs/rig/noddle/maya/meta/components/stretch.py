from __future__ import annotations

import typing

from overrides import override

from tp.core import log
from tp.maya import api
from tp.libs.rig.noddle.maya.meta import component, animcomponent
from tp.libs.rig.noddle.functions import nodes

if typing.TYPE_CHECKING:
	from tp.libs.rig.noddle.core.control import Control

logger = log.rigLogger


class IKSplineStretchComponent(component.Component):

	ID = 'noddleIkSplineStretch'

	@property
	def ik_curve(self) -> api.DagNode:
		try:
			return self.parent_component().sourceNodeByName('ikCurve')
		except AttributeError:
			logger.exception('Parent component with ikCurve attribute not found.')
			raise

	@override(check_signature=False)
	def setup(
			self, parent: animcomponent.AnimComponent, side: str | None = None, component_name: str = 'stretch',
			switch_control: Control | None = None, default_state: bool = False, switch_attr: str = 'stretch',
			stretch_axis: str = 'x', tag: str = 'stretch'):

		if not isinstance(parent, animcomponent.AnimComponent):
			logger.error(f'"{self}" must have AnimComponent instance as parent')
			raise TypeError

		side = side or parent.side
		full_name = '_'.join([parent.indexed_name, component_name])

		super().setup(parent=parent, component_name=full_name, side=side, tag=tag)

		self.add_meta_parent(parent)
		curve_info = nodes.create('curveInfo', [self.component_name, 'curve'], side=self.side, suffix='info')
		self.ik_curve.shapes()[0].attribute('worldSpace')[0].connect(curve_info.inputCurve)
		final_scale_mdv = nodes.create('multiplyDivide', [self.component_name, 'pure'], side=self.side, suffix='mdv')
		final_scale_mdv.operation.set(2)
		curve_info.arcLength.connect(final_scale_mdv.input1X)

		counter_scale_mdv = nodes.create('multiplyDivide', [self.component_name, 'scaled'], side=self.side, suffix='mdv')
		parent.character.root_control.attribute('Scale').connect(counter_scale_mdv.input1X)
		counter_scale_mdv.input2X.set(curve_info.arcLength.asFloat())
		counter_scale_mdv.outputX.connect(final_scale_mdv.input2X)

		if switch_control:
			switch_control.addAttribute(switch_attr, type=api.kMFnNumericBoolean, default=default_state, keyable=True)
			switch_choice = nodes.create('choice',  [self.component_name, 'switch'], side=self.side, suffix='mdl')
			switch_control.attribute(switch_attr).connect(switch_choice.selector)
			switch_choice.input[0].set(1.0)
			final_scale_mdv.outputX.connect(switch_choice.input[1])
			for jnt in parent.iterate_control_joints():
				switch_choice.output.connect(jnt.attribute(f's{stretch_axis}'))
		else:
			logger.warning(f'{self}: No control was used for state control')
