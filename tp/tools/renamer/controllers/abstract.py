from __future__ import annotations

import typing
from abc import abstractmethod

from tp.qt.mvc import Controller

if typing.TYPE_CHECKING:
    from ..events import (
        UpdateNodeTypesEvent,
        UpdatePrefixesSuffixesEvent,
        RenameBaseNameEvent,
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


class ARenamerController(Controller):
    """Abstract class that defines the interface for a renamer controller."""

    @abstractmethod
    def update_node_types(self, event: UpdateNodeTypesEvent):
        """
        Updates node types that can be used to filter nodes that can be renamed.

        :param event: update node types event.
        """

        raise NotImplementedError

    @abstractmethod
    def update_prefixes_suffixes(self, event: UpdatePrefixesSuffixesEvent):
        """
        Updates prefixes and suffixes that can be used to filter nodes that can be renamed.

        :param event: update prefixes and suffixes event.
        """

        raise NotImplementedError

    @abstractmethod
    def rename_base_name(self, event: RenameBaseNameEvent):
        """
        Renames the base name of the nodes.

        :param event: rename base name event.
        """

        raise NotImplementedError

    @abstractmethod
    def search_replace(self, event: RenameBaseNameEvent):
        """
        Renames the base name of the nodes.

        :param event: rename base name event.
        """

        raise NotImplementedError

    @abstractmethod
    def add_prefix(self, event: AddPrefixEvent):
        """
        Adds a prefix to the nodes.

        :param event: add prefix event.
        """

        raise NotImplementedError

    @abstractmethod
    def add_suffix(self, event: AddSuffixEvent):
        """
        Adds a suffix to the nodes.

        :param event: add suffix event.
        """

        raise NotImplementedError

    @abstractmethod
    def remove_prefix(self, event: RemovePrefixEvent):
        """
        Removes a prefix from the nodes.

        :param event: remove prefix event.
        """

        raise NotImplementedError

    @abstractmethod
    def remove_suffix(self, event: RemoveSuffixEvent):
        """
        Removes a suffix from the nodes.

        :param event: remove suffix event.
        """

        raise NotImplementedError

    @abstractmethod
    def edit_index(self, event: EditIndexEvent):
        """
        Edit index of the nodes.

        :param event: edit index event.
        """

        raise NotImplementedError

    @abstractmethod
    def shuffle_index(self, event: ShuffleIndexEvent):
        """
        Shuffle index of the nodes.

        :param event: shuffle index event.
        """

        raise NotImplementedError

    @abstractmethod
    def change_padding(self, event: ChangePaddingEvent):
        """
        Change padding of the nodes.

        :param event: change padding event.
        """

        raise NotImplementedError

    @abstractmethod
    def renumber(self, event: RenumberEvent):
        """
        Renumber nodes.

        :param event: renumber event.
        """

        raise NotImplementedError

    @abstractmethod
    def remove_numbers(self, event: RemoveNumbersEvent):
        """
        Remove numbers from nodes.

        :param event: remove numbers event.
        """

        raise NotImplementedError

    @abstractmethod
    def assign_namespace(self, event: AssignNamespaceEvent):
        """
        Assign namespace to nodes.

        :param event: assign namespace event.
        """

        raise NotImplementedError

    @abstractmethod
    def delete_selected_namespace(self, event: DeleteSelectedNamespaceEvent):
        """
        Deletes selected namespace.

        :param event: delete selected namespace event.
        """

        raise NotImplementedError

    @abstractmethod
    def delete_unused_namespaces(self, event: DeleteUnusedNamespacesEvent):
        """
        Deletes unused namespaces.

        :param event: delete unused namespaces event.
        """

        raise NotImplementedError

    @abstractmethod
    def open_namespace_editor(self, event: OpenNamespaceEditorEvent):
        """
        Opens namespace editor.

        :param event: open namespace editor event.
        """

        raise NotImplementedError

    @abstractmethod
    def open_reference_editor(self, event: OpenReferenceEditorEvent):
        """
        Opens reference editor.

        :param event: open reference editor event.
        """

        raise NotImplementedError
