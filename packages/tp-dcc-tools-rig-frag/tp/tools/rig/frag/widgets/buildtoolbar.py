from __future__ import annotations

from typing import Any

from overrides import override

from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.libs.rig.frag.core import blueprint as bp
from tp.tools.rig.frag.core import blueprint
from tp.tools.rig.frag.editors import settings


class BuildToolbar(qt.QWidget):
    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._is_state_dirty = False
        self._blueprint_model = blueprint.BlueprintModel.get()

        self._setup_widgets()
        self._setup_layouts()

        self._clean_state()
        self._update_mode()

        self._setup_signals()

    @override
    def showEvent(self, event: qt.QShowEvent) -> None:
        super().showEvent(event)
        if not self._is_state_dirty:
            self._is_state_dirty = True
            self.setEnabled(False)
            # cmds.evalDeferred(self._clean_state)
            # TODO: This should be executed in a deferred way
            self._clean_state()

    def _setup_widgets(self):
        """
        Internal function that setup view widgets.
        """

        self._main_stack = qt.sliding_opacity_stacked_widget(parent=self)

        self._new_page = qt.QWidget(parent=self)
        self._new_blueprint_button = qt.base_button('New Blueprint', parent=self)

        self._opened_page = qt.QWidget(parent=self)
        self._blueprint_file_name_label = qt.label('<Blueprint File Name>', parent=self)
        self._blueprint_file_name_label.setProperty('cssClasses', 'subtitle')
        self._rig_name_label = qt.label('<Rig Name>', parent=self)
        self._rig_name_label.setProperty('cssClasses', 'help')
        self._blueprint_mode_label = qt.label('Blueprint', parent=self)
        self._blueprint_mode_label.setProperty('cssClasses', 'mode-title')
        self._divider_label = qt.label('|', parent=self)
        self._rig_mode_label = qt.label('Rig', parent=self)
        self._rig_mode_label.setProperty('cssClasses', 'mode-title')
        self._mode_frame = qt.QFrame(parent=self)
        self._mode_frame.setFrameShape(qt.QFrame.StyledPanel)
        self._mode_frame.setFrameShadow(qt.QFrame.Raised)

        self._validate_button = qt.base_button(
            'Validate', icon=resources.icon('validate', extension='svg', key='tp-dcc-tools-rig-frag'), icon_size=14,
            min_width=80, status_tip='Run validation on the blueprint and all actions.', parent=self)
        self._build_button = qt.base_button(
            'Build', icon=resources.icon('build', extension='svg', key='tp-dcc-tools-rig-frag'), icon_size=14,
            min_width=80, status_tip='Save the blueprint and scene and build the rig.', parent=self)
        self._open_blueprint_button = qt.base_button(
            'Open Blueprint', icon=resources.icon('angle_left', extension='svg', key='tp-dcc-tools-rig-frag'),
            icon_size=14, min_width=80, status_tip='Open the blueprint scene that built this rig.', parent=self)
        self._interactive_building_frame = qt.QFrame(parent=self)
        self._interactive_building_frame.setFrameShape(qt.QFrame.StyledPanel)
        self._interactive_building_frame.setFrameShadow(qt.QFrame.Raised)
        self._next_action_button = qt.base_button(
            'Next Step', icon=resources.icon('forward_step', extension='svg', key='tp-dcc-tools-rig-frag'),
            icon_size=14, min_width=80, status_tip='Run the next action of the interactive build.', parent=self)
        self._next_step_button = qt.base_button(
            'Next Action', icon=resources.icon('forward_step', extension='svg', key='tp-dcc-tools-rig-frag'),
            icon_size=14, min_width=80, status_tip='Skip to the next step of the interactive build.', parent=self)
        self._continue_button = qt.base_button(
            'Continue', icon=resources.icon('build', extension='svg', key='tp-dcc-tools-rig-frag'), icon_size=14,
            min_width=80, status_tip='Continue to the interactive build to the end.', parent=self)

        self._toolbar_frame = qt.QFrame(parent=self)
        self._toolbar_frame.setFrameShape(qt.QFrame.StyledPanel)
        self._toolbar_frame.setFrameShadow(qt.QFrame.Raised)
        self._toolbar_frame.setProperty('cssClasses', 'toolbar')
        self._settings_button = qt.base_button(
            'Settings', icon=resources.icon('gear', extension='svg', key='tp-dcc-tools-rig-frag'), icon_size=14,
            min_width=80, parent=self)
        self._action_editor_button = qt.base_button(
            'Action Editor', icon=resources.icon('action_editor', extension='svg', key='tp-dcc-tools-rig-frag'),
            icon_size=14, min_width=80, parent=self)

        self._main_stack.addWidget(self._new_page)
        self._main_stack.addWidget(self._opened_page)

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        main_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        new_page_layout = qt.vertical_layout(spacing=2, margins=(0, 0, 0, 0))
        self._new_page.setLayout(new_page_layout)
        new_page_layout.addWidget(self._new_blueprint_button)

        opened_page_layout = qt.vertical_layout(spacing=2, margins=(0, 0, 0, 0))
        self._opened_page.setLayout(opened_page_layout)
        mode_frame_layout = qt.vertical_layout(spacing=2, margins=(0, 0, 0, 0))
        self._mode_frame.setLayout(mode_frame_layout)
        top_layout = qt.horizontal_layout(spacing=2, margins=(2, 2, 2, 2))
        blueprint_rig_name_layout = qt.vertical_layout(spacing=2, margins=(0, 0, 0, 0))
        blueprint_rig_name_layout.addWidget(self._blueprint_file_name_label)
        blueprint_rig_name_layout.addWidget(self._rig_name_label)
        top_layout.addLayout(blueprint_rig_name_layout)
        top_layout.addWidget(self._blueprint_mode_label)
        top_layout.addWidget(self._divider_label)
        top_layout.addWidget(self._rig_mode_label)
        top_layout.setStretch(0, 1)
        buttons_layout = qt.horizontal_layout(spacing=2, margins=(0, 0, 0, 0))
        buttons_layout.addWidget(self._validate_button)
        buttons_layout.addWidget(self._build_button)
        buttons_layout.addWidget(self._open_blueprint_button)
        interactive_buttons_layout = qt.horizontal_layout(spacing=2, margins=(0, 0, 0, 0))
        self._interactive_building_frame.setLayout(interactive_buttons_layout)
        interactive_buttons_layout.addWidget(self._next_action_button)
        interactive_buttons_layout.addWidget(self._next_step_button)
        interactive_buttons_layout.addWidget(self._continue_button)
        mode_frame_layout.addLayout(top_layout)
        mode_frame_layout.addLayout(buttons_layout)
        mode_frame_layout.addWidget(self._interactive_building_frame)
        opened_page_layout.addWidget(self._mode_frame)

        toolbar_layout = qt.horizontal_layout(spacing=2, margins=(0, 0, 0, 0))
        self._toolbar_frame.setLayout(toolbar_layout)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._settings_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._action_editor_button)
        toolbar_layout.addStretch()

        main_layout.addWidget(self._main_stack)
        main_layout.addWidget(self._toolbar_frame)

    def _setup_signals(self):
        """
        Internal function that setup node signals.
        """

        self._blueprint_model.fileChanged.connect(self._on_file_changed)
        self._blueprint_model.isFileModifiedChanged.connect(self._on_file_modified_changed)
        self._blueprint_model.rigExistsChanged.connect(self._on_rig_exists_changed)
        self._blueprint_model.settingChanged.connect(self._on_setting_changed)
        self._blueprint_model.readOnlyChanged.connect(self._on_read_only_changed)
        self._new_blueprint_button.clicked.connect(self._blueprint_model.new_file)

        self._validate_button.clicked.connect(self._blueprint_model.run_validation)

        self._settings_button.clicked.connect(self._on_settings_button_clicked)

    def _clean_state(self):
        """
        Internal function that clean build toolbar state.
        """

        self._is_state_dirty = False
        self.setEnabled(True)

    def _update_mode(self):
        """
        Internal function that updates the UI based on whether there is a blueprint or rig available.
        """

        # Prevent mode changes while changing scenes to avoid flickering since a file may be briefly closed
        # before a new one is opened.
        if self._blueprint_model.is_changing_scenes:
            return

        if self._blueprint_model.is_file_open():
            self._main_stack.setCurrentWidget(self._opened_page)
        else:
            self._main_stack.setCurrentWidget(self._new_page)

        if self._blueprint_model.does_rig_exist:
            self._validate_button.setEnabled(False)
            self._build_button.setEnabled(False)
            self._open_blueprint_button.setEnabled(True)
            self._blueprint_mode_label.setEnabled(False)
            self._rig_mode_label.setEnabled(True)
            self._mode_frame.setProperty('cssClasses', 'toolbar-rig')
        else:
            self._validate_button.setEnabled(True)
            self._build_button.setEnabled(True)
            self._open_blueprint_button.setEnabled(False)
            self._blueprint_mode_label.setEnabled(True)
            self._rig_mode_label.setEnabled(False)
            self._mode_frame.setProperty('cssClasses', 'toolbar-blueprint')

        self._interactive_building_frame.setVisible(self._blueprint_model.is_interactive_building())

        self._mode_frame.setStyleSheet('')

    def _update_rig_name(self):
        """
        Internal function that updates UI based on current rig name.
        """

        # Prevent mode changes while changing scenes to avoid flickering since a file may be briefly closed
        # before a new one is opened.
        if self._blueprint_model.is_changing_scenes:
            return

        file_name = self._blueprint_model.blueprint_file_name()
        file_name = file_name if file_name is not None else 'untitled'
        file_name = file_name if not self._blueprint_model.is_file_modified() else f'{file_name}*'

        self._rig_name_label.setText(self._blueprint_model.setting(bp.BlueprintSettings.RigName))
        self._blueprint_file_name_label.setText(file_name)
        self._blueprint_file_name_label.setToolTip(self._blueprint_model.blueprint_file_path())

    def _on_file_changed(self):
        """
        Internal callback function that is called each time current blueprint file is created, opened or saved.
        """

        self._update_mode()
        self._update_rig_name()

    def _on_file_modified_changed(self):
        """
        Internal callback function that is called each time blueprint file is modified within the model.
        """

        self._update_rig_name()

    def _on_rig_exists_changed(self):
        """
        Internal callback function that is called each time the presence of a built rig has changed.
        """

        self._clean_state()
        self._update_mode()

    def _on_setting_changed(self, key: str, value: Any):
        """
        Internal callback function that is called each time a blueprint model setting changes.

        :param str key: setting key.
        :param Any value: setting value.
        """

        if key == bp.BlueprintSettings.RigName:
            self._update_rig_name()

    def _on_read_only_changed(self, flag: bool):
        """
        Internal callback function that is called each time blueprint model read only status changes.

        :param bool flag: True if blueprint is in ready only mode; False otherwise.
        """

        pass

    def _on_settings_button_clicked(self):
        """
        Internal callback function that is called when Settings button is clicked by the user.
        Opens FRAG settings editor.
        """

        settings_window = settings.FragSettingsWindow()
        settings_window.show()
