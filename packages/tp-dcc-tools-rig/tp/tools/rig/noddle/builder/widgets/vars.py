from __future__ import annotations

import typing

from tp.common.qt import api as qt
from tp.common.resources import api as resources

if typing.TYPE_CHECKING:
    from tp.tools.rig.noddle.builder.graph.core.scene import Scene
    from tp.tools.rig.noddle.builder.graph.core.vars import SceneVars
    from tp.tools.rig.noddle.builder.window import NoddleBuilderWindow


class SceneVarsWidget(qt.QWidget):

    JSON_DATA_ROLE = qt.Qt.UserRole + 1

    def __init__(self, main_window: NoddleBuilderWindow, parent: qt.QWidget | None = None):
        super().__init__(parent=parent or main_window)

        self._main_window = main_window

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    @property
    def variables_list_widget(self):
        return self._variables_list_widget

    @property
    def scene_vars(self) -> SceneVars | None:
        return self._main_window.current_editor.scene.vars if self._main_window.current_editor else None

    @property
    def attributes_editor(self):
        return self._main_window.attributes_editor

    def refresh(self):
        """
        Refreshes list of variable widgets.
        """

        self._variables_list_widget.populate()

    def _setup_widgets(self):
        """
        Internal function that creates all UI widgets.
        """

        self._variables_list_widget = VarsListWidget(self)
        self._add_variable_button = qt.base_button(icon=resources.icon('add'), parent=self)
        self._delete_variable_button = qt.base_button(icon=resources.icon('delete'), parent=self)

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        main_layout = qt.vertical_layout(spacing=0, margins=(0, 0, 0, 0))
        self.setLayout(main_layout)

        buttons_layout = qt.horizontal_layout(spacing=2, margins=(0, 0, 0, 0))
        buttons_layout.addWidget(self._add_variable_button)
        buttons_layout.addWidget(self._delete_variable_button)

        main_layout.addLayout(buttons_layout)
        main_layout.addWidget(self._variables_list_widget)

    def _setup_signals(self):
        """
        Internal function that connects all signals for this graph.
        """

        self._add_variable_button.clicked.connect(self._on_add_variable_button_clicked)
        self._delete_variable_button.clicked.connect(self._on_delete_variable_button_clicked)

    def _on_add_variable_button_clicked(self):
        """
        Internal callback function that is called each time user clicks Add Variable button.
        Adds a new variable.
        """

        pass

    def _on_delete_variable_button_clicked(self):
        """
        Internal callback function that is called each time user clicks Delete Variable button.
        Deletes an existing variable.
        """

        pass


class VarsListWidget(qt.QListWidget):

    variableRenamed = qt.Signal(qt.QListWidgetItem)

    PIXMAP_ROLE = qt.Qt.UserRole
    JSON_DATA_ROLE = qt.Qt.UserRole + 1

    def __init__(self, vars_widget: SceneVarsWidget, parent: qt.QWidget | None = None):
        super().__init__(parent=parent or vars_widget)

        self._vars_widget = vars_widget

        self.setSelectionMode(qt.QAbstractItemView.SingleSelection)
        self.setDragEnabled(True)

        self._setup_signals()

    def populate(self):
        """
        Fills list widget with all available variables.
        """

        self.clear()

    def _setup_signals(self):
        """
        Internal function that connects all signals for this graph.
        """

        pass


class VarAttributeWidget(qt.QGroupBox):

    dataTypeSwitched = qt.Signal(qt.QListWidgetItem, str)

    def __init__(self, list_item: qt.QListWidgetItem, scene: Scene, parent: qt.QWidget | None = None):
        super().__init__(parent=parent)

        self._list_item = list_item
        self._scene = scene

        json_data = self._list_item.data(VarsListWidget.JSON_DATA_ROLE)
        self._var_name = json_data['var_name']
        self.setTitle(f'Variable {self._var_name}')

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self):
        """
        Internal function that creates all UI widgets.
        """

        pass

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        pass

    def _setup_signals(self):
        """
        Internal function that connects all signals for this graph.
        """

        pass
