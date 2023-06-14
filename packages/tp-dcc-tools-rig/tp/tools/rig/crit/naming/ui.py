import copy
import random
from typing import Tuple, List, Dict

from overrides import override

from tp.bootstrap import api
from tp.common.naming import manager
from tp.common.qt import api as qt

from tp.libs.rig.crit import api as crit
from tp.tools.rig.crit.naming.widgets import stringedit, presets, tokens


class UIState:
	def __init__(self):
		super().__init__()

		self.is_admin = False
		self.presets_manager = None							# type: crit.namingpresets.PresetsManager
		self.current_naming_manager = None					# type: manager.NameManager
		self.current_preset = None							# type: crit.namingpresets.Preset
		self.original_manager = None						# type: crit.namingpresets.PresetsManager
		self.crit_config = None								# type: crit.Configuration
		self.preset_operations = PresetOperations()
		self.requires_save = True


class PresetOperations:
	def __init__(self):
		self._operations = dict()

	def add_create_operation(self, preset: crit.namingpresets.Preset, crit_type: str):
		"""
		Adds a create operation into the list of presets operations.

		:param crit.namingpresets.Preset preset: preset we want to add create operation for.
		:param str crit_type: crit naming type.
		"""

		self._operations.setdefault(preset, dict()).setdefault('create', list()).append(crit_type)


