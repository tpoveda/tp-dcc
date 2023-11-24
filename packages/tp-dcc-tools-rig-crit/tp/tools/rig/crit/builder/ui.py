from __future__ import annotations

import typing
from typing import List
from functools import partial

from overrides import override

from tp.core import log
from tp.preferences.interfaces import core
from tp.common.python import profiler
from tp.common.qt import api as qt
from tp.common.qt.widgets import frameless

from tp.libs.rig.crit import api as crit
from tp.tools.rig.crit.builder import interface, controller
from tp.tools.rig.crit.builder.managers import commands, editors
from tp.tools.rig.crit.builder.widgets import rigselector, loadingwidget
from tp.tools.rig.crit.builder.views import createview

if typing.TYPE_CHECKING:
	from tp.tools.rig.crit.builder.models.rig import RigModel
	from tp.tools.rig.crit.builder.models.component import ComponentModel

logger = log.rigLogger


class CritBuilderWindow(frameless.FramelessWindow):

	WINDOW_SETTINGS_PATH = 'tp/critbuilder'

	def __init__(self):

		self._ui_interface = interface.CritUiInterface.create()
		self._ui_interface.set_builder(self)
		self._crit_config = crit.Configuration()
		self._editors_manager = editors.EditorsManager()
		self._editors_manager.close_all_editors()
		self._components_manager = self._crit_config.components_manager()
		self._ui_commands_manager = commands.UiCommandsManager()
		self._controller = controller.CritBuilderController(
			components_manager=self._components_manager, editors_manager=self._editors_manager,
			ui_commands_manager=self._ui_commands_manager, ui_interface=self._ui_interface)
		self._controller.componentAdded.connect(self._on_component_added)
		self._theme_prefs = core.theme_preference_interface()

		self._rig_selector = None				# type: rigselector.RigSelector
		self._loading_widget = None				# type: loadingwidget.LoadingWidget
		self._create_view = None				# type: createview.CreateView

		super().__init__(name='CritBuilderWindow', title='CRIT Builder', width=580, height=600, save_window_pref=False)

		self._editors_manager.invoke_editor_by_id(
			'ComponentsLibrary', parent=self._main_window, create_view=self._create_view,
			components_manager=self._controller.components_manager,
			components_model_manager=self._controller.components_models_manager)

		self.refresh_ui()

	@property
	def controller(self) -> controller.CritBuilderController:
		return self._controller

	@override
	def setup_ui(self):
		super().setup_ui()

		main_layout = qt.horizontal_layout(spacing=0, margins=(0, 0, 0, 0))
		self.set_main_layout(main_layout)

		self._loading_widget = loadingwidget.LoadingWidget(parent=self.parent())

		self._rig_selector = rigselector.RigSelector(crit_builder=self)
		self.title_bar.title_layout.addSpacing(10)
		self.title_bar.title_layout.addWidget(self._rig_selector)
		self.title_bar.title_layout.addStretch()
		self.title_contents_layout.setContentsMargins(*qt.margins_dpi_scale(0, 2, 0, 2))
		self.title_bar.set_title_align(qt.Qt.AlignRight)

		self._main_stack = qt.sliding_opacity_stacked_widget(parent=self)
		main_layout.addWidget(self._main_stack)

		main_splitter = qt.QSplitter(parent=self)
		self._main_window = qt.QMainWindow(parent=self)
		main_window_widget = qt.QWidget(parent=self)
		self._main_window_layout = qt.vertical_layout()
		main_window_widget.setLayout(self._main_window_layout)
		self._main_window.setCentralWidget(main_window_widget)

		main_splitter.addWidget(self._main_window)
		self._outliners_widget = qt.QWidget(parent=self)
		self._outliners_widget.setLayout(qt.vertical_layout())
		self._menu_tab_widget = qt.LineTabWidget(alignment=qt.Qt.AlignLeft, parent=self)
		self._create_view = createview.CreateView(
			components_manager=self._components_manager, controller=self._controller, ui_interface=self._ui_interface,
			theme_prefs=self._theme_prefs, parent=self)
		self._menu_tab_widget.add_tab(self._create_view, {'text': 'Modules', 'image': 'puzzle', 'checked': True})
		self._outliners_widget.layout().addWidget(self._menu_tab_widget)

		self._main_window_layout.addWidget(self._outliners_widget)

		self._main_stack.addWidget(main_splitter)

		self._menubar = CritBuilderMenuBar(self._controller, self._create_view, parent=self._main_window)
		self._main_window.setMenuBar(self._menubar)

	@override
	def enterEvent(self, event: qt.QEvent) -> None:
		self.check_refresh()
		return super().enterEvent(event)

	@override
	def mousePressEvent(self, event: qt.QMouseEvent) -> None:
		qt.clear_focus_widgets()
		return super().mousePressEvent(event)

	@override
	def setup_signals(self):
		super().setup_signals()

		self._controller.rigAdded.connect(self._on_controller_rig_added)
		self._rig_selector.addRigClicked.connect(self._on_rig_selector_add_rig_clicked)
		self._rig_selector.renameClicked.connect(self._on_rig_selector_rename_rig_clicked)
		self._rig_selector.deleteRigClicked.connect(self._on_rig_selector_delete_rig_clicked)

	def check_refresh(self):
		"""
		Checks whether UI should be refreshed and refreshes it if necessary.
		"""

		if not self._controller.needs_refresh():
			return

		self.refresh_ui()

	@profiler.fn_timer
	def refresh_ui(self):
		"""
		Refreshes UI by clearing the current rig and querying for all scene rig and components.

		..warning:: refreshing the UI is an expensive process, so we should call this function sparingly.
		"""

		self._show_loading_widget()
		try:
			self._controller.refresh()
			rig_names = self._controller.rig_names()
			if not self._rig_selector:
				return
			current_text = self._rig_selector.update_list(rig_names, keep_same=True)
			if not current_text:
				self._rig_selector.set_current_index(0, update=False)
				current_text = self._rig_selector.current_text()
				self._create_view.clear_tree()
			rig_model = self._controller.rig_model_by_name(current_text)
			if rig_model is None:
				self._update_rig_mode()
				self._update_crit_settings()
				return

			self._controller.set_current_rig_container(rig_model)
			self._create_view.apply_rig(rig_model)
			self._create_view.update()
			self._update_crit_settings()
			self._update_rig_mode()
		finally:
			self._set_rig_polished_ui(False)
			self._hide_loading_widget()

	def soft_refresh_components(self, component_models: List[ComponentModel]):
		"""
		Cheap refresh function that updates the component widgets within components tree that matches given
		component models.

		:param List[ComponentModel] component_models: list of component models to refresh UI of.
		"""

		components_tree = self._ui_interface.components_tree()
		logger.debug(f'Soft refreshing components: "{component_models}"')

		for component_model in component_models:
			component_widget = components_tree.component_widget_by_model(component_model)
			if not component_widget:
				continue
			component_widget.refresh_ui()

	def set_rig(self, name: str, apply: bool = True):
		"""
		Sets the current CRIT Builder active rig.

		:param str name: name of the rig to set as active.
		:param whether apply: to set rig as active one.
		"""

		rig_model = self._controller.set_current_rig_container_by_name(name)
		if name and apply:
			self._create_view.apply_rig(rig_model)
			self._update_crit_settings()
			self._update_rig_mode()
			self._set_rig_polished_ui(False)

	def update_rig_name(self):
		"""
		Updates selected current rig within rig selector and emits controller rigRenamed signal.
		"""

		rig_names = self._controller.rig_names()
		self._rig_selector.update_list(rig_names, set_to=self._controller.current_rig_container.rig_model.rig.name())
		self._controller.rigRenamed.emit()

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

	def _update_crit_settings(self):
		"""
		Internal function that updates CRIT settings.
		"""

		pass

	def _set_rig_polished_ui(self, flag: bool):
		"""
		Internal function that sets whether rig UI is polished.

		:param bool flag: True if rig UI should be polished; False otherwise.
		"""

		pass

	def _update_rig_mode(self):
		"""
		Updates rig mode radio buttons.
		"""

		pass

	def _on_controller_rig_added(self):
		"""
		Internal callback function that is called each time a new rig is added through the controller.

		Updates the rig selector to select the new rig added and refreshes CRIT Builder UI.
		"""

		rig_names = self._controller.rig_names()
		rig_model = self._controller.current_rig_container.rig_model
		current_name = '' if not rig_model else rig_model.name
		self._rig_selector.update_list(rig_names, set_to=current_name)
		self.refresh_ui()

	def _on_rig_selector_add_rig_clicked(self) -> RigModel:
		"""
		Internal callback that is called each time user presses the Add Rig button within Rig Selector widget.
		Creates a new rig within current scene.

		:return: new added rig model.
		:rtype: RigModel
		"""

		rig_model = self.controller.add_rig(set_current=True)
		self._update_crit_settings()
		self._set_rig_polished_ui(False)

		return rig_model

	def _on_rig_selector_rename_rig_clicked(self):
		"""
		Internal callback function that is called each time user presses the Rename Rig button within Rig selector
		widget.
		Renames current active rig.
		"""

		self.controller.rename_rig()

	def _on_rig_selector_delete_rig_clicked(self) -> bool:
		"""
		Internal callabck function that is called each time user presses the Delete Rig button within Rig selector
		widget.
		Deletes current active rig.

		:return: True if the rename rig operation was successful; False otherwise.
		:rtype: bool
		"""

		rig_to_delete = self._rig_selector.current_text()
		if not rig_to_delete:
			return False

		result = qt.show_warning(
			title=f'Delete "{rig_to_delete}?', message=f'Are you sure you want to delete "{rig_to_delete}"?',
			icon='Warning', button_a='Yes', button_b='Cancel', parent=self)
		if result != 'A':
			return False

		rig_container_to_delete = self._controller.rig_container_by_name(rig_to_delete)
		if rig_container_to_delete != self._controller.current_rig_container:
			logger.warning('Is not possible to delete non active rig')
			return False

		try:
			self._show_loading_widget()
			self._controller.delete_rig(rig_container_to_delete)
			self.refresh_ui()
			self._update_crit_settings()
		finally:
			self._hide_loading_widget()

		return True

	def _on_component_added(self):
		"""
		Internal callback function that is called each time a new component is added through the controller.
		"""

		self._update_rig_mode()

		# TEMP
		self.refresh_ui()


class CritBuilderMenuBar(qt.QMenuBar):
	def __init__(
			self, controller: controller.CritBuilderController, create_view: createview.CreateView,
			parent: qt.QMainWindow | None = None):
		super().__init__(parent)

		self._parent = parent
		self._controller = controller
		self._create_view = create_view

		self._editors_menu = qt.get_or_create_menu(self, '&Editors')
		self.addMenu(self._editors_menu)
		editors_classes = self._controller.editors_manager.editors()
		for editor_class in editors_classes:
			show_editor_action = self._editors_menu.addAction(editor_class.NAME)
			show_editor_action.triggered.connect(partial(self._on_editor_menu_item_clicked, editor_class.ID))

	def _on_editor_menu_item_clicked(self, editor_id: str):
		"""
		Internal callback function that is called each time an editor action is clicked by the user.

		:param str editor_id: ID of the editor to open.
		"""

		kwargs = {}
		if editor_id == 'ComponentsLibrary':
			kwargs.update({
				'create_view': self._create_view,
				'components_manager': self._controller.components_manager,
				'components_model_manager': self._controller.components_models_manager})

		self._controller.editors_manager.invoke_editor_by_id(editor_id, parent=self._parent, **kwargs)
