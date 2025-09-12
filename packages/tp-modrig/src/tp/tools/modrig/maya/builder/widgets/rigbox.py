from __future__ import annotations

from Qt.QtCore import Qt, Signal
from Qt.QtWidgets import QWidget, QComboBox

from tp.libs import qt


class RigBoxWidget(QWidget):
    """Widget that shows a combo box with the available rigs and buttons to add,
    rename and delete rigs.
    """

    rigSelected = Signal(str)
    addRigClicked = Signal()
    renameRigClicked = Signal()
    deleteRigClicked = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

        self.setFixedHeight(qt.dpi_scale(24))

    def disable_edit_buttons(self) -> None:
        """Disables the edit buttons."""

        self._rename_rig_button.setEnabled(False)
        self._delete_rig_button.setEnabled(False)

    def enable_edit_buttons(self) -> None:
        """Enables the edit buttons."""

        self._rename_rig_button.setEnabled(True)
        self._delete_rig_button.setEnabled(True)

    def set_rigs(self, rig_names: list[str]) -> None:
        """Sets the available rigs in the combo box.

        Args:
            rig_names: List of rig names to set in the combo box.
        """

        self._rig_combo.clear()
        self._rig_combo.addItems(rig_names)

    def set_current_rig(self, rig_name: str) -> None:
        """Sets the current rig in the combo box.

        Args:
            rig_name: Name of the rig to set as current.
        """

        index = self._rig_combo.findText(rig_name)
        if index != -1:
            self._rig_combo.setCurrentIndex(index)

    def _setup_widgets(self) -> None:
        """Set up the widgets for the widget."""

        self._rig_combo = QComboBox(parent=self)
        self._rig_combo.setMinimumWidth(qt.dpi_scale(150))

        self._create_rig_button = qt.factory.styled_button(
            button_icon=qt.icon("plus_circle"),
            style=qt.uiconsts.ButtonStyles.TransparentBackground,
            tooltip="Create New Rig",
            theme_updates=False,
        )
        self._rename_rig_button = qt.factory.styled_button(
            button_icon=qt.icon("pencil"),
            style=qt.uiconsts.ButtonStyles.TransparentBackground,
            tooltip="Rename Rig",
            theme_updates=False,
        )
        self._delete_rig_button = qt.factory.styled_button(
            button_icon=qt.icon("cancel_circle"),
            style=qt.uiconsts.ButtonStyles.TransparentBackground,
            tooltip="Delete Rig",
            theme_updates=False,
        )

    def _setup_layouts(self) -> None:
        """Set up the layouts for the widget."""

        main_layout = qt.factory.horizontal_layout(
            spacing=2, margins=(0, 0, 0, 0), alignment=Qt.AlignTop
        )
        self.setLayout(main_layout)

        main_layout.addWidget(self._rig_combo)
        main_layout.addWidget(self._create_rig_button)
        main_layout.addWidget(self._rename_rig_button)
        main_layout.addWidget(self._delete_rig_button)
        main_layout.setStretchFactor(self._rig_combo, 5)

    def _setup_signals(self) -> None:
        """Set up the signals for the widget."""

        self._rig_combo.currentTextChanged.connect(self.rigSelected.emit)
        self._create_rig_button.leftClicked.connect(
            self._on_add_rig_button_left_clicked
        )
        self._rename_rig_button.leftClicked.connect(
            self._on_rename_rig_button_left_clicked
        )
        self._delete_rig_button.leftClicked.connect(
            self._on_delete_rig_button_left_clicked
        )

    def _on_add_rig_button_left_clicked(self) -> None:
        """Callback called when the add rig button is clicked."""

        self.addRigClicked.emit()

    def _on_rename_rig_button_left_clicked(self) -> None:
        """Callback called when the rename rig button is clicked."""

        self.renameRigClicked.emit()

    def _on_delete_rig_button_left_clicked(self) -> None:
        """Callback called when the delete rig button is clicked."""

        self.deleteRigClicked.emit()
