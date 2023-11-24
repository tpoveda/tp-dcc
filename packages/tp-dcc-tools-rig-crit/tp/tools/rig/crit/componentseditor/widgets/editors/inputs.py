from __future__ import annotations

from tp.common.qt import api as qt
from tp.common.resources import api as resources


class InputLayerSettingsWidget(qt.QWidget):

	def __init__(self, parent: qt.QWidget | None = None):
		super().__init__(parent)

		main_layout = qt.vertical_layout()
		self.setLayout(main_layout)

		buttons_layout = qt.horizontal_layout(spacing=2)
		self._create_input_button = qt.base_button('Create', icon=resources.icon('add'), parent=self)
		self._delete_input_button = qt.base_button('Delete', icon=resources.icon('trash'), parent=self)
		self._refresh_button = qt.base_button(icon=resources.icon('refresh'), parent=self)
		buttons_layout.addWidget(self._create_input_button)
		buttons_layout.addWidget(self._delete_input_button)
		buttons_layout.addStretch()
		buttons_layout.addWidget(self._refresh_button)

		inputs_splitter = qt.QSplitter(parent=self)
		inputs_splitter.setSizePolicy(qt.QSizePolicy.Expanding, qt.QSizePolicy.Expanding)

		self._inputs_tree = qt.QTreeWidget(parent=self)
		self._inputs_tree.setHeaderLabels(['Inputs Hierarchy'])
		self._inputs_tree.setIndentation(15)
		self._inputs_tree.setSelectionMode(qt.QAbstractItemView.ExtendedSelection)

		self._inputs_tab = qt.LineTabWidget(alignment=qt.Qt.AlignLeft, parent=self)
		scroll = qt.QScrollArea(parent=self)
		scroll.setWidgetResizable(True)
		self._settings_layout = qt.vertical_layout(spacing=2)
		settings_widget = qt.widget(layout=self._settings_layout, parent=self)
		scroll.setWidget(settings_widget)
		settings_buttons_layout = qt.horizontal_layout(spacing=2)
		self._add_setting_button = qt.base_button(icon=resources.icon('add'), parent=self)
		settings_buttons_layout.addWidget(self._add_setting_button)
		settings_buttons_layout.addStretch()

		self._inputs_stack = qt.sliding_opacity_stacked_widget(parent=self)
		empty_widget = qt.widget(layout=qt.horizontal_layout(spacing=0, margins=(0, 0, 0, 0)))
		empty_label = qt.label('Select an Input', parent=self)
		empty_label.theme_level = empty_label.Levels.H5
		empty_widget.layout().addStretch()
		empty_widget.layout().addWidget(empty_label)
		empty_widget.layout().addStretch()

		# self._input_settings_widget = InputHookSettingsWidget(parent=self)
		self._settings_stack = qt.sliding_opacity_stacked_widget(parent=self)
		input_hook_settings = qt.widget(layout=qt.vertical_layout(spacing=2), parent=self)
		self._inputs_tab.add_tab(self._inputs_stack, {'text': 'Properties', 'image': 'settings'})
		self._inputs_tab.add_tab(self._settings_stack, {'text': 'Settings', 'image': 'edit_property'})

		input_hook_settings.layout().addWidget(scroll)
		input_hook_settings.layout().addWidget(qt.divider(parent=self))
		input_hook_settings.layout().addLayout(settings_buttons_layout)
		# self._input_attribute_settings_widget = attributes.AttributeSettingsWidget(parent=self)
		self._settings_stack.addWidget(input_hook_settings)
		# self._settings_stack.addWidget(self._input_attribute_settings_widget)

		self._inputs_stack.addWidget(empty_widget)
		# self._inputs_stack.addWidget(self._input_settings_widget)

		inputs_splitter.addWidget(self._inputs_tree)
		inputs_splitter.addWidget(self._inputs_tab)

		main_layout.addLayout(buttons_layout)
		main_layout.addWidget(qt.divider(parent=self))
		main_layout.addWidget(inputs_splitter)
