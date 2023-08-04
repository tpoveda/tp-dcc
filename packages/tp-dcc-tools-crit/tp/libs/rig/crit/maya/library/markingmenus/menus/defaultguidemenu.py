from __future__ import annotations

import typing
from typing import Tuple, List, Dict

from overrides import override

from tp.core import log
from tp.maya import api
from tp.maya.libs.triggers import markingmenu
from tp.libs.rig.crit import api as crit

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.component import Component
	from tp.libs.rig.crit.maya.core.rig import Rig

logger = log.rigLogger


class CritDefaultGuideMenu(markingmenu.MarkingMenuDynamic):

	ID = 'critDefaultGuideMenu'

	@override
	def execute(self, layout: markingmenu.MarkingMenuLayout, arguments: Dict) -> markingmenu.MarkingMenuLayout:

		components, rig = self._apply_crit_context_to_arguments(arguments)
		if components is None or rig is None:
			return layout

		generic = [
			{
				'type': 'command',
				'id': 'critDeleteComponent',
				'arguments': arguments
			}
		]

		layout['items'] = {'generic': generic}

		return layout

	def _apply_crit_context_to_arguments(self, arguments: Dict) -> Tuple[List[Component] | None, Rig | None]:
		"""
		Internal function that retrieves the component and rigs from marking menu arguments.

		:param Dict arguments: marking menu dictionaries.
		:return: tuple containing the found components and its rig.
		:rtype: Tuple[List[Component] or None, Rig or None]
		"""

		arguments['nodes'] = [i for i in arguments['nodes'] if i.hasFn(api.kNodeTypes.kDagNode)]
		try:
			components = crit.components_from_nodes(arguments['nodes'])
		except Exception:
			logger.error('Unhandled exception when initializing CRIT from scene nodes', exc_info=True)
			return None, None

		component_instances = list(components.keys())
		rig = None
		if component_instances:
			rig = component_instances[0].rig

		arguments.update({'rig': rig, 'components': component_instances, 'componentToNodes': components})

		return component_instances, rig
