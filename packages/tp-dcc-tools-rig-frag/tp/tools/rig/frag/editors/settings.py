from __future__ import annotations

from typing import Any

from overrides import override

from tp.common.qt import api as qt
from tp.libs.rig.frag.core import action, blueprint as bp
from tp.tools.rig.frag.core import blueprint


class FragSettingsWindow(qt.FramelessWindow):

    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(title='FRAG Settings', parent=parent)

        self.resize(600, 400)

    @override
    def setup_widgets(self):
        super().setup_widgets()

        self._settings_widget = FragSettings(parent=self)

    @override
    def setup_layouts(self):
        super().setup_layouts()

        main_layout = self.set_main_layout(qt.vertical_layout(spacing=2, margins=(0, 0, 0, 0)))
        main_layout.addWidget(self._settings_widget)


class FragSettings(qt.QWidget):
    """
    Panel that displays FRAG general and blueprint settings.
    """

    def __init__(self, parent: FragSettingsWindow | None = None):
        super().__init__(parent=parent)

        self._blueprint_model = blueprint.BlueprintModel.get()
        self._model = self._blueprint_model.build_step_tree_model

        self._setup_widgets()
        self._setup_layouts()
        self._update_all_setting_values()
        self._setup_signals()

        self._tab_widget.setEnabled(not self._blueprint_model.is_read_only())

    def _setup_widgets(self):
        """
        Internal function that creates all UI widgets.
        """

        self._tab_widget = qt.QTabWidget(parent=self)

        self._blueprint_tab_widget = qt.QWidget(parent=self)
        self._file_label = qt.label('File', properties=[('cssClasses', 'section-title')], parent=self)
        self._file_path_label = qt.label(
            'File Path', alignment=qt.Qt.AlignRight | qt.Qt.AlignTrailing | qt.Qt.AlignVCenter, min_width=120,
            status_tip='The path to the currently open blueprint.', parent=self)
        self._file_path_text_label = qt.label('<File Path>', parent=self)
        self._file_path_text_label.setTextInteractionFlags(
            qt.Qt.TextSelectableByMouse | qt.Qt.LinksAccessibleByMouse)
        self._blueprint_spacer_item = qt.QSpacerItem(20, 20)
        self._settings_label = qt.label('Settings', properties=[('cssClasses', 'section-title')], parent=self)
        self._rig_name_label = qt.label(
            'Rig Name', alignment=qt.Qt.AlignRight | qt.Qt.AlignTrailing | qt.Qt.AlignVCenter, min_width=120,
            status_tip='The name of the rig. Used to name the core hierarchy nodes and can be used by actions as well.',
            parent=self)
        self._rig_name_edit = qt.line_edit(parent=self)
        self._rig_node_name_label = qt.label(
            'Rig Node Name', alignment=qt.Qt.AlignRight | qt.Qt.AlignTrailing | qt.Qt.AlignVCenter, min_width=120,
            status_tip='The naming format to use for the parent rig node. Can use any settings key, such as {rigName}.',
            parent=self)
        self._rig_node_name_format_edit = qt.line_edit(parent=self)
        self._debug_build_label = qt.label(
            'Debug Build', alignment=qt.Qt.AlignRight | qt.Qt.AlignTrailing | qt.Qt.AlignVCenter, min_width=120,
            parent=self)
        self._debug_build_check = qt.checkbox(parent=self)
        self._blueprint_help_label = qt.label(
            'Settings for the current blueprint.', properties=[('cssClasses', 'help')], parent=self)

        self._general_tab_widget = qt.QWidget(parent=self)
        self._config_label = qt.label('Settings', properties=[('cssClasses', 'section-title')], parent=self)
        self._config_file_label = qt.label(
            'Config File', alignment=qt.Qt.AlignRight | qt.Qt.AlignTrailing | qt.Qt.AlignVCenter, min_width=120,
            status_tip='The global config that affects overall settings and behavior.', parent=self)
        self._config_file_path_text_label = qt.label('<File Path>', parent=self)
        self._config_file_path_text_label.setTextInteractionFlags(
            qt.Qt.TextSelectableByMouse | qt.Qt.LinksAccessibleByMouse)
        self._general_spacer_item = qt.QSpacerItem(20, 20)
        self._action_packages_label = qt.label(
            'Action Packages', properties=[('cssClasses', 'section-title')], parent=self)
        self._action_packages = ActionPackagesList(parent=self)
        self._general_help_label = qt.label(
            'General settings that affect all Blueprints.', properties=[('cssClasses', 'help')], parent=self)

        self._tab_widget.addTab(self._blueprint_tab_widget, 'Blueprint')
        self._tab_widget.addTab(self._general_tab_widget, 'General')

    def _setup_layouts(self):

        main_layout = qt.vertical_layout(spacing=2, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        main_layout.addWidget(self._tab_widget)

        blueprint_widget_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self._blueprint_tab_widget.setLayout(blueprint_widget_layout)
        blueprint_form_layout = qt.form_layout(spacing=2, margins=(0, 0, 0, 0))
        blueprint_form_layout.setWidget(0, qt.QFormLayout.SpanningRole, self._file_label)
        blueprint_form_layout.setWidget(1, qt.QFormLayout.LabelRole, self._file_path_label)
        blueprint_form_layout.setWidget(1, qt.QFormLayout.FieldRole, self._file_path_text_label)
        blueprint_form_layout.setItem(2, qt.QFormLayout.SpanningRole, self._blueprint_spacer_item)
        blueprint_form_layout.setWidget(3, qt.QFormLayout.SpanningRole, self._settings_label)
        blueprint_form_layout.setWidget(4, qt.QFormLayout.LabelRole, self._rig_name_label)
        blueprint_form_layout.setWidget(4, qt.QFormLayout.FieldRole, self._rig_name_edit)
        blueprint_form_layout.setWidget(5, qt.QFormLayout.LabelRole, self._rig_node_name_label)
        blueprint_form_layout.setWidget(5, qt.QFormLayout.FieldRole, self._rig_node_name_format_edit)
        blueprint_form_layout.setWidget(6, qt.QFormLayout.LabelRole, self._debug_build_label)
        blueprint_form_layout.setWidget(6, qt.QFormLayout.FieldRole, self._debug_build_check)
        blueprint_widget_layout.addLayout(blueprint_form_layout)
        blueprint_widget_layout.addStretch()
        blueprint_widget_layout.addWidget(self._blueprint_help_label)

        general_widget_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self._general_tab_widget.setLayout(general_widget_layout)
        general_form_layout = qt.form_layout(spacing=2, margins=(0, 0, 0, 0))
        general_form_layout.setWidget(0, qt.QFormLayout.SpanningRole, self._config_label)
        general_form_layout.setWidget(1, qt.QFormLayout.LabelRole, self._config_file_label)
        general_form_layout.setWidget(1, qt.QFormLayout.FieldRole, self._config_file_path_text_label)
        general_form_layout.setItem(2, qt.QFormLayout.SpanningRole, self._general_spacer_item)
        general_form_layout.setWidget(3, qt.QFormLayout.SpanningRole, self._action_packages_label)
        general_form_layout.setWidget(4, qt.QFormLayout.SpanningRole, self._action_packages)
        general_widget_layout.addLayout(general_form_layout)
        general_widget_layout.addStretch()
        general_widget_layout.addWidget(self._general_help_label)

    def _setup_signals(self):

        self._blueprint_model.fileChanged.connect(self._on_file_changed)
        self._blueprint_model.settingChanged.connect(self._on_setting_changed)
        self._blueprint_model.readOnlyChanged.connect(self._on_read_only_changed)

        self._rig_name_edit.textEdited.connect(self._rig_name_text_edited)
        self._rig_node_name_format_edit.textEdited.connect(self._on_rig_node_format_text_edited)
        self._debug_build_check.stateChanged.connect(self._on_debug_build_state_changed)

    def _rig_name_text_edited(self):
        """
        Internal callback function that is called each time rig name line edit is edited by the user.
        """

        self._blueprint_model.set_setting(bp.BlueprintSettings.RigName, self._rig_name_edit.text())

    def _on_rig_node_format_text_edited(self):
        """
        Internal callback function that is called each time rig node format line edit is edited by the user.
        """

        self._blueprint_model.set_setting(
            bp.BlueprintSettings.RigNodeNameFormat, self._rig_node_name_format_edit.text())

    def _on_debug_build_state_changed(self):
        """
        Internal callback function that is called each time debug build checkbox is toggled by the user.
        """

        self._blueprint_model.set_setting(bp.BlueprintSettings.DebugBuild, self._debug_build_check.isChecked())

    def _update_all_setting_values(self):
        """
        Internal function that updates UI based on current blueprint model setting values.
        """

        self._file_path_text_label.setText(self._blueprint_model.blueprint_file_path())
        self._config_file_path_text_label.setText(self._blueprint_model.blueprint.config_file_path)

        self._rig_name_edit.setText(self._blueprint_model.setting(bp.BlueprintSettings.RigName))
        self._rig_node_name_format_edit.setText(self._blueprint_model.setting(bp.BlueprintSettings.RigNodeNameFormat))

    def _on_file_changed(self):
        """
        Internal callback function that is called each time current blueprint file is created, opened or saved.
        """

        self._file_path_text_label.setText(self._blueprint_model.blueprint_file_path())
        self._update_all_setting_values()

    def _on_setting_changed(self, key: str, value: Any):
        """
        Internal callback function that is called each time a blueprint model setting changes.

        :param str key: setting key.
        :param Any value: setting value.
        """

        if key == bp.BlueprintSettings.RigName:
            self._rig_name_edit.setText(str(value))
        elif key == bp.BlueprintSettings.RigNodeNameFormat:
            self._rig_node_name_format_edit.setText(str(value))

    def _on_read_only_changed(self, flag: bool):
        """
        Internal callback function that is called each time blueprint model read only status changes.

        :param bool flag: True if blueprint is in ready only mode; False otherwise.
        """

        self._tab_widget.setEnabled(not flag)


class ActionPackagesList(qt.QWidget):
    """
    Custom settings widget that displays the list of action packages in the BuildAcitonPackageRegistry.
    """

    def __init__(self, parent: FragSettings | None = None):
        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()

    @override
    def showEvent(self, event: qt.QShowEvent) -> None:
        super().showEvent(event)
        self.refresh()

    def refresh(self):
        """
        Updates packages list.
        """

        try:
            self._tree_widget.clear()

            actions_registry = action.BuildActionPackageRegistry()

            for package in actions_registry.action_packages:
                package_item = qt.QTreeWidgetItem([package.__name__, package.__path__[0]])
                self._tree_widget.addTopLevelItem(package_item)
        except AttributeError:
            pass

    def _setup_widgets(self):
        """
        Internal function that creates all UI widgets.
        """

        self.refresh()

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        main_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        self._tree_widget = qt.QTreeWidget(parent=self)
        self._tree_widget.setHeaderLabels(['Name', 'Path'])
        main_layout.addWidget(self._tree_widget)
