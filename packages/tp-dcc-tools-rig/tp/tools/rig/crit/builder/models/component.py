from __future__ import annotations

import typing

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.component import Component
	from tp.tools.rig.crit.builder.models.rig import RigModel


class ComponentModel(qt.QObject):

	component_type = ''

	def __init__(self, component: Component | None = None, rig_model: RigModel | None = None):
		super().__init__()

		self._component = component
		self._rig_model = rig_model
		self._hidden = False

	@property
	def component(self) -> Component:
		return self._component

	@property
	def rig_model(self) -> RigModel:
		return self._rig_model

	@property
	def name(self) -> str:
		return self._component.name()

	@property
	def side(self) -> str:
		return self._component.side()
