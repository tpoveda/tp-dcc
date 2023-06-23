from __future__ import annotations

import typing
from typing import List

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.builder.models.rig import RigModel
	from tp.tools.rig.crit.builder.models.component import ComponentModel


class SelectionModel:
	"""
	Model that holds current selected components within CRIT Builder UI.
	"""

	def __init__(self):
		self._rig_model = None						# type: RigModel
		self._component_models = []					# type: List[ComponentModel]

	@property
	def rig_model(self) -> RigModel:
		return self._rig_model

	@rig_model.setter
	def rig_model(self, value: RigModel):
		self._rig_model = value

	@property
	def component_models(self) -> List[ComponentModel]:
		return self._component_models

	@component_models.setter
	def component_models(self, value: List[ComponentModel]):
		self._component_models = value
