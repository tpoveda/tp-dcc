from __future__ import annotations

from overrides import override

import maya.cmds as cmds

from tp.core import log
from tp.libs.rig.crit import api as crit
from tp.tools.rig.crit.builder.core import command

logger = log.rigLogger


class HighlightFromSceneUiCommand(command.CritUiCommand):

	ID = 'highlightFromScene'
	UI_DATA = {'icon': 'cursor', 'label': 'Highlight From Scene'}

	@override(check_signature=False)
	def execute(self):
		"""

		"""

		scene_components = crit.components_from_selected()



class SelectInSceneUiCommand(command.CritUiCommand):

	ID = 'selectInScene'
	UI_DATA = {'icon': 'cursor', 'label': 'Select In Scene'}

	@override(check_signature=False)
	def execute(self):
		"""
		Select guide layer root node or all rig controls.
		"""

		components = [selected_component.component for selected_component in self.selected_components()]
		if not components:
			logger.warning('Must select component within UI')
			return

		select = []
		for component in components:
			if component.guide_layer():
				select.append(component.guide_layer().guide_root().fullPathName())
			elif component.rig_layer():
				select += [control.fullPathName() for control component.rig_layer().iterate_controls()]
		cmds.select(select)
