from __future__ import annotations

import typing

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.component import Component
	from tp.tools.rig.crit.builder.models.rig import RigModel


class ComponentModel(qt.QObject):

	component_type = ''

	def __init__(self, component: Component, rig_model: RigModel | None = None):
		super().__init__()

		self._component = component
		self._rig_model = rig_model
		self._hidden = False