class NamingConventionWindow(qt.FramelessWindow):

	WINDOW_SETTINGS_PATH = 'tp/critnamingconvention'

	def __init__(self):
		super().__init__(
			name='CritNamingConvention', title='CRIT Naming Convention', width=580, height=440, save_window_pref=False)

		self.disable_state()
		self._init_preset_tree()

	@override
	def setup_ui(self):
		super().setup_ui()

		self._ui_state = UIState()
		self._ui_state.is_admin = api.current_package_manager().is_admin

		self._presets_view = presets.PresetView(parent=self)
		self._presets_view.setMaximumWidth(qt.dpi_scale(200))
		self._convention_combobox = qt.ComboBoxRegularWidget(
			label='Crit Type', box_ratio=100, label_ratio=8, sort_alphabetically=True, parent=self)
		self._convention_combobox.layout().setAlignment(self._convention_combobox.label, qt.Qt.AlignRight)
		self._rules_combobox = qt.ComboBoxRegularWidget(
			label='Rule Type', box_ratio=100, label_ratio=8, sort_alphabetically=True, parent=self)
		self._rules_combobox.layout().setAlignment(self._rules_combobox.label, qt.Qt.AlignRight)
		self._rule_expression_widget = stringedit.CompleterStringEdit('Rule', label_ratio=8, edit_ratio=100, parent=self)
		self._rule_expression_widget.layout().setAlignment(self._rule_expression_widget.label, qt.Qt.AlignRight)
		self._rule_preview_label = qt.label(text='Rule Preview: ', parent=self)
		self._tokens_widget = tokens.TokensWidget(parent=self)
		self._tokens_label = qt.LabelDivider('Fields', parent=self)
		self._save_cancel_button = qt.OkCancelButtons('Save', parent=self)
		self._rule_completer = qt.QCompleter([], parent=self)
		self._rule_expression_widget.edit.setCompleter(self._rule_completer)

		main_layout = qt.vertical_layout(margins=qt.consts.WINDOW_MARGINS, spacing=qt.consts.WINDOW_SPACING)
		self.set_main_layout(main_layout)

		convention_widget = qt.QWidget(parent=self)
		convention_layout = qt.vertical_layout(parent=convention_widget)
		convention_layout.addWidget(self._convention_combobox)
		convention_layout.addWidget(self._rules_combobox)
		convention_layout.addWidget(self._rule_expression_widget)
		convention_layout.addWidget(self._rule_preview_label)
		convention_layout.addWidget(self._tokens_label)
		convention_layout.addWidget(self._tokens_widget, 1)
		convention_layout.addWidget(self._tokens_widget, 1)

		splitter = qt.QSplitter(qt.Qt.Horizontal, parent=self)
		splitter.addWidget(self._presets_view)
		splitter.addWidget(convention_widget)
		main_layout.addWidget(splitter, 1)
		main_layout.addWidget(self._save_cancel_button, 0, qt.Qt.AlignBottom)

	@override
	def setup_signals(self):
		super().setup_signals()

		self._presets_view.selectionChanged.connect(self._on_preset_selection_changed)
		self._presets_view._preset_model.dataChanged.connect(self._on_preset_data_changed)
		self._convention_combobox.currentIndexChanged.connect(self._on_convention_type_index_changed)
		self._rules_combobox.currentIndexChanged.connect(self._on_rules_type_index_changed)
		self._rule_expression_widget.textChanged.connect(self._on_rule_expression_text_changed)

	def enable_state(self, preset: bool = True):
		"""
		Enable all the widgets based on given argumenet.

		:param bool preset: whether to enable preset related widgets.
		"""

		to_enable = [self._convention_combobox] if preset else [
			self._rules_combobox, self._rule_preview_label, self._rule_expression_widget, self._tokens_widget,
			self._tokens_label
		]
		[w.setEnabled(True) for w in to_enable]

	def disable_state(self):
		"""
		Disables all the widgets.
		"""

		to_disable = [
			self._convention_combobox, self._rules_combobox, self._rule_preview_label, self._rule_expression_widget,
			self._tokens_widget, self._tokens_label]
		[w.setEnabled(False) for w in to_disable]

	def set_preview_rule_text(self, text: str):
		"""
		Sets the preview text to show.

		:param str text: preview rule text.
		"""

		self._rule_preview_label.setText(f'<b>Rule Preview:</b> <i>{text}</i>')

	def _init_preset_tree(self):
		"""
		Internal function that initializes preset tree data.
		"""

		crit_config = crit.Configuration()
		self._ui_state.presets_manager = crit.namingpresets.PresetsManager()
		self._ui_state.original_manager = crit.namingpresets.PresetsManager()
		self._ui_state.crit_config = crit_config
		try:
			component_types = list(crit_config.components_manager().components.keys())
		except AttributeError:
			# component managers are only available for DCCs
			component_types = list()
		self._ui_state.presets_manager.update_available_naming_managers(component_types)
		self._ui_state.original_manager.update_available_naming_managers(component_types)
		hierarchy = self._ui_state.presets_manager.preferences_interface.naming_preset_hierarchy()
		self._ui_state.presets_manager.load_from_hierarchy(hierarchy)
		self._ui_state.original_manager.load_from_hierarchy(hierarchy)
		root = self._ui_state.presets_manager.root_preset
		if root is not None:
			self._presets_view.load_preset(root, include_root=self._ui_state.is_admin, parent=None)

	def _load_preset(self, preset_name: str):
		"""
		Internal function that loads preset with given name and updates UI with preset data.

		:param str preset_name: name of the preset to load.
		"""

		self._ui_state.current_preset = self._ui_state.presets_manager.find_preset(preset_name)
		self._update_naming_managers()

	def _update_naming_managers(self):
		"""
		Internal function that updates naming manager types.
		"""

		types = sorted(list(self._ui_state.presets_manager.available_naming_manager_types()))
		local_types = {i.crit_type for i in self._ui_state.current_preset.managers_data}

		self._convention_combobox.blockSignals(True)
		self._convention_combobox.clear()
		try:
			for global_type in types:
				self._convention_combobox.add_item(global_type, user_data=global_type in local_types)
		finally:
			self._convention_combobox.blockSignals(False)
		self._on_convention_type_index_changed(0)

	def _update_rule_types(self):

		global_rules = list(sorted(self._ui_state.current_naming_manager.iterate_rules(recursive=True), key=lambda x: x.name))
		local_rules = list(self._ui_state.current_naming_manager.iterate_rules(recursive=False))
		self._rules_combobox.blockSignals(True)
		try:
			self._rules_combobox.clear()
			for global_rule in global_rules:
				self._rules_combobox.add_item(global_rule.name, user_data=global_rule in local_rules)
		finally:
			self._rules_combobox.blockSignals(False)

		self._on_rules_type_index_changed(0)

	def _reset_current_rule(self):
		"""
		Internal function that updates UI taking into account current rule.
		"""

		current_rule_name = self._rules_combobox.current_text()
		name_manager = self._ui_state.current_naming_manager
		rule = name_manager.rule(current_rule_name, recursive=True)
		rule_tokens = rule.example_tokens
		token_values = dict(rule.example_tokens)
		rule_tokens_line_edit = {}
		for token_name in rule_tokens:
			found_token = name_manager.token(token_name)
			rule_tokens_line_edit[token_name] = token_name
			if found_token is None:
				continue
			random_token_int = random.randrange(0, found_token.count())
			key_value = list(found_token.iterate_key_values())[random_token_int]
			token_values[token_name] = key_value.value
		self._rule_expression_widget.set_text(name_manager.resolve(rule.name, rule_tokens_line_edit))
		self._rule_completer.setModel(qt.QStringListModel(rule_tokens.keys()))
		self.set_preview_rule_text(name_manager.resolve(current_rule_name, token_values))

	def _update_preview_rule_label(self) -> Tuple[Dict[str, List[str]], str]:
		"""
		Internal function that updates preview rule label.

		:return: tuple with the preview token values and the final preview text.
		:rtype: Tuple[Dict[str, List[str]], str]
		"""

		current_rule_name = self._rules_combobox.current_text()
		name_manager = self._ui_state.current_naming_manager
		rule = name_manager.rule(current_rule_name, recursive=True)
		rule_tokens = rule.tokens()
		token_values = dict(rule.example_tokens)
		for token_name in rule_tokens:
			found_token = name_manager.token(token_name)
			if found_token is None:
				continue
			random_token_int = random.randrange(0, found_token.count())
			key_value = list(found_token.iterate_key_values())[random_token_int]
			token_values[token_name] = key_value.value
		preview_label = name_manager.resolve(current_rule_name, token_values)
		self.set_preview_rule_text(preview_label)

		return token_values, preview_label

	def _on_preset_selection_changed(self, event: presets.PresetView.ExtendedTreeViewSelectionChangedEvent):
		"""
		Internal callback function that is called each time a preset is selected in preset view.

		:param naming.PresetView.ExtendedTreeViewSelectionChangedEvent event: selection event.
		"""

		for selection in event.current_items:
			preset_name = selection.data(0)
			self._load_preset(preset_name)
			break

		self.enable_state(True)

	def _on_preset_data_changed(self, top_left, bottom_right, roles):
		print('data changed ...')

	def _on_convention_type_index_changed(self, index: int):
		"""
		Internal callback function that is called each time the Crit type convention combobox index changes.

		:param int index: crit type index.
		"""

		self._convention_combobox.item_data(index, qt.Qt.UserRole)
		requested_convention = self._convention_combobox.current_text()
		is_local = self._convention_combobox.current_data(qt.Qt.UserRole)
		naming_manager = self._ui_state.current_preset.find_name_manager_for_type(requested_convention)

		if not is_local:
			# create naming manager in memory, so we do not modify the original one
			rules = [i.serialize() for i in naming_manager.iterate_rules(recursive=True)]
			tokens = [i.serialize() for i in naming_manager.iterate_tokens(recursive=True)]
			naming_manager = self._ui_state.current_preset.create_name_manager_data(
				name=None, crit_type=requested_convention, tokens=tokens, rules=rules).manager
			self._convention_combobox.set_item_data(index, True)		# we mark combobox as local
			self._ui_state.preset_operations.add_create_operation(self._ui_state.current_preset, requested_convention)
			self._ui_state.requires_save = True
		else:
			self._ui_state.preset_operations.add_create_operation(self._ui_state.current_preset, requested_convention)
			self._ui_state.requires_save = True
			naming_manager.set_tokens(copy.deepcopy(set(naming_manager.iterate_tokens(recursive=True))))

		self._ui_state.current_naming_manager = naming_manager
		self._update_rule_types()
		self._tokens_widget.reload_from_name_manager(self._ui_state.current_naming_manager)
		self.enable_state(False)

	def _on_rules_type_index_changed(self, index: int):
		"""
		Internal callback function that is called each time rule combobox index changes.

		:param int index: rule index.
		"""

		self._reset_current_rule()

	def _on_rule_expression_text_changed(self, text: str):
		"""
		Internal callback function that is called when rule expression text changes.

		:param str text: rule expression text.
		"""

		current_rule_name = self._rules_combobox.current_text()
		name_manager = self._ui_state.current_naming_manager
		if name_manager.has_rule(current_rule_name, recursive=False):
			current_rule = name_manager.rule(current_rule_name)
		else:
			parent_rule = name_manager.rule(current_rule_name)
			current_rule = name_manager.add_rule(recursive=False, **parent_rule.serialize())

		tokens = current_rule.example_tokens
		expression = []
		for token in text.split('_'):
			has_token = tokens.get(token)
			expression.append(token if not has_token else crit.namingpresets.surround_text_as_token(token))
		name_manager.rule(current_rule_name).expression = '_'.join(expression)
		self._update_preview_rule_label()
