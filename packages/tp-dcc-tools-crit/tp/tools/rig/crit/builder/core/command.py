from __future__ import annotations

import sys
import typing
import traceback
from typing import List, Dict, Any

from tp.common.qt import api as qt
from tp.common import plugin
from tp.common.python import decorators

from tp.tools.rig.crit.builder import interface

if typing.TYPE_CHECKING:
	from logging import Logger
	from tp.tools.rig.crit.builder.models.rig import RigModel
	from tp.tools.rig.crit.builder.models.component import ComponentModel
	from tp.tools.rig.crit.builder.models.selection import SelectionModel


class CritUiCommand(qt.QObject):
	"""
	Class that implements custom CRIT Commands. Crit UI Commands are executed by CritBuilderController, which give
	them access to the different available rig and component models.
	"""

	ID = ''
	CREATOR = ''

	refreshRequested = qt.Signal(bool)

	def __init__(self, logger: Logger, ui_interface: interface.CritUiInterface):
		super().__init__()

		self._logger = logger
		self._crit_builder = ui_interface.builder()
		self._ui_interface = interface.CritUiInterface.instance()
		self._controller = self._ui_interface.controller()

		self._rig_model = None						# type: RigModel
		self._component_model = None				# type: ComponentModel
		self._selected_models = []					# type: List[ComponentModel]

	@property
	def rig_model(self) -> RigModel | None:
		return self._rig_model

	@rig_model.setter
	def rig_model(self, value: RigModel):
		self._rig_model = value

	@property
	def component_model(self) -> ComponentModel | None:
		return self._component_model

	@component_model.setter
	def component_model(self, value: ComponentModel):
		self._component_model = value

	@decorators.abstractmethod
	def execute(self, **args) -> Any:
		"""
		Executes UI command. This function MUST be overridden in subclasses and should never be called directly.
		Instead, call process function.

		:param Dict args: keyword arguments being used by the command.
		:return: command execution result.
		:rtype: Any
		"""

		pass

	def variants(self) -> List[Dict]:
		"""
		Returns list with all available command variants. e.g.:
			[
				{
					'id': 'selected',
					'name': Mirror Selected Components'
					'icon': 'mirror'
					'args': {}
				},
				{
					'id': 'all',
					'name': Mirror All Components'
					'icon': 'mirror'
					'args': {'all_components': True}
				},
				...
			]

		:return: list of command variants.
		:rtype: List[Dict]
		"""

		return []

	def process(self, variant_id: str | None = None, args: Dict | None = None) -> Any:
		"""
		Processes current command taking into account the varint command to execute.

		:param str variant_id: optional command variant to execute.
		:param Dict or None args: optional arguments to pass to the executed command.
		:return: command execution resulit.
		:rtype: Any
		..note:: A command can define multiple variants by implementing multiple sub-classes using the following ID
				format: {COMMAND_ID}.{VARIANT_ID}
		"""

		args = args or {}
		stat = plugin.PluginStats(self)
		exc_type, exc_value, exc_tb = None, None, None
		try:
			stat.start()
			self._logger.debug(f'Executing CRIT UI command: "{self.ID}"')
			variant = self.variant_by_id(variant_id)
			if variant_id:
				exec_args = variant['args']
				exec_args.update(args)
				return self.execute(**exec_args)
			return self.execute(**args)
		except Exception:
			exc_type, exc_value, exc_tb = sys.exc_info()
			stat.finish(traceback.format_exception(exc_type, exc_value, exc_tb))
			raise
		finally:
			if not exc_type:
				stat.finish(None)
			self._logger.debug(
				f'Finished executing CRIT UI Command: "{self.ID}", execution time: {stat.info["executionTime"]}')

	def variant_by_id(self, variant_id: str) -> Dict:
		"""
		Returns the command variant instance from given variant ID.

		:param str variant_id: CRIT Command UI variant ID.
		:return: found command variant with given ID.
		:rtype: Dict
		"""

		if not variant_id:
			return {}

		try:
			return [x for x in self.variants() if x['id'] == variant_id][0]
		except Exception:
			raise Exception(f'Variant with ID "{variant_id}" not found for CRIT Command UI "{self.ID}"')

	def set_selected(self, selection_model: SelectionModel):
		"""
		Sets the current selection model which stores references to the current selected rig and component models
		within CRIT Builder UI.

		:param SelectionModel selection_model: selection model instance.
		"""

		self._selected_models = selection_model.component_models
		self._rig_model = selection_model.rig_model

	def request_refresh(self, force: bool = False):
		"""
		Request a refresh in the UI.

		:param bool force: whether to force the refresh.
		"""

		self._logger.debug(f'CRIT UI Command: "{self.ID}" requested UI refresh!')
		self.refreshRequested.emit(force)

	def rig_exists(self) -> bool:
		"""
		Returns whether the internal rig model exists within current scene.

		:return: True if rig model exists within current scene; False otherwise.
		:rtype: bool
		"""

		return not self._rig_model or (self._rig_model and not self._rig_model.exists())

	def selected_components(self) -> List[ComponentModel]:
		"""
		Returns a list of component models based on selection and what is the target model:
			- Uses target model first. It will exclude selectedModels if not included in selectedModels.
			- If target model is in selectedModels, it includes all selectedModels.
			- If target model is none, it will use the last element in selectedModels

		:return: list of selected component models.
		:rtype: List[ComponentModel]
		"""

		component_models = []
		if self._component_model in self._selected_models:
			component_models = list(set(self._selected_models + [self._component_model]))
		else:
			if self._component_model is not None:
				component_models = [self._component_model]
			else:
				if self._selected_models:
					component_models = [self._selected_models[-1]]			# use lat selected if not target model

		return component_models
