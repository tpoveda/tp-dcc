from __future__ import annotations

import typing
from dataclasses import dataclass, field

if typing.TYPE_CHECKING:
    from tp.naming.consts import EditIndexMode


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


@dataclass
class EditIndexEvent:
    """
    Event for editing the index.
    """

    text: str
    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    index: int
    mode: EditIndexMode
    success: bool = False


@dataclass
class ShuffleIndexEvent:
    """
    Event for shuffling the index.
    """

    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    index: int
    offset: int
    success: bool = False


@dataclass
class ChangePaddingEvent:
    """
    Event for changing the padding.
    """

    padding: int
    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class RenumberEvent:
    """
    Event for renumbering the nodes.
    """

    nice_name_type: str
    remove_trailing_numbers: bool
    padding: int
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class RemoveNumbersEvent:
    """
    Event for removing numbers from the nodes.
    """

    nice_name_type: str
    trailing_only: bool
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class AssignNamespaceEvent:
    """
    Event for assigning a namespace to the nodes.
    """

    namespace: str
    nice_name_type: str
    remove_namespace: bool
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class DeleteSelectedNamespaceEvent:
    """
    Event for deleting selected namespaces.
    """

    rename_shape: bool
    success: bool = False


@dataclass
class DeleteUnusedNamespacesEvent:
    """
    Event for deleting unused namespaces.
    """

    success: bool = False


@dataclass
class OpenNamespaceEditorEvent:
    """
    Event for opening the namespace editor.
    """

    success: bool = False


@dataclass
class OpenReferenceEditorEvent:
    """
    Event for opening the reference editor.
    """

    success: bool = False


@dataclass
class AutoPrefixEvent:
    """
    Event for auto prefix nodes based on their types.
    """

    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class AutoSuffixEvent:
    """
    Event for auto suffix nodes based on their types.
    """

    nice_name_type: str
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False


@dataclass
class MakeUniqueNameEvent:
    """
    Event for making unique names.
    """

    nice_name_type: str
    padding: int
    rename_shape: bool
    hierarchy: bool
    selection_only: bool
    success: bool = False
