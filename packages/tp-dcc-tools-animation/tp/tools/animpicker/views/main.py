from __future__ import annotations

import typing
from functools import partial

from overrides import override

from tp.core import dcc
from tp.common.qt import api as qt
from tp.tools.animpicker import consts, utils, uiutils
from tp.tools.animpicker.views import editor
from tp.tools.animpicker.widgets import buttons

if dcc.is_maya():
	from tp.tools.animpicker.maya import editor as maya_editor

if typing.TYPE_CHECKING:
	from tp.tools.animpicker.controller import AnimPickerController
	from tp.tools.animpicker.events import PreCreateMapEvent, CreateMapEvent


class AnimPickerView(qt.FramelessWindow):

	WINDOW_SETTINGS_PATH = 'tp/animpicker'
	VERSION = '0.0.1'

	def __init__(
			self, controller: AnimPickerController,
			parent: qt.QWidget | None = None):

		self._controller = controller

		self._working_size = qt.QSize(400, 400)
		self._bottom_menu_visible = True
		self._map_mode = True
		self._clipboard = []

		super().__init__(title=f'Animation Picker {self.VERSION}', width=600, height=700, overlay=False, parent=parent)

	@override
	def setup_ui(self):
		super().setup_ui()

		self.setMinimumSize(qt.QSize(120, 120))

		self.set_main_layout(qt.vertical_layout(margins=(0, 0, 0, 0)))
		main_layout = self.main_layout()

		self._stack_widget = qt.sliding_opacity_stacked_widget(parent=self)
		main_layout.addWidget(self._stack_widget)

		self._setup_main_widget()
		self._setup_cretion_widget()

		qt.QTimer.singleShot(1, partial(self.refresh))

	@override
	def setup_signals(self):
		super().setup_signals()

		self._controller.warning.connect(self._on_warning)
		self._group_name_line.textChanged.connect(self._controller.updater('group_name'))
		self._controller.listen('group_name', self._group_name_line.setText, value=consts.DEFAULT_GROUP_NAME)
		self._map_name_line.textChanged.connect(self._controller.updater('map_name'))
		self._controller.listen('map_name', self._group_name_line.setText, value=consts.DEFAULT_MAP_NAME)
		self._map_width_spinbox.valueChanged.connect(self._controller.updater('map_width'))
		self._controller.listen('map_width', self._map_width_spinbox.setValue, value=consts.DEFAULT_MAP_WIDTH)
		self._map_height_spinbox.valueChanged.connect(self._controller.updater('map_height'))
		self._controller.listen('map_height', self._map_height_spinbox.setValue, value=consts.DEFAULT_MAP_HEIGHT)
		self._background_image_line.textChanged.connect(self._controller.updater('image_path'))
		self._controller.listen('image_path', self._background_image_line.setText, value='')

		self._controller.preCreateMap.connect(self._on_pre_create_map_event)
		self._controller.createMap.connect(self._on_create_map_event)

		self._create_new_map_button.clicked.connect(self._on_create_new_map_button_clicked)
		self._import_map_file_button.clicked.connect(self._on_import_map_file_button_clicked)
		self._edit_current_map_button.clicked.connect(self._on_edit_current_map_button_clicked)
		self._export_map_file_button.clicked.connect(self._on_export_map_file_button_clicked)

	def refresh(self, *args):
		"""
		Refreshes UI.
		"""

		self._determine_page()

	def _setup_cretion_widget(self):
		"""
		Internal function that creates init widget.
		"""

		self._init_widget = qt.widget(layout=qt.vertical_layout(spacing=2, margins=(2, 2, 2, 2)))

		top_horizontal_layout = qt.horizontal_layout(spacing=6)
		self._info_button = qt.tool_button(icon='help', tooltip='Open the link for documentation.', parent=self)
		self._info_button.setAutoRaise(True)
		self._info_label = qt.label('To view help, hover the mouse over', parent=self)
		self._info_label.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Preferred)
		font = self._info_label.font()
		font.setItalic(True)
		self._info_label.setFont(font)
		self._info_label.setAlignment(qt.Qt.AlignCenter)
		top_horizontal_layout.addWidget(self._info_button)
		top_horizontal_layout.addWidget(self._info_label)

		self._type_label = qt.label('---- CREATE NEW MAP ----', parent=self).strong()
		self._type_label.setAlignment(qt.Qt.AlignCenter)
		self._type_label.setMinimumSize(qt.QSize(0, 40))
		self._type_label.setMaximumHeight(40)
		self._type_label.setStyleSheet('background-color: #111;')

		self._name_widget = qt.widget(layout=qt.grid_layout(), parent=self)
		self._name_widget.setToolTip(
			'To create a new map,\n1. Type in a group name in the 1st field,\n2. Type in a map name in the 2nd field, '
			'such as "Body" or "Facial".')
		self._group_name_line = qt.line_edit(parent=self)
		self._map_name_line = qt.line_edit(parent=self)
		self._name_widget.layout().addWidget(qt.label('Group Name:', parent=self), 0, 0, qt.Qt.AlignRight)
		self._name_widget.layout().addWidget(self._group_name_line, 0, 1)
		self._name_widget.layout().addWidget(qt.label('Map Name:', parent=self), 1, 0, qt.Qt.AlignRight)
		self._name_widget.layout().addWidget(self._map_name_line, 1, 1)

		self._background_options_widget = qt.widget(layout=qt.horizontal_layout(), parent=self)
		self._background_options_widget.setToolTip(
			'Select a button to set image or color only to background.\nTo use a background image,\n1. Check on '
			'"Use BG image",\n2. To select an image file, click on icon or type the path in.')
		self._use_background_image_radio = qt.QRadioButton('Use BG image', parent=self)
		self._use_background_color_only_radio = qt.QRadioButton('BG color only', parent=self)
		self._background_options_widget.layout().addWidget(self._use_background_image_radio)
		self._background_options_widget.layout().addWidget(self._use_background_color_only_radio)
		self._background_options_widget.layout().addStretch()

		self._background_color_widget = qt.widget(layout=qt.horizontal_layout())
		self._background_color_widget.setToolTip(
			'To change background color, click on the color swatch.\nOr you can move the slider to change "value" of '
			'the color.')
		background_color_label = qt.label('BG Color:', parent=self)
		self._background_color_button = buttons.ColorButton(color=consts.DEFAULT_MAP_BACKGROUND_COLOR, parent=self)
		self._background_color_button.setFixedSize(qt.QSize(20, 20))
		self._background_color_slider = qt.QSlider(parent=self)
		self._background_color_slider.setMaximum(255)
		self._background_color_slider.setValue(255)
		self._background_color_slider.setOrientation(qt.Qt.Horizontal)
		self._background_color_widget.layout().addWidget(background_color_label)
		self._background_color_widget.layout().addWidget(self._background_color_button)
		self._background_color_widget.layout().addWidget(self._background_color_slider)

		self._background_image_widget = qt.widget(layout=qt.horizontal_layout(), parent=self)
		self._background_image_widget.setEnabled(False)
		background_image_label = qt.label('BG Image:', parent=self)
		self._background_image_line = qt.line_edit(parent=self)
		self._background_image_browse_button = qt.tool_button(icon='open_folder', parent=self)
		self._background_image_browse_button.setFixedSize(qt.QSize(20, 20))
		self._background_image_browse_button.setAutoRaise(True)
		self._background_image_snapshot_button = qt.tool_button(icon='camera', parent=self)
		self._background_image_snapshot_button.setFixedSize(qt.QSize(20, 20))
		self._background_image_snapshot_button.setAutoRaise(True)
		self._background_image_snapshot_button.setVisible(False)
		self._background_image_widget.layout().addWidget(background_image_label)
		self._background_image_widget.layout().addWidget(self._background_image_line)
		self._background_image_widget.layout().addWidget(self._background_image_browse_button)
		self._background_image_widget.layout().addWidget(self._background_image_snapshot_button)

		self._size_widget = qt.widget(layout=qt.horizontal_layout(), parent=self)
		self._size_widget.setToolTip('To set map size, type value in width or height field.')
		map_size_label = qt.label('Map Size', parent=self)
		map_width_label = qt.label('Width', parent=self)
		map_width_label.setIndent(15)
		self._map_width_spinbox = qt.QSpinBox(parent=self)
		self._map_width_spinbox.setButtonSymbols(qt.QSpinBox.NoButtons)
		self._map_width_spinbox.setMinimum(120)
		self._map_width_spinbox.setMaximum(9999)
		self._map_width_spinbox.setValue(consts.DEFAULT_MAP_WIDTH)
		map_height_label = qt.label('Width', parent=self)
		map_height_label.setIndent(15)
		self._map_height_spinbox = qt.QSpinBox(parent=self)
		self._map_height_spinbox.setButtonSymbols(qt.QSpinBox.NoButtons)
		self._map_height_spinbox.setMinimum(120)
		self._map_height_spinbox.setValue(consts.DEFAULT_MAP_HEIGHT)
		self._size_widget.layout().addWidget(map_size_label)
		self._size_widget.layout().addWidget(map_width_label)
		self._size_widget.layout().addWidget(self._map_width_spinbox)
		self._size_widget.layout().addWidget(map_height_label)
		self._size_widget.layout().addWidget(self._map_height_spinbox)

		buttons_layout = qt.horizontal_layout()
		self._create_new_map_button = qt.base_button('Create New Map', tooltip=consts.CREATE_NEW_MAP_TOOLTIP, parent=self)
		self._import_map_file_button = qt.base_button('Import Map File', tooltip=consts.IMPORT_MAP_TOOLTIP, parent=self)
		self._edit_current_map_button = qt.base_button('Save teo Node', tooltip=consts.EDIT_MAP_TOOLTIP, parent=self)
		self._export_map_file_button = qt.base_button('Export to Map File', tooltip=consts.EXPORT_MAP_TOOLTIP, parent=self)
		self._edit_current_map_button.setVisible(False)
		self._export_map_file_button.setVisible(False)
		for btn in [
			self._create_new_map_button, self._import_map_file_button, self._edit_current_map_button,
			self._export_map_file_button]:
			btn.setFixedHeight(30)
			btn.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Fixed)
			btn.setStyleSheet('QPushButton{background-color: #55bef2;color: black;}')
		buttons_layout.addWidget(self._create_new_map_button)
		buttons_layout.addWidget(self._import_map_file_button)
		buttons_layout.addWidget(self._edit_current_map_button)
		buttons_layout.addWidget(self._export_map_file_button)
		self._cancel_button = qt.base_button('Cancel', parent=self)
		self._cancel_button.setFixedHeight(30)
		self._cancel_button.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Fixed)
		self._cancel_button.setStyleSheet('QPushButton{background-color: #f26f55;color: black;}')

		self._init_widget.layout().addLayout(top_horizontal_layout)
		self._init_widget.layout().addWidget(self._type_label)
		self._init_widget.layout().addWidget(self._name_widget)
		self._init_widget.layout().addWidget(self._background_options_widget)
		self._init_widget.layout().addWidget(self._background_color_widget)
		self._init_widget.layout().addWidget(self._background_image_widget)
		self._init_widget.layout().addWidget(self._size_widget)
		self._init_widget.layout().addStretch()
		self._init_widget.layout().addLayout(buttons_layout)
		self._init_widget.layout().addWidget(self._cancel_button)

		self._stack_widget.addWidget(self._init_widget)

		self._use_background_button_group = qt.QButtonGroup(parent=self)
		self._use_background_button_group.addButton(self._use_background_color_only_radio, 0)
		self._use_background_button_group.addButton(self._use_background_image_radio, 1)
		self._background_color_button.enable_drag_drop = False
		uiutils.set_button_color(self._background_color_button, *consts.DEFAULT_MAP_BACKGROUND_COLOR.getRgbF()[:3])
		self._background_color_slider.setValue(consts.DEFAULT_MAP_BACKGROUND_COLOR.value())

	def _setup_main_widget(self):
		"""
		Internal function that creates main widget.
		"""

		self._main_widget = qt.widget(layout=qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0)))
		if dcc.is_maya():
			self._editor_widget = maya_editor.MayaAnimPickerEditorWidget(controller=self._controller, parent=self)
		else:
			self._editor_widget = editor.AnimPickerEditorWidget(controller=self._controller, parent=self)

		self._main_widget.layout().addWidget(self._editor_widget)

		self._stack_widget.addWidget(self._main_widget)

	def _determine_page(self):
		"""
		Internal function that checks whether initial or main pages should be set as the active one based on current
		DCC scene state.
		"""

		picker_nodes = self._controller.filter_picker_nodes()
		if picker_nodes:
			self._stack_widget.setCurrentIndex(0)
			self.resize(self._working_size)
		else:
			self._move_to_init_page()

	def _move_to_init_page(self, edit: bool = False):
		"""
		Internal function that is called when initial page is set as the active one.

		:param bool edit: whether settings are editable.
		"""

		self._working_size = self.size()

		self._create_new_map_button.setVisible(not edit)
		self._import_map_file_button.setVisible(not edit)
		self._edit_current_map_button.setVisible(edit)
		self._export_map_file_button.setVisible(edit)

		if edit:
			self._type_label.setText('---- EDIT CURRENT MAP ----')
		else:
			self._type_label.setText('---- CREATE NEW MAP ----')
			# self._group_name_line.setText(utils.numeric_name(consts.DEFAULT_GROUP_NAME, self._group_name_line.labels))
			self._group_name_line.setText(utils.numeric_name(self._controller.state.group_name, []))
			self._map_name_line.setText(utils.numeric_name(
				self._controller.state.map_name, [self.map_name(i) for i in range(self._editor_widget.tab_widget.count())]))

		self._stack_widget.setCurrentIndex(1)
		self.resize(300, 320)

	def _on_warning(self, msg: str):
		"""
		Internal callback function that is called each time a warning is produced by the controller.

		:param str msg: warning message.
		"""

		uiutils.warning(msg, parent=self)

	def _on_create_new_map_button_clicked(self):
		"""
		Internal callback function that is called each time Create New Map button is clicked by the user.
		Creates a new animation picker map based on current settings.
		"""

		self._controller.create_new_map()

	def _on_pre_create_map_event(self, event: PreCreateMapEvent):
		"""
		Internal callback function that is called before a new map is created by the controller.

		:param  PreCreateMapEvent event: event.
		"""

		if event.group_name in self._editor_widget.group_line_edit.labels():
			if event.map_name in [self.map_name(i) for i in range(self._editor_widget.tab_widget.count())]:
				event.result = False
		else:
			self._editor_widget.group_line_edit.append_label(event.group_name)
			self._editor_widget.tab_widget.clear()
			event.result = True

	def _on_create_map_event(self, event: CreateMapEvent):
		"""
		Internal callback function that is called when a new map is created by the controller.

		:param CreateMapEvent event: event.
		"""

		tab = self._editor_widget.tab_widget.add_graphics_tab(event.map_name)
		index = self._editor_widget.tab_widget.indexOf(tab)
		scene = self._editor_widget.tab_widget.scene_at_index(index)
		scene.color = self._background_color_button.color()
		self._stack_widget.setCurrentIndex(0)
		self._editor_widget.tab_widget.scene_at_index(index).map_size = qt.QSizeF(event.map_width, event.map_height)
		self.resize(self._working_size)
		event.scene = scene
		event.use_background_image = bool(self._use_background_button_group.checkedId())
		event.result = True

	def _on_import_map_file_button_clicked(self):
		"""
		Internal callback function that is called each time Import Map File button is clicked by the user.
		Imports a picker map file.
		"""

		self._controller.import_map()

	def _on_edit_current_map_button_clicked(self):
		"""
		Internal callback function that is called each time Save to Node button is clicked by the user.
		Saves current changes into scene.
		"""

		self._controller.edit_current_map()

	def _on_export_map_file_button_clicked(self):
		"""
		Internal callback function that is called each time Export Map File button is clicked by the user.
		Exports a picker map file.
		"""

		self._controller.export_map()
