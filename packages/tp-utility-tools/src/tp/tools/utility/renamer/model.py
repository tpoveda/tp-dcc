from __future__ import annotations

import logging

from Qt.QtCore import Signal

from tp.qt.mvc import Model, UiProperty
from tp.naming.consts import EditIndexMode

from .events import (
    UpdateNodeTypesEvent,
    UpdatePrefixesSuffixesEvent,
    RenameBaseNameEvent,
    SearchReplaceEvent,
    AddPrefixEvent,
    AddSuffixEvent,
    RemovePrefixEvent,
    RemoveSuffixEvent,
    EditIndexEvent,
    ShuffleIndexEvent,
    ChangePaddingEvent,
    RenumberEvent,
    RemoveNumbersEvent,
    AssignNamespaceEvent,
    DeleteSelectedNamespaceEvent,
    DeleteUnusedNamespacesEvent,
    OpenNamespaceEditorEvent,
    OpenReferenceEditorEvent,
    AutoPrefixEvent,
    AutoSuffixEvent,
    MakeUniqueNameEvent,
)

logger = logging.getLogger(__name__)


class RenamerModel(Model):
    """
    Model class that stores all the data for the Renamer tool.
    """

    updateNodeTypes = Signal(UpdateNodeTypesEvent)
    updatePrefixesSuffixes = Signal(UpdatePrefixesSuffixesEvent)
    renameBaseName = Signal(RenameBaseNameEvent)
    searchReplace = Signal(SearchReplaceEvent)
    addPrefix = Signal(AddPrefixEvent)
    addSuffix = Signal(AddSuffixEvent)
    removePrefix = Signal(RemovePrefixEvent)
    removeSuffix = Signal(RemoveSuffixEvent)
    editIndex = Signal(EditIndexEvent)
    shuffleIndex = Signal(ShuffleIndexEvent)
    changePadding = Signal(ChangePaddingEvent)
    doRenumber = Signal(RenumberEvent)
    removeNumbers = Signal(RemoveNumbersEvent)
    assignNamespace = Signal(AssignNamespaceEvent)
    deleteSelectedNamespace = Signal(DeleteSelectedNamespaceEvent)
    deleteUnusedNamespaces = Signal(DeleteUnusedNamespacesEvent)
    openNamespaceEditor = Signal(OpenNamespaceEditorEvent)
    openReferenceEditor = Signal(OpenReferenceEditorEvent)
    autoPrefix = Signal(AutoPrefixEvent)
    autoSuffix = Signal(AutoSuffixEvent)
    makeUniqueName = Signal(MakeUniqueNameEvent)

    def initialize_properties(self) -> list[UiProperty]:
        """
        Overrides `initialize_properties` to Initialize the properties associated with the instance.

        This method initializes the properties associated with the instance.

        :return: A list of initialized UI properties.
        """

        return [
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

    def edit_index(self):
        """
        Edits the index of the node names.

        :raises ValueError: If the edit mode is invalid.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        edit_mode = self.properties.index_combo.value
        text = self.properties.at_index.value
        index = int(self.properties.index.value)

        if not search_hierarchy and not selection_only:
            logger.warning("The `All` filter cannot be used with edit index.")
            return

        if edit_mode == 0:
            mode = EditIndexMode.Insert
        elif edit_mode == 1:
            mode = EditIndexMode.Replace
        elif edit_mode == 2:
            mode = EditIndexMode.Remove
        else:
            raise ValueError(f"Invalid edit mode: {edit_mode}")
        if index > 0:
            index -= 1

        event = EditIndexEvent(
            text=text,
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
            index=index,
            mode=mode,
        )
        self.editIndex.emit(event)
        if not event.success:
            logger.error("Failed to edit index of node names.")

    def shuffle_index(self, offset: int):
        """
        Shuffles the index of the node names.

        :param offset: The offset to shuffle the index.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        shuffle_index = int(self.properties.index_shuffle.value)
        if not search_hierarchy and not selection_only:
            logger.warning("The `All` filter cannot be used with shuffle index.")
            return

        if shuffle_index > 0:
            shuffle_index -= 1

        event = ShuffleIndexEvent(
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
            index=shuffle_index,
            offset=offset,
        )
        self.shuffleIndex.emit(event)
        if not event.success:
            logger.error("Failed to shuffle index of node names.")
            return

        old_value = int(self.properties.index_shuffle.value)
        new_value = old_value + offset
        if new_value == 0:
            new_value = 1 if old_value > 1 else -1
        self.update_property("index_shuffle", str(new_value))

    def change_padding(self):
        """
        Changes the padding of the node names.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        padding = int(self.properties.renumber_padding.value)
        if not search_hierarchy and not selection_only:
            logger.warning("The `All` filter cannot be used with change padding.")
            return

        event = ChangePaddingEvent(
            padding=padding,
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.changePadding.emit(event)
        if not event.success:
            logger.error("Failed to change padding of node names.")

    def renumber(self, trailing_only: bool = False):
        """
        Renumber the node names.

        :param trailing_only: Whether to renumber only the trailing numbers.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        padding = int(self.properties.renumber_padding.value)
        if not search_hierarchy and not selection_only:
            logger.warning("The `All` filter cannot be used with renumber.")
            return

        event = RenumberEvent(
            nice_name_type=nice_name_type,
            remove_trailing_numbers=trailing_only,
            padding=padding,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.doRenumber.emit(event)
        if not event.success:
            logger.error("Failed to renumber node names.")

    def remove_numbers(self, trailing_only: bool = False):
        """
        Removes the numbers from the node names.

        :param trailing_only: Whether to remove only the trailing numbers.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        event = RemoveNumbersEvent(
            nice_name_type=nice_name_type,
            trailing_only=trailing_only,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.removeNumbers.emit(event)
        if not event.success:
            logger.error("Failed to remove numbers from node names.")

    def assign_namespace(self):
        """
        Assigns a namespace to the node names.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        namespace = self.properties.namespace.value
        remove_namespace = (
            True if self.properties.namespace_option_index.value == 1 else False
        )

        event = AssignNamespaceEvent(
            namespace=namespace,
            nice_name_type=nice_name_type,
            remove_namespace=remove_namespace,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.assignNamespace.emit(event)
        if not event.success:
            logger.error("Failed to assign namespace to node names.")

    def delete_selected_namespace(self):
        """
        Deletes selected namespaces.
        """

        event = DeleteSelectedNamespaceEvent(
            rename_shape=self.properties.auto_shapes.value
        )
        self.deleteSelectedNamespace.emit(event)
        if not event.success:
            logger.error("Failed to delete selected namespace.")

    def delete_unused_namespaces(self):
        """
        Deletes unused namespaces.
        """

        event = DeleteUnusedNamespacesEvent()
        self.deleteUnusedNamespaces.emit(event)
        if not event.success:
            logger.error("Failed to delete unused namespaces.")

    def open_namespace_editor(self):
        """
        Opens namespace editor.
        """

        event = OpenNamespaceEditorEvent()
        self.openNamespaceEditor.emit(event)

    def open_reference_editor(self):
        """
        Opens reference editor.
        """

        event = OpenReferenceEditorEvent()
        self.openReferenceEditor.emit(event)

    def auto_prefix(self):
        """
        Auto prefixes nodes based on its node type.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]

        event = AutoPrefixEvent(
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.autoPrefix.emit(event)
        if not event.success:
            logger.error("Failed to auto prefix node names.")

    def auto_suffix(self):
        """
        Auto suffixes nodes based on its node type.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]

        event = AutoSuffixEvent(
            nice_name_type=nice_name_type,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.autoSuffix.emit(event)
        if not event.success:
            logger.error("Failed to auto suffix node names.")

    def make_unique_name(self):
        """
        Make a unique name for the node.
        """

        search_hierarchy, selection_only = self._get_filter_options()
        nice_name_type = self.properties.node_types.value[
            self.properties.active_node_type_index.value
        ]
        padding = int(self.properties.renumber_padding.value)

        event = MakeUniqueNameEvent(
            nice_name_type=nice_name_type,
            padding=padding,
            rename_shape=self.properties.auto_shapes.value,
            hierarchy=search_hierarchy,
            selection_only=selection_only,
        )
        self.makeUniqueName.emit(event)
        if not event.success:
            logger.error("Failed to make unique name for node.")

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
