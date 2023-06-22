from __future__ import annotations

import typing
from typing import List
from functools import partial

from overrides import override

from tp.common.qt import api as qt

if typing.TYPE_CHECKING:
	from tp.tools.modelchecker.controller import ModelCheckerController


class ModelCheckerView(qt.FramelessWindow):

	WINDOW_SETTINGS_PATH = 'tp/modelchecker'
	VERSION = '0.0.1'

	def __init__(self, controller: ModelCheckerController, parent: qt.QWidget | None = None):

		self._controller = controller

		self._selected_root_node_line = None							#type: qt.QLineEdit
		self._clear_selected_node_button = None							#type: qt.QPushButton
		self._select_selected_node_button = None						#type: qt.QPushButton
		self._categories = {}
		self._commands = {}

		super().__init__(title=f'Model Checker {self.VERSION}', width=800, height=600, parent=parent)

	@override
	def setup_ui(self):
		super().setup_ui()

		self.set_main_layout(qt.vertical_layout(margins=(6, 6, 6, 6)))

		columns_layout = qt.horizontal_layout()
		report_layout = qt.vertical_layout()
		checks_layout = qt.vertical_layout()
		columns_layout.addLayout(checks_layout)
		columns_layout.addLayout(report_layout)

		selected_node_layout = qt.horizontal_layout()
		checks_layout.addLayout(selected_node_layout)
		self._selected_root_node_line = qt.line_edit(read_only=True, parent=self)
		self._clear_selected_node_button = qt.base_button(text='Clear', max_width=60, parent=self)
		self._select_selected_node_button = qt.base_button(text='Select', max_width=60, parent=self)
		selected_node_layout.addWidget(qt.label('Root Node', max_width=80, parent=self))
		selected_node_layout.addWidget(self._selected_root_node_line)
		selected_node_layout.addWidget(self._clear_selected_node_button)
		selected_node_layout.addWidget(self._select_selected_node_button)

		settings_layout = qt.horizontal_layout()
		self._metadata_check = qt.QCheckBox(parent=self)
		self._consolidate_check = qt.QCheckBox(parent=self)
		settings_layout.addWidget(qt.label(text='Include scene metadata: ', parent=self))
		settings_layout.addWidget(self._metadata_check)
		settings_layout.addWidget(qt.label(text='Consolidate display: ', parent=self))
		settings_layout.addWidget(self._consolidate_check)
		self._report_output_text = qt.QTextEdit(parent=self)
		self._report_output_text.setReadOnly(True)
		self._report_output_text.setMinimumWidth(600)
		run_layout = qt.horizontal_layout()
		self._clear_report_button = qt.base_button(text='Clear', max_width=150, parent=self)
		self._run_all_checked_button = qt.base_button(text='Run All Checked', parent=self)
		run_layout.addWidget(qt.label(text='Report: ', parent=self))
		run_layout.addWidget(self._clear_report_button)
		run_layout.addWidget(self._run_all_checked_button)
		report_layout.addLayout(settings_layout)
		report_layout.addWidget(self._report_output_text)
		report_layout.addLayout(run_layout)

		for category_name in self._controller.categories():
			self._categories[category_name] = {}
			self._categories[category_name]['widget'] = qt.QWidget(parent=self)
			self._categories[category_name]['layout'] = qt.vertical_layout()
			self._categories[category_name]['widget'].setLayout(self._categories[category_name]['layout'])
			self._categories[category_name]['header'] = qt.horizontal_layout()
			self._categories[category_name]['button'] = qt.QPushButton(category_name, parent=self)
			self._categories[category_name]['button'].setStyleSheet(
				'background-color: grey; text-transform: uppercase; color: #000000; font-size: 18px;')
			self._categories[category_name]['collapse'] = qt.QPushButton('\u2193', parent=self)
			self._categories[category_name]['collapse'].setMaximumWidth(30)
			self._categories[category_name]['header'].addWidget(self._categories[category_name]['button'])
			self._categories[category_name]['header'].addWidget(self._categories[category_name]['collapse'])
			checks_layout.addLayout(self._categories[category_name]['header'])
			checks_layout.addWidget(self._categories[category_name]['widget'])

		for command_name in sorted(self._controller.commands.keys()):
			command_label = self._controller.commands[command_name]['label']
			command_category = self._controller.commands[command_name]['category']
			self._commands[command_name] = {}
			self._commands[command_name]['widget'] = qt.QWidget(parent=self)
			self._commands[command_name]['widget'].setMaximumHeight(40)
			self._commands[command_name]['widget'].setStyleSheet('padding: 0px; margin: 0px;')
			self._commands[command_name]['layout'] = qt.horizontal_layout(spacing=4, margins=(0, 0, 0, 0))
			self._commands[command_name]['widget'].setLayout(self._commands[command_name]['layout'])
			self._categories[command_category]['layout'].addWidget(self._commands[command_name]['widget'])
			self._commands[command_name]['label'] = qt.label(text=command_label, min_width=180, parent=self)
			self._commands[command_name]['checkbox'] = qt.QCheckBox(parent=self)
			self._commands[command_name]['checkbox'].setMaximumWidth(20)
			self._commands[command_name]['checkbox'].setChecked(False)
			self._commands[command_name]['button'] = qt.base_button(text='Run', max_width=40, parent=self)
			self._commands[command_name]['button'].setMaximumWidth(40)
			self._commands[command_name]['error'] = qt.base_button(text='Select Error Nodes', max_width=150, parent=self)
			self._commands[command_name]['error'].setEnabled(False)
			self._commands[command_name]['layout'].addWidget(self._commands[command_name]['label'])
			self._commands[command_name]['layout'].addWidget(self._commands[command_name]['checkbox'])
			self._commands[command_name]['layout'].addWidget(self._commands[command_name]['button'])
			self._commands[command_name]['layout'].addWidget(self._commands[command_name]['error'])

		checks_layout.addStretch()

		check_buttons_layout = qt.horizontal_layout()
		checks_layout.addLayout(check_buttons_layout)
		self._uncheck_all_button = qt.base_button(text='Uncheck All', parent=self)
		self._invert_check_button = qt.base_button(text='Invert', parent=self)
		self._check_all_button = qt.base_button(text='Check All', parent=self)
		check_buttons_layout.addWidget(self._uncheck_all_button)
		check_buttons_layout.addWidget(self._invert_check_button)
		check_buttons_layout.addWidget(self._check_all_button)

		self.main_layout().addLayout(columns_layout)

	@override
	def setup_signals(self):
		super().setup_signals()

		self._controller.filteredNodes.connect(self._on_controller_filtered_nodes)
		self._controller.filteredTopNode.connect(self._on_controller_filtered_top_node)

		self._consolidate_check.stateChanged.connect(self._on_consolidated_checkbox_state_changed)
		self._metadata_check.stateChanged.connect(self._on_metadata_checkbox_state_changed)
		self._clear_selected_node_button.clicked.connect(self._on_clear_selected_node_button_clicked)
		self._select_selected_node_button.clicked.connect(self._on_select_selected_node_button_clicked)
		self._clear_report_button.clicked.connect(self._on_clear_report_button_clicked)
		self._run_all_checked_button.clicked.connect(self._on_run_all_checked_button_clicked)
		self._uncheck_all_button.clicked.connect(self._on_uncheck_all_checks_button_clicked)
		self._invert_check_button.clicked.connect(self._on_invert_checks_button_clicked)
		self._check_all_button.clicked.connect(self._on_check_all_checks_button_clicked)

		for category_name in self._controller.categories():
			self._categories[category_name]['collapse'].clicked.connect(
				partial(self._on_collapsed_category_button_clicked, category_name))
			self._categories[category_name]['button'].clicked.connect(
				partial(self._on_category_button_clicked, category_name))

		for command_name in sorted(self._controller.commands.keys()):
			self._commands[command_name]['button'].clicked.connect(
				partial(self._on_run_command_button_clicked, command_name))

	@override
	def load_settings(self):
		super().load_settings()

		if not self.WINDOW_SETTINGS_PATH:
			return

		consolidated = self._settings.value('/'.join((self.WINDOW_SETTINGS_PATH, 'consolidated')), False, bool)
		metadata = self._settings.value('/'.join((self.WINDOW_SETTINGS_PATH, 'metadata')), False, bool)
		checked_commands = self._settings.value('/'.join((self.WINDOW_SETTINGS_PATH, 'commands')), {})

		self._consolidate_check.setChecked(consolidated)
		self._metadata_check.setChecked(metadata)
		for command_name, checked in checked_commands.items():
			if command_name not in self._commands:
				continue
			self._commands[command_name]['checkbox'].setChecked(checked)

	@override
	def save_settings(self):
		super().save_settings()

		if not self.WINDOW_SETTINGS_PATH:
			return

		self._settings.setValue('/'.join((self.WINDOW_SETTINGS_PATH, 'consolidated')), self._consolidate_check.isChecked())
		self._settings.setValue('/'.join((self.WINDOW_SETTINGS_PATH, 'metadata')), self._metadata_check.isChecked())
		checked_commands = {}
		for command_name in self._controller.commands:
			checked_commands[command_name] = self._commands[command_name]['checkbox'].isChecked()
		self._settings.setValue('/'.join((self.WINDOW_SETTINGS_PATH, 'commands')), checked_commands)

	def _refresh_report(self):
		"""
		Internal function that updates report UI.
		"""

		self._report_output_text.clear()

		last_failed = None
		consolidated = self._consolidate_check.isChecked()

		html = ''

		if self._metadata_check.isChecked():
			metadata = self._controller.scene_metadata()
			html += "----------------- Scene Metadata -----------------<br>"
			for key in metadata:
				html += f"{key}: {metadata[key]}<br>"
			html += "-----------------------------------------------------<br>"

		for command_name in sorted(self._controller.commands.keys()):
			if command_name not in self._controller.results:
				self._commands[command_name]['error'].setEnabled(False)
				self._commands[command_name]['label'].setStyleSheet('background-color: none;')
				continue
			failed = len(self._controller.results[command_name] or []) != 0
			if failed:
				if self._controller.results[command_name][0] is None:
					self._commands[command_name]['error'].setEnabled(False)
					self._commands[command_name]['label'].setStyleSheet('background-color: #8C6803;')
				else:
					self._commands[command_name]['error'].setEnabled(True)
					self._commands[command_name]['error'].clicked.connect(
						partial(self._on_command_error_button_clicked, self._controller.results[command_name]))
					self._commands[command_name]['label'].setStyleSheet('background-color: #664444;')
			else:
				self._commands[command_name]['error'].setEnabled(False)
				self._commands[command_name]['label'].setStyleSheet('background-color: #446644;')

			command_label = self._controller.commands[command_name]['label']

			if last_failed != failed and last_failed is not None or (failed is True and last_failed is True):
				html += "<br>"
			last_failed = failed
			if failed:
				if self._controller.results[command_name][0] is None:
					html += f"&#10752; {command_label}<font color=#8C6803> [ NOT IMPLEMENTED ]</font><br>"
				else:
					html += f"&#10752; {command_label}<font color=#9c4f4f> [ FAILED ]</font><br>"
			else:
				html += f"{command_label}<font color=#64a65a> [ SUCCESS ]</font><br>"
			if failed:
				if consolidated and self._controller.results[command_name][0] and '.' in self._controller.results[command_name][0]:
					store = {}
					for node in self._controller.results[command_name]:
						name = node.split(".")[0]
						store[name] = store.get(name, 0) + 1
					for node in store:
						word = "issues" if store[node] > 1 else "issue"
						html += f"&#9492;&#9472; {node} - <font color=#9c4f4f>{store[node]} {word}</font><br>"
				else:
					for node in self._controller.results[command_name]:
						html += f"&#9492;&#9472; {node}<br>"

		self._report_output_text.insertHtml(html)

	def _on_consolidated_checkbox_state_changed(self):
		"""
		Internal callback function that is called each time consolidated checkbox state changes.
		Refreshes report UI.
		"""

		self._refresh_report()

	def _on_metadata_checkbox_state_changed(self):
		"""
		Internal callback function that is called each time metadata checkbox state changes.
		Refreshes report UI.
		"""

		self._refresh_report()

	def _on_controller_filtered_nodes(self, node_names: List[str]):
		"""
		Internal callback function that is called each time nodes are filtered by the controller.

		:param List[str] node_names: list of filtered node names.
		"""

		if not node_names:
			self._report_output_text.clear()
			self._report_output_text.insertPlainText('Object in Root Node does not exists.\n')

	def _on_controller_filtered_top_node(self, top_node: str):
		"""
		Internal callback function that is called each time top node is filtered by the controller.

		:param str top_node: filtered top node name.
		"""

		if not top_node:
			self._selected_root_node_line.clear()

	def _on_clear_selected_node_button_clicked(self):
		"""
		Internal callback function that is called when Clear button is clicke by the user.
		Clears root node text.
		"""

		self._selected_root_node_line.setText('')

	def _on_select_selected_node_button_clicked(self):
		"""
		Internal callback function that is called when Select button is clicked by the user.
		Sets root node text from first current selected node within scene.
		"""

		top_node_name = self._controller.top_node()
		if not top_node_name:
			return

		self._selected_root_node_line.setText(top_node_name)

	def _on_clear_report_button_clicked(self):
		"""
		Internal callback function that is called when Clear button is clicked by the user.
		Clears internal report variables and clears out report text.
		"""

		self._controller.clear_report()
		for command_name in self._controller.commands.keys():
			self._commands[command_name]['error'].setEnabled(False)
			self._commands[command_name]['label'].setStyleSheet('background-color: none;')
		self._report_output_text.clear()

	def _on_run_all_checked_button_clicked(self):
		"""
		Internal callback function that is called when Run All Checked button is clicked by the user.
		Executes all checked checks.
		"""

		checked_commands = []
		nodes = self._controller.filter_nodes(top_node=self._selected_root_node_line.text())
		if not nodes:
			self._report_output_text.clear()
			self._report_output_text.insertHtml('No nodes to check.')
			return

		for command_name in self._controller.commands:
			if self._commands[command_name]['checkbox'].isChecked():
				checked_commands.append(command_name)

		self._controller.run_commands(checked_commands, nodes)

		self._refresh_report()

	def _on_uncheck_all_checks_button_clicked(self):
		"""
		Internal callback function that is called each time Uncheck All button is clicked by the user.
		Unchecks all check checkboxes.
		"""

		for command_name in self._controller.commands:
			self._commands[command_name]['checkbox'].setChecked(False)

	def _on_invert_checks_button_clicked(self):
		"""
		Internal callback function that is called each time Invert button is clicked by the user.
		Inverts check checkboxes.
		"""

		for command_name in self._controller.commands:
			self._commands[command_name]['checkbox'].setChecked(not self._commands[command_name]['checkbox'].isChecked())

	def _on_check_all_checks_button_clicked(self):
		"""
		Internal callback function that is called each time Check All button is clicked by the user.
		Checks all check checkboxes.
		"""

		for command_name in self._controller.commands:
			self._commands[command_name]['checkbox'].setChecked(True)

	def _on_collapsed_category_button_clicked(self, category_name: str):
		"""
		Internal callback function that is called each time a collapse category button is clicked by the user.
		Expands/Collapses selected category widget.

		:param str category_name: collapsed category name.
		"""

		state = self._categories[category_name]['widget'].isVisible()
		button_label = u'\u21B5' if state else u'\u2193'
		# self.adjustSize()
		self._categories[category_name]['collapse'].setText(button_label)
		self._categories[category_name]['widget'].setVisible(not state)

	def _on_category_button_clicked(self, category_name: str):
		"""
		Internal callback function that is called each time a category button is clicked by the user.
		Checks/Unchecks all checks of the clicked category.

		:param str category_name: clicked category name.
		"""

		unchecked_category_buttons = []
		category_buttons = []
		for command_name, command in self._controller.commands.items():
			category = command['category']
			if category == category_name:
				category_buttons.append(command_name)
				if self._commands[command_name]['checkbox'].isChecked():
					unchecked_category_buttons.append(command_name)

		for category in category_buttons:
			checked = len(unchecked_category_buttons) != len(category_buttons)
			self._commands[category]['checkbox'].setChecked(checked)

	def _on_run_command_button_clicked(self, command_name: str):
		"""
		Internal callback function that is called each time a Run command button is clicked by the user.

		:param str command_name: name of the command to run.
		"""

		nodes = self._controller.filter_nodes(top_node=self._selected_root_node_line.text())
		self._controller.run_commands([command_name], nodes)

		self._refresh_report()

	def _on_command_error_button_clicked(self, result: List[str]):
		"""
		Internal callback function that is called each time Command Error button is clicked by the user.
		Selects all error nodes.

		:param List[str] result: list of nodes that did not pass the checks.
		"""

		self._controller.select_nodes(result)



