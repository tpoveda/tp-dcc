from __future__ import annotations

import typing

from tp.libs.qt.mvc import Controller

if typing.TYPE_CHECKING:
    from .. import events


class ARenamerController(Controller):
    """Abstract class that defines the interface for a renamer controller."""

    def update_node_types(self, event: events.UpdateNodeTypesEvent):
        """Updates node types that can be used to filter nodes that can be
        renamed.

        Args:
            event: Update node types event.
        """

        raise NotImplementedError

    def update_prefixes_suffixes(self, event: events.UpdatePrefixesSuffixesEvent):
        """Updates prefixes and suffixes that can be used to filter nodes
        that can be renamed.

        Args:
            event: Update prefixes and suffixes event.
        """

        raise NotImplementedError

    def rename_base_name(self, event: events.RenameBaseNameEvent):
        """Renames the base name of the nodes.

        Args:
            event: Rename base name event.
        """

        raise NotImplementedError

    def search_replace(self, event: events.RenameBaseNameEvent):
        """Renames the base name of the nodes.

        Args:
            event: Rename base name event.
        """

        raise NotImplementedError

    def add_prefix(self, event: events.AddPrefixEvent):
        """Adds a prefix to the nodes.

        Args:
            event: Add prefix event.
        """

        raise NotImplementedError

    def add_suffix(self, event: events.AddSuffixEvent):
        """Adds a suffix to the nodes.

        Args:
            event: Add suffix event.
        """

        raise NotImplementedError

    def remove_prefix(self, event: events.RemovePrefixEvent):
        """Removes a prefix from the nodes.

        Args:
            event: Remove prefix event.
        """

        raise NotImplementedError

    def remove_suffix(self, event: events.RemoveSuffixEvent):
        """Removes a suffix from the nodes.

        Args:
            event: Remove suffix event.
        """

        raise NotImplementedError

    def edit_index(self, event: events.EditIndexEvent):
        """Edit index of the nodes.

        Args:
            event: Edit index event.
        """

        raise NotImplementedError

    def shuffle_index(self, event: events.ShuffleIndexEvent):
        """Shuffle index of the nodes.

        Args:
            event: Shuffle index event.
        """

        raise NotImplementedError

    def change_padding(self, event: events.ChangePaddingEvent):
        """Change padding of the nodes.

        Args:
            event: Change padding event.
        """

        raise NotImplementedError

    def renumber(self, event: events.RenumberEvent):
        """Renumber nodes.

        Args:
            event: Renumber event.
        """

        raise NotImplementedError

    def remove_numbers(self, event: events.RemoveNumbersEvent):
        """Remove numbers from nodes.

        Args:
            event: Remove numbers event.
        """

        raise NotImplementedError

    def assign_namespace(self, event: events.AssignNamespaceEvent):
        """Assign namespace to nodes.

        Args:
            event: Assign namespace event.
        """

        raise NotImplementedError

    def delete_selected_namespace(self, event: events.DeleteSelectedNamespaceEvent):
        """Deletes selected namespace.

        Args:
            event: Delete selected namespace event.
        """

        raise NotImplementedError

    def delete_unused_namespaces(self, event: events.DeleteUnusedNamespacesEvent):
        """Deletes unused namespaces.

        Args:
            event: Delete unused namespaces event.
        """

        raise NotImplementedError

    def open_namespace_editor(self, event: events.OpenNamespaceEditorEvent):
        """Opens namespace editor.

        Args:
            event: Open namespace editor event.
        """

        raise NotImplementedError

    def open_reference_editor(self, event: events.OpenReferenceEditorEvent):
        """Opens reference editor.

        Args:
            event: Open reference editor event.
        """

        raise NotImplementedError

    def auto_prefix(self, event: events.AutoPrefixEvent):
        """Auto prefix nodes.

        Args:
            event: Auto prefix event.
        """

        raise NotImplementedError

    def auto_suffix(self, event: events.AutoSuffixEvent):
        """Auto suffix nodes.

        Args:
            event: Auto suffix event.
        """

        raise NotImplementedError

    def make_unique_name(self, event: events.MakeUniqueNameEvent):
        """Make unique name for nodes.

        Args:
            event: Make unique name event.
        """

        raise NotImplementedError
