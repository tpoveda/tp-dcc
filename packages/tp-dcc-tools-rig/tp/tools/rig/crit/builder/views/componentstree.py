from __future__ import annotations

import typing

from tp.common.qt import api as qt

from tp.tools.rig.crit.builder.widgets import treewidget

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.builder.models.rig import RigModel
	from tp.tools.rig.crit.builder.models.component import ComponentModel


class ComponentsTreeView(treewidget.TreeWidgetFrame):
	"""
	Main view to show components. Is composed by:
	ComponentsTreeView
		SearchBar
		ComponentTreeWidget
			List(TreeWidgetItem)
	"""

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(title='SETTINGS', parent=parent)

		self.setup_ui(ComponentsTreeWidget(parent=self))

	def apply_rig(self, rig_model: RigModel):
		"""
		Applies given rig model instance and fills tree widget.

		:param RigModel rig_model: rig model instance.
		"""

		self.setUpdatesEnabled(False)
		try:
			for component_model in rig_model.component_models:
				self.add_component(component_model)
			self._tree_widget.clearSelection()
		finally:
			self.setUpdatesEnabled(False)

	def add_component(self, component_model: ComponentModel, group=None):
		"""
		Adds given component model instance into the tree widget.

		:param ComponentModel component_model: component model instance.
		"""

		self._tree_widget.add_component(component_model, group=group)

	def sync(self):
		"""
		Syncs tree widget with the current model.
		"""

		self._tree_widget.sync()

	def clear(self):
		"""
		Clears out the tree widget.
		"""

		self._tree_widget.clear()


class ComponentsTreeWidget(qt.QTreeWidget):

	def sync(self):
		"""
		Synchronizes the contents of this tree widget based on the applied rig model.
		"""

		pass
