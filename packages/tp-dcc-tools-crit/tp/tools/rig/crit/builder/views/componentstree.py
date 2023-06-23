from __future__ import annotations

import typing

from overrides import override

from tp.core import log
from tp.common.qt import api as qt

from tp.tools.rig.crit.builder.widgets import treewidget

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.managers import ComponentsManager
	from tp.tools.rig.crit.builder.models.rig import RigModel
	from tp.tools.rig.crit.builder.models.component import ComponentModel
	from tp.tools.rig.crit.builder.controller import CritBuilderController
	from tp.tools.rig.crit.builder.managers.components import ComponentsModelManager

logger = log.rigLogger


class ComponentsTreeView(treewidget.TreeWidgetFrame):
	"""
	Main view to show components. Is composed by:
	ComponentsTreeView
		SearchBar
		ComponentTreeWidget
			List(TreeWidgetItem)
	"""

	def __init__(
			self,  components_manager: ComponentsManager | None = None,
			components_model_manager: ComponentsModelManager | None = None,
			controller: CritBuilderController | None = None,
			parent: qt.QWidget | None = None):
		super().__init__(title='SETTINGS', parent=parent)

		self._components_model_manager = components_model_manager
		self._controller = controller
		self._crit_builder = self._controller.crit_builder()

		self._highlight_button = qt.base_button(parent=parent)
		self._select_in_scene_button = qt.base_button(parent=parent)
		self._group_button = qt.base_button(parent=parent)
		self._menu_button = qt.base_button(parent=parent)

		self.setup_ui(ComponentsTreeWidget(
			components_manager=components_manager, components_model_manager=components_model_manager,
			controller=controller, parent=self))
		self.setup_signals()

	@override
	def setup_ui(self, tree_widget: qt.QTreeWidget):
		super().setup_ui(tree_widget=tree_widget)
		self.setContentsMargins(0, 0, 0, 0)

	@override
	def setup_toolbar(self) -> qt.QHBoxLayout:
		result = super().setup_toolbar()



		return result




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
			self.setUpdatesEnabled(True)

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

	class ComponentWidget(qt.StackItem):
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
			self._title_default_object_name = None

			super().__init__(
				title=component_model.name, icon=component_model.icon, collapsed=False,  start_hidden=False,
				shift_arrows_enabled=False, delete_button_enabled=True, item_icon_size=14, parent=parent)

		@property
		def model(self) -> ComponentModel:
			return self._model

		@property
		def component_type(self) -> str:
			return self._model.component_type

		@property
		def name(self) -> str:
			return self._model.name

		@override
		def setup_ui(self):
			super().setup_ui()

			self._title_default_object_name = self._title_frame.objectName()

		def sync(self):
			"""
			Synchronizes the contents of this widget based on the applied rig model.
			"""

			logger.debug('Syncing UI with the scene')
			self._widget_hide(self._model.is_hidden())
			# self._tree.update_selection_colors()
			# self._update_tool_icons()
			# if self._collapsed:
			# 	return
			# self._component_settings.update_ui()

		def _widget_hide(self, hide: bool):
			"""
			Internal function that handles the visual behaviour to show/hide the component widget.

			:param bool hide: whether to show/hide component widget.
			"""

			self._title_frame.setObjectName('diagonalBG' if hide else self._title_default_object_name)
			self._title_frame.setStyle(self._title_frame.style())

	def __init__(
			self, components_manager: ComponentsManager | None = None,
			components_model_manager: ComponentsModelManager | None = None,
			controller: CritBuilderController | None = None,
			parent: qt.QWidget | None = None):

		self._components_manager = components_manager
		self._components_model_manager = components_model_manager
		self._controller = controller
		self._header_item = qt.QTreeWidgetItem(['Component'])

		super().__init__(allow_sub_groups=True, parent=parent)

	def sync(self):
		"""
		Synchronizes the contents of this tree widget based on the applied rig model.
		"""

		for item in self.item_widgets(item_type=self.ITEM_TYPE_WIDGET):
			item.sync()

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

		component_widget.expand()

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
