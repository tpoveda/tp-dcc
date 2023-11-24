from __future__ import annotations

from tp.common.qt import api as qt
from tp.common.resources import api as resources
from tp.tools.rig.frag.core import blueprint


class BuildToolbar(qt.QWidget):
    def __init__(self, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._is_state_dirty = False
        self._blueprint_model = blueprint.BlueprintModel.get()

        self._setup_widgets()
        self._setup_layouts()

        self._clean_state()

        self._setup_signals()

    def _setup_widgets(self):
        """
        Internal function that setup view widgets.
        """

        self._main_stack = qt.sliding_opacity_stacked_widget(parent=self)

        self._new_page = qt.QWidget(parent=self)
        self._new_blueprint_button = qt.base_button('New Blueprint', parent=self)

        self._opened_page = qt.QWidget(parent=self)
        self._mode_frame = qt.QFrame(parent=self)
        self._mode_frame.setFrameShape(qt.QFrame.StyledPanel)
        self._mode_frame.setFrameShadow(qt.QFrame.Raised)
        self._validate_button = qt.base_button(
            'Validate', icon=resources.icon('validate', extension='svg'), icon_size=14, min_width=80,
            status_tip='Run validation on the blueprint and all actions.', parent=self)
        self._validate_button = qt.base_button(
            'Build', icon=resources.icon('build', extension='svg'), icon_size=14, min_width=80,
            status_tip='Save the blueprint and scene and build the rig.', parent=self)

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
        buttons_layout = qt.horizontal_layout(spacing=2, margins=(0, 0, 0, 0))
        buttons_layout.addWidget(self._validate_button)
        mode_frame_layout.addLayout(buttons_layout)
        opened_page_layout.addWidget(self._mode_frame)

        main_layout.addWidget(self._main_stack)

    def _setup_signals(self):
        """
        Internal function that setup node signals.
        """

        self._blueprint_model.rigExistsChanged.connect(self._on_rig_exists_changed)

        self._new_blueprint_button.clicked.connect(self._blueprint_model.new_file)

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

    def _on_rig_exists_changed(self):
        """
        Internal callback function that is called each time the presence of a built rig has changed.
        :return:
        """

        pass
