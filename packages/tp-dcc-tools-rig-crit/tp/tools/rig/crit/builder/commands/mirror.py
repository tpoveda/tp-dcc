from __future__ import annotations

from typing import List, Dict

from tp.tools.rig.crit.builder.core import command


class MirrorComponentsUiCommand(command.CritUiCommand):

	ID = 'mirrorComponents'
	UI_DATA = {'icon': 'mirror', 'label': 'Mirror Selected Components'}

	_original_settings = dict(translate=('x',), rotate='yz', parent=None, side='r', duplicate=True)

	def execute(self, duplicate: bool = True, all_components: bool = False):
		"""
		Mirror current selected components.

		:param bool duplicate: whether to duplicate selected components and mirror those components instead.
		:param bool all_components: whether to mirror selected or all components.
		"""

		rig = self._rig_model.rig
		if all_components:
			components = rig.components()
		else:
			components = [component_model.component for component_model in self._selected_component_models]
		for component in components:
			arguments = dict(**self._original_settings)
			arguments['component'] = component
			arguments['duplicate'] = duplicate

		raise NotImplementedError

	def variants(self) -> List[Dict]:

		return [
			{'id': 'selected', 'name': 'Mirror Selected Components', 'icon': 'mirror', 'args': {}},
			{'id': 'all', 'name': 'Mirror All Components', 'icon': 'mirror', 'args': {'all_components': True}},
			{'id': 'duplicate', 'name': 'Mirror & Duplicate Selected Components', 'icon': 'mirror', 'args': {'duplicate': True}}
		]
