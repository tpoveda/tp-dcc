from __future__ import annotations

from overrides import override

import maya.cmds as cmds

from tp.core import log
from tp.common.qt import api as qt
from tp.libs.rig.crit import api as crit
from tp.tools.rig.crit.builder.core import command
from tp.tools.rig.crit.builder.views import componentstree

logger = log.rigLogger


class HighlightFromSceneUiCommand(command.CritUiCommand):

	ID = 'highlightFromScene'
	UI_DATA = {'icon': 'cursor', 'label': 'Highlight From Scene'}

	@override(check_signature=False)
	def execute(self):
		"""
		Selects all components widget within components tree widget of the components that are selected in the scene.
		"""

		scene_components = crit.components_from_selected()
		components_tree = self._ui_interface.components_tree()
		components_tree.clearSelection()
		for i in range(components_tree.model().rowCount()):
			index = components_tree.model().index(i, 0)
			widget = components_tree.indexWidget(index)
			if isinstance(widget, components_tree.ComponentWidget) and widget.model.component in scene_components:
				components_tree.selectionModel().select(index, qt.QItemSelectionModel.SelectionFlag.Select)
				components_tree.scrollTo(index)


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
				select += [control.fullPathName() for control in component.rig_layer().iterate_controls()]
		cmds.select(select)


class MinimizeAllComponentsUiCommand(command.CritUiCommand):

	ID = 'minimizeAllComponents'
	UI_DATA = {'icon': 'shrink', 'label': 'Minimize All Components'}

	@override(check_signature=False)
	def execute(self):
		"""
		Minimizes all component widgets within components tree widget.
		"""

		self._ui_interface.components_tree().minimize_all()


class MaximizeAllComponentsUiCommand(command.CritUiCommand):

	ID = 'maximizeAllComponents'
	UI_DATA = {'icon': 'toggle_full_screen', 'label': 'Maximize All Components'}

	@override(check_signature=False)
	def execute(self):
		"""
		Maximizes all component widgets within components tree widget.
		"""

		self._ui_interface.components_tree().maximize_all()


class SelectAllComponentsUiCommand(command.CritUiCommand):

	ID = 'selectAllComponents'
	UI_DATA = {'icon': 'check_all', 'label': 'Select All Components'}

	@override(check_signature=False)
	def execute(self):
		"""
		Select all components widgets within components tree widget.
		"""

		self._ui_interface.components_tree().selectAll()


class InvertSelectedComponentsUiCommand(command.CritUiCommand):

	ID = 'invertSelectedComponents'
	UI_DATA = {'icon': 'invert_selection', 'label': 'Invert Selected Components'}

	@override(check_signature=False)
	def execute(self):
		"""
		Inverts selected components widgets within components tree widget.
		"""

		current_selection = self.selected_component_models
		components_tree = self._ui_interface.components_tree()
		components_tree.clearSelection()
		for i in range(components_tree.model().rowCount()):
			index = components_tree.model().index(i, 0)
			widget = components_tree.indexWidget(index)
			if isinstance(widget, componentstree.ComponentsTreeWidget.ComponentWidget) and widget.model not in current_selection:
				components_tree.selectionModel().select(index, qt.QItemSelectionModel.SelectionFlag.Select)
