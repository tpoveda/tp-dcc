from __future__ import annotations

from loguru import logger
from Qt.QtCore import QObject
from Qt.QtWidgets import QWidget, QAbstractItemView

from tp.libs.qt.widgets import (
    TableViewWidget,
    TableModel,
    BaseDataSource,
    ColumnDataSource,
)
from tp.libs.qt import dpi
from tp.libs.qt import factory as qt


class PresetsTableWidget(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._table_controller: PresetsTableController | None = None

        self._setup_widgets()
        self._setup_layouts()

    @property
    def model(self) -> TableModel:
        """The model of the table widget."""

        return self._table_model

    @property
    def view(self) -> TableViewWidget:
        """The view of the table widget."""

        return self._table_view_widget

    def _setup_widgets(self):
        """Set up the widgets of the table widget."""

        self._table_view_widget = TableViewWidget(
            manual_reload=False, searchable=False, parent=self
        )
        self._table_model = TableModel(parent=self)
        self._table_view_widget.set_model(self._table_model)
        self._table_view_widget.table_view.verticalHeader().hide()
        self._table_view_widget.table_view.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self._table_view_widget.table_view.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )

    def set_controller(self, controller: PresetsTableController):
        """Set the controller of the table widget."""

        if self._table_controller is not None:
            logger.warning("Controller already set. Skipping...")
            return

        self._table_controller = controller

        self._table_view_widget.register_row_data_source(
            PresetSourceColumn(
                controller=self._table_controller,
                header_text="Source",
                parent=self,
            )
        )
        self._table_view_widget.register_column_data_sources(
            [
                PresetsTargetColumn(header_text="Target"),
                PresetsConstraintTypeColumn(header_text="Constraint"),
            ]
        )
        self._table_controller.clear()
        self._table_view_widget.table_view.horizontalHeader().resizeSection(
            0, dpi.dpi_scale(130)
        )
        self._table_view_widget.table_view.horizontalHeader().resizeSection(
            1, dpi.dpi_scale(130)
        )
        self._table_view_widget.table_view.horizontalHeader().resizeSection(
            2, dpi.dpi_scale(130)
        )

    def _setup_layouts(self):
        """Set up the layouts of the table widget."""

        main_layout = qt.vertical_layout()
        self.setLayout(main_layout)

        main_layout.addWidget(self._table_view_widget)


class PresetsTableController(QObject):
    """Controller for the presets table widget."""

    def __init__(
        self,
        model: TableModel,
        view: TableViewWidget,
        parent: QObject | None = None,
        default_constraint: str = "orient",
    ) -> None:
        """Initialize the controller for the presets table widget.

        Args:
            model: The table model.
            view: The table view widget.
            parent: The parent `QObject`.
            default_constraint: The default constraint type.
        """

        super().__init__(parent=parent)

        self._model = model
        self._view = view
        self._default_constraint = default_constraint

        self._preset_source_names = ["--- Source Preset ---"]
        self._preset_target_names = ["--- Target Preset ---"]

    @property
    def preset_source_names(self) -> list[str]:
        """List of preset source names."""

        return self._preset_source_names.copy()

    @property
    def preset_target_names(self) -> list[str]:
        """List of preset target names."""

        return self._preset_target_names.copy()

    def clear(self):
        """Clear the table model."""

        self._model.row_data_source.set_user_objects([])
        self._model.reload()


class PresetSourceColumn(BaseDataSource):
    def __init__(
        self,
        controller: PresetsTableController,
        header_text: str | None = None,
        model: TableModel | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)

        self._controller = controller


class PresetsTargetColumn(ColumnDataSource):
    def __init__(
        self,
        header_text: str | None = None,
        model: TableModel | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)


class PresetsConstraintTypeColumn(ColumnDataSource):
    def __init__(
        self,
        header_text: str | None = None,
        model: TableModel | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(header_text=header_text, model=model, parent=parent)
