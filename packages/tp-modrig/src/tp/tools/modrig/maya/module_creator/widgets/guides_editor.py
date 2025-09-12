from __future__ import annotations

import typing

from Qt.QtWidgets import QWidget

from tp.libs import qt
from tp.libs.qt.widgets import TreeModel, TreeViewWidget

if typing.TYPE_CHECKING:
    from ..model import ModuleCreatorModel


class GuidesEditorWidget(QWidget):
    """Editor widget for managing guides in a rig module."""

    def __init__(self, model: ModuleCreatorModel, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._model = model

        self._setup_widgets()
        self._setup_layouts()
        self._setup_signals()

    def _setup_widgets(self):
        """Set up the widgets for the editor."""

        self._tree_view_widget = GuidesTreeView(parent=self)
        self._create_guide_button = qt.factory.styled_button(
            button_icon=qt.icon("plus_circle"),
            style=qt.uiconsts.ButtonStyles.TransparentBackground,
            tooltip="Create New Guide",
            theme_updates=False,
        )

        self._tree_view_widget.toolbar_layout.addWidget(self._create_guide_button)

    def _setup_layouts(self):
        """Set up the layouts for the editor."""

        main_layout = qt.factory.vertical_layout()
        self.setLayout(main_layout)

        main_layout.addWidget(self._tree_view_widget)

    def _setup_signals(self):
        """Set up the signals for the editor."""

        self._create_guide_button.leftClicked.connect(
            self._model.create_guide_for_current_module
        )


class GuidesTreeView(TreeViewWidget):
    def __init__(
        self,
        expand: bool = True,
        sorting: bool = True,
        parent: QWidget | None = None,
    ):
        super().__init__(title="", expand=expand, sorting=sorting, parent=parent)
