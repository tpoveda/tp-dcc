from __future__ import annotations

import typing
from functools import wraps
from typing import Callable

from Qt.QtCore import Qt
from Qt.QtWidgets import (
    QApplication,
    QWidget,
    QMainWindow,
    QDockWidget,
    QPushButton,
    QMessageBox,
)

from tp.libs import qt
from tp.libs.qt.widgets import OverlayLoadingWidget
from tp.tools.modrig.maya.builder.plugins.editors.modules_library import (
    ModulesLibraryWidget,
)
from tp.tools.modrig.maya.builder.widgets.rigbox import RigBoxWidget

if typing.TYPE_CHECKING:
    from .model import ModuleCreatorModel
    from tp.tools.modrig.maya.builder.models import RigModel


class ModuleCreatorView(QWidget):
    def __init__(self, model: ModuleCreatorModel, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._model = model

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self):
        """Set up the widgets for the view."""

        self._main_window = QMainWindow()
        test = QPushButton("Test", self)
        self._main_window.setCentralWidget(test)
        self._main_widget = QWidget(parent=self)
        self._main_window.setCentralWidget(self._main_widget)

        self._rig_box = RigBoxWidget(parent=self)

        self._modules_library = ModulesLibraryWidget(
            modules_manager=self._model.modules_manager, parent=self
        )
        modules_library_dock = QDockWidget(parent=self)
        modules_library_dock.setWidget(self._modules_library)
        modules_library_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self._main_window.addDockWidget(Qt.LeftDockWidgetArea, modules_library_dock)

        self._loading_widget = OverlayLoadingWidget(parent=self._main_window)
        self._loading_widget.hide()

    def _setup_layouts(self):
        """Set up the layouts for the view."""

        main_layout = qt.factory.vertical_layout()
        self.setLayout(main_layout)

        main_widget_layout = qt.factory.vertical_layout()
        self._main_widget.setLayout(main_widget_layout)
        main_widget_layout.addWidget(self._rig_box)
        main_widget_layout.addStretch()

        main_layout.addWidget(self._main_window)

    def _setup_signals(self):
        """Set up the signals for the view."""

        self._model.listen("rigs", self._on_model_rigs_changed)
        self._model.listen("current_rig", self._on_model_current_rig_changed)

        self._rig_box.rigSelected.connect(self._model.set_current_rig_by_name)
        self._rig_box.addRigClicked.connect(self._model.add_rig)
        self._rig_box.deleteRigClicked.connect(self._on_rig_box_delete_rig_clicked)
        self._modules_library.moduleItemDoubleClicked.connect(self._model.add_module)

    # region === Loading ===

    @staticmethod
    def loading_decorator(func: Callable) -> Callable:
        """Decorator to show and hide the loading widget while executing a
        function.

        Args:
            func: The function to decorate.

        Returns:
            The decorated function.
        """

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                self.show_loading_widget()
                result = func(self, *args, **kwargs)
                return result
            finally:
                self.hide_loading_widget()

        return wrapper

    def show_loading_widget(self) -> None:
        """Show the loading widget."""

        self._loading_widget.show()
        QApplication.processEvents()

    def hide_loading_widget(self) -> None:
        """Hide the loading widget."""

        self._loading_widget.hide()
        QApplication.processEvents()

    # endregion

    # region  === Model Callbacks === #

    @loading_decorator
    def _on_model_rigs_changed(self, rigs: list[RigModel]) -> None:
        """Callback function called when the rigs in the model change.

        Args:
            rigs: The new list of rig models.
        """

        with qt.block_signals(self._rig_box, children=True):
            self._rig_box.set_rigs([rig.name for rig in rigs])

    def _on_model_current_rig_changed(self, current_rig: RigModel | None) -> None:
        """Callback function called when the current rig in the model changes.

        Args:
            current_rig: The new current rig model, or `None` if no rig is
                selected.
        """

        if current_rig is None:
            self._rig_box.disable_edit_buttons()
        else:
            self._rig_box.enable_edit_buttons()

            with qt.block_signals(self._rig_box, children=True):
                self._rig_box.set_current_rig(current_rig.name)

    # endregion

    # === UI Callbacks === #

    def _on_rig_box_delete_rig_clicked(self):
        current_rig = self._model.current_rig
        if current_rig is None:
            return

        result = QMessageBox.question(
            self,
            f'Delete "{current_rig.name}?"',
            f'Are you sure you want to delete "{current_rig.name}" rig?',
            buttons=QMessageBox.Yes | QMessageBox.Cancel,
        )
        if result != QMessageBox.Yes:
            return

        try:
            self.show_loading_widget()
            self._model.delete_current_rig()
        finally:
            self.hide_loading_widget()
