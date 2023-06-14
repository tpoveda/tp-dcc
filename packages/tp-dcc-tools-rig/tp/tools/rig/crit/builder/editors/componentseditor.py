from __future__ import annotations

import typing

from overrides import override

from tp.common.qt import api as qt
from tp.common.qt.widgets import groupedtreewidget

from tp.tools.rig.crit.builder.views import editor
from tp.tools.rig.crit.builder.widgets import treewidget

if typing.TYPE_CHECKING:
	from tp.libs.rig.crit.maya.core.managers import ComponentsManager
	from tp.tools.rig.crit.builder.managers.components import ComponentsModelManager


class ComponentsLibraryEditor(editor.EditorView):

	ID = 'ComponentsLibrary'
	NAME = 'Rig Components Library'
	TOOLTIP = 'Allows to add new rig components into a CRIT rig'
	DEFAULT_DOCK_AREA = qt.Qt.RightDockWidgetArea
	IS_SINGLETON = True

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent)

		self._components_manager = None						# type: ComponentsManager
		self._components_model_manager = None				# type: ComponentsModelManager
		self._components_library_widget = None				# type: ComponentsLibraryWidget

	@override(check_signature=False)
	def show(
			self, components_manager: ComponentsManager | None = None,
			components_model_manager: ComponentsModelManager | None = None) -> None:

		self._components_manager = components_manager
		self._components_model_manager = components_model_manager

		if not self._components_library_widget:
			self._components_library_widget = ComponentsLibraryWidget(
				components_manager=components_manager, components_model_manager=components_model_manager, parent=self)


class ComponentsLibraryWidget(treewidget.TreeWidgetFrame):
	"""
	Component Library tree widget that shows the list of component current available for the user.
	When an element of the tree is clicked, a new component is created and added to the components tree view.
	"""

	def __init__(
			self, components_manager: ComponentsManager | None = None,
			components_model_manager: ComponentsModelManager | None = None, locked: bool = False,
			parent: qt.QWidget | None = None):
		super().__init__(title='COMPONENTS', parent=parent)

		components_tree_widget = ComponentsLibraryTreeWidget(components_manager, components_model_manager, locked, parent)
		# components_tree_widget.set_drag_drop_enabled(False)

		self.setup_ui(components_tree_widget)


class ComponentsLibraryTreeWidget(groupedtreewidget.GroupedTreeWidget):
	"""
	Custom tree widget that contains the list of components that we can add to the rig.
	"""

	def __init__(
			self, components_manager: ComponentsManager | None = None,
			components_model_manager: ComponentsModelManager | None = None, locked: bool = False,
			parent: qt.QWidget | None = None):

		self._components_manager = components_manager
		self._components_model_manager = components_model_manager

		super().__init__(locked=locked, parent=parent)

		self.setRootIsDecorated(True)

	@override
	def _setup_ui(self):

		self.setSortingEnabled(False)

		super()._setup_ui()

		components = []
		for n, d in self._components_manager.components.items():
			print('component found ...', n, d)

