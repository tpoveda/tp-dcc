from __future__ import annotations

import typing

from tp.common.qt import api as qt

from tp.tools.rig.crit.builder.widgets import treewidget

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.builder.models.rig import RigModel
	from tp.tools.rig.crit.builder.models.component import ComponentModel
	from tp.tools.rig.crit.builder.controller import CritBuilderController


class ComponentsTreeView(treewidget.TreeWidgetFrame):
	"""
	Main view to show components. Is composed by:
	ComponentsTreeView
		SearchBar
		ComponentTreeWidget
			List(TreeWidgetItem)
	"""

	def __init__(self, controller: CritBuilderController | None = None, parent: qt.QWidget | None = None):
		super().__init__(title='SETTINGS', parent=parent)

		self.setup_ui(ComponentsTreeWidget(controller=controller, parent=self))

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
		:param group:
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


class ComponentsTreeWidget(qt.GroupedTreeWidget):

	class ComponentWidget(qt.QWidget):
		"""
		Stacked widget that represents a component within Components tree widget.
		"""

		syncRequested = qt.Signal()

		def __init__(
				self, component_model: ComponentModel, controller: CritBuilderController | None = None,
				parent: ComponentsTreeWidget | None = None):

			self._model = component_model
			self._tree = parent
			self._controller = controller

			super().__init__(parent=parent)

			main_layout = qt.horizontal_layout()
			self.setLayout(main_layout)
			main_layout.addWidget(qt.QPushButton('Hello World', parent=self))

		@property
		def model(self) -> ComponentModel:
			return self._model

		@property
		def component_type(self) -> str:
			return self._model.component_type

		@property
		def name(self) -> str:
			return self._model.name

	def __init__(self, controller: CritBuilderController | None = None, parent: qt.QWidget | None = None):

		self._controller = controller
		self._header_item = qt.QTreeWidgetItem(['Component'])

		super().__init__(allow_sub_groups=True, parent=parent)

	def sync(self):
		"""
		Synchronizes the contents of this tree widget based on the applied rig model.
		"""

		pass

	def add_component(
			self, component_model: ComponentModel,
			group: qt.GroupedTreeWidget.GroupWidget | None = None) -> ComponentsTreeWidget.ComponentWidget:
		"""
		Adds a component widget to this tree widget based on the given component model.

		:param ComponentModel component_model: component model instance.
		:param qt.GroupedTreeWidget.GroupWidget group: optional parent group widget.
		:return: newly created component widget instance.
		:rtype: ComponentsTreeWidget.ComponentWidget
		"""

		component_widget = ComponentsTreeWidget.ComponentWidget(
			component_model=component_model, controller=self._controller, parent=self)
		component_widget.syncRequested.connect(self.sync)
		self.add_component_widget(component_widget, group=group)

		if self.updatesEnabled():
			self.sync()

		return component_widget

	def add_component_widget(
			self, component_widget: ComponentsTreeWidget.ComponentWidget,
			group: qt.GroupedTreeWidget.GroupWidget | None = None):
		"""
		Adds given component widget into the tree widget.

		:param ComponentsTreeWidget.ComponentWidget component_widget: component widget instance.
		:param qt.GroupedTreeWidget.GroupWidget group: optional parent group widget.
		"""

		new_tree_item = self.add_new_item(
			component_widget.component_type, component_widget, widget_info=hash(component_widget.model),
			item_type=self.ITEM_TYPE_WIDGET)
		if group is not None:
			self.add_to_group(new_tree_item, group)
