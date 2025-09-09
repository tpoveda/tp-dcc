from __future__ import annotations

import typing

from Qt.QtCore import Qt
from Qt.QtWidgets import (
    QSizePolicy,
    QApplication,
    QWidget,
    QProgressBar,
    QAbstractItemView,
    QSpacerItem,
)
from Qt.QtGui import QIcon, QEnterEvent

from tp.libs.python import paths
from tp.qt import factory, uiconsts, contexts, dpi
from tp.qt.widgets.viewmodel.views import TableViewWidget

from . import tooltips

if typing.TYPE_CHECKING:
    from .model import RigFromSkeletonModel


class RigFromSkeletonView(QWidget):
    """Main widget for the Rig from Skeleton tool."""

    def __init__(self, model: RigFromSkeletonModel, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._model = model

        self._setup_widgets()
        self._setup_layouts()
        self._link_properties()
        self._setup_signals()

    def enterEvent(self, event: QEnterEvent):
        """Overrides `enterEvent` method to handle the enter event.

        :param event: enter event to handle.
        """

        self._model.update_widgets_from_properties()
        super().enterEvent(event)

    def _setup_widgets(self):
        """Internal function that setup all view widgets."""

        self._auto_left_right_checkbox = factory.checkbox_widget(
            text="Auto Right Side",
            tooltip=tooltips.AUTO_LEFT_RIGHT_CHECKBOX_TOOLTIP,
            parent=self,
        )

        self._source_collapsible_frame = factory.collapsible_frame(
            "Source Joints - Name Options",
            thin=True,
            content_margins=(
                uiconsts.SPACING,
                uiconsts.SPACING,
                uiconsts.SPACING,
                uiconsts.SPACING,
            ),
            content_spacing=uiconsts.SPACING,
            collapsed=True,
            parent=self,
        )

        self._source_namespace_string_edit = factory.string_edit(
            label_text="Namespace",
            edit_placeholder="characterX:",
            tooltip=tooltips.SOURCE_NAMESPACE_STRING_EDIT_TOOLTIP,
            parent=self,
        )
        self._source_left_string_edit = factory.string_edit(
            label_text="Left Right ID",
            edit_placeholder="_L",
            tooltip=tooltips.SOURCE_LEFT_RIGHT_STRING_EDIT_TOOLTIP,
            parent=self,
        )
        self._source_right_string_edit = factory.string_edit(
            edit_placeholder="_R",
            tooltip=tooltips.SOURCE_LEFT_RIGHT_STRING_EDIT_TOOLTIP,
            parent=self,
        )
        self._source_left_right_always_prefix_checkbox = factory.checkbox_widget(
            text="L-R Is Prefix",
            tooltip=tooltips.SOURCE_LEFT_RIGHT_FORCE_PREFIX_CHECKBOX_TOOLTIP,
            right=True,
            parent=self,
        )
        self._source_left_right_always_suffix_checkbox = factory.checkbox_widget(
            text="L-R Is Suffix",
            tooltip=tooltips.SOURCE_LEFT_RIGHT_FORCE_SUFFIX_CHECKBOX_TOOLTIP,
            right=True,
            parent=self,
        )
        self._source_left_right_separator_on_border = factory.checkbox_widget(
            text="Separator on Border",
            tooltip=tooltips.SOURCE_LEFT_RIGHT_SEPARATOR_ON_BORDER_CHECKBOX_TOOLTIP,
            right=True,
            parent=self,
        )
        self._source_prefix_string_edit = factory.string_edit(
            label_text="Prefix",
            edit_placeholder="xxx_",
            label_ratio=3,
            edit_ratio=6,
            parent=self,
        )
        self._source_suffix_string_edit = factory.string_edit(
            label_text="Suffix",
            edit_placeholder="_xxx",
            label_ratio=3,
            edit_ratio=6,
            parent=self,
        )

        self._table_view_widget = TableViewWidget(
            manual_reload=False, searchable=False, parent=self
        )
        self._table_view_widget.set_model(self._model.table_model)
        self._table_view_widget.table_view.verticalHeader().hide()
        self._table_view_widget.table_view.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        self._table_view_widget.table_view.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        self._table_view_widget.register_row_data_source(self._model.source_column)
        self._table_view_widget.register_column_data_sources(
            [self._model.target_column]
        )
        self._model.table_model.clear()
        self._table_view_widget.table_view.horizontalHeader().resizeSection(
            0, dpi.dpi_scale(180)
        )
        self._table_view_widget.table_view.horizontalHeader().resizeSection(
            1, dpi.dpi_scale(180)
        )

        self._source_combo = factory.combobox_widget(searchable=True, parent=self)
        self._target_combo = factory.combobox_widget(searchable=True, parent=self)

        self._dots_menu_button = factory.styled_button(
            "",
            button_icon=QIcon(paths.canonical_path("./resources/icons/dots.png")),
            tooltip=tooltips.MISC_SETTINGS_BUTTON_TOOLTIP,
            style=factory.ButtonStyles.TransparentBackground,
            parent=self,
        )
        self._dots_menu_button.setVisible(False)
        self._clear_button = factory.styled_button(
            "",
            button_icon=QIcon(paths.canonical_path("./resources/icons/clear_list.png")),
            tooltip=tooltips.CLEAR_BUTTON_TOOLTIP,
            style=factory.ButtonStyles.TransparentBackground,
            parent=self,
        )
        self._add_button = factory.styled_button(
            "",
            button_icon=QIcon(paths.canonical_path("./resources/icons/plus.png")),
            tooltip=tooltips.ADD_BUTTON_TOOLTIP,
            style=factory.ButtonStyles.TransparentBackground,
            parent=self,
        )
        self._remove_button = factory.styled_button(
            "",
            button_icon=QIcon(paths.canonical_path("./resources/icons/minus.png")),
            tooltip=tooltips.REMOVE_BUTTON_TOOLTIP,
            style=factory.ButtonStyles.TransparentBackground,
            parent=self,
        )

        self._buttons_divider = factory.label_divider(parent=self)

        self._build_from_skeleton_button = factory.styled_button(
            "Build Rig from Skeleton",
            button_icon=QIcon(paths.canonical_path("./resources/icons/man.png")),
            tooltip=tooltips.BUILD_FROM_SKELETON_BUTTON_TOOLTIP,
            style=factory.ButtonStyles.Default,
            parent=self,
        )

        self._progress_divider = factory.divider(parent=self)
        self._progress_bar = QProgressBar(parent=self)
        self._progress_bar.setMinimum(0)
        self._progress_bar.setMaximum(100)
        self._progress_bar_message_label = factory.BaseLabel(
            "Status: Waiting for user input", parent=self
        )
        self._progress_bar_message_label.setAlignment(Qt.AlignCenter)
        self._progress_bar_message_label.setSizePolicy(
            QSizePolicy.Preferred, QSizePolicy.Maximum
        )
        self._progress_divider.setVisible(False)
        self._progress_bar.setVisible(False)
        self._progress_bar_message_label.setVisible(False)

    def _setup_layouts(self):
        """Internal function that creates all UI layouts and add all widgets to them."""

        contents_layout = factory.vertical_main_layout()
        contents_layout.setSpacing(uiconsts.SMALL_SPACING)
        self.setLayout(contents_layout)

        checkbox_layout = factory.horizontal_layout(
            margins=(
                uiconsts.SPACING,
                uiconsts.SPACING,
                uiconsts.SPACING,
                uiconsts.SPACING,
            ),
            spacing=uiconsts.SPACING,
        )
        checkbox_layout.addWidget(self._auto_left_right_checkbox, 1)

        source_namespace_layout = factory.horizontal_layout(spacing=uiconsts.SPACING)
        source_namespace_layout.addWidget(self._source_namespace_string_edit)
        source_namespace_layout.addWidget(self._source_left_string_edit, 10)
        source_namespace_layout.addWidget(self._source_right_string_edit, 5)
        source_checkbox_layout = factory.horizontal_layout(spacing=uiconsts.SPACING)
        source_checkbox_layout.addWidget(
            self._source_left_right_always_prefix_checkbox, 1
        )
        source_checkbox_layout.addWidget(
            self._source_left_right_always_suffix_checkbox, 1
        )
        source_checkbox_layout.addWidget(self._source_left_right_separator_on_border, 1)
        source_prefix_suffix_layout = factory.horizontal_main_layout()
        source_prefix_suffix_layout.addWidget(self._source_prefix_string_edit, 1)
        source_prefix_suffix_layout.addWidget(self._source_suffix_string_edit, 1)
        self._source_collapsible_frame.add_layout(source_namespace_layout)
        self._source_collapsible_frame.add_layout(source_checkbox_layout)
        self._source_collapsible_frame.add_layout(source_prefix_suffix_layout)

        combo_boxes_layout = factory.horizontal_layout()
        combo_boxes_layout.addWidget(self._source_combo, 1)
        combo_boxes_layout.addWidget(self._target_combo, 1)

        table_layout = factory.vertical_layout()
        table_layout.addWidget(self._table_view_widget)

        table_buttons_layout = factory.horizontal_layout(spacing=uiconsts.SPACING)
        table_buttons_layout.addWidget(self._dots_menu_button, 1)
        table_buttons_layout.addWidget(self._add_button, 1)
        table_buttons_layout.addWidget(self._remove_button, 1)
        table_buttons_layout.addWidget(self._clear_button, 1)
        table_buttons_layout.addItem(
            QSpacerItem(1000, 0, QSizePolicy.Expanding, QSizePolicy.Preferred)
        )

        buttons_layout = factory.horizontal_layout(spacing=uiconsts.SPACING)
        buttons_layout.addWidget(self._build_from_skeleton_button, 20)

        contents_layout.addLayout(checkbox_layout)
        contents_layout.addWidget(self._source_collapsible_frame)
        contents_layout.addLayout(combo_boxes_layout)
        contents_layout.addLayout(table_layout)
        contents_layout.addLayout(table_buttons_layout)
        contents_layout.addWidget(self._buttons_divider)
        contents_layout.addLayout(buttons_layout)
        contents_layout.addWidget(self._progress_divider)
        contents_layout.addWidget(self._progress_bar)
        # noinspection PyTypeChecker
        contents_layout.addWidget(self._progress_bar_message_label, Qt.AlignCenter)

    def _link_properties(self):
        """Internal function that link between UI widgets and tool UI properties."""

        self._model.link_property(self._auto_left_right_checkbox, "auto_left_right")
        self._model.link_property(
            self._source_namespace_string_edit, "source_namespace"
        )
        self._model.link_property(self._source_left_string_edit, "source_left")
        self._model.link_property(self._source_right_string_edit, "source_right")
        self._model.link_property(
            self._source_left_right_always_prefix_checkbox, "source_always_prefix"
        )
        self._model.link_property(
            self._source_left_right_always_suffix_checkbox, "source_always_suffix"
        )
        self._model.link_property(
            self._source_left_right_separator_on_border, "source_separator"
        )
        self._model.link_property(self._source_prefix_string_edit, "source_prefix")
        self._model.link_property(self._source_suffix_string_edit, "source_suffix")
        self._model.link_property(self._source_combo, "active_preset_source_index")
        self._model.link_property(self._target_combo, "active_preset_target_index")
        self._model.link_property(self._progress_bar, "progress")
        self._model.link_property(self._progress_bar_message_label, "progress_message")

    def _setup_signals(self):
        """Internal function that connects all widget signals."""

        self._model.table_model.rowsInserted.connect(self._on_table_model_rows_inserted)
        self._model.listen(
            "preset_source_names", self._on_model_preset_source_names_changed
        )
        self._model.listen(
            "preset_target_names", self._on_model_preset_target_names_changed
        )
        self._model.listen("progress", self._on_model_progres_changed)

        self._auto_left_right_checkbox.toggled.connect(self._on_auto_left_right_toggled)
        self._source_combo.itemChanged.connect(self._on_source_combo_item_changed)
        self._target_combo.itemChanged.connect(self._on_target_combo_item_changed)
        self._table_view_widget.selectionChanged.connect(
            self._on_table_view_widget_selection_changed
        )
        self._add_button.clicked.connect(self._on_add_button_clicked)
        self._remove_button.clicked.connect(self._on_remove_button_clicked)
        self._clear_button.clicked.connect(self._on_clear_button_clicked)
        self._build_from_skeleton_button.clicked.connect(
            self._on_build_from_skeleton_button_clicked
        )

    def _on_table_model_rows_inserted(self):
        """Internal callback function that is called each time rows are inserted in the
        table model.
        """

        table_model = self._table_view_widget.model()
        for row in range(table_model.rowCount()):
            first_column_index = table_model.index(row, 0)
            second_column_index = table_model.index(row, 1)
            if table_model.flags(first_column_index) & Qt.ItemIsEditable:
                self._table_view_widget.open_persistent_editor(first_column_index)
            if table_model.flags(second_column_index) & Qt.ItemIsEditable:
                self._table_view_widget.open_persistent_editor(second_column_index)

    def _on_model_preset_source_names_changed(self, preset_source_names: list[str]):
        """Internal callback function that is called each time the preset source
         names are changed.

        :param preset_source_names: list of preset source names.
        """

        with contexts.block_signals(self._source_combo):
            self._source_combo.clear()
            self._source_combo.add_items(preset_source_names)

    def _on_model_preset_target_names_changed(self, preset_target_names: list[str]):
        """Internal callback function that is called each time the preset target
        names are changed.

        :param preset_target_names: list of preset target names.
        """

        with contexts.block_signals(self._target_combo):
            self._target_combo.clear()
            self._target_combo.add_items(preset_target_names)

    def _on_model_progres_changed(self, value: int):
        """Internal callback function that is called each time the progress value
        is changed.

        :param value: progress value.
        """

        QApplication.processEvents()

    def _on_auto_left_right_toggled(self, flag: bool):
        """Internal callback function that is called each time the auto left right
        checkbox is toggled.

        :param flag: flag to set.
        """

        self._source_left_string_edit.setEnabled(flag)
        self._source_right_string_edit.setEnabled(flag)
        self._source_left_right_always_prefix_checkbox.setEnabled(flag)
        self._source_left_right_always_suffix_checkbox.setEnabled(flag)
        self._source_left_right_separator_on_border.setEnabled(flag)

    def _on_source_combo_item_changed(self):
        """Internal callback function that is called each time the source combo item
        is changed.
        """

        self._model.update_sources_from_active_presets()

    def _on_target_combo_item_changed(self):
        """Internal callback function that is called each time the target combo item
        is changed.
        """

        self._model.update_targets_from_active_presets()

    def _on_table_view_widget_selection_changed(self):
        """Internal callback function that is called each time the table view widget
        selection is changed.
        """

        self._model.update_property(
            "selected_rows_indexes", self._table_view_widget.selected_rows_indexes()
        )

    def _on_add_button_clicked(self):
        """Internal callback function that is called each time the add button is clicked."""

        self._model.insert_item()
        self._model.update_property(
            "selected_rows_indexes", self._table_view_widget.selected_rows_indexes()
        )

    def _on_remove_button_clicked(self):
        """Internal callback function that is called each time the remove button is clicked."""

        self._model.remove_selected_items()
        self._model.update_property(
            "selected_rows_indexes", self._table_view_widget.selected_rows_indexes()
        )

    def _on_clear_button_clicked(self):
        """Internal callback function that is called each time the clear button is clicked."""

        self._model.clear_items()
        self._model.update_property(
            "selected_rows_indexes", self._table_view_widget.selected_rows_indexes()
        )

    def _on_build_from_skeleton_button_clicked(self):
        """Internal callback function that is called each time the build from skeleton
        button is clicked.
        """

        self._progress_divider.setVisible(True)
        self._progress_bar.setVisible(True)
        self._progress_bar_message_label.setVisible(True)
        self._model.build_from_skeleton()
