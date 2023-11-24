from typing import Dict

from overrides import override

from tp.core import log
from tp.preferences.interfaces import core
from tp.common.python import profiler
from tp.common.qt import api as qt
from tp.common.resources import icon
from tp.common.resources import api as resources

from tp.libs.rig.crit import api as crit
from tp.tools.rig.crit.builder.widgets import loadingwidget
from tp.tools.rig.crit.componentseditor import controller
from tp.tools.rig.crit.componentseditor.widgets import creator, editor

logger = log.rigLogger


class ComponentsEditorWindow(qt.FramelessWindow):

	def __init__(self):

		self._crit_config = crit.Configuration()
		self._components_manager = self._crit_config.components_manager()
		self._naming_manager = self._crit_config.find_name_manager_for_type('component')
		self._controller = controller.CritComponentsEditorController(
			components_manager=self._components_manager, name_manager=self._naming_manager)
		self._theme_pref = core.theme_preference_interface()

		self._loading_widget = None  					# type: loadingwidget.LoadingWidget

		super().__init__(name='CritComponentsEditor', title='CRIT Components Editor')

		self.refresh_ui()

	def resizeEvent(self, event: qt.QResizeEvent) -> None:
		if self._loading_widget and self._loading_widget.isVisible():
			self._loading_widget.update()
		super().resizeEvent(event)

	def mousePressEvent(self, event: qt.QMouseEvent) -> None:
		qt.clear_focus_widgets()
		super().mousePressEvent(event)

	@override
	def setup_ui(self):
		super().setup_ui()

		self._loading_widget = loadingwidget.LoadingWidget(parent=self.parent())
		components_widget = qt.widget(layout=qt.vertical_layout(spacing=2, parent=self), parent=self)
		components_combo_layout = qt.horizontal_layout(spacing=2)
		self._components_combo = qt.combobox(parent=self)
		self._components_combo.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Preferred)
		self._add_component_button = qt.base_button(icon=resources.icon('add'), parent=self)
		self._refresh_components_button = qt.base_button(icon=resources.icon('refresh'), parent=self)
		components_combo_layout.addWidget(self._components_combo)
		components_combo_layout.addWidget(self._add_component_button)
		components_combo_layout.addWidget(self._refresh_components_button)
		self._components_creator = creator.ComponentsCreator(controller=self._controller, parent=self)
		self._components_editor = editor.ComponentsEditor(controller=self._controller, parent=self)
		self._components_stack = qt.sliding_opacity_stacked_widget(parent=self)
		empty_widget = qt.widget(layout=qt.horizontal_layout(spacing=0, margins=(0, 0, 0, 0)), parent=self)
		empty_label = qt.label('Select a Rig Component', parent=self)
		empty_label.theme_level = empty_label.Levels.H5
		empty_widget.layout().addStretch()
		empty_widget.layout().addWidget(empty_label)
		empty_widget.layout().addStretch()
		self._components_stack.addWidget(empty_widget)
		self._components_stack.addWidget(self._components_editor)
		components_widget.layout().addLayout(components_combo_layout)
		components_widget.layout().addWidget(qt.divider(parent=self))
		components_widget.layout().addWidget(self._components_stack)

		self._main_stack = qt.sliding_opacity_stacked_widget(parent=self)
		self._main_stack.addWidget(components_widget)
		self._main_stack.addWidget(self._components_creator)

		self.main_layout().addWidget(self._main_stack)

	@override
	def setup_signals(self):
		super().setup_signals()

		self._controller.availableComponentsChanged.connect(self._on_controller_available_components_changed)
		self._controller.newComponentAdded.connect(self._on_controller_new_component_added)
		self._controller.activeComponentChanged.connect(self._on_controller_active_component_changed)
		self._controller.startEditingComponent.connect(self._on_controller_start_editing_component)

		self._add_component_button.clicked.connect(self._on_add_component_button_clicked)
		self._components_combo.currentTextChanged.connect(self._on_components_combo_text_changed)
		self._components_creator.cancelled.connect(self._on_components_creator_cancelled)

	@profiler.fn_timer
	def refresh_ui(self):
		"""
		Refreshes components editor UI.
		"""

		self._show_loading_widget()
		try:
			self._controller.refresh()
		finally:
			self._hide_loading_widget()

	def _show_loading_widget(self):
		"""
		Internal function that shows the overlay loading widget.
		"""

		if not self._loading_widget:
			return

		self._loading_widget.show()
		qt.process_ui_events()

	def _hide_loading_widget(self):
		"""
		Internal function that hides the overlay loading widget.
		"""

		if not self._loading_widget:
			return

		self._loading_widget.hide()
		qt.process_ui_events()

	def _on_controller_available_components_changed(self, components_data: Dict[str, Dict]):
		"""
		Internal callback function that is called each time available components changes within controller.

		:param Dict[str, Dict] components_data: found components data.
		"""

		self._components_combo.clear()
		self._components_combo.addItem('Select Rig Component...')
		background_icon = resources.icon('rounded_square_filled')
		component_color = self._theme_pref.CRIT_COMPONENT_COLOR
		for component_name, component_data in components_data.items():
			component_icon = icon.colorize_layered_icon(
				[background_icon, resources.icon(component_data['icon'])], size=qt.dpi_scale(16),
				colors=[component_color], scaling=[1, 0.7])
			self._components_combo.addItem(component_icon, component_name, userData=component_data)

	def _on_controller_new_component_added(self):
		"""
		Internal callback function that is called each time a new component was added by the controller.
		"""

		self._main_stack.setCurrentIndex(0)

	def _on_controller_active_component_changed(self, component_name: str):
		"""
		Internal callback function that is called each time a rig component is edited.

		:param str component_name: name of the active component.
		"""

		with qt.block_signals(self._components_combo):
			if not component_name:
				self._components_combo.setCurrentIndex(0)
			else:
				self._components_combo.setCurrentText(component_name)

	def _on_controller_start_editing_component(self, success: bool):
		"""
		Internal callback function that is called each time a component is being edited by the controller.

		:param bool success: whether start editing component operation was successful.
		"""

		self._components_stack.setCurrentIndex(0 if not success else 1)
		if not success:
			with qt.block_signals(self._components_combo):
				self._components_combo.setCurrentIndex(0)
			return

	def _on_add_component_button_clicked(self):
		"""
		Internal callback function that is called each time Add Component button is clicked by the user.
		Loads components creator UI.
		"""

		self._main_stack.setCurrentIndex(1)

	def _on_components_creator_cancelled(self):
		"""
		Internal callback function that is called each time component creation operation is cancelled by the user.
		"""

		self._main_stack.setCurrentIndex(0)

	def _on_components_combo_text_changed(self, component_name: str):
		"""
		Internal callback function that is called each time a component combo box is selected by the user.

		:param str component_name: selected component name.
		"""

		current_index = self._components_combo.currentIndex()
		component_data = self._components_combo.currentData()
		if current_index <= 0 or not component_name or not component_data:
			self._components_stack.setCurrentIndex(0)
			return

		self._controller.active_component = component_name
