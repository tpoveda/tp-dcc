from __future__ import annotations

import typing

from Qt.QtCore import Signal
from Qt.QtWidgets import QWidget
from Qt.QtGui import QIcon

from tp.qt import contexts
from tp.python import paths
from tp.qt import uiconsts, factory

from . import consts, tooltips

if typing.TYPE_CHECKING:
    from .model import RenamerModel


class RenamerView(QWidget):
    closeRequested = Signal()

    def __init__(self, model: RenamerModel, parent: QWidget | None = None):
        super().__init__(parent=parent)

        self._model = model

        self._setup_widgets()
        self._setup_layouts()
        self._link_properties()
        self._setup_signals()

    def _setup_widgets(self):
        """
        Internal function that setup all view widgets.
        """

        # Filters
        self._filters_frame = factory.collapsible_frame(
            "Filters", thin=True, parent=self
        )
        self._filters_frame.setToolTip(tooltips.FILTERS_TOOLTIP)
        self._nodes_filter_combo = factory.combobox_widget(
            tooltip=tooltips.NODES_FILTER_TOOLTIP, searchable=True, parent=self
        )
        self._auto_shapes_checkbox = factory.checkbox(
            "Auto Shapes",
            tooltip=tooltips.AUTO_SHAPES_TOOLTIP,
            parent=self,
        )
        self._options_radio = factory.radio_button_group(
            radio_names=consts.RADIO_NAMES,
            default=0,
            tooltips=tooltips.RADIO_NAMES_TOOLTIPS,
            parent=self,
        )

        # Base Name
        self._base_name_frame = factory.collapsible_frame(
            "Base Name", thin=True, parent=self
        )
        self._base_name_line = factory.line_edit(
            placeholder_text="Base Name",
            tooltip=tooltips.BASE_NAME_TOOLTIP,
            parent=self,
        )
        self._numeric_padding_int = factory.int_edit(
            "Numeric Padding",
            tooltip=tooltips.NUMERIC_PADDING_TOOLTIP,
            label_ratio=10,
            edit_ratio=6,
            parent=self,
        )
        self._force_rename_button = factory.styled_button(
            button_icon=QIcon(paths.canonical_path("resources/icons/todo.png")),
            tooltip=tooltips.BASE_NAME_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )

        # Search & Replace
        self._search_replace_frame = factory.collapsible_frame(
            "Search & Replace", thin=True, parent=self
        )
        self._search_line = factory.line_edit(
            placeholder_text="Search",
            tooltip=tooltips.SEARCH_REPLACE_TOOLTIP,
            parent=self,
        )
        self._replace_line = factory.line_edit(
            placeholder_text="Replace",
            tooltip=tooltips.SEARCH_REPLACE_TOOLTIP,
            parent=self,
        )
        self._search_replace_button = factory.styled_button(
            button_icon=QIcon(
                paths.canonical_path("resources/icons/search_replace.png")
            ),
            tooltip=tooltips.BASE_NAME_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )

        # Prefix/Suffix
        self._prefix_suffix_frame = factory.collapsible_frame(
            "Prefix/Suffix", thin=True, parent=self
        )
        self._prefix_edit = factory.string_edit(
            edit_placeholder="Add Prefix",
            tooltip=tooltips.PREFIX_TOOLTIP,
            parent=self,
        )
        self._prefix_button = factory.styled_button(
            button_icon=QIcon(paths.canonical_path("resources/icons/prefix.png")),
            tooltip=tooltips.PREFIX_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._prefix_combo = factory.combobox_widget(
            tooltip=tooltips.PREFIXES_TOOLTIP, searchable=True, parent=self
        )
        self._suffix_edit = factory.string_edit(
            edit_placeholder="Add Suffix",
            tooltip=tooltips.SUFFIX_TOOLTIP,
            parent=self,
        )
        self._suffix_button = factory.styled_button(
            button_icon=QIcon(paths.canonical_path("resources/icons/suffix.png")),
            tooltip=tooltips.SUFFIX_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._suffix_combo = factory.combobox_widget(
            tooltip=tooltips.SUFFIXES_TOOLTIP, searchable=True, parent=self
        )
        self._remove_prefix_button = factory.styled_button(
            text="Remove Prefix",
            button_icon=QIcon(paths.canonical_path("resources/icons/trash.png")),
            tooltip=tooltips.REMOVE_PREFIX_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._remove_suffix_button = factory.styled_button(
            text="Remove Suffix",
            button_icon=QIcon(paths.canonical_path("resources/icons/trash.png")),
            tooltip=tooltips.REMOVE_SUFFIX_TOOLTIP,
            parent=self,
        )

        # Index
        self._index_frame = factory.collapsible_frame(
            "Index", thin=True, tooltip=tooltips.INDEX_FRAME_TOOLTIP, parent=self
        )
        self._at_index_string_edit = factory.string_edit(
            edit_placeholder="Add at Index",
            tooltip=tooltips.ADD_AT_INDEX_TOOLTIP,
            parent=self,
        )
        self._index_combo = factory.combobox_widget(
            items=("Insert", "Replace", "Remove"),
            tooltip=tooltips.INSERT_INDEX_COMBO_BOX_TOOLTIP,
            parent=self,
        )
        self._index_int_edit = factory.int_edit(
            "Index", tooltip=tooltips.ADD_AT_INDEX_TOOLTIP, parent=self
        )
        self._at_index_button = factory.styled_button(
            text="",
            button_icon=QIcon(paths.canonical_path("resources/icons/index_text.png")),
            tooltip=tooltips.ADD_AT_INDEX_TOOLTIP,
            parent=self,
        )
        self._index_shuffle_label = factory.label(
            "Shuffle by Index", tooltip=tooltips.INDEX_SHUFFLE_TOOLTIP, parent=self
        )
        self._index_shuffle_negate_button = factory.styled_button(
            text="",
            button_icon=QIcon(paths.canonical_path("resources/icons/arrow_left.png")),
            tooltip=tooltips.INDEX_SHUFFLE_TOOLTIP,
            parent=self,
        )
        self._index_shuffle_int_edit = factory.int_edit(
            "", tooltip=tooltips.INDEX_SHUFFLE_TOOLTIP, parent=self
        )
        self._index_shuffle_positive_button = factory.styled_button(
            text="",
            button_icon=QIcon(paths.canonical_path("resources/icons/arrow_right.png")),
            tooltip=tooltips.INDEX_SHUFFLE_TOOLTIP,
            parent=self,
        )

        # Renumber
        self._renumber_frame = factory.collapsible_frame(
            "Renumber", thin=True, parent=self
        )
        self._renumber_combo = factory.combobox(
            items=consts.RENUMBER_OPTIONS,
            tooltip=tooltips.RENUMBER_TOOLTIP,
        )
        self._renumber_padding_int = factory.int_edit(
            "Pad", tooltip=tooltips.RENUMBER_PADDING_TOOLTIP, parent=self
        )
        self._renumber_button = factory.styled_button(
            text="",
            button_icon=QIcon(
                paths.canonical_path("resources/icons/numbered_list.png")
            ),
            tooltip=tooltips.INDEX_SHUFFLE_TOOLTIP,
            parent=self,
        )
        self._remove_numbers_button = factory.styled_button(
            text="Remove All Numbers",
            button_icon=QIcon(paths.canonical_path("resources/icons/trash.png")),
            tooltip=tooltips.REMOVE_ALL_NUMBERS_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._remove_tail_numbers_button = factory.styled_button(
            text="Remove Tail Numbers",
            button_icon=QIcon(paths.canonical_path("resources/icons/trash.png")),
            tooltip=tooltips.REMOVE_TAIL_NUMBERS_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )

        # Namespace
        self._namespace_frame = factory.collapsible_frame(
            "Namespace", thin=True, tooltip=tooltips.NAMESPACE_TOOLTIP, parent=self
        )
        self._namespace_string_edit = factory.string_edit(
            edit_placeholder="Namespace",
            tooltip=tooltips.NAMESPACE_TOOLTIP,
            parent=self,
        )
        self._namespace_combo = factory.combobox(
            items=consts.NAMESPACE_OPTIONS,
            tooltip=tooltips.NAMESPACE_TOOLTIP,
            parent=self,
        )
        self._namespace_button = factory.styled_button(
            text="",
            button_icon=QIcon(paths.canonical_path("resources/icons/namespace.png")),
            tooltip=tooltips.RENUMBER_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._delete_selected_namespace_button = factory.styled_button(
            text="Delete Namespace",
            button_icon=QIcon(paths.canonical_path("resources/icons/trash.png")),
            tooltip=tooltips.DELETE_NAMESPACE_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._delete_unused_namespaces_button = factory.styled_button(
            text="Unused Namespaces",
            button_icon=QIcon(paths.canonical_path("resources/icons/trash.png")),
            tooltip=tooltips.DELETE_UNUSED_NAMESPACES_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._open_namespace_editor_button = factory.styled_button(
            text="Namespace Editor",
            button_icon=QIcon(paths.canonical_path("resources/icons/browser.png")),
            tooltip=tooltips.OPEN_NAMESPACE_EDITOR_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._open_reference_editor_button = factory.styled_button(
            text="Reference Editor",
            button_icon=QIcon(paths.canonical_path("resources/icons/browser.png")),
            tooltip=tooltips.OPEN_REFERENCE_EDITOR_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )

        # Misc
        self._misc_frame = factory.collapsible_frame("Misc", thin=True, parent=self)
        self._auto_prefix_button = factory.styled_button(
            text="Auto Prefix",
            button_icon=QIcon(paths.canonical_path("resources/icons/prefix.png")),
            tooltip=tooltips.AUTO_PREFIX_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._auto_suffix_button = factory.styled_button(
            text="Auto Suffix",
            button_icon=QIcon(paths.canonical_path("resources/icons/suffix.png")),
            tooltip=tooltips.AUTO_SUFFIX_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )
        self._make_unique_button = factory.styled_button(
            text="Make Unique Name",
            button_icon=QIcon(paths.canonical_path("resources/icons/unique.png")),
            tooltip=tooltips.MAKE_UNIQUE_NAME_TOOLTIP,
            min_width=uiconsts.BUTTON_WIDTH_ICON_MEDIUM,
            parent=self,
        )

    def _setup_layouts(self):
        """
        Internal function that creates all UI layouts and add all widgets to them.
        """

        contents_layout = factory.vertical_main_layout()
        self.setLayout(contents_layout)

        filter_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        filter_layout.addWidget(self._nodes_filter_combo, 2)
        filter_layout.addWidget(self._auto_shapes_checkbox, 1)
        options_radio_layout = factory.vertical_layout(spacing=0)
        options_radio_layout.addWidget(self._options_radio)
        options_radio_layout.addSpacing(5)
        self._filters_frame.add_layout(filter_layout)
        self._filters_frame.add_layout(options_radio_layout)

        base_name_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        force_sub_layout = factory.horizontal_layout(
            margins=(uiconsts.LARGE_SPACING, 0, 0, 0)
        )
        force_sub_layout.addWidget(self._numeric_padding_int)
        base_name_layout.addWidget(self._base_name_line, 5)
        base_name_layout.addLayout(force_sub_layout, 5)
        base_name_layout.addWidget(self._force_rename_button, 1)
        self._base_name_frame.add_layout(base_name_layout)

        search_replace_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        search_replace_layout.addWidget(self._search_line, 12)
        search_replace_layout.addWidget(self._replace_line, 12)
        search_replace_layout.addWidget(self._search_replace_button, 1)
        self._search_replace_frame.add_layout(search_replace_layout)

        suffix_prefix_layout = factory.vertical_layout()
        prefix_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        prefix_layout.addWidget(self._prefix_edit, 13)
        prefix_layout.addWidget(self._prefix_combo, 11)
        prefix_layout.addWidget(self._prefix_button, 1)

        suffix_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        suffix_layout.addWidget(self._suffix_edit, 13)
        suffix_layout.addWidget(self._suffix_combo, 11)
        suffix_layout.addWidget(self._suffix_button, 1)
        remove_prefix_suffix_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        remove_prefix_suffix_layout.addWidget(self._remove_prefix_button, 1)
        remove_prefix_suffix_layout.addWidget(self._remove_suffix_button, 1)
        suffix_prefix_layout.addLayout(prefix_layout)
        suffix_prefix_layout.addLayout(suffix_layout)
        suffix_prefix_layout.addLayout(remove_prefix_suffix_layout)
        self._prefix_suffix_frame.add_layout(suffix_prefix_layout)

        index_main_layout = factory.vertical_layout()
        index_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        index_layout.addWidget(self._at_index_string_edit, 8)
        index_layout.addWidget(self._index_combo, 8)
        index_layout.addWidget(self._index_int_edit, 8)
        index_layout.addWidget(self._at_index_button, 1)
        index_shuffle_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        index_shuffle_layout.addWidget(self._index_shuffle_label, 20)
        index_shuffle_layout.addWidget(self._index_shuffle_negate_button, 1)
        index_shuffle_layout.addWidget(self._index_shuffle_int_edit, 7)
        index_shuffle_layout.addWidget(self._index_shuffle_positive_button, 1)
        index_main_layout.addLayout(index_layout)
        index_main_layout.addLayout(index_shuffle_layout)
        self._index_frame.add_layout(index_main_layout)

        renumber_main_layout = factory.vertical_layout()
        renumber_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        renumber_layout.addWidget(self._renumber_combo, 16)
        renumber_layout.addWidget(self._renumber_padding_int, 8)
        renumber_layout.addWidget(self._renumber_button, 1)
        renumber_buttons_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        renumber_buttons_layout.addWidget(self._remove_numbers_button, 1)
        renumber_buttons_layout.addWidget(self._remove_tail_numbers_button, 1)
        renumber_main_layout.addLayout(renumber_layout)
        renumber_main_layout.addLayout(renumber_buttons_layout)
        self._renumber_frame.add_layout(renumber_main_layout)

        namespace_main_layout = factory.vertical_layout()
        namespace_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        namespace_layout.addWidget(self._namespace_string_edit, 16)
        namespace_layout.addWidget(self._namespace_combo, 8)
        namespace_layout.addWidget(self._namespace_button, 1)
        namespace_delete_buttons_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        namespace_delete_buttons_layout.addWidget(
            self._delete_selected_namespace_button, 1
        )
        namespace_delete_buttons_layout.addWidget(
            self._delete_unused_namespaces_button, 1
        )
        namespace_editors_buttons_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        namespace_editors_buttons_layout.addWidget(
            self._open_namespace_editor_button, 1
        )
        namespace_editors_buttons_layout.addWidget(
            self._open_reference_editor_button, 1
        )
        namespace_main_layout.addLayout(namespace_layout)
        namespace_main_layout.addLayout(namespace_delete_buttons_layout)
        namespace_main_layout.addLayout(namespace_editors_buttons_layout)
        self._namespace_frame.add_layout(namespace_main_layout)

        misc_layout = factory.horizontal_layout(
            spacing=uiconsts.SPACING,
            margins=(uiconsts.REGULAR_PADDING, 0, uiconsts.REGULAR_PADDING, 0),
        )
        misc_layout.addWidget(self._auto_prefix_button, 1)
        misc_layout.addWidget(self._auto_suffix_button, 1)
        misc_layout.addWidget(self._make_unique_button, 1)
        self._misc_frame.add_layout(misc_layout)

        contents_layout.addWidget(self._filters_frame)
        contents_layout.addWidget(self._base_name_frame)
        contents_layout.addWidget(self._search_replace_frame)
        contents_layout.addWidget(self._prefix_suffix_frame)
        contents_layout.addWidget(self._index_frame)
        contents_layout.addWidget(self._renumber_frame)
        contents_layout.addWidget(self._namespace_frame)
        contents_layout.addWidget(self._misc_frame)
        contents_layout.addStretch()

        self._all_disabled_widgets: list[QWidget] = [
            self._at_index_string_edit, self._index_combo, self._index_int_edit, self._at_index_button,
            self._index_shuffle_label, self._remove_numbers_button, self._remove_tail_numbers_button,
            self._index_shuffle_positive_button, self._index_shuffle_negate_button, self._index_shuffle_int_edit,
            self._renumber_button, self._force_rename_button, self._base_name_line, self._renumber_padding_int,
            self._numeric_padding_int, self._renumber_combo
        ]


    def _link_properties(self):
        """
        Internal function that link between UI widgets and tool UI properties.
        """

        self._model.link_property(self._nodes_filter_combo, "active_node_type_index")
        self._model.link_property(self._auto_shapes_checkbox, "auto_shapes")
        self._model.link_property(self._options_radio, "rename_option_index")
        self._model.link_property(self._base_name_line, "base_name")
        self._model.link_property(self._numeric_padding_int, "numeric_padding")
        self._model.link_property(self._search_line, "search")
        self._model.link_property(self._replace_line, "replace")
        self._model.link_property(self._prefix_edit, "prefix")
        self._model.link_property(self._prefix_combo, "prefix_index")
        self._model.link_property(self._suffix_edit, "suffix")
        self._model.link_property(self._suffix_combo, "suffix_index")
        self._model.link_property(self._at_index_string_edit, "at_index")
        self._model.link_property(self._index_combo, "index_combo")
        self._model.link_property(self._index_int_edit, "index")
        self._model.link_property(self._index_shuffle_int_edit, "index_shuffle")
        self._model.link_property(self._renumber_combo, "renumber_option_index")
        self._model.link_property(self._renumber_padding_int, "renumber_padding")
        self._model.link_property(self._namespace_string_edit, "namespace")
        self._model.link_property(self._namespace_combo, "namespace_option_index")

    def _setup_signals(self):
        """
        Internal function that setup all signals connections.
        """

        self._model.listen("node_types", self._on_node_types_changed)
        self._model.listen("prefixes", self._on_prefixes_changed)
        self._model.listen("suffixes", self._on_suffixes_changed)

        self._base_name_frame.closeRequested.connect(self.closeRequested.emit)
        self._filters_frame.closeRequested.connect(self.closeRequested.emit)
        self._search_replace_frame.closeRequested.connect(self.closeRequested.emit)
        self._prefix_suffix_frame.closeRequested.connect(self.closeRequested.emit)
        self._index_frame.closeRequested.connect(self.closeRequested.emit)
        self._renumber_frame.closeRequested.connect(self.closeRequested.emit)
        self._namespace_frame.closeRequested.connect(self.closeRequested.emit)
        self._misc_frame.closeRequested.connect(self.closeRequested.emit)
        self._options_radio.toggled.connect(self._on_options_radio_toggled)
        self._prefix_combo.itemChanged.connect(self._on_prefix_combo_item_changed)
        self._suffix_combo.itemChanged.connect(self._on_suffix_combo_item_changed)
        self._force_rename_button.clicked.connect(self._on_force_rename_button_clicked)
        self._search_replace_button.clicked.connect(
            self._on_search_replace_button_clicked
        )
        self._prefix_button.clicked.connect(self._on_prefix_button_clicked)
        self._suffix_button.clicked.connect(self._on_suffix_button_clicked)
        self._remove_prefix_button.clicked.connect(
            self._on_remove_prefix_button_clicked
        )
        self._remove_suffix_button.clicked.connect(
            self._on_remove_suffix_button_clicked
        )
        self._index_combo.itemChanged.connect(self._on_index_combo_item_changed)
        self._at_index_button.clicked.connect(self._on_at_index_button_clicked)
        self._index_shuffle_negate_button.clicked.connect(
            self._on_index_shuffle_negate_button_clicked
        )
        self._index_shuffle_positive_button.clicked.connect(
            self._on_index_shuffle_positive_button_clicked
        )
        self._renumber_button.clicked.connect(self._on_renumber_button_clicked)
        self._remove_numbers_button.clicked.connect(
            self._on_remove_numbers_button_clicked
        )
        self._remove_tail_numbers_button.clicked.connect(
            self._on_remove_tail_numbers_button_clicked
        )
        self._namespace_button.clicked.connect(self._on_namespace_button_clicked)
        self._delete_selected_namespace_button.clicked.connect(self._on_delete_selected_namespace_button_clicked)
        self._delete_unused_namespaces_button.clicked.connect(self._on_delete_unused_namespaces_button_clicked)
        self._open_namespace_editor_button.clicked.connect(self._on_open_namespace_editor_button_clicked)
        self._open_reference_editor_button.clicked.connect(self._on_open_reference_editor_button_clicked)
        self._auto_prefix_button.clicked.connect(self._on_auto_prefix_button_clicked)
        self._auto_suffix_button.clicked.connect(self._on_auto_suffix_button_clicked)
        self._make_unique_button.clicked.connect(self._on_make_unique_name_button_clicked)

    def _on_node_types_changed(self, node_types: list[str]):
        """
        Internal callback function that is called when node types are changed.

        :param node_types: list of node types.
        """

        with contexts.block_signals(self._nodes_filter_combo):
            self._nodes_filter_combo.clear()
            self._nodes_filter_combo.add_items(node_types)

    def _on_prefixes_changed(self, prefixes: list[str]):
        """
        Internal callback function that is called when prefixes are changed.

        :param prefixes: list of prefixes.
        """

        with contexts.block_signals(self._prefix_combo):
            self._prefix_combo.clear()
            self._prefix_combo.add_items(prefixes)

    def _on_suffixes_changed(self, suffixes: list[str]):
        """
        Internal callback function that is called when suffixes are changed.

        :param suffixes: list of suffixes.
        """

        with contexts.block_signals(self._suffix_combo):
            self._suffix_combo.clear()
            self._suffix_combo.add_items(suffixes)

    def _on_options_radio_toggled(self, index: int):
        """
        Internal callback function that is called when the options radio is toggled.

        :param index: index of the radio button that was toggled.
        """

        if index == 2:
            for widget in self._all_disabled_widgets:
                widget.setDisabled(True)
        else:
            for widget in self._all_disabled_widgets:
                widget.setDisabled(False)
            if self._model.properties.index_combo.value == 2:
                self._at_index_string_edit.setDisabled(True)


    def _on_prefix_combo_item_changed(self):
        """
        Internal callback function that is called when the prefix combo item is changed.
        """

        index = self._prefix_combo.current_index()

        # If the index is 0 (Select ...), we don't want to do anything.
        if index == 0:
            return

        text = self._prefix_combo.current_text()
        text_parts = text.split("'")
        self._model.update_property("prefix", f"{text_parts[-2]}_")

    def _on_suffix_combo_item_changed(self):
        """
        Internal callback function that is called when the suffix combo item is changed.
        """

        index = self._suffix_combo.current_index()

        # If the index is 0 (Select ...), we don't want to do anything.
        if index == 0:
            return

        text = self._suffix_combo.current_text()
        text_parts = text.split("'")
        self._model.update_property("suffix", f"_{text_parts[-2]}")

    def _on_force_rename_button_clicked(self):
        """
        Internal callback function that is called when the force rename button is clicked.
        """

        self._model.force_rename()

    def _on_search_replace_button_clicked(self):
        """
        Internal callback function that is called when the search replace button is clicked.
        """

        self._model.search_replace()

    def _on_prefix_button_clicked(self):
        """
        Internal callback function that is called when the prefix button is clicked.
        """

        self._model.add_prefix()

    def _on_suffix_button_clicked(self):
        """
        Internal callback function that is called when the suffix button is clicked.
        """

        self._model.add_suffix()

    def _on_remove_prefix_button_clicked(self):
        """
        Internal callback function that is called when the remove prefix button is clicked.
        """

        self._model.remove_prefix()

    def _on_remove_suffix_button_clicked(self):
        """
        Internal callback function that is called when the remove suffix button is clicked.
        """

        self._model.remove_suffix()

    def _on_index_combo_item_changed(
        self, event: factory.ComboBoxRegularWidget.ComboItemChangedEvent
    ):
        """
        Internal callback function that is called when the index combo item is changed.

        :param event: index combo item changed event.
        """

        self._at_index_string_edit.setDisabled(True if event.index == 2 else False)

    def _on_at_index_button_clicked(self):
        """
        Internal callback function that is called when the at index button is clicked.
        """

        self._model.edit_index()

    def _on_index_shuffle_negate_button_clicked(self):
        """
        Internal callback function that is called when the index shuffle negate button is clicked.
        """

        self._model.shuffle_index(-1)

    def _on_index_shuffle_positive_button_clicked(self):
        """
        Internal callback function that is called when the index shuffle positive button is clicked.
        """

        self._model.shuffle_index(1)

    def _on_renumber_button_clicked(self):
        """
        Internal callback function that is called when the renumber button is clicked.

        :raises ValueError: If the renumber option is invalid.
        """

        renumber_option = consts.RENUMBER_OPTIONS[
            self._model.properties.renumber_option_index.value
        ]
        if renumber_option == "Change Padding":
            self._model.change_padding()
        elif renumber_option == "Append":
            self._model.renumber(trailing_only=False)
        elif renumber_option == "Replace":
            self._model.renumber(trailing_only=True)
        else:
            raise ValueError(f"Invalid renumber option: {renumber_option}")

    def _on_remove_numbers_button_clicked(self):
        """
        Internal callback function that is called when the remove numbers button is clicked.
        """

        self._model.remove_numbers(trailing_only=False)

    def _on_remove_tail_numbers_button_clicked(self):
        """
        Internal callback function that is called when the remove tail numbers button is clicked.
        """

        self._model.remove_numbers(trailing_only=True)

    def _on_namespace_button_clicked(self):
        """
        Internal callback function that is called when the namespace button is clicked.
        """

        self._model.assign_namespace()

    def _on_delete_selected_namespace_button_clicked(self):
        """
        Internal callback function that is called when the delete selected namespace button is clicked.
        """

        self._model.delete_selected_namespace()

    def _on_delete_unused_namespaces_button_clicked(self):
        """
        Internal callback function that is called when the delete unused namespaces button is clicked.
        """

        self._model.delete_unused_namespaces()

    def _on_open_namespace_editor_button_clicked(self):
        """
        Internal callback function that is called when the open namespace editor button is clicked.
        """

        self._model.open_namespace_editor()

    def _on_open_reference_editor_button_clicked(self):
        """
        Internal callback function that is called when the open reference editor button is clicked.
        """

        self._model.open_reference_editor()

    def _on_auto_prefix_button_clicked(self):
        """
        Internal callback function that is called each time auto prefix button is clicked.
        """

        self._model.auto_prefix()

    def _on_auto_suffix_button_clicked(self):
        """
        Internal callback function that is called each time auto suffix button is clicked.
        """

        self._model.auto_suffix()

    def _on_make_unique_name_button_clicked(self):
        """
        Internal callback function that is called each time make unique button is clicked.
        """

        self._model.make_unique_name()
