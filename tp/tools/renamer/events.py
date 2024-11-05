from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class UpdateNodeTypesEvent:
    """
    Event for retrieving available node types.
    """

    node_types: list[str] = field(default_factory=list)


@dataclass
class UpdatePrefixesSuffixesEvent:
    """
    Event for retrieving available prefixes and suffixes.
    """

    prefixes: list[str] = field(default_factory=list)
    suffixes: list[str] = field(default_factory=list)


@dataclass
class RenameBaseNameEvent:
    """
    Event for renaming the base name.
    """

    base_name: str
    nice_name_type: str
    padding: int
    hierarchy: bool
    success: bool = False


@dataclass
class SearchReplaceEvent:
    """
    Event for searching and replacing text.
    """

    search: str
    replace: str
    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class AddPrefixEvent:
    """
    Event for adding a prefix.
    """

    prefix: str
    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class AddSuffixEvent:
    """
    Event for adding a suffix.
    """

    suffix: str
    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class RemovePrefixEvent:
    """
    Event for removing a prefix.
    """

    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class RemoveSuffixEvent:
    """
    Event for removing a suffix.
    """

    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False
