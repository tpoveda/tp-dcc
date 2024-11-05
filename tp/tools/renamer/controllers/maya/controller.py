from __future__ import annotations

import typing

from maya import mel

from tp.naming.maya import api as naming
from tp.maya.cmds import filtertypes, decorators

from ..abstract import ARenamerController

if typing.TYPE_CHECKING:
    from ...events import (
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
    )


class MayaRenamerController(ARenamerController):
    """Class that defines the interface for a renamer hook for Maya."""

    def update_node_types(self, event: UpdateNodeTypesEvent):
        """
        Returns list of node types that can be used to filter nodes that can be renamed.

        :param event: update node types event.
        """

        event.node_types = list(filtertypes.TYPE_FILTERS.keys())

    def update_prefixes_suffixes(self, event: UpdatePrefixesSuffixesEvent):
        """
        Updates prefixes and suffixes that can be used to filter nodes that can be renamed.

        :param event: update prefixes and suffixes event.
        """

        event.prefixes = list(filtertypes.SUFFIXES.copy())
        event.suffixes = list(filtertypes.SUFFIXES.copy())

    @decorators.undo
    def rename_base_name(self, event: RenameBaseNameEvent):
        """
        Renames the base name of the nodes.

        :param event: rename base name event.
        """

        new_names = naming.rename_selected_objects(
            event.base_name,
            event.nice_name_type,
            padding=event.padding,
            hierarchy=event.hierarchy,
        )
        event.success = True if new_names else False

    @decorators.undo
    def search_replace(self, event: SearchReplaceEvent):
        """
        Renames the base name of the nodes.

        :param event: search replace event.
        """

        new_names = naming.search_replace_filtered_type(
            event.search,
            event.replace,
            event.nice_name_type,
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
        )
        event.success = True if new_names else False

    @decorators.undo
    def add_prefix(self, event: AddPrefixEvent):
        """
        Adds a prefix to the nodes.

        :param event: add prefix event.
        """

        new_names = naming.prefix_suffix_filtered_type(
            event.prefix,
            event.nice_name_type,
            naming.PrefixSuffixType.Prefix,
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
        )
        event.success = True if new_names else False

    @decorators.undo
    def add_suffix(self, event: AddSuffixEvent):
        """
        Adds a suffix to the nodes.

        :param event: add suffix event.
        """

        new_names = naming.prefix_suffix_filtered_type(
            event.suffix,
            event.nice_name_type,
            naming.PrefixSuffixType.Suffix,
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
        )
        event.success = True if new_names else False

    @decorators.undo
    def remove_prefix(self, event: RemovePrefixEvent):
        """
        Removes a prefix from the nodes.

        :param event: remove prefix event.
        """

        new_names = naming.edit_index_item_filtered_type(
            0,
            event.nice_name_type,
            mode=naming.EditIndexMode.Remove,
            separator="_",
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
            dag=False,
            remove_maya_defaults=True,
            transforms_only=True,
        )
        event.success = True if new_names else False

    @decorators.undo
    def remove_suffix(self, event: RemoveSuffixEvent):
        """
        Removes a suffix from the nodes.

        :param event: remove suffix event.
        """

        new_names = naming.edit_index_item_filtered_type(
            -1,
            event.nice_name_type,
            mode=naming.EditIndexMode.Remove,
            separator="_",
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
            dag=False,
            remove_maya_defaults=True,
            transforms_only=True,
        )
        event.success = True if new_names else False

    @decorators.undo
    def edit_index(self, event: EditIndexEvent):
        """
        Edit index of the nodes.

        :param event: edit index event.
        """

        new_names = naming.edit_index_item_filtered_type(
            event.index,
            event.nice_name_type,
            text=event.text,
            mode=event.mode,
            separator="_",
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
            dag=False,
            remove_maya_defaults=True,
            transforms_only=True,
        )
        event.success = True if new_names else False

    @decorators.undo
    def shuffle_index(self, event: ShuffleIndexEvent):
        """
        Shuffle index of the nodes.

        :param event: shuffle index event.
        """

        new_names = naming.shuffle_item_by_index_filtered_type(
            event.index,
            event.nice_name_type,
            offset=event.offset,
            separator="_",
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
            dag=False,
            remove_maya_defaults=True,
            transforms_only=True,
        )
        event.success = True if new_names else False

    @decorators.undo
    def change_padding(self, event: ChangePaddingEvent):
        """
        Change padding of the nodes.

        :param event: change padding event.
        """

        new_names = naming.change_suffix_padding_filter(
            event.nice_name_type,
            padding=event.padding,
            add_underscore=True,
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
            dag=False,
            remove_maya_defaults=True,
            transforms_only=True,
        )
        event.success = True if new_names else False

    @decorators.undo
    def renumber(self, event: RenumberEvent):
        """
        Renumber nodes.

        :param event: renumber event.
        """

        new_names = naming.renumber_filtered_type(
            event.nice_name_type,
            remove_trailing_numbers=event.remove_trailing_numbers,
            padding=event.padding,
            add_underscore=True,
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
            dag=False,
            remove_maya_defaults=True,
            transforms_only=True,
        )
        event.success = True if new_names else False

    @decorators.undo
    def remove_numbers(self, event: RemoveNumbersEvent):
        """
        Remove numbers from nodes.

        :param event: remove numbers event.
        """

        new_names = naming.remove_numbers_filtered_type(
            event.nice_name_type,
            trailing_only=event.trailing_only,
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
            dag=False,
            remove_maya_defaults=True,
            transforms_only=True,
        )
        event.success = True if new_names else False

    @decorators.undo
    def assign_namespace(self, event: AssignNamespaceEvent):
        """
        Assign namespace to nodes.

        :param event: assign namespace event.
        """

        new_names = naming.create_assign_namespace_filtered_type(
            event.namespace,
            event.nice_name_type,
            remove_namespace=event.remove_namespace,
            rename_shape=event.rename_shape,
            search_hierarchy=event.hierarchy,
            selection_only=event.selection_only,
            dag=False,
            remove_maya_defaults=True,
            transforms_only=True,
        )
        event.success = True if new_names else False

    @decorators.undo
    def delete_selected_namespace(self, event: DeleteSelectedNamespaceEvent):
        """
        Deletes selected namespace.

        :param event: delete selected namespace event.
        """

        event.success = naming.delete_selected_namespace(
            rename_shape=event.rename_shape
        )

    @decorators.undo
    def delete_unused_namespaces(self, event: DeleteUnusedNamespacesEvent):
        """
        Deletes unused namespaces.

        :param event: delete unused namespaces event.
        """

        deleted_namespaces = naming.remove_empty_namespaces()
        event.success = True if deleted_namespaces else False

    def open_namespace_editor(self, event: OpenNamespaceEditorEvent):
        """
        Opens namespace editor.

        :param event: open namespace editor event.
        """

        mel.eval("namespaceEditor")
        event.success = True

    def open_reference_editor(self, event: OpenReferenceEditorEvent):
        """
        Opens reference editor.

        :param event: open reference editor event.
        """

        mel.eval('tearOffRestorePanel "Reference Editor" referenceEditor true')
        event.success = True
