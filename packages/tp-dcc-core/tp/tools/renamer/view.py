#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains tp-dcc-tools-renamer view
"""

from Qt.QtCore import Qt, QRegExp
from Qt.QtWidgets import QSizePolicy, QWidget, QButtonGroup, QSpacerItem
from Qt.QtGui import QRegExpValidator

from tp.core import dcc
from tp.core.managers import resources
from tp.common.qt import base, contexts as qt_contexts
from tp.tools.renamer import model, controller
from tp.common.qt.widgets import layouts, dividers, splitter, buttons, comboboxes, checkboxes, tabs, lineedits


class RenamerView(base.BaseWidget):
	def __init__(self, parent=None):
		if dcc.is_maya():
			from tp.tools.renamer.maya import model as maya_model, controller as maya_controller
			self._controller = maya_controller.RenamerControllerMaya(model=maya_model.RenamerModelMaya())
		else:
			self._controller = controller.RenamerController(model=model.RenamerModel())
		super(RenamerView, self).__init__(parent=parent)

		self.refresh()

	def ui(self):
		super(RenamerView, self).ui()

		top_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
		top_layout.setAlignment(Qt.AlignLeft)
		self._buttons_grp = QButtonGroup(self)
		self._buttons_grp.setExclusive(True)
		self.main_layout.addLayout(top_layout)
		self.main_layout.addLayout(dividers.DividerLayout())

		self._categories_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
		self._categories_layout.setAlignment(Qt.AlignLeft)

		selection_layout = layouts.HorizontalLayout(spacing=2, margins=(4, 0, 4, 0))
		top_layout.addLayout(selection_layout)

		self._all_radio = buttons.BaseRadioButton('All', parent=self)
		self._all_radio.setFixedHeight(19)
		self._all_radio.setAutoExclusive(True)
		self._selected_radio = buttons.BaseRadioButton('Selected', parent=self)
		self._selected_radio.setFixedHeight(19)
		self._selected_radio.setChecked(True)
		self._selected_radio.setAutoExclusive(True)
		self._hierarchy_cbx = checkboxes.BaseCheckBox('Hierarchy', parent=self)
		self._hierarchy_cbx.setFixedHeight(19)
		self._node_types_combo = comboboxes.BaseComboBox(parent=self)
		self._auto_rename_shapes_cbx = None
		self._auto_rename_shapes_cbx = checkboxes.BaseCheckBox('Auto Rename Shapes', parent=self)
		self._auto_rename_shapes_cbx.setChecked(True)
		if not dcc.is_maya():
			self._auto_rename_shapes_cbx.setVisible(False)

		selection_layout.addWidget(self._selected_radio)
		selection_layout.addWidget(self._all_radio)
		selection_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
		selection_layout.addWidget(self._hierarchy_cbx)
		selection_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
		selection_layout.addWidget(self._node_types_combo)
		if self._auto_rename_shapes_cbx:
			selection_layout.addItem(QSpacerItem(10, 0, QSizePolicy.Fixed, QSizePolicy.Fixed))
			selection_layout.addWidget(self._auto_rename_shapes_cbx)

		self._splitter = splitter.CollapsibleSplitter(parent=self)
		self._splitter.setOrientation(Qt.Horizontal)
		self._splitter.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
		self.main_layout.addWidget(self._splitter)

		self._rename_tab = tabs.BaseTabWidget(parent=self)
		self._splitter.addWidget(self._rename_tab)

		rename_widget = QWidget()
		rename_widget.setLayout(layouts.VerticalLayout(spacing=2, margins=(0, 0, 0, 0)))
		rename_widget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
		rename_layout = layouts.HorizontalLayout(spacing=2, margins=(2, 2, 2, 2))
		rename_layout.setAlignment(Qt.AlignLeft)
		rename_widget.layout().addLayout(rename_layout)
		self._base_name_cbx = checkboxes.BaseCheckBox(parent=self)
		rename_layout.addWidget(self._base_name_cbx)
		self._renamer_line = lineedits.BaseLineEdit(parent=self)
		self._renamer_line.setPlaceholderText('New Name')
		rename_layout.addWidget(self._renamer_line)
		reg_ex = QRegExp("^(?!^_)[a-zA-Z_]+")
		text_validator = QRegExpValidator(reg_ex, self._renamer_line)
		self._renamer_line.setValidator(text_validator)
		self._renamer_button = buttons.BaseButton(parent=self)
		self._renamer_button.setIcon(resources.icon('rename'))
		rename_layout.addWidget(self._renamer_button)

		rename_widget.layout().addWidget(dividers.Divider(parent=self))

		prefix_layout = layouts.HorizontalLayout(spacing=5, margins=(0, 0, 0, 0))
		prefix_layout.setAlignment(Qt.AlignLeft)
		rename_widget.layout().addLayout(prefix_layout)
		self._prefix_cbx = checkboxes.BaseCheckBox(parent=self)
		prefix_layout.addWidget(self._prefix_cbx)
		self._prefix_line = lineedits.BaseLineEdit(parent=self)
		self._prefix_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		self._prefix_line.setPlaceholderText('Prefix')
		prefix_reg_exp = QRegExp("^(?!^_)[a-zA-Z_]+")
		prefix_validator = QRegExpValidator(prefix_reg_exp, self._prefix_line)
		self._prefix_line.setValidator(prefix_validator)
		self._prefix_combo = comboboxes.BaseComboBox(parent=self)
		self._prefix_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		prefix_layout.addWidget(self._prefix_line)
		prefix_layout.addWidget(self._prefix_combo)
		self._prefix_button = buttons.BaseButton(parent=self)
		self._prefix_button.setIcon(resources.icon('prefix'))
		self._remove_prefix_button = buttons.BaseButton(parent=self)
		self._remove_prefix_button.setIcon(resources.icon('trash'))
		prefix_layout.addWidget(self._prefix_button)
		prefix_layout.addWidget(self._remove_prefix_button)

		# remove_first_layout = layouts.HorizontalLayout(spacing=2, margins=(0, 0, 0, 0))
		# remove_first_layout.setAlignment(Qt.AlignLeft)
		# rename_widget.layout().addLayout(remove_first_layout)
		# self._remove_first_cbx = checkbox.BaseCheckBox(parent=self)
		# remove_first_layout.addWidget(self._remove_first_cbx)
		# self._remove_first_lbl = label.BaseLabel('Remove first: ')
		# self._remove_first_spn = spinbox.BaseSpinBox(parent=self)
		# self._remove_first_spn.setFocusPolicy(Qt.NoFocus)
		# self._remove_first_spn.setMinimum(0)
		# self._remove_first_spn.setMaximum(99)
		# last_digits_lbl = label.BaseLabel(' digits', parent=self)
		# remove_first_layout.addWidget(self._remove_first_lbl)
		# remove_first_layout.addWidget(self._remove_first_spn)
		# remove_first_layout.addWidget(last_digits_lbl)
		# self._remove_first_btn = buttons.BaseButton(parent=self)
		# self._remove_first_btn.setIcon(resources.icon('trash'))
		# remove_first_layout.addStretch()
		# remove_first_layout.addWidget(self._remove_first_btn)
		#
		# rename_widget.layout().addWidget(dividers.Divider(parent=self))
		#
		# suffix_layout = layouts.HorizontalLayout(spacing=5, margins=(0, 0, 0, 0))
		# suffix_layout.setAlignment(Qt.AlignLeft)
		# rename_widget.layout().addLayout(suffix_layout)
		# self._suffix_cbx = checkbox.BaseCheckBox(parent=self)
		# suffix_layout.addWidget(self._suffix_cbx)
		# self._suffix_line = lineedit.BaseLineEdit(parent=self)
		# self._suffix_line.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		# suffix_reg_exp = QRegExp("^[a-zA-Z_0-9]+")
		# suffix_validator = QRegExpValidator(suffix_reg_exp, self._suffix_line)
		# self._suffix_line.setValidator(suffix_validator)
		# self._suffix_line.setPlaceholderText('Suffix')
		# self._suffix_combo = combobox.BaseComboBox(parent=self)
		# self._suffix_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
		# suffix_layout.addWidget(self._suffix_line)
		# suffix_layout.addWidget(self._suffix_combo)
		# self._suffix_btn = buttons.BaseButton(parent=self)
		# self._suffix_btn.setIcon(resources.icon('suffix'))
		# self._remove_suffix_btn = buttons.BaseButton(parent=self)
		# self._remove_suffix_btn.setIcon(resources.icon('trash'))
		# suffix_layout.addWidget(self._suffix_btn)
		# suffix_layout.addWidget(self._remove_suffix_btn)
		#
		# remove_last_layout = layouts.HorizontalLayout(spacing=5, margins=(0, 0, 0, 0))
		# remove_last_layout.setAlignment(Qt.AlignLeft)
		# rename_widget.layout().addLayout(remove_last_layout)
		# self._remove_last_cbx = checkbox.BaseCheckBox(parent=self)
		# remove_last_layout.addWidget(self._remove_last_cbx)
		# self._remove_last_lbl = label.BaseLabel('Remove last: ', parent=self)
		# self._remove_last_spn = spinbox.BaseSpinBox(parent=self)
		# self._remove_last_spn.setFocusPolicy(Qt.NoFocus)
		# self._remove_last_spn.setMinimum(0)
		# self._remove_last_spn.setMaximum(99)
		# last_digits_lbl2 = label.BaseLabel(' digits', parent=None)
		# remove_last_layout.addWidget(self._remove_last_lbl)
		# remove_last_layout.addWidget(self._remove_last_spn)
		# remove_last_layout.addWidget(last_digits_lbl2)
		# self._remove_last_btn = buttons.BaseButton()
		# self._remove_last_btn.setIcon(resources.icon('trash'))
		# remove_last_layout.addStretch()
		# remove_last_layout.addWidget(self._remove_last_btn)
		#
		# rename_widget.layout().addWidget(dividers.Divider(parent=self))

		rename_widget.layout().addStretch()

		# self._tools_rename_widget = toolsrenamewidget.ToolsRenameWidget(
		# 	model=self._model, controller=self._controller, parent=self)
		# self._auto_rename_widget = nameitrenamewidget.NameItRenameWidget(
		# 	model=self._model, controller=self._controller, parent=self)

		self._rename_tab.addTab(rename_widget, 'Renamer')
		# self._rename_tab.addTab(self._auto_rename_widget, 'NameIt')
		# self._rename_tab.addTab(self._tools_rename_widget, 'Tools')

	def setup_signals(self):
		super(RenamerView, self).setup_signals()

		self._controller.model.checkNameChanged.connect(self._on_model_check_name_changed)
		self._controller.model.nameChanged.connect(self._on_model_name_changed)
		self._controller.model.checkPrefixChanged.connect(self._on_model_check_prefix_changed)

		self._selected_radio.clicked.connect(self._controller.set_selection)
		self._all_radio.clicked.connect(self._controller.set_all_selection)
		self._hierarchy_cbx.toggled.connect(self._controller.toggle_hierarchy_check)
		self._base_name_cbx.toggled.connect(self._controller.toggle_name_check)
		self._renamer_line.textChanged.connect(self._controller.change_name)
		self._renamer_button.clicked.connect(self._controller.rename_simple)
		self._prefix_cbx.toggled.connect(self._controller.toggle_prefix_check)
		self._prefix_line.textChanged.connect(self._controller.change_prefix)
		self._prefix_button.clicked.connect(self._controller.add_prefix)
		self._remove_prefix_button.clicked.connect(self._controller.remove_prefix)

	# =================================================================================================================
	# BASE
	# =================================================================================================================

	def refresh(self):

		self._base_name_cbx.setChecked(self._controller.model.name_check)
		self._renamer_line.setText(self._controller.model.name)
		self._prefix_cbx.setChecked(self._controller.model.prefix_check)
		self._prefix_line.setText(self._controller.model.prefix)

	# =================================================================================================================
	# CALLBACKS
	# =================================================================================================================

	def _on_model_check_name_changed(self, flag):
		"""
		Internal callback function that is called when check name changes within model.

		:param bool flag: whether model check name is True or False.
		"""

		with qt_contexts.block_signals(self._base_name_cbx):
			self._base_name_cbx.setChecked(flag)
		self._renamer_line.setEnabled(flag)
		self._renamer_button.setEnabled(flag)

	def _on_model_name_changed(self, new_name):
		"""
		Internal callback function that is called when name value changes within model.

		:param str new_name: new model name.
		"""

		with qt_contexts.block_signals(self._renamer_line):
			self._renamer_line.setText(new_name)

	def _on_model_check_prefix_changed(self, flag):
		"""
		Internal callback function that is called when check prefix changes within model.

		:param bool flag: whether model check prefix is True or False.
		"""

		with qt_contexts.block_signals(self._prefix_cbx):
			self._prefix_cbx.setChecked(flag)
		self._prefix_line.setEnabled(flag)
		self._prefix_combo.setEnabled(flag)
		self._prefix_button.setEnabled(flag)
		self._remove_prefix_button.setEnabled(flag)
