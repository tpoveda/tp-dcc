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
