from __future__ import annotations

from functools import partial

from overrides import override

from tp.common.python import profiler
from tp.common.qt import api as qt
from tp.common.qt.widgets import frameless

from tp.libs.rig.crit import api as crit
from tp.tools.rig.crit.builder import interface, controller
from tp.tools.rig.crit.builder.managers import commands, editors
from tp.tools.rig.crit.builder.widgets import rigselector, loadingwidget
from tp.tools.rig.crit.builder.views import createview


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
		self._create_view = createview.CreateView(controller=self._controller, parent=self)
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

		self._rig_selector.addRigClicked.connect(self._on_rig_selector_add_rig_clicked)

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
				return

			self._controller.set_current_rig_container(rig_model)
			self._create_view.apply_rig(rig_model)
			self._create_view.update()
		finally:
			self._hide_loading_widget()

	def set_rig(self, name: str, apply: bool = True):
		"""
		Sets the current CRIT Builder active rig.

		:param str name: name of the rig to set as active.
		:param whether apply: to set rig as active one.
		"""

		rig_model = self._controller.set_current_rig_container_by_name(name)
		if name and apply:
			print('Setting rig ...')

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

	def _on_rig_selector_add_rig_clicked(self):
		"""
		Internal callback that is called each time user pressed the Add Rig button within Rig Selector widget.
		Creates a new rig within current scene.
		"""

		rig_model = self.controller.add_rig(set_current=True)
		print(rig_model)

	def _on_component_added(self):
		"""
		Internal callback function that is called each time a new component is added through the controller.
		"""

		self.update_rig_mode()


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
