from __future__ import annotations

import logging

from Qt.QtCore import Signal

from tp.qt.mvc import Model, UiProperty

from .events import (
    UpdateNodeTypesEvent,
    UpdatePrefixesSuffixesEvent,
    RenameBaseNameEvent,
    SearchReplaceEvent,
    AddPrefixEvent,
    AddSuffixEvent,
    RemovePrefixEvent,
    RemoveSuffixEvent,
)

logger = logging.getLogger(__name__)


class RenamerModel(Model):
    """Model class that stores all the data for the Renamer tool."""

    updateNodeTypes = Signal(UpdateNodeTypesEvent)
    updatePrefixesSuffixes = Signal(UpdatePrefixesSuffixesEvent)
    renameBaseName = Signal(RenameBaseNameEvent)
    searchReplace = Signal(SearchReplaceEvent)
    addPrefix = Signal(AddPrefixEvent)
    addSuffix = Signal(AddSuffixEvent)
    removePrefix = Signal(RemovePrefixEvent)
    removeSuffix = Signal(RemoveSuffixEvent)

    def initialize_properties(self) -> list[UiProperty]:
        """
        Overrides `initialize_properties` to Initialize the properties associated with the instance.

        This method initializes the properties associated with the instance.

        :return: A list of initialized UI properties.
        """

        properties = [
            UiProperty("node_types", [], type=list[str]),
            UiProperty("active_node_type_index", 0),
            UiProperty("auto_shapes", True),
            UiProperty("rename_option_index", 0),
            UiProperty("base_name", ""),
            UiProperty("numeric_padding", "2"),
            UiProperty("search", ""),
            UiProperty("replace", ""),
            UiProperty("prefixes", [], type=list[str]),
            UiProperty("prefix", ""),
            UiProperty("prefix_index", 0),
            UiProperty("suffixes", [], type=list[str]),
            UiProperty("suffix", ""),
            UiProperty("suffix_index", 0),
            UiProperty("at_index", ""),
            UiProperty("index_combo", 0),
            UiProperty("index", "-2"),
            UiProperty("index_shuffle", "-1"),
            UiProperty("renumber_option_index", 0),
            UiProperty("renumber_padding", "2"),
            UiProperty("namespace", ""),
            UiProperty("namespace_option_index", 0),
        ]

        return properties

    def update_node_types(self):
        """
        Updates available node types.
        """

        event = UpdateNodeTypesEvent()
        self.updateNodeTypes.emit(event)
        self.update_property("node_types", event.node_types)

    def update_prefixes_suffixes(self):
        """
        Updates available prefixes and suffixes.
        """

        event = UpdatePrefixesSuffixesEvent()
        self.updatePrefixesSuffixes.emit(event)
        self.update_property("prefixes", event.prefixes)
        self.update_property("suffixes", event.suffixes)

    def force_rename(self):
        """
        Forces the renaming of the nodes.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        base_name = self.properties.base_name.value

        if not search_hierarchy and not selection_only:
            logger.warning("The `All` filter cannot be used with force name.")
            return
        if not base_name:
            logger.warning("Please type a base name.")
            return
        if ":" in base_name:
            logger.warning(
                "':' is an illegal character in names, use the namespaces instead."
            )
            return

        event = RenameBaseNameEvent(
            base_name=base_name,
            nice_name_type=nice_name_type,
            padding=int(self.properties.numeric_padding.value),
            hierarchy=search_hierarchy,
        )
        self.renameBaseName.emit(event)
        if not event.success:
            logger.error("Failed to rename nodes.")

    def search_replace(self):
        """
        Searches and replaces the nodes.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        search_text = self.properties.search.value
        replace_text = self.properties.replace.value

        if not search_text:
            logger.warning("Please type a search text.")
            return
        if ":" in replace_text or ":" in search_text:
            logger.warning(
                "':' is an illegal character in names, use the namespaces instead."
            )
            return

        event = SearchReplaceEvent(
            search=search_text,
            replace=replace_text,
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.searchReplace.emit(event)
        if not event.success:
            logger.error("Failed to search and replace node names.")

    def add_prefix(self):
        """
        Adds a prefix to the nodes.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        prefix: str = self.properties.prefix.value

        if not prefix:
            logger.warning("Please type a prefix.")
            return
        if prefix[0].isdigit():
            logger.warning("Prefix cannot start with a digit.")
            return

        event = AddPrefixEvent(
            prefix=prefix,
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.addPrefix.emit(event)
        if not event.success:
            logger.error("Failed to add prefix to node names.")

    def add_suffix(self):
        """
        Adds a suffix to the nodes.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        suffix: str = self.properties.suffix.value

        if not suffix:
            logger.warning("Please type a suffix.")
            return

        event = AddSuffixEvent(
            suffix=suffix,
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.addSuffix.emit(event)
        if not event.success:
            logger.error("Failed to add suffix to node names.")

    def remove_prefix(self):
        """
        Removes a prefix from the node names.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        if not search_hierarchy and not selection_only:
            logger.warning("The `All` filter cannot be used with force name.")
            return

        event = RemovePrefixEvent(
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.removePrefix.emit(event)
        if not event.success:
            logger.error("Failed to remove prefix from node names.")

    def remove_suffix(self):
        """
        Removes a suffix from the node names.
        :return:
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        if not search_hierarchy and not selection_only:
            logger.warning("The `All` filter cannot be used with force name.")
            return

        event = RemoveSuffixEvent(
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.removeSuffix.emit(event)
        if not event.success:
            logger.error("Failed to remove suffix from node names.")

    def _get_filter_options(self) -> tuple[bool, bool]:
        """
        Internal function that returns the filter options.

        :return: tuple containing whether to search hierarchy and whether to rename only the current selection.
        """

        search_hierarchy = False
        selection_only = False
        if self.properties.rename_option_index.value == 0:
            search_hierarchy = False
            selection_only = True
        elif self.properties.rename_option_index.value == 1:
            search_hierarchy = True
            selection_only = True

        return search_hierarchy, selection_only
